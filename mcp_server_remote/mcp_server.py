from mcp.server.fastmcp import FastMCP

mcp = FastMCP("UserManagementMCPServer", host="127.0.0.1", port=8002)

id = 0
users = {}

@mcp.tool()
def create_user(username: str, email: str) -> str:
    global id
    """Create a new user with the given username and email."""
    users[username] = {'email': email, 'id': id}
    print(f"Created user: {username}, email: {email}, id: {id}")
    id += 1
    return f"User '{username}' with email '{email}' created successfully."

@mcp.tool()
def delete_user(username: str) -> str:
    """Delete the user with the given username."""
    if username in users:
        del users[username]
    print(f"Deleted user: {username}")
    return f"User '{username}' deleted successfully."

@mcp.tool()
def get_user(username: str) -> dict:
    """Retrieve the details of the user with the given username."""
    user = users.get(username)
    print(f"Retrieving user: {user}")
    return users.get(username, f"User '{username}' not found.")
