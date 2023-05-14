from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from shared_state import state  # Import the shared state
import traceback  # import traceback module for detailed error logging
from typing import Optional


router = APIRouter()


# Define the nested classes for the data model
class Order(BaseModel):
    action: Optional[str] = Field(alias="{{strategy.order.action}}")
    contracts: Optional[str] = Field(alias="{{strategy.order.contracts}}")
    price: Optional[str] = Field(alias="{{strategy.order.price}}")
    id: Optional[str] = Field(alias="{{strategy.order.id}}")
    comment: Optional[str] = Field(alias="{{strategy.order.comment}}")
    alert_message: Optional[str] = Field(alias="{{strategy.order.alert_message}}")


class StrategyInfo(BaseModel):
    position_size: Optional[str] = Field(alias="{{strategy.position_size}}")
    order: Order
    market_position: Optional[str] = Field(alias="{{strategy.market_position}}")
    market_position_size: Optional[str] = Field(
        alias="{{strategy.market_position_size}}"
    )
    prev_market_position: Optional[str] = Field(
        alias="{{strategy.prev_market_position}}"
    )
    prev_market_position_size: Optional[str] = Field(
        alias="{{strategy.prev_market_position_size}}"
    )


class Plots(BaseModel):
    plot_0: Optional[str] = Field(alias="{{plot_0}}")
    plot_1: Optional[str] = Field(alias="{{plot_1}}")


class CurrentInfo(BaseModel):
    fire_time: Optional[str] = Field(alias="{{timenow}}")
    plots: Plots


class BarInfo(BaseModel):
    open: Optional[str] = Field(alias="{{open}}")
    high: Optional[str] = Field(alias="{{high}}")
    low: Optional[str] = Field(alias="{{low}}")
    close: Optional[str] = Field(alias="{{close}}")
    volume: Optional[str] = Field(alias="{{volume}}")
    time: Optional[str] = Field(alias="{{time}}")


class AlertInfo(BaseModel):
    exchange: Optional[str] = Field(alias="{{exchange}}")
    ticker: Optional[str] = Field(alias="{{ticker}}")
    price: Optional[str] = Field(alias="{{close}}")
    volume: Optional[str] = Field(alias="{{volume}}")
    interval: Optional[str] = Field(alias="{{interval}}")


# Main Signal model
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
