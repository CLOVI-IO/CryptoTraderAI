# exchanges/crypto_com/private/create_order.py

from fastapi import APIRouter, HTTPException
import traceback
import os
import json
import asyncio
import time
import logging
from typing import Optional, List
from redis_handler import RedisHandler

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Sample request payload
request_sample = {
    "id": 1,
    "nonce": int(time.time() * 1000),
    "method": "private/create-order",
    "params": {
        "instrument_name": "BTCUSD-PERP",
        "side": "SELL",
        "type": "LIMIT",
        "price": "50000.5",
        "quantity": "0.01",
        "client_oid": "c5f682ed-7108-4f1c-b755-972fcdca0f02",
        "exec_inst": ["POST_ONLY"],
        "time_in_force": "FILL_OR_KILL",
    },
}


@router.post("/create_order")
async def create_order():
    try:
        redis_handler = RedisHandler()
        r = redis_handler.redis_client
        last_signal_json = r.get("last_signal")
        if last_signal_json is None:
            # Handle the case where last_signal is None
            raise Exception("No last_signal in Redis")
        last_signal = json.loads(last_signal_json)

        # Prepare the order payload
        request_sample["params"]["instrument_name"] = last_signal["alert_info"][
            "ticker"
        ]
        request_sample["params"]["side"] = (
            last_signal["strategy_info"]["order"]["action"].split("_")[0].upper()
        )
        request_sample["params"]["price"] = last_signal["bar_info"]["close"]

        logging.debug(f"Creating order with payload: {request_sample}")

        # TODO: Call the Exchange API to create the order with the request_sample payload
        # NOTE: This is a placeholder and will need to be replaced with the actual API call

        # Placeholder response
        response = {
            "id": 1,
            "method": "private/create-order",
            "code": 0,
            "result": {
                "client_oid": "c5f682ed-7108-4f1c-b755-972fcdca0f02",
                "order_id": "18342311",
            },
        }

        logging.debug(f"Order created: {response}")

        return response

    except Exception as e:
        error_message = str(e)
        if not error_message:
            error_message = repr(e)
        logging.error(
            f"Failed to create order. Error: {error_message}. Traceback: {traceback.format_exc()}"
        )
        raise HTTPException(
            status_code=500, detail=f"Failed to create order: {error_message}"
        )
