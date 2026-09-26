from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String,
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