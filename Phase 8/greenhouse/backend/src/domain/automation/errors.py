"""Automation errors. The API maps them to HTTP status codes."""

# Phase 7: LocationNotFoundError now lives with the location domain, because
# the overview facade needs it too. It is re-exported here so Phase 6 imports
# keep working.
from domain.locations.errors import LocationNotFoundError

__all__ = ["LocationNotFoundError", "UnknownStrategyError"]


class UnknownStrategyError(ValueError):
    """The strategy key is not registered (HTTP 400)."""
