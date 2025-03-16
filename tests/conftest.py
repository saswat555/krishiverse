# conftest.py
import os
import pytest
import asyncio
from datetime import datetime, timezone
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import Base, engine
from app.dependencies import get_current_user
from app.schemas import DeviceType

# --- Recreate the Database Schema ---
@pytest.fixture(scope="session", autouse=True)
def recreate_database():
    async def _recreate():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
    asyncio.get_event_loop().run_until_complete(_recreate())

# --- Override Authentication Dependency ---
@pytest.fixture(autouse=True)
def override_get_current_user():
    # Create a dummy user object to be used by tests.
    dummy_user = type("DummyUser", (), {
        "id": 1,
        "email": "dummy@example.com",
        "hashed_password": "dummy",
        "role": "user",
        "created_at": datetime.now(timezone.utc)
    })
    app.dependency_overrides[get_current_user] = lambda: dummy_user
    yield
    # Clean up override after tests.
    app.dependency_overrides[get_current_user] = None

# --- Fixtures for Device Data ---
@pytest.fixture
def test_dosing_device_fixture():
    return {
        "name": "HighPrecision Dosing Unit",
        "type": DeviceType.DOSING_UNIT,
        "mac_id": "MAC_TEST_DOSING",
        "http_endpoint": "http://localhost/simulated_esp",  # full URL for discovery calls
        "location_description": "Greenhouse #12, East Wing",
        "pump_configurations": [
            {"pump_number": 1, "chemical_name": "Nutrient A", "chemical_description": "Core nutrient blend"},
            {"pump_number": 2, "chemical_name": "Nutrient B", "chemical_description": "Supplemental nutrient blend"},
            {"pump_number": 3, "chemical_name": "Nutrient C", "chemical_description": "pH balancer"},
            {"pump_number": 4, "chemical_name": "Nutrient D", "chemical_description": "Tertiary trace elements"}
        ]
    }

@pytest.fixture
def test_sensor_device_fixture():
    return {
        "name": "HighAccuracy pH/TDS Sensor",
        "type": DeviceType.PH_TDS_SENSOR,
        "mac_id": "MAC_TEST_SENSOR",
        "http_endpoint": "http://localhost/simulated_esp",  # full URL for discovery calls
        "location_description": "Row 5, Reservoir Edge",
        "sensor_parameters": {"ph_calibration": "7.01", "tds_calibration": "600"}
    }

# --- Async Client Fixture ---
@pytest.fixture
async def async_client():
    transport = ASGITransport(app)
    client = AsyncClient(transport=transport, base_url="http://test", follow_redirects=True)
    yield client
    await client.aclose()
