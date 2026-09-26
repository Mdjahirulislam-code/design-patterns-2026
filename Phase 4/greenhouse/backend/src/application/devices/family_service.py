from domain.devices.family_factory import get_family_factory
class DeviceFamilyService:
    def __init__(self,repo): self.repo=repo
    def provision_family(self,family):
        existing=self.repo.list_devices(device_family=family)
        if existing: return existing
        return self.repo.save_devices(get_family_factory(family).create_device_set())
    def list_devices(self,**filters): return self.repo.list_devices(**filters)
