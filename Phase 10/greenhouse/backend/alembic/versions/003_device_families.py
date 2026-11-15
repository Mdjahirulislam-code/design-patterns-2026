"""add device families and actuators

Revision ID: 003
Revises: 002
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    # Add device family column
    op.add_column(
        "devices",
        sa.Column(
            "device_family",
            sa.String(length=64),
            server_default="simulation",
            nullable=False,
        ),
    )


    # Add actuator support
    op.execute(
        """
        UPDATE devices
        SET role = 'sensor'
        WHERE role IS NULL
        """
    )


    op.create_index(
        "ix_devices_device_family",
        "devices",
        ["device_family"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_devices_device_family",
        table_name="devices",
    )

    op.drop_column(
        "devices",
        "device_family",
    )