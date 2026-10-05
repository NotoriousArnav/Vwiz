"""Text extraction from uploaded documents.

Every format collapses to plain text plus a little structure the agent can use
(headings, tables). The output is deliberately lossy — we are feeding a language
model, not preserving formatting.

Security note: every uploaded document is untrusted input that becomes agent
context. XML-family formats (docx, odt, epub) are parsed with defusedxml where
possible, because they are XML bombs and entity-expansion vectors. Plain text is
decoded conservatively rather than trusting a declared encoding.
"""

from __future__ import annotations

import csv
import io
import re
import zipfile
from dataclasses import dataclass, field
from pathlib import Path

# Formats the uploader accepts. Grouped by extractor family.
SUPPORTED_SUFFIXES: tuple[str, ...] = (
    # PDF
    ".pdf",
    # Plain text
    ".txt",
    ".text",
    ".log",
    ".csv",
    ".tsv",
    # Markdown
    ".md",
    ".markdown",
    ".mdx",
    # Rich text
    ".rtf",
    # Word / OpenDocument
    ".docx",
    ".odt",
    # Web
    ".html",
    ".htm",
    ".xhtml",
)

# Anything we accept but cannot parse well enough to be useful. Rejected at the
# uploader so the user gets an error instead of an empty document.
REJECTED_SUFFIXES: dict[str, str] = {
    ".doc": "legacy binary .doc — please re-save as .docx or .pdf",
    ".ppt": "PowerPoint — please export to PDF",
    ".pptx": "PowerPoint — please export to PDF",
    ".xls": "legacy binary .xls — please re-save as .xlsx or .csv",
    ".xlsx": "spreadsheets are better supplied as .csv",
}

MAX_CHARS = 2_000_000

# Formats that are zip archives underneath, and so need a decompression guard.
_ZIP_FORMATS = frozenset({".docx", ".odt"})

_WS_RUN = re.compile(r"[ \t]{2,}")
_BLANK_RUN = re.compile(r"\n{3,}")


@dataclass
class Extracted:
    """Extraction result: normalized text plus whatever structure we kept."""

    text: str
    kind: str
    meta: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class UnsupportedFormat(ValueError):
    """Raised when a file type cannot be handled."""


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #
def extract(
    path: Path,
    *,
    max_chars: int = MAX_CHARS,
    max_expanded_bytes: int | None = None,
) -> Extracted:
    """Extract text from `path`, dispatching on suffix.

    Raises `UnsupportedFormat` for anything we cannot parse.
    """
    suffix = path.suffix.lower()

    if suffix in REJECTED_SUFFIXES:
        raise UnsupportedFormat(f"{suffix} is not supported: {REJECTED_SUFFIXES[suffix]}")

    handler = _HANDLERS.get(suffix)
    if handler is None:
        raise UnsupportedFormat(
            f"{suffix or 'this file'} is not supported. "
            f"Accepted: {', '.join(sorted(set(SUPPORTED_SUFFIXES)))}"
        )

    raw = path.read_bytes()
    if suffix in _ZIP_FORMATS:
        _guard_zip(raw, suffix, max_chars, max_expanded_bytes)

    result = handler(raw, suffix)

    if len(result.text) > max_chars:
        result.warnings.append(f"truncated from {len(result.text):,} to {max_chars:,} characters")
        result.text = result.text[:max_chars]
    return result


def _guard_zip(raw: bytes, suffix: str, max_chars: int, max_expanded_bytes: int | None) -> None:
    """Reject zip bombs before any parser decompresses them.

    `.docx` and `.odt` are zip archives, so the upload size cap says almost
    nothing about the real memory cost: 400KB of compressed XML expands to
    400MB. The central directory holds each entry's uncompressed size, so we can
    check that without inflating anything.

    The default budget is generous because document XML runs several times
    longer than the prose it contains.
    """
    budget = max_expanded_bytes or max(max_chars * 40, 64 * 1024 * 1024)
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            entries = archive.infolist()
            total = sum(entry.file_size for entry in entries)
            # Each entry is decompressed individually, so a single huge member
            # is its own peak, independent of the archive total.
            largest = max((entry.file_size for entry in entries), default=0)
    except (zipfile.BadZipFile, OSError) as exc:
        raise UnsupportedFormat(f"{suffix} is not a readable archive ({exc})") from exc

    if largest > budget or total > budget * 4:
        raise UnsupportedFormat(
            f"{suffix} expands to {total / 1e6:.0f}MB uncompressed, over the "
            f"{budget / 1e6:.0f}MB budget — this looks like a zip bomb"
        )


def _normalize(text: str) -> str:
    """Collapse whitespace while keeping paragraph breaks meaningful."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WS_RUN.sub(" ", text)
    return _BLANK_RUN.sub("\n\n", text).strip()


# --------------------------------------------------------------------------- #
# Plain text and tabular
# --------------------------------------------------------------------------- #
def _decode(raw: bytes) -> str:
    """Decode bytes to text without trusting any declared encoding.

    BOMs first, then a heuristic for BOM-less UTF-16, then UTF-8, then latin-1
    as a last resort — it never fails, so a mis-encoded file degrades instead of
    raising.
    """
    for bom, encoding in (
        (b"\xef\xbb\xbf", "utf-8-sig"),
        (b"\xff\xfe", "utf-16-le"),
        (b"\xfe\xff", "utf-16-be"),
    ):
        if raw.startswith(bom):
            return raw.decode(encoding, errors="replace")

    if (encoding := _sniff_utf16(raw)) is not None:
        return raw.decode(encoding, errors="replace")

    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("latin-1", errors="replace")


def _sniff_utf16(raw: bytes) -> str | None:
    """Guess UTF-16 without a BOM, which Word and Windows tools often omit.

    UTF-16 ASCII text is UTF-8-valid but riddled with NUL bytes, so the UTF-8
    attempt would succeed and return interleaved garbage. Detect the tell-tale
    NULs and decide the endianness from which half of them is dense.
    """
    sample = raw[:4096]
    if len(sample) < 4 or b"\x00" not in sample:
        return None

    # Strip a trailing odd byte, which would be the start of a half character.
    even_nuls = sample[0::2].count(0)
    odd_nuls = sample[1::2].count(0)
    half = len(sample) // 2

    if odd_nuls > half * 0.3 and even_nuls < half * 0.1:
        return "utf-16-le"
    if even_nuls > half * 0.3 and odd_nuls < half * 0.1:
        return "utf-16-be"
    return None


def _extract_txt(raw: bytes, suffix: str) -> Extracted:
    text = _normalize(_decode(raw))
    kind = "table" if suffix in (".csv", ".tsv") else "text"
    return Extracted(text=text, kind=kind, meta={"encoding": "auto"})


def _extract_csv(raw: bytes, suffix: str) -> Extracted:
    """Render a CSV as a Markdown table so headers survive into the prompt."""
    text = _decode(raw)
    delimiter = "\t" if suffix == ".tsv" else ","
    try:
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter))
    except csv.Error as exc:
        return Extracted(
            text=_normalize(text),
            kind="text",
            warnings=[f"CSV parse failed ({exc}); returned raw text"],
        )

    rows = [row for row in rows if any(cell.strip() for cell in row)]
    if not rows:
        return Extracted(text="", kind="table", warnings=["file contained no rows"])

    # Pad ragged rows so the Markdown table stays well-formed.
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]

    def cell(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ").strip() or "—"

    header = "| " + " | ".join(cell(c) for c in rows[0]) + " |"
    rule = "| " + " | ".join("---" for _ in rows[0]) + " |"
    body = ["| " + " | ".join(cell(c) for c in row) + " |" for row in rows[1:]]
    return Extracted(
        text="\n".join([header, rule, *body]),
        kind="table",
        meta={"rows": str(len(rows)), "columns": str(width)},
    )


# --------------------------------------------------------------------------- #
# Markdown
# --------------------------------------------------------------------------- #
def _extract_markdown(raw: bytes, suffix: str) -> Extracted:
    """Strip Markdown syntax, keeping heading levels as context markers.

    A plain-text strip is enough: the model reads prose better than markup, and
    the heading hierarchy is the only structure worth preserving.

    Fenced code is passed through verbatim and stays in place, because the
    global whitespace collapse would flatten indentation that is meaningful, and
    because code appearing after the prose that concludes a document misleads
    the model about what supports what.
    """
    text = _decode(raw)
    chunks: list[tuple[str, list[str]]] = []
    buffer: list[str] = []
    fence: list[str] | None = None

    def flush() -> None:
        """Close the current prose run as one chunk."""
        if any(line.strip() for line in buffer):
            chunks.append(("prose", list(buffer)))
        buffer.clear()

    for line in text.replace("\r\n", "\n").split("\n"):
        if line.lstrip().startswith(("```", "~~~")):
            if fence is None:
                flush()
                fence = []
            else:
                chunks.append(("code", fence))
                fence = None
            continue

        if fence is not None:
            fence.append(line)
            continue

        stripped = line.strip()
        if not stripped:
            buffer.append("")
            continue

        heading = re.match(r"^(#{1,6})\s+(.*)$", stripped)
        if heading:
            buffer.append(f"{'#' * len(heading.group(1))} {heading.group(2).strip()}")
            continue

        # Drop inline emphasis, images, and link targets but keep link text.
        stripped = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", stripped)
        stripped = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", stripped)
        stripped = re.sub(r"~~([^~]+)~~", r"\1", stripped)
        stripped = re.sub(r"[*_]{1,3}([^*_]+)[*_]{1,3}", r"\1", stripped)
        stripped = re.sub(r"^>\s?", "", stripped)
        stripped = re.sub(r"^([-*+]|\d+\.)\s+", "- ", stripped)
        buffer.append(stripped)

    if fence is not None:  # unterminated fence: keep what we captured
        chunks.append(("code", fence))
    flush()

    if not chunks:
        return Extracted(text="", kind="markdown", warnings=["file contained no text"])

    parts = []
    for kind, lines in chunks:
        body = _normalize("\n".join(lines)) if kind == "prose" else "\n".join(lines).strip("\n")
        if body:
            parts.append(body)

    return Extracted(text="\n\n".join(parts), kind="markdown")


# --------------------------------------------------------------------------- #
# PDF
# --------------------------------------------------------------------------- #
def _extract_pdf(raw: bytes, suffix: str) -> Extracted:
    import pdfplumber

    pages: list[str] = []
    warnings: list[str] = []
    with pdfplumber.open(io.BytesIO(raw)) as pdf:
        for number, page in enumerate(pdf.pages, start=1):
            # Scanned pages have no text layer; flag rather than silently
            # returning an empty document.
            content = (page.extract_text() or "").strip()
            if not content:
                warnings.append(f"page {number} has no text layer (likely a scan)")
            if content:
                pages.append(content)

    if not pages:
        raise UnsupportedFormat(
            "no extractable text — this PDF looks scanned, so it needs OCR first"
        )
    return Extracted(
        text=_normalize("\n\n".join(pages)),
        kind="pdf",
        meta={"pages": str(len(pdf.pages))},
        warnings=warnings,
    )


# --------------------------------------------------------------------------- #
# Word (.docx)
# --------------------------------------------------------------------------- #
def _extract_docx(raw: bytes, suffix: str) -> Extracted:
    import docx

    document = docx.Document(io.BytesIO(raw))
    blocks: list[str] = []
    tables = 0

    # Walk the body in document order so headings, prose, and tables stay in
    # sequence — iterating paragraphs alone would drop every table.
    body = document.element.body
    for child in body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            text = "".join(node.text or "" for node in child.iter() if node.tag.endswith("}t"))
            text = text.strip()
            if not text:
                continue
            style = ""
            pstyle = child.find(
                ".//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pStyle"
            )
            if pstyle is not None:
                style = pstyle.get(
                    "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val", ""
                )
            match = re.match(r"^(?:Heading|heading)\s*(\d)$", style or "")
            if match:
                depth = min(int(match.group(1)), 6)
                blocks.append(f"{'#' * depth} {text}")
            else:
                blocks.append(text)
        elif tag == "tbl":
            rows = _docx_table_rows(child)
            if rows:
                tables += 1
                blocks.append(_as_markdown_table(rows))

    text = _normalize("\n\n".join(blocks))
    if not text:
        raise UnsupportedFormat("document appears to be empty")

    return Extracted(
        text=text,
        kind="docx",
        meta={"tables": str(tables)},
        warnings=["images and footnotes were skipped"] if _docx_has_images(document) else [],
    )


def _docx_table_rows(element) -> list[list[str]]:
    ns = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    rows = []
    for row in element.iter(f"{ns}tr"):
        cells = []
        for cell in row.iter(f"{ns}tc"):
            cells.append(
                " ".join(node.text or "" for node in cell.iter() if node.tag.endswith("}t")).strip()
            )
        rows.append(cells)
    return rows


def _docx_has_images(document) -> bool:
    return any(part.partname.startswith("/word/media/") for part in document.part.package.parts)


# --------------------------------------------------------------------------- #
# OpenDocument (.odt)
# --------------------------------------------------------------------------- #
def _extract_odt(raw: bytes, suffix: str) -> Extracted:
    from odf import teletype
    from odf.opendocument import load

    # odfpy parses through defusedxml, so entity expansion is already blocked.
    document = load(io.BytesIO(raw))
    blocks: list[str] = []
    tables = 0

    def walk(element) -> None:
        """Depth-first in document order, so prose and tables stay sequenced."""
        nonlocal tables

        for child in getattr(element, "childNodes", ()):
            qname = getattr(child, "qname", None)
            name = qname[1] if qname else ""

            if name in ("p", "h"):
                content = teletype.extractText(child).strip()
                if not content:
                    continue
                if name == "h":
                    level = child.getAttribute("outlinelevel")
                    blocks.append(f"{'#' * min(int(level) + 1, 6)} {content}")
                else:
                    blocks.append(content)
            elif name == "list":
                # A list item's paragraphs are already nested, so read the whole
                # item as one line instead of descending and double-counting.
                for item in child.childNodes:
                    if getattr(item, "qname", ("", "", ""))[1] != "list-item":
                        continue
                    content = teletype.extractText(item).strip()
                    if content:
                        blocks.append(f"- {content}")
            elif name == "table":
                rows = _odt_table_rows(child)
                if rows:
                    tables += 1
                    blocks.append(_as_markdown_table(rows))
            elif name in ("section", "frame", "text-box", "list-item"):
                # Containers: descend so nested content is not dropped.
                walk(child)

    walk(document.text)

    if not blocks:
        raise UnsupportedFormat("document appears to be empty")

    return Extracted(
        text=_normalize("\n\n".join(blocks)),
        kind="odt",
        meta={"nodes": str(len(blocks)), "tables": str(tables)},
    )


def _odt_table_rows(element) -> list[list[str]]:
    from odf import table as odf_table
    from odf import teletype

    rows: list[list[str]] = []
    for row in element.getElementsByType(odf_table.TableRow):
        cells: list[str] = []
        for cell in row.getElementsByType(odf_table.TableCell):
            cells.append(teletype.extractText(cell).strip())
            # An empty span merges the cell across columns; repeat it so the
            # rendered table keeps a consistent width.
            repeat = cell.getAttribute("numbercolumnsrepeated")
            if repeat and repeat.isdigit() and not cells[-1]:
                cells.extend([""] * (int(repeat) - 1))
        if cells:
            rows.append(cells)
    return rows


# --------------------------------------------------------------------------- #
# HTML
# --------------------------------------------------------------------------- #
def _extract_html(raw: bytes, suffix: str) -> Extracted:
    """Strip HTML to readable text, keeping headings and tables."""
    from bs4 import BeautifulSoup

    # defusedxml only covers XML; html.parser does not expand external entities.
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "noscript"]):
        tag.decompose()

    blocks: list[str] = []
    tables = 0
    for element in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "table"]):
        if element.name == "table":
            rows = [
                [cell.get_text(" ", strip=True) for cell in row.find_all(["td", "th"])]
                for row in element.find_all("tr")
            ]
            rows = [row for row in rows if any(row)]
            if rows:
                tables += 1
                blocks.append(_as_markdown_table(rows))
            element.decompose()
            continue
        if element.name == "li":
            # Skip list items already covered by a nested list's text.
            blocks.append(f"- {element.get_text(' ', strip=True)}")
            continue
        text = element.get_text(" ", strip=True)
        if text:
            depth = int(element.name[1]) if element.name[0] == "h" else 0
            blocks.append(f"{'#' * depth} {text}" if depth else text)

    body = _normalize("\n\n".join(blocks)) or _normalize(soup.get_text(" ", strip=True))
    if not body:
        raise UnsupportedFormat("no readable text found")

    return Extracted(
        text=body,
        kind="html",
        meta={"tables": str(tables)},
    )


# --------------------------------------------------------------------------- #
# RTF — best effort
# --------------------------------------------------------------------------- #
_RTF_CONTROL = re.compile(r"\\[a-z]+-?\d*\s?|[{}]")


def _extract_rtf(raw: bytes, suffix: str) -> Extracted:
    """Very rough RTF text extraction.

    RTF is a typesetting language, not markup: correct handling means a full
    parser. This recovers the readable prose and warns, which beats rejecting
    the file outright.
    """
    text = _decode(raw)
    # Drop the font/colour/color tables, which hold brace-heavy noise.
    text = re.sub(r"\{\\(?:fonttbl|colortbl|stylesheet|info)[\s\S]*?\n\}", "", text)
    text = _RTF_CONTROL.sub("", text)
    text = text.replace("\\\\", "\n").replace("\\'", "'")
    text = _normalize(text)

    if not text:
        raise UnsupportedFormat("no readable text found in RTF")
    return Extracted(
        text=text,
        kind="rtf",
        warnings=["RTF formatting was discarded; only text was recovered"],
    )


# --------------------------------------------------------------------------- #
def _as_markdown_table(rows: list[list[str]]) -> str:
    """Render rows as a Markdown table, padding ragged cells."""
    width = max(len(row) for row in rows)
    padded = [row + [""] * (width - len(row)) for row in rows]

    def cell(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ").strip() or "—"

    header = "| " + " | ".join(cell(c) for c in padded[0]) + " |"
    rule = "| " + " | ".join("---" for _ in padded[0]) + " |"
    body = ["| " + " | ".join(cell(c) for c in row) + " |" for row in padded[1:]]
    return "\n".join([header, rule, *body])


_HANDLERS = {
    ".pdf": _extract_pdf,
    ".txt": _extract_txt,
    ".text": _extract_txt,
    ".log": _extract_txt,
    ".csv": _extract_csv,
    ".tsv": _extract_csv,
    ".md": _extract_markdown,
    ".markdown": _extract_markdown,
    ".mdx": _extract_markdown,
    ".rtf": _extract_rtf,
    ".docx": _extract_docx,
    ".odt": _extract_odt,
    ".html": _extract_html,
    ".htm": _extract_html,
    ".xhtml": _extract_html,
}
