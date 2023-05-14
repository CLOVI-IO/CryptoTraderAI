from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from shared_state import state  # Import the shared state
import traceback  # import traceback module for detailed error logging

router = APIRouter()


class Signal(BaseModel):
    symbol: str
    close: float
    volume: float
    interval: str
    strategy: str


@router.get("/order")
def get_order():
    try:
        # Check if last_signal has been set in the shared state
        if "last_signal" not in state or state["last_signal"] is None:
            raise HTTPException(status_code=400, detail="No signal available")

        # Retrieve the last signal from the shared state
        last_signal = state["last_signal"]

        print(f"Retrieved signal from shared state: {last_signal}")  # Debug print

        # Format JSON output
        formatted_output = {
            "symbol": last_signal.symbol,
            "close": last_signal.close,
            "volume": last_signal.volume,
            "interval": last_signal.interval,
            "strategy": last_signal.strategy,
            # Add other tags for the Crypto.com exchange API
            "type": "LIMIT",
            "side": "BUY",
            "price": last_signal.close,
            "quantity": last_signal.volume,
        }

        print(f"Formatted order: {formatted_output}")  # Debug print

        return formatted_output

    except Exception as e:
        # print the traceback of the error
        print(f"Failed to create order. Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")
