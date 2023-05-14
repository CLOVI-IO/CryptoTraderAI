from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
from shared_state import state  # Import the shared state

# Load environment variables
load_dotenv()

router = APIRouter()

risk_reward_ratio = float(os.getenv("RISK_REWARD_RATIO", "0"))
risk_percentage = float(os.getenv("RISK_PERCENTAGE", "0"))


class Signal(BaseModel):
    symbol: str
    close: float
    volume: float
    interval: str
    strategy: str


@router.post("/order")
def create_order(signal: Signal):
    state["last_signal"] = signal.dict()

    if state["last_signal"] is None:
        raise HTTPException(status_code=400, detail="No signal available")

    formatted_output = format_order(state["last_signal"])
    return formatted_output


@router.get("/order")
def get_order():
    if state["last_signal"] is None:
        raise HTTPException(status_code=400, detail="No signal available")

    formatted_output = format_order(state["last_signal"])
    return formatted_output


def calculate_take_profit(entry_price):
    take_profit = entry_price + (entry_price * risk_reward_ratio)
    return round(take_profit, 2)


def calculate_stop_loss(entry_price):
    stop_loss = entry_price - (entry_price * risk_percentage)
    return round(stop_loss, 2)


def format_order(signal):
    # Calculate take-profit and stop-loss levels
    take_profit = calculate_take_profit(signal["close"])
    stop_loss = calculate_stop_loss(signal["close"])

    # Format JSON output
    formatted_output = {
        "symbol": signal["symbol"],
        "close": signal["close"],
        "volume": signal["volume"],
        "interval": signal["interval"],
        "strategy": signal["strategy"],
        "take_profit": take_profit,
        "stop_loss": stop_loss,
        # Add other tags for the Crypto.com exchange API
        "type": "LIMIT",
        "side": "BUY",
        "price": signal["close"],
        "quantity": signal["volume"],
    }

    return formatted_output
