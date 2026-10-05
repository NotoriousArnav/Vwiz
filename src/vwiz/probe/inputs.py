"""Document materialization for the probe agent.

The agent's `read` tool returns text files as text but anything else (PDF,
docx, odt, ...) as an opaque base64 blob. So a binary document placed in
`inputs/` is invisible to the agent. The fix: alongside the original, write an
extracted-text sidecar (`<name>.txt`) using our `ingest` extractors. The agent
reads the sidecar; the original stays for provenance.

Sidecars are regenerated from the original every time, never edited — the
original is the source of truth, the `.txt` is a disposable view.
"""

from __future__ import annotations

import re
import shutil
from pathlib import Path

from vwiz.config import Settings

__all__ = ["materialize", "INPUTS_DIR"]

INPUTS_DIR = "inputs"

# ingest kinds the agent can already read with zero loss, so no sidecar needed.
_TEXT_NATIVE_KINDS = frozenset({"text", "table", "markdown"})

# Upper bound on sidecar size. The agent pages through reads, but an unbounded
# sidecar invites a full-file read that blows the context window.
_SIDECAR_MAX_CHARS = 100_000

_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def materialize(source: Path, scratch: Path, settings: Settings) -> dict:
    """Copy `source` into `scratch/inputs/` plus a text sidecar when needed.

    Returns a dict with `original`, `sidecar` (or None), and `notes`.
    """
    from vwiz import ingest

    inputs = scratch / INPUTS_DIR
    inputs.mkdir(parents=True, exist_ok=True)

    safe = _UNSAFE.sub("_", Path(source).name).strip("._") or "upload.bin"
    safe = safe[:120]
    target = inputs / safe
    for i in range(1, 100):
        if not target.exists():
            break
        target = inputs / f"{target.stem}_{i}{target.suffix}"
    shutil.copyfile(source, target)

    notes: list[str] = [f"stored as inputs/{target.name}"]
    sidecar: Path | None = None
    try:
        result = ingest.extract(
            target,
            max_chars=settings.max_document_chars,
            max_expanded_bytes=settings.max_archive_expanded_bytes,
        )
    except ingest.UnsupportedFormat as exc:
        notes.append(f"no text extractor ({exc}); agent will see this file as binary")
        return {"original": target, "sidecar": None, "notes": notes}
    except (OSError, ValueError) as exc:
        notes.append(f"extraction failed ({exc}); agent will see this file as binary")
        return {"original": target, "sidecar": None, "notes": notes}

    notes.append(f"extracted {len(result.text):,} chars ({result.kind})")
    notes.extend(result.warnings)
    if result.kind in _TEXT_NATIVE_KINDS:
        notes.append("agent reads this format directly; no sidecar written")
        return {"original": target, "sidecar": None, "notes": notes}

    text = result.text
    if len(text) > _SIDECAR_MAX_CHARS:
        notes.append(
            f"sidecar truncated to {_SIDECAR_MAX_CHARS:,} of {len(text):,} chars; "
            "see the original for the rest"
        )
        text = text[:_SIDECAR_MAX_CHARS]

    sidecar = target.with_name(target.name + ".txt")
    meta = ", ".join(f"{k}={v}" for k, v in result.meta.items())
    header = (
        f"# Extracted text: {target.name}\n"
        f"# kind={result.kind}"
        + (f" ({meta})" if meta else "")
        + "\n# Regenerated from the original on every import; do not edit.\n\n"
    )
    sidecar.write_text(header + text, encoding="utf-8")
    notes.append(f"sidecar: inputs/{sidecar.name} — read this file, not the original")
    return {"original": target, "sidecar": sidecar, "notes": notes}
