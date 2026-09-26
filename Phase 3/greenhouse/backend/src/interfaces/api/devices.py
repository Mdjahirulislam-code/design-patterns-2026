from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from infrastructure.db import get_session
from infrastructure.persistence.device_repository import DeviceRepository
from application.devices.family_service import DeviceFamilyService
from application.devices.mappers import device_to_dto

router=APIRouter(prefix="/api/devices",tags=["devices"])

@router.get("")
def list_devices(family:str|None=None,role:str|None=None,session:Session=Depends(get_session)):
    return [device_to_dto(d) for d in DeviceFamilyService(DeviceRepository(session)).list_devices(device_family=family,role=role)]

@router.post("/provision",status_code=201)
def provision(family:str,session:Session=Depends(get_session)):
    try:
        return [device_to_dto(d) for d in DeviceFamilyService(DeviceRepository(session)).provision_family(family)]
    except ValueError as e:
        raise HTTPException(400,str(e))
