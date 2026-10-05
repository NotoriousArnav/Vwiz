"""Deep agent assembly for the probe CLI.

One agent over the MCP fleet, with the manim-video skill loaded through
progressive disclosure. The backend root is a scratch tree, never the repo, so
the agent's file tools cannot reach `.env` or `src/`.
"""

from __future__ import annotations

import shutil
from pathlib import Path

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend

from vwiz.config import Settings
from vwiz.probe.mcp_servers import MCPAdapter, build_config

__all__ = ["SCRATCH_ROOT", "prepare_scratch", "build_agent"]

# Backend root for the agent. Gitignored; rebuilt on every CLI start.
SCRATCH_ROOT = Path(".vwiz-probe")

# Canonical skill location in the repo, copied into the scratch tree.
SKILL_SOURCE = Path("skills/manim-video")


def prepare_scratch(repo_root: Path | None = None) -> Path:
    """(Re)build the scratch tree: root + skill copy, nothing else.

    Wiping and re-copying each start means a previous run's artefacts can never
    leak into the next one, and the skill copy is always current.
    """
    root = Path(repo_root or Path.cwd())
    scratch = root / SCRATCH_ROOT
    if scratch.exists():
        shutil.rmtree(scratch)
    skill_src = root / SKILL_SOURCE
    if not (skill_src / "SKILL.md").exists():
        raise RuntimeError(f"Skill missing at {skill_src}; clone manim-video-lab first.")
    shutil.copytree(skill_src, scratch / "skills" / "manim-video")
    (scratch / "inputs").mkdir(parents=True, exist_ok=True)
    return scratch


async def build_agent(settings: Settings, repo_root: Path | None = None):
    """Discover MCP tools, then build the deep agent. Returns (agent, tools)."""
    if not settings.google_api_key:
        raise RuntimeError("GOOGLE_API_KEY is not set; the probe agent needs it.")
    # create_deep_agent resolves "google_genai:..." via init_chat_model, which
    # reads the process environment — not our Settings. Seed it without echoing.
    import os

    os.environ.setdefault("GOOGLE_API_KEY", settings.google_api_key)
    scratch = prepare_scratch(repo_root)
    backend = FilesystemBackend(root_dir=str(scratch), virtual_mode=True)
    async with MCPAdapter(build_config(settings)) as adapter:
        tools = await adapter.list_tools()
        agent = create_deep_agent(
            model=f"google_genai:{settings.gemini_agent_model}",
            backend=backend,
            tools=tools,
            skills=["skills/"],
        )
        return agent, tools
