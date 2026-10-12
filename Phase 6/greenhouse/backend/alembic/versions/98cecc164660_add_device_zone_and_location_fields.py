"""add device zone and location fields

Revision ID: 005
Revises: 004
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    op.add_column(
        "devices",
        sa.Column(
            "zone_id",
            postgresql.UUID(as_uuid=True),
            nullable=True
        )
    )

    op.add_column(
        "devices",
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            nullable=True
        )
    )

    op.create_index(
        "ix_devices_zone_id",
        "devices",
        ["zone_id"]
    )

    op.create_foreign_key(
        "fk_devices_zone_id",
        "devices",
        "zones",
        ["zone_id"],
        ["id"],
        ondelete="SET NULL"
    )

    op.create_foreign_key(
        "fk_devices_location_id",
        "devices",
        "locations",
        ["location_id"],
        ["id"],
        ondelete="SET NULL"
    )


def downgrade() -> None:

    op.drop_constraint(
        "fk_devices_location_id",
        "devices",
        type_="foreignkey"
    )

    op.drop_constraint(
        "fk_devices_zone_id",
        "devices",
        type_="foreignkey"
    )

    op.drop_index(
        "ix_devices_zone_id",
        table_name="devices"
    )

    op.drop_column(
        "devices",
        "location_id"
    )

    op.drop_column(
        "devices",
        "zone_id"
    )