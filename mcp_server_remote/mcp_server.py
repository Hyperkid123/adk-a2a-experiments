from pydantic import AnyHttpUrl
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.auth.settings import AuthSettings
from .token_verifier import IntrospectionTokenVerifier
from .auth_utils import get_authenticated_user, log_user_action, require_scope

# Create token verifier that calls our OAuth server's introspection endpoint
token_verifier = IntrospectionTokenVerifier(
    introspection_url="http://localhost:8003/introspect"
)

mcp = FastMCP(
    "UserManagementMCPServer",
    host="127.0.0.1",
    port=8002,
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("http://localhost:8003"),
        resource_server_url=AnyHttpUrl("http://localhost:8002"),
        required_scopes=["user"]
    ),
    token_verifier=token_verifier
)

id = 0
users = {}

@mcp.tool()
def create_user() -> dict:
    global id
    """Create a user record from the authenticated user's token data."""

    # Get authenticated user info from token
    user = get_authenticated_user()
    if not user:
        return {"error": "No authenticated user found. Authentication required.", "success": False}

    if not user.username or not user.email:
        return {"error": "Token does not contain required user information (username, email).", "success": False}

    # Log the action with user info
    log_user_action("create_user", {"from_token_user": user.username})

    print(f"👤 Creating user from token data: {user.to_dict()}")

    # Use the authenticated user's data to create the record
    username = user.username
    if username in users:
        return {
            "error": f"User '{username}' already exists.",
            "success": False,
            "existing_user": users[username]
        }

    new_user = {
        'email': user.email,
        'name': user.name,
        'username': user.username,
        'user_id': user.user_id,
        'id': id,
        'created_by': user.client_id,
        'created_with_scopes': user.scopes
    }

    users[username] = new_user

    print(f"✅ Created user: {username}, email: {user.email}, id: {id}")
    id += 1

    return {
        "success": True,
        "message": f"User '{user.name or username}' created successfully from token data.",
        "user": new_user
    }

@mcp.tool()
def delete_user(username: str) -> str:
    """Delete the user with the given username."""

    # Check if user has admin privileges for delete operations
    if not require_scope("admin"):
        log_user_action("delete_user_denied", {"username": username, "reason": "insufficient_privileges"})
        return f"Error: Admin privileges required to delete users."

    log_user_action("delete_user", {"username": username})

    if username in users:
        del users[username]
        print(f"Deleted user: {username}")
        return f"User '{username}' deleted successfully."
    else:
        return f"User '{username}' not found."

@mcp.tool()
def get_user(username: str) -> dict:
    """Retrieve the details of the user with the given username."""

    log_user_action("get_user", {"username": username})

    user = users.get(username)
    print(f"Retrieving user: {user}")
    return users.get(username, f"User '{username}' not found.")
