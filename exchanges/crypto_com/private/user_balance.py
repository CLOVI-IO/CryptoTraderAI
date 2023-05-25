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
    start_time = time.time()  # Save the start time

    # authenticate when required
    if not auth.authenticated:
        print("Authenticating...")
        await auth.authenticate()

    nonce = str(int(time.time() * 1000))
    method = "private/get-account-summary"
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

    end_time = time.time()  # Save the end time
    latency = end_time - start_time  # Calculate the difference, which is the latency
    print(f"Latency for fetch_user_balance: {latency} seconds")  # Print the latency

    if "id" in response and response["id"] == id:
        if "code" in response and response["code"] == 0:
            # Store user balance in Redis
            redis_handler.redis_client.set("user_balance", json.dumps(response))
            print("Stored user balance in Redis.")
            # Retrieve stored data for debugging purposes
            user_balance_redis = redis_handler.redis_client.get("user_balance")
            print(f"Retrieved from Redis: {user_balance_redis}")
            return response, latency
        else:
            raise Exception(f"Error fetching user balance. Response: {response}")

    raise Exception(
        f"Response id does not match request id. Request id: {id}, Response: {response}"
    )


@router.post("/exchanges/crypto_com/private/user_balance")
async def get_user_balance():
    try:
        response, latency = await fetch_user_balance()
        return {"response": response, "latency": latency}
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user balance. Error: {str(e)}"
        )
