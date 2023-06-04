# viewsignal.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from dotenv import load_dotenv, find_dotenv
import os
import json
from redis_handler import RedisHandler  # import RedisHandler

# load dotenv in the root dir
load_dotenv(find_dotenv())

router = APIRouter()


@router.get("/viewsignal")
def view_signal():
    try:
        redis_handler = RedisHandler()  # create RedisHandler instance
        r = redis_handler.redis_client  # access redis client from RedisHandler
        last_signal = r.get("last_signal")
        if last_signal is None:
            print("No signal found in Redis")
            return {"signal": "No signal"}
        else:
            signal = json.loads(last_signal)  # Convert JSON string to Python object
            print(f"Retrieved signal from Redis: {signal}")
            return {"signal": signal}
    except Exception as e:
        print(f"Failed to retrieve signal: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An error occurred while retrieving the signal"},
        )
