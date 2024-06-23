import os
import json
import logging
from fastapi import APIRouter, WebSocket, HTTPException
from starlette.websockets import WebSocketDisconnect
from dotenv import load_dotenv, find_dotenv
from redis_handler import RedisHandler
from datetime import datetime

router = APIRouter()

# Load environment variables
load_dotenv(find_dotenv())

# Configure logging
logging.basicConfig(level=logging.DEBUG)

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


@router.websocket("/ws/order")
async def websocket_order(websocket: WebSocket):
    await websocket.accept()
    logging.info("Order: WebSocket accepted")
    connected_websockets.add(websocket)

    pubsub = redis_client.pubsub()
    pubsub.subscribe("last_order")
    logging.info("Order: Subscribed to 'last_order' channel")

    try:
        while True:
            message = pubsub.get_message()
            if message and message["type"] == "message":
                last_order = json.loads(message["data"])
                logging.info(
                    f"Order: Received last_order from Redis channel: {last_order}"
                )

                # Log the order details
                logging.info(f"Order ready to be sent: {last_order}")

                # Notify connected WebSocket clients
                for ws in connected_websockets:
                    await ws.send_json(last_order)
                    logging.debug(f"Order: Sent order to client: {last_order}")

                # Here you would send the order to the crypto_com API
                # For now, we are just logging the order
                # Uncomment and implement the send order logic when ready
                # await send_order_to_crypto_com(last_order)

    except WebSocketDisconnect:
        logging.error("Order: WebSocket disconnected.")
        connected_websockets.remove(websocket)
    except Exception as e:
        logging.error(f"Order: Unexpected error: {str(e)}")
    finally:
        pubsub.unsubscribe("last_order")
        logging.info("Order: Unsubscribed from 'last_order' channel")


logging.info(":: Order endpoint ready ::")


# Placeholder function for sending order to crypto_com
async def send_order_to_crypto_com(order):
    # Implement the logic for sending order to the crypto_com API
    pass
