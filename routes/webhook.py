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
TRADINGVIEW_IPS = os.getenv("TRADINGVIEW_IPS", "").split(",")

logging.debug(
    f"Environment Variables - REDIS_HOST: {REDIS_HOST}, REDIS_PORT: {REDIS_PORT}, REDIS_PASSWORD: {'******' if REDIS_PASSWORD else 'None'}, REDIS_DB: {REDIS_DB}"
)
logging.debug(f"Environment Variables - TRADINGVIEW_IPS: {TRADINGVIEW_IPS}")


@router.post("/webhook")
async def webhook(request: Request):
    client_host = request.headers.get("X-Forwarded-For", request.client.host)
    tradingview_ips = TRADINGVIEW_IPS

    logging.debug(f"Client IP: {client_host}")
    logging.debug(f"Whitelisted IPs: {tradingview_ips}")

    if client_host not in tradingview_ips:
        logging.error(f"Access denied for IP: {client_host}")
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
        logging.debug(f"Content-Type: {content_type}")

        if "application/json" in content_type:
            payload = await request.json()
        elif "text/plain" in content_type:
            body = await request.body()
            payload = body.decode()
            payload = json.loads(payload)
        else:
            logging.error(f"Unsupported media type: {content_type}")
            raise HTTPException(status_code=415, detail="Unsupported media type")

        logging.debug(f"Payload: {json.dumps(payload)}")

        redis_client.set("last_signal", json.dumps(payload))
        redis_client.publish("last_signal", json.dumps(payload))
        logging.info(
            f"Webhook endpoint: Set and published 'last_signal' to Redis: {json.dumps(payload)}"
        )

        return {"status": "ok"}
    except json.JSONDecodeError as e:
        logging.error(f"JSON decode error: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON format")
    except Exception as e:
        logging.error(f"Webhook endpoint: Failed to set and publish signal: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Webhook endpoint: An error occurred while setting and publishing the signal - {e}",
        )
