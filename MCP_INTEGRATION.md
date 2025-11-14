# MCP Integration with Google ADK

## Overview

Model Context Protocol (MCP) servers integrate with Google ADK agents as **direct tool providers**, complementing A2A agent delegation for complete orchestration.

## Key Interfaces

### MCPToolset
```python
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams

toolset = MCPToolset(
    connection_params=StreamableHTTPConnectionParams(
        url="http://localhost:8002/mcp"
    )
)
```

### Agent Integration
```python
orchestrator = Agent(
    tools=[toolset],           # MCP tools for operations
    sub_agents=[remote_agent], # A2A agents for reasoning
)
```

## Architecture Pattern

```
Orchestrator Agent
├── MCPToolset ────→ MCP Server (tools: create_user, get_user, delete_user)
└── RemoteA2aAgent ─→ A2A Server (agents: weather, math)
```

## Use Cases

| Pattern | Purpose | Interface |
|---------|---------|-----------|
| **MCP Tools** | Direct operations (CRUD, API calls) | `MCPToolset` |
| **A2A Agents** | Complex reasoning & delegation | `RemoteA2aAgent` |

## Integration Benefits

- **Tool Operations**: Direct function calls via MCP protocol
- **Agent Reasoning**: Natural language delegation via A2A protocol
- **Service Independence**: MCP servers are stateless tool providers
- **Deployment Flexibility**: Scale tools independently from reasoning agents

## Key Difference from A2A

- **MCP**: `function_call(params) → result`
- **A2A**: `message_exchange(context) → response`

MCP handles operational tasks, A2A handles reasoning tasks.