# viewsignal.py
from fastapi import APIRouter
from starlette.responses import JSONResponse
from fastapi import responses

from dotenv import load_dotenv, find_dotenv
import os
import json
import logging  # import logging module
from redis_handler import RedisHandler  # import RedisHandler

# load dotenv in the root dir
load_dotenv(find_dotenv())

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.INFO)


@router.get("/viewsignal")
def view_signal():
    try:
        redis_handler = RedisHandler()  # create RedisHandler instance
        r = redis_handler.redis_client  # access redis client from RedisHandler
        last_signal = r.get("last_signal")
        if last_signal is None:
            logging.info("No signal found in Redis")  # replace print with logging.info
            return {"signal": "No signal"}
        else:
            signal = json.loads(last_signal)  # Convert JSON string to Python object
            logging.info(
                f"Retrieved signal from Redis: {signal}"
            )  # replace print with logging.info
            return {"signal": signal}
    except Exception as e:
        logging.error(
            f"Failed to retrieve signal: {str(e)}"
        )  # replace print with logging.error
        return JSONResponse(
            status_code=500,
            content={"detail": "An error occurred while retrieving the signal"},
        )
