from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import traceback  # import traceback module for detailed error logging
from typing import Optional, List
import os
import json
import redis

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
def get_order(payload: Payload,
              client_oid: Optional[str] = None,
              exec_inst: Optional[List[str]] = None,
              time_in_force: Optional[str] = None,
              ref_price: Optional[str] = None,
              ref_price_type: Optional[str] = None,
              spot_margin: Optional[str] = None):
    try:
        REDIS_HOST = os.getenv("REDIS_HOST")
        REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
        r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

        last_signal = json.loads(r.get("last_signal"))

        # Extract action from the strategy_info
        action = last_signal["strategy_info"]["order"]["action"]

        # Split action into side and type
        order_side, order_type = action.split('_')

        # Format JSON output
        order = {
            "instrument_name": last_signal["alert_info"]["ticker"],
            "close": last_signal["bar_info"]["close"],
            "volume": last_signal["alert_info"]["volume"],
            "interval": last_signal["alert_info"]["interval"],
            "strategy": action,
            "type": order_type,
            "side": order_side,
            "price": last_signal["bar_info"]["close"],
            "quantity": last_signal["alert_info"]["volume"],
        }

        # Add optional parameters if they're provided
        if client_oid:
            order["client_oid"] = client_oid
        if exec_inst:
            order["exec_inst"] = exec_inst
        if time_in_force:
            order["time_in_force"] = time_in_force
        if ref_price:
            order["ref_price"] = ref_price
        if ref_price_type:
            order["ref_price_type"] = ref_price_type
        if spot_margin:
            order["spot_margin"] = spot_margin

       
