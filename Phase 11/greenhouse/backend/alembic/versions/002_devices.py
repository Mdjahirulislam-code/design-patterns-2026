"""devices

Revision ID: 002
Revises: 001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "devices",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("device_type", sa.String(length=64), nullable=False),
        sa.Column("role", sa.String(length=32), server_default="sensor", nullable=False),
        sa.Column("display_name", sa.String(length=128), nullable=True),
        sa.Column(
            "default_config",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'{}'::jsonb"),
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
    op.create_index("ix_devices_role", "devices", ["role"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_devices_role", table_name="devices")
    op.drop_table("devices")
