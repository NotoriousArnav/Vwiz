"""Audio-first chain: script -> per-beat TTS -> timestamps -> timed code.

Gated at code: this module runs stages 1–4 automatically after the agent
produces a beat script. Rendering (stage 5) stays behind Preview/Final so a
human reviews the timed code first. One model call per beat keeps requests
small enough for Groq's token ceiling and isolates failures to one beat.
"""

from __future__ import annotations

from vwiz import audio as audio_mod
from vwiz import llm
from vwiz.config import Settings

__all__ = ["ChainResult", "run_chain"]


class ChainResult:
    """Beats with timings, the caption file, and the combined multi-scene code."""

    def __init__(
        self,
        beats: list[audio_mod.BeatAudio],
        srt_path,
        code: str,
        scene_names: list[str],
        failed: list[str] | None = None,
    ) -> None:
        self.beats = beats
        self.srt_path = srt_path
        self.code = code
        self.scene_names = scene_names
        self.failed = failed or []


def run_chain(script: str, chat_id: str, settings: Settings) -> ChainResult:
    """Synthesize beats, extract timestamps, generate one Scene per beat."""
    beats = audio_mod.synthesize_beats(script, chat_id, settings)

    codes: list[str] = []
    scene_names: list[str] = []
    failed: list[str] = []
    for index, beat in enumerate(beats):
        try:
            name, code = llm.generate_beat_code(
                beat_name=beat.name,
                beat_text=beat.text,
                beat_seconds=beat.seconds,
                pauses=list(beat.pauses or []),
                settings=settings,
                index=index,
            )
        except Exception as exc:  # noqa: BLE001 - one bad beat skips, rest ship
            failed.append(f"{beat.name}: {exc}")
            continue
        scene_names.append(name)
        codes.append(code)

    if not codes:
        detail = "; ".join(failed) if failed else "unknown codegen failure"
        raise RuntimeError(f"timed codegen failed for every beat ({detail})")

    combined = llm.combine_beat_codes(codes)
    srt_path = audio_mod.write_srt(beats, chat_id, settings)
    return ChainResult(
        beats=beats, srt_path=srt_path, code=combined, scene_names=scene_names, failed=failed
    )
