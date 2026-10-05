"""One agent turn for the Streamlit app: MCP tools + manim-video skill.

Reuses the probe's scratch tree (`prepare_scratch`), fleet config
(`build_config`), and document materializer (`materialize`). MCP discovery and
the run itself share one `async with MCPAdapter(...)` block, so tools can never
outlive their connections.

The model comes from the user's Settings choice, not a silent chain — the same
`llm_provider` the direct chat path uses.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langchain_core.messages import HumanMessage

from vwiz.config import Settings

__all__ = ["TurnResult", "model_string", "run_agent_turn"]


# Groq's on-demand tier caps requests at 8k tokens, but the full fleet plus
# the skill index runs ~8.8k. These three add bulk without unique capability
# (our agent *is* the research agent; fetch/extract cover single-page reads),
# so Groq turns go out without them. Other providers keep the full fleet.
_GROQ_SLIM_TOOLS = frozenset({"exa_agent_run", "tavily_tavily_crawl", "tavily_tavily_map"})


@dataclass
class TurnResult:
    """What one agent turn produced."""

    text: str
    code: str | None = None
    tool_names: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def model_string(settings: Settings) -> str:
    """init_chat_model reference for the selected provider. No I/O."""
    provider = (settings.llm_provider or "groq").lower()
    if provider == "google":
        return f"google_genai:{settings.gemini_agent_model}"
    if provider == "groq":
        return f"groq:{settings.groq_model}"
    if provider == "ollama":
        return f"ollama:{settings.ollama_model}"
    raise RuntimeError(
        f"Unknown LLM provider {settings.llm_provider!r}; pick google, groq, or ollama in Settings."
    )


def _seed_keys(settings: Settings) -> None:
    """init_chat_model reads the process environment, not Settings."""
    if settings.google_api_key:
        os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)
    if settings.groq_api_key:
        os.environ.setdefault("GROQ_API_KEY", settings.groq_api_key)


async def run_agent_turn(chat, settings: Settings) -> TurnResult:
    """Run one full turn: materialize docs, discover tools, invoke, parse."""
    from vwiz import llm
    from vwiz.probe import agent as agent_mod
    from vwiz.probe.inputs import materialize
    from vwiz.probe.mcp_servers import MCPAdapter, build_config, server_names

    notes: list[str] = []
    scratch = agent_mod.prepare_scratch()

    # Stage every chat document where the agent's `read` tool can see it.
    seen: set[str] = set()
    staged = 0
    for source in list(chat.documents) + [p for m in chat.messages for p in (m.attachments or [])]:
        key = str(source)
        if key in seen:
            continue
        seen.add(key)
        if not Path(source).is_file():
            notes.append(f"{Path(source).name}: missing on disk, skipped")
            continue
        try:
            result = materialize(Path(source), scratch, settings)
        except Exception as exc:  # noqa: BLE001 - one bad file skips, never kills
            notes.append(f"{Path(source).name}: could not stage ({exc})")
            continue
        staged += 1
        notes.extend(result["notes"])

    # History without the prepended system prompt: the agent carries it via
    # `system_prompt=`, and passing both would double it.
    history = llm.to_langchain(chat.messages)[1:]
    doc_block = llm.document_context(chat.messages, settings, documents=chat.documents)
    if doc_block:
        history.append(HumanMessage(content=doc_block))

    _seed_keys(settings)
    provider = (settings.llm_provider or "groq").lower()
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        model = ChatOllama(
            model=settings.ollama_model,
            base_url=settings.ollama_base_url,
            temperature=0.7,
        )
    else:
        model = model_string(settings)

    async with MCPAdapter(build_config(settings)) as adapter:
        tools = await adapter.list_tools()
        if provider == "groq":
            tools = [t for t in tools if t.name not in _GROQ_SLIM_TOOLS]
        agent = create_deep_agent(
            model=model,
            backend=FilesystemBackend(root_dir=str(scratch), virtual_mode=True),
            tools=tools,
            skills=["skills/"],
            system_prompt=llm.agent_prompt(),
        )
        fleet = ", ".join(server_names(settings)) or "none"
        notes.append(f"fleet: {fleet} ({len(tools)} tools)")
        notes.append(f"staged {staged} document(s) into inputs/")
        result = await agent.ainvoke({"messages": history})

    messages = result.get("messages", []) if isinstance(result, dict) else []
    fired: list[str] = []
    for msg in messages:
        for call in getattr(msg, "tool_calls", None) or []:
            name = call.get("name", "?") if isinstance(call, dict) else getattr(call, "name", "?")
            if not fired or fired[-1] != name:
                fired.append(name)

    raw = ""
    for msg in reversed(messages):
        if msg.__class__.__name__.startswith("AI"):
            raw = llm.chunk_text(msg) or getattr(msg, "content", "") or ""
            if isinstance(raw, list):
                raw = ""
            if raw:
                break

    text, code = llm.parse_agent_reply(raw) if raw else ("(empty reply from agent)", None)
    return TurnResult(text=text, code=code, tool_names=fired, notes=notes)
