"""FastAPI dependencies that build application services for a request.

Tests replace these with in-memory fakes through `app.dependency_overrides`.
"""

from fastapi import Depends
from sqlalchemy.orm import Session

from application.readings.sampling import SamplingService
from application.readings.service import ReadingIngest
from infrastructure.db import get_session
from infrastructure.persistence.device_repository import DeviceRepository
from infrastructure.sampler_runner import build_reading_ingest


def get_reading_ingest(session: Session = Depends(get_session)) -> ReadingIngest:
    return build_reading_ingest(session)


def get_sampling_service(session: Session = Depends(get_session)) -> SamplingService:
    return SamplingService(DeviceRepository(session))
