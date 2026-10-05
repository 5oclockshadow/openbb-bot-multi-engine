from __future__ import annotations

import logging

from app.config import settings
from app.core.agent_graph import AgentGraph
from app.mcp.parent import MCPParentServer

logger = logging.getLogger(__name__)


class MCPIntegratedAgentGraph(AgentGraph):
    """Enhanced agent graph that integrates with MCP parent server."""

    def __init__(self, mcp_parent: MCPParentServer | None = None) -> None:
        super().__init__()
        self.mcp_parent = mcp_parent or MCPParentServer(settings.MCP_CONFIG_PATH)
        self.available_tools: list[str] = []

    async def init_mcp(self) -> None:
        """Initialize and start the MCP parent server."""
        await self.mcp_parent.start()
        self.available_tools = self.mcp_parent.get_all_tools()
        logger.info(f"Agent graph initialized with {len(self.available_tools)} tools from MCP.")

    async def process(self, message):
        """Process a message using MCP tools and agent reasoning."""
        # Refresh available tools in case of hot-reload
        self.available_tools = self.mcp_parent.get_all_tools()

        text = message.text.lower().strip()

        # Route based on intent
        if any(token in text for token in ["price", "stock", "ticker", "financial"]):
            route = "support"  # OpenBB tools available here
            used_tools = [t for t in self.available_tools if "stock" in t or "price" in t]
        elif any(token in text for token in ["pricing", "demo", "quote", "trial", "buy"]):
            route = "sales"
            used_tools = [t for t in self.available_tools if "qualify" in t or "demo" in t]
        elif any(token in text for token in ["help", "issue", "question", "faq"]):
            route = "support"
            used_tools = [t for t in self.available_tools if "knowledge" in t or "faq" in t]
        else:
            route = "support"
            used_tools = []

        return {
            "agent": route,
            "route_to": f"{route}-queue",
            "available_tools": self.available_tools,
            "used_tools": used_tools,
            "summary": f"Routed to '{route}' with {len(used_tools)} relevant tools.",
            "response": f"Processing your request using {len(used_tools)} available tools.",
            "channel": message.channel,
            "session_id": message.session_id,
            "mcp_status": self.mcp_parent.get_status(),
        }
