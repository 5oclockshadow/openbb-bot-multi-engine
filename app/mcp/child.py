from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class MCPChildServer(ABC):
    """Base class for all MCP child servers."""

    def __init__(self) -> None:
        self.port = 5000
        self.tools: list[str] = []
        self.prompts: dict[str, str] = {}

    @abstractmethod
    async def start(self, port: int) -> None:
        """Start the child server."""
        ...

    @abstractmethod
    async def stop(self) -> None:
        """Stop the child server gracefully."""
        ...

    def get_prompts(self) -> dict[str, str]:
        """Return prompts defined by this server."""
        return self.prompts

    @abstractmethod
    async def call_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        """Call a tool by name with the given arguments."""
        ...
