# order.py
# add last order to redis

from fastapi import APIRouter, WebSocket, BackgroundTasks, HTTPException, Depends
from exchanges.crypto_com.public.auth import get_auth
import traceback
import os
import json
import time
import logging
import asyncio
from datetime import datetime
from typing import Optional, List
from models import Payload
from redis_handler import RedisHandler
from custom_exceptions import OrderException
from starlette.websockets import WebSocketDisconnect

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Get the singleton instance of the Authentication class.
auth = Depends(get_auth)

connected_websockets = set()

# Create an instance of RedisHandler
redis_handler = RedisHandler()


# WebSocket endpoint
@router.websocket("/ws/order")
async def websocket_order(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            last_signal = Payload(**json.loads(data))
            logging.debug(f"Received last_signal from webhook: {last_signal}")
            await send_order_request(last_signal)
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)


# Sends an order request
async def send_order_request(last_signal: Payload):
    method = "private/create-order"
    nonce = str(int(time.time() * 1000))
    id = int(nonce)
    client_oid = f"{nonce}-order"  # You can replace this with any format you want

    # TODO: take quantity to tradeguart endpoint (send instrument_name, receive the quantity)
    request = {
        "id": id,
        "method": method,
        "params": {
            "instrument_name": last_signal.instrument_name,
            "side": last_signal.side,
            "type": last_signal.type,
            "price": str(last_signal.price),
            "quantity": "0.01",
            "client_oid": client_oid,
            "exec_inst": ["POST_ONLY"],
            "time_in_force": "FILL_OR_KILL",
        },
        "nonce": nonce,
    }

    logging.debug(f"Sending request: {request}")
    await auth.send_request(method, request["params"])
    return id, request


# Fetches the order
async def fetch_order():
    # Authenticate when required
    if not auth.authenticated:
        logging.info("Authenticating...")
        await auth.authenticate()

    request_id, request = await send_order_request()

    response = await auth.websocket.recv()

    response = json.loads(response)

    logging.debug(f"Received response at {datetime.utcnow().isoformat()}: {response}")

    if "id" in response and response["id"] == request_id:
        if "code" in response and response["code"] == 0:
            # Store user balance in Redis
            redis_handler.redis_client.set("last_order", json.dumps(response))
            logging.info(f"Stored order in Redis at {datetime.utcnow().isoformat()}.")
            # Retrieve stored data for debugging purposes
            order_redis = redis_handler.redis_client.get("last_order")
            logging.debug(
                f"Retrieved from Redis at {datetime.utcnow().isoformat()}: {order_redis}"
            )
            return {"message": "Successfully fetched order", "order": response}
        else:
            raise OrderException("Response id does not match request id")
    else:
        raise OrderException("Response id does not match request id")
