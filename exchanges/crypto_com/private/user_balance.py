from fastapi import APIRouter, WebSocket, BackgroundTasks, Depends, HTTPException
import asyncio
import time
import json
import logging
import websockets
from datetime import datetime, timezone
from exchanges.crypto_com.public.auth import get_auth, Authentication
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
    """WebSocket endpoint for user balance"""
    await websocket.accept()
    connected_websockets.add(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        connected_websockets.remove(websocket)

async def send_user_balance_request(auth):
    """Send user balance request via WebSocket"""
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
    """Fetch user balance with retries and error handling"""
    if not auth.authenticated:
        logging.info("Authenticating...")
        await auth.authenticate()

    start_time = datetime.now(timezone.utc)
    attempt = 0
    request_id = None
    while attempt < retries:
        try:
            request_id, request = await send_user_balance_request(auth)
            break
        except Exception as e:
            if attempt == retries - 1:
                end_time = datetime.now(timezone.utc)
                latency = (end_time - start_time).total_seconds()
                logging.error(f"Error occurred. Latency: {latency}s. Exception: {str(e)}")
                raise e
            attempt += 1
            await asyncio.sleep(delay)

    recv_attempts = 0
    response = None
    while recv_attempts < max_recv_attempts:
        recv_attempts += 1
        try:
            response = await asyncio.wait_for(auth.websocket.recv(), timeout=recv_timeout)
            response = json.loads(response)
        except asyncio.TimeoutError:
            logging.error("Timeout error while waiting for response.")
            raise UserBalanceException("Timeout error while waiting for response")
        except websockets.exceptions.ConnectionClosedOK:
            logging.info("WebSocket connection closed after receiving valid response.")
            break
        except Exception as e:
            logging.error(f"Error while receiving response: {str(e)}")
            raise UserBalanceException(f"Error while receiving response: {str(e)}")

        logging.debug(f"Received response at {datetime.now(timezone.utc).isoformat()}: {response}")

        if "method" in response and response["method"] == "public/heartbeat":
            logging.info("Received heartbeat, ignoring.")
            continue

        if "id" in response and response["id"] == request_id:
            if "code" in response and response["code"] == 0:
                redis_handler.redis_client.set("user_balance", json.dumps(response))
                logging.info(f"Stored user balance in Redis at {datetime.now(timezone.utc).isoformat()}.")
                user_balance_redis = redis_handler.redis_client.get("user_balance")
                logging.debug(f"Retrieved from Redis at {datetime.now(timezone.utc).isoformat()}: {user_balance_redis}")
                end_time = datetime.now(timezone.utc)
                latency = (end_time - start_time).total_seconds()

                # Close the WebSocket connection after successfully receiving the response
                await auth.websocket.close()
                logging.info("WebSocket connection closed after receiving valid response.")

                # Return the balance
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

    if response:
        logging.error(f"Failed to receive the expected response after {recv_attempts} attempts. The last response: {response}")
    raise UserBalanceException("Failed to receive the expected response after all attempts")

@router.get("/user_balance")
async def get_user_balance(background_tasks: BackgroundTasks, auth: Authentication = Depends(get_auth)):
    """Get user balance and store in Redis if not already cached"""
    start_time = datetime.now(timezone.utc)
    user_balance_redis = redis_handler.redis_client.get("user_balance")
    end_time = datetime.now(timezone.utc)
    latency = (end_time - start_time).total_seconds()
    if user_balance_redis is None:
        logging.info("No cached user balance found. Starting background task to fetch user balance.")
        background_tasks.add_task(fetch_user_balance, auth)
        return {
            "message": "Started fetching user balance",
            "timestamp": start_time.isoformat(),
            "latency": f"{latency} seconds",
        }
    else:
        logging.info("User balance found in Redis.")
        logging.debug(f"User balance from Redis: {user_balance_redis}")
        return {
            "message": "Successfully fetched user balance",
            "balance": json.loads(user_balance_redis),
            "timestamp": end_time.isoformat(),
            "latency": f"{latency} seconds",
        }
