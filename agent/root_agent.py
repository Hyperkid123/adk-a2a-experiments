import os
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from agent.weather_agent_gemini import getWeatherAgent
from agent.maths_agent import getMathsAgent
from agent.config import getModel
from google.genai import types


import warnings
# Ignore all warnings
warnings.filterwarnings("ignore")

import logging
logging.basicConfig(level=logging.ERROR)

os.environ["GOOGLE_API_KEY"] = os.environ['GEMINI_API_KEY']
APP_NAME = "orchestrator_app"  # Match the app name used in main.py
USER_ID = "user_1"
SESSION_ID = "session_001"

def getRootAgent():
    root_agent = Agent(
        name="root_agent",
        model=getModel(),
        description="A root agent that distributes and delegates weather and maths requests to sub-agents.",
        instruction="You are a helpful root assistant. "
                    "Use the available sub-agents to execute weather and maths requests. "
                    "Clearly present successful reports or polite error messages based on the sub-agent's output status."
                    "You have access to the following sub-agents: weather_agent and maths_agent.",
        tools=[],
        sub_agents=[getWeatherAgent(), getMathsAgent()],
          generate_content_config=types.GenerateContentConfig(
              safety_settings=[
                  types.SafetySetting(  # avoid false alarm about rolling dice.
                      category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                      threshold=types.HarmBlockThreshold.OFF,
                  ),
              ]
          ),
    )
    return root_agent


async def getRunner():
    root_agent = getRootAgent()
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    runner = Runner(
        agent=root_agent, # The agent we want to run
        app_name=APP_NAME,   # Associates runs with our app
        session_service=session_service # Uses our session manager
    )
    return [runner, session]
