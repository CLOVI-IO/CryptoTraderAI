# webhook.py
from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv, find_dotenv
import os
import json
import redis
import logging


router = APIRouter()

logging.basicConfig(level=logging.DEBUG)

load_dotenv(find_dotenv())


def connect_to_redis():
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

    try:
        r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)
        r.ping()
        print("Connected to Redis successfully!")
        return r
    except Exception as e:
        print(f"Error connecting to Redis: {str(e)}")
        return None


@router.post("/webhook")
async def webhook(request: Request):
    client_host = request.client.host
    tradingview_ips = os.getenv("TRADINGVIEW_IPS", "").split(",")

    if client_host not in tradingview_ips:
        raise HTTPException(status_code=403, detail="Access denied")

    redis_client = connect_to_redis()
    if redis_client is None:
        raise HTTPException(status_code=500, detail="Failed to connect to Redis")

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

        # Publish the payload to a channel
        redis_client.publish("last_signal", json.dumps(payload))
        print(f"Published 'last_signal' to Redis: {json.dumps(payload)}")

        return {"status": "ok"}

    except Exception as e:
        print(f"Failed to publish signal: {e}")
        raise HTTPException(
            status_code=500, detail="An error occurred while publishing the signal"
        )
