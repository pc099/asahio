# Changelog

All notable changes to the ASAHIO Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-26

### Added — SDK v2: Full Platform Coverage

#### Core Infrastructure
- **HTTP Methods**: Added PATCH, PUT, DELETE, and parameterized GET to BaseClient and AsyncBaseClient
- **Type System**: Created 40+ dataclasses across 9 domains (agents, aba, providers, routing, traces, interventions, analytics, billing, health)
- **Resource Modules**: Added 12 resource namespaces with ~68 methods total

#### Agentic Capabilities
- **Tool Use**: Added `tools`, `tool_choice` parameters to `chat.completions.create()`
- **Web Search**: Added `enable_web_search` and `web_search_config` parameters
- **MCP**: Added `mcp_servers` parameter for Model Context Protocol integration
- **Computer Use**: Added `enable_computer_use` and `computer_use_config` parameters (Anthropic)
- **Fallback Chains**: Added `chain_id` parameter to route through custom fallback chains

#### Resource Modules

##### `client.agents` — Agent Lifecycle & Mode Transitions
- `create()` — Create new agent with routing/intervention modes
- `list()` — List all agents
- `get()` — Get agent by ID
- `update()` — Update agent configuration
- `archive()` — Soft-delete agent
- `stats()` — Get agent statistics (calls, cache hits, latency)
- `mode_eligibility()` — Check if agent qualifies for mode transition
- `transition_mode()` — Transition agent to new mode
- `mode_history()` — Get mode transition history
- `create_session()` — Create agent session

##### `client.aba` — Agent Behavioral Analytics
- `get_fingerprint()` — Get behavioral fingerprint for an agent
- `list_fingerprints()` — List all fingerprints with min observation filter
- `org_overview()` — Get organization-wide ABA overview
- `list_structural_records()` — List structural records
- `get_risk_prior()` — Get risk prior from Model C global pool
- `list_anomalies()` — List detected anomalies
- `cold_start_status()` — Get cold start status for an agent
- `create_observation()` — Create manual ABA observation
- `tag_hallucination()` — Tag a call as hallucination

##### `client.chains` — Fallback Chains (BYOM)
- `create()` — Create fallback chain
- `list()` — List all chains
- `get()` — Get chain by ID
- `delete()` — Delete chain
- `test()` — Test chain with sample prompt

##### `client.provider_keys` — BYOM Provider Keys
- `create()` — Add provider API key (BYOM)
- `list()` — List all provider keys
- `get()` — Get key by ID
- `delete()` — Delete provider key
- `rotate()` — Rotate provider key

##### `client.routing` — Routing Dry Runs & Constraints
- `dry_run()` — Dry run routing decision without executing
- `get_decision()` — Get routing decision for a specific call
- `list_constraints()` — List routing constraints
- `create_constraint()` — Create routing constraint
- `delete_constraint()` — Delete constraint

##### `client.traces` — Call Traces & Sessions
- `get()` — Get trace by ID
- `list()` — List traces with filters
- `get_session()` — Get session by ID
- `list_sessions()` — List sessions
- `get_session_graph()` — Get session graph visualization data
- `list_session_steps()` — List all steps in a session

##### `client.interventions` — Intervention Logs & Stats
- `list_logs()` — List intervention logs
- `get_stats()` — Get intervention statistics
- `fleet_overview()` — Get fleet-wide intervention overview

##### `client.analytics` — Cost & Savings Analytics
- `overview()` — Get analytics overview with date filters
- `model_breakdown()` — Get model usage breakdown
- `cache_performance()` — Get cache performance metrics
- `savings()` — Get cost savings breakdown

##### `client.billing` — Plans, Subscriptions, Usage
- `get_subscription()` — Get current subscription
- `list_plans()` — List available billing plans
- `get_usage()` — Get billing usage for a period
- `update_subscription()` — Update subscription plan

##### `client.models` — Model Registry & Custom Endpoints
- `list()` — List all models from registry
- `get()` — Get model by ID
- `create_endpoint()` — Create custom model endpoint (fine-tuned/custom)
- `list_endpoints()` — List custom endpoints
- `get_endpoint()` — Get endpoint by ID
- `update_endpoint()` — Update endpoint configuration
- `delete_endpoint()` — Delete custom endpoint

##### `client.ollama` — Ollama Configuration
- `get_config()` — Get Ollama configuration
- `update_config()` — Update Ollama base URL and enabled status
- `test_connection()` — Test Ollama connection

##### `client.health` — Provider Health Checks
- `check()` — Get overall health status
- `list_providers()` — Get health status of all providers
- `get_provider()` — Get health status of specific provider

#### Tool Helpers (`asahio.tools`)
- `function_to_tool()` — Convert Python function to OpenAI tool schema
  - Supports type hints (str, int, float, bool, list, dict, Optional)
  - Extracts parameter descriptions from Google-style docstrings
  - Handles required vs optional parameters
- `extract_tool_calls()` — Parse tool calls from chat completion response
- `format_tool_result()` — Format tool execution result for API submission

#### Enhanced Types
- **AsahioMetadata**: Added `risk_score`, `risk_factors`, `intervention_level`, `tools_requested`, `tools_called`
- **Message**: Added `tool_calls` and `tool_call_id` fields for tool use
- **PaginatedList**: Generic paginated response type for list endpoints

#### Testing
- Added 22 SDK tests covering agents resource and tool helpers
- Test pattern established using pytest with monkeypatch for HTTP mocking
- All async methods tested with pytest-asyncio

### Changed
- Updated `chat.completions.create()` signature to include 8 new agentic parameters
- Expanded BaseClient HTTP methods from POST-only to full REST support

### Documentation
- Completely rewrote README with comprehensive SDK v2 examples
- Added usage examples for all 12 resource modules
- Added tool use workflow documentation
- Added routing mode and intervention mode guides
- Added async usage examples
- Added type safety documentation

## [0.1.0] - 2026-03-06

### Added
- Initial SDK release
- Chat completions gateway support
- Streaming support
- Two-dimensional mode system (routing_mode × intervention_mode)
- Response metadata at `response.asahio`
- Backward compatibility aliases (`asahi`, `acorn`)
- Sync and async clients
- Type-safe responses with Pydantic

[0.2.0]: https://github.com/asahio-ai/asahio-python/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/asahio-ai/asahio-python/releases/tag/v0.1.0
