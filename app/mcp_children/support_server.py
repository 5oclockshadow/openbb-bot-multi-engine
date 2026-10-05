from __future__ import annotations

import logging
from typing import Any

from app.mcp.child import MCPChildServer

logger = logging.getLogger(__name__)


class SupportServer(MCPChildServer):
    """Example MCP child server for customer support workflows."""

    def __init__(self) -> None:
        super().__init__()
        self.tools = [
            "lookup_knowledge",
            "search_faqs",
            "escalate_to_human",
            "log_ticket",
        ]
        self.prompts = {
            "support_system": "You are a helpful customer support agent. Resolve issues efficiently.",
        }

    async def start(self, port: int) -> None:
        self.port = port
        logger.info(f"Support MCP server started on port {port}")

    async def stop(self) -> None:
        logger.info(f"Support MCP server stopped")

    async def call_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        """Simulate calling support tools."""
        if tool_name == "lookup_knowledge":
            query = args.get("query", "")
            return {"found": True, "articles": [f"Article about {query}"]}
        elif tool_name == "escalate_to_human":
            return {"escalated": True, "ticket_id": "TKT-12345"}
        return {"error": f"Unknown tool: {tool_name}"}
