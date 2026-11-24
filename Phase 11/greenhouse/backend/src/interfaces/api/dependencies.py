"""FastAPI dependencies that build application services for a request.

Tests replace these with in-memory fakes through `app.dependency_overrides`.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from application.actuators.executions import ActuatorExecutionService
from application.actuators.service import ActuatorStateService
from application.alerts.service import AlertQueryService
from application.automation.service import AutomationService
from application.commands.service import CommandService
from application.devices.queries import DeviceQueryService
from application.overview.facade import LocationOverviewFacade
from application.readings.sampling import SamplingService
from application.readings.service import ReadingIngest
from infrastructure.adapters.actuators.factory import build_actuator_port
from infrastructure.db import get_session
from infrastructure.events import build_event_bus
from infrastructure.persistence.alert_repository import AlertRepository
from infrastructure.persistence.actuator_state_repository import ActuatorStateRepository
from infrastructure.persistence.automation_repository import (
    AutomationLocationRepository,
    AutomationRuleRepository,
)
from infrastructure.persistence.command_log_repository import CommandLogRepository
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.persistence.execution_log_repository import ExecutionLogRepository
from infrastructure.persistence.location_repository import LocationRepository
from infrastructure.persistence.reading_repository import ReadingRepository
from infrastructure.sampler_runner import build_reading_ingest


def get_reading_ingest(session: Session = Depends(get_session)) -> ReadingIngest:
    return build_reading_ingest(session)


def get_sampling_service(session: Session = Depends(get_session)) -> SamplingService:
    return SamplingService(DeviceRepository(session))


def build_automation_service(session: Session) -> AutomationService:
    return AutomationService(
        locations=AutomationLocationRepository(session),
        rules=AutomationRuleRepository(session),
        sensors=DeviceRepository(session),
        readings=ReadingRepository(session),
    )


def get_automation_service(session: Session = Depends(get_session)) -> AutomationService:
    return build_automation_service(session)


# Phase 7: the overview route gets ONLY this facade. The repositories are wired
# here, so the handler never imports them.
def get_overview_facade(session: Session = Depends(get_session)) -> LocationOverviewFacade:
    return LocationOverviewFacade(
        locations=LocationRepository(session),
        devices=DeviceRepository(session),
        readings=ReadingRepository(session),
        rules=AutomationRuleRepository(session),
        automation=build_automation_service(session),
        states=ActuatorStateRepository(session),
    )


# Phase 8: device read models with actuator state, and state transitions
def get_device_queries(session: Session = Depends(get_session)) -> DeviceQueryService:
    return DeviceQueryService(DeviceRepository(session), ActuatorStateRepository(session))


def get_actuator_state_service(
    session: Session = Depends(get_session),
) -> ActuatorStateService:
    return ActuatorStateService(
        DeviceRepository(session),
        ActuatorStateRepository(session),
        events=build_event_bus(session),
    )


# Phase 9: the service receives one ActuatorPort. The decorator chain
# (logging -> max run time -> simulation adapter) is built in the factory.
def get_execution_service(
    session: Session = Depends(get_session),
) -> ActuatorExecutionService:
    executions = ExecutionLogRepository(session)
    port = build_actuator_port(
        executions=executions,
        states=ActuatorStateRepository(session),
    )
    return ActuatorExecutionService(DeviceRepository(session), port, executions)


# Phase 10: commands run through the same decorated port as Phase 9.
def get_command_service(
    session: Session = Depends(get_session),
) -> CommandService:
    states = ActuatorStateRepository(session)
    port = build_actuator_port(
        executions=ExecutionLogRepository(session),
        states=states,
    )
    return CommandService(
        devices=DeviceRepository(session),
        states=states,
        port=port,
        log=CommandLogRepository(session),
        events=build_event_bus(session),
    )


# Phase 11: the alert list
def get_alert_service(session: Session = Depends(get_session)) -> AlertQueryService:
    return AlertQueryService(AlertRepository(session))
