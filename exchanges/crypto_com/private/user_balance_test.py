import asyncio
import json
import logging
import websockets
from datetime import datetime, timezone
from redis_handler import RedisHandler
from exchanges.crypto_com.public.auth import get_auth, Authentication

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Global variable to track the last known user balance
last_user_balance = None


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
    global last_user_balance

    async for message in auth.websocket:
        response = json.loads(message)

        if response.get("method") == "public/heartbeat":
            logging.info("Received heartbeat, responding.")
            heartbeat_response = {
                "id": response["id"],
                "method": "public/respond-heartbeat",
            }
            await auth.websocket.send(json.dumps(heartbeat_response))
            logging.info("Sent heartbeat response.")
            continue

        if response.get("method") == "user.balance":
            current_user_balance = response["result"]["data"]
            logging.debug(f"Current user balance: {current_user_balance}")

            if current_user_balance != last_user_balance:
                last_user_balance = current_user_balance
                balance_data = json.dumps(response)
                logging.debug(f"Balance data to be stored in Redis: {balance_data}")

                redis_handler.set("user_balance", balance_data)
                logging.info(
                    f"Stored user balance in Redis at {datetime.now(timezone.utc).isoformat()}"
                )


async def start_user_balance_subscription(redis_handler: RedisHandler):
    auth = get_auth()
    await auth.connect()
    await auth.authenticate()

    await send_user_balance_subscription_request(auth)
    await handle_user_balance_updates(auth, redis_handler)
