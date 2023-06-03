from fastapi import APIRouter, WebSocket, FastAPI
from starlette.websockets import WebSocketDisconnect
import os
import json
import time
import aioredis
import logging
from models import Payload
from exchanges.crypto_com.public.auth import get_auth
from aioredis.pubsub import Receiver
from asyncio import create_task

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

# Initialize a pubsub Receiver
mpsc = Receiver()

redis_pool = None

@app.on_event("startup")
async def startup():
    global redis_pool
    # Asynchronously create a Redis connection pool
    redis_pool = await aioredis.create_pool(
        f'redis://{REDIS_HOST}:{REDIS_PORT}', password=REDIS_PASSWORD,
        minsize=5, maxsize=10)

@router.websocket("/ws/order")
async def websocket_order(websocket: WebSocket):
    await websocket.accept()
    logging.info("WebSocket accepted")
    connected_websockets.add(websocket)

    # Use the Redis connection pool to get a connection
    with await redis_pool as conn:
        # Subscribe to 'last_signal' channel
        await conn.execute('subscribe', mpsc.channel('last_signal'))
        logging.info("Subscribed to 'last_signal' channel")
        
        try:
            # Asynchronously iterate over messages in the channel
            async for channel, message in mpsc.iter():
                last_signal = Payload(**json.loads(message))
                logging.info(f"Received last_signal from Redis channel: {last_signal}")  
                await send_to_order_endpoint(last_signal)  # Send data to create_order endpoint
                await websocket.send_text(json.dumps(last_signal.dict()))  # Sending as JSON string
                logging.debug(f"Sent signal to client: {last_signal}")
        except WebSocketDisconnect:
            logging.error("WebSocket disconnected.")
            connected_websockets.remove(websocket)
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")
        finally:
            # Unsubscribe from 'last_signal' channel
            await conn.execute('unsubscribe', 'last_signal')
            logging.info("Unsubscribed from 'last_signal' channel")

async def send_to_order_endpoint(data: Payload):
    # replace with your actual create_order endpoint
    url = "http://your_url_here/create_order"
    try:
        response = await auth.session.post(url, json=data.dict())
        response.raise_for_status()
        if response.status_code == 200:
            logging.debug(f"Successfully sent data to order endpoint. Response: {response.json()}")
        else:
            logging.error(f"Failed to send data to order endpoint. Status code: {response.status_code}")
    except Exception as e:
        logging.error(f"Error sending data to order endpoint: {str(e)}")

logging.info("Order endpoint ready")
