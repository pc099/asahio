"""Tests for the ABA observation writer."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.aba_writer import ABAObservationPayload, write_aba_observation


@pytest.fixture
def payload() -> ABAObservationPayload:
    return ABAObservationPayload(
        org_id=str(uuid.uuid4()),
        agent_id=str(uuid.uuid4()),
        call_trace_id=str(uuid.uuid4()),
        prompt="What is Python?",
        response="Python is a programming language.",
        model_used="gpt-4o",
        latency_ms=150,
        cache_hit=False,
        input_tokens=10,
        output_tokens=20,
    )


class TestABAWriter:
    @pytest.mark.asyncio
    async def test_creates_fingerprint_on_first_call(self, payload: ABAObservationPayload) -> None:
        """First observation for an agent should create a new fingerprint."""
        mock_session = AsyncMock()
        # scalar_one_or_none returns None (no existing fingerprint)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        # For the last_type query
        mock_last_result = MagicMock()
        mock_last_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(side_effect=[mock_result, mock_last_result])
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_factory = AsyncMock()
        mock_factory.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.aba_writer.async_session_factory", return_value=mock_factory):
            await write_aba_observation(payload)

        # Should have added fingerprint + structural record = 2 add calls
        assert mock_session.add.call_count == 2
        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_updates_existing_fingerprint(self, payload: ABAObservationPayload) -> None:
        """Observation for existing agent should update the fingerprint, not create new."""
        mock_fingerprint = MagicMock()
        mock_fingerprint.total_observations = 5
        mock_fingerprint.avg_complexity = 0.3
        mock_fingerprint.avg_context_length = 50.0
        mock_fingerprint.hallucination_rate = 0.0
        mock_fingerprint.model_distribution = {"gpt-4o": 5}
        mock_fingerprint.cache_hit_rate = 0.2
        mock_fingerprint.baseline_confidence = 0.5

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = mock_fingerprint
        mock_last_result = MagicMock()
        mock_last_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(side_effect=[mock_result, mock_last_result])
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_factory = AsyncMock()
        mock_factory.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.aba_writer.async_session_factory", return_value=mock_factory):
            await write_aba_observation(payload)

        # Only structural record added (fingerprint already exists)
        assert mock_session.add.call_count == 1
        # Fingerprint should be updated
        assert mock_fingerprint.total_observations == 6

    @pytest.mark.asyncio
    async def test_handles_db_error_gracefully(self, payload: ABAObservationPayload) -> None:
        """DB errors should be caught and logged, not raised."""
        mock_factory = AsyncMock()
        mock_factory.__aenter__ = AsyncMock(side_effect=RuntimeError("DB connection failed"))
        mock_factory.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.aba_writer.async_session_factory", return_value=mock_factory):
            # Should not raise
            await write_aba_observation(payload)

    @pytest.mark.asyncio
    async def test_minimal_payload(self) -> None:
        """Payload with only required fields should still work."""
        minimal = ABAObservationPayload(
            org_id=str(uuid.uuid4()),
            agent_id=str(uuid.uuid4()),
        )

        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_last_result = MagicMock()
        mock_last_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(side_effect=[mock_result, mock_last_result])
        mock_session.add = MagicMock()
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_factory = AsyncMock()
        mock_factory.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.aba_writer.async_session_factory", return_value=mock_factory):
            await write_aba_observation(minimal)

        mock_session.commit.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_token_count_is_sum_of_input_output(self, payload: ABAObservationPayload) -> None:
        """StructuralRecord token_count should be input_tokens + output_tokens."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_last_result = MagicMock()
        mock_last_result.scalar_one_or_none.return_value = None
        mock_session.execute = AsyncMock(side_effect=[mock_result, mock_last_result])
        added_objects = []
        mock_session.add = MagicMock(side_effect=lambda obj: added_objects.append(obj))
        mock_session.flush = AsyncMock()
        mock_session.commit = AsyncMock()

        mock_factory = AsyncMock()
        mock_factory.__aenter__ = AsyncMock(return_value=mock_session)
        mock_factory.__aexit__ = AsyncMock(return_value=False)

        with patch("app.services.aba_writer.async_session_factory", return_value=mock_factory):
            await write_aba_observation(payload)

        # Find the StructuralRecord in added objects
        from app.db.models import StructuralRecord
        records = [o for o in added_objects if isinstance(o, StructuralRecord)]
        assert len(records) == 1
        assert records[0].token_count == payload.input_tokens + payload.output_tokens
