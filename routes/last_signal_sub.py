# redis_pub_sub.py
import asyncio
from fastapi import APIRouter
import os
import json
import redis
import logging
from fastapi.responses import EventSourceResponse
from fastapi import FastAPI

app = FastAPI()

router = APIRouter()

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

async def listen_to_redis(send):
    while True:
        try:
            pubsub = redis_client.pubsub()  
            pubsub.subscribe("last_signal")  
            logging.info("Subscribed to 'last_signal' channel")  

            while True:
                try:
                    message = pubsub.get_message()
                    if message and message["type"] == "message":
                        last_signal = json.loads(message["data"])
                        logging.info(f"Received last_signal from Redis channel: {last_signal}")  
                        await send({"data": f"Received signal from Redis: {last_signal}"})
                except Exception as e:
                    logging.error(f"Error in listen_to_redis: {e}")
                    break
        except Exception as e:
            logging.error(f"Error connecting to Redis: {e}")
            logging.info("Attempting to reconnect in 5 seconds...")
            await asyncio.sleep(5)



@app.get("/last_signal_sub")
async def last_signal_sub():
    async def event_generator():
        await listen_to_redis
    return EventSourceResponse(event_generator())
