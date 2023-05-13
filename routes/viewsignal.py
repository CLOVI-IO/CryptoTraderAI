from fastapi import APIRouter
import os

router = APIRouter()
last_signal = None

@router.get("/viewsignal")
def view_signal():
    global last_signal
    if last_signal:
        return {"signal": last_signal}
    else:
        return {"signal": "No signal"}
