class ConfigurationError(ValueError):
    pass


class LocationNotFoundError(LookupError):
    """No location with that id (HTTP 404)."""
