import os
import asyncio
import json
from fastapi import FastAPI
from routes import webhook, viewsignal, order, exchange, last_order
from routes.tradeguard import subscribe_to_last_order
from exchanges.crypto_com.private.user_balance_ws import start_user_balance_subscription
from redis_handler import RedisHandler
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

app = FastAPI()

# Get Redis connection details from environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Create a shared RedisHandler instance
redis_handler = RedisHandler(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB
)

# Initialize last_signal in the application state
app.state.last_signal = None

# Include the route endpoints from other files
app.include_router(webhook.router)
app.include_router(viewsignal.router)
app.include_router(order.router)
app.include_router(last_order.router)
app.include_router(exchange.router)


@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(
        subscribe_to_last_order(redis_handler)
    )  # Pass the RedisHandler instance
    loop.create_task(
        start_user_balance_subscription(redis_handler)
    )  # Pass the RedisHandler instance


if __name__ == "__main__":
    import uvicorn

    logging.info("Starting Uvicorn server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
