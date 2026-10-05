"""MCP server fleet for the probe CLI, as an MCPConfig dict.

Servers whose credentials are missing are dropped *before* the config is built:
a dead member fails the whole tool-catalog load, so partial degradation has to
happen here, not at discovery time.
"""

from __future__ import annotations

import warnings

with warnings.catch_warnings():
    # langchain.mcp is beta and warns on import; the probe opts in knowingly.
    warnings.simplefilter("ignore")
    from langchain.mcp import MCPAdapter

from vwiz.config import Settings

__all__ = ["MCPAdapter", "build_config", "server_names"]


def build_config(settings: Settings) -> dict:
    """Assemble the {"mcpServers": {...}} dict from the settings in force.

    Exa and Context7 need no key. Tavily only joins when TAVILY_API_KEY is set —
    without it the endpoint 401s and would poison discovery for the rest.
    """
    servers: dict[str, dict] = {
        "exa": {"url": "https://mcp.exa.ai/mcp"},
        "context7": {"url": "https://mcp.context7.com/mcp"},
    }
    if settings.exa_api_key:
        servers["exa"] = {"url": f"https://mcp.exa.ai/mcp?exaApiKey={settings.exa_api_key}"}
    if settings.tavily_api_key:
        servers["tavily"] = {
            "url": f"https://mcp.tavily.com/mcp/?tavilyApiKey={settings.tavily_api_key}"
        }
    return {"mcpServers": servers}


def server_names(settings: Settings) -> list[str]:
    """Which servers made it into the fleet, for the startup inventory."""
    return list(build_config(settings)["mcpServers"])
