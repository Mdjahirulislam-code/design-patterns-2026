"""Actuator lifecycle and policy errors. The API maps them to HTTP status codes."""

from domain.actuators.policies import MAX_RUN_TIME_MESSAGE, POLICY_MAX_RUN_TIME


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


# ---------------- Phase 9: policy decorators ----------------

class ActuatorPolicyError(Exception):
    """A policy decorator refused the command (HTTP 409).

    The wrapped adapter was not called. `policy` is the name that goes into
    actuator_execution_log.policy_applied.
    """

    policy: str = "policy"


class MaxRunTimeExceededError(ActuatorPolicyError):
    """The actuator has been running for the maximum run time or longer."""

    policy = POLICY_MAX_RUN_TIME

    def __init__(self, message: str = MAX_RUN_TIME_MESSAGE) -> None:
        super().__init__(message)
