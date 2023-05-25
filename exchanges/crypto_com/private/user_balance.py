# user_balance.py

from fastapi import APIRouter, HTTPException
import asyncio
import time
import json
from exchanges.crypto_com.public.auth import Authentication
from redis_handler import RedisHandler

auth = Authentication()
redis_handler = RedisHandler()

router = APIRouter()


async def fetch_user_balance():
    # authenticate when required
    if not auth.authenticated:
        print("Authenticating...")
        await auth.authenticate()

    nonce = str(int(time.time() * 1000))
    method = "private/user-balance"
    id = int(nonce)

    request = {
        "id": id,
        "method": method,
        "params": {},
        "nonce": nonce,
    }

    print("Sending request:", request)
    response = await auth.send_request(request)
    print("Received response:", response)

    if "id" in response and response["id"] == id:
        if "code" in response and response["code"] == 0:
            # Store user balance in Redis
            if response is not None:
                json_response = json.dumps(response)
                if json_response is not None:
                    redis_handler.redis_client.set("user_balance", json_response)
                    print("Stored user balance in Redis.")
                else:
                    print("json.dumps(response) returned None.")
            else:
                print("Response was None.")
            # Retrieve stored data for debugging purposes
            user_balance_redis = redis_handler.redis_client.get("user_balance")
            print(f"Retrieved from Redis: {user_balance_redis}")
            return response
        else:
            raise Exception("Error fetching user balance")

    raise Exception("Response id does not match request id")


@router.post("/exchanges/crypto_com/private/user_balance")
async def get_user_balance():
    try:
        response = await fetch_user_balance()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
