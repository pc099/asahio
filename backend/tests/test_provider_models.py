"""Tests for Provider Sprint DB models (CRUD on SQLite)."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.models import (
    ChainSlot,
    GuidedChain,
    OllamaConfig,
    Organisation,
    ProviderKey,
)


# ── ProviderKey ─────────────────────────────────────────────────────────


class TestProviderKey:
    @pytest.mark.asyncio
    async def test_create_and_read(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        async with session_factory() as session:
            org = Organisation(id=uuid.uuid4(), name="PK Org", slug=f"pk-org-{uuid.uuid4().hex[:8]}")
            session.add(org)
            await session.flush()

            pk = ProviderKey(
                id=uuid.uuid4(),
                organisation_id=org.id,
                provider="openai",
                encrypted_key="gAAAAABh...",
                key_hint="...xK9z",
            )
            session.add(pk)
            await session.commit()

            result = await session.execute(
                select(ProviderKey).where(ProviderKey.organisation_id == org.id)
            )
            row = result.scalar_one()
            assert row.provider == "openai"
            assert row.encrypted_key == "gAAAAABh..."
            assert row.key_hint == "...xK9z"
            assert row.is_active is True

    @pytest.mark.asyncio
    async def test_soft_delete(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        async with session_factory() as session:
            org = Organisation(id=uuid.uuid4(), name="PK Org2", slug=f"pk-org2-{uuid.uuid4().hex[:8]}")
            session.add(org)
            await session.flush()

            pk = ProviderKey(
                id=uuid.uuid4(),
                organisation_id=org.id,
                provider="google",
                encrypted_key="enc-key",
            )
            session.add(pk)
            await session.commit()

            pk.is_active = False
            await session.commit()

            result = await session.execute(
                select(ProviderKey).where(ProviderKey.id == pk.id)
            )
            assert result.scalar_one().is_active is False


# ── GuidedChain + ChainSlot ────────────────────────────────────────────


class TestGuidedChain:
    @pytest.mark.asyncio
    async def test_create_chain_with_slots(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        async with session_factory() as session:
            org = Organisation(id=uuid.uuid4(), name="Chain Org", slug=f"chain-org-{uuid.uuid4().hex[:8]}")
            session.add(org)
            await session.flush()

            chain = GuidedChain(
                id=uuid.uuid4(),
                organisation_id=org.id,
                name="Primary + Fallback",
                fallback_triggers=["rate_limit", "server_error", "timeout"],
            )
            session.add(chain)
            await session.flush()

            slot1 = ChainSlot(
                id=uuid.uuid4(),
                chain_id=chain.id,
                provider="openai",
                model="gpt-4o",
                priority=1,
            )
            slot2 = ChainSlot(
                id=uuid.uuid4(),
                chain_id=chain.id,
                provider="anthropic",
                model="claude-haiku-4-5",
                priority=2,
                max_latency_ms=500,
            )
            session.add_all([slot1, slot2])
            await session.commit()

            result = await session.execute(
                select(GuidedChain).where(GuidedChain.id == chain.id)
            )
            loaded = result.scalar_one()
            assert loaded.name == "Primary + Fallback"
            assert loaded.fallback_triggers == ["rate_limit", "server_error", "timeout"]
            assert loaded.is_active is True

    @pytest.mark.asyncio
    async def test_chain_slots_ordered_by_priority(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with session_factory() as session:
            org = Organisation(id=uuid.uuid4(), name="Slot Org", slug=f"slot-org-{uuid.uuid4().hex[:8]}")
            session.add(org)
            await session.flush()

            chain = GuidedChain(
                id=uuid.uuid4(),
                organisation_id=org.id,
                name="Three-slot chain",
            )
            session.add(chain)
            await session.flush()

            for priority, model in [(3, "deepseek-chat"), (1, "gpt-4o"), (2, "claude-sonnet-4-6")]:
                session.add(ChainSlot(
                    id=uuid.uuid4(),
                    chain_id=chain.id,
                    provider="test",
                    model=model,
                    priority=priority,
                ))
            await session.commit()

            result = await session.execute(
                select(ChainSlot).where(ChainSlot.chain_id == chain.id).order_by(ChainSlot.priority)
            )
            slots = result.scalars().all()
            assert [s.priority for s in slots] == [1, 2, 3]
            assert slots[0].model == "gpt-4o"

    @pytest.mark.asyncio
    async def test_delete_chain_cascades_slots(
        self, session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with session_factory() as session:
            org = Organisation(id=uuid.uuid4(), name="Del Org", slug=f"del-org-{uuid.uuid4().hex[:8]}")
            session.add(org)
            await session.flush()

            chain = GuidedChain(
                id=uuid.uuid4(),
                organisation_id=org.id,
                name="To delete",
            )
            session.add(chain)
            await session.flush()

            session.add(ChainSlot(
                id=uuid.uuid4(),
                chain_id=chain.id,
                provider="openai",
                model="gpt-4o",
                priority=1,
            ))
            await session.commit()

            await session.delete(chain)
            await session.commit()

            result = await session.execute(
                select(ChainSlot).where(ChainSlot.chain_id == chain.id)
            )
            assert result.scalars().all() == []


# ── OllamaConfig ───────────────────────────────────────────────────────


class TestOllamaConfig:
    @pytest.mark.asyncio
    async def test_create_and_read(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        async with session_factory() as session:
            org = Organisation(id=uuid.uuid4(), name="Ollama Org", slug=f"ollama-org-{uuid.uuid4().hex[:8]}")
            session.add(org)
            await session.flush()

            config = OllamaConfig(
                id=uuid.uuid4(),
                organisation_id=org.id,
                name="Dev Server",
                base_url="http://10.0.0.5:11434",
                available_models=["llama3", "codellama"],
            )
            session.add(config)
            await session.commit()

            result = await session.execute(
                select(OllamaConfig).where(OllamaConfig.organisation_id == org.id)
            )
            row = result.scalar_one()
            assert row.base_url == "http://10.0.0.5:11434"
            assert row.available_models == ["llama3", "codellama"]
            assert row.is_verified is False

    @pytest.mark.asyncio
    async def test_verify_config(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        async with session_factory() as session:
            org = Organisation(id=uuid.uuid4(), name="Ollama Org2", slug=f"ollama-org2-{uuid.uuid4().hex[:8]}")
            session.add(org)
            await session.flush()

            config = OllamaConfig(
                id=uuid.uuid4(),
                organisation_id=org.id,
                base_url="http://localhost:11434",
            )
            session.add(config)
            await session.commit()

            config.is_verified = True
            config.available_models = ["llama3:latest", "mistral-7b:latest"]
            await session.commit()

            result = await session.execute(
                select(OllamaConfig).where(OllamaConfig.id == config.id)
            )
            row = result.scalar_one()
            assert row.is_verified is True
            assert len(row.available_models) == 2
