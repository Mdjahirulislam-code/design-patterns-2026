"""Names and limits of the actuator policies (Phase 9 — Decorator)."""

from datetime import timedelta

# Names stored in actuator_execution_log.policy_applied
POLICY_LOGGING = "logging"
POLICY_MAX_RUN_TIME = "maxRunTime"

# An actuator that has been in the state "running" this long is blocked.
MAX_RUN_TIME = timedelta(minutes=30)
MAX_RUN_TIME_MESSAGE = "Max run time exceeded"
