from __future__ import annotations

import asyncio
import logging
from typing import Any

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.config import settings
from app.core.agent_graph_mcp import MCPIntegratedAgentGraph
from app.mcp.parent import MCPParentServer
from app.services.runtime import RuntimeController
from app.transports.base import InboundMessage

logger = logging.getLogger(__name__)

app = FastAPI(title="OpenBB Multi Engine with MCP", version="0.1.0")

mcp_parent = MCPParentServer(settings.MCP_CONFIG_PATH)
agent_graph = MCPIntegratedAgentGraph(mcp_parent)
runtime = RuntimeController()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "openbb-bot-multi-engine-mcp"}


@app.get("/mcp/status")
async def mcp_status() -> JSONResponse:
    """Get current MCP parent server status and all child servers."""
    return JSONResponse(status_code=200, content=mcp_parent.get_status())


@app.get("/mcp/tools")
async def mcp_tools() -> JSONResponse:
    """Get flat list of all available tools from MCP."""
    return JSONResponse(
        status_code=200,
        content={
            "tools": mcp_parent.get_all_tools(),
            "count": len(mcp_parent.get_all_tools()),
        },
    )


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Starting OpenBB Multi-Engine with MCP...")
    await agent_graph.init_mcp()
    await runtime.start()
    logger.info("Startup complete.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("Shutting down...")
    await runtime.stop()
    await mcp_parent.stop()
    logger.info("Shutdown complete.")


@app.post("/ingest")
async def ingest(message: dict[str, Any]) -> JSONResponse:
    """Ingest a message from any transport channel."""
    try:
        session = message.get("session_id", "default-session")
        text = message.get("text", "")
        channel = message.get("channel", "unknown")
        payload = {
            "channel": channel,
            "sender_id": message.get("sender_id", "anonymous"),
            "session_id": session,
            "user_id": message.get("user_id", session),
            "text": text,
            "metadata": message.get("metadata", {}),
        }
        inbound = InboundMessage(**payload)
        result = await agent_graph.process(inbound)
        return JSONResponse(status_code=200, content={"ok": True, "result": result})
    except Exception as exc:
        logger.error(f"Error ingesting message: {exc}")
        return JSONResponse(status_code=400, content={"ok": False, "error": str(exc)})
