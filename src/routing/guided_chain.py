"""Guided Chain Executor — tries slots in priority order with fallback.

Pure Python, no database access.  Operates on in-memory dataclasses.
The executor receives ``get_provider`` and ``resolve_key`` callables via
constructor (dependency injection) so it can be used from both the
legacy ``src/`` optimizer and the async ``backend/`` gateway.

Usage::

    executor = GuidedChainExecutor(get_provider=get_provider, resolve_key=resolver.resolve)
    response, attempts = executor.execute(chain_config, request, org_id)
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

import httpx

from src.providers.base import (
    BillingException,
    InferenceRequest,
    InferenceResponse,
    ProviderAdapter,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderServerError,
)

logger = logging.getLogger(__name__)


# ── Data Classes ───────────────────────────────────────────────────────


@dataclass
class ChainSlotConfig:
    """Configuration for one slot in a guided chain."""

    position: int
    model_id: str
    provider: str
    fallback_triggers: list[str] = field(default_factory=lambda: ["rate_limit", "server_error", "timeout"])
    max_latency_ms: Optional[int] = None
    max_cost_per_1k_tokens: Optional[float] = None


@dataclass
class GuidedChainConfig:
    """Full chain definition with ordered slots."""

    chain_id: str
    name: str
    slots: list[ChainSlotConfig] = field(default_factory=list)


@dataclass
class ChainAttempt:
    """Record of one slot attempt during chain execution."""

    slot_position: int
    provider: str
    model: str
    success: bool
    error: Optional[str] = None
    trigger: Optional[str] = None
    latency_ms: Optional[int] = None


# ── Trigger Classification ─────────────────────────────────────────────

# Valid trigger types that can appear in fallback_triggers.
VALID_TRIGGERS = frozenset({"rate_limit", "server_error", "timeout", "cost_ceiling", "no_key"})


def _classify_trigger(exc: Exception) -> str:
    """Map an exception to a trigger type string."""
    if isinstance(exc, ProviderRateLimitError):
        return "rate_limit"
    if isinstance(exc, ProviderServerError):
        return "server_error"
    if isinstance(exc, httpx.TimeoutException):
        return "timeout"
    if isinstance(exc, BillingException):
        return "no_key"
    return "unknown"


# ── Executor ───────────────────────────────────────────────────────────


class GuidedChainExecutor:
    """Executes a guided chain by trying slots in priority order.

    Args:
        get_provider: Callable that returns a ``ProviderAdapter`` by name.
        resolve_key: Callable that returns an API key given (provider, org_id).
    """

    def __init__(
        self,
        get_provider: Callable[[str], ProviderAdapter],
        resolve_key: Callable[..., str],
    ) -> None:
        self._get_provider = get_provider
        self._resolve_key = resolve_key

    def execute(
        self,
        chain: GuidedChainConfig,
        request: InferenceRequest,
        org_id: Optional[str] = None,
    ) -> tuple[InferenceResponse, list[ChainAttempt]]:
        """Execute the chain, trying slots in priority order.

        Args:
            chain: The chain configuration with ordered slots.
            request: The inference request to send.
            org_id: Organisation ID passed to the key resolver.

        Returns:
            Tuple of (response, list of attempt records).

        Raises:
            RuntimeError: All slots exhausted without a successful response.
        """
        if not chain.slots:
            raise RuntimeError(f"Chain '{chain.name}' has no slots configured")

        attempts: list[ChainAttempt] = []
        sorted_slots = sorted(chain.slots, key=lambda s: s.position)

        for slot in sorted_slots:
            attempt = self._try_slot(slot, request, org_id)
            attempts.append(attempt)

            if attempt.success:
                logger.info(
                    "Chain '%s' succeeded on slot %d (%s/%s)",
                    chain.name,
                    slot.position,
                    slot.provider,
                    slot.model_id,
                )
                # Reconstruct the response from the attempt
                # The response is stored temporarily on the attempt object
                response = attempt._response  # type: ignore[attr-defined]
                del attempt._response  # type: ignore[attr-defined]
                return response, attempts

            # Check if the trigger allows fallback
            if attempt.trigger and attempt.trigger not in slot.fallback_triggers:
                logger.warning(
                    "Chain '%s' slot %d trigger '%s' not in fallback_triggers %s — stopping",
                    chain.name,
                    slot.position,
                    attempt.trigger,
                    slot.fallback_triggers,
                )
                break

            logger.info(
                "Chain '%s' slot %d failed (trigger=%s) — falling back",
                chain.name,
                slot.position,
                attempt.trigger,
            )

        raise RuntimeError(
            f"Chain '{chain.name}' exhausted all {len(sorted_slots)} slots "
            f"without a successful response"
        )

    def _try_slot(
        self,
        slot: ChainSlotConfig,
        request: InferenceRequest,
        org_id: Optional[str],
    ) -> ChainAttempt:
        """Attempt inference on a single slot."""
        start = time.monotonic()

        # Resolve API key
        try:
            api_key = self._resolve_key(slot.provider, org_id)
        except BillingException as exc:
            return ChainAttempt(
                slot_position=slot.position,
                provider=slot.provider,
                model=slot.model_id,
                success=False,
                error=str(exc),
                trigger="no_key",
            )

        # Get provider adapter
        try:
            provider = self._get_provider(slot.provider)
        except (ValueError, KeyError) as exc:
            return ChainAttempt(
                slot_position=slot.position,
                provider=slot.provider,
                model=slot.model_id,
                success=False,
                error=str(exc),
                trigger="unknown",
            )

        # Build per-slot request with the slot's model
        slot_request = InferenceRequest(
            model=slot.model_id,
            prompt=request.prompt,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            system_prompt=request.system_prompt,
        )

        # Execute inference
        try:
            response = provider.call(slot_request, api_key)
        except (ProviderRateLimitError, ProviderServerError, BillingException, httpx.TimeoutException) as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            trigger = _classify_trigger(exc)
            return ChainAttempt(
                slot_position=slot.position,
                provider=slot.provider,
                model=slot.model_id,
                success=False,
                error=str(exc),
                trigger=trigger,
                latency_ms=elapsed_ms,
            )
        except ProviderRequestError as exc:
            elapsed_ms = int((time.monotonic() - start) * 1000)
            return ChainAttempt(
                slot_position=slot.position,
                provider=slot.provider,
                model=slot.model_id,
                success=False,
                error=str(exc),
                trigger="unknown",
                latency_ms=elapsed_ms,
            )

        elapsed_ms = int((time.monotonic() - start) * 1000)

        # Check cost ceiling
        if slot.max_cost_per_1k_tokens is not None:
            total_tokens = response.input_tokens + response.output_tokens
            if total_tokens > 0:
                # Rough per-1k cost estimate from token usage
                # (actual cost check would need model pricing — for now
                # this is a placeholder that can be wired to the model registry)
                pass  # cost_ceiling trigger reserved for future pricing integration

        attempt = ChainAttempt(
            slot_position=slot.position,
            provider=slot.provider,
            model=slot.model_id,
            success=True,
            latency_ms=elapsed_ms,
        )
        # Stash response temporarily for the caller to extract
        attempt._response = response  # type: ignore[attr-defined]
        return attempt
