import os
from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv, find_dotenv
import json
import logging
from redis_handler import RedisHandler

router = APIRouter()

logging.basicConfig(level=logging.DEBUG)

load_dotenv(find_dotenv())

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))


@router.post("/webhook")
async def webhook(request: Request):
    client_host = request.client.host
    tradingview_ips = os.getenv("TRADINGVIEW_IPS", "").split(",")

    if client_host not in tradingview_ips:
        raise HTTPException(status_code=403, detail="Access denied")

    redis_handler = RedisHandler(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB
    )
    redis_client = redis_handler.redis_client
    if redis_client is None:
        raise HTTPException(
            status_code=500, detail="Webhook endpoint: Failed to connect to Redis"
        )

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

        # Set the payload to a key and also publish it
        redis_client.set("last_signal", json.dumps(payload))
        redis_client.publish("last_signal", json.dumps(payload))
        logging.info(
            f"Webhook endpoint: Set and published 'last_signal' to Redis: {json.dumps(payload)}"
        )

        return {"status": "ok"}
    except Exception as e:
        logging.error(f"Webhook endpoint: Failed to set and publish signal: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Webhook endpoint: An error occurred while setting and publishing the signal - {e}",
        )
