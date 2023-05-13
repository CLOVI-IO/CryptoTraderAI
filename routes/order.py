from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

router = APIRouter()

# Global variable to store the last signal
last_signal = None

# Risk management settings
risk_reward_ratio = float(os.getenv("RISK_REWARD_RATIO"))
risk_percentage = float(os.getenv("RISK_PERCENTAGE"))

class Signal(BaseModel):
    symbol: str
    close: float
    volume: float
    interval: str
    strategy: str

@router.post("/order")
def create_order(signal: Signal):
    global last_signal
    last_signal = signal

    # Calculate take-profit and stop-loss levels
    take_profit = calculate_take_profit(last_signal.close)
    stop_loss = calculate_stop_loss(last_signal.close)

    # Format JSON output
    formatted_output = {
        "symbol": last_signal.symbol,
        "close": last_signal.close,
        "volume": last_signal.volume,
        "interval": last_signal.interval,
        "strategy": last_signal.strategy,
        "take_profit": take_profit,
        "stop_loss": stop_loss,
        # Add other tags for the Crypto.com exchange API
        "type": "LIMIT",
        "side": "BUY",
        "price": last_signal.close,
        "quantity": last_signal.volume
    }

    return formatted_output

def calculate_take_profit(entry_price):
    take_profit = entry_price + (entry_price * risk_reward_ratio)
    return round(take_profit, 2)

def calculate_stop_loss(entry_price):
    stop_loss = entry_price - (entry_price * risk_percentage)
    return round(stop_loss, 2)
