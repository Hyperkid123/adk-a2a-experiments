import os
from google.adk.agents import Agent


import warnings
# Ignore all warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)

os.environ["GOOGLE_API_KEY"] = os.environ['GEMINI_API_KEY']

MODEL_GEMINI_2_5_FLASH = "gemini-2.5-flash"
APP_NAME = "weather_tutorial_app"
USER_ID = "user_1"
SESSION_ID = "session_001"

# @title Define the get_weather Tool
def get_weather(city: str) -> dict:
    """Retrieves the current weather report for a specified city.

    Args:
        city (str): The name of the city (e.g., "New York", "London", "Tokyo").

    Returns:
        dict: A dictionary containing the weather information.
              Includes a 'status' key ('success' or 'error').
              If 'success', includes a 'report' key with weather details.
              If 'error', includes an 'error_message' key.
    """
    print(f"--- Tool: get_weather called for city: {city} ---") # Log tool execution
    city_normalized = city.lower().replace(" ", "") # Basic normalization

    # Mock weather data
    mock_weather_db = {
        "newyork": {"status": "success", "report": "The weather in New York is sunny with a temperature of 25°C."},
        "london": {"status": "success", "report": "It's cloudy in London with a temperature of 15°C."},
        "tokyo": {"status": "success", "report": "Tokyo is experiencing light rain and a temperature of 18°C."},
    }

    if city_normalized in mock_weather_db:
        return mock_weather_db[city_normalized]
    else:
        return {"status": "error", "error_message": f"Sorry, I don't have weather information for '{city}'."}


def getWeatherAgent():
    AGENT_MODEL = MODEL_GEMINI_2_5_FLASH

    weather_agent = Agent(
        name="weather_agent_v1",
        model=AGENT_MODEL,
        description="Provides weather information for specific cities.",
        instruction="You are a helpful weather assistant. "
                    "When the user asks for the weather in a specific city, "
                    "use the 'get_weather' tool to find the information. "
                    "If the tool returns an error, inform the user politely. "
                    "If the tool is successful, present the weather report clearly.",
        tools=[get_weather],
    )
    return weather_agent
