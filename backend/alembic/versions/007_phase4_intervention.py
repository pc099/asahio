"""Add intervention_logs, mode_transition_logs tables and Phase 4 columns.

Revision ID: 007_phase4_intervention
Revises: 006_aba_tables
Create Date: 2026-03-19
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_phase4_intervention"
down_revision: Union[str, None] = "006_aba_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(bind, table_name: str) -> bool:
    """Check if a table exists in the public schema."""
    result = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = 'public' AND table_name = :t"
        ),
        {"t": table_name},
    )
    return result.scalar() is not None


def _column_exists(bind, table_name: str, column_name: str) -> bool:
    """Check if a column exists on a table."""
    result = bind.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_schema = 'public' AND table_name = :t AND column_name = :c"
        ),
        {"t": table_name, "c": column_name},
    )
    return result.scalar() is not None


def upgrade() -> None:
    bind = op.get_bind()

    # ── intervention_logs table ──────────────────────────────────────────
    if not _table_exists(bind, "intervention_logs"):
        op.create_table(
            "intervention_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "organisation_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("organisations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "agent_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("agents.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column(
                "call_trace_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("call_traces.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("request_id", sa.String(64), nullable=True),
            sa.Column("intervention_level", sa.Integer, nullable=False),
            sa.Column("intervention_mode", sa.String(20), nullable=False),
            sa.Column("risk_score", sa.Numeric(5, 4), nullable=False),
            sa.Column("risk_factors", postgresql.JSONB, nullable=False, server_default="{}"),
            sa.Column("action_taken", sa.String(50), nullable=False),
            sa.Column("action_detail", sa.Text, nullable=True),
            sa.Column("original_model", sa.String(100), nullable=True),
            sa.Column("final_model", sa.String(100), nullable=True),
            sa.Column("prompt_modified", sa.Boolean, nullable=False, server_default="false"),
            sa.Column("was_blocked", sa.Boolean, nullable=False, server_default="false"),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index(
            "ix_intervention_logs_org_created",
            "intervention_logs",
            ["organisation_id", "created_at"],
        )
        op.create_index(
            "ix_intervention_logs_agent_id",
            "intervention_logs",
            ["agent_id"],
        )

    # ── mode_transition_logs table ───────────────────────────────────────
    if not _table_exists(bind, "mode_transition_logs"):
        op.create_table(
            "mode_transition_logs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "organisation_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("organisations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "agent_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("agents.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("previous_mode", sa.String(20), nullable=False),
            sa.Column("new_mode", sa.String(20), nullable=False),
            sa.Column("trigger", sa.String(50), nullable=False),
            sa.Column("baseline_confidence", sa.Numeric(5, 4), nullable=True),
            sa.Column("evidence", postgresql.JSONB, nullable=False, server_default="{}"),
            sa.Column(
                "operator_user_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index(
            "ix_mode_transitions_org_agent",
            "mode_transition_logs",
            ["organisation_id", "agent_id"],
        )

    # ── Column additions to call_traces ──────────────────────────────────
    if not _column_exists(bind, "call_traces", "risk_score"):
        op.add_column("call_traces", sa.Column("risk_score", sa.Numeric(5, 4), nullable=True))

    if not _column_exists(bind, "call_traces", "intervention_level"):
        op.add_column("call_traces", sa.Column("intervention_level", sa.Integer, nullable=True))

    # ── Column additions to agents ───────────────────────────────────────
    if not _column_exists(bind, "agents", "mode_entered_at"):
        op.add_column(
            "agents",
            sa.Column("mode_entered_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists(bind, "agents", "autonomous_authorized_at"):
        op.add_column(
            "agents",
            sa.Column("autonomous_authorized_at", sa.DateTime(timezone=True), nullable=True),
        )

    if not _column_exists(bind, "agents", "autonomous_authorized_by"):
        op.add_column(
            "agents",
            sa.Column(
                "autonomous_authorized_by",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="SET NULL"),
                nullable=True,
            ),
        )

    if not _column_exists(bind, "agents", "risk_threshold_overrides"):
        op.add_column(
            "agents",
            sa.Column("risk_threshold_overrides", postgresql.JSONB, nullable=True),
        )


def downgrade() -> None:
    # Remove agent columns
    op.drop_column("agents", "risk_threshold_overrides")
    op.drop_column("agents", "autonomous_authorized_by")
    op.drop_column("agents", "autonomous_authorized_at")
    op.drop_column("agents", "mode_entered_at")

    # Remove call_trace columns
    op.drop_column("call_traces", "intervention_level")
    op.drop_column("call_traces", "risk_score")

    # Drop tables
    op.drop_table("mode_transition_logs")
    op.drop_table("intervention_logs")
