"""Probe CLI: a REPL over the deep agent with a tool-call trace.

Usage: vwiz-probe
"""

from __future__ import annotations

import asyncio

from vwiz.config import get_settings
from vwiz.probe import agent as agent_mod
from vwiz.probe.mcp_servers import server_names


async def _amain() -> None:
    settings = get_settings()
    print(f"fleet: {', '.join(server_names(settings))}")
    print("building agent (MCP discovery + skill scan)...")
    ag, tools = await agent_mod.build_agent(settings)
    print(f"tools ({len(tools)}): {', '.join(t.name for t in tools)}")
    print("type a prompt, or /quit. Replies stream below; tool calls are traced.")
    while True:
        try:
            prompt = input("\n> ").strip()
        except EOFError, KeyboardInterrupt:
            break
        if not prompt or prompt.lower() in {"/quit", "/q", "quit", "exit"}:
            break
        fired: list[str] = []
        try:
            async for chunk in ag.astream(
                {"messages": [{"role": "user", "content": prompt}]},
                config={"configurable": {"thread_id": "probe"}},
                stream_mode="messages",
            ):
                msg = chunk[0] if isinstance(chunk, tuple) else chunk
                for call in getattr(msg, "tool_calls", None) or []:
                    name = (
                        call.get("name", "?")
                        if isinstance(call, dict)
                        else getattr(call, "name", "?")
                    )
                    if not fired or fired[-1] != name:
                        fired.append(name)
                        print(f"\n[tool: {name}]", flush=True)
                text = getattr(msg, "content", None)
                if isinstance(text, str) and text:
                    print(text, end="", flush=True)
                elif isinstance(text, list):
                    for block in text:
                        if isinstance(block, dict) and block.get("type") == "text":
                            print(block.get("text", ""), end="", flush=True)
            print()
            if fired:
                print(f"(tools used: {', '.join(fired)})")
        except Exception as exc:
            print(f"\nerror: {type(exc).__name__}: {str(exc)[:300]}")


def main() -> None:
    asyncio.run(_amain())


if __name__ == "__main__":
    main()
