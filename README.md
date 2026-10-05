# Vwiz — Visualization Wizard

Turn notes and web research into a narrated, animated explainer video.

An agent ingests your documents, researches gaps, drafts a storyboard,
synthesizes narration, generates [Manim](https://www.manim.community/) animation
code, renders it inside a hardened Docker sandbox, and muxes picture with audio
into a finished MP4.

## Status

Early prototype. The Streamlit frontend and document ingest exist; the agent
pipeline is stubbed and lands in milestone M3. See the plan for the full design:
`~/.opencode/plan/2026-10-05-vwiz-visualization-wizard.md`.

## Supported documents

Attach any of these to the chat. Extraction runs on upload, so a file that
cannot be read fails immediately instead of mid-generation.

| Family | Extensions | Notes |
| --- | --- | --- |
| PDF | `.pdf` | Text layer only; scanned pages are reported, not OCR'd |
| Plain text | `.txt` `.text` `.log` | UTF-8 / UTF-16 / BOM / latin-1 detected |
| Tabular | `.csv` `.tsv` | Rendered as a Markdown table, headers preserved |
| Markdown | `.md` `.markdown` `.mdx` | Headings kept as levels; fenced code verbatim |
| Word | `.docx` | Paragraphs, headings and tables in document order |
| OpenDocument | `.odt` | Headings, lists and tables |
| Rich text | `.rtf` | Best effort — only prose recovered, layout lost |
| Web | `.html` `.htm` `.xhtml` | Script and style stripped |

Legacy `.doc`, `.ppt(x)` and `.xls(x)` are rejected with a message pointing at a
better format rather than being parsed badly.

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
  ingest.py      text extraction per file format
  models.py      Chat / Message / Role
  store.py       on-disk chat persistence
  graph/         LangGraph pipeline      (M3)
  mcp/           memory + search servers (M1, M4)
  render/        Docker sandbox         (M0)
  services/      TTS, media, prompts    (M2)
```

## Security note

Uploaded documents and search results are untrusted input that flows into agent
context, so they are a live prompt-injection vector. Retrieved text is treated
as data rather than instructions, and LLM-generated Manim code only ever runs
inside the sandboxed container — never on the host.

Parsing untrusted files has its own hazards, so extraction is defensive:

- `.docx` and `.odt` are zip archives. Their uncompressed size is read from the
  central directory and checked *before* anything is inflated, because the
  upload cap bounds only the compressed bytes.
- XML-family formats go through `defusedxml`, blocking entity expansion and
  external entities. HTML uses `html.parser`, which does not fetch externals.
- Filenames from the client are reduced to a basename and filtered to a safe
  character set; the stored name is a server-generated uuid.
- Extraction is capped by `MAX_DOCUMENT_CHARS`, and truncation is reported to
  the user rather than silently applied.