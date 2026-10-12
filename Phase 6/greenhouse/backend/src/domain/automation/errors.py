"""Automation errors. The API maps them to HTTP status codes."""


class UnknownStrategyError(ValueError):
    """The strategy key is not registered (HTTP 400)."""


class LocationNotFoundError(LookupError):
    """No location with that id (HTTP 404)."""
