"""
Remote A2A agent server setup with OAuth authentication middleware.
Handles the HTTP server for remote agents with token extraction.
"""

from fastapi import Request
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from agent.root_agent import getRootAgent
from agent.auth_context import user_auth_token


def create_remote_agent_app():
    """
    Create the remote A2A agent FastAPI application with OAuth middleware.

    Returns:
        FastAPI app configured for A2A with authentication
    """
    # Create remote agent app with OAuth middleware
    app = to_a2a(getRootAgent(), port=8001)

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        """
        Extract OAuth token from Authorization header and set in context variable.
        Makes token available to agent tools via user_auth_token.get()
        """
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

    return app