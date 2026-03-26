# ASAHIO API Reference

**Base URL:** `https://api.asahio.dev`

**Version:** v1

---

## Table of Contents

- [Authentication](#authentication)
- [Gateway API](#gateway-api)
- [Agents](#agents)
- [Agent Behavioral Analytics (ABA)](#agent-behavioral-analytics-aba)
- [Chains](#chains)
- [Provider Keys](#provider-keys)
- [Routing](#routing)
- [Traces](#traces)
- [Interventions](#interventions)
- [Analytics](#analytics)
- [Billing](#billing)
- [Models](#models)
- [Health](#health)
- [Errors](#errors)

---

## Authentication

ASAHIO uses API keys for authentication. Include your API key in the `Authorization` header:

```http
Authorization: Bearer asahio_live_your_key_here
```

**Header Format:**
```
Authorization: Bearer <api_key>
```

**API Key Prefixes:**
- `asahio_live_` — Production keys
- `asahio_test_` — Test mode keys

**Getting an API Key:**
1. Sign up at https://asahio.in
2. Navigate to Settings → API Keys
3. Click "Create API Key"
4. Copy and securely store your key (shown only once)

---

## Gateway API

### POST /v1/chat/completions

OpenAI-compatible chat completions endpoint with ASAHIO intelligent routing and caching.

**Request:**

```json
{
  "model": "gpt-4o",
  "messages": [
    {"role": "user", "content": "Explain quantum computing"}
  ],
  "stream": false,
  "routing_mode": "AUTO",
  "intervention_mode": "ASSISTED",
  "quality_preference": "high",
  "latency_preference": "normal",
  "agent_id": "agt_abc123",
  "session_id": "session_xyz",
  "model_endpoint_id": "ep_custom123",
  "chain_id": "chain_fallback",

  // SDK v2 agentic parameters
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "get_weather",
        "description": "Get weather for a location",
        "parameters": {
          "type": "object",
          "properties": {
            "location": {"type": "string"}
          },
          "required": ["location"]
        }
      }
    }
  ],
  "tool_choice": "auto",
  "enable_web_search": true,
  "web_search_config": {
    "max_results": 5,
    "recency_days": 7
  },
  "mcp_servers": [
    {
      "name": "github",
      "config": {"repo": "asahio-ai/asahio"}
    }
  ],
  "enable_computer_use": false,
  "computer_use_config": null
}
```

**Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `model` | string | No | Model to use (defaults to AUTO selection) |
| `messages` | array | Yes | Array of message objects with `role` and `content` |
| `stream` | boolean | No | Enable SSE streaming (default: false) |
| `routing_mode` | string | No | `AUTO`, `EXPLICIT`, or `GUIDED` (default: AUTO) |
| `intervention_mode` | string | No | `OBSERVE`, `ASSISTED`, or `AUTONOMOUS` (default: OBSERVE) |
| `quality_preference` | string | No | `high`, `balanced`, or `fast` (default: high) |
| `latency_preference` | string | No | `low` or `normal` (default: normal) |
| `agent_id` | string | No | Agent ID to track calls |
| `session_id` | string | No | External session ID for multi-turn conversations |
| `model_endpoint_id` | string | No | Custom model endpoint (BYOM) |
| `chain_id` | string | No | Fallback chain for GUIDED mode |
| `tools` | array | No | OpenAI-compatible tool definitions |
| `tool_choice` | string/object | No | `auto`, `none`, `required`, or specific function |
| `enable_web_search` | boolean | No | Enable web search (default: false) |
| `web_search_config` | object | No | Web search configuration |
| `mcp_servers` | array | No | MCP server configurations |
| `enable_computer_use` | boolean | No | Enable computer use (Anthropic) |
| `computer_use_config` | object | No | Computer use configuration |

**Response:**

```json
{
  "id": "chatcmpl_abc123",
  "object": "chat.completion",
  "created": 1711234567,
  "model": "gpt-4o-mini",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Quantum computing is...",
        "tool_calls": [
          {
            "id": "call_abc",
            "type": "function",
            "function": {
              "name": "get_weather",
              "arguments": "{\"location\": \"San Francisco\"}"
            }
          }
        ]
      },
      "finish_reason": "tool_calls"
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 150,
    "total_tokens": 170
  },
  "asahio": {
    "request_id": "req_xyz789",
    "cache_hit": false,
    "cache_tier": null,
    "model_requested": "gpt-4o",
    "model_used": "gpt-4o-mini",
    "provider": "openai",
    "routing_mode": "AUTO",
    "intervention_mode": "ASSISTED",
    "cost_without_asahio": 0.0050,
    "cost_with_asahio": 0.0008,
    "savings_usd": 0.0042,
    "savings_pct": 84.0,
    "routing_reason": "Selected cheaper model with equivalent quality",
    "risk_score": 0.12,
    "intervention_level": 0,
    "tools_called": ["get_weather"]
  }
}
```

**Streaming Response:**

Enable streaming with `"stream": true`:

```
data: {"id":"chatcmpl_1","object":"chat.completion.chunk","choices":[{"delta":{"content":"Quantum"},"index":0}]}

data: {"id":"chatcmpl_1","object":"chat.completion.chunk","choices":[{"delta":{"content":" computing"},"index":0}]}

data: [DONE]

event: asahio
data: {"request_id":"req_123","cache_hit":false,"savings_usd":0.0042}
```

---

## Agents

Manage agent configurations and lifecycle.

### POST /agents

Create a new agent.

**Request:**
```json
{
  "name": "Customer Support Agent",
  "slug": "support-agent",
  "description": "Handles customer inquiries",
  "routing_mode": "AUTO",
  "intervention_mode": "OBSERVE",
  "model_endpoint_id": null,
  "metadata": {"team": "support"},
  "blueprint_id": null
}
```

**Response:**
```json
{
  "id": "agt_abc123",
  "organisation_id": "org_xyz",
  "name": "Customer Support Agent",
  "slug": "support-agent",
  "description": "Handles customer inquiries",
  "routing_mode": "AUTO",
  "intervention_mode": "OBSERVE",
  "model_endpoint_id": null,
  "is_active": true,
  "metadata": {"team": "support"},
  "risk_threshold_overrides": null,
  "mode_entered_at": "2026-03-26T12:00:00Z",
  "autonomous_authorized_at": null,
  "autonomous_authorized_by": null,
  "blueprint_id": null,
  "created_at": "2026-03-26T12:00:00Z",
  "updated_at": "2026-03-26T12:00:00Z"
}
```

### GET /agents

List all agents.

**Query Parameters:**
- `limit` (number) — Max results (default: 50)
- `offset` (number) — Pagination offset (default: 0)

**Response:**
```json
{
  "data": [
    {
      "id": "agt_abc123",
      "name": "Customer Support Agent",
      "slug": "support-agent",
      "routing_mode": "AUTO",
      "intervention_mode": "OBSERVE",
      "is_active": true,
      "created_at": "2026-03-26T12:00:00Z"
    }
  ],
  "pagination": {
    "total": 1,
    "limit": 50,
    "offset": 0
  }
}
```

### GET /agents/{id}

Get agent by ID.

### PATCH /agents/{id}

Update agent.

**Request:**
```json
{
  "name": "Updated Agent Name",
  "routing_mode": "GUIDED",
  "intervention_mode": "ASSISTED"
}
```

### POST /agents/{id}/archive

Archive (soft delete) an agent.

### GET /agents/{id}/stats

Get agent statistics.

**Response:**
```json
{
  "agent_id": "agt_abc123",
  "total_calls": 1250,
  "cache_hits": 562,
  "cache_hit_rate": 0.4496,
  "avg_latency_ms": 234.5,
  "total_input_tokens": 125000,
  "total_output_tokens": 87500,
  "total_sessions": 89
}
```

### GET /agents/{id}/mode-eligibility

Check if agent is eligible for mode transition.

**Response:**
```json
{
  "agent_id": "agt_abc123",
  "current_mode": "AUTO",
  "eligible": true,
  "suggested_mode": "ASSISTED",
  "reason": "Agent has 1000+ observations with 98% success rate",
  "evidence": {
    "total_observations": 1250,
    "success_rate": 0.98,
    "error_rate": 0.02,
    "avg_risk_score": 0.15
  }
}
```

### POST /agents/{id}/mode-transition

Transition agent to new mode.

**Request:**
```json
{
  "target_mode": "ASSISTED",
  "operator_authorized": false
}
```

**Response:**
```json
{
  "agent_id": "agt_abc123",
  "previous_mode": "AUTO",
  "new_mode": "ASSISTED",
  "transition_reason": "Automatic transition based on performance metrics"
}
```

### GET /agents/{id}/mode-history

Get mode transition history.

**Query Parameters:**
- `limit` (number) — Max results (default: 50)

### POST /agents/{id}/sessions

Create a new session for an agent.

**Request:**
```json
{
  "external_session_id": "session_abc123"
}
```

---

## Agent Behavioral Analytics (ABA)

Access agent behavioral fingerprints, anomalies, and risk data.

### GET /aba/fingerprints/{agent_id}

Get behavioral fingerprint for an agent.

**Response:**
```json
{
  "agent_id": "agt_abc123",
  "total_observations": 1250,
  "avg_complexity": 0.65,
  "avg_context_length": 1850,
  "avg_latency_ms": 234.5,
  "success_rate": 0.98,
  "error_rate": 0.02,
  "avg_risk_score": 0.15,
  "dominant_agent_type": "RAG",
  "tool_usage_distribution": [
    {"tool": "search", "count": 450, "success_rate": 0.96},
    {"tool": "calculator", "count": 200, "success_rate": 0.99}
  ],
  "tool_success_rates": {"search": 0.96, "calculator": 0.99},
  "tool_risk_correlation": {"search": 0.12, "calculator": 0.05},
  "preferred_model_by_tool": {"search": "gpt-4o", "calculator": "gpt-4o-mini"},
  "created_at": "2026-03-20T10:00:00Z",
  "updated_at": "2026-03-26T12:00:00Z"
}
```

### GET /aba/fingerprints

List all fingerprints.

**Query Parameters:**
- `min_observations` (number) — Minimum observations required (default: 0)
- `limit` (number) — Max results (default: 50)
- `offset` (number) — Pagination offset (default: 0)

### GET /aba/org/overview

Get organization-wide ABA overview.

**Response:**
```json
{
  "total_agents": 15,
  "total_observations": 18750,
  "avg_observations_per_agent": 1250,
  "agents_in_cold_start": 3,
  "agents_ready_for_transition": 5,
  "fleet_avg_risk_score": 0.18,
  "fleet_success_rate": 0.96
}
```

### GET /aba/structural-records

List structural records.

**Query Parameters:**
- `agent_id` (string) — Filter by agent
- `limit` (number) — Max results (default: 50)
- `offset` (number) — Pagination offset (default: 0)

### GET /aba/risk-prior

Get risk prior from Model C global pool.

**Query Parameters:**
- `agent_type` (string) — Required. Agent type classification
- `complexity_bucket` (number) — Required. Complexity bucket (0.0-1.0)

**Response:**
```json
{
  "agent_type": "RAG",
  "complexity_bucket": 0.65,
  "prior_risk_score": 0.18,
  "confidence": 0.85,
  "sample_size": 5000
}
```

### GET /aba/anomalies

List detected anomalies.

**Query Parameters:**
- `agent_id` (string) — Filter by agent
- `severity` (string) — `low`, `medium`, `high`

**Response:**
```json
{
  "data": [
    {
      "id": "anom_123",
      "agent_id": "agt_abc123",
      "anomaly_type": "latency_spike",
      "severity": "high",
      "description": "Latency exceeded 3σ threshold (1250ms vs avg 234ms)",
      "detected_at": "2026-03-26T11:30:00Z",
      "call_id": "call_xyz"
    }
  ]
}
```

### GET /aba/cold-start-status/{agent_id}

Get cold start status for an agent.

**Response:**
```json
{
  "agent_id": "agt_abc123",
  "in_cold_start": false,
  "observations_count": 1250,
  "min_observations_required": 100,
  "progress": 1.0,
  "estimated_completion": null
}
```

### POST /aba/observation

Create manual ABA observation.

**Request:**
```json
{
  "agent_id": "agt_abc123",
  "prompt": "User question here",
  "response": "Agent response here",
  "model_used": "gpt-4o-mini",
  "latency_ms": 245,
  "success": true
}
```

### POST /aba/calls/{call_id}/tag

Tag a call as hallucination.

**Request:**
```json
{
  "hallucination_detected": true,
  "notes": "Fabricated citation to non-existent paper"
}
```

---

## Chains

Manage fallback chains for GUIDED routing mode.

### POST /providers/chains

Create a fallback chain.

**Request:**
```json
{
  "name": "Cost-Optimized Chain",
  "description": "Try cheap model first, fallback to premium",
  "slots": [
    {
      "priority": 1,
      "model": "gpt-4o-mini",
      "provider": "openai",
      "fallback_on_error": true,
      "fallback_on_rate_limit": true
    },
    {
      "priority": 2,
      "model": "gpt-4o",
      "provider": "openai",
      "fallback_on_error": false,
      "fallback_on_rate_limit": false
    }
  ]
}
```

### GET /providers/chains

List all chains.

### GET /providers/chains/{id}

Get chain by ID.

### DELETE /providers/chains/{id}

Delete a chain.

### POST /providers/chains/{id}/test

Test a chain with sample prompt.

**Request:**
```json
{
  "prompt": "Hello, world!"
}
```

**Response:**
```json
{
  "success": true,
  "slot_used": 1,
  "model_used": "gpt-4o-mini",
  "response": "Hello! How can I help you?",
  "fallback_occurred": false,
  "latency_ms": 234
}
```

---

## Provider Keys

Manage BYOM (Bring Your Own Model) provider API keys.

### POST /providers/keys

Add provider API key.

**Request:**
```json
{
  "provider": "openai",
  "api_key": "sk-proj-...",
  "name": "OpenAI Production Key",
  "metadata": {"team": "engineering"}
}
```

### GET /providers/keys

List all provider keys.

**Response:**
```json
{
  "data": [
    {
      "id": "pk_abc123",
      "provider": "openai",
      "name": "OpenAI Production Key",
      "key_suffix": "...abc123",
      "is_active": true,
      "created_at": "2026-03-26T12:00:00Z"
    }
  ]
}
```

### GET /providers/keys/{id}

Get provider key by ID.

### DELETE /providers/keys/{id}

Delete provider key.

### POST /providers/keys/{id}/rotate

Rotate provider key.

**Request:**
```json
{
  "new_api_key": "sk-proj-new_key_here"
}
```

---

## Routing

Routing decisions and constraints.

### POST /routing/dry-run

Dry run routing decision without executing.

**Request:**
```json
{
  "prompt": "Explain quantum computing",
  "agent_id": "agt_abc123",
  "constraints": {
    "max_cost_per_call": 0.01,
    "max_latency_ms": 2000,
    "allowed_providers": ["openai", "anthropic"]
  }
}
```

**Response:**
```json
{
  "selected_model": "gpt-4o-mini",
  "selected_provider": "openai",
  "routing_reason": "Lowest cost model meeting quality requirements",
  "estimated_cost": 0.0008,
  "estimated_latency_ms": 250,
  "routing_factors": {
    "complexity_score": 0.65,
    "context_length": 1850,
    "budget_constraint": 0.01,
    "quality_preference": "high"
  }
}
```

### GET /routing/decisions/{call_id}

Get routing decision for a specific call.

### GET /routing/constraints

List routing constraints.

**Query Parameters:**
- `agent_id` (string) — Filter by agent

### POST /routing/constraints

Create routing constraint.

**Request:**
```json
{
  "agent_id": "agt_abc123",
  "constraint_type": "cost_ceiling",
  "value": 0.01,
  "priority": 1
}
```

### DELETE /routing/constraints/{id}

Delete constraint.

---

## Traces

Call traces and session analytics.

### GET /traces/{id}

Get trace by ID.

### GET /traces

List traces.

**Query Parameters:**
- `agent_id` (string) — Filter by agent
- `session_id` (string) — Filter by session
- `limit` (number) — Max results (default: 50)
- `offset` (number) — Pagination offset (default: 0)

### GET /traces/sessions/{id}

Get session by ID.

### GET /traces/sessions

List sessions.

**Query Parameters:**
- `agent_id` (string) — Filter by agent
- `limit` (number) — Max results (default: 50)
- `offset` (number) — Pagination offset (default: 0)

### GET /traces/sessions/{id}/graph

Get session graph visualization data.

**Response:**
```json
{
  "session_id": "sess_abc123",
  "total_steps": 12,
  "critical_path_steps": 8,
  "nodes": [
    {
      "id": "call_1",
      "type": "call",
      "model_used": "gpt-4o-mini",
      "latency_ms": 234,
      "is_critical_path": true
    }
  ],
  "edges": [
    {
      "from": "call_1",
      "to": "call_2",
      "relationship": "depends_on"
    }
  ]
}
```

### GET /traces/sessions/{id}/steps

List all steps in a session.

---

## Interventions

Intervention logs and statistics.

### GET /interventions/logs

List intervention logs.

**Query Parameters:**
- `agent_id` (string) — Filter by agent
- `action_type` (string) — `augmented`, `rerouted`, `blocked`
- `limit` (number) — Max results (default: 50)
- `offset` (number) — Pagination offset (default: 0)

### GET /interventions/stats

Get intervention statistics.

**Query Parameters:**
- `agent_id` (string) — Filter by agent

**Response:**
```json
{
  "agent_id": "agt_abc123",
  "total_interventions": 125,
  "augmented_count": 80,
  "rerouted_count": 40,
  "blocked_count": 5,
  "intervention_rate": 0.10,
  "avg_risk_score_when_intervened": 0.68
}
```

### GET /interventions/fleet/overview

Get fleet-wide intervention overview.

**Response:**
```json
{
  "total_agents": 15,
  "total_interventions_24h": 450,
  "avg_risk_score": 0.22,
  "agents_in_autonomous_mode": 3,
  "high_risk_agents": [
    {
      "agent_id": "agt_xyz",
      "risk_score": 0.75,
      "intervention_count_24h": 50
    }
  ]
}
```

---

## Analytics

Cost, savings, and performance analytics.

### GET /analytics/overview

Get analytics overview.

**Query Parameters:**
- `agent_id` (string) — Filter by agent
- `start_date` (string) — ISO 8601 date
- `end_date` (string) — ISO 8601 date

**Response:**
```json
{
  "total_calls": 10000,
  "total_cost": 125.50,
  "total_savings": 450.30,
  "avg_cost_per_call": 0.0126,
  "cache_hit_rate": 0.42,
  "avg_latency_ms": 245.5
}
```

### GET /analytics/model-breakdown

Get model usage breakdown.

**Query Parameters:**
- `agent_id` (string) — Filter by agent
- `start_date` (string) — ISO 8601 date
- `end_date` (string) — ISO 8601 date

**Response:**
```json
{
  "data": [
    {
      "model_name": "gpt-4o-mini",
      "provider": "openai",
      "call_count": 7500,
      "total_cost": 60.00,
      "avg_latency_ms": 210.5,
      "success_rate": 0.98
    },
    {
      "model_name": "gpt-4o",
      "provider": "openai",
      "call_count": 2500,
      "total_cost": 65.50,
      "avg_latency_ms": 345.2,
      "success_rate": 0.99
    }
  ]
}
```

### GET /analytics/cache-performance

Get cache performance metrics.

**Response:**
```json
{
  "overall_hit_rate": 0.42,
  "tier1_hits": 3200,
  "tier2_hits": 1000,
  "total_hits": 4200,
  "total_requests": 10000,
  "avg_cache_latency_ms": 2.5,
  "savings_from_cache_usd": 180.50
}
```

### GET /analytics/savings

Get cost savings breakdown.

**Response:**
```json
{
  "data": [
    {
      "source": "intelligent_routing",
      "savings_usd": 250.30,
      "percentage_of_total": 55.6
    },
    {
      "source": "semantic_cache",
      "savings_usd": 180.50,
      "percentage_of_total": 40.1
    },
    {
      "source": "intervention_prevention",
      "savings_usd": 19.50,
      "percentage_of_total": 4.3
    }
  ],
  "total_savings_usd": 450.30
}
```

---

## Billing

Subscription and usage management.

### GET /billing/subscription

Get current subscription.

**Response:**
```json
{
  "plan_id": "pro",
  "status": "active",
  "current_period_start": "2026-03-01T00:00:00Z",
  "current_period_end": "2026-04-01T00:00:00Z",
  "cancel_at_period_end": false
}
```

### GET /billing/plans

List available billing plans.

**Response:**
```json
{
  "data": [
    {
      "id": "free",
      "name": "Free",
      "price_monthly": 0,
      "included_calls": 1000,
      "features": ["Basic routing", "7-day retention"]
    },
    {
      "id": "pro",
      "name": "Pro",
      "price_monthly": 99,
      "included_calls": 100000,
      "features": ["All routing modes", "90-day retention", "ABA analytics"]
    }
  ]
}
```

### GET /billing/usage

Get billing usage.

**Query Parameters:**
- `start_date` (string) — ISO 8601 date
- `end_date` (string) — ISO 8601 date

**Response:**
```json
{
  "period_start": "2026-03-01T00:00:00Z",
  "period_end": "2026-03-26T12:00:00Z",
  "total_calls": 75000,
  "included_calls": 100000,
  "overage_calls": 0,
  "estimated_cost": 99.00
}
```

### POST /billing/subscription/update

Update subscription plan.

**Request:**
```json
{
  "plan_id": "enterprise"
}
```

---

## Models

Model registry and custom endpoints.

### GET /models

List all models from registry.

**Response:**
```json
{
  "data": [
    {
      "id": "gpt-4o",
      "provider": "openai",
      "display_name": "GPT-4o",
      "input_cost_per_1m": 2.50,
      "output_cost_per_1m": 10.00,
      "context_window": 128000,
      "supports_tools": true,
      "supports_vision": true
    }
  ]
}
```

### GET /models/{id}

Get model by ID.

### POST /models/endpoints

Create custom model endpoint.

**Request:**
```json
{
  "name": "Fine-tuned GPT-4o",
  "base_model": "gpt-4o",
  "endpoint_url": "https://api.openai.com/v1/chat/completions",
  "api_key": "sk-proj-...",
  "headers": {
    "X-Custom-Header": "value"
  },
  "metadata": {"version": "v2"}
}
```

### GET /models/endpoints

List custom endpoints.

### GET /models/endpoints/{id}

Get endpoint by ID.

### PATCH /models/endpoints/{id}

Update endpoint.

### DELETE /models/endpoints/{id}

Delete endpoint.

---

## Health

System health checks.

### GET /health

Get overall health status.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "pinecone": "healthy"
  }
}
```

### GET /health/providers

Get health status of all providers.

**Response:**
```json
{
  "data": [
    {
      "provider": "openai",
      "status": "healthy",
      "last_checked": "2026-03-26T12:00:00Z",
      "error": null
    },
    {
      "provider": "anthropic",
      "status": "degraded",
      "last_checked": "2026-03-26T12:00:00Z",
      "error": "High latency detected"
    }
  ]
}
```

### GET /health/providers/{provider}

Get health status of specific provider.

---

## Errors

ASAHIO uses standard HTTP status codes and returns errors in a consistent format:

**Error Response:**
```json
{
  "error": {
    "code": "INVALID_REQUEST",
    "message": "The 'messages' field is required",
    "detail": null
  }
}
```

**Common Error Codes:**

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_REQUEST` | 400 | Malformed request body or missing required fields |
| `UNAUTHORIZED` | 401 | Missing or invalid API key |
| `FORBIDDEN` | 403 | Valid API key but insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found (or cross-org access blocked) |
| `RATE_LIMIT_EXCEEDED` | 429 | Rate limit exceeded for your plan |
| `BUDGET_EXCEEDED` | 429 | Monthly budget limit exceeded |
| `INTERNAL_ERROR` | 500 | Internal server error |
| `PROVIDER_ERROR` | 502 | Upstream provider error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

**Rate Limiting:**

Rate limits are applied per API key:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 998
X-RateLimit-Reset: 1711234567
```

**Retry Logic:**

- `429` (Rate Limit) — Retry after `X-RateLimit-Reset` timestamp
- `500`, `502`, `503` — Retry with exponential backoff (max 3 attempts)
- `400`, `401`, `403`, `404` — Do not retry (client error)

---

## Changelog

**v1.0.0** (2026-03-26)
- Initial API release
- SDK v2 support: tools, web search, MCP, computer use
- Full platform coverage: 90+ endpoints
- Tool usage tracking in traces

---

## Support

- **Documentation:** https://docs.asahio.dev
- **API Status:** https://status.asahio.dev
- **Support:** support@asahio.dev
- **GitHub:** https://github.com/asahio-ai/asahio-python
