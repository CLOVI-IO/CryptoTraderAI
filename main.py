# main.py
from fastapi import FastAPI, WebSocket, BackgroundTasks
from routes import webhook, viewsignal, order, exchange, last_order
from exchanges.crypto_com.private import user_balance
from exchanges.crypto_com.public import auth
from models import Payload
from redis_handler import RedisHandler
import json
import logging

app = FastAPI()

# Initialize last_signal in the application state
app.state.last_signal = None

# Create RedisHandler instance and subscribe to the Redis channel 'last_signal'
redis_handler = RedisHandler()
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
