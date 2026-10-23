# AGENT BUILD PROMPT

You are working in the repository `5oclockshadow/openbb-bot-multi-engine`.

Build the complete MCP-based multi-transport AI orchestration platform described in this conversation.

## Objective

Create a production-ready starter platform that supports:
- Discord community bot
- Telegram direct support and payments
- Slack internal operations
- Gmail async workflows
- website funnel / lead intake
- multi-agent orchestration driven by a graph / ReAct style planner
- Redis-backed queue and memory layer
- FastAPI control plane
- MCP parent-child architecture with JSON hot reload

## Architectural principles

1. Do not build one monolithic bot.
2. Separate transport adapters from orchestration.
3. Use a parent MCP server to manage child MCP servers.
4. Keep the agent-facing tool list as a single flat list, not a nested dictionary.
5. Each child server exposes domain tools, prompts, and status.
6. Parent server handles validation, health, lifecycle, and hot reload.
7. Use JSON-driven config as source of truth.
8. Include status endpoints and tool endpoints for operators.
9. Prefer modular Python classes and clean interfaces over hardcoded wiring.
10. Treat each transport as a plugin adapter with start(), stop(), emit().

## Core required components

### 1. FastAPI app
Create a FastAPI app with these routes:
- `/health`
- `/ingest`
- `/mcp/status`
- `/mcp/tools`

### 2. Runtime controller
Create a runtime controller that:
- owns memory store
- owns message bus
- owns agent graph
- owns transports registry
- dispatches inbound messages to the graph
- coordinates startup and shutdown

### 3. MCP parent server
Create `MCPParentServer` with:
- config loader reading `mcp_servers_config.json`
- validation before startup
- hot reload detection on file modification
- add/remove/restart reconciliation
- flat list of all tools from all running child servers
- aggregated child status response
- no nested dict tool structure presented to the agent
- enable/disable behavior from config

### 4. MCP child server abstraction
Create `MCPChildServer` base class with:
- start(port)
- stop()
- call_tool(name, args)
- get_prompts()

### 5. Example MCP child servers
Create at least 3 example child servers:
- OpenBB financial data server
- Sales CRM / funnel server
- Support knowledge / ticketing server

Each child should define:
- a list of tools
- prompt metadata
- simulated or real call_tool logic

### 6. Agent graph
Create `AgentGraph` or `MCPIntegratedAgentGraph` with:
- routing based on intent and metadata
- response generation logic
- tool selection based on available flat list
- channel-aware flow logic
- optional enrichment with MCP status and loaded tools

### 7. Transport adapters
Create adapter classes for:
- Discord
- Telegram
- Slack
- Gmail

Use a shared `InboundMessage` data model with:
- channel
- sender_id
- session_id
- user_id
- text
- metadata

### 8. Redis-backed infrastructure
Use Redis for:
- queueing messages between services
- storing conversation context
- optional vector memory / embedding cache

If Redis is unavailable, degrade gracefully to in-memory fallback.

### 9. Autoscaler
Add a lightweight autoscaler that can:
- track queue depth
- adjust worker concurrency targets
- support future worker clusters

### 10. Docker
Provide:
- `Dockerfile`
- `docker-compose.yml`
- redis service
- app service
- environment file support

## Required file structure

Keep the project organized like this:

app/
  config.py
  services/
    runtime.py
    autoscaler.py
  core/
    agent_graph.py
    agent_graph_mcp.py
    memory.py
    queue.py
  mcp/
    config.py
    parent.py
    child.py
  transports/
    base.py
    discord_transport.py
    telegram_transport.py
    slack_transport.py
    gmail_transport.py
  mcp_children/
    openbb_server.py
    sales_server.py
    support_server.py

main.py
main_mcp.py
mcp_servers_config.json
README.md
MCP_ARCHITECTURE.md
Dockerfile
docker-compose.yml
.env.example
pyproject.toml

## Config file behavior

`mcp_servers_config.json` must be JSON shaped like:

{
  "servers": {
    "openbb": {
      "module": "app.mcp_children.openbb_server",
      "class": "OpenBBServer",
      "enabled": true,
      "port": 5001,
      "tools": ["get_stock_price", "get_income_statement"],
      "timeout": 30
    }
  }
}

The parent server must:
- validate each server before loading
- ignore invalid entries but keep going
- start new servers automatically
- stop removed servers automatically
- restart changed config entries
- expose a flat list of tools to the agent

## Agent tool contract

The agent must see this shape, not a nested dict:

[
  "get_stock_price",
  "get_income_statement",
  "qualify_lead",
  "schedule_demo",
  "lookup_knowledge",
  "escalate_to_human"
]

Do not pass tools as:
{
  "openbb": [...],
  "sales": [...],
  "support": [...]
}

## Quality bar

- Clean, readable Python
- type hints
- pydantic models for inbound messages and config objects
- graceful fallback for absent Redis
- no brittle hardcoded transport logic
- complete startup/shutdown lifecycle
- parameterized config over direct code coupling
- hot reload support and status visibility

## Acceptance criteria

The final implementation should allow:
- editing `mcp_servers_config.json` and seeing parent server reload automatically
- calling `/mcp/status` and seeing child server statuses
- calling `/mcp/tools` and seeing a flat tool list
- ingesting a message from any transport via `/ingest`
- routing requests to the correct agent/specialist based on message intent
- building this project in Docker with Redis running locally or in compose

## Hard constraint

The system must maintain a parent server that is responsible for validation, lifecycle, and tool visibility; the agent should only consume the parent’s flat tool list and not a nested server dictionary.

## Example prompt to use with the agent

"Build a multi-transport AI orchestration platform in Python with FastAPI, Redis, Docker, and MCP parent-child architecture. Use a JSON config file for MCP servers, validate their config, hot reload on changes, and expose one flat tool list to the agent. Include Discord, Telegram, Slack, and Gmail adapters, a graph-based agent router, and status endpoints. Keep the architecture modular and extensible."

## Final instruction

Proceed systematically:
1. Create the project structure.
2. Implement core config and settings.
3. Implement MCP config loader, validation, and parent lifecycle.
4. Build child server examples and flat tool aggregation.
5. Add the agent graph and runtime controller.
6. Add transport adapters.
7. Add Redis and autoscaler support.
8. Add Docker and compose setup.
9. Add docs and examples.
10. Verify by running the health endpoint and MCP status endpoints.

This is the prompt pack for the AI agent that will build the repo.
