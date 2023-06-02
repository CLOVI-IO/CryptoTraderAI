# order.py
from fastapi import APIRouter, WebSocket, BackgroundTasks
from redis import Redis
from asyncio import Queue
import json
import os
import logging
from models import Payload

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT", 6379)
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

@router.websocket("/ws/order")
async def websocket_endpoint(websocket: WebSocket, background_tasks: BackgroundTasks):
    # Connect to Redis.
    redis = Redis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
    pubsub = redis.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe("last_signal")

    # Create a queue for messages.
    queue = Queue()

    # Add a background task for reading from Redis and putting messages into the queue.
    background_tasks.add_task(read_from_redis, pubsub, queue)

    # Accept the WebSocket connection.
    await websocket.accept()

    # Keep reading messages from the queue and sending them via WebSocket.
    while True:
        message = await queue.get()
        await websocket.send_text(f"Received signal from Redis: {message}")

def read_from_redis(pubsub, queue):
    for message in pubsub.listen():
        if message["type"] == "message":
            last_signal = Payload(**json.loads(message["data"]))
            logging.debug(f"Received last_signal from Redis channel: {last_signal}")
            queue.put_nowait(str(last_signal))
