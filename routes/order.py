from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from shared_state import state  # Import the shared state
import traceback  # import traceback module for detailed error logging
from typing import Optional

# Output json Exemple
# {
#     "symbol": "SOLUSDT",
#     "close": "20.96",
#     "volume": "256.81",
#     "interval": "1",
#     "strategy": "Open Long",
#     "type": "LIMIT",
#     "side": "BUY",
#     "price": "20.96",
#     "quantity": "256.81"
# }


router = APIRouter()


# Define the nested classes for the data model
class Order(BaseModel):
    action: Optional[str]
    contracts: Optional[str]
    price: Optional[str]
    id: Optional[str]
    comment: Optional[str]
    alert_message: Optional[str]


class StrategyInfo(BaseModel):
    position_size: Optional[str]
    order: Order
    market_position: Optional[str]
    market_position_size: Optional[str]
    prev_market_position: Optional[str]
    prev_market_position_size: Optional[str]


class Plots(BaseModel):
    plot_0: Optional[str]
    plot_1: Optional[str]


class CurrentInfo(BaseModel):
    fire_time: Optional[str]
    plots: Plots


class BarInfo(BaseModel):
    open: Optional[str]
    high: Optional[str]
    low: Optional[str]
    close: Optional[str]
    volume: Optional[str]
    time: Optional[str]


class AlertInfo(BaseModel):
    exchange: Optional[str]
    ticker: Optional[str]
    price: Optional[str]
    volume: Optional[str]
    interval: Optional[str]


# Main Signal model
class Signal(BaseModel):
    alert_info: AlertInfo
    bar_info: BarInfo
    current_info: CurrentInfo
    strategy_info: StrategyInfo


# New Payload class
class Payload(BaseModel):
    signal: Signal


@router.post("/order")
def get_order(payload: Payload):
    try:
        last_signal = payload.signal.dict()

        # Based on the strategy of the signal, define the order type and side
        order_type = "LIMIT"
        order_side = "BUY"
        if last_signal["strategy_info"]["order"]["action"] == "SELL":
            order_side = "SELL"

        # Format JSON output
        formatted_output = {
            "symbol": last_signal["alert_info"]["ticker"],
            "close": last_signal["bar_info"]["close"],
            "volume": last_signal["alert_info"]["volume"],
            "interval": last_signal["alert_info"]["interval"],
            "strategy": last_signal["strategy_info"]["order"]["action"],
            "type": order_type,
            "side": order_side,
            "price": last_signal["bar_info"]["close"],
            "quantity": last_signal["alert_info"]["volume"],
        }

        return formatted_output

    except Exception as e:
        # print the traceback of the error
        print(f"Failed to create order. Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")
