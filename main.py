from agent.root_agent import getRunner, USER_ID, SESSION_ID, getRootAgent
from agent.call_agent import callAgentAsync
from google.adk.a2a.utils.agent_to_a2a import to_a2a
from google.adk.agents.remote_a2a_agent import AGENT_CARD_WELL_KNOWN_PATH, RemoteA2aAgent
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner
from mcp_server_remote.mcp_server import mcp



import asyncio
import signal
import uvicorn

initial_state = {
    "multiply_enabled": False
}

async def create_remote_agent_runner():
    weather_agent = RemoteA2aAgent(
        name="remote_weather_agent",
        description="A remote agent that provides weather information and sum operation.",
        agent_card="http://localhost:8001/.well-known/agent-card.json"
    )

    # MCP server over networks
    toolset = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            url="http://localhost:8002/mcp"
        )
    )

    orchestrator_agent = Agent(
        model="gemini-2.5-flash",
        name="orchestrator_agent",
        description="An orchestrator agent that delegates weather and maths requests to a remote weather agent.",
        instruction="You are a helpful orchestrator assistant. "
                    "Use the remote weather agent to execute weather and maths requests. "
                    "Clearly present successful reports or polite error messages based on the remote agent's output status.",
        # toolset can include remote MCP servers
        tools=[toolset],
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
        session_id=SESSION_ID,
        state=initial_state
    )
    retrieved_session = await session_service.get_session(
        app_name="orchestrator_app",
        user_id=USER_ID,
        session_id=SESSION_ID
    )
    runner = Runner(
        agent=orchestrator_agent, # The agent we want to run
        app_name="orchestrator_app",   # Associates runs with our app
        session_service=session_service, # Uses our session manager
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
    await callAgentAsync("Create user with name John and email john@example.com",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID)
    await callAgentAsync("Get details of user John",
                                       runner=runner,
                                       user_id=USER_ID,
                                       session_id=SESSION_ID)

# Global variables for graceful shutdown (recommended pattern from Stack Overflow)
shutdown_event = None
running_tasks = []

async def graceful_shutdown():
    """Graceful shutdown coroutine"""
    print("\nShutdown signal received...")
    if shutdown_event:
        shutdown_event.set()

def signal_handler(signum, frame):
    """Signal handler that works with asyncio"""
    loop = None
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        pass

    if loop and loop.is_running():
        # Use run_coroutine_threadsafe for cross-thread safety
        asyncio.run_coroutine_threadsafe(graceful_shutdown(), loop)

async def run_servers():
    global shutdown_event, running_tasks

    app1 = to_a2a(getRootAgent(), port=8001)
    runner = await create_remote_agent_runner()
    server1 = uvicorn.Server(uvicorn.Config(app1, host="127.0.0.1", port=8001))

    # Create shutdown event
    shutdown_event = asyncio.Event()

    # Register signal handlers (Stack Overflow recommended pattern)
    for sig in [signal.SIGINT, signal.SIGTERM]:
        signal.signal(sig, signal_handler)

    async def delayed_conversation():
        print("Waiting 5 seconds for the server to start...")
        await asyncio.sleep(5)
        print("Starting conversation with orchestrator agent...")
        await run_conversation(runner)
        print("Conversation completed. Servers will continue running...")
        print("Press Ctrl+C to exit")

    # Start servers and track tasks
    print("Starting MCP server on port 8002...")
    mcp_task = asyncio.create_task(mcp.run_streamable_http_async())

    print("Starting A2A server on port 8001...")
    server_task = asyncio.create_task(server1.serve())

    conversation_task = asyncio.create_task(delayed_conversation())

    # Track all running tasks globally
    running_tasks = [mcp_task, server_task, conversation_task]

    try:
        # Run until shutdown signal or conversation completes
        done, pending = await asyncio.wait([
            asyncio.create_task(shutdown_event.wait()),
            conversation_task
        ], return_when=asyncio.FIRST_COMPLETED)

        # If conversation completed naturally, wait for shutdown signal
        if conversation_task in done:
            print("Conversation completed. Servers will continue running...")
            print("Press Ctrl+C to exit")
            await shutdown_event.wait()

    finally:
        # Cleanup using finally block (aiohttp pattern from Stack Overflow)
        print("Shutting down servers...")

        # Signal uvicorn to shutdown gracefully first
        server1.should_exit = True

        # Cancel all pending tasks
        for task in running_tasks:
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete (with exception handling)
        if running_tasks:
            await asyncio.gather(*running_tasks, return_exceptions=True)

        print("All servers stopped")

def main():
    print("Hello from my-agent-python!")
    asyncio.run(run_servers())

if __name__ == "__main__":
    main()

