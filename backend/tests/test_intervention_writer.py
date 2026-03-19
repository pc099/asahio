"""Tests for the intervention log writer."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.intervention_writer import InterventionLogPayload, write_intervention_log


@pytest.fixture
def payload() -> InterventionLogPayload:
    return InterventionLogPayload(
        org_id=str(uuid.uuid4()),
        agent_id=str(uuid.uuid4()),
        call_trace_id=str(uuid.uuid4()),
        request_id="req-123",
        intervention_level=2,
        intervention_mode="ASSISTED",
        risk_score=0.55,
        risk_factors={"complexity": 0.7, "model_risk": 0.3},
        action_taken="augment",
        action_detail="Appended verification suffix",
        original_model="gpt-4o",
        final_model="gpt-4o",
        prompt_modified=True,
        was_blocked=False,
    )


class TestInterventionWriter:
    @pytest.mark.asyncio
    async def test_writes_log_entry(self, payload: InterventionLogPayload) -> None:
        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.services.intervention_writer.async_session_factory",
            return_value=mock_ctx,
        ):
            await write_intervention_log(payload)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

        log_entry = mock_session.add.call_args[0][0]
        assert log_entry.intervention_level == 2
        assert log_entry.action_taken == "augment"
        assert log_entry.risk_score == 0.55
        assert log_entry.prompt_modified is True

    @pytest.mark.asyncio
    async def test_handles_missing_agent_id(self) -> None:
        payload = InterventionLogPayload(
            org_id=str(uuid.uuid4()),
            intervention_level=0,
            intervention_mode="OBSERVE",
            risk_score=0.1,
            action_taken="log",
        )

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.services.intervention_writer.async_session_factory",
            return_value=mock_ctx,
        ):
            await write_intervention_log(payload)

        log_entry = mock_session.add.call_args[0][0]
        assert log_entry.agent_id is None
        assert log_entry.call_trace_id is None

    @pytest.mark.asyncio
    async def test_db_error_does_not_raise(self, payload: InterventionLogPayload) -> None:
        """Fire-and-forget: DB errors logged, not raised."""
        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(side_effect=RuntimeError("DB down"))
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.services.intervention_writer.async_session_factory",
            return_value=mock_ctx,
        ):
            # Should not raise
            await write_intervention_log(payload)

    @pytest.mark.asyncio
    async def test_block_log(self) -> None:
        payload = InterventionLogPayload(
            org_id=str(uuid.uuid4()),
            intervention_level=4,
            intervention_mode="AUTONOMOUS",
            risk_score=0.95,
            action_taken="block",
            was_blocked=True,
        )

        mock_session = AsyncMock()
        mock_session.add = MagicMock()
        mock_session.commit = AsyncMock()

        mock_ctx = AsyncMock()
        mock_ctx.__aenter__ = AsyncMock(return_value=mock_session)
        mock_ctx.__aexit__ = AsyncMock(return_value=False)

        with patch(
            "app.services.intervention_writer.async_session_factory",
            return_value=mock_ctx,
        ):
            await write_intervention_log(payload)

        log_entry = mock_session.add.call_args[0][0]
        assert log_entry.was_blocked is True
        assert log_entry.intervention_level == 4
