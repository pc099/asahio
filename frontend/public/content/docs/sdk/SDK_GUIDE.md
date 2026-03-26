# ASAHIO Python SDK Guide

Complete guide to using the ASAHIO Python SDK for intelligent LLM routing, caching, and observability.

---

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Authentication](#authentication)
- [Gateway API](#gateway-api)
- [Agent Management](#agent-management)
- [Agent Behavioral Analytics](#agent-behavioral-analytics)
- [Tool Use (Function Calling)](#tool-use-function-calling)
- [Chains & Fallbacks](#chains--fallbacks)
- [Provider Keys (BYOM)](#provider-keys-byom)
- [Routing & Constraints](#routing--constraints)
- [Traces & Sessions](#traces--sessions)
- [Interventions](#interventions)
- [Analytics](#analytics)
- [Billing](#billing)
- [Models & Endpoints](#models--endpoints)
- [Health Checks](#health-checks)
- [Async Usage](#async-usage)
- [Error Handling](#error-handling)
- [Best Practices](#best-practices)

---

## Installation

```bash
pip install asahio
```

**Requirements:**
- Python 3.9+
- Dependencies: `httpx`, `pydantic`, `anyio`

---

## Quick Start

```python
from asahio import Asahio

# Initialize client
client = Asahio(api_key="asahio_live_your_key")

# Make a request
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Explain quantum computing"}],
    routing_mode="AUTO",
    intervention_mode="ASSISTED",
)

print(response.choices[0].message.content)
print(f"Model: {response.asahio.model_used}")
print(f"Saved: ${response.asahio.savings_usd:.4f}")
```

---

## Authentication

### API Key Setup

**Option 1: Pass directly**
```python
from asahio import Asahio

client = Asahio(api_key="asahio_live_your_key")
```

**Option 2: Environment variable**
```bash
export ASAHIO_API_KEY="asahio_live_your_key"
```

```python
from asahio import Asahio

client = Asahio()  # Reads from ASAHIO_API_KEY
```

**Backward-compatible env vars:**
- `ASAHI_API_KEY`
- `ACORN_API_KEY`

### Client Configuration

```python
client = Asahio(
    api_key="asahio_live_your_key",
    base_url="https://api.asahio.dev",  # Custom gateway URL
    timeout=120.0,                       # Request timeout (seconds)
    max_retries=2,                       # Retry failed requests
    org_slug="your-org",                 # Multi-tenant org routing
)
```

---

## Gateway API

### Basic Chat Completion

```python
response = client.chat.completions.create(
    messages=[
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "What is Python?"}
    ],
    model="gpt-4o",  # Optional - AUTO mode will select best model
)

print(response.choices[0].message.content)
```

### Routing Modes

**AUTO — Intelligent Six-Factor Routing**
```python
response = client.chat.completions.create(
    messages=[...],
    routing_mode="AUTO",
    quality_preference="high",    # or "balanced", "fast"
    latency_preference="normal",  # or "low"
)
```

ASAHIO considers:
1. Prompt complexity
2. Context length
3. Agent behavioral history
4. Latency requirements
5. Budget constraints
6. Provider health

**EXPLICIT — Pin to Specific Model**
```python
response = client.chat.completions.create(
    messages=[...],
    routing_mode="EXPLICIT",
    model="gpt-4o",  # Exact model
)
```

**GUIDED — Rule-Based Routing**
```python
response = client.chat.completions.create(
    messages=[...],
    routing_mode="GUIDED",
    chain_id="chain_abc123",  # Fallback chain
)
```

### Intervention Modes

**OBSERVE — Watch Only**
```python
response = client.chat.completions.create(
    messages=[...],
    intervention_mode="OBSERVE",  # No modifications
)
```

**ASSISTED — Augment + Reroute**
```python
response = client.chat.completions.create(
    messages=[...],
    intervention_mode="ASSISTED",
    # ASAHIO may:
    # - Serve from cache
    # - Augment risky prompts
    # - Reroute high-risk calls
)
```

**AUTONOMOUS — Full Intervention** (requires authorization)
```python
response = client.chat.completions.create(
    messages=[...],
    intervention_mode="AUTONOMOUS",
    agent_id="agt_abc123",  # Must be authorized
    # ASAHIO may block calls if risk exceeds threshold
)
```

### Streaming

```python
stream = client.chat.completions.create(
    messages=[{"role": "user", "content": "Count to five"}],
    stream=True,
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Response Metadata

```python
response = client.chat.completions.create(messages=[...])

# ASAHIO metadata
metadata = response.asahio
print(f"Request ID: {metadata.request_id}")
print(f"Cache hit: {metadata.cache_hit}")
print(f"Cache tier: {metadata.cache_tier}")
print(f"Model requested: {metadata.model_requested}")
print(f"Model used: {metadata.model_used}")
print(f"Provider: {metadata.provider}")
print(f"Cost without ASAHIO: ${metadata.cost_without_asahio:.4f}")
print(f"Cost with ASAHIO: ${metadata.cost_with_asahio:.4f}")
print(f"Savings: ${metadata.savings_usd:.4f} ({metadata.savings_pct:.1f}%)")
print(f"Risk score: {metadata.risk_score}")
```

---

## Agent Management

### Create Agent

```python
agent = client.agents.create(
    name="Customer Support Agent",
    slug="support-agent",
    description="Handles customer inquiries",
    routing_mode="AUTO",
    intervention_mode="OBSERVE",
    metadata={"team": "support", "version": "v1"},
)

print(f"Agent ID: {agent.id}")
```

### List Agents

```python
agents = client.agents.list()

for agent in agents:
    print(f"{agent.name} ({agent.slug}) - {agent.routing_mode}")
```

### Get Agent

```python
agent = client.agents.get("agt_abc123")
print(f"Agent: {agent.name}")
print(f"Mode: {agent.routing_mode} / {agent.intervention_mode}")
```

### Update Agent

```python
updated_agent = client.agents.update(
    "agt_abc123",
    name="Updated Agent Name",
    routing_mode="GUIDED",
    intervention_mode="ASSISTED",
)
```

### Archive Agent

```python
client.agents.archive("agt_abc123")
```

### Agent Statistics

```python
stats = client.agents.stats("agt_abc123")

print(f"Total calls: {stats.total_calls}")
print(f"Cache hit rate: {stats.cache_hit_rate:.1%}")
print(f"Avg latency: {stats.avg_latency_ms:.0f}ms")
print(f"Total sessions: {stats.total_sessions}")
```

### Mode Transitions

**Check Eligibility**
```python
eligibility = client.agents.mode_eligibility("agt_abc123")

if eligibility.eligible:
    print(f"Eligible for: {eligibility.suggested_mode}")
    print(f"Reason: {eligibility.reason}")
else:
    print(f"Not eligible: {eligibility.reason}")
```

**Transition Mode**
```python
transition = client.agents.transition_mode(
    "agt_abc123",
    target_mode="ASSISTED",
    operator_authorized=False,  # Set True for AUTONOMOUS
)

print(f"Transitioned from {transition.previous_mode} to {transition.new_mode}")
```

**Mode History**
```python
history = client.agents.mode_history("agt_abc123", limit=10)

for entry in history:
    print(f"{entry.created_at}: {entry.previous_mode} → {entry.new_mode}")
    print(f"  Trigger: {entry.trigger}")
```

### Agent Sessions

```python
session = client.agents.create_session(
    "agt_abc123",
    external_session_id="user_session_xyz",
)

# Use in gateway calls
response = client.chat.completions.create(
    messages=[...],
    agent_id="agt_abc123",
    session_id="user_session_xyz",
)
```

---

## Agent Behavioral Analytics

### Get Fingerprint

```python
fingerprint = client.aba.get_fingerprint("agt_abc123")

print(f"Observations: {fingerprint.total_observations}")
print(f"Avg complexity: {fingerprint.avg_complexity:.2f}")
print(f"Success rate: {fingerprint.success_rate:.1%}")
print(f"Dominant type: {fingerprint.dominant_agent_type}")

# Tool usage
for tool in fingerprint.tool_usage_distribution:
    print(f"Tool: {tool['tool']}, Calls: {tool['count']}, Success: {tool['success_rate']:.1%}")
```

### List Fingerprints

```python
fingerprints = client.aba.list_fingerprints(
    min_observations=100,
    limit=50,
)

for fp in fingerprints.data:
    print(f"{fp.agent_id}: {fp.total_observations} observations")
```

### Organization Overview

```python
overview = client.aba.org_overview()

print(f"Total agents: {overview.total_agents}")
print(f"Agents in cold start: {overview.agents_in_cold_start}")
print(f"Ready for transition: {overview.agents_ready_for_transition}")
print(f"Fleet success rate: {overview.fleet_success_rate:.1%}")
```

### List Anomalies

```python
anomalies = client.aba.list_anomalies(
    agent_id="agt_abc123",
    severity="high",
)

for anomaly in anomalies:
    print(f"⚠️  {anomaly.anomaly_type}: {anomaly.description}")
    print(f"   Detected: {anomaly.detected_at}")
```

### Cold Start Status

```python
status = client.aba.cold_start_status("agt_abc123")

if status.in_cold_start:
    print(f"Progress: {status.progress:.0%}")
    print(f"Observations: {status.observations_count}/{status.min_observations_required}")
else:
    print("Agent ready!")
```

### Tag Hallucination

```python
client.aba.tag_hallucination(
    call_id="call_xyz789",
    hallucination_detected=True,
    notes="Fabricated citation to non-existent research paper",
)
```

### Manual Observation

```python
client.aba.create_observation(
    agent_id="agt_abc123",
    prompt="User question here",
    response="Agent response here",
    model_used="gpt-4o-mini",
)
```

---

## Tool Use (Function Calling)

### Define Tools

```python
from asahio.tools import function_to_tool

def get_weather(location: str, unit: str = "celsius") -> str:
    """Get current weather for a location.

    Args:
        location: City name
        unit: Temperature unit (celsius or fahrenheit)
    """
    # Your API call here
    return '{"temp": 22, "condition": "sunny"}'

# Convert to tool schema
tool = function_to_tool(get_weather)
```

### Call with Tools

```python
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "What's the weather in SF?"}],
    tools=[tool],
    tool_choice="auto",  # or "required", "none", or specific function
)
```

### Extract & Execute Tool Calls

```python
from asahio.tools import extract_tool_calls, format_tool_result

# Extract tool calls from response
tool_calls = extract_tool_calls(response.model_dump())

# Execute tools and collect results
tool_results = []
for call in tool_calls:
    if call["name"] == "get_weather":
        import json
        args = json.loads(call["arguments"])
        result = get_weather(**args)

        tool_results.append(format_tool_result(
            tool_call_id=call["id"],
            content=result,
            name=call["name"],
        ))

# Submit tool results
response = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "What's the weather in SF?"},
        response.choices[0].message.model_dump(),
        *tool_results,
    ],
)
```

### Web Search

```python
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Latest AI news?"}],
    enable_web_search=True,
    web_search_config={
        "max_results": 5,
        "recency_days": 7,
    },
)
```

### MCP (Model Context Protocol)

```python
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Analyze this codebase"}],
    mcp_servers=[
        {
            "name": "github",
            "config": {"repo": "asahio-ai/asahio"},
        }
    ],
)
```

### Computer Use

```python
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Take a screenshot"}],
    enable_computer_use=True,
    computer_use_config={
        "display_width": 1920,
        "display_height": 1080,
    },
)
```

---

## Chains & Fallbacks

### Create Chain

```python
chain = client.chains.create(
    name="Cost-Optimized Chain",
    description="Try cheap model first, fallback to premium",
    slots=[
        {
            "priority": 1,
            "model": "gpt-4o-mini",
            "provider": "openai",
            "fallback_on_error": True,
            "fallback_on_rate_limit": True,
        },
        {
            "priority": 2,
            "model": "gpt-4o",
            "provider": "openai",
        },
    ],
)

print(f"Chain ID: {chain.id}")
```

### List Chains

```python
chains = client.chains.list()

for chain in chains:
    print(f"{chain.name}: {len(chain.slots)} slots")
```

### Test Chain

```python
result = client.chains.test(
    "chain_abc123",
    prompt="Hello, world!",
)

print(f"Slot used: {result.slot_used}")
print(f"Model: {result.model_used}")
print(f"Fallback: {result.fallback_occurred}")
```

### Use Chain in Requests

```python
response = client.chat.completions.create(
    messages=[...],
    routing_mode="GUIDED",
    chain_id="chain_abc123",
)
```

---

## Provider Keys (BYOM)

### Add Provider Key

```python
key = client.provider_keys.create(
    provider="openai",
    api_key="sk-proj-...",
    name="OpenAI Production Key",
    metadata={"team": "engineering"},
)

print(f"Key ID: {key.id}")
```

### List Keys

```python
keys = client.provider_keys.list()

for key in keys:
    print(f"{key.provider}: {key.name} (...{key.key_suffix})")
```

### Rotate Key

```python
updated_key = client.provider_keys.rotate(
    "pk_abc123",
    new_api_key="sk-proj-new_key_here",
)
```

### Delete Key

```python
client.provider_keys.delete("pk_abc123")
```

---

## Routing & Constraints

### Dry Run

```python
result = client.routing.dry_run(
    prompt="Explain quantum computing",
    agent_id="agt_abc123",
    constraints={
        "max_cost_per_call": 0.01,
        "max_latency_ms": 2000,
        "allowed_providers": ["openai", "anthropic"],
    },
)

print(f"Selected: {result.selected_model} ({result.selected_provider})")
print(f"Estimated cost: ${result.estimated_cost:.4f}")
print(f"Estimated latency: {result.estimated_latency_ms}ms")
```

### Get Routing Decision

```python
decision = client.routing.get_decision("call_xyz789")

print(f"Model: {decision.selected_model}")
print(f"Reason: {decision.routing_reason}")
print(f"Factors: {decision.routing_factors}")
```

### Create Constraint

```python
constraint = client.routing.create_constraint(
    agent_id="agt_abc123",
    constraint_type="cost_ceiling",
    value=0.01,  # Max $0.01 per call
    priority=1,
)
```

### List Constraints

```python
constraints = client.routing.list_constraints(agent_id="agt_abc123")

for c in constraints:
    print(f"{c.constraint_type}: {c.value}")
```

---

## Traces & Sessions

### Get Trace

```python
trace = client.traces.get("tr_abc123")

print(f"Model: {trace.model_used}")
print(f"Latency: {trace.latency_ms}ms")
print(f"Cost: ${trace.cost:.4f}")
```

### List Traces

```python
traces = client.traces.list(
    agent_id="agt_abc123",
    limit=100,
)

for trace in traces.data:
    print(f"{trace.created_at}: {trace.model_used} - ${trace.cost:.4f}")
```

### Get Session

```python
session = client.traces.get_session("sess_abc123")

print(f"Agent: {session.agent_id}")
print(f"Steps: {session.total_steps}")
print(f"Started: {session.started_at}")
```

### Session Graph

```python
graph = client.traces.get_session_graph("sess_abc123")

print(f"Total steps: {graph.total_steps}")
print(f"Critical path: {graph.critical_path_steps}")

for node in graph.nodes:
    print(f"  {node['id']}: {node['model_used']} - {node['latency_ms']}ms")
```

### Session Steps

```python
steps = client.traces.list_session_steps("sess_abc123")

for step in steps:
    print(f"Step {step.step_number}: {step.model_used}")
```

---

## Interventions

### List Logs

```python
logs = client.interventions.list_logs(
    agent_id="agt_abc123",
    action_type="rerouted",
    limit=50,
)

for log in logs.data:
    print(f"{log.created_at}: {log.action_type}")
    print(f"  Reason: {log.reason}")
```

### Get Stats

```python
stats = client.interventions.get_stats(agent_id="agt_abc123")

print(f"Total interventions: {stats.total_interventions}")
print(f"Augmented: {stats.augmented_count}")
print(f"Rerouted: {stats.rerouted_count}")
print(f"Blocked: {stats.blocked_count}")
print(f"Intervention rate: {stats.intervention_rate:.1%}")
```

### Fleet Overview

```python
overview = client.interventions.fleet_overview()

print(f"Total agents: {overview.total_agents}")
print(f"24h interventions: {overview.total_interventions_24h}")
print(f"Avg risk: {overview.avg_risk_score:.2f}")

for agent in overview.high_risk_agents:
    print(f"  {agent['agent_id']}: risk {agent['risk_score']:.2f}")
```

---

## Analytics

### Overview

```python
overview = client.analytics.overview(
    start_date="2026-03-01",
    end_date="2026-03-31",
)

print(f"Total calls: {overview.total_calls}")
print(f"Total cost: ${overview.total_cost:.2f}")
print(f"Total savings: ${overview.total_savings:.2f}")
print(f"Cache hit rate: {overview.cache_hit_rate:.1%}")
```

### Model Breakdown

```python
breakdown = client.analytics.model_breakdown()

for model in breakdown:
    print(f"{model.model_name}: {model.call_count} calls, ${model.total_cost:.2f}")
```

### Cache Performance

```python
cache = client.analytics.cache_performance()

print(f"Overall hit rate: {cache.overall_hit_rate:.1%}")
print(f"Tier 1 hits: {cache.tier1_hits}")
print(f"Tier 2 hits: {cache.tier2_hits}")
print(f"Cache savings: ${cache.savings_from_cache_usd:.2f}")
```

### Savings Breakdown

```python
savings = client.analytics.savings()

for source in savings:
    print(f"{source.source}: ${source.savings_usd:.2f} ({source.percentage_of_total:.1f}%)")
```

---

## Billing

### Get Subscription

```python
subscription = client.billing.get_subscription()

print(f"Plan: {subscription.plan_id}")
print(f"Status: {subscription.status}")
print(f"Period: {subscription.current_period_start} to {subscription.current_period_end}")
```

### List Plans

```python
plans = client.billing.list_plans()

for plan in plans:
    print(f"{plan.name}: ${plan.price_monthly}/mo")
    print(f"  Included calls: {plan.included_calls}")
```

### Get Usage

```python
usage = client.billing.get_usage(
    start_date="2026-03-01",
    end_date="2026-03-26",
)

print(f"Total calls: {usage.total_calls}")
print(f"Included: {usage.included_calls}")
print(f"Overage: {usage.overage_calls}")
print(f"Estimated cost: ${usage.estimated_cost:.2f}")
```

### Update Subscription

```python
subscription = client.billing.update_subscription(plan_id="enterprise")
```

---

## Models & Endpoints

### List Models

```python
models = client.models.list()

for model in models:
    print(f"{model['id']}: ${model['input_cost_per_1m']:.2f}/1M tokens")
```

### Create Custom Endpoint

```python
endpoint = client.models.create_endpoint(
    name="Fine-tuned GPT-4o",
    base_model="gpt-4o",
    endpoint_url="https://api.openai.com/v1/chat/completions",
    api_key="sk-proj-...",
    metadata={"version": "v2"},
)

# Use in requests
response = client.chat.completions.create(
    messages=[...],
    model_endpoint_id=endpoint["id"],
    routing_mode="EXPLICIT",
)
```

### List Custom Endpoints

```python
endpoints = client.models.list_endpoints()

for ep in endpoints:
    print(f"{ep['name']}: {ep['base_model']}")
```

---

## Health Checks

### Overall Health

```python
health = client.health.check()

print(f"Status: {health.status}")
print(f"Version: {health.version}")

for component, status in health.components.items():
    print(f"  {component}: {status}")
```

### Provider Health

```python
providers = client.health.list_providers()

for provider in providers:
    print(f"{provider.provider}: {provider.status}")
    if provider.error:
        print(f"  Error: {provider.error}")
```

---

## Async Usage

All resources have async versions:

```python
from asahio import AsyncAsahio

async def main():
    client = AsyncAsahio(api_key="asahio_live_your_key")

    # All methods are async
    response = await client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}],
    )

    agents = await client.agents.list()
    stats = await client.agents.stats(agents[0].id)

    await client.close()

# Context manager
async with AsyncAsahio(api_key="...") as client:
    response = await client.chat.completions.create(...)
```

---

## Error Handling

```python
from asahio import Asahio, AsahioError

client = Asahio(api_key="...")

try:
    response = client.chat.completions.create(
        messages=[{"role": "user", "content": "Hello"}],
    )
except AsahioError as e:
    print(f"Error: {e}")
    # Check error details
    if "RATE_LIMIT" in str(e):
        # Handle rate limit
        pass
    elif "BUDGET_EXCEEDED" in str(e):
        # Handle budget exceeded
        pass
```

**Common Errors:**
- `INVALID_REQUEST` — Malformed request
- `UNAUTHORIZED` — Invalid API key
- `NOT_FOUND` — Resource not found
- `RATE_LIMIT_EXCEEDED` — Rate limit hit
- `BUDGET_EXCEEDED` — Budget limit hit
- `PROVIDER_ERROR` — Upstream provider error

---

## Best Practices

### 1. Use Agent IDs

Track calls by agent for better analytics:

```python
response = client.chat.completions.create(
    messages=[...],
    agent_id="agt_abc123",  # Track this agent
)
```

### 2. Leverage Sessions

Group related calls into sessions:

```python
# Create session
session = client.agents.create_session(
    "agt_abc123",
    external_session_id="user_conv_xyz",
)

# Use in all calls
for user_message in conversation:
    response = client.chat.completions.create(
        messages=[...],
        agent_id="agt_abc123",
        session_id="user_conv_xyz",
    )
```

### 3. Start with OBSERVE Mode

Test new agents in OBSERVE mode first:

```python
agent = client.agents.create(
    name="New Agent",
    routing_mode="AUTO",
    intervention_mode="OBSERVE",  # No modifications
)

# After 100+ observations, check eligibility
eligibility = client.aba.mode_eligibility(agent.id)
if eligibility.eligible:
    client.agents.transition_mode(agent.id, target_mode="ASSISTED")
```

### 4. Monitor Fingerprints

Check agent behavioral fingerprints regularly:

```python
fingerprint = client.aba.get_fingerprint("agt_abc123")

if fingerprint.success_rate < 0.95:
    print("⚠️ Low success rate - investigate")

if fingerprint.avg_risk_score > 0.5:
    print("⚠️ High risk score - review prompts")
```

### 5. Use Tool Helpers

Don't manually build tool schemas:

```python
from asahio.tools import function_to_tool

# Convert Python function automatically
tool = function_to_tool(my_function)

response = client.chat.completions.create(
    messages=[...],
    tools=[tool],
)
```

### 6. Enable Web Search for Research Tasks

```python
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Latest AI breakthroughs?"}],
    enable_web_search=True,  # Get current info
    web_search_config={"recency_days": 7},
)
```

### 7. Set Routing Constraints

Prevent cost overruns:

```python
client.routing.create_constraint(
    agent_id="agt_abc123",
    constraint_type="cost_ceiling",
    value=0.01,  # Max $0.01 per call
)
```

### 8. Use Fallback Chains

Build resilient routing:

```python
chain = client.chains.create(
    name="Resilient Chain",
    slots=[
        {"priority": 1, "model": "gpt-4o-mini", "fallback_on_error": True},
        {"priority": 2, "model": "claude-sonnet-4-5", "fallback_on_error": True},
        {"priority": 3, "model": "gpt-4o"},  # Last resort
    ],
)
```

### 9. Monitor Interventions

Track when ASAHIO intervenes:

```python
stats = client.interventions.get_stats("agt_abc123")

if stats.intervention_rate > 0.20:
    print("⚠️ High intervention rate - review agent behavior")
```

### 10. Close Clients

Always close clients when done:

```python
# Context manager (recommended)
with Asahio(api_key="...") as client:
    response = client.chat.completions.create(...)
# Auto-closed

# Or manually
client = Asahio(api_key="...")
try:
    response = client.chat.completions.create(...)
finally:
    client.close()
```

---

## Examples Repository

Find more examples at: https://github.com/asahio-ai/asahio-examples

- Basic usage
- Tool use workflows
- Agent lifecycle management
- Session graph analysis
- Cost optimization strategies
- Production best practices

---

## Support

- **Documentation:** https://docs.asahio.dev
- **API Reference:** https://docs.asahio.dev/api
- **GitHub:** https://github.com/asahio-ai/asahio-python
- **Support:** support@asahio.dev
