# last_order.py

from fastapi import APIRouter, HTTPException, Depends
from .auth import get_auth, Authentication
import os
import json
import redis

router = APIRouter()


@router.get("/last_order")
async def get_last_order(auth: Authentication = Depends(get_auth)):
    try:
        response = await auth.send_request(
            "private/get-order-detail", params={"order_id": "your_order_id"}
        )

        REDIS_HOST = os.getenv("REDIS_HOST")
        REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
        r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

        r.set("last_order", json.dumps(response))

        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
