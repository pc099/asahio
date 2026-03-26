"""
Example 4: Sessions and Traces

This example demonstrates:
- Creating agent sessions
- Making multi-turn conversations
- Viewing trace history
- Analyzing session graphs
"""

from asahio import Asahio

client = Asahio()

# Create an agent
agent = client.agents.create(
    name="Conversation Agent",
    routing_mode="AUTO",
    intervention_mode="ASSISTED",
)

print(f"Created agent: {agent.id}")

# Create a session for this agent
session = client.agents.create_session(
    agent.id,
    external_session_id="user_conv_12345"
)

print(f"Created session: {session.id}")

# Have a multi-turn conversation
print("\n" + "=" * 60)
print("MULTI-TURN CONVERSATION")
print("=" * 60)

conversation = []

turns = [
    "Hi, I need help with my order",
    "My order number is #12345",
    "I want to return an item",
    "How long does a return take?"
]

for i, user_message in enumerate(turns, 1):
    print(f"\nTurn {i}:")
    print(f"  User: {user_message}")

    # Add user message to conversation
    conversation.append({"role": "user", "content": user_message})

    # Make request with session tracking
    response = client.chat.completions.create(
        messages=conversation,
        agent_id=agent.id,
        session_id="user_conv_12345",
    )

    assistant_message = response.choices[0].message.content
    print(f"  Assistant: {assistant_message[:100]}...")

    # Add assistant response to conversation
    conversation.append({"role": "assistant", "content": assistant_message})

    # Show metadata
    print(f"  Model: {response.asahio.model_used}, Cache: {response.asahio.cache_hit}")

# List traces for this agent
print("\n" + "=" * 60)
print("TRACE HISTORY")
print("=" * 60)

traces = client.traces.list(
    agent_id=agent.id,
    limit=10
)

print(f"Total traces: {traces.total}")
print(f"Showing: {len(traces.data)} traces\n")

for trace in traces.data:
    print(f"Trace {trace.id}:")
    print(f"  Model: {trace.model_used}")
    print(f"  Latency: {trace.latency_ms}ms" if trace.latency_ms else "  Latency: N/A")
    print(f"  Cache: {trace.cache_hit}")
    print(f"  Cost: ${trace.cost:.4f}" if hasattr(trace, 'cost') else "  Cost: N/A")
    print()

# Get session details
print("=" * 60)
print("SESSION DETAILS")
print("=" * 60)

session_details = client.traces.get_session(session.id)
print(f"Session ID: {session_details.id}")
print(f"Agent ID: {session_details.agent_id}")
print(f"Started: {session_details.started_at}")
print(f"Last seen: {session_details.last_seen_at}")

# List sessions for agent
print("\n" + "=" * 60)
print("ALL SESSIONS FOR AGENT")
print("=" * 60)

sessions = client.traces.list_sessions(
    agent_id=agent.id,
    limit=5
)

for sess in sessions.data:
    print(f"Session: {sess.external_session_id}")
    print(f"  Started: {sess.started_at}")
    print(f"  Total steps: {sess.total_steps if hasattr(sess, 'total_steps') else 'N/A'}")

# Get session graph (for visualization)
print("\n" + "=" * 60)
print("SESSION GRAPH")
print("=" * 60)

try:
    graph = client.traces.get_session_graph(session.id)
    print(f"Total steps: {graph.total_steps}")
    print(f"Critical path steps: {graph.critical_path_steps}")

    print("\nGraph nodes:")
    for node in graph.nodes[:5]:  # Show first 5
        print(f"  {node['id']}: {node['type']} - {node.get('model_used', 'N/A')}")

    print(f"\n(Total: {len(graph.nodes)} nodes, {len(graph.edges)} edges)")
except Exception as e:
    print(f"Session graph not available yet: {e}")

client.close()
