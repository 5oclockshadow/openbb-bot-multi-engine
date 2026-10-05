from __future__ import annotations

import logging
from typing import Any

from app.mcp.child import MCPChildServer

logger = logging.getLogger(__name__)


class OpenBBServer(MCPChildServer):
    """Example MCP child server for OpenBB financial data."""

    def __init__(self) -> None:
        super().__init__()
        self.tools = [
            "get_stock_price",
            "get_income_statement",
            "get_balance_sheet",
            "get_cashflow_statement",
            "search_ticker",
        ]
        self.prompts = {
            "openbb_system": "You are a financial data assistant powered by OpenBB.",
        }

    async def start(self, port: int) -> None:
        self.port = port
        logger.info(f"OpenBB MCP server started on port {port}")

    async def stop(self) -> None:
        logger.info(f"OpenBB MCP server stopped")

    async def call_tool(self, tool_name: str, args: dict[str, Any]) -> Any:
        """Simulate calling OpenBB tools."""
        if tool_name == "get_stock_price":
            ticker = args.get("ticker", "AAPL")
            return {"ticker": ticker, "price": 150.25, "currency": "USD"}
        elif tool_name == "search_ticker":
            query = args.get("query", "")
            return {"results": [{"ticker": "AAPL", "name": "Apple Inc."}]}
        return {"error": f"Unknown tool: {tool_name}"}
