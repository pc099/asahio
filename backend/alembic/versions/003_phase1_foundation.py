"""Phase 1 foundation alignment tables and columns.

Revision ID: 003_phase1
Revises: 002
Create Date: 2026-03-06
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_phase1"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

compliance_tier = postgresql.ENUM(
    "standard", "enterprise", "hipaa", name="compliancetier", create_type=False
)
routing_mode = postgresql.ENUM(
    "AUTO", "EXPLICIT", "GUIDED", name="routingmode", create_type=False
)
intervention_mode = postgresql.ENUM(
    "OBSERVE", "ASSISTED", "AUTONOMOUS", name="interventionmode", create_type=False
)
billing_status = postgresql.ENUM(
    "trialing", "active", "past_due", "canceled", name="billingstatus", create_type=False
)
model_endpoint_type = postgresql.ENUM(
    "platform", "fine_tuned", "external", name="modelendpointtype", create_type=False
)
plan_tier = postgresql.ENUM("free", "pro", "enterprise", name="plantier", create_type=False)


def upgrade() -> None:
    bind = op.get_bind()
    compliance_tier.create(bind, checkfirst=True)
    routing_mode.create(bind, checkfirst=True)
    intervention_mode.create(bind, checkfirst=True)
    billing_status.create(bind, checkfirst=True)
    model_endpoint_type.create(bind, checkfirst=True)
    plan_tier.create(bind, checkfirst=True)

    op.add_column(
        "organisations",
        sa.Column("compliance_tier", compliance_tier, nullable=False, server_default="standard"),
    )

    op.create_table(
        "billing_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organisations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("plan", plan_tier, nullable=False, server_default="free"),
        sa.Column("status", billing_status, nullable=False, server_default="trialing"),
        sa.Column("billing_email", sa.String(255), nullable=True),
        sa.Column("stripe_price_id", sa.String(255), nullable=True),
        sa.Column("stripe_meter_name", sa.String(255), nullable=False, server_default="asahio_tokens"),
        sa.Column("current_period_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("current_period_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("organisation_id", name="uq_billing_account_org"),
    )

    op.create_table(
        "model_endpoints",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organisations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("endpoint_type", model_endpoint_type, nullable=False, server_default="platform"),
        sa.Column("provider", sa.String(100), nullable=False, server_default="asahio"),
        sa.Column("model_id", sa.String(255), nullable=False),
        sa.Column("endpoint_url", sa.Text(), nullable=True),
        sa.Column("secret_reference", sa.Text(), nullable=True),
        sa.Column("default_headers", postgresql.JSONB, server_default="{}"),
        sa.Column("capability_flags", postgresql.JSONB, server_default="{}"),
        sa.Column("fallback_model_id", sa.String(255), nullable=True),
        sa.Column("health_status", sa.String(50), nullable=False, server_default="unknown"),
        sa.Column("last_health_error", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_model_endpoints_org_id", "model_endpoints", ["organisation_id"])

    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organisations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "model_endpoint_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("model_endpoints.id"),
            nullable=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("routing_mode", routing_mode, nullable=False, server_default="AUTO"),
        sa.Column("intervention_mode", intervention_mode, nullable=False, server_default="OBSERVE"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("organisation_id", "slug", name="uq_agents_org_slug"),
    )
    op.create_index("ix_agents_org_id", "agents", ["organisation_id"])

    op.create_table(
        "agent_sessions",
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
        sa.Column("external_session_id", sa.String(255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "organisation_id",
            "agent_id",
            "external_session_id",
            name="uq_agent_sessions_external",
        ),
    )
    op.create_index("ix_agent_sessions_org_id", "agent_sessions", ["organisation_id"])

    op.add_column("request_logs", sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column(
        "request_logs",
        sa.Column("agent_session_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "request_logs",
        sa.Column("model_endpoint_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column("request_logs", sa.Column("request_id", sa.String(64), nullable=True))
    op.add_column(
        "request_logs",
        sa.Column("intervention_mode", sa.String(20), nullable=True),
    )
    op.create_foreign_key("fk_request_logs_agent_id", "request_logs", "agents", ["agent_id"], ["id"])
    op.create_foreign_key("fk_request_logs_agent_session_id", "request_logs", "agent_sessions", ["agent_session_id"], ["id"])
    op.create_foreign_key("fk_request_logs_model_endpoint_id", "request_logs", "model_endpoints", ["model_endpoint_id"], ["id"])

    op.create_table(
        "call_traces",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organisations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column(
            "agent_session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agent_sessions.id"),
            nullable=True,
        ),
        sa.Column(
            "request_log_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("request_logs.id"),
            nullable=True,
        ),
        sa.Column("request_id", sa.String(64), nullable=True),
        sa.Column("model_requested", sa.String(100), nullable=True),
        sa.Column("model_used", sa.String(100), nullable=True),
        sa.Column("provider", sa.String(50), nullable=True),
        sa.Column("routing_mode", sa.String(20), nullable=True),
        sa.Column("intervention_mode", sa.String(20), nullable=True),
        sa.Column("policy_action", sa.String(50), nullable=True),
        sa.Column("policy_reason", sa.Text(), nullable=True),
        sa.Column("cache_hit", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("cache_tier", sa.String(20), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("trace_metadata", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_call_traces_org_created", "call_traces", ["organisation_id", "created_at"])

    op.create_table(
        "routing_decision_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organisation_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organisations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id"), nullable=True),
        sa.Column(
            "call_trace_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("call_traces.id"),
            nullable=True,
        ),
        sa.Column("routing_mode", sa.String(20), nullable=True),
        sa.Column("intervention_mode", sa.String(20), nullable=True),
        sa.Column("selected_model", sa.String(100), nullable=True),
        sa.Column("selected_provider", sa.String(50), nullable=True),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=True),
        sa.Column("decision_summary", sa.Text(), nullable=True),
        sa.Column("factors", postgresql.JSONB, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index(
        "ix_routing_decisions_org_created",
        "routing_decision_logs",
        ["organisation_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_routing_decisions_org_created", table_name="routing_decision_logs")
    op.drop_table("routing_decision_logs")
    op.drop_index("ix_call_traces_org_created", table_name="call_traces")
    op.drop_table("call_traces")
    op.drop_constraint("fk_request_logs_model_endpoint_id", "request_logs", type_="foreignkey")
    op.drop_constraint("fk_request_logs_agent_session_id", "request_logs", type_="foreignkey")
    op.drop_constraint("fk_request_logs_agent_id", "request_logs", type_="foreignkey")
    op.drop_column("request_logs", "intervention_mode")
    op.drop_column("request_logs", "request_id")
    op.drop_column("request_logs", "model_endpoint_id")
    op.drop_column("request_logs", "agent_session_id")
    op.drop_column("request_logs", "agent_id")
    op.drop_index("ix_agent_sessions_org_id", table_name="agent_sessions")
    op.drop_table("agent_sessions")
    op.drop_index("ix_agents_org_id", table_name="agents")
    op.drop_table("agents")
    op.drop_index("ix_model_endpoints_org_id", table_name="model_endpoints")
    op.drop_table("model_endpoints")
    op.drop_table("billing_accounts")
    op.drop_column("organisations", "compliance_tier")

    bind = op.get_bind()
    model_endpoint_type.drop(bind, checkfirst=True)
    billing_status.drop(bind, checkfirst=True)
    intervention_mode.drop(bind, checkfirst=True)
    routing_mode.drop(bind, checkfirst=True)
    compliance_tier.drop(bind, checkfirst=True)


