from fastapi import APIRouter, HTTPException
import traceback
import os
import json
import redis
import asyncio
import time
import logging
from typing import Optional, List

from ..models import Payload
from exchanges.crypto_com.public import auth

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)


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
