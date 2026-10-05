# MCP Parent Server Architecture

This example demonstrates a **parent MCP server** that dynamically manages child servers via a JSON config file with hot-reload.

## Key Concepts

### 1. One Parent, Many Children

- **Parent** (`MCPParentServer`): Coordinates all child MCP servers, validates configs, and exposes a **flat list of tools** to the agent
- **Children** (e.g., `OpenBBServer`, `SalesServer`, `SupportServer`): Each handles a domain (finance, sales, support) and exports tools

### 2. Hot-Reload from JSON

Edit `mcp_servers_config.json` to:

- **Enable/disable** a server: Set `"enabled": true/false`
- **Add/remove** servers: Add/delete an entry in the `"servers"` dict
- **Change port/tools/params**: Modify any field

The parent watches the file every 2 seconds (configurable) and:

- Stops removed servers
- Starts new servers
- Restarts modified servers
- Validates all configs before loading

### 3. Validation Layer

The parent validates:

- Module and class name existence
- Port range (1024-65535)
- Required fields (enabled, port, tools, etc.)
- Returns error messages if validation fails

### 4. Agent Sees One List

The agent does **not** see nested dictionaries. It sees a flat list:

```python
[
    "get_stock_price",
    "get_income_statement",
    "qualify_lead",
    "schedule_demo",
    "lookup_knowledge",
    "escalate_to_human"
]
```

When the agent calls a tool, the parent routes it to the correct child server.

## Example Config

```json
{
  "servers": {
    "openbb": {
      "module": "app.mcp_children.openbb_server",
      "class": "OpenBBServer",
      "enabled": true,
      "port": 5001,
      "tools": [
        "get_stock_price",
        "get_income_statement",
        "get_balance_sheet"
      ]
    },
    "sales": {
      "module": "app.mcp_children.sales_server",
      "class": "SalesServer",
      "enabled": true,
      "port": 5002,
      "tools": [
        "qualify_lead",
        "schedule_demo"
      ]
    }
  }
}
```

## Usage

### Start the Server

```bash
uvicorn main_mcp:app --reload
```

### Check MCP Status

```bash
curl http://localhost:8000/mcp/status
```

Returns:

```json
{
  "parent_status": "running",
  "children": {
    "openbb": {
      "name": "openbb",
      "status": "running",
      "port": 5001,
      "tools": ["get_stock_price", ...]
    }
  },
  "total_tools": 13,
  "tools": ["get_stock_price", "qualify_lead", ...]
}
```

### Get All Tools (Flat List for Agent)

```bash
curl http://localhost:8000/mcp/tools
```

Returns:

```json
{
  "tools": [
    "get_stock_price",
    "get_income_statement",
    "qualify_lead",
    "schedule_demo",
    "lookup_knowledge",
    "escalate_to_human"
  ],
  "count": 6
}
```

### Send a Message

```bash
curl -X POST http://localhost:8000/ingest \
  -H "Content-Type: application/json" \
  -d '{
    "channel": "discord",
    "sender_id": "user123",
    "session_id": "sess-abc",
    "user_id": "user123",
    "text": "What is the stock price of AAPL?",
    "metadata": {}
  }'
```

The agent receives:

```json
{
  "agent": "support",
  "route_to": "support-queue",
  "available_tools": ["get_stock_price", "qualify_lead", ...],
  "used_tools": ["get_stock_price"],
  "mcp_status": { "children": {...}, "total_tools": 13 }
}
```

## Hot-Reload Workflow

1. **Edit** `mcp_servers_config.json`
2. **Parent detects change** (every 2 seconds)
3. **Validates** the new config
4. **Reconciles servers**:
   - Stops removed servers
   - Starts new servers
   - Restarts changed servers
5. **Agent** automatically gets updated tool list

## Adding a New Server

1. Create a new child class inheriting from `MCPChildServer`:

```python
from app.mcp.child import MCPChildServer

class MyNewServer(MCPChildServer):
    def __init__(self):
        super().__init__()
        self.tools = ["tool1", "tool2"]
    
    async def start(self, port: int):
        # Initialize server on port
        pass
    
    async def stop(self):
        # Clean shutdown
        pass
    
    async def call_tool(self, tool_name: str, args: dict):
        # Execute tool
        pass
```

2. Add entry to `mcp_servers_config.json`:

```json
"my_new_server": {
  "module": "app.mcp_children.my_new_server",
  "class": "MyNewServer",
  "enabled": true,
  "port": 5004,
  "tools": ["tool1", "tool2"]
}
```

3. Save. Parent detects and starts it automatically.

## Disabling/Enabling Servers at Runtime

Just edit the JSON and change `"enabled": true/false`. Parent will handle the rest.

```json
"openbb": {
  "enabled": false  // Disable OpenBB server
}
```

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                  FastAPI App                            │
│                                                         │
│  ┌─────────────────────────────────────────────��────┐  │
│  │  MCPIntegratedAgentGraph                         │  │
│  │  - agent.process(message)                        │  │
│  │  - available_tools = [flat list]                 │  │
│  └────────────┬─────────────────────────────────────┘  │
│               │ calls                                   │
│  ┌────────────▼──────────────────────────────────────┐ │
│  │  MCPParentServer                                 │ │
│  │  - hot_reload() watching mcp_servers_config.json │ │
│  │  - get_all_tools() -> flat list                  │ │
│  │  - validate configs                              │ │
│  │  - manage child lifecycle                        │ │
│  └──────┬────────────┬──────────────┬───────────────┘ │
│         │            │              │                  │
│    ┌────▼───┐  ┌─────▼──┐  ┌───────▼──┐              │
│    │OpenBB  │  │ Sales  │  │ Support  │              │
│    │Server  │  │ Server │  │ Server   │              │
│    │(5001)  │  │ (5002) │  │ (5003)   │              │
│    └────────┘  └────────┘  └──────────┘              │
│                                                         │
│  Tools: [stock_price, income, qualify, demo, faq...]   │
└─────────────────────────────────────────────────────────┘

JSON Config File (Hot-Reload)
         mcp_servers_config.json
```

## Key Benefits

✅ **Single point of tool registration**: JSON config  
✅ **Zero downtime updates**: Hot-reload child servers  
✅ **Validation before load**: Prevents bad configs  
✅ **Agent simplicity**: Sees one flat tool list  
✅ **Extensible**: Add domains without touching agent code  
✅ **Operational visibility**: `/mcp/status` endpoint shows everything  
