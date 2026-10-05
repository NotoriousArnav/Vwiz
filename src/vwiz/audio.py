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
from pathlib import Path

from vwiz.config import Settings

__all__ = ["AudioError", "synthesize", "probe_duration", "mux_narration"]


class AudioError(RuntimeError):
    """Anything that kept narration from being built or muxed, inline."""


# Raw PCM format the TTS API returns. Fixed per the verified probe.
_TTS_RATE = 24_000
_TTS_CHANNELS = 1
_TTS_WIDTH = 2

# Upper bound on one narration request. Long scripts should be split per
# scene once multi-scene timing lands; one blob keeps v1 predictable.
_MAX_SCRIPT_CHARS = 5_000


def synthesize(text: str, chat_id: str, settings: Settings) -> tuple[Path, float]:
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

    out = settings.renders_dir / chat_id / "narration.wav"
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
