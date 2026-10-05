from __future__ import annotations

import logging
from typing import Any

from app.mcp.child import MCPChildServer

logger = logging.getLogger(__name__)


class SalesServer(MCPChildServer):
    """Example MCP child server for sales/CRM workflows."""

    def __init__(self) -> None:
        super().__init__()
        self.tools = [
            "qualify_lead",
            "schedule_demo",
            "create_opportunity",
            "get_pipeline_status",
        ]
        self.prompts = {
            "sales_system": "You are a sales assistant. Help qualify leads and move deals forward.",
        }

    async def start(self, port: int) -> None:
        self.port = port
        logger.info(f"Sales MCP server started on port {port}")

    async def stop(self) -> None:
        logger.info(f"Sales MCP server stopped")

    async def call_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        """Simulate calling sales tools."""
        if tool_name == "qualify_lead":
            return {"qualified": True, "score": 85, "next_step": "schedule_demo"}
        elif tool_name == "schedule_demo":
            return {"demo_scheduled": True, "time_slot": "2025-01-15 2PM UTC"}
        return {"error": f"Unknown tool: {tool_name}"}
