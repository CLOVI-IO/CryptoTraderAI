import os
import json
import logging
import asyncio
from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
from dotenv import load_dotenv, find_dotenv
from redis_handler import RedisHandler
from datetime import datetime, timezone
from exchanges.crypto_com.public.auth import get_auth
import websockets
import time

router = APIRouter()

# Load environment variables
load_dotenv(find_dotenv())

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("order.py")

# Get Redis connection details from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Create RedisHandler instance with explicit environment variables
redis_handler = RedisHandler(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB
)
redis_client = redis_handler.redis_client  # Access redis client from RedisHandler

connected_websockets = set()


async def send_order_subscription_request(auth):
    """Send order subscription request via WebSocket"""
    method = "subscribe"
    nonce = str(int(time.time() * 1000))
    params = {"channels": ["private.orders"]}

    request = {
        "id": int(nonce),
        "method": method,
        "params": params,
        "nonce": nonce,
    }

    logger.info(
        f"Sending subscription request at {datetime.now(timezone.utc).isoformat()}: {request}"
    )
    await auth.websocket.send(json.dumps(request))


async def handle_order_updates(auth, redis_handler):
    """Handle order updates received via WebSocket"""
    while True:
        try:
            response = await auth.websocket.recv()
            logger.debug(f"Received WebSocket message: {response}")
            response_data = json.loads(response)

            if response_data.get("method") == "private/orders":
                logger.info(f"Order update received: {response_data}")
                order_data = json.dumps(response_data["result"]["data"])
                redis_handler.set("order_update", order_data)
                logger.info(f"Order data written to Redis: {order_data}")
            elif response_data.get("method") == "public/heartbeat":
                heartbeat_id = response_data["id"]
                await auth.websocket.send(
                    json.dumps(
                        {"id": heartbeat_id, "method": "public/respond-heartbeat"}
                    )
                )
                logger.info(f"Sent heartbeat response for id {heartbeat_id}.")
            else:
                logger.debug(f"Non-order related message received: {response_data}")

        except websockets.ConnectionClosed as e:
            logger.error(f"WebSocket connection closed: {e}")
            break
        except Exception as e:
            logger.error(f"Error in WebSocket handling: {e}")
            break


async def start_order_subscription(redis_handler):
    while True:
        try:
            auth = get_auth()
            await auth.connect()
            await auth.authenticate()
            await send_order_subscription_request(auth)
            await handle_order_updates(auth, redis_handler)
        except Exception as e:
            logger.error(f"Error in WebSocket connection: {e}")
            logger.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)


@router.websocket("/ws/order")
async def websocket_order(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket accepted")
    connected_websockets.add(websocket)

    pubsub = redis_client.pubsub()
    pubsub.subscribe("last_order")
    logger.info("Subscribed to 'last_order' channel")

    try:
        while True:
            message = pubsub.get_message()
            if message and message["type"] == "message":
                last_order = json.loads(message["data"])
                logger.info(f"Received last_order from Redis channel: {last_order}")

                # Send order to the crypto_com API
                response = await send_order_to_crypto_com(last_order)
                logger.info(f"Received response from crypto_com: {response}")

                # Write order and response to order_history in Redis
                await update_order_history(redis_handler, last_order, response)

                # Notify connected WebSocket clients
                for ws_client in connected_websockets:
                    await ws_client.send_json(
                        {"order": last_order, "response": response}
                    )
                    logger.debug(f"Sent order response to client: {response}")

    except WebSocketDisconnect:
        logger.error("WebSocket disconnected.")
        connected_websockets.remove(websocket)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
    finally:
        pubsub.unsubscribe("last_order")
        logger.info("Unsubscribed from 'last_order' channel")


async def send_order_to_crypto_com(order):
    """Send order to Crypto.com via WebSocket"""
    try:
        auth = get_auth()
        await auth.connect()
        await auth.authenticate()

        request = {
            "id": int(time.time() * 1000),
            "method": "private/create-order",
            "params": order["params"],
            "nonce": str(int(time.time() * 1000)),
        }
        await auth.websocket.send(json.dumps(request))
        logger.info(f"Sent order to crypto_com: {request}")
        response = await auth.websocket.recv()
        logger.info(f"Received response from crypto_com: {response}")
        return json.loads(response)
    except Exception as e:
        logger.error(f"Failed to send order to crypto_com: {str(e)}")
        return {"error": str(e)}


async def update_order_history(redis_handler, order, response):
    """Update the order history in Redis"""
    order_history_entry = {
        "order": order,
        "response": response,
        "timestamp": datetime.utcnow().isoformat(),
    }
    order_history = redis_handler.get("order_history")
    if order_history:
        order_history = json.loads(order_history)
    else:
        order_history = []
    order_history.append(order_history_entry)
    redis_handler.set("order_history", json.dumps(order_history))
    logger.info(f"Stored order and response in 'order_history': {order_history_entry}")


logger.info(":: Order endpoint ready ::")

# Start the order subscription handler in the background
asyncio.get_event_loop().create_task(start_order_subscription(redis_handler))
