import json

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from .auth_context import user_auth_token
from .token_decoder import get_current_user

from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from .config import getModel
from google.adk.tools import FunctionTool


APP_NAME = "maths_tutorial_app"
USER_ID = "user_2"
SESSION_ID = "session_002"

async def sum(a: int, b: int, tool_context: ToolContext) -> int:
    """Returns the sum of two integers.

    Args:
        a (int): The first integer.
        b (int): The second integer.

    Returns:
        int: The sum of the two integers.
    """
    # Decode the current OAuth token to get user information
    try:
        user_info = await get_current_user()
        if user_info:
            print(f"Authenticated user: {user_info.username} ({user_info.email})")
            print(f"User scopes: {user_info.scopes}")
        else:
            print("No authenticated user or invalid token")
    except Exception as e:
        print(f"Error decoding token: {e}")
        user_info = None

    print(f"--- Tool: sum called with a={a}, b={b}, for user {user_info.username if user_info else 'unknown'} ---")
    return a + b

def multiply(a: int, b: int, tool_context: ToolContext) -> int | dict:

    """Returns the product of two integers.

    Args:
        a (int): The first integer.
        b (int): The second integer.

    Returns:
        int | dict: The product of the two integers, or a dictionary containing 
            error information if an error occurs during multiplication.
    """
    print(f"--- Tool: multiply called with a={a}, b={b} ---") # Log tool execution
    return a * b

def getMathsAgent():
    return Agent(
        name="maths_agent",
        model=getModel(),
        description="Provides mathematical information and tools.",
        instruction="You are a helpful mathematical assistant powered that can do maths operation. "
                    "Use the sum tool to sum operations when the user requests it. "
                    "Clearly present successful reports or polite error messages based on the tool's output status.",
        tools=[FunctionTool(func=sum), FunctionTool(func=multiply)],
    )