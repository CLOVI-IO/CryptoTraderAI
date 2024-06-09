from fastapi import APIRouter, WebSocket, HTTPException
from starlette.websockets import WebSocketDisconnect
from dotenv import load_dotenv, find_dotenv
import os
import json
import logging
from models import Payload
from redis_handler import RedisHandler

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
    pubsub.subscribe("last_signal")
    logging.info("Order: Subscribed to 'last_signal' channel")

    try:
        while True:
            message = pubsub.get_message()
            if message and message["type"] == "message":
                last_signal = Payload(**json.loads(message["data"]))
                logging.info(
                    f"Order: Received last_signal from Redis channel: {last_signal}"
                )
                await websocket.send_text(
                    json.dumps(last_signal.dict())
                )  # Sending as JSON string
                logging.debug(f"Order: Sent signal to client: {last_signal}")
    except WebSocketDisconnect:
        logging.error("Order: WebSocket disconnected.")
        connected_websockets.remove(websocket)
    except Exception as e:
        logging.error(f"Order: Unexpected error: {str(e)}")
    finally:
        pubsub.unsubscribe("last_signal")
        logging.info("Order: Unsubscribed from 'last_signal' channel")


logging.info(":: Order endpoint ready ::")
