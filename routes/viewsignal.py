# routes/viewsignal.py

from fastapi import APIRouter, Depends
from fastapi import FastAPI
import json

router = APIRouter()

@router.get("/viewsignal")
def view_signal(app: FastAPI = Depends()):
    # Retrieve the last signal from Redis
    last_signal = app.state.redis.get('last_signal')
    if last_signal:
        return {"signal": json.loads(last_signal)}
    else:
        return {"signal": "No signal"}
