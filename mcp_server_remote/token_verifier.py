import httpx
import asyncio
from typing import Optional
from mcp.server.auth.provider import AccessToken, TokenVerifier


class ExtendedAccessToken(AccessToken):
    """Extended AccessToken with user information fields"""
    user_id: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    name: Optional[str] = None


class IntrospectionTokenVerifier(TokenVerifier):
    """
    TokenVerifier that validates tokens using OAuth 2.0 Token Introspection (RFC 7662)
    """

    def __init__(self, introspection_url: str, client_timeout: float = 5.0):
        """
        Initialize the token verifier.

        Args:
            introspection_url: URL of the OAuth server's introspection endpoint
            client_timeout: Timeout for HTTP requests in seconds
        """
        self.introspection_url = introspection_url
        self.client_timeout = client_timeout

    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """
        Verify a bearer token using token introspection.

        Args:
            token: The bearer token to verify

        Returns:
            AccessToken if valid, None if invalid or expired
        """
        try:
            async with httpx.AsyncClient(timeout=self.client_timeout) as client:
                response = await client.post(
                    self.introspection_url,
                    json={"token": token},
                    headers={"Content-Type": "application/json"}
                )

                if response.status_code != 200:
                    return None

                introspection_data = response.json()

                # Check if token is active
                if not introspection_data.get("active", False):
                    return None

                # Extract token information
                scopes = []
                if "scope" in introspection_data and introspection_data["scope"]:
                    scopes = introspection_data["scope"].split()

                print(f"Token introspection data: {introspection_data}")
                print(f"Token scopes: {scopes}")

                # Create an extended AccessToken with user information
                return ExtendedAccessToken(
                    token=token,
                    client_id=introspection_data.get("client_id", "unknown"),
                    scopes=scopes,
                    expires_at=introspection_data.get("exp"),
                    resource=None,
                    # User information from introspection
                    user_id=introspection_data.get("sub"),
                    username=introspection_data.get("username"),
                    email=introspection_data.get("email"),
                    name=introspection_data.get("name")
                )

        except (httpx.RequestError, httpx.TimeoutException, KeyError, ValueError) as e:
            # Log error in production
            print(f"Token verification failed: {e}")
            return None