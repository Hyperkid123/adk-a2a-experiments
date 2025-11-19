import json

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from .auth_context import user_auth_token

from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from .config import getModel
from google.adk.tools import FunctionTool


APP_NAME = "maths_tutorial_app"
USER_ID = "user_2"
SESSION_ID = "session_002"

def sum(a: int, b: int, tool_context: ToolContext) -> int:
    """Returns the sum of two integers.

    Args:
        a (int): The first integer.
        b (int): The second integer.

    Returns:
        int: The sum of the two integers.
    """
    token = user_auth_token.get()
    print(f"Auth token in tool context: {token}")

    TOKEN_CACHE_KEY = "sum_tool_key"
    SCOPES = ["user"]

    creds = None
    cached_token_info = tool_context.state.get(TOKEN_CACHE_KEY)
    if cached_token_info:
        try:
            creds = Credentials.from_authorized_user_info(cached_token_info, SCOPES)
            if not creds.valid and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                tool_context.state[TOKEN_CACHE_KEY] = json.loads(creds.to_json()) # Update cache
            elif not creds.valid:
                creds = None # Invalid, needs re-auth
                tool_context.state[TOKEN_CACHE_KEY] = None
        except Exception as e:
            print(f"Error loading/refreshing cached creds: {e}")
            creds = None
            tool_context.state[TOKEN_CACHE_KEY] = None
    print(f"Credentials before auth flow: {creds}")
    print(f"--- Tool: sum called with a={a}, b={b} ---") # Log tool execution
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