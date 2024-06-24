import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from redis_handler import RedisHandler
from workers.websocket_manager import WebSocketManager

logger = logging.getLogger("user_balance_ws")


async def send_user_balance_subscription_request(manager):
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

    logger.info(
        f"Sending subscription request at {datetime.now(timezone.utc).isoformat()}: {request}"
    )
    await manager.send_request(method, params)


async def handle_user_balance_updates(manager, redis_handler):
    """Handle user balance updates received via WebSocket"""
    while True:
        try:
            response = await manager.websocket.recv()
            logger.debug(f"Received WebSocket message: {response}")
            response_data = json.loads(response)

            if (
                response_data.get("method") == "subscribe"
                and response_data.get("result")
                and response_data["result"].get("subscription") == "user.balance"
            ):
                logger.info(f"User balance update received: {response_data}")
                balance_data = json.dumps(response_data["result"]["data"])
                redis_handler.set("user_balance", balance_data)
                logger.info(f"User balance data written to Redis: {balance_data}")
            elif response_data.get("method") == "public/heartbeat":
                # Handle heartbeat messages to keep the connection alive
                heartbeat_id = response_data["id"]
                await manager.respond_heartbeat(heartbeat_id)
                logger.info(f"Sent heartbeat response for id {heartbeat_id}.")
            else:
                logger.debug(f"Non-user.balance message received: {response_data}")

        except websockets.ConnectionClosed as e:
            logger.error(f"WebSocket connection closed: {e}")
            break
        except Exception as e:
            logger.error(f"Error in WebSocket handling: {e}")
            break


async def start_user_balance_subscription(redis_handler):
    manager = WebSocketManager()
    while True:
        try:
            await manager.connect()
            await manager.authenticate()
            await send_user_balance_subscription_request(manager)
            await handle_user_balance_updates(manager, redis_handler)
        except Exception as e:
            logger.error(f"Error in WebSocket connection: {e}")
            logger.info("Reconnecting in 5 seconds...")
            await asyncio.sleep(5)
