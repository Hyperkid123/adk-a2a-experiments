from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext

MODEL_GEMINI_2_5_FLASH = "gemini-2.5-flash"

APP_NAME = "maths_tutorial_app"
USER_ID = "user_2"
SESSION_ID = "session_002"

def sum(a: int, b: int) -> int:
    """Returns the sum of two integers.

    Args:
        a (int): The first integer.
        b (int): The second integer.

    Returns:
        int: The sum of the two integers.
    """
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
        model=MODEL_GEMINI_2_5_FLASH,
        description="Provides mathematical information and tools.",
        instruction="You are a helpful mathematical assistant powered that can do maths operation. "
                    "Use the sum tool to sum operations when the user requests it. "
                    "Clearly present successful reports or polite error messages based on the tool's output status.",
        tools=[sum, multiply],
    )