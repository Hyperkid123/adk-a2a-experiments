"""
OAuth authentication client for A2A remote agents.
Provides authenticated HTTP client factory for injecting OAuth tokens into A2A communication.
"""

import httpx
from a2a.client import ClientFactory, ClientConfig
from a2a.types import TransportProtocol


def authenticated_client_factory(token: str):
    """
    Create a client factory that injects OAuth Authorization header into all A2A HTTP requests.

    Args:
        token: OAuth access token to include in Authorization header

    Returns:
        ClientFactory configured with OAuth authentication
    """
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