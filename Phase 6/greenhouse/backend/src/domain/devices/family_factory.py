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
    # Phase 5: protocol "simulation" selects the in-process generator adapter.
    protocol="simulation"
    def create_device_set(self):
        sensors=[
            MoistureSensorCreator().create_sensor(),
            LightSensorCreator().create_sensor(),
        ]
        return [
            *[Device(None,s.device_type,"sensor",self.family_key,s.display_name,{**s.default_config,"protocol":self.protocol}) for s in sensors],
            Device(None,"water_pump","actuator",self.family_key,"Sim irrigation pump",{"protocol":self.protocol}),
            Device(None,"grow_light","actuator",self.family_key,"Sim grow light",{"protocol":self.protocol}),
        ]

class EdgeHardwareFactory(DeviceFamilyFactory):
    family_key="edge"
    # Phase 5: the edge kit is the real-device (ESP32) path and talks MQTT.
    protocol="mqtt"
    def create_device_set(self):
        sensors=[
            MoistureSensorCreator().create_sensor(),
            LightSensorCreator().create_sensor(),
        ]
        return [
            *[Device(None,s.device_type,"sensor",self.family_key,"Edge "+s.display_name,{**s.default_config,"protocol":self.protocol}) for s in sensors],
            Device(None,"water_pump","actuator",self.family_key,"Edge irrigation pump",{"protocol":self.protocol}),
            Device(None,"grow_light","actuator",self.family_key,"Edge grow light",{"protocol":self.protocol}),
        ]

def get_family_factory(family:str):
    if family=="simulation": return SimulationDeviceFactory()
    if family=="edge": return EdgeHardwareFactory()
    raise ValueError("Unknown device family")
