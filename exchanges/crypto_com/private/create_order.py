# create_order.py

from fastapi import APIRouter, WebSocket, BackgroundTasks, HTTPException, Depends
from datetime import datetime
import asyncio
import time
import traceback
import logging
import json
import uuid
from redis_handler import RedisHandler
from typing import Optional, List
from custom_exceptions import OrderException
from exchanges.crypto_com.public.auth import get_auth

router = APIRouter()
logging.basicConfig(level=logging.DEBUG)
connected_websockets = set()

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
        "client_oid": str(uuid.uuid4()),
        "exec_inst": ["POST_ONLY"],
        "time_in_force": "FILL_OR_KILL",
    },
}

redis_handler = RedisHandler()

# Get the singleton instance of the Authentication class.
auth = Depends(get_auth)


async def fetch_order(order_request):
    start_time = datetime.utcnow()
    try:
        await send_order_request(order_request)
        logging.info(f"Sent order request at {datetime.utcnow().isoformat()}.")
        end_time = datetime.utcnow()
        latency = (end_time - start_time).total_seconds()
        logging.info(f"Order request latency: {latency} seconds")
    except Exception as e:
        error_message = str(e)
        if not error_message:
            error_message = repr(e)
        logging.error(
            f"Failed to fetch order. Error: {error_message}. Traceback: {traceback.format_exc()}"
        )
        raise OrderException("Failed to fetch order")


async def send_order_request(order_request):
    await auth.send_request(order_request["method"], order_request["params"])


async def recv_order_response(request_id):
    recv_attempts = 0
    start_time = datetime.utcnow()
    while recv_attempts < 5:
        recv_attempts += 1
        response = await asyncio.wait_for(auth.websocket.recv(), timeout=10)

        if "id" in response and response["id"] == request_id:
            if "code" in response and response["code"] == 0:
                redis_handler.redis_client.set("last_order", json.dumps(response))
                logging.info(
                    f"Stored order in Redis at {datetime.utcnow().isoformat()}."
                )
                order_redis = redis_handler.redis_client.get("last_order")
                logging.debug(
                    f"Retrieved from Redis at {datetime.utcnow().isoformat()}: {order_redis}"
                )
                end_time = datetime.utcnow()
                latency = (end_time - start_time).total_seconds()
                return {
                    "message": "Successfully fetched order",
                    "order": response,
                    "timestamp": start_time.isoformat(),
                    "latency": f"{latency} seconds",
                }
            else:
                end_time = datetime.utcnow()
                latency = (end_time - start_time).total_seconds()
                logging.error(
                    f"Response id does not match request id. Expected: {request_id}, Actual: {response.get('id')}, Full Response: {response}, Latency: {latency}s"
                )
                raise OrderException("Response id does not match request id")
        else:
            logging.info(
                f"Response does not contain an 'id'. Full Response: {response}"
            )
        await asyncio.sleep(1)
    end_time = datetime.utcnow()
    latency = (end_time - start_time).total_seconds()
    logging.error(
        f"Failed to receive expected response after 5 attempts. Last Response: {response}, Latency: {latency}s"
    )
    raise OrderException("Failed to receive expected response after 5 attempts")


@router.post("/orders/")
async def create_order(request: Optional[dict] = None):
    if request is None:
        request = request_sample
    request_id = request["id"]

    try:
        await fetch_order(request)
        response = await recv_order_response(request_id)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
