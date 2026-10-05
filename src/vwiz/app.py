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

import subprocess

import streamlit as st

from vwiz import store
from vwiz.config import get_settings
from vwiz.models import Chat, Message, Role

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
            _render_transcript(chat)
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
def _render_transcript(chat: Chat) -> None:
    """Scrollable message history. Stays pinned to the bottom on new messages."""
    if not chat.messages:
        st.markdown("### Ask for a visualization")
        st.caption(
            "Describe what you want to see, or attach PDFs and ask the agent to work from them."
        )
        _render_suggestions()
        return

    for message in chat.messages:
        with st.chat_message("user" if message.role is Role.USER else "assistant"):
            st.markdown(message.content)
            if message.attachments:
                _render_attachments(message.attachments)


def _render_input(chat: Chat, settings) -> None:
    """The composer, outside the scroll container so it never scrolls away."""
    prompt = st.chat_input(
        "Ask for a visualization, or attach documents",
        accept_file="multiple",
        file_type=["pdf"],
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
        st.caption(f"📎 {path.name}")


def _handle_submit(chat: Chat, settings, prompt) -> None:
    # A suggestion pill arrives as a bare string, so it has no .text/.files.
    text = (prompt.text if hasattr(prompt, "text") else str(prompt)) or ""
    files = getattr(prompt, "files", None) or []

    attachments = []
    for uploaded in files:
        path = _save_upload(uploaded, settings, chat.id)
        attachments.append(path)
        if path not in chat.documents:
            chat.documents.append(path)

    # An attachment-only turn still needs a bubble to hang the files off.
    body = text if text.strip() else f"📎 {len(attachments)} file(s) attached"
    chat.messages.append(Message(role=Role.USER, content=body, attachments=attachments))
    # First real message names the chat, which is all the sidebar shows.
    if chat.title == "New chat" and text.strip():
        chat.title = " ".join(text.split())[:40]

    # TODO(agent): call the Gemini agent. Stubbed until it lands — it should
    # stream tokens here, set chat.code, and return a render URL.
    chat.messages.append(
        Message(
            role=Role.AGENT,
            content=(
                "Agent not wired yet. Received your message"
                + (f" and {len(attachments)} attachment(s)." if attachments else ".")
            ),
        )
    )
    store.save(chat, settings)
    st.rerun()


def _save_upload(uploaded, settings, chat_id):
    """Persist an upload under a server-generated filename."""
    import re
    import uuid
    from pathlib import Path

    if uploaded.size > settings.max_upload_bytes:
        st.error(
            f"{uploaded.name} exceeds the {settings.max_upload_bytes // 1024 // 1024}MB limit."
        )
        st.stop()

    # Client-supplied names are untrusted: keep the basename, drop directory
    # components and anything outside a conservative character set.
    base = Path(uploaded.name or "").name
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", base).strip("._") or "upload.pdf"
    safe = safe[:120]

    target_dir = settings.uploads_dir / chat_id
    target_dir.mkdir(parents=True, exist_ok=True)
    target = target_dir / f"{uuid.uuid4().hex[:8]}_{safe}"
    target.write_bytes(uploaded.getvalue())
    return target


# --------------------------------------------------------------------------- #
# Right: render preview over generated code
# --------------------------------------------------------------------------- #
def _render_inspector(chat: Chat, settings) -> None:
    """Render preview stacked over generated code, as a bordered pseudo-table.

    A plain stacked pair of containers reads as loose cards. Nesting both inside
    an outer border with `gap=None` and a header row gives the same content the
    look of a two-row table, which matches how the panes relate: one artefact,
    shown two ways.
    """
    with st.container(border=True, gap=None):
        head_left, head_right = st.columns([1, 1], gap="small")
        with head_left:
            st.markdown("**Render**")
            st.caption(f"quick draft · {settings.preview_quality} · {settings.preview_fps}fps")
        with head_right:
            st.markdown("**Code**")
            st.caption(chat.code_filename or "scene.py")

        st.divider()

        render_left, code_right = st.columns([1, 1], gap="medium")
        with render_left:
            _render_preview(chat, settings)
        with code_right:
            _render_code(chat)


def _render_preview(chat: Chat, settings) -> None:
    st.caption(f"Quick draft · {settings.preview_quality} · {settings.preview_fps}fps")

    if chat.video_path and chat.video_path.exists():
        st.video(str(chat.video_path))
        return

    if chat.code:
        st.info(
            "No preview yet. The render node is not wired up — this pane will "
            "show a fast low-quality draft here, with the final render on demand."
        )
    else:
        st.info("Generated Manim code will preview here.")

    if not _docker_ready():
        st.caption("⚠️ Docker socket unavailable, so rendering cannot start.")


def _render_code(chat: Chat) -> None:
    if chat.code:
        with st.container(key="code_pane"):
            st.code(chat.code, language="python")
        st.download_button(
            "Download .py",
            data=chat.code,
            file_name=chat.code_filename or "scene.py",
            mime="text/x-python",
        )
        return

    st.info("Generated Manim code appears here.")


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
