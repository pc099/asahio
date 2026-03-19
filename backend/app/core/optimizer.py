"""Bridge to the legacy optimizer used by the canonical ASAHIO backend."""

import asyncio
import logging
import sys
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

from app.services.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitOpenError,
    execute_with_retry,
    RetryConfig,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Per-provider circuit breakers (module-level singletons)
# ---------------------------------------------------------------------------
_provider_circuits: dict[str, CircuitBreaker] = {}

_PROVIDER_CB_CONFIG = CircuitBreakerConfig(
    failure_threshold=5,
    recovery_timeout_seconds=30.0,
    half_open_max_calls=1,
    degraded_failure_threshold=2,
)

_PROVIDER_RETRY_CONFIG = RetryConfig(
    max_attempts=2,
    base_delay_seconds=0.5,
    max_delay_seconds=5.0,
    jitter=True,
)


def _get_circuit(provider: str) -> CircuitBreaker:
    """Get or create a circuit breaker for a provider."""
    if provider not in _provider_circuits:
        _provider_circuits[provider] = CircuitBreaker(provider, _PROVIDER_CB_CONFIG)
    return _provider_circuits[provider]

PROJECT_ROOT = str(Path(__file__).resolve().parents[3])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

_ROUTING_MODE_ALIASES = {
    "AUTOPILOT": "AUTO",
    "AUTO": "AUTO",
    "GUIDED": "GUIDED",
    "EXPLICIT": "EXPLICIT",
}

_LEGACY_ROUTING_MODES = {
    "AUTO": "autopilot",
    "GUIDED": "guided",
    "EXPLICIT": "explicit",
}


@dataclass
class GatewayResult:
    """Normalized result from the optimizer for the gateway response."""

    response: str = ""
    request_id: Optional[str] = None
    model_used: str = "unknown"
    model_requested: Optional[str] = None
    provider: Optional[str] = None
    routing_mode: Optional[str] = None
    intervention_mode: Optional[str] = None
    agent_id: Optional[str] = None
    agent_session_id: Optional[str] = None
    model_endpoint_id: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    cost_without_asahi: float = 0.0
    cost_with_asahi: float = 0.0
    savings_usd: float = 0.0
    savings_pct: Optional[float] = None
    cache_hit: bool = False
    cache_tier: Optional[str] = None
    latency_ms: Optional[int] = None
    routing_reason: Optional[str] = None
    routing_factors: dict = field(default_factory=dict)
    routing_confidence: Optional[float] = None
    policy_action: str = "observe_only"
    policy_reason: Optional[str] = None
    risk_score: Optional[float] = None
    risk_factors: dict = field(default_factory=dict)
    intervention_level: Optional[int] = None
    error_message: Optional[str] = None


def normalize_routing_mode(value: Optional[str]) -> str:
    if not value:
        return "AUTO"
    return _ROUTING_MODE_ALIASES.get(value.upper(), value.upper())


def _legacy_routing_mode(value: Optional[str]) -> str:
    normalized = normalize_routing_mode(value)
    return _LEGACY_ROUTING_MODES.get(normalized, "autopilot")


def _create_optimizer(use_mock: bool = True):
    try:
        from src.core.optimizer import InferenceOptimizer

        return InferenceOptimizer(use_mock=use_mock)
    except Exception:
        logger.exception("Failed to create InferenceOptimizer")
        return None


@lru_cache(maxsize=1)
def get_optimizer_instance(use_mock: bool = True):
    return _create_optimizer(use_mock=use_mock)


async def run_inference(
    prompt: str,
    routing_mode: str = "AUTO",
    intervention_mode: str = "OBSERVE",
    quality_preference: Optional[str] = "high",
    latency_preference: Optional[str] = "normal",
    model_override: Optional[str] = None,
    org_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    agent_session_id: Optional[str] = None,
    model_endpoint_id: Optional[str] = None,
    provider_hint: Optional[str] = None,
    use_mock: bool = True,
    redis=None,
    session_step: Optional[int] = None,
    fingerprint_hallucination_rate: Optional[float] = None,
    agent_type: Optional[str] = None,
    threshold_overrides: Optional[dict] = None,
) -> GatewayResult:
    start_time = time.time()
    normalized_routing_mode = normalize_routing_mode(routing_mode)
    norm_intervention_mode = intervention_mode.upper()

    # ── Risk scoring (sync, <2ms) ────────────────────────────────────────
    risk_breakdown = None
    try:
        from app.services.risk_scorer import RiskScoringEngine

        risk_engine = RiskScoringEngine()
        risk_breakdown = risk_engine.fast_estimate(
            prompt=prompt,
            model_id=model_override,
            fingerprint_hallucination_rate=fingerprint_hallucination_rate,
            session_step=session_step,
        )
    except Exception:
        logger.debug("Risk scorer unavailable, skipping intervention")

    # Classify dependency level for context-aware caching
    dep_level = None
    try:
        from app.services.dependency_classifier import DependencyClassifier

        classifier = DependencyClassifier()
        dep_classification = classifier.classify(prompt)
        dep_level = dep_classification.level
    except Exception:
        logger.debug("Dependency classifier unavailable, defaulting to standard cache")

    if redis and org_id:
        try:
            from app.services.cache import RedisCache

            cache = RedisCache(redis)

            # Use context-aware cache if dependency level is available
            if dep_level is not None:
                from app.services.coherence_validator import CoherenceValidator

                validator = CoherenceValidator()
                hit = await cache.context_get(
                    org_id, prompt,
                    dependency_level=dep_level,
                    model=model_override,
                    coherence_validator=validator,
                )
            else:
                hit = await cache.get(org_id, prompt, model=model_override)
            if hit:
                elapsed = int((time.time() - start_time) * 1000)
                logger.info(
                    "Cache %s hit for org %s (similarity=%.4f)",
                    hit.cache_tier,
                    org_id,
                    hit.similarity or 1.0,
                )
                cache_risk = risk_breakdown.composite_score if risk_breakdown else None
                cache_factors = risk_breakdown.factors if risk_breakdown else {}
                cache_level = 0  # Cache hits default to LOG
                return GatewayResult(
                    response=hit.response,
                    model_used=hit.model_used,
                    model_requested=model_override,
                    provider=provider_hint,
                    routing_mode=normalized_routing_mode,
                    intervention_mode=norm_intervention_mode,
                    agent_id=agent_id,
                    agent_session_id=agent_session_id,
                    model_endpoint_id=model_endpoint_id,
                    input_tokens=0,
                    output_tokens=0,
                    cost_without_asahi=0.0,
                    cost_with_asahi=0.0,
                    savings_usd=0.0,
                    savings_pct=100.0,
                    cache_hit=True,
                    cache_tier=hit.cache_tier,
                    latency_ms=elapsed,
                    routing_reason=f"Cache {hit.cache_tier} hit",
                    routing_factors={"cache": hit.cache_tier},
                    policy_action="log",
                    policy_reason="Cache hit — intervention not applicable",
                    risk_score=cache_risk,
                    risk_factors=cache_factors,
                    intervention_level=cache_level,
                )
        except Exception:
            logger.exception("Redis cache check failed, falling through to optimizer")

    # ── Intervention evaluation (sync, <0.5ms) ──────────────────────────
    intervention_decision = None
    if risk_breakdown is not None:
        try:
            from app.services.intervention_engine import InterventionEngine

            intervention_eng = InterventionEngine()
            intervention_decision = intervention_eng.evaluate(
                risk_score=risk_breakdown.composite_score,
                intervention_mode=norm_intervention_mode,
                prompt=prompt,
                current_model=model_override,
                agent_type=agent_type,
                threshold_overrides=threshold_overrides,
            )

            # BLOCK: return error immediately
            if intervention_decision.should_block:
                elapsed = int((time.time() - start_time) * 1000)
                blocked_result = GatewayResult(
                    response="",
                    routing_mode=normalized_routing_mode,
                    intervention_mode=norm_intervention_mode,
                    agent_id=agent_id,
                    agent_session_id=agent_session_id,
                    model_endpoint_id=model_endpoint_id,
                    latency_ms=elapsed,
                    policy_action="block",
                    policy_reason=intervention_decision.reason,
                    risk_score=risk_breakdown.composite_score,
                    risk_factors=risk_breakdown.factors,
                    intervention_level=intervention_decision.level.value,
                    error_message="Request blocked by intervention engine due to high risk score",
                )
                # Fire-and-forget: log the block
                if org_id:
                    _fire_intervention_log(
                        org_id=org_id, agent_id=agent_id,
                        decision=intervention_decision,
                        risk_breakdown=risk_breakdown,
                        intervention_mode=norm_intervention_mode,
                        original_model=model_override, final_model=None,
                    )
                return blocked_result
        except Exception:
            logger.debug("Intervention engine unavailable, proceeding without intervention")

    # Run the routing engine to get model selection and factor breakdown
    from app.services.provider_health import get_all_provider_health
    from app.services.routing import RoutingContext, RoutingEngine

    provider_health = get_all_provider_health()

    routing_ctx = RoutingContext(
        prompt=prompt,
        routing_mode=normalized_routing_mode,
        quality_preference=quality_preference or "high",
        latency_preference=latency_preference or "normal",
        model_override=model_override,
        provider_hint=provider_hint,
        provider_health=provider_health,
    )
    routing_engine = RoutingEngine()
    routing_decision = routing_engine.route(routing_ctx)

    # Use routing decision to inform the model override if AUTO mode selected a model
    effective_model = model_override or routing_decision.selected_model

    # Apply intervention actions to the effective model and prompt
    effective_prompt = prompt
    if intervention_decision is not None:
        if intervention_decision.rerouted_model:
            effective_model = intervention_decision.rerouted_model
        if intervention_decision.augmented_prompt:
            effective_prompt = intervention_decision.augmented_prompt

    optimizer = get_optimizer_instance(use_mock=use_mock)
    if not optimizer:
        return GatewayResult(
            response="Optimizer unavailable",
            error_message="Failed to initialize InferenceOptimizer",
        )

    # Get circuit breaker for the selected provider
    selected_provider = routing_decision.selected_provider or provider_hint or "unknown"
    circuit = _get_circuit(selected_provider)
    circuit.set_provider_health(provider_health.get(selected_provider, "healthy"))

    loop = asyncio.get_event_loop()
    try:

        async def _run_inference():
            return await loop.run_in_executor(
                None,
                lambda: optimizer.infer(
                    prompt=effective_prompt,
                    routing_mode=_legacy_routing_mode(normalized_routing_mode),
                    quality_preference=quality_preference,
                    latency_preference=latency_preference,
                    model_override=effective_model,
                    organization_id=org_id,
                ),
            )

        result = await execute_with_retry(
            _run_inference, circuit, _PROVIDER_RETRY_CONFIG, timeout_seconds=30.0,
        )

        elapsed = int((time.time() - start_time) * 1000)
        cache_tier_map = {0: None, 1: "exact", 2: "semantic", 3: "intermediate"}
        cache_tier = cache_tier_map.get(result.cache_tier, None)

        cost_original = result.cost_original or result.cost * 3
        cost_with = result.cost
        savings = cost_original - cost_with
        savings_pct = (savings / cost_original * 100) if cost_original > 0 else 0.0

        # Resolve policy fields from intervention decision
        if intervention_decision is not None:
            policy_action = intervention_decision.action
            policy_reason = intervention_decision.reason
            i_level = intervention_decision.level.value
        else:
            policy_action = "log"
            policy_reason = "Risk scorer unavailable — defaulting to log"
            i_level = 0

        r_score = risk_breakdown.composite_score if risk_breakdown else None
        r_factors = risk_breakdown.factors if risk_breakdown else {}

        gateway_result = GatewayResult(
            response=result.response,
            request_id=getattr(result, "request_id", None),
            model_used=result.model_used,
            model_requested=model_override,
            provider=routing_decision.selected_provider or provider_hint,
            routing_mode=normalized_routing_mode,
            intervention_mode=norm_intervention_mode,
            agent_id=agent_id,
            agent_session_id=agent_session_id,
            model_endpoint_id=model_endpoint_id,
            input_tokens=result.tokens_input,
            output_tokens=result.tokens_output,
            cost_without_asahi=cost_original,
            cost_with_asahi=cost_with,
            savings_usd=savings,
            savings_pct=round(savings_pct, 2),
            cache_hit=result.cache_hit,
            cache_tier=cache_tier,
            latency_ms=elapsed,
            routing_reason=routing_decision.reason,
            routing_factors=routing_decision.factors,
            routing_confidence=routing_decision.confidence,
            policy_action=policy_action,
            policy_reason=policy_reason,
            risk_score=r_score,
            risk_factors=r_factors,
            intervention_level=i_level,
        )

        if redis and org_id and result.response and not result.cache_hit:
            asyncio.create_task(
                _store_in_cache(redis, org_id, prompt, result.response, result.model_used)
            )

        # Fire-and-forget: log intervention
        if org_id and intervention_decision is not None:
            _fire_intervention_log(
                org_id=org_id, agent_id=agent_id,
                decision=intervention_decision,
                risk_breakdown=risk_breakdown,
                intervention_mode=norm_intervention_mode,
                original_model=model_override,
                final_model=result.model_used,
            )

        return gateway_result
    except CircuitOpenError as exc:
        elapsed = int((time.time() - start_time) * 1000)
        logger.warning(
            "Circuit open for provider %s (org %s): %s",
            selected_provider, org_id, exc,
        )
        return GatewayResult(
            response="",
            routing_mode=normalized_routing_mode,
            intervention_mode=norm_intervention_mode,
            agent_id=agent_id,
            agent_session_id=agent_session_id,
            model_endpoint_id=model_endpoint_id,
            provider=selected_provider,
            latency_ms=elapsed,
            policy_action="circuit_open",
            policy_reason=f"Provider {selected_provider} temporarily unavailable",
            risk_score=risk_breakdown.composite_score if risk_breakdown else None,
            risk_factors=risk_breakdown.factors if risk_breakdown else {},
            intervention_level=0,
            error_message=f"Provider {selected_provider} temporarily unavailable — circuit breaker open",
        )
    except Exception as exc:
        logger.exception("Inference failed for org %s", org_id)
        return GatewayResult(response="", error_message=str(exc))


async def _store_in_cache(redis, org_id: str, query: str, response: str, model_used: str) -> None:
    try:
        from app.services.cache import RedisCache

        cache = RedisCache(redis)
        await cache.set(org_id, query, response, model_used)
    except Exception:
        logger.exception("Failed to cache result for org %s", org_id)


def _fire_intervention_log(
    *,
    org_id: str,
    agent_id: Optional[str],
    decision,
    risk_breakdown,
    intervention_mode: str,
    original_model: Optional[str],
    final_model: Optional[str],
) -> None:
    """Fire-and-forget intervention log write."""
    try:
        from app.services.intervention_writer import (
            InterventionLogPayload,
            write_intervention_log,
        )

        payload = InterventionLogPayload(
            org_id=org_id,
            agent_id=agent_id,
            intervention_level=decision.level.value,
            intervention_mode=intervention_mode,
            risk_score=risk_breakdown.composite_score if risk_breakdown else 0.0,
            risk_factors=risk_breakdown.factors if risk_breakdown else {},
            action_taken=decision.action,
            action_detail=decision.reason,
            original_model=original_model,
            final_model=final_model,
            prompt_modified=decision.augmented_prompt is not None,
            was_blocked=decision.should_block,
        )
        asyncio.create_task(write_intervention_log(payload))
    except Exception:
        logger.debug("Failed to fire intervention log task")
