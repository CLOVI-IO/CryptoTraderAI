from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse
from dotenv import load_dotenv, find_dotenv
import os
import json
import logging
from redis_handler import RedisHandler

# Load dotenv in the root dir
load_dotenv(find_dotenv())

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get Redis connection details from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))


@router.get("/viewsignal")
def view_signal():
    try:
        # Create RedisHandler instance with explicit environment variables
        redis_handler = RedisHandler(
            host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB
        )
        r = redis_handler.redis_client  # get connected redis client from RedisHandler
        last_signal = r.get("last_signal")
        if last_signal is None:
            logging.info("No signal found in Redis")
            return {"signal": "No signal"}
        else:
            signal = json.loads(last_signal)  # Convert JSON string to Python object
            logging.info(f"Retrieved signal from Redis: {signal}")
            return {"signal": signal}
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse signal as JSON: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to parse signal as JSON")
    except Exception as e:
        logging.error(f"Failed to retrieve signal: {str(e)}")
        raise HTTPException(
            status_code=500, detail="An error occurred while retrieving the signal"
        )
