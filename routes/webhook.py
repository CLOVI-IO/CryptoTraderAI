# webhook.py
from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv, find_dotenv
import os
import json
import redis

router = APIRouter()

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
    redis_client = connect_to_redis()
    if redis_client is None:
        raise HTTPException(status_code=500, detail="Failed to connect to Redis")

    client_host = request.client.host
    tradingview_ips = os.getenv("TRADINGVIEW_IPS", "").split(",")

    if client_host not in tradingview_ips:
        raise HTTPException(status_code=403, detail="Access denied")

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

        redis_client.set("last_signal", json.dumps(payload))
        print(f"Stored 'last_signal' in Redis: {json.dumps(payload)}")

        # Debug code: Retrieve the value from Redis to ensure it was stored correctly
        redis_value = redis_client.get("last_signal")
        if redis_value is not None:
            print(f"Retrieved 'last_signal' from Redis: {redis_value.decode()}")
        else:
            print("Failed to retrieve 'last_signal' from Redis")

        return {"status": "ok"}

    except Exception as e:
        print(f"Failed to store signal: {e}")
        raise HTTPException(
            status_code=500, detail="An error occurred while storing the signal"
        )
