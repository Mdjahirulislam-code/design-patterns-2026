"""alerts

Alerts stored by the AlertPersistenceSubscriber (Phase 11 — Observer).
All foreign keys are nullable and ON DELETE SET NULL.

Revision ID: 011
Revises: 010
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "011"
down_revision: str | None = "010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True),
                  server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("location_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("zone_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("device_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("severity", sa.String(length=16), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=16),
                  server_default=sa.text("'active'"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["location_id"], ["locations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["zone_id"], ["zones.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_alerts_status_created", "alerts",
                    ["status", sa.text("created_at DESC")], unique=False)
    op.create_index("ix_alerts_zone_created", "alerts",
                    ["zone_id", sa.text("created_at DESC")], unique=False)
    op.create_index("ix_alerts_location_created", "alerts",
                    ["location_id", sa.text("created_at DESC")], unique=False)


def downgrade() -> None:

    op.drop_index("ix_alerts_location_created", table_name="alerts")
    op.drop_index("ix_alerts_zone_created", table_name="alerts")
    op.drop_index("ix_alerts_status_created", table_name="alerts")
    op.drop_table("alerts")
