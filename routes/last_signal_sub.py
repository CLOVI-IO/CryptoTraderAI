import asyncio
from fastapi import APIRouter
from fastapi.responses import EventSourceResponse
from dotenv import load_dotenv, find_dotenv
import os
import json
import redis
import logging

router = APIRouter()

# Load environment variables
load_dotenv(find_dotenv())

# Configure logging
logging.basicConfig(level=logging.INFO)


def connect_to_redis():
    REDIS_HOST = os.getenv("REDIS_HOST", "redis")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

    try:
        r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
        r.ping()
        logging.info("Connected to Redis successfully!")
        return r
    except Exception as e:
        logging.error(f"Error connecting to Redis: {str(e)}")
        return None


redis_client = connect_to_redis()


async def listen_to_redis(send):
    pubsub = redis_client.pubsub()
    pubsub.subscribe("last_signal")
    logging.info("Subscribed to 'last_signal' channel")

    while True:
        message = pubsub.get_message()
        if message and message["type"] == "message":
            last_signal = json.loads(message["data"])
            logging.info(f"Received last_signal from Redis channel: {last_signal}")
            await send({"data": f"Received signal from Redis: {last_signal}"})
        await asyncio.sleep(0.01)


@router.get("/last_signal_sub")
async def last_signal_sub():
    async def event_generator():
        loop = asyncio.get_event_loop()
        queue = asyncio.Queue()

        async def send(event):
            await queue.put(event)

        loop.create_task(listen_to_redis(send))

        while True:
            event = await queue.get()
            yield event

    return EventSourceResponse(event_generator())
