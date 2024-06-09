import os
from fastapi import FastAPI, Request, Response
from routes import webhook, viewsignal, order, exchange, last_order
from exchanges.crypto_com.private import user_balance
from exchanges.crypto_com.public import auth
from models import Payload
from redis_handler import RedisHandler
import json
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()


# Middleware to add ngrok-skip-browser-warning header
@app.middleware("http")
async def add_ngrok_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response


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

# Create RedisHandler instance and subscribe to the Redis channel 'last_signal'
redis_handler = RedisHandler(
    host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD, db=REDIS_DB
)
redis_client = redis_handler.redis_client
pubsub = redis_client.pubsub()
pubsub.subscribe("last_signal")
logging.info("Order: Subscribed to 'last_signal' channel")


# Add a task that runs in the background after startup
@app.on_event("startup")
async def startup_event():
    while True:
        message = pubsub.get_message()
        if message and message["type"] == "message":
            last_signal = Payload(**json.loads(message["data"]))
            logging.info(
                f"Order: Received last_signal from Redis channel: {last_signal}"
            )
            app.state.last_signal = last_signal  # update last_signal in the app state


@app.get("/")
def hello_world():
    return {"message": "Hello, World!"}


# Include the route endpoints from other files
app.include_router(auth.router)
app.include_router(webhook.router)
app.include_router(viewsignal.router)
app.include_router(order.router)
app.include_router(last_order.router)
app.include_router(exchange.router)
app.include_router(user_balance.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
