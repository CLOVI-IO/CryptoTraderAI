from fastapi import APIRouter, HTTPException, BackgroundTasks
from dotenv import load_dotenv, find_dotenv
import os
import logging
import json
from datetime import datetime
from redis_handler import RedisHandler

router = APIRouter()

# Load environment variables
load_dotenv(find_dotenv())

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Get Redis connection details from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))


@router.get("/last_order")
async def get_last_order():
    start_time = datetime.utcnow()
    output = {}  # dictionary to hold all relevant details

    # Create RedisHandler instance with explicit environment variables
    redis_handler = RedisHandler(
        host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB
    )
    redis_client = (
        redis_handler.redis_client
    )  # get connected redis client from RedisHandler
    try:
        last_order = redis_client.get("last_order")
        if not last_order:
            output.update(
                {
                    "message": "No last order in Redis",
                    "timestamp": start_time.isoformat(),
                    "latency": "N/A",
                }
            )
            return output

        try:
            last_order = json.loads(last_order)  # Parse into JSON only if not None
            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds()

            output.update(
                {
                    "message": "Successfully fetched last order",
                    "order": last_order,
                    "timestamp": end_time.isoformat(),
                    "latency": f"{latency} seconds",
                }
            )

            return output

        except Exception as e:
            end_time = datetime.utcnow()
            latency = (end_time - start_time).total_seconds()
            output.update(
                {
                    "error": f"Failed to get last order: {str(e)}",
                    "timestamp": end_time.isoformat(),
                    "latency": f"{latency} seconds",
                }
            )
            return output
    except Exception as e:
        logging.error(f"Failed in /last_order endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")
