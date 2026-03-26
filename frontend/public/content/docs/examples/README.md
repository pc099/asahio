# ASAHIO Code Examples

Practical code examples demonstrating common ASAHIO use cases.

---

## Getting Started

All examples require the ASAHIO Python SDK:

```bash
pip install asahio
export ASAHIO_API_KEY="asahio_live_your_key"
```

---

## Examples

### 1. Basic Usage
**File:** `01_basic_usage.py`

Demonstrates the fundamentals:
- Initializing the ASAHIO client
- Making a simple chat completion request
- Accessing response metadata (cost, savings, model used)
- Understanding cache behavior

**Run:**
```bash
python 01_basic_usage.py
```

**Key Concepts:**
- OpenAI-compatible API
- AUTO routing mode
- ASAHIO metadata (cost, savings, model selection)
- Semantic caching

---

### 2. Agent Management
**File:** `02_agent_management.py`

Demonstrates agent lifecycle:
- Creating agents with custom configuration
- Tracking calls by agent
- Viewing agent statistics
- Mode transitions (OBSERVE → ASSISTED → AUTONOMOUS)
- Checking mode eligibility

**Run:**
```bash
python 02_agent_management.py
```

**Key Concepts:**
- Agent creation and configuration
- Mode transitions
- Agent statistics
- Behavioral tracking

---

### 3. Tool Use (Function Calling)
**File:** `03_tool_use.py`

Demonstrates tool use workflows:
- Converting Python functions to OpenAI tool schemas
- Making requests with tools
- Extracting tool calls from responses
- Executing tools and submitting results

**Run:**
```bash
python 03_tool_use.py
```

**Key Concepts:**
- `function_to_tool()` helper
- Tool execution workflow
- Multi-turn tool conversations
- Tool call extraction

---

### 4. Sessions and Traces
**File:** `04_sessions_and_traces.py`

Demonstrates session management and observability:
- Creating agent sessions
- Multi-turn conversations
- Viewing trace history
- Analyzing session graphs

**Run:**
```bash
python 04_sessions_and_traces.py
```

**Key Concepts:**
- Session creation
- Conversation history
- Trace querying
- Session graph analysis

---

### 5. Analytics and Cost Monitoring
**File:** `05_analytics_and_cost.py`

Demonstrates cost analytics:
- Viewing cost analytics over time periods
- Model usage breakdown
- Cache performance metrics
- Savings analysis
- Per-agent analytics
- Fleet-wide intervention monitoring

**Run:**
```bash
python 05_analytics_and_cost.py
```

**Key Concepts:**
- Cost tracking
- Model usage analytics
- Cache performance
- Savings attribution
- Billing integration

---

## Common Patterns

### Pattern 1: Simple Chat with Auto-Routing

```python
from asahio import Asahio

client = Asahio()

response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Hello"}],
    routing_mode="AUTO",  # Let ASAHIO pick the best model
)

print(response.choices[0].message.content)
print(f"Saved: ${response.asahio.savings_usd:.4f}")
```

### Pattern 2: Agent-Tracked Conversation

```python
# Create agent
agent = client.agents.create(
    name="My Agent",
    routing_mode="AUTO",
    intervention_mode="ASSISTED",
)

# Make tracked calls
response = client.chat.completions.create(
    messages=[...],
    agent_id=agent.id,
)

# View stats
stats = client.agents.stats(agent.id)
print(f"Cache hit rate: {stats.cache_hit_rate:.1%}")
```

### Pattern 3: Tool Use Workflow

```python
from asahio.tools import function_to_tool, extract_tool_calls, format_tool_result

# Define and convert tool
def my_function(param: str) -> str:
    """Function description."""
    return result

tool = function_to_tool(my_function)

# Request with tool
response = client.chat.completions.create(
    messages=[...],
    tools=[tool],
)

# Extract and execute
tool_calls = extract_tool_calls(response.model_dump())
for call in tool_calls:
    result = my_function(**json.loads(call['arguments']))
    tool_result = format_tool_result(
        tool_call_id=call['id'],
        content=result,
        name=call['name']
    )
```

### Pattern 4: Session Management

```python
# Create session
session = client.agents.create_session(
    agent_id="agt_123",
    external_session_id="user_session_xyz"
)

# Use in all related calls
for message in conversation:
    response = client.chat.completions.create(
        messages=[...],
        agent_id="agt_123",
        session_id="user_session_xyz",
    )
```

### Pattern 5: Cost Monitoring

```python
# Get analytics
overview = client.analytics.overview(
    start_date="2026-03-01",
    end_date="2026-03-31"
)

print(f"Total cost: ${overview.total_cost:.2f}")
print(f"Total savings: ${overview.total_savings:.2f}")

# Model breakdown
breakdown = client.analytics.model_breakdown()
for model in breakdown:
    print(f"{model.model_name}: {model.call_count} calls")
```

---

## Advanced Examples

### Streaming Responses

```python
stream = client.chat.completions.create(
    messages=[{"role": "user", "content": "Count to five"}],
    stream=True,
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Web Search

```python
response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Latest AI news?"}],
    enable_web_search=True,
    web_search_config={
        "max_results": 5,
        "recency_days": 7
    }
)
```

### Fallback Chains

```python
chain = client.chains.create(
    name="Cost-Optimized",
    slots=[
        {"priority": 1, "model": "gpt-4o-mini", "fallback_on_error": True},
        {"priority": 2, "model": "gpt-4o"}
    ]
)

response = client.chat.completions.create(
    messages=[...],
    routing_mode="GUIDED",
    chain_id=chain.id
)
```

### Async Usage

```python
from asahio import AsyncAsahio

async def main():
    async with AsyncAsahio() as client:
        response = await client.chat.completions.create(
            messages=[{"role": "user", "content": "Hello"}]
        )
        print(response.choices[0].message.content)

import asyncio
asyncio.run(main())
```

---

## Error Handling

```python
from asahio import AsahioError

try:
    response = client.chat.completions.create(messages=[...])
except AsahioError as e:
    if "RATE_LIMIT" in str(e):
        print("Rate limit exceeded - waiting before retry")
    elif "BUDGET_EXCEEDED" in str(e):
        print("Monthly budget exceeded")
    else:
        print(f"Error: {e}")
```

---

## Best Practices

1. **Always close clients:**
   ```python
   with Asahio() as client:
       # Use client
       pass
   # Auto-closed
   ```

2. **Use agent IDs for tracking:**
   ```python
   response = client.chat.completions.create(
       messages=[...],
       agent_id="agt_123",  # Track by agent
   )
   ```

3. **Monitor behavioral analytics:**
   ```python
   fingerprint = client.aba.get_fingerprint(agent.id)
   if fingerprint.success_rate < 0.95:
       print("⚠️ Low success rate")
   ```

4. **Set cost constraints:**
   ```python
   client.routing.create_constraint(
       agent_id="agt_123",
       constraint_type="cost_ceiling",
       value=0.01  # Max $0.01 per call
   )
   ```

5. **Use streaming for long responses:**
   ```python
   stream = client.chat.completions.create(
       messages=[...],
       stream=True
   )
   ```

---

## Next Steps

- **[SDK Guide](../sdk/SDK_GUIDE.md)** — Complete SDK documentation
- **[API Reference](../api/API_REFERENCE.md)** — All endpoints
- **[Quickstart](../guides/QUICKSTART.md)** — 5-minute getting started
- **[Best Practices](../guides/BEST_PRACTICES.md)** — Production tips

---

## Support

- **Dashboard:** https://app.asahio.dev
- **Docs:** https://docs.asahio.dev
- **GitHub:** https://github.com/asahio-ai/asahio-python
- **Email:** support@asahio.dev
