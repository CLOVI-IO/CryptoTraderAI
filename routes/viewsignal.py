# viewsignal.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from shared_state import state  # Import the shared state

router = APIRouter()


@router.get("/viewsignal")
def view_signal():
    try:
        print(f"Retrieving signal: {state['last_signal']}")
        if state["last_signal"]:
            return {"signal": state["last_signal"]}
        else:
            return {"signal": "No signal"}
    except Exception as e:
        print(f"Failed to retrieve signal: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An error occurred while retrieving the signal"},
        )
