from fastapi import APIRouter, WebSocket, FastAPI
from starlette.websockets import WebSocketDisconnect
import os
import json
import time
import redis
import logging
from models import Payload
from exchanges.crypto_com.public.auth import get_auth

app = FastAPI() # if this is your main app. Otherwise, this would be in your main app file

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Get the singleton instance of the Authentication class.
auth = get_auth()

connected_websockets = set()

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

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
                logging.info(f"Order: Received last_signal from Redis channel: {last_signal}")  
                await send_to_order_endpoint(last_signal)  # Send data to create_order endpoint
                await websocket.send_text(json.dumps(last_signal.dict()))  # Sending as JSON string
                logging.debug(f"Order: Sent signal to client: {last_signal}")
    except WebSocketDisconnect:
        logging.error("Order: WebSocket disconnected.")
        connected_websockets.remove(websocket)
    except Exception as e:
        logging.error(f"Order: Unexpected error: {str(e)}")
    finally:
        pubsub.unsubscribe("last_signal")  
        logging.info("Order: Unsubscribed from 'last_signal' channel")

async def send_to_order_endpoint(data: Payload):
    # replace with your actual create_order endpoint
    url = "http://your_url_here/create_order"
    try:
        response = await auth.session.post(url, json=data.dict())
        response.raise_for_status()
        if response.status_code == 200:
            logging.debug(f"Order: Successfully sent data to order endpoint. Response: {response.json()}")
        else:
            logging.error(f"Order: Failed to send data to order endpoint. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Order: Error sending data to order endpoint: {str(e)}")

logging.info(":: Order endpoint ready ::") 
