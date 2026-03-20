"""Tests for provider base classes, DTOs, and exceptions."""

import pytest

from src.providers.base import (
    BillingException,
    InferenceRequest,
    InferenceResponse,
    ProviderAdapter,
    ProviderRateLimitError,
    ProviderRequestError,
    ProviderServerError,
)
from src.exceptions import AsahiException


# ── DTO construction ────────────────────────────────────────────────────


class TestInferenceRequest:
    def test_defaults(self) -> None:
        req = InferenceRequest(model="gpt-4o", prompt="Hello")
        assert req.model == "gpt-4o"
        assert req.prompt == "Hello"
        assert req.max_tokens == 1024
        assert req.temperature == 1.0
        assert req.system_prompt is None

    def test_custom_fields(self) -> None:
        req = InferenceRequest(
            model="claude-sonnet-4-6",
            prompt="Test",
            max_tokens=512,
            temperature=0.7,
            system_prompt="Be concise.",
        )
        assert req.max_tokens == 512
        assert req.temperature == 0.7
        assert req.system_prompt == "Be concise."


class TestInferenceResponse:
    def test_fields(self) -> None:
        resp = InferenceResponse(
            text="Hello world",
            input_tokens=10,
            output_tokens=5,
            latency_ms=200,
            model="gpt-4o",
            provider="openai",
        )
        assert resp.text == "Hello world"
        assert resp.input_tokens == 10
        assert resp.output_tokens == 5
        assert resp.latency_ms == 200
        assert resp.model == "gpt-4o"
        assert resp.provider == "openai"


# ── ProviderAdapter ABC ────────────────────────────────────────────────


class TestProviderAdapter:
    def test_cannot_instantiate(self) -> None:
        with pytest.raises(TypeError):
            ProviderAdapter()  # type: ignore[abstract]

    def test_concrete_subclass(self) -> None:
        class DummyProvider(ProviderAdapter):
            @property
            def provider_name(self) -> str:
                return "dummy"

            def call(self, request, api_key):
                return InferenceResponse(
                    text="ok",
                    input_tokens=1,
                    output_tokens=1,
                    latency_ms=1,
                    model=request.model,
                    provider=self.provider_name,
                )

            def supports_model(self, model_id: str) -> bool:
                return model_id.startswith("dummy-")

        p = DummyProvider()
        assert p.provider_name == "dummy"
        assert p.supports_model("dummy-v1")
        assert not p.supports_model("gpt-4o")

        resp = p.call(InferenceRequest(model="dummy-v1", prompt="hi"), "key")
        assert resp.text == "ok"
        assert resp.provider == "dummy"


# ── Exceptions ──────────────────────────────────────────────────────────


class TestExceptions:
    def test_billing_exception_hierarchy(self) -> None:
        exc = BillingException("no credits")
        assert isinstance(exc, AsahiException)
        assert str(exc) == "no credits"

    def test_rate_limit_error(self) -> None:
        exc = ProviderRateLimitError("429 rate limited")
        assert isinstance(exc, AsahiException)

    def test_server_error_status(self) -> None:
        exc = ProviderServerError("internal error", status_code=503)
        assert exc.status_code == 503

    def test_request_error_status(self) -> None:
        exc = ProviderRequestError("bad request", status_code=400)
        assert exc.status_code == 400
