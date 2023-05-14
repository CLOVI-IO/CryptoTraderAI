from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from shared_state import state  # Import the shared state
import traceback  # import traceback module for detailed error logging

router = APIRouter()


# Define the nested classes for the data model
class Order(BaseModel):
    action: str = Field(alias="{{strategy.order.action}}")
    contracts: str = Field(alias="{{strategy.order.contracts}}")
    price: str = Field(alias="{{strategy.order.price}}")
    id: str = Field(alias="{{strategy.order.id}}")
    comment: str = Field(alias="{{strategy.order.comment}}")
    alert_message: str = Field(alias="{{strategy.order.alert_message}}")


class StrategyInfo(BaseModel):
    position_size: str = Field(alias="{{strategy.position_size}}")
    order: Order
    market_position: str = Field(alias="{{strategy.market_position}}")
    market_position_size: str = Field(alias="{{strategy.market_position_size}}")
    prev_market_position: str = Field(alias="{{strategy.prev_market_position}}")
    prev_market_position_size: str = Field(
        alias="{{strategy.prev_market_position_size}}"
    )


class Plots(BaseModel):
    plot_0: str = Field(alias="{{plot_0}}")
    plot_1: str = Field(alias="{{plot_1}}")


class CurrentInfo(BaseModel):
    fire_time: str = Field(alias="{{timenow}}")
    plots: Plots


class BarInfo(BaseModel):
    open: str = Field(alias="{{open}}")
    high: str = Field(alias="{{high}}")
    low: str = Field(alias="{{low}}")
    close: str = Field(alias="{{close}}")
    volume: str = Field(alias="{{volume}}")
    time: str = Field(alias="{{time}}")


class AlertInfo(BaseModel):
    exchange: str = Field(alias="{{exchange}}")
    ticker: str = Field(alias="{{ticker}}")
    price: str = Field(alias="{{close}}")
    volume: str = Field(alias="{{volume}}")
    interval: str = Field(alias="{{interval}}")


# Main Signal model
class Signal(BaseModel):
    alert_info: AlertInfo
    bar_info: BarInfo
    current_info: CurrentInfo
    strategy_info: StrategyInfo


@router.get("/order")
def get_order():
    try:
        # Check if last_signal has been set in the shared state
        if "last_signal" not in state or state["last_signal"] is None:
            raise HTTPException(status_code=400, detail="No signal available")

        # Retrieve the last signal from the shared state
        last_signal = Signal(**state["last_signal"])

        print(f"Retrieved signal from shared state: {last_signal}")  # Debug print

        # Based on the strategy of the signal, define the order type and side
        order_type = "LIMIT"
        order_side = last_signal.strategy_info.order.action

        # Format JSON output
        formatted_output = {
            "symbol": last_signal.alert_info.ticker,
            "close": last_signal.alert_info.price,
            "volume": last_signal.alert_info.volume,
            "interval": last_signal.alert_info.interval,
            "strategy": last_signal.strategy_info.market_position,
            # Add other tags for the Crypto.com exchange API
            "type": order_type,
            "side": order_side,
            "price": last_signal.strategy_info.order.price,
            "quantity": last_signal.strategy_info.position_size,
        }

        print(f"Formatted order: {formatted_output}")  # Debug print

        return formatted_output

    except Exception as e:
        # print the traceback of the error
        print(f"Failed to create order. Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")
