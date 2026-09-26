from abc import ABC, abstractmethod
from domain.devices.entity import Device
from domain.sensors.creators import MoistureSensorCreator, LightSensorCreator

class DeviceFamilyFactory(ABC):
    @property
    @abstractmethod
    def family_key(self)->str: ...

    @abstractmethod
    def create_device_set(self)->list[Device]: ...

class SimulationDeviceFactory(DeviceFamilyFactory):
    family_key="simulation"
    def create_device_set(self):
        sensors=[
            MoistureSensorCreator().create_sensor(),
            LightSensorCreator().create_sensor(),
        ]
        return [
            *[Device(None,s.device_type,"sensor",self.family_key,s.display_name,{**s.default_config,"protocol":"sim"}) for s in sensors],
            Device(None,"water_pump","actuator",self.family_key,"Sim irrigation pump",{"protocol":"sim"}),
            Device(None,"grow_light","actuator",self.family_key,"Sim grow light",{"protocol":"sim"}),
        ]

class EdgeHardwareFactory(DeviceFamilyFactory):
    family_key="edge"
    def create_device_set(self):
        sensors=[
            MoistureSensorCreator().create_sensor(),
            LightSensorCreator().create_sensor(),
        ]
        return [
            *[Device(None,s.device_type,"sensor",self.family_key,"Edge "+s.display_name,{**s.default_config,"protocol":"gpio-stub"}) for s in sensors],
            Device(None,"water_pump","actuator",self.family_key,"Edge irrigation pump",{"protocol":"gpio-stub"}),
            Device(None,"grow_light","actuator",self.family_key,"Edge grow light",{"protocol":"gpio-stub"}),
        ]

def get_family_factory(family:str):
    if family=="simulation": return SimulationDeviceFactory()
    if family=="edge": return EdgeHardwareFactory()
    raise ValueError("Unknown device family")
