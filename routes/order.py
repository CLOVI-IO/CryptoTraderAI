# order.py
from fastapi import APIRouter, WebSocket, BackgroundTasks
from starlette.websockets import WebSocketDisconnect
import os
import json
import time
import redis
import logging
from models import Payload
from exchanges.crypto_com.public.auth import get_auth

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Get the singleton instance of the Authentication class.
auth = get_auth()

connected_websockets = set()

def connect_to_redis():
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

    try:
        r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
        r.ping()
        logging.info("Connected to Redis successfully!")
        return r
    except Exception as e:
        logging.error(f"Error connecting to Redis: {str(e)}")
        return None

redis_client = connect_to_redis()

RETRY_LIMIT = 3  # Maximum number of reconnection attempts

@router.websocket("/ws/order")
async def websocket_order(websocket: WebSocket, background_tasks: BackgroundTasks):
    await websocket.accept()
    logging.info("WebSocket accepted")
    connected_websockets.add(websocket)

    retry_count = 0
    while retry_count < RETRY_LIMIT:
        try:
            background_tasks.add_task(listen_to_redis, websocket)
            retry_count = 0  # Reset the counter if the connection is successful
        except WebSocketDisconnect:
            logging.error("WebSocket disconnected. Attempting to reconnect...")
            connected_websockets.remove(websocket)
            retry_count += 1
            time.sleep(5)  # Wait for 5 seconds before retrying
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
            break
    if retry_count == RETRY_LIMIT:
        logging.error("Maximum retry attempts reached. Connection failed.")

async def listen_to_redis(websocket: WebSocket):
    pubsub = redis_client.pubsub()  
    pubsub.subscribe("last_signal")  
    logging.info("Subscribed to 'last_signal' channel")  

    try:
        while True:
            message = pubsub.get_message()
            if message and message["type"] == "message":
                last_signal = Payload(**json.loads(message["data"]))
                logging.info(f"Received last_signal from Redis channel: {last_signal}")  
                await send_to_order_endpoint(last_signal)  # Send data to create_order endpoint
                await websocket.send_text(json.dumps(last_signal.dict()))  # Sending as JSON string
                logging.debug(f"Sent signal to client: {last_signal}")
    except Exception as e:
        logging.error(f"Error in listen_to_redis: {e}")
    finally:
        pubsub.unsubscribe("last_signal")  
        logging.info("Unsubscribed from 'last_signal' channel")

async def send_to_order_endpoint(data: Payload):
    # replace with your actual create_order endpoint
    url = "http://your_url_here/create_order"
    try:
        response = await auth.session.post(url, json=data.dict())
        response.raise_for_status()
    except Exception as e:
        logging.error(f"Error sending data to order endpoint: {str(e)}")

def read_last_signal():
    try:
        last_signal = redis_client.get("last_signal")
        if last_signal is None:
            logging.info("No last_signal value in Redis.")
        else:
            logging.info(f"Read last_signal from Redis: {last_signal.decode()}")  # Decoding bytes to string
    except Exception as e:
        logging.error(f"Error reading last_signal from Redis: {str(e)}")

read_last_signal()
logging.info("Order endpoint ready") 
