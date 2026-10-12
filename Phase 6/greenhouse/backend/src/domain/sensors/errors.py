"""Domain errors of the reading flow. The API layer maps them to HTTP codes."""


class DeviceNotFoundError(Exception):
    """No device with that id (HTTP 404)."""


class SensorReadError(Exception):
    """An adapter could not produce or translate a reading (HTTP 400)."""


class InvalidSamplingError(Exception):
    """Sampling settings break a domain rule, e.g. interval below 5 s (HTTP 400)."""
