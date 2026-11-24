"""actuator_states

One persisted lifecycle state per actuator (Phase 8 — State).
Existing actuators are seeded to 'idle' here, in the migration.
Actuators created later get their row when they are provisioned.

Revision ID: 008
Revises: 007
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "008"
down_revision: str | None = "007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    op.create_table(
        "actuator_states",
        sa.Column(
            "device_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "state",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("device_id"),
    )

    # Seed (added by hand): every existing actuator starts in 'idle'.
    op.execute(
        """
        INSERT INTO actuator_states (device_id, state)
        SELECT id, 'idle'
        FROM devices
        WHERE role = 'actuator'
        """
    )


def downgrade() -> None:

    op.drop_table("actuator_states")
