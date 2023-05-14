from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from shared_state import state  # Import the shared state
import traceback  # import traceback module for detailed error logging

router = APIRouter()


class Plots(BaseModel):
    plot_0: str
    plot_1: str


class Order(BaseModel):
    action: str
    contracts: str
    price: str
    id: str
    comment: str
    alert_message: str


class StrategyInfo(BaseModel):
    position_size: str
    order: Order
    market_position: str
    market_position_size: str
    prev_market_position: str
    prev_market_position_size: str


class CurrentInfo(BaseModel):
    fire_time: str
    plots: Plots


class BarInfo(BaseModel):
    open: str
    high: str
    low: str
    close: str
    volume: str
    time: str


class AlertInfo(BaseModel):
    exchange: str
    ticker: str
    price: str
    volume: str
    interval: str


class Signal(BaseModel):
    alert_info: AlertInfo
    bar_info: BarInfo
    current_info: CurrentInfo
    strategy_info: StrategyInfo


# get only for debuging, need to be changed when connection to exchange
@router.get("/order")
def get_order(signal: Signal):
    try:
        last_signal = signal.dict()

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
