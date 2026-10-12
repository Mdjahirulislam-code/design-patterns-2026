from dataclasses import dataclass
from uuid import UUID

# Phase 5: the adapter is selected from default_config.protocol.
PROTOCOL_SIMULATION = "simulation"
PROTOCOL_MQTT = "mqtt"

# Phase 3 stored "sim" / "gpio-stub". Migration 006 rewrites those rows, the
# aliases below only keep a not-yet-migrated row readable.
_PROTOCOL_ALIASES = {
    "sim": PROTOCOL_SIMULATION,
    "gpio-stub": PROTOCOL_MQTT,
}

DEFAULT_SAMPLING_INTERVAL_SECONDS = 300
MIN_SAMPLING_INTERVAL_SECONDS = 5


@dataclass(frozen=True)
class Device:
    id: UUID | None
    device_type: str
    role: str
    device_family: str
    display_name: str
    default_config: dict
    # Phase 4
    zone_id: UUID | None = None
    # Phase 5: these columns are the source of truth for sampling, not default_config.
    sampling_interval_seconds: int = DEFAULT_SAMPLING_INTERVAL_SECONDS
    tracking_enabled: bool = True

    @property
    def protocol(self) -> str:
        """Normalized default_config.protocol: "simulation" or "mqtt"."""
        raw = str(self.default_config.get("protocol") or "").strip().lower()
        if not raw:
            # Phase 2 sensors were saved without a protocol.
            return PROTOCOL_MQTT if self.device_family == "edge" else PROTOCOL_SIMULATION
        return _PROTOCOL_ALIASES.get(raw, raw)

    @property
    def uses_vendor_stub(self) -> bool:
        """Documented flag that selects the vendor stub adapter (see docs/patterns/adapter.md)."""
        return self.default_config.get("vendor_stub") is True
