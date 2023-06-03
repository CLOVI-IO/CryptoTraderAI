from fastapi import APIRouter, BackgroundTasks
from fastapi.responses import JSONResponse
from dotenv import load_dotenv, find_dotenv
import os
import json
import asyncio
from redis_handler import RedisHandler  # import RedisHandler

# load dotenv in the root dir
load_dotenv(find_dotenv())

router = APIRouter()

latest_signal = None

def handle_message(message):
    global latest_signal
    latest_signal = message['data']

@router.on_event("startup")
async def startup_event():
    redis_handler = RedisHandler()  # create RedisHandler instance
    r = redis_handler.redis_client  # access redis client from RedisHandler
    p = r.pubsub()
    p.subscribe(**{'last_signal': handle_message})
    while True:
        message = p.get_message()
        if message:
            handle_message(message)
        await asyncio.sleep(0.001)  # sleep a bit between messages to prevent high CPU usage

@router.get("/viewsignal")
def view_signal():
    global latest_signal
    if latest_signal is None:
        print("No signal found in Redis")
        return {"signal": "No signal"}
    else:
        signal = json.loads(latest_signal)  # Convert JSON string to Python object
        print(f"Retrieved signal from Redis: {signal}")
        return {"signal": signal}
