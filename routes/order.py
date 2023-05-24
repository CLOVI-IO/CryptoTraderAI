from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import traceback
from typing import Optional, List
import os
import json
import redis
import asyncio
import time
import logging

from exchanges.crypto_com.public import auth

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)


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


class Signal(BaseModel):
    alert_info: AlertInfo
    bar_info: BarInfo
    current_info: CurrentInfo
    strategy_info: StrategyInfo


class Payload(BaseModel):
    signal: Signal


@router.post("/order")
async def get_order(
    payload: Payload,
    client_oid: Optional[str] = None,
    exec_inst: Optional[List[str]] = None,
    time_in_force: Optional[str] = None,
    ref_price: Optional[str] = None,
    ref_price_type: Optional[str] = None,
    spot_margin: Optional[str] = None,
):
    start_time = time.time()
    try:
        # auth_response = await auth.authenticate()
        # if auth_response["message"] != "Authenticated successfully":
        #    raise HTTPException(status_code=401, detail="User is not authenticated")

        # Log auth response for debugging
        # logging.debug(f"Auth response: {auth_response}")

        REDIS_HOST = os.getenv("REDIS_HOST")
        REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
        r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

        last_signal = json.loads(r.get("last_signal"))
        action = last_signal["strategy_info"]["order"]["action"]
        order_side, order_type = action.split("_")

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

        r.set("last_order", json.dumps(order))

        end_time = time.time()
        latency = end_time - start_time

        # Log order for debugging
        logging.debug(f"Order: {order}")

        response = {
            "last_order": order,
            "execution_time": end_time,
            "latency": latency,
        }

        # Log order for debugging
        logging.debug(f"Order: {order}")

        return response

    except Exception as e:
        logging.error(f"Failed to create order. Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")
