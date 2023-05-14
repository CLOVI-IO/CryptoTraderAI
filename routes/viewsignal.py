from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# last_signal = None


@router.get("/viewsignal")
def view_signal():
    try:
        global last_signal
        print(f"Retrieving signal: {last_signal}")
        if last_signal:
            return {"signal": last_signal}
        else:
            return {"signal": "No signal"}
    except Exception as e:
        print(f"Failed to retrieve signal: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An error occurred while retrieving the signal"},
        )
