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

_STYLES = """
<style>
.st-key-preview_pane { border-radius: 8px; }
.st-key-code_pane textarea {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 0.8rem;
    line-height: 1.5;
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
        _render_chat(chat, settings)
    with _inspector_column:
        _render_inspector(chat, settings)


# --------------------------------------------------------------------------- #
# Sidebar: previous chats + settings
# --------------------------------------------------------------------------- #
def _sidebar(settings) -> None:
    st.markdown("## 🪄 Vwiz")

    if st.button("＋ New chat", type="primary", use_container_width=True):
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
            use_container_width=True,
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
    if st.button("⚙️ Settings", use_container_width=True):
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
def _render_chat(chat: Chat, settings) -> None:
    for message in chat.messages:
        with st.chat_message("user" if message.role is Role.USER else "assistant"):
            st.markdown(message.content)
            if message.attachments:
                _render_attachments(message.attachments)

    prompt = st.chat_input(
        "Ask for a visualization, or attach documents",
        accept_file="multiple",
        file_type=["pdf"],
    )
    if prompt:
        _handle_submit(chat, settings, prompt)


def _render_attachments(paths) -> None:
    for path in paths:
        st.caption(f"📎 {path.name}")


def _handle_submit(chat: Chat, settings, prompt) -> None:
    attachments = []
    for uploaded in getattr(prompt, "files", []) or []:
        path = _save_upload(uploaded, settings, chat.id)
        attachments.append(path)
        if path not in chat.documents:
            chat.documents.append(path)

    chat.messages.append(Message(role=Role.USER, content=str(prompt.text), attachments=attachments))
    # First real message names the chat, which is all the sidebar shows.
    if chat.title == "New chat" and prompt.text.strip():
        chat.title = " ".join(str(prompt.text).split())[:40]

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
    st.markdown("### Render")

    with st.container(key="preview_pane", border=True):
        _render_preview(chat, settings)

    st.markdown("### Code")

    with st.container(key="code_pane", border=True):
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
        st.caption(chat.code_filename or "scene.py")
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
