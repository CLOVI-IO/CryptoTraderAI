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

# Fetch trade percentage from environment variable
TRADE_PERCENTAGE = float(os.getenv("TRADE_PERCENTAGE", 10))

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
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)


# Sends an order request
async def send_order_request():
    method = "private/create-order"
    nonce = str(int(time.time() * 1000))
    id = int(nonce)

    request = {
        "id": id,
        "method": method,
        "params": {
            "quantity": 0.01,  # Hardcoded for now
        },
        "nonce": nonce,
    }

    logging.info(f"Sending request at {datetime.utcnow().isoformat()}: {request}")
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


# This function listens to changes in the last_signal key and triggers the fetch_order function when the key changes
async def listen_for_signals():
    pubsub = redis_handler.redis_client.pubsub()
    pubsub.subscribe("__keyspace@0__:last_signal")
    while True:
        message = pubsub.get_message()
        if message:
            # Check if the message type is a change in the key (the 'set' command)
            if message["type"] == "message" and message["data"] == b"set":
                logging.info(
                    f"Last signal changed at {datetime.utcnow().isoformat()}, fetching order..."
                )
                # Trigger the fetch_order function
                await fetch_order()
        await asyncio.sleep(0.1)


# Start the listener when the module is loaded
asyncio.create_task(listen_for_signals())
