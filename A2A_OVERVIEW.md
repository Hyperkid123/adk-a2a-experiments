# Agent-to-Agent (A2A) Communication: A Conceptual Overview

This document explains the core concepts of Agent-to-Agent communication and how this project demonstrates it. If you're an engineer who needs to understand A2A quickly, this is your starting point.

## What is Agent-to-Agent Communication?

Agent-to-Agent (A2A) communication is a protocol that allows AI agents to talk to each other over HTTP, similar to how microservices communicate via REST APIs. But instead of rigid API contracts, agents discover each other's capabilities dynamically and delegate tasks naturally.

Think of it this way: instead of building one monolithic agent that does everything, you build specialized agents that collaborate. A weather agent, a math agent, a translation agent - each focused on what it does best. The A2A protocol provides the plumbing to wire them together.

## The Core Insight: Agents as Network Services

Traditional approach:
```
User -> Single Agent with 50 tools
```

A2A approach:
```
User -> Orchestrator Agent -> Weather Agent (3 tools)
                            -> Math Agent (5 tools)
                            -> Translation Agent (10 tools)
```

Each agent becomes a discoverable service on your network. This unlocks:
- **Specialization**: Agents can focus on specific domains
- **Reusability**: One weather agent serves many orchestrators
- **Scalability**: Add capacity by deploying more instances
- **Modularity**: Update the weather agent without touching the orchestrator

## Key Concepts

### 1. Agent Cards

An agent card is a JSON document (by default served on a route similar to `/.well-known/agent-card.json`) that describes what an agent can do:

```json
{
  "name": "root_agent",
  "description": "Handles weather and math requests",
  "capabilities": {
    "sub_agents": [
      {"name": "weather_agent", "description": "Provides weather info"},
      {"name": "maths_agent", "description": "Does math operations"}
    ]
  }
}
```

This is the discovery mechanism. When an orchestrator connects to a remote agent, it fetches the agent card to understand what capabilities are available.

You can think of agent cards as OpenAPI specs for AI agents. They enable runtime capability discovery without hardcoding.

### 2. Delegation Over Ownership

In traditional architectures, you import tools directly into your agent. With A2A, you delegate to remote agents:

```python
# Traditional: Import tools directly
agent = Agent(tools=[get_weather, calculate_sum])

# A2A: Delegate to remote agents
remote_agent = RemoteA2aAgent(
    agent_card="http://weather-service:8001/.well-known/agent-card.json"
)
orchestrator = Agent(sub_agents=[remote_agent])
```

The orchestrator doesn't need to know how `get_weather()` works. It just knows there's a remote agent that can handle weather queries.

Agents become loosely coupled. Update the weather service implementation without touching the orchestrator code.

### 3. HTTP as the Transport Layer

A2A uses standard HTTP for communication:

- **GET `/.well-known/agent-card.json`**: Fetch capabilities
- **POST `/`**: Send messages to the agent (JSON-RPC format)

This means agents can be:
- Deployed anywhere (localhost, different servers, different clouds)
- Protected by standard HTTP tools (load balancers, API gateways, auth)
- Monitored with existing observability infrastructure

A2A agents are just HTTP services. All your existing web infrastructure knowledge applies.

## How Google ADK Enables A2A

The Google AI Development Kit (ADK) provides two key abstractions:

### 1. `to_a2a()` - Turn Any Agent into an HTTP Service

```python
from google.adk.a2a.utils.agent_to_a2a import to_a2a

root_agent = Agent(name="root", sub_agents=[weather_agent, math_agent])
app = to_a2a(root_agent, port=8001)

# Now you have a fully functional HTTP server
server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=8001))
await server.serve()
```

The `to_a2a()` wrapper handles:
- Exposing the agent card at `/.well-known/agent-card.json`
- Accepting HTTP POST requests with user messages
- Routing messages to the appropriate sub-agents
- Serializing responses back to HTTP

### 2. `RemoteA2aAgent` - Connect to Remote Agents

```python
from google.adk.agents.remote_a2a_agent import RemoteA2aAgent

remote_agent = RemoteA2aAgent(
    name="remote_weather_agent",
    agent_card="http://localhost:8001/.well-known/agent-card.json"
)

orchestrator = Agent(sub_agents=[remote_agent])
```

The `RemoteA2aAgent` handles:
- Fetching and parsing the agent card
- Serializing messages to HTTP requests
- Sending requests to the remote agent
- Deserializing responses back to agent messages

`to_a2a()` and `RemoteA2aAgent` are two sides of the same coin. One publishes capabilities, the other consumes them.

## The Flow in This Project

This project demonstrates A2A with a concrete example:

```
User Query: "What's the weather in London?"

1. [User] -> [Orchestrator Agent]
   Message: "What's the weather in London?"

2. [Orchestrator Agent] -> [RemoteA2aAgent]
   Decision: This is a weather query, delegate to remote agent

3. [RemoteA2aAgent] -> HTTP POST -> [Root Agent Server on :8001]
   Request: {"content": {"role": "user", "parts": [{"text": "..."}]}}

4. [Root Agent] -> [Weather Agent]
   Decision: Route to weather_agent_v1 sub-agent

5. [Weather Agent] -> get_weather("London")
   Tool execution: Lookup in mock database

6. [Weather Agent] -> [Root Agent] -> HTTP Response -> [RemoteA2aAgent]
   Response: {"status": "success", "report": "It's cloudy in London..."}

7. [RemoteA2aAgent] -> [Orchestrator Agent] -> [User]
   Final: "It's cloudy in London with a temperature of 15C."
```

### The Architecture

```
+---------------------------+     +---------------------------+
|  Orchestrator Process     |     |  Root Agent Server        |
|  (Client)                 |     |  (Port 8001)              |
|                           |     |                           |
|  Orchestrator Agent       |     |  Root Agent               |
|    |                      |     |    |                      |
|    +-> RemoteA2aAgent ----+-HTTP-+-->|                      |
|                           |     |    +-> Weather Agent      |
|                           |     |    |     get_weather()    |
|                           |     |    |                      |
|                           |     |    +-> Maths Agent        |
|                           |     |          sum()            |
+---------------------------+     +---------------------------+
```

In this demo, both processes run in the same Python program using `asyncio.gather()`, but in production they could be separate services on different machines.

### What Makes This Interesting

**Location transparency**: The orchestrator doesn't care that the weather agent is remote. From its perspective, delegating to a `RemoteA2aAgent` looks identical to delegating to a local sub-agent.

**Hierarchy of agents**: The root agent is itself composed of sub-agents (weather and math). This creates a tree structure where routing decisions happen at multiple levels.

**Standard tools**: The `get_weather()` and `sum()` tools are just normal Python functions. The A2A protocol wraps them seamlessly.

## Why This Matters for Building Agent Systems

### 1. Separation of Concerns

Each agent can be developed, tested, and deployed independently. The weather team doesn't need to coordinate with the orchestrator team.

### 2. Technology Flexibility

The weather agent could be written in Python, the math agent in JavaScript, the translation agent in Go. As long as they speak A2A (HTTP + agent cards), they interoperate.

### 3. Operational Independence

Deploy new versions of the weather agent without restarting the orchestrator. Scale the weather service independently based on demand.

### 4. Security Boundaries

Each agent can have its own authentication, rate limiting, and audit logging. Sensitive tools can be isolated in secured agents.

### 5. Composability

Build complex agent systems by composing simpler agents:

```
Customer Service Bot
  +-> FAQ Agent (retrieves answers from docs)
  +-> Order Status Agent
        +-> Inventory Agent (checks stock)
        +-> Shipping Agent (tracks packages)
  +-> Escalation Agent (connects to human support)
```

Each agent in this tree could be owned by different teams, deployed to different environments, and evolved independently.

## Mental Model: Agents as Microservices

If you understand microservices, you already understand A2A:

| Microservices | A2A |
|---------------|-----|
| REST endpoint | Agent card endpoint |
| OpenAPI spec | Agent card JSON |
| HTTP request/response | Message exchange via RemoteA2aAgent |
| Service discovery | Agent card discovery |
| API gateway | Orchestrator agent |
| Backend service | Specialized sub-agent |

The key difference: Instead of rigid JSON schemas, agents communicate with natural language. The LLM handles the "translation" between human intent and tool invocations.

## Common Patterns

### Pattern 1: Fan-Out
Orchestrator delegates to multiple specialized agents in parallel.

```
User: "Give me the weather in Paris and calculate 15+27"

Orchestrator
  +-> Weather Agent (parallel)
  +-> Math Agent (parallel)
```

### Pattern 2: Chain of Delegation
Agent delegates to another agent, which delegates further.

```
User -> Orchestrator -> Root Agent -> Weather Agent -> get_weather()
```

### Pattern 3: Conditional Routing
Orchestrator chooses which agent to call based on query type.

```
User: "What's the weather?"
Orchestrator -> Weather Agent

User: "What's 5+5?"
Orchestrator -> Math Agent
```

## Getting Started with A2A

To build your own A2A system:

1. **Identify specializations**: What distinct capabilities do you need? (weather, math, translation, etc.)

2. **Build focused agents**: Create one agent per specialization with its tools

3. **Expose via A2A**: Wrap agents with `to_a2a()` and deploy as HTTP services

4. **Create orchestrator**: Build a coordinator agent that delegates to your specialized agents using `RemoteA2aAgent`

5. **Test the flow**: Send queries and verify messages route correctly through the agent hierarchy

## Key Takeaways

- **A2A is HTTP for AI agents**: Standard protocol for agent-to-agent communication
- **Agent cards enable discovery**: Runtime capability advertisement without hardcoding
- **Delegation over ownership**: Agents coordinate with remote agents instead of owning all tools
- **Location transparency**: Remote agents look like local sub-agents to the caller
- **Microservices mindset applies**: Deployment, scaling, security patterns transfer directly

The power of A2A isn't in any single agent - it's in how agents compose. By treating agents as network services, you unlock the same architectural patterns that made microservices successful: modularity, scalability, and independent evolution.

---

**Next Steps**:
- Read the full README.md for setup and running instructions
- Explore ARCHITECTURE.md for detailed implementation specifics
- Check out the code in /agent/* to see how agents are structured
