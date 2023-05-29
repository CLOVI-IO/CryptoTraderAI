from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
import os
import json
import time
from datetime import datetime
from redis_handler import RedisHandler
from exchanges.crypto_com.public.auth import get_auth

# Get the singleton instance of the Authentication class.
auth = Depends(get_auth)

# Create an instance of RedisHandler
redis_handler = RedisHandler()

router = APIRouter()


@router.get("/last_order")
async def get_last_order(background_tasks: BackgroundTasks):
    start_time = datetime.utcnow()

    try:
        last_order = redis_handler.redis_client.get("last_order")
        end_time = datetime.utcnow()
        latency = (end_time - start_time).total_seconds()
        if last_order is None:
            background_tasks.add_task(subscribe_to_last_order)
            return {
                "message": "Started subscribing to last order updates.",
                "timestamp": end_time.isoformat(),
                "latency": f"{latency} seconds",
            }
        else:
            return {
                "message": "Successfully fetched last order",
                "last_order": json.loads(last_order),
                "timestamp": end_time.isoformat(),
                "latency": f"{latency} seconds",
            }

    except Exception as e:
        print(f"Failed to get last order. Error: {str(e)}")
        end_time = datetime.utcnow()
        latency = (end_time - start_time).total_seconds()
        print(f"Timestamp: {end_time.isoformat()}, Latency: {latency} seconds")
        raise HTTPException(
            status_code=500, detail=f"Failed to get last order: {str(e)}"
        )


async def subscribe_to_last_order():
    try:
        pubsub = redis_handler.redis_client.pubsub(ignore_subscribe_messages=True)
        pubsub.subscribe("last_order")
        while True:
            message = pubsub.get_message()
            if message:
                print(f"Received update: {message['data']}")
    except Exception as e:
        print(f"Failed to subscribe to last_order updates. Error: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to subscribe to last_order updates: {str(e)}",
        )
