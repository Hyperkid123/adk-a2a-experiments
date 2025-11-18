# ADK Agent-to-Agent Development

A working example of Google ADK agent-to-agent communication and MCP integration with OAuth authentication.

## Documentation

- `A2A_OVERVIEW.md` - Agent-to-Agent concepts and patterns
- `MCP_INTEGRATION.md` - MCP server integration guide
- `docs/MCP_OAuth_Authentication.md` - OAuth authentication implementation with MCP servers

## Project Structure

```
agent/
   root_agent.py              # Root agent with weather/math sub-agents
   weather_agent_gemini.py    # Weather lookup sub-agent
   maths_agent.py             # Math sub-agent
   call_agent.py              # Agent invocation utilities
mcp_server_remote/
   mcp_server.py              # MCP server with user management tools
main.py                       # Entry point - runs servers & client
```

## Setup

1. **Install dependencies**:
   ```bash
   export GEMINI_API_KEY="your-api-key"
   make install  # or: uv sync
   ```

2. **Run the system**:
   ```bash
   make run  # or: uv run main.py
   ```

## How It Works

- **Port 8001**: Root agent HTTP server (weather + math tools)
- **Port 8002**: MCP server (user management tools) with OAuth authentication
- **Port 8003**: OAuth mock server (token issuance and introspection)
- **Client**: Orchestrator agent using RemoteA2aAgent + MCPToolset
- **Agent Card**: `http://localhost:8001/.well-known/agent-card.json`

Supported queries:
- Weather: London, New York, Tokyo (Paris fails intentionally)
- Math: Sum operations
- User management: Create, get, delete users via MCP tools

## Development

### Adding New Tools

1. **Create tool function** in relevant agent file:
   ```python
   def multiply(a: int, b: int) -> int:
       return a * b
   ```

2. **Add to agent's tools**:
   ```python
   tools=[sum, multiply]
   ```

### Adding New Sub-Agents

1. **Create agent file**: `agent/new_agent.py`
2. **Import in** `agent/root_agent.py`
3. **Add to sub_agents list**:
   ```python
   sub_agents=[getWeatherAgent(), getMathsAgent(), getNewAgent()]
   ```

### Extending Weather Data

Modify `mock_weather_db` in `agent/weather_agent_gemini.py`:
```python
"paris": {"status": "success", "report": "Paris is sunny with 20C."}
```

## Troubleshooting

**Port already in use:**
```bash
lsof -i :8001 && kill -9 <PID>
```

**Missing API key:**
```bash
export GEMINI_API_KEY="your-key"
```

**Port mismatch:** Ensure `to_a2a(getRootAgent(), port=8001)` and uvicorn server use the same port

**Agent not responding:**
- Check: `curl http://localhost:8001/.well-known/agent-card.json`
- Increase delay in `main.py` if needed
