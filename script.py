#!/usr/bin/env python3
"""
Prompt -> Research via Tavily/Exa MCP -> Narration script ->
Gemini TTS -> Groq word timestamps -> Manim code ->
Docker render -> Merge audio/video -> Print final output path
"""

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated, TypedDict

import requests
from dotenv import load_dotenv
from google import genai
from google.genai import types
from groq import Groq
from langchain_core.messages import HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages

load_dotenv()

# -----------------------------
# Configuration
# -----------------------------

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GOOGLE_API_KEY = os.environ["GOOGLE_API_KEY"]
TAVILY_API_KEY = os.environ["TAVILY_API_KEY"]
EXA_API_KEY = os.environ["EXA_API_KEY"]

GROQ_LLM = "openai/gpt-oss-120b"
GROQ_STT_MODEL = "whisper-large-v3-turbo"
GEMINI_TTS_MODEL = "gemini-3.8-flash-tts"
GEMINI_VOICE = "Koda"
MAX_MANIM_FIX_ATTEMPTS = 3

# manim-video skill (Agent Skills-compatible folder). Prompts below load
# style/API rules from these files at runtime instead of hardcoding them.
SKILL_DIR = Path("skills/manim-video")
# Pinned to the skill-tested base (SKILL.md: v0.20.1). Override with
# MANIM_DOCKER_IMAGE=manim-video-runtime:v0.20.1 after running
# skills/manim-video/scripts/setup.sh, or any custom image.
MANIM_DOCKER_IMAGE = os.environ.get("MANIM_DOCKER_IMAGE", "manimcommunity/manim:v0.20.1")

WORKDIR = Path("generated_video")
WORKDIR.mkdir(exist_ok=True)

AUDIO_PATH = WORKDIR / "narration.wav"
TRANSCRIPT_PATH = WORKDIR / "word_timestamps.json"
MANIM_CODE_PATH = WORKDIR / "animation.py"
# Manim v0.18 writes 720p/, v0.21+ writes 720p30/ — resolved dynamically.
MANIM_VIDEO_CANDIDATES = [
    WORKDIR / "media/videos/animation/720p30/ManimScene.mp4",
    WORKDIR / "media/videos/animation/720p/ManimScene.mp4",
]
FINAL_VIDEO_PATH = WORKDIR / "final_video.mp4"


def _find_manim_output() -> Path:
    for candidate in MANIM_VIDEO_CANDIDATES:
        if candidate.exists():
            return candidate
    matches = sorted((WORKDIR / "media/videos/animation").glob("*/ManimScene.mp4"))
    return matches[0] if matches else MANIM_VIDEO_CANDIDATES[0]

MANIM_DOCKER_COMMAND = [
    "docker",
    "run",
    "--rm",
    "-v",
    f"{WORKDIR.resolve()}:/manim",
    "-w",
    "/manim",
    MANIM_DOCKER_IMAGE,
    "manim",
    "-qm",
    "animation.py",
    "ManimScene",
]


def _read_skill_ref(name: str, limit: int = 1200) -> str:
    """Read a manim-video skill reference file, truncated for TPM budget."""
    try:
        return (SKILL_DIR / "references" / name).read_text(encoding="utf-8")[:limit]
    except OSError:
        return ""


def _skill_rules(topic: str = "") -> str:
    """Compose a small skill-grounded rule block for Manim codegen prompts."""
    t = topic.lower()
    parts = [
        'Style contract (skills/manim-video/SKILL.md): BG="#1C1C1C", PRIMARY="#58C4DD", '
        'SECONDARY="#83C167", ACCENT="#FFFF00", MONO="Noto Sans Mono". '
        "Set self.camera.background_color=BG in construct(). "
        "Title 48 / Heading 36 / Body 30 / Label 24. buff>=0.5 on to_edge(). "
        "Max 5-6 elements visible; breathing self.wait() after each reveal."
    ]
    # Troubleshooting patterns are the highest-value excerpt (fixes real crashes).
    trouble = _read_skill_ref("troubleshooting.md", limit=1000)
    if trouble:
        parts.append("Skill troubleshooting excerpt:\n" + trouble)
    # Topic-specific reference: matrices/equations vs plots/graphs.
    if any(k in t for k in ("matrix", "matrices", "equation", "derivation", "proof")):
        eq = _read_skill_ref("equations.md", limit=800)
        if eq:
            parts.append("Skill equations excerpt:\n" + eq)
    if any(k in t for k in ("graph", "plot", "chart", "data", "curve", "axes")):
        gr = _read_skill_ref("graphs-and-data.md", limit=800)
        if gr:
            parts.append("Skill graphs excerpt:\n" + gr)
    block = "\n\n".join(parts)
    return block[:2500]

# -----------------------------
# Graph state
# -----------------------------


class PipelineState(TypedDict):
    user_prompt: str
    messages: Annotated[list, add_messages]
    research_notes: str
    narration_script: str
    word_timestamps: list[dict]
    manim_code: str
    final_video_path: str


# -----------------------------
# Node 1: Research using MCP tools
# -----------------------------


def research_node(state: PipelineState) -> dict:
    """Research using Tavily directly, then summarize with a small Groq call."""

    response = requests.post(
        "https://api.tavily.com/search",
        headers={
            "Authorization": f"Bearer {TAVILY_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "query": state["user_prompt"],
            "search_depth": "basic",
            "max_results": 3,
            "include_answer": True,
        },
        timeout=30,
    )

    response.raise_for_status()
    data = response.json()

    results = data.get("results", [])

    compact_results = "\n".join(
        f"- {item.get('title', '')}: {item.get('content', '')[:500]}" for item in results
    )

    research_material = (
        f"Topic: {state['user_prompt']}\n\n"
        f"Tavily answer:\n{data.get('answer', '')}\n\n"
        f"Search results:\n{compact_results}"
    )

    llm = ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=GROQ_API_KEY,
        temperature=0.2,
        max_tokens=500,
    )

    summary = llm.invoke(
        f"""Summarize the following research into under 180 words.

Include:
- Key concepts
- One example
- Concepts to visualize

Research:
{research_material}
"""
    )

    return {"research_notes": summary.content.strip()}


# -----------------------------
# Node 2: Generate narration script
# -----------------------------


def script_node(state: PipelineState) -> dict:
    """Turn research notes into a clean narration script."""

    llm = ChatGroq(
        model=GROQ_LLM,
        api_key=GROQ_API_KEY,
        temperature=0.4,
    )

    prompt = f"""Create a clear, engaging narration script for a Manim educational video.

Topic:
{state["user_prompt"]}

Research notes:
{state["research_notes"]}

Requirements:
- The narration should take approximately 60-120 seconds to read aloud.
- Use plain, natural spoken English.
- No markdown, headings, bullet points, stage directions, sound cues, or speaker labels.
- Explain concepts in an order that can be visualized.
- Include a brief takeaway at the end.
- Return only the narration text.
"""

    response = llm.invoke(prompt)
    narration_script = response.content.strip()

    return {"narration_script": narration_script}


# -----------------------------
# Node 3: Generate TTS audio with Gemini
# -----------------------------


def tts_node(state: PipelineState) -> dict:
    """Generate WAV narration using Gemini Flash TTS."""

    client = genai.Client(api_key=GOOGLE_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_TTS_MODEL,
        contents=state["narration_script"],
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config={
                "voice_config": {
                    "prebuilt_voice_config": {
                        "voice_name": GEMINI_VOICE,
                    }
                }
            },
        ),
    )

    part = response.candidates[0].content.parts[0]

    if not part.inline_data or not part.inline_data.data:
        raise RuntimeError("Gemini TTS did not return audio data.")

    AUDIO_PATH.write_bytes(part.inline_data.data)

    print(f"🔊 Audio generated: {AUDIO_PATH}")

    return {}


# -----------------------------
# Node 4: Transcribe audio with Groq
# -----------------------------


def transcribe_node(state: PipelineState) -> dict:
    """Use Groq Whisper to obtain word-level timestamps."""

    client = Groq(api_key=GROQ_API_KEY)

    with AUDIO_PATH.open("rb") as audio_file:
        transcript = client.audio.transcriptions.create(
            file=audio_file,
            model=GROQ_STT_MODEL,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )

    words = transcript.words

    if not words:
        raise RuntimeError("Groq did not return word-level timestamps.")

    TRANSCRIPT_PATH.write_text(
        json.dumps(words, indent=2),
        encoding="utf-8",
    )

    print(f"🕒 Word timestamps saved: {TRANSCRIPT_PATH}")

    return {"word_timestamps": words}


# -----------------------------
# Node 5: Generate Manim code
# -----------------------------


def _compress_timestamps(words: list[dict], max_gap: float = 10.0, max_words: int = 30) -> list[dict]:
    """Group word-level timestamps into ~10s / sentence segments for the LLM prompt."""
    segments: list[dict] = []
    cur_words: list[str] = []
    cur_start: float | None = None
    cur_end: float = 0.0

    for w in words:
        text = str(w.get("word", ""))
        start = float(w.get("start", 0.0))
        end = float(w.get("end", 0.0))
        if cur_start is None:
            cur_start = start
        cur_words.append(text)
        cur_end = end
        duration = cur_end - cur_start
        sentence_end = text.rstrip().endswith((".", "?", "!"))
        if (sentence_end and duration >= 4.0) or duration >= max_gap or len(cur_words) >= max_words:
            segments.append(
                {"s": round(cur_start, 1), "e": round(cur_end, 1), "text": " ".join(cur_words)}
            )
            cur_words = []
            cur_start = None

    if cur_words and cur_start is not None:
        segments.append(
            {"s": round(cur_start, 1), "e": round(cur_end, 1), "text": " ".join(cur_words)}
        )

    return segments


def _sanitize_manim_code(code: str) -> str:
    """Auto-fix common LLM mistakes: wrong class name, deprecated Axes API."""
    import re

    # 1. Any `class Foo(Scene)` -> `class ManimScene(Scene)`
    code = re.sub(r"class\s+\w+\s*\(\s*Scene\s*\)", "class ManimScene(Scene)", code, count=1)
    # 2. Axes.get_graph() was removed; use Axes.plot() in CE v0.18+.
    code = code.replace(".get_graph(", ".plot(")
    # 3. `label` inside axis configs is not a valid Manim kwarg — it
    #    propagates to Mobject.__init__ and crashes the render.
    #    Strip `"label": ...` entries; labels should be separate Text mobjects.
    code = re.sub(r"""["']label["']\s*:\s*["'][^"']*["']\s*,?""", "", code)
    code = re.sub(r""",\s*,+""", ",", code)
    # 4. Ensure manim import exists.
    if "from manim import" not in code:
        code = "from manim import *\n" + code
    return code


def _fix_manim_code_with_llm(broken_code: str, error_log: str, skill_notes: str = "") -> str:
    """Ask Groq for a minimal fix of broken Manim code (no full rewrite)."""
    llm = ChatGroq(
        model=GROQ_LLM,
        api_key=GROQ_API_KEY,
        temperature=0.1,
        max_tokens=3500,
    )
    prompt = f"""Fix this Manim Community Edition v0.20.1 script so it renders.

Rules:
- Make the MINIMAL edit that fixes the traceback. Do not rewrite working scenes.
- Keep exactly one `class ManimScene(Scene)`.
- Use `axes.plot(fn, color=...)`, never `get_graph()`.
- Never pass `label=` or `"label":` inside Axes / axis_config / x_axis_config / y_axis_config. Use a separate Text/MathTex for labels.
- Preserve scene hygiene: do not leave two Axes on screen at once; if your fix adds an Axes, FadeOut the previous one first.
- Only use Manim CE v0.20.1 APIs. Return only valid Python code, no markdown fences.
{skill_notes}

Traceback (truncated):
{error_log}

Broken code:
{broken_code}
"""
    response = llm.invoke(prompt)
    fixed = response.content.strip()
    if fixed.startswith("```"):
        fixed = fixed.strip("`")
        if fixed.lower().startswith("python"):
            fixed = fixed[6:]
    return _sanitize_manim_code(fixed)


def _truncate_log(text: str, limit: int = 2500) -> str:
    """Keep the tail of docker logs so the fix prompt stays under TPM limits."""
    text = text or ""
    return text[-limit:] if len(text) > limit else text


def _hygiene_warning(code: str) -> str:
    """Heuristic: flag new Axes created without fading previous axes objects."""
    import re

    axes_defs = list(re.finditer(r"(\w+)\s*=\s*Axes\s*\(", code))
    if len(axes_defs) < 2:
        return ""
    issues = []
    for prev, cur in zip(axes_defs, axes_defs[1:]):
        prev_var = prev.group(1)
        between = code[prev.end() : cur.start()]
        faded = (
            re.search(r"FadeOut\([^)]*\b" + re.escape(prev_var) + r"\b", between) is not None
            or "self.clear()" in between
        )
        if not faded:
            line = code[: cur.start()].count("\n") + 1
            issues.append(f"{cur.group(1)} (line ~{line}) without FadeOut({prev_var})")
    if issues:
        return "⚠️ Hygiene: overlapping Axes likely — " + "; ".join(issues) + "."
    n_fade = code.count("FadeOut") + code.count("self.clear()")
    if len(axes_defs) > n_fade:
        return (
            f"⚠️ Hygiene: {len(axes_defs)}x Axes() but only {n_fade}x FadeOut/clear — "
            "scenes likely overlap."
        )
    return ""


def manim_code_node(state: PipelineState) -> dict:
    """Generate a Manim Community Edition scene aligned to narration timing."""

    llm = ChatGroq(
        model=GROQ_LLM,
        api_key=GROQ_API_KEY,
        temperature=0.1,
        max_tokens=5000,
    )

    segments = _compress_timestamps(state["word_timestamps"])
    total_duration = round(float(state["word_timestamps"][-1]["end"]), 1)
    skill_notes = _skill_rules(state.get("user_prompt", ""))

    prompt = f"""Write a complete Python script for Manim Community Edition v0.20.1.

The concatenated segment texts below are the full narration ({total_duration}s total).
Use each segment's start/end seconds to time major visuals approximately.

Narration timeline (seconds):
{json.dumps(segments, indent=1)}

Skill guidance (from skills/manim-video/):
{skill_notes}

Hard requirements:
- Define exactly one Scene class named ManimScene spelled exactly that way.
- Use only Manim Community Edition v0.20.1 APIs.
- For function graphs on Axes, use axes.plot(fn, color=...) — never get_graph().
- Never pass label= or "label": inside Axes(), axis_config, x_axis_config, or y_axis_config (it crashes). Use a separate Text/MathTex for axis titles.
- For axis labels use plain strings like "I (A)", never backslash-escaped labels.
- Scene hygiene (important): each narration segment is a fresh visual.
  Start every new segment by fading out the previous segment's mobjects,
  e.g. self.play(FadeOut(prev_group)).
  Never leave two Axes on screen at once — always FadeOut the old
  axes + labels + curves + points before Create()ing the next Axes.
  Group per-segment objects in a VGroup so they can be removed together.
  Do not reference a faded-out Axes later unless you recreate it.
- Do not use external images, fonts, network access, or nonstandard packages.
- Use self.wait() and animation timing so major visuals align approximately with narration.
- Keep on-screen text concise and readable at 720p.
- Keep the script compact (under ~220 lines). It MUST end with a complete
  construct() method — never leave a dangling assignment or truncated block.
- Avoid overly long animations; total duration should closely match the audio.
- The code must be directly runnable with:
  manim -qm animation.py ManimScene

Return only valid Python code.
Do not wrap the code in markdown fences.
"""

    manim_code = ""
    for attempt in range(1, MAX_MANIM_FIX_ATTEMPTS + 1):
        if attempt == 1:
            response = llm.invoke(prompt)
            manim_code = response.content.strip()
        # Remove markdown fences if the model adds them despite instructions.
        if manim_code.startswith("```"):
            manim_code = manim_code.strip("`")

            if manim_code.lower().startswith("python"):
                manim_code = manim_code[6:]

        manim_code = _sanitize_manim_code(manim_code)

        if "class ManimScene(Scene)" not in manim_code:
            error = "Missing `class ManimScene(Scene)`."
        else:
            try:
                compile(manim_code, str(MANIM_CODE_PATH), "exec")
                break
            except SyntaxError as exc:
                error = f"SyntaxError line {exc.lineno}: {exc.msg} (text: {(exc.text or '').strip()[:200]})"

        if attempt >= MAX_MANIM_FIX_ATTEMPTS:
            raise RuntimeError(
                f"Generated Manim code failed validation after {MAX_MANIM_FIX_ATTEMPTS} attempts: {error}"
            )
        print(f"⚠️ Manim code invalid ({error}), asking LLM to fix...")
        manim_code = _fix_manim_code_with_llm(
            _truncate_log(manim_code, limit=8000), error, skill_notes
        )

    warning = _hygiene_warning(manim_code)
    if warning:
        print(warning)

    MANIM_CODE_PATH.write_text(manim_code, encoding="utf-8")

    print(f"📝 Manim script generated: {MANIM_CODE_PATH}")

    return {"manim_code": manim_code}


# -----------------------------
# Node 6: Render Manim video with Docker
# -----------------------------


def render_node(state: PipelineState) -> dict:
    """Render with Docker; on failure ask the LLM to fix the code in-run.

    This preserves the already-generated TTS audio — no full pipeline
    rerun (and no wasted Gemini/Groq tokens) just because Manim code
    had a bad kwarg.
    """

    print("🎬 Rendering Manim video with Docker...")
    print(f"🐳 Image: {MANIM_DOCKER_IMAGE}")

    code = state.get("manim_code") or (
        MANIM_CODE_PATH.read_text(encoding="utf-8") if MANIM_CODE_PATH.exists() else ""
    )
    if not code:
        raise RuntimeError("No Manim code available to render.")
    skill_notes = _skill_rules(state.get("user_prompt", ""))

    last_stdout = ""
    last_stderr = ""
    for attempt in range(1, MAX_MANIM_FIX_ATTEMPTS + 1):
        MANIM_CODE_PATH.write_text(code, encoding="utf-8")
        result = subprocess.run(
            MANIM_DOCKER_COMMAND,
            cwd=WORKDIR,
            capture_output=True,
            text=True,
        )
        last_stdout, last_stderr = result.stdout, result.stderr

        if result.returncode == 0:
            manim_video = _find_manim_output()
            if manim_video.exists():
                print(f"✅ Manim video rendered: {manim_video}")
                return {"manim_code": code}
            last_stdout = f"Render exited 0 but output missing. Searched: {[str(p) for p in MANIM_VIDEO_CANDIDATES]}"

        if attempt >= MAX_MANIM_FIX_ATTEMPTS:
            break

        print(f"⚠️ Render attempt {attempt} failed, asking LLM to fix...")

        # Truncate: docker progress bars are huge; keep traceback tail only.
        error_log = (
            f"STDOUT tail:\n{_truncate_log(last_stdout)}\n\n"
            f"STDERR tail:\n{_truncate_log(last_stderr, limit=1500)}"
        )
        # Keep the fix prompt small: truncated code tail + error.
        code = _fix_manim_code_with_llm(
            _truncate_log(code, limit=8000), error_log, skill_notes
        )
        try:
            compile(code, str(MANIM_CODE_PATH), "exec")
        except SyntaxError as exc:
            print(f"⚠️ LLM fix had a syntax error ({exc}), retrying...")

    raise RuntimeError(
        f"Manim Docker render failed after {MAX_MANIM_FIX_ATTEMPTS} attempts "
        f"(TTS audio preserved at {AUDIO_PATH}).\n\n"
        f"STDOUT:\n{last_stdout}\n\nSTDERR:\n{last_stderr}"
    )


# -----------------------------
# Node 7: Merge Manim video and narration audio
# -----------------------------


def merge_node(state: PipelineState) -> dict:
    """Merge the rendered Manim video with the Gemini TTS narration."""

    print("🎧 Merging Manim video with narration audio...")
    manim_video = _find_manim_output()

    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(manim_video),
        "-i",
        str(AUDIO_PATH),
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-shortest",
        str(FINAL_VIDEO_PATH),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg merge failed.\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )

    final_path = str(FINAL_VIDEO_PATH.resolve())

    print(f"✅ Final video created: {final_path}")

    return {"final_video_path": final_path}


# -----------------------------
# Build LangGraph pipeline
# -----------------------------


def build_graph():
    graph = StateGraph(PipelineState)

    graph.add_node("research", research_node)
    graph.add_node("write_script", script_node)
    graph.add_node("generate_tts", tts_node)
    graph.add_node("transcribe", transcribe_node)
    graph.add_node("write_manim", manim_code_node)
    graph.add_node("render_manim", render_node)
    graph.add_node("merge_av", merge_node)

    graph.add_edge(START, "research")
    graph.add_edge("research", "write_script")
    graph.add_edge("write_script", "generate_tts")
    graph.add_edge("generate_tts", "transcribe")
    graph.add_edge("transcribe", "write_manim")
    graph.add_edge("write_manim", "render_manim")
    graph.add_edge("render_manim", "merge_av")
    graph.add_edge("merge_av", END)

    return graph.compile()


# -----------------------------
# Entry point
# -----------------------------


async def main():
    if len(sys.argv) < 2:
        print('Usage: python video_pipeline.py "Your video topic or prompt"')
        sys.exit(1)

    user_prompt = " ".join(sys.argv[1:])

    print("🚀 Starting video generation pipeline")
    print(f"📌 Topic: {user_prompt}\n")

    app = build_graph()

    initial_state = {
        "user_prompt": user_prompt,
        "messages": [HumanMessage(content=user_prompt)],
    }

    final_state = await app.ainvoke(initial_state)

    print("\n🎉 Video generation complete")
    print(f"📁 Final output: {final_state['final_video_path']}")


if __name__ == "__main__":
    asyncio.run(main())
