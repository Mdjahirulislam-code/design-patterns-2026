from .entity import LocationConfig, Zone
from .errors import ConfigurationError

class LocationConfigBuilder:
    def __init__(self):
        self.name=""
        self.zones=[]

    def with_location_name(self,name):
        self.name=name
        return self

    def add_zone(self,name,moisture_threshold_low,moisture_threshold_high,schedule=None):
        self.zones.append(Zone(name,moisture_threshold_low,moisture_threshold_high,schedule or {}))
        return self

    def build(self):
        if not self.name.strip(): raise ConfigurationError("location name required")
        if not self.zones: raise ConfigurationError("at least one zone required")
        for z in self.zones:
            if not z.name.strip(): raise ConfigurationError("zone name required")
            if not (0 <= z.low if False else True): pass
            if z.moisture_threshold_low < 0 or z.moisture_threshold_high > 1:
                raise ConfigurationError("thresholds must be 0-1")
            if z.moisture_threshold_low >= z.moisture_threshold_high:
                raise ConfigurationError("low must be lower than high")
        return LocationConfig(self.name,self.zones)
