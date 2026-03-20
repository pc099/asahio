"""Add provider_keys, guided_chains, chain_slots, ollama_configs tables.

Revision ID: 008_provider_sprint
Revises: 007_phase4_intervention
Create Date: 2026-03-20
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_provider_sprint"
down_revision: Union[str, None] = "007_phase4_intervention"
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


def upgrade() -> None:
    bind = op.get_bind()

    # ── provider_keys ────────────────────────────────────────────────────
    if not _table_exists(bind, "provider_keys"):
        op.create_table(
            "provider_keys",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "organisation_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("organisations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("encrypted_key", sa.Text, nullable=False),
            sa.Column("key_hint", sa.String(10), nullable=True),
            sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
            sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("organisation_id", "provider", name="uq_provider_key_org_provider"),
        )
        op.create_index("ix_provider_keys_org_id", "provider_keys", ["organisation_id"])

    # ── guided_chains ────────────────────────────────────────────────────
    if not _table_exists(bind, "guided_chains"):
        op.create_table(
            "guided_chains",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "organisation_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("organisations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(255), nullable=False),
            sa.Column(
                "fallback_triggers",
                postgresql.JSONB,
                server_default=sa.text("'[\"rate_limit\",\"server_error\",\"timeout\"]'::jsonb"),
                nullable=False,
            ),
            sa.Column("is_default", sa.Boolean, server_default=sa.text("false"), nullable=False),
            sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )
        op.create_index("ix_guided_chains_org_id", "guided_chains", ["organisation_id"])

    # ── chain_slots ──────────────────────────────────────────────────────
    if not _table_exists(bind, "chain_slots"):
        op.create_table(
            "chain_slots",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "chain_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("guided_chains.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("provider", sa.String(50), nullable=False),
            sa.Column("model", sa.String(100), nullable=False),
            sa.Column("priority", sa.Integer, nullable=False),
            sa.Column("max_latency_ms", sa.Integer, nullable=True),
            sa.Column("max_cost_per_1k_tokens", sa.Numeric(8, 6), nullable=True),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("chain_id", "priority", name="uq_chain_slot_position"),
        )
        op.create_index("ix_chain_slots_chain_id", "chain_slots", ["chain_id"])

    # ── ollama_configs ───────────────────────────────────────────────────
    if not _table_exists(bind, "ollama_configs"):
        op.create_table(
            "ollama_configs",
            sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "organisation_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("organisations.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("name", sa.String(255), nullable=True),
            sa.Column("base_url", sa.Text, nullable=False),
            sa.Column("is_verified", sa.Boolean, server_default=sa.text("false"), nullable=False),
            sa.Column(
                "available_models",
                postgresql.JSONB,
                server_default=sa.text("'[]'::jsonb"),
                nullable=False,
            ),
            sa.Column("last_verified_at", sa.DateTime(timezone=True), nullable=True),
            sa.Column("is_active", sa.Boolean, server_default=sa.text("true"), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.UniqueConstraint("organisation_id", "base_url", name="uq_ollama_config_org_url"),
        )
        op.create_index("ix_ollama_configs_org_id", "ollama_configs", ["organisation_id"])


def downgrade() -> None:
    op.drop_table("chain_slots")
    op.drop_table("guided_chains")
    op.drop_table("provider_keys")
    op.drop_table("ollama_configs")
