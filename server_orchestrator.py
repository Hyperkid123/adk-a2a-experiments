"""
Server orchestration for ADK A2A, MCP, and OAuth servers.
Handles startup, shutdown, and coordination of all servers.
"""

import asyncio
import signal
import uvicorn
from agent.remote_server import create_remote_agent_app
from mcp_server_remote.mcp_server import mcp
from oauth_mock_server.server import run_oauth_server_async


class ServerOrchestrator:
    """Manages lifecycle of all servers (A2A, MCP, OAuth)"""

    def __init__(self):
        self.shutdown_event = None
        self.running_tasks = []

    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            """Signal handler that works with asyncio"""
            loop = None
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                pass

            if loop and loop.is_running():
                # Use run_coroutine_threadsafe for cross-thread safety
                asyncio.run_coroutine_threadsafe(self._graceful_shutdown(), loop)

        # Register signal handlers (Stack Overflow recommended pattern)
        for sig in [signal.SIGINT, signal.SIGTERM]:
            signal.signal(sig, signal_handler)

    async def _graceful_shutdown(self):
        """Graceful shutdown coroutine"""
        print("\nShutdown signal received...")
        if self.shutdown_event:
            self.shutdown_event.set()

    async def start_servers(self):
        """
        Start all servers and return when they're ready.
        Servers will run until shutdown signal is received.
        """
        print("Starting servers...")

        # Create shutdown event
        self.shutdown_event = asyncio.Event()

        # Setup signal handlers
        self._setup_signal_handlers()

        # Create remote agent server
        remote_agent_app = create_remote_agent_app()
        server1 = uvicorn.Server(uvicorn.Config(remote_agent_app, host="127.0.0.1", port=8001))

        # Start servers and track tasks
        print("Starting MCP server on port 8002...")
        mcp_task = asyncio.create_task(mcp.run_streamable_http_async())

        print("Starting A2A server on port 8001...")
        server_task = asyncio.create_task(server1.serve())

        print("Starting OAuth mock server on port 8003...")
        oauth_task = asyncio.create_task(run_oauth_server_async())

        # Track all running tasks
        self.running_tasks = [mcp_task, server_task, oauth_task]

        # Wait a moment for servers to start
        await asyncio.sleep(5)
        print("All servers started successfully!")

        return server1  # Return server1 for potential shutdown control

    async def wait_for_shutdown(self):
        """Wait for shutdown signal"""
        if self.shutdown_event:
            await self.shutdown_event.wait()

    async def shutdown_servers(self):
        """Gracefully shutdown all servers"""
        print("Shutting down servers...")

        # Cancel all pending tasks
        for task in self.running_tasks:
            if not task.done():
                task.cancel()

        # Wait for all tasks to complete (with exception handling)
        if self.running_tasks:
            await asyncio.gather(*self.running_tasks, return_exceptions=True)

        print("All servers stopped")

    async def run_until_shutdown(self):
        """
        Start servers and run until shutdown signal.
        Complete server lifecycle management.
        """
        try:
            await self.start_servers()
            print("Servers running. Press Ctrl+C to exit")
            await self.wait_for_shutdown()
        finally:
            await self.shutdown_servers()


async def start_all_servers():
    """
    Convenience function to start all servers.
    Returns ServerOrchestrator instance for manual control.
    """
    orchestrator = ServerOrchestrator()
    await orchestrator.start_servers()
    return orchestrator


async def run_servers_until_shutdown():
    """
    Convenience function to run all servers until shutdown.
    Handles complete lifecycle automatically.
    """
    orchestrator = ServerOrchestrator()
    await orchestrator.run_until_shutdown()