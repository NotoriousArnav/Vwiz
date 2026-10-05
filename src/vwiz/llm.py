"""LLM plumbing: model factory, message conversion, and content-block handling.

Deliberately thin — no LangGraph, no tools yet. This module proves the
API + LangChain + google-genai path end to end before we build on it.
"""

from __future__ import annotations

from collections.abc import Generator, Iterable
from functools import lru_cache
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from vwiz.config import Settings
from vwiz.models import Message, Role


def get_llm(settings: Settings, *, temperature: float = 0.7) -> ChatGoogleGenerativeAI:
    """Build the chat model from settings. Fails loudly when the key is absent."""
    if not settings.google_api_key:
        raise RuntimeError(
            "GOOGLE_API_KEY is not set. Add it to your .env or export it in the "
            "environment and reload the app."
        )
    return ChatGoogleGenerativeAI(
        model=settings.gemini_agent_model,
        google_api_key=settings.google_api_key,
        temperature=temperature,
    )


def _groq_llm(settings: Settings, *, temperature: float = 0.7) -> ChatGroq:
    """Build the fallback chat model from settings."""
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not set.")
    return ChatGroq(
        model=settings.groq_model,
        groq_api_key=settings.groq_api_key,
        temperature=temperature,
    )


def _provider_chain(settings: Settings) -> list[tuple[str, object]]:
    """Providers in priority order. A provider is only usable if its key is set.

    Gemini is primary; Groq is the fallback. Later providers don't get contacted
    unless an earlier one fails before producing any text.
    """
    chain: list[tuple[str, object]] = []
    if settings.google_api_key:
        chain.append(("google", lambda: get_llm(settings)))
    if settings.groq_api_key:
        chain.append(("groq", lambda: _groq_llm(settings)))
    return chain


def _chain_or_raise(chain: list[tuple[str, object]]) -> None:
    if not chain:
        raise RuntimeError(
            "No LLM provider configured. Set GOOGLE_API_KEY and/or GROQ_API_KEY in .env."
        )


_SYSTEM_PROMPT_PATH = Path(__file__).with_name("system.md")


@lru_cache(maxsize=1)
def system_prompt() -> str:
    """The system prompt, loaded once from `system.md` beside this module.

    Cached because it is read every turn and never changes at runtime. A missing
    or empty file is an error, not a silent no-op: without it every protection in
    the prompt is quietly gone and the model will answer from memory.
    """
    try:
        text = _SYSTEM_PROMPT_PATH.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"System prompt missing at {_SYSTEM_PROMPT_PATH}") from exc
    if not text:
        raise RuntimeError(f"System prompt at {_SYSTEM_PROMPT_PATH} is empty")
    return text


def to_langchain(messages: Iterable[Message]) -> list[HumanMessage | AIMessage | SystemMessage]:
    """Map project messages onto LangChain messages for the chat model.

    The shared system prompt is prepended so every turn carries the full
    grounding and code-discipline instructions.
    """
    out: list[HumanMessage | AIMessage | SystemMessage] = [SystemMessage(content=system_prompt())]
    for message in messages:
        if message.role is Role.USER:
            out.append(HumanMessage(content=message.content))
        elif message.role is Role.AGENT:
            out.append(AIMessage(content=message.content))
        elif message.role is Role.SYSTEM:
            out.append(SystemMessage(content=message.content))
    return out


def chunk_text(chunk: object) -> str:
    """Pull the text out of one streamed chunk.

    `AIMessageChunk.content` is not always a string. On the newer Gemini models it
    is a list of standard content blocks like
    `[{'type': 'text', 'text': 'pong', 'index': 0}]`, and concatenating it as a
    string crashes on the first token. Some paths also hand back a plain string.
    """
    content = getattr(chunk, "content", None)
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content or []:
        # Standard content block: {'type': 'text', 'text': '...'}
        if isinstance(block, dict) and block.get("type") == "text":
            text = block.get("text")
            if isinstance(text, str):
                parts.append(text)
    return "".join(parts)


def stream_reply(messages: Iterable[Message], settings: Settings) -> Generator[str]:
    """Yield the assistant's reply as text tokens, to feed `st.write_stream`.

    Falls back to the next provider in the chain (Gemini, then Groq) only when a
    provider fails before producing any output. Once tokens have flowed, we do
    not switch models and interleave a different voice into a partial reply.
    """
    chain = _provider_chain(settings)
    _chain_or_raise(chain)
    history = to_langchain(messages)
    last_error: Exception | None = None
    yielded = False
    for _name, factory in chain:
        try:
            for chunk in factory().stream(history):
                text = chunk_text(chunk)
                if text:
                    yielded = True
                    yield text
            return
        except Exception as exc:
            last_error = exc
            if yielded:
                raise
    if last_error is not None:
        raise last_error


def make_title(first_message: str, settings: Settings) -> str:
    """Ask the model for a short chat title based on the first user message."""
    prompt = [
        SystemMessage(
            content=(
                "Give the chat a short, specific title describing what the user "
                "wants to animate. Six words or fewer. Respond with only the title — "
                "no quotes, no punctuation, no explanation."
            )
        ),
        HumanMessage(content=first_message),
    ]
    chain = _provider_chain(settings)
    if not chain:
        return " ".join(first_message.split())[:40]
    for _name, factory in chain:
        try:
            out = factory().invoke(prompt)
            title = " ".join(chunk_text(out).split())[:60]
            if title:
                return title
        except Exception:
            continue
    return " ".join(first_message.split())[:40]
