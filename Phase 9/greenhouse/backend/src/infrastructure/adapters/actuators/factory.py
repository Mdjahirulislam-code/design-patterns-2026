"""Composition of the decorated actuator port (Phase 9).

This is the one place that knows the wrappers and their order:

    LoggingActuatorDecorator -> MaxRunTimeActuatorDecorator -> SimulationActuatorAdapter

Logging is outermost so that an attempt blocked by max-run-time is still
written to the execution log. Callers only receive an ActuatorPort.
"""

from collections.abc import Callable
from datetime import datetime, timedelta

from domain.actuators.policies import MAX_RUN_TIME
from domain.actuators.ports import ActuatorPort
from infrastructure.adapters.actuators.logging_decorator import (
    ExecutionLogWriter,
    LoggingActuatorDecorator,
)
from infrastructure.adapters.actuators.max_runtime_decorator import (
    ActuatorStateReader,
    MaxRunTimeActuatorDecorator,
)
from infrastructure.adapters.actuators.simulation import SimulationActuatorAdapter

# One simulation adapter for the whole process (it only remembers commands in memory).
_simulation = SimulationActuatorAdapter()


def build_actuator_port(
    executions: ExecutionLogWriter,
    states: ActuatorStateReader,
    clock: Callable[[], datetime] | None = None,
    max_run_time: timedelta = MAX_RUN_TIME,
    adapter: ActuatorPort | None = None,
) -> ActuatorPort:
    core = adapter or _simulation
    guarded = MaxRunTimeActuatorDecorator(core, states, clock=clock, max_run_time=max_run_time)
    return LoggingActuatorDecorator(guarded, executions)
