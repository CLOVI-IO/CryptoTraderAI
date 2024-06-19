# user_balance_ws.py

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
    # Re-authenticate and create a new WebSocket connection each time
    logging.info("Authenticating and creating a new WebSocket connection...")
    await auth.connect()
    await auth.authenticate()

    start_time = datetime.now(timezone.utc)
    request_id, request = await send_user_balance_request(auth)

    attempt = 0
    while attempt < retries:
        recv_attempts = 0
        while recv_attempts < max_recv_attempts:
            recv_attempts += 1
            try:
                response = await asyncio.wait_for(auth.websocket.recv(), timeout=recv_timeout)
            except asyncio.TimeoutError:
                logging.error("Timeout error while waiting for response.")
                raise UserBalanceException("Timeout error while waiting for response")
            except websockets.exceptions.ConnectionClosedOK:
                logging.info("WebSocket connection closed after receiving valid response.")
                return
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
                logging.info("Received heartbeat, responding.")
                heartbeat_response = {
                    "id": response["id"],
                    "method": "public/respond-heartbeat"
                }
                await auth.websocket.send(json.dumps(heartbeat_response))
                logging.info("Sent heartbeat response.")
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
            raise UserBalanceException("Response id does not match request id")

        attempt += 1
        await asyncio.sleep(delay)

    logging.error(f"Failed to receive the expected response after {recv_attempts} attempts. The last response: {response}")
    raise UserBalanceException("Failed to receive the expected response after all attempts")

# Ensure the WebSocket connection is kept alive with heartbeats
async def keep_websocket_alive(auth: Authentication):
    """Keep the WebSocket connection alive with heartbeats"""
    while True:
        try:
            if auth.websocket.open:
                # Wait to receive a message
                response = await asyncio.wait_for(auth.websocket.recv(), timeout=35)  # Wait for up to 35 seconds for a message
                response = json.loads(response)

                if response.get("method") == "public/heartbeat":
                    logging.info("Received heartbeat, responding.")
                    heartbeat_response = {
                        "id": response["id"],
                        "method": "public/respond-heartbeat"
                    }
                    await auth.websocket.send(json.dumps(heartbeat_response))
                    logging.info("Sent heartbeat response.")
                else:
                    logging.debug(f"Received non-heartbeat message: {response}")
            await asyncio.sleep(5)  # Check every 5 seconds for the next message
        except asyncio.TimeoutError:
            logging.error("Timeout waiting for heartbeat. Connection may be broken.")
            break
        except Exception as e:
            logging.error(f"Error during WebSocket keep-alive: {e}")
            break

# Background task to maintain WebSocket connection
@router.on_event("startup")
async def startup_event():
    auth = await get_auth()
    asyncio.create_task(keep_websocket_alive(auth))

@router.on_event("shutdown")
async def shutdown_event():
    for ws in connected_websockets:
        await ws.close()
