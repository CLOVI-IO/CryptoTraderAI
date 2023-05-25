from fastapi import APIRouter, HTTPException
import asyncio
import time
import json
import logging
from exchanges.crypto_com.public.auth import Authentication
from redis_handler import RedisHandler

auth = Authentication()
redis_handler = RedisHandler()
router = APIRouter()

logging.basicConfig(level=logging.INFO)


async def send_user_balance_request():
    nonce = str(int(time.time() * 1000))
    method = "private/user-balance"
    id = int(nonce)

    request = {
        "id": id,
        "method": method,
        "params": {},
        "nonce": nonce,
    }

    logging.info("Sending request: %s", request)
    await auth.send_request(request)
    return id, request


async def fetch_user_balance():
    # authenticate when required
    if not auth.authenticated:
        logging.info("Authenticating...")
        await auth.authenticate()

    request_id, request = await send_user_balance_request()

    while True:
        response = await auth.websocket.recv()
        response = json.loads(response)
        logging.debug("Received response: %s", response)

        if "id" in response and response["id"] == request_id:
            if "code" in response and response["code"] == 0:
                # Store user balance in Redis
                redis_handler.redis_client.set("user_balance", json.dumps(response))
                logging.info("Stored user balance in Redis.")
                # Retrieve stored data for debugging purposes
                user_balance_redis = redis_handler.redis_client.get("user_balance")
                logging.debug("Retrieved from Redis: %s", user_balance_redis)
                return {
                    "message": "Successfully fetched user balance",
                    "balance": response,
                }
            else:
                logging.error(
                    "Error fetching user balance. Request: %s, Response: %s",
                    request,
                    response,
                )
                raise Exception("Error fetching user balance")

        logging.error(
            "Response id does not match request id. Request id: %s, Request: %s, Response: %s",
            request_id,
            request,
            response,
        )
        raise Exception("Response id does not match request id")


@router.post("/exchanges/crypto_com/private/user_balance")
async def get_user_balance():
    try:
        start_time = time.time()  # Save the start time
        response = await fetch_user_balance()
        end_time = time.time()  # Save the end time
        latency = end_time - start_time
        logging.info(
            "Latency for get_user_balance: %s seconds", latency
        )  # Print the latency
        return {"response": response, "latency": latency}
    except Exception as e:
        logging.error("Failed to get user balance. Error: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get user balance. Error: {str(e)}"
        )
