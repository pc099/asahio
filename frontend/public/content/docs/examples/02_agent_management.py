"""
Example 2: Agent Management

This example demonstrates:
- Creating agents
- Tracking calls by agent
- Viewing agent statistics
- Mode transitions (OBSERVE → ASSISTED → AUTONOMOUS)
"""

from asahio import Asahio

client = Asahio()

# Create an agent
print("Creating agent...")
agent = client.agents.create(
    name="Customer Support Agent",
    slug="support-agent",
    description="Handles customer inquiries and support tickets",
    routing_mode="AUTO",
    intervention_mode="OBSERVE",  # Start in observe-only mode
    metadata={
        "team": "support",
        "version": "v1.0",
        "environment": "production"
    }
)

print(f"✓ Agent created: {agent.name} ({agent.id})")
print(f"  Routing mode: {agent.routing_mode}")
print(f"  Intervention mode: {agent.intervention_mode}")

# Make some calls tracked to this agent
print("\nMaking tracked calls...")
for i in range(5):
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": f"Test query #{i+1}"}],
        agent_id=agent.id,
    )
    print(f"  Call {i+1}: {response.asahio.model_used} - ${response.asahio.cost_with_asahio:.4f}")

# Check agent statistics
print("\nAgent Statistics:")
stats = client.agents.stats(agent.id)
print(f"  Total calls: {stats.total_calls}")
print(f"  Cache hits: {stats.cache_hits}")
print(f"  Cache hit rate: {stats.cache_hit_rate:.1%}")
print(f"  Avg latency: {stats.avg_latency_ms:.0f}ms" if stats.avg_latency_ms else "  Avg latency: N/A")
print(f"  Total sessions: {stats.total_sessions}")

# Check mode eligibility (after more observations, you can transition modes)
print("\nMode Transition Eligibility:")
eligibility = client.agents.mode_eligibility(agent.id)
print(f"  Eligible: {eligibility.eligible}")
print(f"  Current mode: {eligibility.current_mode}")
if eligibility.eligible:
    print(f"  Suggested mode: {eligibility.suggested_mode}")
    print(f"  Reason: {eligibility.reason}")
else:
    print(f"  Reason: {eligibility.reason}")

# If eligible, transition to ASSISTED mode
if eligibility.eligible and eligibility.suggested_mode == "ASSISTED":
    print("\nTransitioning to ASSISTED mode...")
    transition = client.agents.transition_mode(
        agent.id,
        target_mode="ASSISTED",
        operator_authorized=False,
    )
    print(f"  ✓ Transitioned from {transition.previous_mode} to {transition.new_mode}")
    print(f"  Reason: {transition.transition_reason}")

# View mode history
print("\nMode History:")
history = client.agents.mode_history(agent.id, limit=5)
for entry in history:
    print(f"  {entry.created_at}: {entry.previous_mode} → {entry.new_mode}")
    print(f"    Trigger: {entry.trigger}")

# Update agent metadata
print("\nUpdating agent...")
updated_agent = client.agents.update(
    agent.id,
    metadata={"team": "support", "version": "v1.1", "updated": "true"}
)
print(f"  ✓ Agent updated: {updated_agent.metadata}")

# List all agents
print("\nAll Agents:")
all_agents = client.agents.list()
for a in all_agents:
    print(f"  - {a.name} ({a.slug}): {a.routing_mode}/{a.intervention_mode}")

client.close()
