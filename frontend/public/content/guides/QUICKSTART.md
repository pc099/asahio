# ASAHIO Quickstart Guide

Get started with ASAHIO in 5 minutes. This guide will walk you through installation, authentication, and your first intelligent LLM call.

---

## What is ASAHIO?

ASAHIO is an LLM observability and routing platform that:
- **Routes intelligently** — Auto-select the optimal model based on cost, quality, and latency
- **Caches semantically** — Serve similar queries from cache (~0.5ms response time)
- **Detects anomalies** — Identify hallucinations and behavioral drift
- **Intervenes when needed** — Augment risky prompts or reroute high-risk calls

---

## 1. Installation

```bash
pip install asahio
```

**Requirements:** Python 3.9+

---

## 2. Get API Key

1. Sign up at [https://app.asahio.dev](https://app.asahio.dev)
2. Navigate to **Settings → API Keys**
3. Click **"Create API Key"**
4. Copy your key (starts with `asahio_live_`)

**Set environment variable:**
```bash
export ASAHIO_API_KEY="asahio_live_your_key_here"
```

---

## 3. Your First Call

```python
from asahio import Asahio

# Initialize client
client = Asahio()  # Reads from ASAHIO_API_KEY

# Make a call
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Explain quantum computing"}],
)

print(response.choices[0].message.content)
```

**That's it!** ASAHIO automatically:
- Selected the best model (likely `gpt-4o-mini`)
- Checked the cache first
- Routed to the cheapest provider
- Tracked cost and savings

---

## 4. Check Savings

```python
print(f"Model used: {response.asahio.model_used}")
print(f"Cost: ${response.asahio.cost_with_asahio:.4f}")
print(f"Saved: ${response.asahio.savings_usd:.4f} ({response.asahio.savings_pct:.1f}%)")
print(f"Cache hit: {response.asahio.cache_hit}")
```

**Expected output:**
```
Model used: gpt-4o-mini
Cost: $0.0008
Saved: $0.0042 (84.0%)
Cache hit: False
```

---

## 5. Enable Caching

Run the same query again:

```python
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Explain quantum computing"}],
)

print(f"Cache hit: {response.asahio.cache_hit}")  # True!
print(f"Latency: ~2ms")  # Blazing fast
```

**Semantic cache** means similar queries also hit the cache:

```python
# Slightly different wording, same intent
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "What is quantum computing?"}],
)

print(f"Cache tier: {response.asahio.cache_tier}")  # "semantic"
```

---

## 6. Create an Agent

Track calls by agent for behavioral analytics:

```python
agent = client.agents.create(
    name="My First Agent",
    routing_mode="AUTO",
    intervention_mode="OBSERVE",
)

print(f"Agent ID: {agent.id}")
```

Use in calls:

```python
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}],
    agent_id=agent.id,  # Track this agent
)
```

---

## 7. Check Agent Stats

After a few calls:

```python
stats = client.agents.stats(agent.id)

print(f"Total calls: {stats.total_calls}")
print(f"Cache hit rate: {stats.cache_hit_rate:.1%}")
print(f"Avg latency: {stats.avg_latency_ms:.0f}ms")
```

---

## 8. Tool Use (Function Calling)

Define a tool:

```python
from asahio.tools import function_to_tool

def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f'{{"temp": 72, "condition": "sunny", "location": "{location}"}}'

# Convert to tool schema
tool = function_to_tool(get_weather)
```

Call with tool:

```python
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "What's the weather in SF?"}],
    tools=[tool],
    tool_choice="auto",
)

# Check if tool was called
if response.asahio.tools_called:
    print(f"Tools called: {response.asahio.tools_called}")
```

---

## 9. Monitor Behavioral Analytics

After 100+ calls, check the agent's fingerprint:

```python
fingerprint = client.aba.get_fingerprint(agent.id)

print(f"Total observations: {fingerprint.total_observations}")
print(f"Success rate: {fingerprint.success_rate:.1%}")
print(f"Avg risk score: {fingerprint.avg_risk_score:.2f}")
```

Check for anomalies:

```python
anomalies = client.aba.list_anomalies(agent_id=agent.id)

for anomaly in anomalies:
    print(f"⚠️  {anomaly.anomaly_type}: {anomaly.description}")
```

---

## 10. Streaming

Enable streaming for real-time responses:

```python
stream = client.chat.completions.create(
    messages=[{"role": "user", "content": "Count to five"}],
    stream=True,
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## Complete Example

Put it all together:

```python
from asahio import Asahio
from asahio.tools import function_to_tool

# Initialize
client = Asahio()

# Create agent
agent = client.agents.create(
    name="Weather Assistant",
    routing_mode="AUTO",
    intervention_mode="ASSISTED",
)

# Define tool
def get_weather(location: str) -> str:
    """Get weather for a location."""
    return f'{{"temp": 72, "condition": "sunny"}}'

tool = function_to_tool(get_weather)

# Make call with tool
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "What's the weather in SF?"}],
    agent_id=agent.id,
    tools=[tool],
)

# Print response
print(response.choices[0].message.content)

# Check metadata
print(f"\nModel: {response.asahio.model_used}")
print(f"Cost: ${response.asahio.cost_with_asahio:.4f}")
print(f"Saved: ${response.asahio.savings_usd:.4f}")
print(f"Cache: {response.asahio.cache_hit}")
print(f"Risk: {response.asahio.risk_score:.2f}")

# Check agent stats
stats = client.agents.stats(agent.id)
print(f"\nAgent Stats:")
print(f"  Total calls: {stats.total_calls}")
print(f"  Cache hit rate: {stats.cache_hit_rate:.1%}")
```

---

## Next Steps

### Learn More
- **[SDK Guide](../sdk/SDK_GUIDE.md)** — Complete SDK documentation
- **[API Reference](../api/API_REFERENCE.md)** — All endpoints
- **[Examples Repository](https://github.com/asahio-ai/asahio-examples)** — Real-world examples

### Key Concepts
- **[Routing Modes](./ROUTING_MODES.md)** — AUTO, EXPLICIT, GUIDED
- **[Intervention Modes](./INTERVENTION_MODES.md)** — OBSERVE, ASSISTED, AUTONOMOUS
- **[Agent Behavioral Analytics](./ABA_GUIDE.md)** — Fingerprints, anomalies, transitions

### Production Ready
- **[Best Practices](./BEST_PRACTICES.md)** — Production deployment guide
- **[Error Handling](./ERROR_HANDLING.md)** — Retry logic and error codes
- **[Rate Limits](./RATE_LIMITS.md)** — Quotas and throttling

---

## Common Issues

### "No API key provided"

Set the environment variable:
```bash
export ASAHIO_API_KEY="asahio_live_your_key"
```

Or pass directly:
```python
client = Asahio(api_key="asahio_live_your_key")
```

### "RATE_LIMIT_EXCEEDED"

You've hit your plan's rate limit. Upgrade or wait for reset:

```python
# Check usage
usage = client.billing.get_usage()
print(f"Calls: {usage.total_calls}/{usage.included_calls}")
```

### "BUDGET_EXCEEDED"

Your monthly budget is exceeded. Adjust in dashboard or upgrade plan.

---

## Support

- **Dashboard:** [https://app.asahio.dev](https://app.asahio.dev)
- **Docs:** [https://docs.asahio.dev](https://docs.asahio.dev)
- **Email:** support@asahio.dev
- **GitHub:** [https://github.com/asahio-ai/asahio-python](https://github.com/asahio-ai/asahio-python)

---

**You're all set!** 🎉

Start building with ASAHIO and save up to 90% on LLM costs while improving reliability and observability.
