"""locations and zones

Revision ID: 004
Revises: 003
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "004"
down_revision: str | None = "003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    op.create_table(
        "locations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )


    op.create_table(
        "zones",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column(
            "location_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=128),
            nullable=False,
        ),
        sa.Column(
            "moisture_threshold_low",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "moisture_threshold_high",
            sa.Float(),
            nullable=False,
        ),
        sa.Column(
            "schedule",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["location_id"],
            ["locations.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )


    op.create_index(
        "ix_zones_location_id",
        "zones",
        ["location_id"],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_zones_location_id",
        table_name="zones",
    )

    op.drop_table("zones")

    op.drop_table("locations")