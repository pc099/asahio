"""Tests for GuidedChainExecutor — fallback chain execution logic."""

import pytest
import httpx

from src.providers.base import (
    BillingException,
    InferenceRequest,
    InferenceResponse,
    ProviderAdapter,
    ProviderRateLimitError,
    ProviderServerError,
)
from src.routing.guided_chain import (
    ChainAttempt,
    ChainSlotConfig,
    GuidedChainConfig,
    GuidedChainExecutor,
    _classify_trigger,
)


# ── Helpers ────────────────────────────────────────────────────────────


class FakeProvider(ProviderAdapter):
    """Configurable fake provider for testing."""

    def __init__(self, name: str = "fake", response_text: str = "ok") -> None:
        self._name = name
        self._response_text = response_text
        self._calls: list[InferenceRequest] = []
        self._side_effect: BaseException | None = None

    @property
    def provider_name(self) -> str:
        return self._name

    def call(self, request: InferenceRequest, api_key: str) -> InferenceResponse:
        self._calls.append(request)
        if self._side_effect is not None:
            raise self._side_effect
        return InferenceResponse(
            text=self._response_text,
            input_tokens=10,
            output_tokens=20,
            latency_ms=50,
            model=request.model,
            provider=self._name,
        )

    def supports_model(self, model_id: str) -> bool:
        return True

    def fail_with(self, exc: BaseException) -> "FakeProvider":
        self._side_effect = exc
        return self


def _make_chain(slots: list[ChainSlotConfig]) -> GuidedChainConfig:
    return GuidedChainConfig(chain_id="test-chain", name="Test Chain", slots=slots)


def _make_slot(
    position: int = 1,
    provider: str = "openai",
    model: str = "gpt-4o",
    triggers: list[str] | None = None,
) -> ChainSlotConfig:
    return ChainSlotConfig(
        position=position,
        model_id=model,
        provider=provider,
        fallback_triggers=triggers if triggers is not None else ["rate_limit", "server_error", "timeout"],
    )


# ── Trigger Classification ─────────────────────────────────────────────


class TestClassifyTrigger:
    def test_rate_limit(self) -> None:
        assert _classify_trigger(ProviderRateLimitError("429")) == "rate_limit"

    def test_server_error(self) -> None:
        assert _classify_trigger(ProviderServerError("500")) == "server_error"

    def test_timeout(self) -> None:
        assert _classify_trigger(httpx.ReadTimeout("timeout")) == "timeout"

    def test_billing(self) -> None:
        assert _classify_trigger(BillingException("no key")) == "no_key"

    def test_unknown(self) -> None:
        assert _classify_trigger(RuntimeError("unexpected")) == "unknown"


# ── Executor ───────────────────────────────────────────────────────────


class TestGuidedChainExecutor:
    def test_primary_slot_succeeds(self) -> None:
        """When the first slot succeeds, no fallback happens."""
        provider = FakeProvider("openai", "hello from gpt")
        providers = {"openai": provider}
        executor = GuidedChainExecutor(
            get_provider=lambda name: providers[name],
            resolve_key=lambda prov, org=None: "sk-test",
        )
        chain = _make_chain([_make_slot(1, "openai", "gpt-4o")])
        request = InferenceRequest(model="gpt-4o", prompt="hi")

        response, attempts = executor.execute(chain, request)

        assert response.text == "hello from gpt"
        assert response.provider == "openai"
        assert len(attempts) == 1
        assert attempts[0].success is True
        assert attempts[0].slot_position == 1

    def test_fallback_on_rate_limit(self) -> None:
        """When slot 1 gets rate limited, slot 2 is tried."""
        p1 = FakeProvider("openai").fail_with(ProviderRateLimitError("429"))
        p2 = FakeProvider("anthropic", "fallback response")
        providers = {"openai": p1, "anthropic": p2}
        executor = GuidedChainExecutor(
            get_provider=lambda name: providers[name],
            resolve_key=lambda prov, org=None: "key",
        )
        chain = _make_chain([
            _make_slot(1, "openai", "gpt-4o"),
            _make_slot(2, "anthropic", "claude-haiku-4-5"),
        ])
        request = InferenceRequest(model="gpt-4o", prompt="test")

        response, attempts = executor.execute(chain, request)

        assert response.text == "fallback response"
        assert response.provider == "anthropic"
        assert len(attempts) == 2
        assert attempts[0].success is False
        assert attempts[0].trigger == "rate_limit"
        assert attempts[1].success is True

    def test_fallback_on_timeout(self) -> None:
        """Timeout triggers fallback."""
        p1 = FakeProvider("openai").fail_with(httpx.ReadTimeout("timeout"))
        p2 = FakeProvider("anthropic", "got it")
        providers = {"openai": p1, "anthropic": p2}
        executor = GuidedChainExecutor(
            get_provider=lambda name: providers[name],
            resolve_key=lambda prov, org=None: "key",
        )
        chain = _make_chain([
            _make_slot(1, "openai", "gpt-4o"),
            _make_slot(2, "anthropic", "claude-haiku-4-5"),
        ])
        request = InferenceRequest(model="any", prompt="test")

        response, attempts = executor.execute(chain, request)

        assert response.text == "got it"
        assert attempts[0].trigger == "timeout"

    def test_fallback_on_server_error(self) -> None:
        """Server error (5xx) triggers fallback."""
        p1 = FakeProvider("openai").fail_with(ProviderServerError("502", 502))
        p2 = FakeProvider("google", "google ok")
        providers = {"openai": p1, "google": p2}
        executor = GuidedChainExecutor(
            get_provider=lambda name: providers[name],
            resolve_key=lambda prov, org=None: "key",
        )
        chain = _make_chain([
            _make_slot(1, "openai", "gpt-4o"),
            _make_slot(2, "google", "gemini-2.5-flash"),
        ])
        request = InferenceRequest(model="any", prompt="test")

        response, attempts = executor.execute(chain, request)

        assert response.text == "google ok"
        assert attempts[0].trigger == "server_error"

    def test_no_key_trigger(self) -> None:
        """BillingException produces no_key trigger and can trigger fallback."""
        p2 = FakeProvider("anthropic", "anthropic ok")
        providers = {"openai": FakeProvider("openai"), "anthropic": p2}

        def resolve(prov: str, org: str | None = None) -> str:
            if prov == "openai":
                raise BillingException("No key for openai")
            return "key"

        executor = GuidedChainExecutor(
            get_provider=lambda name: providers[name],
            resolve_key=resolve,
        )
        chain = _make_chain([
            _make_slot(1, "openai", "gpt-4o", triggers=["rate_limit", "server_error", "timeout", "no_key"]),
            _make_slot(2, "anthropic", "claude-haiku-4-5"),
        ])
        request = InferenceRequest(model="any", prompt="test")

        response, attempts = executor.execute(chain, request)

        assert response.text == "anthropic ok"
        assert attempts[0].trigger == "no_key"
        assert attempts[0].success is False

    def test_all_slots_fail_raises(self) -> None:
        """RuntimeError when all slots are exhausted."""
        p1 = FakeProvider("openai").fail_with(ProviderRateLimitError("429"))
        p2 = FakeProvider("anthropic").fail_with(ProviderServerError("500"))
        providers = {"openai": p1, "anthropic": p2}
        executor = GuidedChainExecutor(
            get_provider=lambda name: providers[name],
            resolve_key=lambda prov, org=None: "key",
        )
        chain = _make_chain([
            _make_slot(1, "openai", "gpt-4o"),
            _make_slot(2, "anthropic", "claude-haiku-4-5"),
        ])
        request = InferenceRequest(model="any", prompt="test")

        with pytest.raises(RuntimeError, match="exhausted all 2 slots"):
            executor.execute(chain, request)

    def test_trigger_not_in_fallback_stops_chain(self) -> None:
        """If trigger type is not in slot's fallback_triggers, stop — don't try next slot."""
        p1 = FakeProvider("openai").fail_with(ProviderRateLimitError("429"))
        p2 = FakeProvider("anthropic", "should not reach")
        providers = {"openai": p1, "anthropic": p2}
        executor = GuidedChainExecutor(
            get_provider=lambda name: providers[name],
            resolve_key=lambda prov, org=None: "key",
        )
        # Slot 1 only falls back on server_error and timeout — NOT rate_limit
        chain = _make_chain([
            _make_slot(1, "openai", "gpt-4o", triggers=["server_error", "timeout"]),
            _make_slot(2, "anthropic", "claude-haiku-4-5"),
        ])
        request = InferenceRequest(model="any", prompt="test")

        with pytest.raises(RuntimeError, match="exhausted"):
            executor.execute(chain, request)

        # Slot 2 was never tried because rate_limit is not in slot 1's triggers
        assert len(p2._calls) == 0

    def test_empty_chain_raises(self) -> None:
        """Chain with no slots raises immediately."""
        executor = GuidedChainExecutor(
            get_provider=lambda name: FakeProvider(),
            resolve_key=lambda prov, org=None: "key",
        )
        chain = _make_chain([])
        request = InferenceRequest(model="any", prompt="test")

        with pytest.raises(RuntimeError, match="no slots configured"):
            executor.execute(chain, request)

    def test_slots_tried_in_priority_order(self) -> None:
        """Slots are sorted by position, not insertion order."""
        call_order: list[str] = []

        class TrackingProvider(ProviderAdapter):
            def __init__(self, name: str) -> None:
                self._name = name

            @property
            def provider_name(self) -> str:
                return self._name

            def call(self, request: InferenceRequest, api_key: str) -> InferenceResponse:
                call_order.append(self._name)
                # First two fail, third succeeds
                if len(call_order) < 3:
                    raise ProviderServerError("fail")
                return InferenceResponse(
                    text="ok", input_tokens=5, output_tokens=5,
                    latency_ms=10, model=request.model, provider=self._name,
                )

            def supports_model(self, model_id: str) -> bool:
                return True

        providers = {
            "deepseek": TrackingProvider("deepseek"),
            "openai": TrackingProvider("openai"),
            "anthropic": TrackingProvider("anthropic"),
        }
        executor = GuidedChainExecutor(
            get_provider=lambda name: providers[name],
            resolve_key=lambda prov, org=None: "key",
        )
        # Insert out of order — position 3, 1, 2
        chain = _make_chain([
            _make_slot(3, "anthropic", "claude-haiku-4-5"),
            _make_slot(1, "openai", "gpt-4o"),
            _make_slot(2, "deepseek", "deepseek-chat"),
        ])
        request = InferenceRequest(model="any", prompt="test")

        response, attempts = executor.execute(chain, request)

        assert call_order == ["openai", "deepseek", "anthropic"]
        assert response.provider == "anthropic"

    def test_request_model_overridden_per_slot(self) -> None:
        """Each slot sends its own model_id, not the original request model."""
        received_models: list[str] = []

        class ModelCapture(ProviderAdapter):
            @property
            def provider_name(self) -> str:
                return "test"

            def call(self, request: InferenceRequest, api_key: str) -> InferenceResponse:
                received_models.append(request.model)
                if len(received_models) == 1:
                    raise ProviderRateLimitError("429")
                return InferenceResponse(
                    text="ok", input_tokens=5, output_tokens=5,
                    latency_ms=10, model=request.model, provider="test",
                )

            def supports_model(self, model_id: str) -> bool:
                return True

        executor = GuidedChainExecutor(
            get_provider=lambda name: ModelCapture(),
            resolve_key=lambda prov, org=None: "key",
        )
        chain = _make_chain([
            _make_slot(1, "openai", "gpt-4o"),
            _make_slot(2, "anthropic", "claude-haiku-4-5"),
        ])
        request = InferenceRequest(model="original-model", prompt="test")

        executor.execute(chain, request)

        assert received_models == ["gpt-4o", "claude-haiku-4-5"]

    def test_org_id_passed_to_resolver(self) -> None:
        """org_id is forwarded to the key resolver."""
        resolved_orgs: list[str | None] = []

        def track_resolve(prov: str, org: str | None = None) -> str:
            resolved_orgs.append(org)
            return "key"

        executor = GuidedChainExecutor(
            get_provider=lambda name: FakeProvider(),
            resolve_key=track_resolve,
        )
        chain = _make_chain([_make_slot(1)])
        request = InferenceRequest(model="any", prompt="test")

        executor.execute(chain, request, org_id="org-123")

        assert resolved_orgs == ["org-123"]

    def test_attempt_records_latency(self) -> None:
        """Successful attempts include latency_ms."""
        executor = GuidedChainExecutor(
            get_provider=lambda name: FakeProvider(),
            resolve_key=lambda prov, org=None: "key",
        )
        chain = _make_chain([_make_slot(1)])
        request = InferenceRequest(model="any", prompt="test")

        _, attempts = executor.execute(chain, request)

        assert attempts[0].latency_ms is not None
        assert attempts[0].latency_ms >= 0
