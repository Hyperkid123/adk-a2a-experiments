from agent.root_agent import getRunner, USER_ID, SESSION_ID, getRootAgent
from agent.call_agent import callAgentAsync
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent
from google.adk.agents.llm_agent import Agent
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner



import asyncio
import uvicorn

async def create_remote_agent_runner():
    weather_agent = RemoteA2aAgent(
        name="remote_weather_agent",
        description="A remote agent that provides weather information and sum operation.",
        agent_card="http://localhost:8001/.well-known/agent-card.json"
    )

    orchestrator_agent = Agent(
        model="gemini-2.5-flash",
        name="orchestrator_agent",
        description="An orchestrator agent that delegates weather and maths requests to a remote weather agent.",
        instruction="You are a helpful orchestrator assistant. "
                    "Use the remote weather agent to execute weather and maths requests. "
                    "Clearly present successful reports or polite error messages based on the remote agent's output status.",
        tools=[],
        sub_agents=[weather_agent],
        generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(  # avoid false alarm about rolling dice.
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.OFF,
            ),
        ])
    )

    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="orchestrator_app",
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    runner = Runner(
        agent=orchestrator_agent, # The agent we want to run
        app_name="orchestrator_app",   # Associates runs with our app
        session_service=session_service # Uses our session manager
    )
    return runner


async def run_conversation(runner):
    await callAgentAsync("What is the weather like in London?",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID)

    await callAgentAsync("How about Paris?",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID) # Expecting the tool's error message

    await callAgentAsync("Tell me the weather in New York",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID)

    await callAgentAsync("Tell me the what is the sum of 15 and 27?",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID)

async def run_servers():
    app1 = to_a2a(getRootAgent(), port=8001)
    runner = await create_remote_agent_runner()

    server1 = uvicorn.Server(uvicorn.Config(app1, host="127.0.0.1", port=8001))

    async def delayed_conversation():
        print("Waiting 5 seconds for the server to start...")
        await asyncio.sleep(5)
        print("Starting conversation with orchestrator agent...")
        await run_conversation(runner)

    await asyncio.gather(server1.serve(), delayed_conversation())

def main():
    print("Hello from my-agent-python!")
    asyncio.run(run_servers())

if __name__ == "__main__":
    main()

