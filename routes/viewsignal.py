from fastapi import APIRouter
from main import app

router = APIRouter()

class SignalResponse:
    def __init__(self, signal_id: int, signal_name: str):
        self.signal_id = signal_id
        self.signal_name = signal_name

@router.get("/viewsignal", response_model=SignalResponse)
def view_signal():
    last_signal = app.state.last_signal  # Access the global last_signal variable
    signal = SignalResponse(signal_id=1, signal_name=last_signal)
    return signal
