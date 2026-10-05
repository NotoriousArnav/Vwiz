# Vwiz — Visualization Wizard

Turn notes (PDFs) and web research into a narrated, animated explainer video.

An agent ingests your documents, researches gaps, drafts a storyboard,
synthesizes narration, generates [Manim](https://www.manim.community/) animation
code, renders it inside a hardened Docker sandbox, and muxes picture with audio
into a finished MP4.

## Status

Early prototype. The Streamlit frontend exists; the agent pipeline is stubbed
and lands in milestone M3. See the plan for the full design:
`~/.opencode/plan/2026-10-05-vwiz-visualization-wizard.md`

## Architecture in one line

Narration drives timing, not the other way round: we synthesize the voiceover
first, *measure* its duration with `ffprobe`, then write Manim code constrained
to that measured duration.

## Requirements

- Python 3.14 (pinned in `.python-version`)
- [uv](https://docs.astral.sh/uv/)
- Docker — **required for rendering.** The current user must be in the `docker`
  group; without it the render stage cannot run:

  ```bash
  sudo usermod -aG docker "$USER"   # then re-login
  ```

  Note that docker-group membership is equivalent to root on the host, so Vwiz
  is a **localhost-only tool** and should not be exposed as a network service.

- `ffmpeg` / `ffprobe` on the host for muxing
- A Google AI Studio API key, plus a Google Cloud project with the
  Text-to-Speech API enabled for Chirp 3 HD voiceover

## Setup

```bash
uv sync
cp .env.example .env    # then fill in the keys
```

Start the memory store:

```bash
docker compose up -d
```

Run the frontend:

```bash
uv run vwiz        # or: uv run streamlit run src/vwiz/app.py
```

## Layout

```
src/vwiz/
  app.py         Streamlit frontend
  cli.py         entrypoint
  config.py      settings, loaded from .env
  models.py      Storyboard / Scene / Project
  graph/         LangGraph pipeline      (M3)
  mcp/           memory + search servers (M1, M4)
  render/        Docker sandbox         (M0)
  services/      TTS, media, prompts    (M2)
```

## Security note

Uploaded PDFs and search results are untrusted input that flows into agent
context, so they are a live prompt-injection vector. Retrieved text is treated
as data rather than instructions, and LLM-generated Manim code only ever runs
inside the sandboxed container — never on the host.