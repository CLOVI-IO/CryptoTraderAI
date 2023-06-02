# webhook.py
from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv, find_dotenv
import os
import json
import logging
from redis_handler import RedisHandler  # import RedisHandler

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)

load_dotenv(find_dotenv())

@router.post("/webhook")
async def webhook(request: Request):
    client_host = request.client.host
    tradingview_ips = os.getenv("TRADINGVIEW_IPS", "").split(",")

    if client_host not in tradingview_ips:
        raise HTTPException(status_code=403, detail="Access denied")

    redis_handler = RedisHandler()  # create RedisHandler instance
    redis_client = redis_handler.redis_client  # access redis client from RedisHandler
    if redis_client is None:
        raise HTTPException(status_code=500, detail="Webhook endpoint: Failed to connect to Redis")

    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            payload = await request.json()
        elif "text/plain" in content_type:
            body = await request.body()
            payload = body.decode()
            payload = json.loads(payload)
        else:
            raise HTTPException(status_code=415, detail="Unsupported media type")

        # Set the payload to a key
        redis_client.set("last_signal", json.dumps(payload))
        print(f"Webhook endpoint: Set 'last_signal' to Redis: {json.dumps(payload)}")

        return {"status": "ok"}

    except Exception as e:
        print(f"Webhook endpoint: Failed to set signal: {e}")
        raise HTTPException(
            status_code=500, detail="Webhook endpoint: An error occurred while setting the signal"
        )
