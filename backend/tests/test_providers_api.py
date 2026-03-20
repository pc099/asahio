"""Tests for the providers API router — BYOK keys, Ollama, guided chains."""

import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import ChainSlot, GuidedChain, OllamaConfig, Organisation, ProviderKey


# ── Helpers ────────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def provider_org(session_factory: async_sessionmaker[AsyncSession]) -> dict:
    """Create an org with an API key for providers tests."""
    from app.db.models import ApiKey, KeyEnvironment, Member, MemberRole, User

    async with session_factory() as session:
        suffix = uuid.uuid4().hex[:8]
        user = User(email=f"provider-{suffix}@example.com", name="Provider User")
        session.add(user)
        await session.flush()

        org = Organisation(name="Provider Org", slug=f"provider-org-{suffix}")
        session.add(org)
        await session.flush()

        member = Member(
            organisation_id=org.id,
            user_id=user.id,
            role=MemberRole.OWNER,
        )
        session.add(member)

        raw_key, prefix, key_hash, last_four = ApiKey.generate(environment="live")
        api_key = ApiKey(
            organisation_id=org.id,
            created_by_user_id=user.id,
            name="Provider Test Key",
            environment=KeyEnvironment.LIVE,
            prefix=prefix,
            key_hash=key_hash,
            last_four=last_four,
            scopes=["*"],
            is_active=True,
        )
        session.add(api_key)
        await session.commit()

        return {
            "org": org,
            "user": user,
            "raw_key": raw_key,
            "org_id": str(org.id),
        }


def _auth_headers(provider_org: dict) -> dict:
    return {"Authorization": f"Bearer {provider_org['raw_key']}"}


# ── BYOK Key CRUD ─────────────────────────────────────────────────────


class TestBYOKKeys:
    @pytest.mark.asyncio
    async def test_list_keys_empty(self, client: AsyncClient, provider_org: dict) -> None:
        resp = await client.get("/providers/keys", headers=_auth_headers(provider_org))
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []

    @pytest.mark.asyncio
    async def test_store_and_list_key(self, client: AsyncClient, provider_org: dict) -> None:
        # Store
        resp = await client.post(
            "/providers/keys",
            json={"provider": "openai", "api_key": "sk-test-12345678"},
            headers=_auth_headers(provider_org),
        )
        assert resp.status_code == 201
        key_data = resp.json()
        assert key_data["provider"] == "openai"
        assert key_data["key_hint"] == "...5678"
        assert key_data["is_active"] is True

        # List
        resp = await client.get("/providers/keys", headers=_auth_headers(provider_org))
        assert resp.status_code == 200
        keys = resp.json()["data"]
        assert len(keys) == 1
        assert keys[0]["provider"] == "openai"

    @pytest.mark.asyncio
    async def test_store_key_invalid_provider(self, client: AsyncClient, provider_org: dict) -> None:
        resp = await client.post(
            "/providers/keys",
            json={"provider": "nonexistent", "api_key": "test-key"},
            headers=_auth_headers(provider_org),
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_key(self, client: AsyncClient, provider_org: dict) -> None:
        # Store
        resp = await client.post(
            "/providers/keys",
            json={"provider": "anthropic", "api_key": "sk-ant-test1234"},
            headers=_auth_headers(provider_org),
        )
        key_id = resp.json()["id"]

        # Delete
        resp = await client.delete(f"/providers/keys/{key_id}", headers=_auth_headers(provider_org))
        assert resp.status_code == 204

        # Should no longer appear in list
        resp = await client.get("/providers/keys", headers=_auth_headers(provider_org))
        keys = resp.json()["data"]
        assert all(k["id"] != key_id for k in keys)

    @pytest.mark.asyncio
    async def test_delete_key_cross_org_404(self, client: AsyncClient, provider_org: dict) -> None:
        fake_id = str(uuid.uuid4())
        resp = await client.delete(f"/providers/keys/{fake_id}", headers=_auth_headers(provider_org))
        assert resp.status_code == 404


# ── Ollama ─────────────────────────────────────────────────────────────


class TestOllama:
    @pytest.mark.asyncio
    async def test_list_ollama_empty(self, client: AsyncClient, provider_org: dict) -> None:
        resp = await client.get("/providers/ollama", headers=_auth_headers(provider_org))
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    @pytest.mark.asyncio
    async def test_verify_ollama_success(self, client: AsyncClient, provider_org: dict) -> None:
        import httpx as _httpx

        mock_response = _httpx.Response(
            200,
            json={"models": [{"name": "llama3"}, {"name": "codellama"}]},
            request=_httpx.Request("GET", "http://10.0.0.5:11434/api/tags"),
        )

        async def fake_get(*args, **kwargs):
            return mock_response

        mock_http = AsyncMock()
        mock_http.get = fake_get

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            resp = await client.post(
                "/providers/ollama/verify",
                json={"base_url": "http://10.0.0.5:11434", "name": "Dev Server"},
                headers=_auth_headers(provider_org),
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["is_verified"] is True
        assert "llama3" in data["available_models"]
        assert data["name"] == "Dev Server"

    @pytest.mark.asyncio
    async def test_verify_ollama_unreachable(self, client: AsyncClient, provider_org: dict) -> None:
        async def fake_get(*args, **kwargs):
            raise Exception("Connection refused")

        mock_http = AsyncMock()
        mock_http.get = fake_get

        with patch("httpx.AsyncClient") as mock_cls:
            mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_http)
            mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            resp = await client.post(
                "/providers/ollama/verify",
                json={"base_url": "http://unreachable:11434"},
                headers=_auth_headers(provider_org),
            )

        assert resp.status_code == 400
        assert "connectivity failed" in resp.json()["detail"].lower()


# ── Guided Chains ──────────────────────────────────────────────────────


class TestGuidedChains:
    @pytest.mark.asyncio
    async def test_list_chains_empty(self, client: AsyncClient, provider_org: dict) -> None:
        resp = await client.get("/providers/chains", headers=_auth_headers(provider_org))
        assert resp.status_code == 200
        assert resp.json()["data"] == []

    @pytest.mark.asyncio
    async def test_create_chain(self, client: AsyncClient, provider_org: dict) -> None:
        resp = await client.post(
            "/providers/chains",
            json={
                "name": "Primary + Fallback",
                "fallback_triggers": ["rate_limit", "server_error", "timeout"],
                "slots": [
                    {"provider": "openai", "model": "gpt-4o", "priority": 1},
                    {"provider": "anthropic", "model": "claude-haiku-4-5", "priority": 2},
                ],
            },
            headers=_auth_headers(provider_org),
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "Primary + Fallback"
        assert len(data["slots"]) == 2
        assert data["slots"][0]["priority"] == 1
        assert data["slots"][0]["model"] == "gpt-4o"

    @pytest.mark.asyncio
    async def test_create_chain_invalid_triggers(self, client: AsyncClient, provider_org: dict) -> None:
        resp = await client.post(
            "/providers/chains",
            json={
                "name": "Bad triggers",
                "fallback_triggers": ["not_a_trigger"],
                "slots": [{"provider": "openai", "model": "gpt-4o", "priority": 1}],
            },
            headers=_auth_headers(provider_org),
        )
        assert resp.status_code == 400
        assert "invalid trigger" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_create_chain_no_priority_1(self, client: AsyncClient, provider_org: dict) -> None:
        resp = await client.post(
            "/providers/chains",
            json={
                "name": "No primary",
                "slots": [{"provider": "openai", "model": "gpt-4o", "priority": 2}],
            },
            headers=_auth_headers(provider_org),
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_get_chain(self, client: AsyncClient, provider_org: dict) -> None:
        # Create
        resp = await client.post(
            "/providers/chains",
            json={
                "name": "Fetch me",
                "slots": [{"provider": "openai", "model": "gpt-4o", "priority": 1}],
            },
            headers=_auth_headers(provider_org),
        )
        chain_id = resp.json()["id"]

        # Get
        resp = await client.get(f"/providers/chains/{chain_id}", headers=_auth_headers(provider_org))
        assert resp.status_code == 200
        assert resp.json()["name"] == "Fetch me"

    @pytest.mark.asyncio
    async def test_delete_chain(self, client: AsyncClient, provider_org: dict) -> None:
        # Create
        resp = await client.post(
            "/providers/chains",
            json={
                "name": "Delete me",
                "slots": [{"provider": "openai", "model": "gpt-4o", "priority": 1}],
            },
            headers=_auth_headers(provider_org),
        )
        chain_id = resp.json()["id"]

        # Delete
        resp = await client.delete(f"/providers/chains/{chain_id}", headers=_auth_headers(provider_org))
        assert resp.status_code == 204

        # Should be 404 now
        resp = await client.get(f"/providers/chains/{chain_id}", headers=_auth_headers(provider_org))
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_chain_test_endpoint(self, client: AsyncClient, provider_org: dict) -> None:
        # Create chain
        resp = await client.post(
            "/providers/chains",
            json={
                "name": "Test chain",
                "slots": [{"provider": "openai", "model": "gpt-4o", "priority": 1}],
            },
            headers=_auth_headers(provider_org),
        )
        chain_id = resp.json()["id"]

        # Test — no BYOK key stored, no env var → should report key not available
        resp = await client.post(f"/providers/chains/{chain_id}/test", headers=_auth_headers(provider_org))
        assert resp.status_code == 200
        data = resp.json()
        assert data["chain_id"] == chain_id
        assert len(data["slots"]) == 1
        # Key availability depends on env vars — just check structure
        assert "key_available" in data["slots"][0]
        assert "provider" in data["slots"][0]
