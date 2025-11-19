"""
OAuth token decoder for remote agent tools.
Provides functions to decode and validate OAuth tokens received in remote agent tools.
"""

import httpx
from typing import Optional, Dict, Any
from agent.auth_context import user_auth_token


class TokenInfo:
    """Container for decoded token information"""

    def __init__(self, introspection_data: Dict[str, Any]):
        self.active = introspection_data.get('active', False)
        self.username = introspection_data.get('username')
        self.email = introspection_data.get('email')
        self.name = introspection_data.get('name')
        self.client_id = introspection_data.get('client_id')
        self.scope = introspection_data.get('scope', '')
        self.scopes = self.scope.split() if self.scope else []
        self.user_id = introspection_data.get('sub')  # 'sub' field contains user ID
        self.expires_at = introspection_data.get('exp')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy access"""
        return {
            'active': self.active,
            'username': self.username,
            'email': self.email,
            'name': self.name,
            'client_id': self.client_id,
            'scopes': self.scopes,
            'user_id': self.user_id,
            'expires_at': self.expires_at
        }

    def has_scope(self, required_scope: str) -> bool:
        """Check if token has a specific scope"""
        return required_scope in self.scopes


async def introspect_token(token: str, introspection_url: str = "http://localhost:8003/introspect") -> Optional[TokenInfo]:
    """
    Introspect an OAuth token to get user information.

    Args:
        token: OAuth access token to introspect
        introspection_url: URL of the OAuth introspection endpoint

    Returns:
        TokenInfo object with user details, or None if token is invalid
    """
    if not token:
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                introspection_url,
                json={"token": token},
                headers={"Content-Type": "application/json"}
            )

            if response.status_code != 200:
                print(f"Token introspection failed: {response.status_code}")
                return None

            data = response.json()
            if not data.get('active', False):
                print("Token is not active")
                return None

            return TokenInfo(data)

    except Exception as e:
        print(f"Error during token introspection: {e}")
        return None


async def get_current_user() -> Optional[TokenInfo]:
    """
    Get current user information from the OAuth token in context.

    This is the main function that remote agent tools should use.
    It gets the token from the current request context and decodes it.

    Returns:
        TokenInfo object with user details, or None if no valid token
    """
    token = user_auth_token.get()
    if not token:
        print("No OAuth token found in context")
        return None

    return await introspect_token(token)


def require_scope(required_scope: str):
    """
    Decorator to require a specific OAuth scope for a tool function.

    Usage:
        @require_scope("admin")
        async def delete_user(username: str) -> str:
            # Tool logic here
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            user = await get_current_user()
            if not user or not user.has_scope(required_scope):
                return {
                    "error": f"Access denied. Required scope: {required_scope}",
                    "success": False
                }
            return await func(*args, **kwargs)
        return wrapper
    return decorator