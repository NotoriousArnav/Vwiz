"""Store and model tests.

Focus on the persistence round-trip and the sanitising helpers, since those are
where a silent bug loses a conversation or lets a client-supplied name reach the
filesystem.
"""

from __future__ import annotations

import pytest

from vwiz import store
from vwiz.config import Settings
from vwiz.models import Chat, Message, Role


@pytest.fixture
def settings(tmp_path) -> Settings:
    return Settings(data_dir=tmp_path / "data")


# --------------------------------------------------------------------------- #
def test_ensure_dirs(settings: Settings) -> None:
    settings.ensure_dirs()
    assert settings.projects_dir.is_dir()
    assert settings.uploads_dir.is_dir()
    assert settings.renders_dir.is_dir()


def test_missing_credentials_reports_absent(settings: Settings) -> None:
    assert "GOOGLE_API_KEY" in settings.missing_credentials()


def test_settings_reads_env(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "test-key")
    assert Settings(data_dir=tmp_path).google_api_key == "test-key"


def test_speaking_rate_bounds() -> None:
    with pytest.raises(ValueError):
        Settings(tts_speaking_rate=9.0)


# --------------------------------------------------------------------------- #
def test_chat_round_trip(settings: Settings) -> None:
    chat = Chat(title="Eigenvalues")
    chat.messages.append(Message(role=Role.USER, content="explain eigenvalues"))
    store.save(chat, settings)

    loaded = store.load(chat.id, settings)
    assert loaded is not None
    assert loaded.title == "Eigenvalues"
    assert loaded.messages[0].content == "explain eigenvalues"
    assert loaded.messages[0].role is Role.USER


def test_load_missing_returns_none(settings: Settings) -> None:
    assert store.load("nope", settings) is None


def test_load_corrupt_returns_none(settings: Settings) -> None:
    chat = store.create(settings)
    directory = store.chat_dir(chat.id, settings)
    (directory / "chat.json").write_text("{not json", encoding="utf-8")
    assert store.load(chat.id, settings) is None


def test_list_summaries_newest_first(settings: Settings) -> None:
    first = store.create(settings)
    second = store.create(settings)
    # Force a distinct, newer timestamp.
    from datetime import UTC, datetime, timedelta

    second.updated_at = datetime.now(UTC) + timedelta(minutes=5)
    store.save(second, settings)

    summaries = store.list_summaries(settings)
    assert summaries[0].id == second.id
    assert {s.id for s in summaries} == {first.id, second.id}


def test_summary_counts_messages(settings: Settings) -> None:
    chat = store.create(settings)
    chat.messages.append(Message(role=Role.USER, content="hi"))
    store.save(chat, settings)
    assert store.list_summaries(settings)[0].message_count == 1


def test_create_persists(settings: Settings) -> None:
    chat = store.create(settings)
    assert store.load(chat.id, settings) is not None


def test_delete_removes_chat(settings: Settings) -> None:
    chat = store.create(settings)
    (settings.uploads_dir / chat.id).mkdir(parents=True)
    store.delete(chat.id, settings)
    assert store.load(chat.id, settings) is None
    assert not (settings.uploads_dir / chat.id).exists()


def test_delete_refuses_traversal(settings: Settings) -> None:
    sibling = settings.projects_dir.parent / "sibling"
    sibling.mkdir(parents=True)
    store.delete("../sibling", settings)
    assert sibling.exists()


# --------------------------------------------------------------------------- #
def test_preview_uses_first_user_message(settings: Settings) -> None:
    chat = Chat()
    assert chat.preview == "No messages yet"
    chat.messages.append(Message(role=Role.AGENT, content="hi there"))
    assert chat.preview == "No messages yet"
    chat.messages.append(Message(role=Role.USER, content="  make   a video  "))
    assert chat.preview == "make a video"


def test_preview_truncates_long_text() -> None:
    chat = Chat()
    chat.messages.append(Message(role=Role.USER, content="x" * 200))
    assert len(chat.preview) == 49
    assert chat.preview.endswith("…")


def test_code_fields_default_to_none() -> None:
    chat = Chat()
    assert chat.code is None
    assert chat.video_path is None
