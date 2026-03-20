"""Add hallucination_tag to call_traces, ip_allowlist and routing_weight_overrides to organisations.

Revision ID: 009_phase_completion
Revises: 008_provider_sprint
Create Date: 2026-03-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_phase_completion"
down_revision: Union[str, None] = "008_provider_sprint"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


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

    # ── call_traces: hallucination_tag + hallucination_tag_notes ──────
    if not _column_exists(bind, "call_traces", "hallucination_tag"):
        op.add_column(
            "call_traces",
            sa.Column("hallucination_tag", sa.String(20), nullable=True),
        )
    if not _column_exists(bind, "call_traces", "hallucination_tag_notes"):
        op.add_column(
            "call_traces",
            sa.Column("hallucination_tag_notes", sa.Text, nullable=True),
        )

    # ── organisations: routing_weight_overrides ──────────────────────
    if not _column_exists(bind, "organisations", "routing_weight_overrides"):
        op.add_column(
            "organisations",
            sa.Column("routing_weight_overrides", postgresql.JSONB, nullable=True),
        )

    # ── organisations: ip_allowlist ──────────────────────────────────
    if not _column_exists(bind, "organisations", "ip_allowlist"):
        op.add_column(
            "organisations",
            sa.Column("ip_allowlist", postgresql.JSONB, nullable=True),
        )


def downgrade() -> None:
    op.drop_column("organisations", "ip_allowlist")
    op.drop_column("organisations", "routing_weight_overrides")
    op.drop_column("call_traces", "hallucination_tag_notes")
    op.drop_column("call_traces", "hallucination_tag")
