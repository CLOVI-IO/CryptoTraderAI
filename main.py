import os
import asyncio
from fastapi import FastAPI
from routes import webhook, viewsignal, order, exchange, last_order
from models import Payload
from redis_handler import RedisHandler
import json
import logging
from dotenv import load_dotenv
from exchanges.crypto_com.private.user_balance_ws import start_user_balance_subscription  # Ensure correct import

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

app = FastAPI()

# Initialize last_signal in the application state
app.state.last_signal = None

# Get Redis connection details from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Log the environment variables being used
logging.info(f"REDIS_HOST: {REDIS_HOST}")
logging.info(f"REDIS_PORT: {REDIS_PORT}")
logging.info(f"REDIS_PASSWORD: {'******' if REDIS_PASSWORD else 'None'}")
logging.info(f"REDIS_DB: {REDIS_DB}")

# Create RedisHandler instance and subscribe to the Redis channel 'last_signal' and 'user_balance'
redis_handler = RedisHandler(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB
)
redis_client = redis_handler.redis_client
pubsub = redis_client.pubsub()
pubsub.subscribe("last_signal", "user_balance")
logging.info("Subscribed to 'last_signal' and 'user_balance' channels")

async def listen_to_redis():
    while True:
        message = pubsub.get_message()
        if message and message["type"] == "message":
            channel = message["channel"].decode("utf-8") if isinstance(message["channel"], bytes) else message["channel"]
            data = message["data"].decode("utf-8") if isinstance(message["data"], bytes) else message["data"]
            logging.info(f"Received message from {channel}: {data}")
            if channel == "last_signal":
                last_signal = Payload(**json.loads(data))
                logging.info(f"Processed last_signal: {last_signal}")
                app.state.last_signal = last_signal  # update last_signal in the app state
            elif channel == "user_balance":
                user_balance = json.loads(data)
                logging.info(f"Processed user_balance: {user_balance}")
                # Process user balance as needed
        await asyncio.sleep(0.1)

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(listen_to_redis())
    loop.create_task(start_user_balance_subscription(redis_handler))  # Pass redis_handler to start_user_balance_subscription

# Include the route endpoints from other files
app.include_router(webhook.router)
app.include_router(viewsignal.router)
app.include_router(order.router)
app.include_router(last_order.router)
app.include_router(exchange.router)

if __name__ == "__main__":
    import uvicorn

    logging.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
