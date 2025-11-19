# OAuth Authentication for ADK A2A Remote Agents

## Problem Statement

ADK's Agent-to-Agent (A2A) protocol enables remote agents to run as separate HTTP services, but requires a mechanism to pass OAuth credentials from orchestrator to remote agent tools over the network.

## Solution Overview

The solution uses ADK's built-in `a2a_client_factory` parameter with a custom `authenticated_client_factory` to inject OAuth tokens into HTTP headers, combined with middleware on the remote agent to extract tokens and make them available to tools via Python's `contextvars`.

## Implementation

### 1. Authenticated Client Factory (Orchestrator Side)

**Purpose**: Inject OAuth token into all A2A HTTP requests from orchestrator to remote agent.

```python
from a2a.client import ClientFactory, ClientConfig
from a2a.types import TransportProtocol
import httpx

def authenticated_client_factory(token: str):
    return ClientFactory(
        ClientConfig(
            supported_transports=[TransportProtocol.http_json, TransportProtocol.jsonrpc],
            use_client_preference=True,
            # Inject the Authorization header here
            httpx_client=httpx.AsyncClient(
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0
            )
        )
    )
```

**Usage**: Pass to `RemoteA2aAgent` via `a2a_client_factory` parameter:

```python
weather_agent = RemoteA2aAgent(
    name="remote_weather_agent",
    description="A remote agent that provides weather information and sum operation.",
    agent_card="http://localhost:8001/.well-known/agent-card.json",
    # This is the key - inject OAuth token via client factory
    a2a_client_factory=authenticated_client_factory(token)
)
```

**Critical Details**:
- Uses ADK's official `a2a_client_factory` parameter (no monkey-patching)
- Configures `httpx.AsyncClient` with Authorization header
- Supports both `http_json` and `jsonrpc` transports
- Token is automatically included in all HTTP requests to the remote agent

### 2. Context Variable for Token Storage

**File**: `agent/auth_context.py`

```python
import contextvars

# Async-safe token storage - each request gets its own context
user_auth_token: contextvars.ContextVar[str | None] = contextvars.ContextVar("user_auth_token", default=None)
```

**Critical Details**:
- Uses Python's `contextvars` for async-safe request isolation
- Each concurrent HTTP request gets its own token context
- Default value is `None` when no token is present
- No race conditions between concurrent requests

### 3. Token Extraction Middleware (Remote Agent)

**Purpose**: Extract OAuth token from incoming HTTP requests and make available to agent tools.

```python
from fastapi import Request
from agent.auth_context import user_auth_token

@app1.middleware("http")
async def auth_middleware(request: Request, call_next):
    # A. Extract Header
    auth_header = request.headers.get("Authorization")

    # B. Set ContextVar (and keep the reset token)
    token_reset_token = None
    if auth_header:
        # Strip "Bearer " if necessary, or pass raw
        token_val = auth_header.replace("Bearer ", "").strip()
        token_reset_token = user_auth_token.set(token_val)

    try:
        # C. Process Request (Agent runs here)
        response = await call_next(request)
        return response
    finally:
        # D. Cleanup (Critical for async hygiene)
        if token_reset_token:
            user_auth_token.reset(token_reset_token)
```

**Critical Details**:
- Middleware runs before agent processing
- Extracts token from `Authorization: Bearer <token>` header
- `user_auth_token.set()` returns reset token for proper cleanup
- `finally` block ensures context is always cleaned up after request
- Token is request-scoped and automatically garbage collected

### 4. Tool Access Pattern

**Usage in agent tools**:

```python
from .auth_context import user_auth_token
from google.adk.tools.tool_context import ToolContext

def sum(a: int, b: int, tool_context: ToolContext) -> int:
    token = user_auth_token.get()  # Access token from context
    print(f"Auth token in tool context: {token}")

    # Use token for authenticated operations
    # ... rest of tool logic

    return a + b
```

**Critical Details**:
- Simple access pattern: `user_auth_token.get()`
- Works in any tool function that imports the context variable
- Returns `None` if no token in current context
- No need to pass token as parameter or access session state

## Complete Flow

```
[Orchestrator] → [authenticated_client_factory] → HTTP with Auth Headers → [Remote Agent Middleware] → [Context Variable] → [Agent Tools]
      ↓                           ↓                            ↓                        ↓                       ↓                    ↓
  Has OAuth Token    Creates HTTP Client with    Authorization: Bearer    Extracts Token to     Sets Context Var    Accesses Token
                     Authorization Headers            <token>              Request Scope                              via .get()
```

1. **Orchestrator** obtains OAuth token via standard OAuth 2.0 flow
2. **authenticated_client_factory** creates HTTP client with Authorization headers
3. **RemoteA2aAgent** uses this client for all A2A communication
4. **Remote agent middleware** extracts token from HTTP headers
5. **Context variable** stores token for current request scope
6. **Agent tools** access token via `user_auth_token.get()`

## Key Benefits

- **Standards Compliant**: Uses RFC 6750 Bearer token authentication
- **ADK Native**: Uses official `a2a_client_factory` parameter, no monkey-patching
- **Async Safe**: Python `contextvars` prevents race conditions
- **Request Scoped**: Token automatically cleaned up after each request
- **Simple Access**: Tools just call `user_auth_token.get()`
- **Over Network**: True separation between orchestrator and remote agent

## Production Considerations

### Security
- Always use HTTPS in production (never send Bearer tokens over HTTP)
- Add token validation/introspection in middleware
- Implement token expiration handling
- Add audit logging for token usage

### Performance
- Cache validated tokens to reduce validation overhead
- Use connection pooling in HTTP client
- Consider token compression for large tokens

### Error Handling
- Handle missing or invalid tokens gracefully
- Implement fallback behavior when auth fails
- Add circuit breakers for auth service calls

## Summary

This approach provides OAuth authentication for ADK A2A remote agents using:

- **`authenticated_client_factory`**: ADK's official mechanism to inject HTTP headers
- **`contextvars`**: Async-safe token storage scoped to HTTP requests
- **HTTP middleware**: Token extraction and lifecycle management
- **Simple tool access**: Direct context variable access in agent tools

The pattern is production-ready and uses ADK's supported APIs without monkey-patching or workarounds.