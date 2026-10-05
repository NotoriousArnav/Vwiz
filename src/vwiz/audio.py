"""Narration-first audio: Gemini TTS synthesis plus A/V sync muxing.

The pipeline is narration-first: synthesize the voiceover, measure it, then
fit the silent Manim render to the audio — stretching the video when the
narration runs long, padding the audio with silence when it runs short. Either
way the shipped mp4 starts and ends both streams together.

TTS always uses the Google key regardless of the chat provider choice: Groq
and Ollama have no voice. Speaking rate is applied with ffmpeg `atempo`
rather than a provider parameter, so it behaves identically everywhere.
"""

from __future__ import annotations

import subprocess
import wave
from dataclasses import dataclass
from pathlib import Path

from vwiz.config import Settings

__all__ = [
    "AudioError",
    "BeatAudio",
    "synthesize",
    "synthesize_beats",
    "split_beats",
    "detect_pauses",
    "build_srt",
    "write_srt",
    "concat_beat_audio",
    "fit_segment",
    "concat_videos",
    "mux_final",
    "probe_duration",
    "mux_narration",
]


class AudioError(RuntimeError):
    """Anything that kept narration from being built or muxed, inline."""


# Raw PCM format the TTS API returns. Fixed per the verified probe.
_TTS_RATE = 24_000
_TTS_CHANNELS = 1
_TTS_WIDTH = 2

# Upper bound on one narration request. Long scripts should be split per
# scene once multi-scene timing lands; one blob keeps v1 predictable.
_MAX_SCRIPT_CHARS = 5_000


def synthesize(
    text: str, chat_id: str, settings: Settings, *, name: str = "narration"
) -> tuple[Path, float]:
    """Synthesize `text` to wav. Returns (wav path, seconds). Raises AudioError."""
    script = text.strip()
    if not script:
        raise AudioError("nothing to narrate — the script is empty")
    if len(script) > _MAX_SCRIPT_CHARS:
        raise AudioError(f"script is {len(script):,} chars; v1 caps at {_MAX_SCRIPT_CHARS:,}")
    if not settings.google_api_key:
        raise AudioError("narration needs GOOGLE_API_KEY in .env (any chat provider works)")

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=settings.google_api_key)
    config = types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=settings.tts_voice)
            ),
            language_code=settings.tts_language,
        ),
    )
    try:
        stream = client.models.generate_content_stream(
            model=settings.tts_model, contents=script, config=config
        )
        chunks: list[bytes] = []
        for chunk in stream:
            for candidate in chunk.candidates or []:
                content = getattr(candidate, "content", None)
                for part in getattr(content, "parts", None) or []:
                    inline = getattr(part, "inline_data", None)
                    if inline and inline.data:
                        chunks.append(
                            inline.data if isinstance(inline.data, bytes) else bytes(inline.data)
                        )
    except Exception as exc:
        raise AudioError(f"TTS request failed ({type(exc).__name__}: {exc})") from exc
    if not chunks:
        raise AudioError("TTS returned no audio — retry, or shorten the script")

    out = settings.renders_dir / chat_id / f"{name}.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    pcm = b"".join(chunks)
    with wave.open(str(out), "wb") as wav:
        wav.setnchannels(_TTS_CHANNELS)
        wav.setsampwidth(_TTS_WIDTH)
        wav.setframerate(_TTS_RATE)
        wav.writeframes(pcm)
    with wave.open(str(out), "rb") as wav:
        seconds = wav.getnframes() / wav.getframerate()
    return out, seconds


@dataclass
class BeatAudio:
    """One narrated segment: its name, wav, exact duration, and start offset."""

    name: str
    wav: Path
    seconds: float
    starts_at: float = 0.0
    # Plain speakable text, kept for SRT captions.
    text: str = ""
    # Intra-beat silences, (start, end) seconds relative to this beat.
    pauses: list[tuple[float, float]] = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.pauses is None:
            self.pauses = []


def split_beats(script: str) -> list[tuple[str, str]]:
    """Split a script on `### Beat: <name>` headings.

    Beat-per-scene timing starts here: each segment is synthesized separately,
    so its duration is known exactly with no STT. A script without headings
    is one beat called "full", keeping every existing caller working.
    """
    import re

    beats: list[tuple[str, str]] = []
    current_name = "full"
    current_lines: list[str] = []
    seen_heading = False
    for line in script.split("\n"):
        heading = re.match(r"^\s*###\s*Beat:\s*(.+?)\s*$", line)
        if heading:
            if seen_heading or any(line.strip() for line in current_lines):
                beats.append((current_name, "\n".join(current_lines).strip()))
            current_name = re.sub(r"[^A-Za-z0-9 _-]+", "", heading.group(1)).strip() or "beat"
            current_lines = []
            seen_heading = True
        else:
            current_lines.append(line)
    tail = "\n".join(current_lines).strip()
    if tail or not beats:
        beats.append((current_name, tail))
    # Drop the pre-first-heading prologue when real beats exist: it is intro
    # chatter, not narration, and would desync the manifest.
    if seen_heading and beats and beats[0][0] == "full" and len(beats) > 1:
        beats.pop(0)
    return [(name, text) for name, text in beats if text]


def synthesize_beats(script: str, chat_id: str, settings: Settings) -> list[BeatAudio]:
    """Synthesize each beat separately. Returns the timing manifest.

    Durations come from the wav headers — sample-accurate and free. Whisper
    only becomes necessary for single-blob or user-uploaded audio, where we
    did not author the boundaries; that is a later phase, not this one.
    """
    import re

    manifest: list[BeatAudio] = []
    offset = 0.0
    for index, (name, text) in enumerate(split_beats(script)):
        slug = re.sub(r"[^A-Za-z0-9_-]+", "_", name).strip("_").lower() or f"beat{index}"
        wav, seconds = synthesize(text, chat_id, settings, name=f"beat_{slug}")
        pauses = detect_pauses(wav)
        manifest.append(
            BeatAudio(
                name=name, wav=wav, seconds=seconds, starts_at=offset, text=text, pauses=pauses
            )
        )
        offset += seconds
    if not manifest:
        raise AudioError("nothing to narrate — the script is empty")
    return manifest


def detect_pauses(
    wav_path: Path, *, min_silence_s: float = 0.30, threshold: float = 0.012
) -> list[tuple[float, float]]:
    """Intra-beat silences from the wav, for animation timing hints.

    RMS envelope over 20 ms windows; runs below `threshold` longer than
    `min_silence_s` are pauses. Reads the 24 kHz mono PCM we synthesize —
    no STT, no new dependency. Returns [(start, end)] in beat-relative seconds.
    """
    import array

    try:
        with wave.open(str(wav_path), "rb") as wav:
            n = wav.getnframes()
            raw = wav.readframes(n)
            width = wav.getsampwidth()
    except (OSError, wave.Error) as exc:
        raise AudioError(f"could not read {Path(wav_path).name} for pauses ({exc})") from exc
    if width != _TTS_WIDTH or not raw:
        return []
    frames = array.array("h", raw)
    # TTS writes little-endian; swap on big-endian hosts.
    import sys

    if sys.byteorder == "big":
        frames.byteswap()
    win = max(1, int(_TTS_RATE * 0.020))
    env: list[float] = []
    for i in range(0, len(frames) - win + 1, win):
        acc = 0
        for v in frames[i : i + win]:
            acc += v * v
        env.append((acc / win) ** 0.5 / 32768.0)
    pauses: list[tuple[float, float]] = []
    start: int | None = None
    for idx, amp in enumerate(env):
        if amp < threshold:
            if start is None:
                start = idx
        elif start is not None:
            a, b = start * 0.020, idx * 0.020
            if b - a >= min_silence_s:
                pauses.append((round(a, 2), round(b, 2)))
            start = None
    if start is not None:
        a, b = start * 0.020, len(env) * 0.020
        if b - a >= min_silence_s:
            pauses.append((round(a, 2), round(b, 2)))
    return pauses


def _srt_time(t: float) -> str:
    ms = int(round(max(0.0, t) * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_srt(beats: list[BeatAudio]) -> str:
    """One cue per beat: manifest offsets plus the speakable text."""
    out: list[str] = []
    for i, beat in enumerate(beats, 1):
        body = " ".join((beat.text or "").split())
        if not body or beat.seconds <= 0:
            continue
        start = beat.starts_at
        end = beat.starts_at + beat.seconds
        if end <= start:
            continue
        out.append(f"{i}\n{_srt_time(start)} --> {_srt_time(end)}\n{body}\n")
    return "\n".join(out)


def write_srt(beats: list[BeatAudio], chat_id: str, settings: Settings) -> Path:
    """Write the caption file next to the beat wavs. Returns its path."""
    out = settings.renders_dir / chat_id / "captions.srt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build_srt(beats), encoding="utf-8")
    return out


def concat_beat_audio(beats: list[BeatAudio], out: Path, settings: Settings) -> Path:
    """Join beat wavs into one track. Returns `out`. Raises AudioError."""
    if not beats:
        raise AudioError("no beats to join")
    inputs: list[str] = []
    for beat in beats:
        inputs += ["-i", str(beat.wav)]
    n = len(beats)
    chain = "".join(f"[{i}:a]" for i in range(n))
    cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", f"{chain}concat=n={n}:v=0:a=1[a]"] + [
        "-map",
        "[a]",
        "-c:a",
        "pcm_s16le",
        str(out),
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=settings.render_timeout_s
        )
    except subprocess.TimeoutExpired as exc:
        raise AudioError("audio concat timed out") from exc
    except OSError as exc:
        raise AudioError(f"could not start ffmpeg ({exc})") from exc
    if proc.returncode != 0:
        raise AudioError(f"audio concat failed:\n{(proc.stderr or '')[-1200:]}")
    return out


def fit_segment(video: Path, beat_seconds: float, out: Path, settings: Settings) -> Path:
    """Fit one beat segment to its narration with setpts. Returns `out`."""
    vdur = probe_duration(video)
    if vdur <= 0 or beat_seconds <= 0:
        raise AudioError("zero-length segment — nothing to fit")
    factor = beat_seconds / vdur
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(video),
        "-filter_complex",
        f"[0:v]setpts=PTS*{factor:.6f}[v]",
        "-map",
        "[v]",
        "-c:v",
        "libx264",
        "-preset",
        "veryfast",
        "-crf",
        "20",
        str(out),
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=settings.render_timeout_s
        )
    except subprocess.TimeoutExpired as exc:
        raise AudioError("segment fit timed out") from exc
    except OSError as exc:
        raise AudioError(f"could not start ffmpeg ({exc})") from exc
    if proc.returncode != 0:
        raise AudioError(f"segment fit failed:\n{(proc.stderr or '')[-1200:]}")
    return out


def concat_videos(parts: list[Path], out: Path, settings: Settings) -> Path:
    """Join fitted beat segments with the concat demuxer (stream copy)."""
    import tempfile

    if not parts:
        raise AudioError("no segments to join")
    if len(parts) == 1:
        import shutil

        shutil.copyfile(parts[0], out)
        return out
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
        for part in parts:
            # Single quotes escaped for the concat file format.
            safe = str(part.resolve()).replace("'", "'\\''")
            handle.write(f"file '{safe}'\n")
        list_path = handle.name
    try:
        proc = subprocess.run(
            ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_path, "-c", "copy", str(out)],
            capture_output=True,
            text=True,
            timeout=settings.render_timeout_s,
        )
    finally:
        Path(list_path).unlink(missing_ok=True)
    if proc.returncode != 0:
        raise AudioError(f"video concat failed:\n{(proc.stderr or '')[-1200:]}")
    return out


def mux_final(
    video: Path,
    audio_wav: Path,
    out: Path,
    settings: Settings,
    *,
    srt_path: Path | None = None,
) -> Path:
    """Mux joined video + joined audio, embedding SRT as mov_text captions."""
    cmd = ["ffmpeg", "-y", "-i", str(video), "-i", str(audio_wav)]
    if srt_path is not None and Path(srt_path).is_file():
        cmd += ["-i", str(srt_path)]
        cmd += [
            "-map",
            "0:v",
            "-map",
            "1:a",
            "-map",
            "2",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-c:s",
            "mov_text",
        ]
    else:
        cmd += ["-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "aac"]
    # Cap to the shorter stream so a rounding wobble cannot tail silence.
    cmd += ["-shortest", str(out)]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=settings.render_timeout_s
        )
    except subprocess.TimeoutExpired as exc:
        raise AudioError(f"final mux timed out after {settings.render_timeout_s}s") from exc
    except OSError as exc:
        raise AudioError(f"could not start ffmpeg ({exc})") from exc
    if proc.returncode != 0:
        raise AudioError(
            f"final mux failed (exit {proc.returncode}):\n{(proc.stderr or '')[-1500:]}"
        )
    return out


def probe_duration(path: Path) -> float:
    """Media duration in seconds via ffprobe. Raises AudioError."""
    try:
        proc = subprocess.run(
            [
                "ffprobe",
                "-v",
                "error",
                "-show_entries",
                "format=duration",
                "-of",
                "csv=p=0",
                str(path),
            ],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except OSError as exc:
        raise AudioError(f"could not start ffprobe ({exc})") from exc
    try:
        return float((proc.stdout or "").strip())
    except ValueError:
        raise AudioError(f"could not read duration of {Path(path).name}") from None


def _atempo(rate: float) -> str:
    """atempo chain for any rate in [0.25, 2.0]; single atempo spans 0.5–2.0."""
    chain = []
    remaining = rate
    while remaining < 0.5:
        chain.append("atempo=0.5")
        remaining /= 0.5
    chain.append(f"atempo={remaining:.3f}")
    return ",".join(chain)


def mux_narration(
    video: Path, narration_wav: Path, out: Path, settings: Settings, *, rate: float = 1.0
) -> Path:
    """Fit `video` to the narration and mux. Returns `out`. Raises AudioError."""
    vdur = probe_duration(video)
    adur = probe_duration(narration_wav) / rate
    if vdur <= 0 or adur <= 0:
        raise AudioError("zero-length video or narration — nothing to sync")

    cmd = ["ffmpeg", "-y", "-i", str(video), "-i", str(narration_wav)]
    if adur >= vdur:
        # Stretch the video to the voiceover: factor > 1 slows motion down.
        cmd += [
            "-filter_complex",
            f"[0:v]setpts=PTS*{adur / vdur:.6f}[v];[1:a]{_atempo(rate)}[a]",
            "-map",
            "[v]",
            "-map",
            "[a]",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "20",
            "-c:a",
            "aac",
        ]
    else:
        # Voiceover is short: keep video speed, pad the tail with silence.
        cmd += [
            "-filter_complex",
            f"[1:a]{_atempo(rate)},apad[ap]",
            "-map",
            "0:v",
            "-map",
            "[ap]",
            "-c:v",
            "copy",
            "-c:a",
            "aac",
            "-t",
            f"{vdur:.3f}",
        ]
    cmd.append(str(out))
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=settings.render_timeout_s
        )
    except subprocess.TimeoutExpired as exc:
        raise AudioError(f"mux timed out after {settings.render_timeout_s}s") from exc
    except OSError as exc:
        raise AudioError(f"could not start ffmpeg ({exc})") from exc
    if proc.returncode != 0:
        tail = (proc.stderr or "")[-1500:]
        raise AudioError(f"mux failed (exit {proc.returncode}):\n{tail}")
    return out
