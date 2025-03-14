from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
from datetime import datetime, UTC

from app.schemas import (
    DosingDeviceCreate,
    SensorDeviceCreate,
    DeviceResponse,
    DeviceType,
    DosingOperation
)
from app.models import Device
from app.core.database import get_db
# UPDATED: Removed old DeviceDiscoveryService imports and use DeviceController instead.
from app.services.device_controller import DeviceController
from app.services.llm import getSensorData

router = APIRouter()

@router.get("/discover", summary="Check if a device is connected")
async def check_device_connection(
    ip: str = Query(..., description="IP address of the device to validate")
):
    """
    Validate connectivity of a device at a specific IP address using the unified device controller.
    """
    controller = DeviceController(device_ip=ip)
    device_info = await controller.discover()
    if device_info is None:
        raise HTTPException(status_code=404, detail="No device found at the provided IP")
    
    # Map device_info keys to a formatted response.
    formatted_device = {
        "id": device_info.get("device_id"),
        "name": device_info.get("device_id"),  # Adjust this if the device sends a proper name.
        "type": device_info.get("type"),
        "status": device_info.get("status"),
        "version": device_info.get("version"),
        "ip": device_info.get("ip")
    }
    return formatted_device

@router.post("/dosing", response_model=DeviceResponse)
async def create_dosing_device(
    device: DosingDeviceCreate,
    session: AsyncSession = Depends(get_db)
):
    """Create a new dosing device with an HTTP endpoint."""
    try:
        new_device = Device(
            name=device.name,
            type=DeviceType.DOSING_UNIT,
            http_endpoint=device.http_endpoint,
            location_description=device.location_description,
            pump_configurations=[pump.model_dump() for pump in device.pump_configurations],
            is_active=True
        )
        session.add(new_device)
        await session.commit()
        await session.refresh(new_device)
        return new_device
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating dosing device: {str(e)}"
        )

@router.post("/sensor", response_model=DeviceResponse)
async def create_sensor_device(
    device: SensorDeviceCreate,
    session: AsyncSession = Depends(get_db)
):
    """Register a new sensor device with an HTTP endpoint."""
    try:
        new_device = Device(
            name=device.name,
            type=device.type,
            http_endpoint=device.http_endpoint,
            location_description=device.location_description,
            sensor_parameters=device.sensor_parameters,
            is_active=True
        )
        session.add(new_device)
        await session.commit()
        await session.refresh(new_device)
        return new_device
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Error creating sensor device: {str(e)}"
        )

@router.get("", response_model=List[DeviceResponse], summary="List all devices")
async def list_devices(db: AsyncSession = Depends(get_db)):
    """Retrieve all registered devices."""
    result = await db.execute(select(Device))
    return result.scalars().all()

@router.get("/{device_id}", response_model=DeviceResponse, summary="Get device details")
async def get_device(device_id: int, db: AsyncSession = Depends(get_db)):
    """Get details of a specific device."""
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.get("/sensoreading/{device_id}")
async def getSensorReadings(device_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get details of a specific device and fetch its sensor readings.
    """
    result = await db.execute(select(Device).where(Device.id == device_id))
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    sensor_data = await getSensorData(device)
    
    return sensor_data
