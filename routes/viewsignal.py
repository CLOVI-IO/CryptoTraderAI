from fastapi import APIRouter
import os

router = APIRouter()

# Global variable to store the last signal
# Note: Consider using a shared state (like a database or in-memory data store) if this app needs to scale
last_signal = None

@router.get("/viewsignal")
def view_signal():
    global last_signal
    if last_signal:
        return {"signal": last_signal}
    else:
        return {"signal": "No signal"}
