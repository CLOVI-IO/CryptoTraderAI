# order.py
# add last order to redis

from fastapi import APIRouter, WebSocket, BackgroundTasks, HTTPException, Depends
from exchanges.crypto_com.public.auth import get_auth
import os
import json
import time
import logging
import asyncio
from datetime import datetime
from typing import Optional, List
from models import Payload
from custom_exceptions import OrderException
from starlette.websockets import WebSocketDisconnect
import aioredis

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Get the singleton instance of the Authentication class.
auth = Depends(get_auth)

connected_websockets = set()


# WebSocket endpoint
@router.websocket("/ws/order")
async def websocket_order(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        # Start listening to Redis in the background
        asyncio.create_task(listen_to_redis())
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)


# Function to listen for messages from the Redis channel
async def listen_to_redis():
    redis = await aioredis.create_redis_pool("redis://localhost")
    channel = (await redis.subscribe("last_signal"))[0]
    while await channel.wait_message():
        message = await channel.get(encoding="utf-8")
        last_signal = Payload(**json.loads(message))
        logging.debug(f"Received last_signal from Redis channel: {last_signal}")
        await send_order_request(last_signal, redis)
        await fetch_order(last_signal, redis)


# Sends an order request
async def send_order_request(last_signal: Payload, redis):
    method = "private/create-order"
    nonce = str(int(time.time() * 1000))
    id = int(nonce)
    client_oid = f"{nonce}-order"

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
async def fetch_order(last_signal: Payload, redis):
    # Authenticate when required
    if not auth.authenticated:
        logging.info("Authenticating...")
        await auth.authenticate()

    request_id, request = await send_order_request(last_signal, redis)

    response = await auth.websocket.recv()

    response = json.loads(response)

    logging.debug(f"Received response at {datetime.utcnow().isoformat()}: {response}")

    if "id" in response and response["id"] == request_id:
        if "code" in response and response["code"] == 0:
            # Store order in Redis
            await redis.set("last_order", json.dumps(response))
            logging.info(f"Stored order in Redis at {datetime.utcnow().isoformat()}.")
        else:
            raise OrderException("Response id does not match request id")
    else:
        raise OrderException("Response id does not match request id")
