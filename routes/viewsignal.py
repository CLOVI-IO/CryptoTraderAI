# viewsignal.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from dotenv import load_dotenv, find_dotenv
import os
import json
import redis

# load dotenv in the root dir
load_dotenv(find_dotenv())

router = APIRouter()


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


@router.get("/viewsignal")
def view_signal():
    redis_client = connect_to_redis()
    if redis_client is None:
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to connect to Redis"},
        )
    try:
        last_signal = redis_client.get("last_signal")
        if last_signal is not None:
            signal = json.loads(
                last_signal.decode()
            )  # Convert JSON string to Python object
            print(f"Retrieved signal from Redis: {signal}")
            return {"signal": signal}
        else:
            print("No signal found in Redis")
            return {"signal": "No signal"}
    except Exception as e:
        print(f"Failed to retrieve signal: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An error occurred while retrieving the signal"},
        )
