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
from routes.tradeguard import fetch_order_quantity
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


@router.websocket("/ws/order")
async def websocket_order(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)


async def send_order_request():
    method = "private/create-order"
    nonce = str(int(time.time() * 1000))
    id = int(nonce)

    request = {
        "id": id,
        "method": method,
        "params": {},
        "nonce": nonce,
    }

    logging.info(f"Sending request at {datetime.utcnow().isoformat()}: {request}")
    await auth.send_request(method, request["params"])
    return id, request


async def fetch_order(retries=3, delay=5, max_recv_attempts=3):
    # Authenticate when required
    if not auth.authenticated:
        logging.info("Authenticating...")
        await auth.authenticate()

    start_time = datetime.utcnow()
    while retries > 0:
        try:
            request_id, request = await send_order_request()
            break  # If request sent successfully, break the loop
        except Exception as e:
            if retries == 1:
                end_time = datetime.utcnow()
                latency = (end_time - start_time).total_seconds()
                logging.error(
                    f"Error occurred. Latency: {latency}s. Exception: {str(e)}"
                )
                raise e  # Re-raise the exception after all attempts exhausted
            retries -= 1
            await asyncio.sleep(delay)  # Wait before next attempt

    recv_attempts = 0
    while recv_attempts < max_recv_attempts:
        recv_attempts += 1
        try:
            response = await asyncio.wait_for(auth.websocket.recv(), timeout=10)
        except asyncio.TimeoutError:
            logging.error("Timeout error while waiting for response.")
            raise OrderException("Timeout error while waiting for response")
        except Exception as e:
            logging.error(f"Error while receiving response: {str(e)}")
            raise OrderException(f"Error while receiving response: {str(e)}")

        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON response: {response}")
            raise OrderException("Invalid JSON response")

        logging.debug(
            f"Received response at {datetime.utcnow().isoformat()}: {response}"
        )

        if "method" in response and response["method"] == "public/heartbeat":
            logging.info("Received heartbeat, continuing to wait for actual response.")
            continue  # Ignore the heartbeat message and keep waiting for the actual response

        if "id" in response and response["id"] == request_id:
            if "code" in response and response["code"] == 0:
                # Store user balance in Redis
                redis_handler.redis_client.set("last_order", json.dumps(response))
                logging.info(
                    f"Stored order in Redis at {datetime.utcnow().isoformat()}."
                )
                # Retrieve stored data for debugging purposes
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
        logging.error(
            f"Response id does not match request id. Request id: {request_id}, Request: {request}, Response: {response}"
        )
        # If it reached here, it means that the response id did not match the request id, which is an error
        raise OrderException("Response id does not match request id")

    logging.error(
        f"Failed to receive the expected response after {recv_attempts} attempts. The last response: {response}"
    )
    # If it reached here, it means that the expected response was not received after all attempts
    raise OrderException("Failed to receive the expected response after all attempts")


@router.get("/order")
async def get_order(background_tasks: BackgroundTasks):
    start_time = datetime.utcnow()
    order_redis = redis_handler.redis_client.get("last_order")
    end_time = datetime.utcnow()
    latency = (end_time - start_time).total_seconds()
    if order_redis is None:
        background_tasks.add_task(fetch_order)
        return {
            "message": "Started fetching order",
            "order": json.load(order_redis),
            "timestamp": start_time.isoformat(),
            "latency": f"{latency} seconds",
        }
    else:
        return {
            "message": "Successfully fetched order",
            "order": json.loads(order_redis),
            "timestamp": end_time.isoformat(),
            "latency": f"{latency} seconds",
        }


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
