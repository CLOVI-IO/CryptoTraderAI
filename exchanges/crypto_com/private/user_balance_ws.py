import asyncio
import json
import logging
import time
import websockets
from datetime import datetime, timezone
from redis_handler import RedisHandler
from exchanges.crypto_com.public.auth import get_auth

# Configure logging
logging.basicConfig(level=logging.DEBUG)


async def send_user_balance_subscription_request(auth):
    """Send user balance subscription request via WebSocket"""
    method = "subscribe"
    nonce = str(int(time.time() * 1000))
    params = {"channels": ["user.balance"]}

    request = {
        "id": int(nonce),
        "method": method,
        "params": params,
        "nonce": nonce,
    }

    logging.info(
        f"Sending subscription request at {datetime.now(timezone.utc).isoformat()}: {request}"
    )
    await auth.websocket.send(json.dumps(request))


async def handle_user_balance_updates(auth, redis_handler):
    """Handle user balance updates received via WebSocket"""
    while True:
        try:
            response = await auth.websocket.recv()
            logging.debug(f"Received WebSocket message: {response}")
            response_data = json.loads(response)

            if (
                response_data.get("method") == "subscribe"
                and response_data.get("result")
                and response_data["result"].get("subscription") == "user.balance"
            ):
                logging.info(f"User balance update received: {response_data}")
                balance_data = json.dumps(response_data["result"]["data"])
                redis_handler.set("user_balance", balance_data)
                logging.info(f"User balance data written to Redis: {balance_data}")
            elif response_data.get("method") == "public/heartbeat":
                # Handle heartbeat messages to keep the connection alive
                heartbeat_id = response_data["id"]
                await auth.websocket.send(
                    json.dumps(
                        {"id": heartbeat_id, "method": "public/respond-heartbeat"}
                    )
                )
                logging.info(f"Sent heartbeat response for id {heartbeat_id}.")
            else:
                logging.debug(f"Non-user.balance message received: {response_data}")

        except websockets.ConnectionClosed as e:
            logging.error(f"WebSocket connection closed: {e}")
            break
        except Exception as e:
            logging.error(f"Error in WebSocket handling: {e}")
            break


async def start_user_balance_subscription(redis_handler):
    while True:
        try:
            auth = get_auth()
            await auth.connect()
            await auth.authenticate()
            await send_user_balance_subscription_request(auth)
            await handle_user_balance_updates(auth, redis_handler)
        except Exception as e:
            logging.error(f"Error in WebSocket connection: {e}")
            logging.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
