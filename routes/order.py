# order.py
from fastapi import APIRouter, WebSocket, BackgroundTasks, HTTPException, Depends
import os
import json
import time
import redis
import logging
from datetime import datetime
from typing import Optional, List
from models import Payload
from exchanges.crypto_com.public.auth import get_auth
from starlette.websockets import WebSocketDisconnect

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

@router.websocket("ws://ai.clovi.io/ws/order")
async def websocket_order(websocket: WebSocket, background_tasks: BackgroundTasks):
    await websocket.accept()
    logging.info("WebSocket accepted")
    connected_websockets.add(websocket)

    try:
        background_tasks.add_task(listen_to_redis, websocket)
    except WebSocketDisconnect:
        logging.error("WebSocket disconnected")
        connected_websockets.remove(websocket)

async def listen_to_redis(websocket: WebSocket):
    pubsub = redis_client.pubsub()  
    pubsub.subscribe("last_signal")  
    logging.info("Subscribed to 'last_signal' channel")  

    while True:
        try:
            message = pubsub.get_message()
            if message and message["type"] == "message":
                last_signal = Payload(**json.loads(message["data"]))
                logging.info(f"Received last_signal from Redis channel: {last_signal}")  
                await websocket.send_text(f"Received signal from Redis: {last_signal}")
        except Exception as e:
            logging.error(f"Error in listen_to_redis: {e}")
            break

    pubsub.unsubscribe("last_signal")  
    logging.info("Unsubscribed from 'last_signal' channel")


def read_last_signal():
    try:
        last_signal = redis_client.get("last_signal")
        if last_signal is None:
            logging.info("No last_signal value in Redis.")
        else:
            logging.info(f"Read last_signal from Redis: {last_signal}")
    except Exception as e:
        logging.error(f"Error reading last_signal from Redis: {str(e)}")



read_last_signal()
logging.info("Order endpoint ready") 
