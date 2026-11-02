"""Actuator lifecycle errors. The API maps them to HTTP status codes."""


class IllegalTransitionError(ValueError):
    """The current state does not allow this command or target (HTTP 409).

    Raised before anything is saved, so the stored state stays as it was.
    """

    def __init__(self, current: str, attempted: str, allowed_commands: list[str]) -> None:
        self.current = current
        self.attempted = attempted
        self.allowed_commands = list(allowed_commands)
        allowed = ", ".join(allowed_commands) if allowed_commands else "none"
        super().__init__(
            f"Cannot {attempted} while the actuator is {current}. Allowed commands: {allowed}."
        )


class UnknownActuatorStateError(ValueError):
    """The state name is not one of off, idle, running, error, maintenance (HTTP 400)."""


class ActuatorNotFoundError(LookupError):
    """No actuator with that id: the device is missing or is not an actuator (HTTP 404)."""
