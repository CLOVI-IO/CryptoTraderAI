from fastapi import APIRouter, WebSocket, HTTPException
from starlette.websockets import WebSocketDisconnect
from dotenv import load_dotenv, find_dotenv
import os
import json
import logging
from models import Payload
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
DEBUG_MODE = os.getenv("DEBUG_MODE", "ON").upper() == "ON"

# Create RedisHandler instance with explicit environment variables
redis_handler = RedisHandler(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB
)
redis_client = redis_handler.redis_client  # Access redis client from RedisHandler

connected_websockets = set()

# Load the order template
with open('templates/order_template.json') as f:
    order_template = json.load(f)

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
                logging.info(f"Order: Received last_order from Redis channel: {last_order}")

                # Create the order using the template
                order = order_template.copy()
                timestamp = int(datetime.now().timestamp() * 1000)
                order["id"] = timestamp
                order["params"]["instrument_name"] = last_order["instrument_name"]
                order["params"]["side"] = last_order["side"]
                order["params"]["type"] = last_order["type"]
                order["params"]["price"] = last_order["price"]
                order["params"]["quantity"] = last_order["quantity"]
                order["params"]["client_oid"] = f"order_{timestamp}"
                order["trigger"]["price"] = last_order["trigger_price"]
                order["trigger"]["callback_rate"] = last_order["callback_rate"]
                order["trigger"]["distance"] = last_order["distance"]
                order["risk_management"]["take_profit"]["price"] = last_order["take_profit_price"]
                order["risk_management"]["take_profit"]["quantity"] = last_order["quantity"]
                order["risk_management"]["stop_loss"]["price"] = last_order["stop_loss_price"]
                order["risk_management"]["stop_loss"]["quantity"] = last_order["quantity"]

                if DEBUG_MODE:
                    order["method"] = "TEST_ORDER"
                    logging.info(f"Order: Debug mode is ON. Order will not be sent to crypto_com: {order}")
                else:
                    # Send the order via WebSocket to crypto_com exchange
                    await websocket.send_json(order)
                    logging.info(f"Order: Sent order to crypto_com: {order}")

                # Log the order history to Redis
                redis_client.lpush("order_history", json.dumps(order))
                logging.info(f"Order: Logged order history to Redis: {order}")

                # Notify connected WebSocket clients
                for ws in connected_websockets:
                    await ws.send_json(order)
                    logging.debug(f"Order: Sent order to client: {order}")
    except WebSocketDisconnect:
        logging.error("Order: WebSocket disconnected.")
        connected_websockets.remove(websocket)
    except Exception as e:
        logging.error(f"Order: Unexpected error: {str(e)}")
    finally:
        pubsub.unsubscribe("last_order")
        logging.info("Order: Unsubscribed from 'last_order' channel")

logging.info(":: Order endpoint ready ::")
