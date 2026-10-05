"""Vwiz frontend entrypoint.

Three columns, left to right:

1. Streamlit's own sidebar — previous chats plus a settings button.
2. The chat window — talk to the agent, or attach documents.
3. Split vertically: a fast low-quality render preview on top, the generated
   code beneath it.

Chats persist to disk rather than `st.session_state`, which does not survive a
browser refresh.
"""

from __future__ import annotations

import ast
import re
import subprocess
import uuid
from pathlib import Path

import streamlit as st

from vwiz import llm, store
from vwiz.config import get_settings
from vwiz.models import Chat, Message, Role

# Filenames arriving from a client are untrusted.
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")

st.set_page_config(page_title="Vwiz", page_icon="🪄", layout="wide")

# Height of the two main panes, in pixels. Fixed so the transcript scrolls
# internally instead of growing the page; the inspector matches it so the
# columns stay flush.
_PANE_HEIGHT = 640

# The code pane is narrow, so tighten the block font and let long lines wrap
# instead of forcing a horizontal scrollbar inside an already-scrolling pane.
_STYLES = """
<style>
.st-key-code_pane pre code {
    font-size: 0.72rem;
    line-height: 1.45;
    white-space: pre-wrap;
    word-break: break-word;
}
</style>
"""


# --------------------------------------------------------------------------- #
# Layout
# --------------------------------------------------------------------------- #
def main() -> None:
    settings = get_settings()
    settings.ensure_dirs()
    st.markdown(_STYLES, unsafe_allow_html=True)

    with st.sidebar:
        _sidebar(settings)

    _chat_column, _inspector_column = st.columns([1.15, 1], gap="medium")

    chat = _active_chat(settings)
    with _chat_column:
        # A fixed-height container gives the transcript its own scroll area, so
        # the page never grows past the viewport. `autoscroll` keeps the newest
        # message in view, which is what makes the pane feel anchored to the
        # bottom rather than the top.
        with st.container(height=_PANE_HEIGHT, autoscroll=True):
            _render_transcript(chat, settings)
        _render_input(chat, settings)

    with _inspector_column, st.container(height=_PANE_HEIGHT):
        _render_inspector(chat, settings)


# --------------------------------------------------------------------------- #
# Sidebar: previous chats + settings
# --------------------------------------------------------------------------- #
def _sidebar(settings) -> None:
    st.markdown("## 🪄 Vwiz")

    if st.button("＋ New chat", type="primary", width="stretch"):
        st.session_state.chat = store.create(settings)
        st.session_state.pop("settings_open", None)
        st.rerun()

    st.markdown("**Previous chats**")
    summaries = store.list_summaries(settings)
    if not summaries:
        st.caption("No saved chats yet.")
        return

    active_id = _active_chat(settings).id
    for summary in summaries:
        is_active = summary.id == active_id
        label = f"{'▸ ' if is_active else ''}{summary.title}"
        cols = st.columns([5, 1])
        if cols[0].button(
            label,
            key=f"open_{summary.id}",
            width="stretch",
            type="primary" if is_active else "secondary",
            help=summary.preview,
        ):
            loaded = store.load(summary.id, settings)
            if loaded is not None:
                st.session_state.chat = loaded
                st.rerun()
        if cols[1].button("✕", key=f"del_{summary.id}", help="Delete chat", disabled=is_active):
            store.delete(summary.id, settings)
            st.rerun()

    st.divider()
    if st.button("⚙️ Settings", width="stretch"):
        st.session_state.settings_open = True


@st.dialog("Settings", width="large")
def _settings_dialog() -> None:
    settings = get_settings()
    st.caption("Changes apply to new work. Credentials are read from `.env`.")

    st.markdown("**Model**")
    st.text_input("Agent model", settings.gemini_agent_model, disabled=True)
    st.text_input("Fast model", settings.gemini_fast_model, disabled=True)

    st.markdown("**Voice**")
    st.text_input("Chirp 3 voice", settings.tts_voice, disabled=True)
    st.slider("Speaking rate", 0.25, 2.0, settings.tts_speaking_rate, 0.05, disabled=True)

    st.markdown("**Render**")
    cols = st.columns(2)
    cols[0].text_input("Render node", settings.render_node_url, disabled=True)
    cols[1].text_input("Preview quality", settings.preview_quality, disabled=True)

    st.markdown("**Cost guards**")
    guards = st.columns(3)
    guards[0].metric("Max scenes", settings.max_scenes)
    guards[1].metric("Max duration", f"{settings.max_total_duration_s:.0f}s")
    guards[2].metric("Max attempts", settings.max_render_attempts)

    st.divider()
    missing = settings.missing_credentials()
    if missing:
        st.warning(f"Not configured: {', '.join(missing)}")
    else:
        st.success("Credentials present.")

    if st.button("Close", type="primary"):
        st.rerun()


# --------------------------------------------------------------------------- #
# Centre: chat window
# --------------------------------------------------------------------------- #
def _render_transcript(chat: Chat, settings) -> None:
    """Scrollable message history. Stays pinned to the bottom on new messages."""
    if not chat.messages:
        st.markdown("### Ask for a visualization")
        st.caption(
            "Describe what you want to see, or attach documents and ask the agent "
            "to work from them."
        )
        _render_suggestions()
        return

    # Confirms what actually parsed out of the attachments, so a silently empty
    # extraction is visible instead of just producing a confused agent later.
    notes = st.session_state.get("upload_notes") or []
    if notes:
        with st.popover(f":material/checklist: {len(notes)} file(s) read"):
            for note in notes:
                st.caption(note)

    for message in chat.messages:
        with st.chat_message("user" if message.role is Role.USER else "assistant"):
            st.markdown(message.content)
            if message.attachments:
                _render_attachments(message.attachments)

    # A pending LLM reply is produced here, inside the transcript container, so
    # autoscroll follows the stream. It lives here rather than in _handle_submit
    # because the transcript is drawn before the composer renders the turn.
    if st.session_state.pop("pending_reply", False):
        _stream_agent_reply(chat, settings)


def _stream_agent_reply(chat: Chat, settings) -> None:
    """Generate the agent reply with streaming, then persist it.

    The model streams its JSON turn raw, then we parse it out: the `text` field
    becomes the stored assistant message, and a valid Manim scene in `code` is
    surfaced to the Code pane after a syntax check. A transient raw JSON bubble
    shows during generation; the rerun replaces it with the parsed prose and the
    code appears in its pane.
    """
    try:
        with st.chat_message("assistant"):
            reply = st.write_stream(llm.stream_reply(chat.messages, settings))
        raw = reply if isinstance(reply, str) else "".join(str(part) for part in reply)
    except Exception as exc:
        # Surface the failure as a normal chat bubble rather than a crash.
        chat.messages.append(
            Message(role=Role.AGENT, content=f"⚠️ Could not reach the model: {exc}")
        )
        if chat.title == "New chat":
            _set_ai_title(chat, settings)
        store.save(chat, settings)
        st.rerun()
        return

    text, code = llm.parse_reply(raw)

    if code is not None:
        # Phase 2 guarantee: nothing broken enters the Code pane. A failed parse
        # leaves the last good scene in place and tells the user why.
        try:
            ast.parse(code)
            chat.code = code
            chat.code_filename = "scene.py"
        except SyntaxError as exc:
            text = f"{text}\n\n⚠️ The generated scene failed a syntax check and was not saved: {exc}"
            code = None

    chat.messages.append(Message(role=Role.AGENT, content=text))
    if chat.title == "New chat":
        _set_ai_title(chat, settings)
    store.save(chat, settings)
    st.rerun()


def _set_ai_title(chat: Chat, settings) -> None:
    """Name the chat from a short model-generated title, not the raw prompt."""
    first_user = next(
        (m.content for m in chat.messages if m.role is Role.USER and m.content.strip()),
        "",
    )
    if not first_user:
        return
    try:
        chat.title = llm.make_title(first_user, settings)
    except Exception:
        chat.title = " ".join(first_user.split())[:40]


def _render_input(chat: Chat, settings) -> None:
    """The composer, outside the scroll container so it never scrolls away."""
    prompt = st.chat_input(
        "Ask for a visualization, or attach documents",
        accept_file="multiple",
        file_type=settings.accepted_upload_types,
        max_upload_size=settings.max_upload_bytes,
    )
    # A suggestion pill stashes its text here, since st.chat_input only returns
    # a value on real keyboard/file submission.
    prompt = prompt or st.session_state.pop("pending_prompt", None)

    if prompt:
        _handle_submit(chat, settings, prompt)


_SUGGESTIONS = {
    ":material/movie: Explain eigenvectors visually": (
        "Explain what an eigenvector is, with an animation that shows a vector "
        "keeping its direction as the matrix scales it."
    ),
    ":material/upload_file: Turn my notes into a video": (
        "Read the attached notes and turn the key ideas into a short explainer."
    ),
    ":material/function: Show me a proof as an animation": (
        "Animate a proof of the Pythagorean theorem step by step."
    ),
}


def _render_suggestions() -> None:
    """Clickable openers, shown only while the chat is empty."""
    chosen = st.pills(
        "Try asking:",
        list(_SUGGESTIONS),
        selection_mode="single",
        label_visibility="collapsed",
        key="suggestion",
    )
    if chosen:
        st.session_state["pending_prompt"] = _SUGGESTIONS[chosen]
        st.session_state.pop("suggestion", None)
        st.rerun()


def _render_attachments(paths) -> None:
    for path in paths:
        st.caption(f":material/attach_file: {path.name}")


def _handle_submit(chat: Chat, settings, prompt) -> None:
    # A suggestion pill arrives as a bare string, so it has no .text/.files.
    text = (prompt.text if hasattr(prompt, "text") else str(prompt)) or ""
    files = getattr(prompt, "files", None) or []

    # Extraction notes belong to the turn being submitted, not the whole session.
    st.session_state["upload_notes"] = []

    attachments = []
    rejected = 0
    for uploaded in files:
        path = _save_upload(uploaded, settings, chat.id)
        if path is None:
            rejected += 1
            continue
        attachments.append(path)
        if path not in chat.documents:
            chat.documents.append(path)

    # An attachment-only turn still needs a bubble to hang the files off.
    body = text if text.strip() else f"📎 {len(attachments)} file(s) attached"
    chat.messages.append(Message(role=Role.USER, content=body, attachments=attachments))

    # The LLM reply is produced in _render_transcript so it can stream inside
    # the transcript's autoscrolling container. Signal it and rerun; the turn
    # resolves on the next render. On a fully rejected upload there is no model
    # call, so name the chat from the prompt text instead.
    if rejected:
        chat.messages.append(
            Message(
                role=Role.AGENT,
                content=f"{rejected} file(s) could not be read; see the error above.",
            )
        )
        st.session_state["pending_reply"] = False
        if chat.title == "New chat" and text.strip():
            chat.title = " ".join(text.split())[:40]
    else:
        st.session_state["pending_reply"] = True

    store.save(chat, settings)
    st.rerun()


def _save_upload(uploaded, settings, chat_id):
    """Validate and persist an upload, then confirm its text is extractable.

    Rejecting an unreadable file here means the user learns immediately, rather
    than after the agent reports that it found nothing to work with.
    """
    from vwiz import ingest

    base = Path(uploaded.name or "").name

    if uploaded.size > settings.max_upload_bytes:
        st.error(f"{base} exceeds the {settings.max_upload_bytes // 1024 // 1024}MB limit.")
        return None

    try:
        # Client-supplied names are untrusted: keep the basename, drop directory
        # components, and strip anything outside a conservative character set.
        safe = _UNSAFE.sub("_", base).strip("._") or "upload.txt"
        safe = safe[:120]

        target_dir = settings.uploads_dir / chat_id
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{uuid.uuid4().hex[:8]}_{safe}"
        target.write_bytes(uploaded.getvalue())

        result = ingest.extract(
            target,
            max_chars=settings.max_document_chars,
            max_expanded_bytes=settings.max_archive_expanded_bytes,
        )
    except ingest.UnsupportedFormat as exc:
        st.error(f"{base}: {exc}")
        return None
    except (OSError, ValueError) as exc:
        st.error(f"{base}: could not be read ({exc}).")
        return None

    st.session_state.setdefault("upload_notes", []).append(
        f"{base}: {len(result.text):,} characters ({result.kind})"
        + (f" — {'; '.join(result.warnings)}" if result.warnings else "")
    )
    return target


# --------------------------------------------------------------------------- #
# Right: render preview over generated code
# --------------------------------------------------------------------------- #
def _render_inspector(chat: Chat, settings) -> None:
    """Render preview stacked over generated code, as a bordered pseudo-table.

    Each row is a canvas: a fixed-height frame that always takes its share of
    the column, holding either the result (video, code) or the status/error
    message for that stage. Empty panes therefore look like intentional
    placeholders rather than collapsed emptiness.
    """
    with st.container(border=True, gap=None):
        st.markdown("**Render**")
        with st.container(border=True, height=_CANVAS_HEIGHT):
            _render_preview(chat, settings)

        st.divider()

        st.markdown("**Code**")
        with st.container(key="code_pane", border=True, height=_CANVAS_HEIGHT):
            _render_code(chat)
        if chat.code:
            st.download_button(
                "Download .py",
                data=chat.code,
                file_name=chat.code_filename or "scene.py",
                mime="text/x-python",
            )


# Height of each preview/code canvas inside the inspector column.
_CANVAS_HEIGHT = 250


def _render_preview(chat: Chat, settings) -> None:
    if chat.video_path and chat.video_path.exists():
        st.video(str(chat.video_path))
        return

    if chat.code:
        st.info(
            "No preview yet. The render node is not wired up — this canvas will "
            "show a fast low-quality draft here, with the final render on demand."
        )
    elif not _docker_ready():
        st.error(
            "Docker socket unavailable — rendering cannot start. Add your user to "
            "the `docker` group and re-login."
        )
    else:
        st.info("Your rendered video will appear here.")


def _render_code(chat: Chat) -> None:
    if chat.code:
        st.code(chat.code, language="python")
        return

    st.info("The agent's generated Manim code will appear here.")


# --------------------------------------------------------------------------- #
def _active_chat(settings) -> Chat:
    """The chat bound to this session, creating one if needed."""
    chat = st.session_state.get("chat")
    if chat is None:
        chat = store.create(settings)
        st.session_state.chat = chat
    return chat


def _docker_ready() -> bool:
    """Probe the Docker socket once per session."""
    cached = st.session_state.get("docker_ok")
    if cached is not None:
        return bool(cached)
    try:
        result = subprocess.run(
            ["docker", "info", "--format", "{{.ServerVersion}}"],
            capture_output=True,
            timeout=10,
            check=False,
        )
        ok = result.returncode == 0
    except OSError, subprocess.SubprocessError:
        ok = False
    st.session_state.docker_ok = ok
    return ok


main()
