from application.devices.dto import DeviceDto
from domain.devices.entity import Device

def device_to_dto(device:Device):
    if device.id is None:
        raise RuntimeError("Unpersisted device")
    return DeviceDto(id=device.id,device_type=device.device_type,role=device.role,device_family=device.device_family,display_name=device.display_name,default_config=device.default_config)
