from fastapi import APIRouter, Depends
from fastapi import FastAPI

router = APIRouter()

@router.get("/viewsignal")
def view_signal(app: FastAPI = Depends()):
    # Retrieve the last signal from application state
    last_signal = app.state.last_signal
    if last_signal:
        return {"signal": last_signal}
    else:
        return {"signal": "No signal"}
