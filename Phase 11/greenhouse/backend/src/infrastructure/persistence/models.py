from datetime import datetime
from uuid import UUID

from decimal import Decimal

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text
)

from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from infrastructure.persistence.base import Base


class DeviceRow(Base):

    __tablename__ = "devices"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    device_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="sensor"
    )

    device_family: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default="simulation"
    )

    display_name: Mapped[str | None] = mapped_column(
        String(128)
    )

    default_config: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )


    # Phase 4 fields
    zone_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "zones.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    location_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "locations.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )


    # Phase 5 fields: source of truth for the sampler
    sampling_interval_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        server_default=text("300")
    )

    tracking_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        server_default=text("true")
    )


    zone = relationship(
        "ZoneRow"
    )

    location = relationship(
        "LocationRow"
    )


    __table_args__ = (
        Index(
            "ix_devices_role",
            "role"
        ),
        Index(
            "ix_devices_family",
            "device_family"
        ),
        Index(
            "ix_devices_zone_id",
            "zone_id"
        ),
    )



class LocationRow(Base):

    __tablename__ = "locations"


    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False
    )


    zones = relationship(
        "ZoneRow",
        cascade="all, delete-orphan"
    )



class ZoneRow(Base):

    __tablename__ = "zones"


    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    location_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "locations.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False
    )

    moisture_threshold_low: Mapped[float] = mapped_column(
        nullable=False
    )

    moisture_threshold_high: Mapped[float] = mapped_column(
        nullable=False
    )

    schedule: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )


    location = relationship(
        "LocationRow",
        back_populates="zones"
    )



class ReadingRow(Base):
    """Phase 5: one stored sensor reading. Rows are only appended."""

    __tablename__ = "sensor_readings"


    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    device_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "devices.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    value: Mapped[Decimal] = mapped_column(
        Numeric(14, 4),
        nullable=False
    )

    unit: Mapped[str] = mapped_column(
        String(32),
        nullable=False
    )

    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False
    )

    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )




# Supports "latest reading per device" and later charts.
Index(
    "ix_sensor_readings_device_recorded",
    ReadingRow.device_id,
    ReadingRow.recorded_at.desc()
)




class AutomationRuleRow(Base):
    """Phase 6: the active automation strategy of one location."""

    __tablename__ = "automation_rules"


    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    location_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "locations.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    strategy_key: Mapped[str] = mapped_column(
        String(32),
        nullable=False
    )

    # reserved for strategy settings (for example margins); not used yet
    parameters: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )


    __table_args__ = (
        # one active strategy per location
        UniqueConstraint(
            "location_id",
            name="uq_automation_rules_location_id"
        ),
    )




class ActuatorStateRow(Base):
    """Phase 8: the persisted lifecycle state of one actuator."""

    __tablename__ = "actuator_states"


    device_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "devices.id",
            ondelete="CASCADE"
        ),
        primary_key=True
    )

    # off | idle | running | error | maintenance
    state: Mapped[str] = mapped_column(
        String(32),
        nullable=False
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )




class ActuatorExecutionLogRow(Base):
    """Phase 9: one attempt to send a command to an actuator. Rows are only appended."""

    __tablename__ = "actuator_execution_log"


    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    device_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "devices.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False
    )

    # list of policy names, for example ["maxRunTime", "logging"]
    policy_applied: Mapped[list] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'[]'::jsonb")
    )

    message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )



# Newest executions first (dashboard list) and newest per device.
Index(
    "ix_actuator_execution_log_created_at",
    ActuatorExecutionLogRow.created_at.desc()
)

Index(
    "ix_actuator_execution_log_device_created",
    ActuatorExecutionLogRow.device_id,
    ActuatorExecutionLogRow.created_at.desc()
)




class CommandLogRow(Base):
    """Phase 10: one operator command (success, failed or rejected). Append only."""

    __tablename__ = "command_log"


    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    command_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )

    device_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "devices.id",
            ondelete="CASCADE"
        ),
        nullable=False
    )

    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        server_default=text("'{}'::jsonb")
    )

    # success | failed | rejected
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False
    )

    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )



# Newest commands first (history list).
Index(
    "ix_command_log_created_at",
    CommandLogRow.created_at.desc()
)




class AlertRow(Base):
    """Phase 11: an alert stored by AlertPersistenceSubscriber.

    All three foreign keys are nullable and ON DELETE SET NULL: an alert from an
    unassigned device keeps location_id and zone_id null, and deleting a
    location, zone or device keeps its alerts.
    """

    __tablename__ = "alerts"


    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )

    location_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "locations.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    zone_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "zones.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    device_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "devices.id",
            ondelete="SET NULL"
        ),
        nullable=True
    )

    # info | warning | critical
    severity: Mapped[str] = mapped_column(
        String(16),
        nullable=False
    )

    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    # threshold.crossed | command.failed | state.changed
    event_type: Mapped[str] = mapped_column(
        String(64),
        nullable=False
    )

    # active | resolved
    status: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
        server_default=text("'active'")
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )

    acknowledged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )



# Newest alerts first, and the usual filters.
Index(
    "ix_alerts_status_created",
    AlertRow.status,
    AlertRow.created_at.desc()
)

Index(
    "ix_alerts_zone_created",
    AlertRow.zone_id,
    AlertRow.created_at.desc()
)

Index(
    "ix_alerts_location_created",
    AlertRow.location_id,
    AlertRow.created_at.desc()
)
