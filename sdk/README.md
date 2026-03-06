# ASAHIO Python SDK

Python client for the ASAHIO gateway and agent control plane.

## Install

```bash
cd sdk
pip install -e .
```

## Quick start

```python
from asahio import Asahio

client = Asahio(
    api_key="asahio_live_your_key",
    org_slug="your-org-slug",
)

response = client.chat.completions.create(
    messages=[{"role": "user", "content": "Summarize the incident timeline."}],
    routing_mode="AUTO",
    intervention_mode="OBSERVE",
)

print(response.choices[0].message.content)
print(response.asahio.model_used)
print(response.asahio.savings_usd)
```

## Compatibility aliases

The SDK still supports one deprecation window for older imports:

```python
from asahi import Asahi
from acorn import Acorn
```

Both aliases forward to the canonical ASAHIO client.

## Client options

- `routing_mode`: `AUTO`, `GUIDED`, or `EXPLICIT`
- `intervention_mode`: `OBSERVE`, `ASSISTED`, or `AUTONOMOUS`
- `agent_id`: bind a call to a registered agent
- `session_id`: bind a call to an agent session
- `model_endpoint_id`: target a BYOM endpoint
- `org_slug`: sends `X-Org-Slug` for multi-tenant dashboard setups

## Response metadata

Canonical metadata lives at `response.asahio`.

Legacy code can still read `response.asahi` during the migration window.

## Streaming

```python
stream = client.chat.completions.create(
    messages=[{"role": "user", "content": "Count to five."}],
    stream=True,
)

for chunk in stream:
    if chunk.choices and chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

The streaming parser ignores the gateway's trailing `event: asahio` metadata event so chunk iteration stays OpenAI-compatible.
