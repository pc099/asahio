"""SDK v2 tool support

Revision ID: 010_sdk_v2_tool_support
Revises: 009_phase_completion
Create Date: 2026-03-26

Adds tool-related fields to call_traces table for SDK v2 agentic capabilities:
- tools_requested: JSONB array of tools provided in the request
- tools_called: JSONB array of tools actually called by the model
- tool_call_count: Integer count of tool calls made
- web_search_enabled: Boolean flag for web search
- mcp_servers_used: JSONB array of MCP servers
- computer_use_enabled: Boolean flag for computer use (Anthropic)
- chain_id: UUID foreign key to guided_chains for fallback chain tracking
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "010_sdk_v2_tool_support"
down_revision: Union[str, None] = "009_phase_completion"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add tool-related fields to call_traces table."""
    # Add tool tracking fields
    op.add_column(
        "call_traces",
        sa.Column("tools_requested", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "call_traces",
        sa.Column("tools_called", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "call_traces",
        sa.Column("tool_call_count", sa.Integer, nullable=True, server_default="0"),
    )

    # Add agentic capability flags
    op.add_column(
        "call_traces",
        sa.Column("web_search_enabled", sa.Boolean, nullable=True, server_default="false"),
    )
    op.add_column(
        "call_traces",
        sa.Column("mcp_servers_used", postgresql.JSONB, nullable=True),
    )
    op.add_column(
        "call_traces",
        sa.Column("computer_use_enabled", sa.Boolean, nullable=True, server_default="false"),
    )

    # Add chain tracking
    op.add_column(
        "call_traces",
        sa.Column(
            "chain_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.create_foreign_key(
        "fk_call_traces_chain_id",
        "call_traces",
        "guided_chains",
        ["chain_id"],
        ["id"],
        ondelete="SET NULL",
    )

    # Add index for tool usage queries
    op.create_index(
        "ix_call_traces_tool_usage",
        "call_traces",
        ["organisation_id", "tool_call_count"],
        postgresql_where=sa.text("tool_call_count > 0"),
    )


def downgrade() -> None:
    """Remove tool-related fields from call_traces table."""
    # Drop index
    op.drop_index("ix_call_traces_tool_usage", table_name="call_traces")

    # Drop foreign key
    op.drop_constraint("fk_call_traces_chain_id", "call_traces", type_="foreignkey")

    # Drop columns
    op.drop_column("call_traces", "chain_id")
    op.drop_column("call_traces", "computer_use_enabled")
    op.drop_column("call_traces", "mcp_servers_used")
    op.drop_column("call_traces", "web_search_enabled")
    op.drop_column("call_traces", "tool_call_count")
    op.drop_column("call_traces", "tools_called")
    op.drop_column("call_traces", "tools_requested")
