# MCP OAuth Authentication

## Overview

This implementation demonstrates OAuth 2.0 authentication integration with Model Context Protocol (MCP) servers using Bearer token authentication over HTTP transport.

## Architecture

The authentication flow involves three main components:

1. **OAuth Server** (Port 8003) - Issues and validates tokens
2. **MCP Server** (Port 8002) - Protected resources requiring authentication
3. **Client Application** - Orchestrator agent making authenticated requests

## Authentication Flow

### 1. Token Acquisition
- Client requests initial OAuth token using `client_credentials` grant
- OAuth server returns access token with basic scopes

### 2. Token Exchange (RFC 8693)
- Client exchanges initial token for MCP-specific token with required scopes
- This step is necessary because MCP spec doesn't allow direct token passing in protocol messages
- Token exchange enables scope refinement and audience-specific tokens

### 3. MCP Authentication
- Client includes exchanged token in HTTP `Authorization: Bearer <token>` header
- MCP server receives requests with Bearer token via StreamableHTTP transport

### 4. Token Validation
- MCP server validates tokens using OAuth 2.0 Token Introspection (RFC 7662)
- Introspection endpoint returns token validity, scopes, and user information
- Server extracts user context (username, email, permissions) from introspection response

## Key Design Decisions

**Why Token Exchange?**
- MCP protocol messages cannot directly contain authentication tokens
- HTTP transport layer handles authentication via standard Bearer headers
- Token exchange allows scope-specific tokens for different services

**Why Introspection?**
- Enables real-time token validation without shared secrets
- Provides user information needed for authorization decisions
- Standard OAuth 2.0 pattern for resource server validation

**User Context Extraction**
- Authenticated user information flows from token introspection
- MCP tools can access user context via auth utilities
- Enables user-specific operations and audit logging

## Benefits

- **Standards Compliant**: Uses RFC 8693 (Token Exchange) and RFC 7662 (Introspection)
- **Scalable**: Resource servers validate tokens independently
- **Secure**: No shared secrets between MCP server and OAuth server
- **Flexible**: Easy to add new MCP servers with same auth pattern
- **User-Aware**: MCP tools have access to authenticated user context

## Usage Pattern

1. Client obtains OAuth token through standard flow
2. Client exchanges token for MCP-specific scope
3. Client includes token in MCP HTTP connection headers
4. MCP server validates token and extracts user context
5. MCP tools operate with authenticated user information

This pattern enables secure, user-aware MCP operations while maintaining separation between authentication (OAuth server) and resource access (MCP server).