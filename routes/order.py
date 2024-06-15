<<<<<<< HEAD
from fastapi import APIRouter, WebSocket, HTTPException
=======
from fastapi import APIRouter, WebSocket, BackgroundTasks, Depends
>>>>>>> dev
from starlette.websockets import WebSocketDisconnect
from dotenv import load_dotenv, find_dotenv
import os
import json
<<<<<<< HEAD
import logging
from models import Payload
from redis_handler import RedisHandler
=======
import redis
import logging
from models import Payload
from exchanges.crypto_com.public.auth import get_auth
>>>>>>> dev

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

<<<<<<< HEAD
=======
redis_client = None

async def connect_to_redis():
    global redis_client
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

    try:
        redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
        redis_client.ping()
        logging.info("Connected to Redis successfully!")
    except Exception as e:
        logging.error(f"Error connecting to Redis: {str(e)}")

# Connect to redis upon startup
connect_to_redis()

RETRY_LIMIT = 3  # Maximum number of reconnection attempts
>>>>>>> dev

@router.websocket("/ws/order")
async def websocket_order(websocket: WebSocket, background_tasks: BackgroundTasks):
    await websocket.accept()
    logging.info("Order: WebSocket accepted")
    connected_websockets.add(websocket)

<<<<<<< HEAD
    pubsub = redis_client.pubsub()
    pubsub.subscribe("last_signal")
    logging.info("Order: Subscribed to 'last_signal' channel")
=======
    for retry_count in range(RETRY_LIMIT):
        try:
            background_tasks.add_task(listen_to_redis, websocket)
            break  # If connection is successful, break the retry loop
        except WebSocketDisconnect:
            logging.error("WebSocket disconnected. Attempting to reconnect...")
            connected_websockets.remove(websocket)
            time.sleep(5)  # Wait for 5 seconds before retrying
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")

    if retry_count + 1 == RETRY_LIMIT:
        logging.error("Maximum retry attempts reached. Connection failed.")

async def listen_to_redis(websocket: WebSocket):
    pubsub = redis_client.pubsub()  
    pubsub.subscribe("last_signal")  
    logging.info("Subscribed to 'last_signal' channel")  
>>>>>>> dev

    try:
        while True:
            message = pubsub.get_message()
            if message and message["type"] == "message":
                last_signal = Payload(**json.loads(message["data"]))
<<<<<<< HEAD
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
=======
                logging.info(f"Received last_signal from Redis channel: {last_signal}")  
                await websocket.send_text(json.dumps(last_signal.dict()))  # Sending as JSON string
                logging.debug(f"Sent signal to client: {last_signal}")
    except Exception as e:
        logging.error(f"Error in listen_to_redis: {e}")
>>>>>>> dev
    finally:
        pubsub.unsubscribe("last_signal")
        logging.info("Order: Unsubscribed from 'last_signal' channel")

<<<<<<< HEAD

logging.info(":: Order endpoint ready ::")
=======
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
>>>>>>> dev
