# user_balance.py

from fastapi import APIRouter, WebSocket, BackgroundTasks, HTTPException, Depends
import asyncio
import time
import json
import logging
import websockets
from datetime import datetime, timezone
from exchanges.crypto_com.public.auth import get_auth, Authentication  # Import Authentication class
from redis_handler import RedisHandler
from custom_exceptions import UserBalanceException
from starlette.websockets import WebSocketDisconnect

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create an instance of RedisHandler
redis_handler = RedisHandler()

# Get the singleton instance of the Authentication class.
auth = Depends(get_auth)

# Define the FastAPI router
router = APIRouter()

# Set of connected WebSockets
connected_websockets = set()

@router.websocket("/ws/user_balance")
async def websocket_user_balance(websocket: WebSocket):
    """
    WebSocket endpoint to manage user balance connections.
    """
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)

async def send_user_balance_request(auth):
    """
    Sends a user balance request to the WebSocket API.
    """
    method = "private/user-balance"
    nonce = str(int(time.time() * 1000))
    id = int(nonce)

    request = {
        "id": id,
        "method": method,
        "params": {},
        "nonce": nonce,
    }

    logging.info(f"Sending request at {datetime.now(timezone.utc).isoformat()}: {request}")
    await auth.send_request(method, request["params"])
    return id, request

async def fetch_user_balance(auth: Authentication, retries=3, delay=5, max_recv_attempts=5, recv_timeout=30):
    """
    Fetches user balance with retries and error handling.
    """
    # Authenticate if not already authenticated
    if not auth.authenticated:
        logging.info("Authenticating...")
        await auth.authenticate()

    start_time = datetime.now(timezone.utc)
    while retries > 0:
        try:
            request_id, request = await send_user_balance_request(auth)
            break  # If request sent successfully, break the loop
        except Exception as e:
            if retries == 1:
                end_time = datetime.now(timezone.utc)
                latency = (end_time - start_time).total_seconds()
                logging.error(f"Error occurred. Latency: {latency}s. Exception: {str(e)}")
                raise e  # Re-raise the exception after all attempts exhausted
            retries -= 1
            await asyncio.sleep(delay)  # Wait before next attempt

    recv_attempts = 0
    while recv_attempts < max_recv_attempts:
        recv_attempts += 1
        try:
            response = await asyncio.wait_for(auth.websocket.recv(), timeout=recv_timeout)
        except asyncio.TimeoutError:
            logging.error("Timeout error while waiting for response.")
            raise UserBalanceException("Timeout error while waiting for response")
        except websockets.exceptions.ConnectionClosedOK:
            logging.warning("WebSocket connection closed, attempting to reconnect...")
            await auth.connect()  # Reconnect
            request_id, request = await send_user_balance_request(auth)  # Resend request
            continue
        except Exception as e:
            logging.error(f"Error while receiving response: {str(e)}")
            raise UserBalanceException(f"Error while receiving response: {str(e)}")

        try:
            response = json.loads(response)
        except json.JSONDecodeError:
            logging.error(f"Invalid JSON response: {response}")
            raise UserBalanceException("Invalid JSON response")

        logging.debug(f"Received response at {datetime.now(timezone.utc).isoformat()}: {response}")

        if "method" in response and response["method"] == "public/heartbeat":
            logging.info("Received heartbeat, continuing to wait for actual response.")
            continue  # Ignore the heartbeat message and keep waiting for the actual response

        if "id" in response and response["id"] == request_id:
            if "code" in response and response["code"] == 0:
                # Store user balance in Redis
                redis_handler.redis_client.set("user_balance", json.dumps(response))
                logging.info(f"Stored user balance in Redis at {datetime.now(timezone.utc).isoformat()}.")
                # Retrieve stored data for debugging purposes
                user_balance_redis = redis_handler.redis_client.get("user_balance")
                logging.debug(f"Retrieved from Redis at {datetime.now(timezone.utc).isoformat()}: {user_balance_redis}")
                end_time = datetime.now(timezone.utc)
                latency = (end_time - start_time).total_seconds()
                return {
                    "message": "Successfully fetched user balance",
                    "balance": response["result"]["data"],
                    "timestamp": start_time.isoformat(),
                    "latency": f"{latency} seconds",
                }
            else:
                end_time = datetime.now(timezone.utc)
                latency = (end_time - start_time).total_seconds()
                logging.error(f"Response code error. Expected code: 0, Actual code: {response.get('code')}, Full Response: {response}, Latency: {latency}s")
                raise UserBalanceException("Response code error")
        logging.error(f"Response id does not match request id. Request id: {request_id}, Request: {request}, Response: {response}")
        # If it reached here, it means that the response id did not match the request id, which is an error
        raise UserBalanceException("Response id does not match request id")

    logging.error(f"Failed to receive the expected response after {recv_attempts} attempts. The last response: {response}")
    # If it reached here, it means that the expected response was not received after all attempts
    raise UserBalanceException("Failed to receive the expected response after all attempts")

@router.get("/user_balance")
async def get_user_balance(background_tasks: BackgroundTasks, auth: Authentication = Depends(get_auth)):
    """
    Endpoint to fetch user balance.
    """
    start_time = datetime.now(timezone.utc)
    user_balance_redis = redis_handler.redis_client.get("user_balance")
    end_time = datetime.now(timezone.utc)
    latency = (end_time - start_time).total_seconds()
    if user_balance_redis is None:
        background_tasks.add_task(fetch_user_balance, auth)
        return {
            "message": "Started fetching user balance",
            "timestamp": start_time.isoformat(),
            "latency": f"{latency} seconds",
        }
    else:
        return {
            "message": "Successfully fetched user balance",
            "balance": json.loads(user_balance_redis),
            "timestamp": end_time.isoformat(),
            "latency": f"{latency} seconds",
        }
