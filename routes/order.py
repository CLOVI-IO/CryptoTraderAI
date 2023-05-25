# order.py

from fastapi import APIRouter, HTTPException
import traceback
import os
import json
import asyncio
import time
import logging
from typing import Optional, List

from models import Payload
from routes.tradeguard import fetch_order_quantity
from redis_handler import RedisHandler

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Fetch trade percentage from environment variable
TRADE_PERCENTAGE = float(os.getenv("TRADE_PERCENTAGE", 10))


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
        redis_handler = RedisHandler()
        r = redis_handler.redis_client

        last_signal = json.loads(r.get("last_signal"))
        action = last_signal["strategy_info"]["order"]["action"]
        order_side, order_type = action.split("_")

        # Fetch order quantity from TradeGuard
        amount_available_to_trade = await fetch_order_quantity(ref_price)

        logging.debug(f"Amount available to trade: {amount_available_to_trade}")

        ref_price = last_signal["bar_info"]["close"]
        quantity_to_buy = amount_available_to_trade / float(ref_price)

        logging.debug(f"Quantity to buy: {quantity_to_buy}")

        order = {
            "instrument_name": last_signal["alert_info"]["ticker"],
            "close": ref_price,
            "volume": last_signal["alert_info"]["volume"],
            "interval": last_signal["alert_info"]["interval"],
            "strategy": action,
            "type": order_type,
            "side": order_side,
            "price": ref_price,
            "quantity": quantity_to_buy,  # use the calculated quantity
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

        response = {
            "last_order": order,
            "execution_time": end_time,
            "latency": latency,
        }

        logging.debug(f"Order: {order}")

        return response

    except Exception as e:
        logging.error(f"Failed to create order. Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to create order: {str(e)}")
