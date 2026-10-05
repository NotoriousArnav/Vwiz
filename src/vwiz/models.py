"""Chat-centric data model.

Deliberately lean: the UI is a chat that produces a video, so a chat carries
messages, attached documents, the current generated code, and the render output.
The earlier storyboard/feedback scaffolding was cut — no speculative contracts
for an agent that does not exist yet.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path

from pydantic import BaseModel, Field


def _new_id() -> str:
    return uuid.uuid4().hex[:12]


class Role(StrEnum):
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class Message(BaseModel):
    """One turn in the conversation."""

    id: str = Field(default_factory=_new_id)
    role: Role
    content: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    # Sanitized, server-generated filenames. Never client-supplied names.
    attachments: list[Path] = Field(default_factory=list)


class Chat(BaseModel):
    """A conversation and the artefact it is producing."""

    id: str = Field(default_factory=_new_id)
    title: str = "New chat"
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    messages: list[Message] = Field(default_factory=list)
    documents: list[Path] = Field(default_factory=list)

    # Right-hand panel state.
    code: str | None = None
    code_filename: str | None = None
    video_path: Path | None = None

    @property
    def preview(self) -> str:
        """Sidebar subtitle: first user message, else a placeholder."""
        for message in self.messages:
            if message.role is Role.USER and message.content.strip():
                text = " ".join(message.content.split())
                return text[:48] + ("…" if len(text) > 48 else "")
        return "No messages yet"


class ChatSummary(BaseModel):
    """Lightweight sidebar row — avoids loading full chats."""

    id: str
    title: str
    updated_at: datetime
    message_count: int
    preview: str
