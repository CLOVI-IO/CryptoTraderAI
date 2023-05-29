from fastapi import APIRouter, HTTPException
import os
import json
import redis

router = APIRouter()


@router.get("/last_order")
async def get_last_order():
    try:
        REDIS_HOST = os.getenv("REDIS_HOST")
        REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
        r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

        last_order = json.loads(r.get("last_order"))

        return last_order

    except Exception as e:
        print(f"Failed to get last order. Error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get last order: {str(e)}"
        )
