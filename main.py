from agent.root_agent import USER_ID, SESSION_ID
from agent.call_agent import callAgentAsync
from oauth_client import OAuthClient
from server_orchestrator import start_all_servers
from orchestrator_setup import create_orchestrator_runner

import asyncio
import logging

# Suppress verbose ADK logging (following ADK docs recommendations)
logging.getLogger('google_adk.google.adk.models.google_llm').setLevel(logging.WARNING)


async def run_conversation(runner):
    try:
        print("Starting conversation with orchestrator agent...")
        response, tool_results = await callAgentAsync("What is the weather like in London?",
                                        runner=runner,
                                        user_id=USER_ID,
                                        session_id=SESSION_ID)

        response, tool_results = await callAgentAsync("How about Paris?",
                                        runner=runner,
                                        user_id=USER_ID,
                                        session_id=SESSION_ID) # Expecting the tool's error message

        response, tool_results = await callAgentAsync("Tell me the weather in New York",
                                        runner=runner,
                                        user_id=USER_ID,
                                        session_id=SESSION_ID)

        response, tool_results = await callAgentAsync("Tell me the what is the sum of 15 and 27?",
                                        runner=runner,
                                        user_id=USER_ID,
                                        session_id=SESSION_ID)

        # Create user and capture the result
        response, tool_results = await callAgentAsync("Create my user account",
                                        runner=runner,
                                        user_id=USER_ID,
                                        session_id=SESSION_ID)

        # Extract username from create_user tool result
        created_username = None
        for tool_result in tool_results:
            if tool_result['tool_name'] == 'create_user' and tool_result['result']:
                try:
                    result = tool_result['result']
                    if isinstance(result, dict) and result.get('success') and 'user' in result:
                        created_username = result['user']['username']
                        break
                except Exception as e:
                    print(f"⚠️ Error extracting username: {e}")

        # Use the extracted username in the next call
        if created_username:
            response, tool_results = await callAgentAsync(f"Get details of user {created_username}",
                                            runner=runner,
                                            user_id=USER_ID,
                                            session_id=SESSION_ID)
        else:
            print("Could not extract username from create_user result, skipping get_user call")
    except Exception as e:
        print(f"❌ Error during conversation: {e}")


async def run_application():
    """Main application entry point"""
    try:
        # Start all servers
        print("🚀 Starting servers...")
        server_orchestrator = await start_all_servers()

        # Get OAuth token
        print("🔑 Getting OAuth token...")
        oauth_client = OAuthClient()
        token = await oauth_client.get_oauth_flow_token()
        if not token:
            print("❌ Failed to get OAuth token - running without authentication")
            token = ""

        # Create agent runner with OAuth token
        print("🤖 Creating agent runner with OAuth token...")
        runner = await create_orchestrator_runner(token)

        # Run conversation
        print("💬 Starting conversation...")
        await run_conversation(runner)

        # Keep servers running until user exits
        print("Conversation completed. Servers will continue running...")
        print("Press Ctrl+C to exit")
        await server_orchestrator.wait_for_shutdown()

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'server_orchestrator' in locals():
            await server_orchestrator.shutdown_servers()

def main():
    print("Hello from my-agent-python!")
    asyncio.run(run_application())

if __name__ == "__main__":
    main()

