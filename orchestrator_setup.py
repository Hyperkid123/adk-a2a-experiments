"""
Orchestrator agent setup and configuration.
Creates the main orchestrator agent with OAuth authentication and MCP/A2A integration.
"""

from agent.root_agent import USER_ID, SESSION_ID
from agent.config import getModel
from agent.auth_client import authenticated_client_factory
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent
from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool import MCPToolset, StreamableHTTPConnectionParams
from google.genai import types
from google.adk.sessions import InMemorySessionService
from google.adk.runners import Runner


async def create_orchestrator_runner(oauth_token: str = ""):
    """
    Create the main orchestrator agent runner with OAuth authentication.

    The orchestrator agent:
    - Uses MCP tools for user management operations (create_user, get_user, delete_user)
    - Delegates to remote A2A agent for weather and math requests
    - Includes OAuth authentication for both MCP and A2A communication

    Args:
        oauth_token: OAuth access token for authenticated operations

    Returns:
        Runner configured with orchestrator agent
    """
    # Setup remote weather agent with OAuth authentication
    weather_agent = RemoteA2aAgent(
        name="remote_weather_agent",
        description="A remote agent that provides weather information and sum operation.",
        agent_card="http://localhost:8001/.well-known/agent-card.json",
        # Inject OAuth token into A2A HTTP communication
        a2a_client_factory=authenticated_client_factory(oauth_token)
    )

    # Setup MCP toolset with OAuth authentication
    toolset = MCPToolset(
        connection_params=StreamableHTTPConnectionParams(
            headers={"Authorization": f"Bearer {oauth_token}"} if oauth_token else {},
            url="http://localhost:8002/mcp"
        )
    )

    # Create orchestrator agent
    orchestrator_agent = Agent(
        model=getModel(),
        name="orchestrator_agent",
        description="An orchestrator agent that delegates weather and maths requests to a remote weather agent.",
        instruction="You are a helpful orchestrator assistant. "
                    "Use your MCP tools for user management operations (create_user, get_user, delete_user). "
                    "Use the remote weather agent for weather and maths requests only. "
                    "Clearly present successful reports or polite error messages based on tool output status.",
        # MCP tools and remote agents
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

    # Create session state with OAuth credentials for ADK tools
    session_state = {
        "multiply_enabled": False,
        "sum_tool_key": {
            "access_token": oauth_token,
            "token_type": "Bearer",
            "client_id": "test-client",  # Should match your OAuth client
            "type": "authorized_user"
        } if oauth_token else None
    }

    # Setup session service
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="orchestrator_app",
        user_id=USER_ID,
        session_id=SESSION_ID,
        state=session_state
    )
    retrieved_session = await session_service.get_session(
        app_name="orchestrator_app",
        user_id=USER_ID,
        session_id=SESSION_ID
    )

    # Create runner
    runner = Runner(
        agent=orchestrator_agent,
        app_name="orchestrator_app",
        session_service=session_service,
    )

    return runner