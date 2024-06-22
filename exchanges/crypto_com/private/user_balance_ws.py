import asyncio
import time
import json
import logging
import websockets
from datetime import datetime, timezone
from fastapi import APIRouter, WebSocket
from redis_handler import RedisHandler
from custom_exceptions import UserBalanceException
from starlette.websockets import WebSocketDisconnect
from exchanges.crypto_com.public.auth import get_auth, Authentication

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create an instance of RedisHandler
redis_handler = RedisHandler()

# Define the FastAPI router
router = APIRouter()

# Set of connected WebSockets
connected_websockets = set()

# To track the last known user balance
last_user_balance = None

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

async def send_user_balance_subscription_request(auth):
    """Send user balance subscription request via WebSocket"""
    method = "subscribe"
    nonce = str(int(time.time() * 1000))
    id = int(nonce)
    params = {
        "channels": ["user.balance"]
    }

    request = {
        "id": id,
        "method": method,
        "params": params,
        "nonce": nonce,
    }

    logging.info(f"Sending subscription request at {datetime.now(timezone.utc).isoformat()}: {request}")
    await auth.send_request(method, params)
    return id, request

async def handle_user_balance_updates(auth: Authentication):
    """Handle user balance updates received via WebSocket"""
    global last_user_balance

    while True:
        try:
            response = await auth.websocket.recv()
            response = json.loads(response)

            if response.get("method") == "public/heartbeat":
                logging.info("Received heartbeat, responding.")
                heartbeat_response = {
                    "id": response["id"],
                    "method": "public/respond-heartbeat"
                }
                await auth.websocket.send(json.dumps(heartbeat_response))
                logging.info("Sent heartbeat response.")
                continue

            if response.get("method") == "user.balance":
                current_user_balance = response["result"]["data"]
                
                if current_user_balance != last_user_balance:
                    last_user_balance = current_user_balance
                    try:
                        balance_data = json.dumps(response)
                        redis_handler.redis_client.set("user_balance", balance_data)
                        logging.info(f"Stored user balance in Redis at {datetime.now(timezone.utc).isoformat()}: {balance_data}")
                        user_balance_redis = redis_handler.redis_client.get("user_balance")
                        logging.debug(f"Retrieved from Redis at {datetime.now(timezone.utc).isoformat()}: {user_balance_redis}")
                    except Exception as e:
                        logging.error(f"Failed to write to Redis: {e}")

                    # Notify connected WebSocket clients
                    for ws in connected_websockets:
                        await ws.send_text(json.dumps(response))
                else:
                    logging.info("Received user balance update but no change detected.")
                continue

            logging.debug(f"Received non-heartbeat and non-user.balance message: {response}")
        except websockets.ConnectionClosed as e:
            logging.error(f"WebSocket connection closed: {e}")
            break
        except Exception as e:
            logging.error(f"Error during WebSocket handling: {e}")
            break

async def fetch_user_balance(auth: Authentication, retries=3, delay=5):
    """Fetch user balance with retries and error handling"""
    attempt = 0
    while attempt < retries:
        try:
            # Re-authenticate and create a new WebSocket connection each time
            logging.info("Authenticating and creating a new WebSocket connection...")
            await auth.connect()
            await auth.authenticate()

            await send_user_balance_subscription_request(auth)
            await handle_user_balance_updates(auth)

            return
        except Exception as e:
            logging.error(f"Error in fetch_user_balance: {e}")
            attempt += 1
            await asyncio.sleep(delay)

    logging.error(f"Failed to receive the expected response after {retries} attempts.")
    raise UserBalanceException("Failed to receive the expected response after all attempts")

# Function to start user balance subscription
async def start_user_balance_subscription(redis_handler: RedisHandler):
    auth = get_auth()
    await fetch_user_balance(auth)
