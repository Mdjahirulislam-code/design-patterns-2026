"""actuator_execution_log

One row per attempt to send a command to an actuator (Phase 9 — Decorator).

Revision ID: 009
Revises: 008
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "009"
down_revision: str | None = "008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    op.create_table(
        "actuator_execution_log",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "device_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "success",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "policy_applied",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
        sa.Column(
            "message",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # newest executions first (dashboard list)
    op.create_index(
        "ix_actuator_execution_log_created_at",
        "actuator_execution_log",
        [sa.text("created_at DESC")],
        unique=False,
    )

    # newest execution of one device
    op.create_index(
        "ix_actuator_execution_log_device_created",
        "actuator_execution_log",
        ["device_id", sa.text("created_at DESC")],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_actuator_execution_log_device_created",
        table_name="actuator_execution_log",
    )

    op.drop_index(
        "ix_actuator_execution_log_created_at",
        table_name="actuator_execution_log",
    )

    op.drop_table("actuator_execution_log")
