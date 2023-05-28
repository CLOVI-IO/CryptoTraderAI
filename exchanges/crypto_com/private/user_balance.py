from fastapi import APIRouter, HTTPException
import asyncio
import time
import json
import logging
from exchanges.crypto_com.public.auth import Authentication
from redis_handler import RedisHandler
from custom_exceptions import UserBalanceException

# Create an instance of RedisHandler
redis_handler = RedisHandler()

auth = Authentication()

router = APIRouter()

logging.basicConfig(level=logging.INFO)


async def send_user_balance_request():
    method = "private/user-balance"
    nonce = str(int(time.time() * 1000))
    id = int(nonce)

    request = {
        "id": id,
        "method": method,
        "params": {},
        "nonce": nonce,
    }

    logging.info("Sending request: %s", request)
    await auth.send_request(method)
    return id, request


async def fetch_user_balance(retries=3, delay=5):
    # authenticate when required
    if not auth.authenticated:
        logging.info("Authenticating...")
        await auth.authenticate()

    while retries > 0:
        try:
            request_id, request = await send_user_balance_request()
            break  # if request sent successfully, break the loop
        except Exception as e:
            if retries == 1:
                raise e  # re-raise the exception after all attempts exhausted
            retries -= 1
            await asyncio.sleep(delay)  # wait before next attempt

    while True:
        try:
            response = await asyncio.wait_for(auth.websocket.recv(), timeout=10)
        except asyncio.TimeoutError:
            logging.error("Timeout error while waiting for response.")
            raise UserBalanceException("Timeout error while waiting for response")
        except Exception as e:
            logging.error(f"Error while receiving response: {str(e)}")
            raise UserBalanceException(f"Error while receiving response: {str(e)}")

        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON response: {response}")
            raise UserBalanceException("Invalid JSON response")

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
                    "Response id does not match request id. Expected: %s, Actual: %s, Full Response: %s",
                    request_id,
                    response.get("id"),
                    response,
                )
                raise UserBalanceException("Response id does not match request id")
        logging.error(
            "Response id does not match request id. Request id: %s, Request: %s, Response: %s",
            request_id,
            request,
            response,
        )
        raise UserBalanceException("Response id does not match request id")


@router.post("/exchanges/crypto_com/private/user_balance")
async def get_user_balance():
    try:
        response = await fetch_user_balance()
        return {"response": response}
    except UserBalanceException as e:
        logging.error("Failed to get user balance. Error: %s", str(e))
        raise HTTPException(
            status_code=500, detail=f"Failed to get user balance. Error: {str(e)}"
        )


if __name__ == "__main__":
    result = asyncio.run(fetch_user_balance())
    print(result)
