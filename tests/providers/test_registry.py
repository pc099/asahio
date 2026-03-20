"""Tests for provider registry and EnvKeyResolver."""

from unittest.mock import patch

import pytest

from src.providers import (
    PROVIDER_REGISTRY,
    EnvKeyResolver,
    get_provider,
    get_provider_for_model,
    register_ollama,
    BillingException,
)
from src.providers.providers import (
    AnthropicProvider,
    DeepSeekProvider,
    GoogleProvider,
    MistralProvider,
    OllamaProvider,
    OpenAIProvider,
)


# ── Registry ────────────────────────────────────────────────────────────


class TestProviderRegistry:
    def test_builtin_providers(self) -> None:
        assert "openai" in PROVIDER_REGISTRY
        assert "anthropic" in PROVIDER_REGISTRY
        assert "google" in PROVIDER_REGISTRY
        assert "deepseek" in PROVIDER_REGISTRY
        assert "mistral" in PROVIDER_REGISTRY

    def test_get_provider_known(self) -> None:
        p = get_provider("openai")
        assert isinstance(p, OpenAIProvider)
        assert p.provider_name == "openai"

    def test_get_provider_unknown(self) -> None:
        with pytest.raises(ValueError, match="Unknown provider"):
            get_provider("nonexistent")

    def test_get_provider_for_model_openai(self) -> None:
        p = get_provider_for_model("gpt-4o")
        assert isinstance(p, OpenAIProvider)

    def test_get_provider_for_model_anthropic(self) -> None:
        p = get_provider_for_model("claude-sonnet-4-6")
        assert isinstance(p, AnthropicProvider)

    def test_get_provider_for_model_google(self) -> None:
        p = get_provider_for_model("gemini-2.5-pro")
        assert isinstance(p, GoogleProvider)

    def test_get_provider_for_model_deepseek(self) -> None:
        p = get_provider_for_model("deepseek-chat")
        assert isinstance(p, DeepSeekProvider)

    def test_get_provider_for_model_mistral(self) -> None:
        p = get_provider_for_model("mistral-large-latest")
        assert isinstance(p, MistralProvider)

    def test_get_provider_for_model_unknown(self) -> None:
        with pytest.raises(ValueError, match="No provider found"):
            get_provider_for_model("totally-unknown-model")


class TestRegisterOllama:
    def test_register_and_retrieve(self) -> None:
        provider = register_ollama("my-server", "http://10.0.0.1:11434")
        assert isinstance(provider, OllamaProvider)
        assert "ollama:my-server" in PROVIDER_REGISTRY

        retrieved = get_provider("ollama:my-server")
        assert retrieved is provider

        # Cleanup
        del PROVIDER_REGISTRY["ollama:my-server"]

    def test_register_updates_existing(self) -> None:
        register_ollama("test-srv", "http://old:11434")
        register_ollama("test-srv", "http://new:11434")

        p = get_provider("ollama:test-srv")
        assert isinstance(p, OllamaProvider)
        assert p._base_url == "http://new:11434"

        # Cleanup
        del PROVIDER_REGISTRY["ollama:test-srv"]


# ── EnvKeyResolver ──────────────────────────────────────────────────────


class TestEnvKeyResolver:
    def test_resolve_openai(self) -> None:
        resolver = EnvKeyResolver()
        with patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-123"}):
            key = resolver.resolve("openai")
        assert key == "sk-test-123"

    def test_resolve_google(self) -> None:
        resolver = EnvKeyResolver()
        with patch.dict("os.environ", {"GOOGLE_API_KEY": "AIza-xxx"}):
            key = resolver.resolve("google")
        assert key == "AIza-xxx"

    def test_resolve_ollama_returns_empty(self) -> None:
        resolver = EnvKeyResolver()
        key = resolver.resolve("ollama")
        assert key == ""

    def test_resolve_ollama_prefixed(self) -> None:
        resolver = EnvKeyResolver()
        key = resolver.resolve("ollama:my-server")
        assert key == ""

    def test_resolve_missing_key_raises(self) -> None:
        resolver = EnvKeyResolver()
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(BillingException, match="API key not configured"):
                resolver.resolve("openai")

    def test_resolve_unknown_provider_raises(self) -> None:
        resolver = EnvKeyResolver()
        with pytest.raises(BillingException, match="No key mapping"):
            resolver.resolve("unknown-provider")
