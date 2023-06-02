# order.py
import os
import json
import logging
import aioredis
from fastapi import APIRouter, WebSocket, BackgroundTasks, WebSocketDisconnect
from models import Payload

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

@router.websocket("/ws/order")
async def websocket_order(websocket: WebSocket, background_tasks: BackgroundTasks):
    await websocket.accept()
    logging.debug("WebSocket accepted")
    
    try:
        redis = await aioredis.create_redis_pool(f'redis://{REDIS_HOST}:{REDIS_PORT}', password=REDIS_PASSWORD)
        background_tasks.add_task(listen_to_redis, redis, websocket)
    except WebSocketDisconnect:
        logging.error("WebSocket disconnected")

async def listen_to_redis(redis, websocket: WebSocket):
    try:
        ch, *_ = await redis.subscribe('last_signal')
        async for message in ch.iter(encoding="utf-8"):
            last_signal = Payload(**json.loads(message))
            logging.debug(f"Received last_signal from Redis channel: {last_signal}")
            await websocket.send_text(f"Received signal from Redis: {last_signal}")

    except Exception as e:
        logging.error(f"Error in listen_to_redis: {e}")

    finally:
        await redis.unsubscribe('last_signal')
        redis.close()
        await redis.wait_closed()
        logging.debug("Unsubscribed from 'last_signal' channel")
