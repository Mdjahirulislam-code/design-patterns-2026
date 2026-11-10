from application.devices.dto import DeviceDto
from domain.actuators.state import INITIAL_STATE, allowed_commands_for
from domain.devices.entity import Device

def device_to_dto(device:Device, state: str | None = None):
    if device.id is None:
        raise RuntimeError("Unpersisted device")

    # Phase 8: lifecycle fields for actuators; allowed commands come from the domain
    if device.role == "actuator":
        state = state or INITIAL_STATE
        commands = allowed_commands_for(state)
    else:
        state = None
        commands = []

    return DeviceDto(
        id=device.id,
        device_type=device.device_type,
        role=device.role,
        device_family=device.device_family,
        display_name=device.display_name,
        default_config=device.default_config,
        zone_id=device.zone_id,
        sampling_interval_seconds=device.sampling_interval_seconds,
        tracking_enabled=device.tracking_enabled,
        state=state,
        allowed_commands=commands,
    )
