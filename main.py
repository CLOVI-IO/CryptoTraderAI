import os
import asyncio
from fastapi import FastAPI
from routes import webhook, viewsignal, order, exchange, last_order, tradeguard
from exchanges.crypto_com.private import user_balance_ws
from redis_handler import RedisHandler
import logging
from dotenv import load_dotenv
import json
from workers.websocket_manager import WebSocketManager

load_dotenv()

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))

redis_handler = RedisHandler(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB
)

app.state.last_signal = None

# Include routers
app.include_router(webhook.router)
app.include_router(viewsignal.router)
app.include_router(order.router)
app.include_router(last_order.router)
app.include_router(exchange.router)
app.include_router(tradeguard.router)


async def listen_to_redis():
    pubsub = redis_handler.redis_client.pubsub()
    pubsub.subscribe("last_signal", "user_balance")
    logging.info("Subscribed to 'last_signal' and 'user_balance' channels")

    while True:
        message = pubsub.get_message()
        if message and message["type"] == "message":
            try:
                channel = (
                    message["channel"].decode("utf-8")
                    if isinstance(message["channel"], bytes)
                    else message["channel"]
                )
                data = (
                    message["data"].decode("utf-8")
                    if isinstance(message["data"], bytes)
                    else message["data"]
                )
                logging.info(f"Received message from {channel}: {data}")
                if channel == "last_signal":
                    last_signal = json.loads(data)
                    logging.info(f"Processed last_signal: {last_signal}")
                    app.state.last_signal = last_signal
                elif channel == "user_balance":
                    user_balance = json.loads(data)
                    logging.info(f"Processed user_balance: {user_balance}")
            except Exception as e:
                logging.error(f"Error processing Redis message: {e}")
        await asyncio.sleep(0.1)


@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(listen_to_redis())
    loop.create_task(user_balance_ws.start_user_balance_subscription(redis_handler))
    loop.create_task(tradeguard.subscribe_to_last_signal())

    # Start WebSocketManager for handling Crypto.com API WebSocket
    websocket_manager = WebSocketManager()
    loop.create_task(websocket_manager.run(["user.order"]))


if __name__ == "__main__":
    import uvicorn

    logging.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
