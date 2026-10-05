"""Chat persistence.

Streamlit reruns the whole script on every interaction and `st.session_state`
does not survive a browser refresh, so chats live on disk. Writes are atomic
(temp file + rename) because a truncated `chat.json` would silently lose the
conversation.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from vwiz.config import Settings
from vwiz.models import Chat, ChatSummary

_CHAT_FILE = "chat.json"


def chat_dir(chat_id: str, settings: Settings) -> Path:
    return settings.projects_dir / chat_id


def save(chat: Chat, settings: Settings) -> Path:
    """Persist a chat atomically. Returns the written path."""
    chat.updated_at = datetime_now()

    directory = chat_dir(chat.id, settings)
    directory.mkdir(parents=True, exist_ok=True)

    target = directory / _CHAT_FILE
    tmp = directory / f"{_CHAT_FILE}.tmp"
    tmp.write_text(chat.model_dump_json(indent=2), encoding="utf-8")
    tmp.replace(target)
    return target


def datetime_now():  # noqa: ANN202 - tiny indirection keeps the import local
    from datetime import UTC, datetime

    return datetime.now(UTC)


def load(chat_id: str, settings: Settings) -> Chat | None:
    """Load one chat, or None if missing or unreadable."""
    path = chat_dir(chat_id, settings) / _CHAT_FILE
    if not path.exists():
        return None
    try:
        return Chat.model_validate_json(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError, ValueError:
        # A corrupt file surfaces as absent rather than killing the app.
        return None


def list_summaries(settings: Settings) -> list[ChatSummary]:
    """All saved chats, most recently updated first."""
    summaries: list[ChatSummary] = []
    if not settings.projects_dir.exists():
        return summaries

    for directory in settings.projects_dir.iterdir():
        if not directory.is_dir():
            continue
        chat = load(directory.name, settings)
        if chat is None:
            continue
        summaries.append(
            ChatSummary(
                id=chat.id,
                title=chat.title,
                updated_at=chat.updated_at,
                message_count=len(chat.messages),
                preview=chat.preview,
            )
        )

    return sorted(summaries, key=lambda s: s.updated_at, reverse=True)


def create(settings: Settings) -> Chat:
    """Create and persist a fresh chat."""
    chat = Chat()
    save(chat, settings)
    return chat


def delete(chat_id: str, settings: Settings) -> None:
    """Remove a chat and its uploads.

    Scoped to the chat's own subdirectory: a crafted id cannot escape the base.
    """
    for base in (settings.projects_dir, settings.uploads_dir):
        target = base / chat_id
        if target.is_dir() and target.resolve().parent == base.resolve():
            shutil.rmtree(target, ignore_errors=True)
