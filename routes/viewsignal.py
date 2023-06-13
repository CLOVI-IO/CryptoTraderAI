# viewsignal.py
from fastapi import APIRouter, HTTPException
from starlette.responses import JSONResponse
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
        r = redis_handler.get_client()  # get connected redis client from RedisHandler
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
    except json.JSONDecodeError as e:
        logging.error(
            f"Failed to parse signal as JSON: {str(e)}"
        )  # replace print with logging.error
        raise HTTPException(status_code=500, detail="Failed to parse signal as JSON")
    except Exception as e:
        logging.error(
            f"Failed to retrieve signal: {str(e)}"
        )  # replace print with logging.error
        raise HTTPException(
            status_code=500, detail="An error occurred while retrieving the signal"
        )
