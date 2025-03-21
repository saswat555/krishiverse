# simulated_esp.py

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn

# Create the FastAPI app for the simulated ESP device.
simulated_esp_app = FastAPI(title="Simulated ESP32 Device")

# Allow CORS for all origins (adjust as needed).
simulated_esp_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@simulated_esp_app.get("/discovery")
async def discovery():
    """
    Simulate the discovery endpoint.
    Returns basic device information.
    """
    return {
        "device_id": "dummy_device",
        "name": "Simulated ESP Device",
        "type": "DOSING_MONITOR_UNIT",
        "version": "2.1.0",
        "status": "online",
        "ip": "127.0.0.1"  # Simulated IP address
    }

@simulated_esp_app.post("/pump")
async def pump(request: Request):
    """
    Simulate activating a pump.
    Expects JSON with "pump" and "amount".
    Returns a success message.
    """
    data = await request.json()
    pump = data.get("pump")
    amount = data.get("amount")
    if pump is None or amount is None:
        raise HTTPException(status_code=400, detail="Missing pump or amount")
    return {
        "message": "Pump started",  # Some tests check for this exact message.
        "pump": pump,
        "dose_ml": amount,
        "timestamp": datetime.utcnow().isoformat()
    }

@simulated_esp_app.get("/monitor")
async def monitor():
    """
    Simulate returning sensor readings.
    """
    return {
        "device_id": "dummy_device",
        "type": "DOSING_MONITOR_UNIT",
        "version": "2.1.0",
        "wifi_connected": True,
        "pH": 6.8,
        "TDS": 750
    }

@simulated_esp_app.post("/dose_monitor")
async def dose_monitor(request: Request):
    """
    Simulate a combined dosing and monitoring endpoint.
    Behaves similar to /pump but returns a different message.
    """
    data = await request.json()
    pump = data.get("pump")
    amount = data.get("amount")
    if pump is None or amount is None:
        raise HTTPException(status_code=400, detail="Missing pump or amount")
    return {
        "message": "Combined started",
        "pump": pump,
        "dose_ml": amount,
        "timestamp": datetime.utcnow().isoformat()
    }

@simulated_esp_app.post("/pump_calibration")
async def pump_calibration(request: Request):
    """
    Simulate pump calibration endpoint.
    Expects a JSON with a "command" key.
    """
    data = await request.json()
    command = data.get("command")
    if command == "stop":
        return {"message": "All pumps off"}
    elif command == "start":
        return {"message": "All pumps on"}
    else:
        raise HTTPException(status_code=400, detail="Invalid command")

# Add a main section to run the app on port 8080.
if __name__ == "__main__":
    uvicorn.run("simulated_esp:simulated_esp_app", host="0.0.0.0", port=8080, reload=True)
