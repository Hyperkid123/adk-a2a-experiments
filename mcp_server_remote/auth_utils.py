from typing import Optional, Dict, Any
from mcp.server.auth.middleware.auth_context import get_access_token
from mcp.server.auth.provider import AccessToken


class UserInfo:
    """Container for authenticated user information"""

    def __init__(self, access_token: AccessToken):
        self.client_id = access_token.client_id
        self.scopes = access_token.scopes
        self.expires_at = access_token.expires_at
        self.token_preview = access_token.token[:20] + "..." if access_token.token else ""
        self.is_admin = "admin" in access_token.scopes
        self.is_user = "user" in access_token.scopes
        self.raw_token = access_token

        # Extract user information from token fields
        # Handle both ExtendedAccessToken and regular AccessToken
        self.user_id = getattr(access_token, 'user_id', None)
        self.username = getattr(access_token, 'username', None)
        self.email = getattr(access_token, 'email', None)
        self.name = getattr(access_token, 'name', None)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/debugging"""
        return {
            "client_id": self.client_id,
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "name": self.name,
            "scopes": self.scopes,
            "expires_at": self.expires_at,
            "token_preview": self.token_preview,
            "is_admin": self.is_admin,
            "is_user": self.is_user
        }


def get_authenticated_user() -> Optional[UserInfo]:
    """
    Get authenticated user information from the current request context.

    Returns:
        UserInfo object if user is authenticated, None otherwise

    Usage:
        user = get_authenticated_user()
        if user:
            print(f"User {user.client_id} with scopes {user.scopes}")
            if user.is_admin:
                # Admin-only functionality
                pass
        else:
            print("No authenticated user")
    """
    access_token = get_access_token()
    if access_token:
        return UserInfo(access_token)
    return None


def log_user_action(action: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Log an action performed by the authenticated user.

    Args:
        action: Description of the action being performed
        details: Optional additional details to log
    """
    user = get_authenticated_user()
    if user:
        print(f"🔐 User Action: {action}")
        print(f"  - Client ID: {user.client_id}")
        print(f"  - Scopes: {user.scopes}")
        if details:
            for key, value in details.items():
                print(f"  - {key}: {value}")
    else:
        print(f"⚠️  Unauthenticated Action: {action}")
        if details:
            for key, value in details.items():
                print(f"  - {key}: {value}")


def require_scope(required_scope: str) -> bool:
    """
    Check if the authenticated user has the required scope.

    Args:
        required_scope: The scope to check for

    Returns:
        True if user has the required scope, False otherwise
    """
    user = get_authenticated_user()
    if not user:
        return False
    return required_scope in user.scopes


def require_admin() -> bool:
    """Check if the authenticated user has admin privileges."""
    return require_scope("admin")