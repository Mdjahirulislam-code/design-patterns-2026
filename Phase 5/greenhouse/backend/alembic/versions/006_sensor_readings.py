"""sensor_readings

Adds the sensor_readings table and the sampling columns on devices.

Revision ID: 006
Revises: 005
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "006"
down_revision: str | None = "005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:

    # --- sampling columns on devices ---------------------------------

    op.add_column(
        "devices",
        sa.Column(
            "sampling_interval_seconds",
            sa.Integer(),
            server_default=sa.text("300"),
            nullable=False,
        ),
    )

    op.add_column(
        "devices",
        sa.Column(
            "tracking_enabled",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
    )

    # Backfill (added by hand, autogenerate does not emit data changes):
    # copy the interval from default_config when it is a number there.
    # Other rows keep the server default 300. Minimum allowed is 5.
    op.execute(
        """
        UPDATE devices
        SET sampling_interval_seconds = GREATEST(
            LEAST((default_config ->> 'sampling_interval_seconds')::numeric, 2147483647)::integer,
            5
        )
        WHERE jsonb_typeof(default_config -> 'sampling_interval_seconds') = 'number'
        """
    )

    # Phase 5 selects the adapter by default_config.protocol = simulation | mqtt.
    # Phase 3 rows used "sim" and "gpio-stub", Phase 2 sensors had no protocol.
    op.execute(
        """
        UPDATE devices
        SET default_config = jsonb_set(default_config, '{protocol}', '"simulation"')
        WHERE default_config ->> 'protocol' = 'sim'
           OR (default_config ->> 'protocol' IS NULL AND device_family = 'simulation')
        """
    )

    op.execute(
        """
        UPDATE devices
        SET default_config = jsonb_set(default_config, '{protocol}', '"mqtt"')
        WHERE default_config ->> 'protocol' = 'gpio-stub'
           OR (default_config ->> 'protocol' IS NULL AND device_family = 'edge')
        """
    )

    # --- sensor_readings ---------------------------------------------

    op.create_table(
        "sensor_readings",
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
            "value",
            sa.Numeric(precision=14, scale=4),
            nullable=False,
        ),
        sa.Column(
            "unit",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=32),
            nullable=False,
        ),
        sa.Column(
            "recorded_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["device_id"],
            ["devices.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # latest reading per device + later charts
    op.create_index(
        "ix_sensor_readings_device_recorded",
        "sensor_readings",
        ["device_id", sa.text("recorded_at DESC")],
        unique=False,
    )


def downgrade() -> None:

    op.drop_index(
        "ix_sensor_readings_device_recorded",
        table_name="sensor_readings",
    )

    op.drop_table("sensor_readings")

    # Protocol names are left as they are; the old values still map in the code.
    op.drop_column("devices", "tracking_enabled")
    op.drop_column("devices", "sampling_interval_seconds")
