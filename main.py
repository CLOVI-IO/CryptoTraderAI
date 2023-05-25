from fastapi import FastAPI
from dotenv import load_dotenv
import os
import uvicorn

# Include the new modules
from exchanges.crypto_com.private import user_balance, create_order
from routes import (
    webhook,
    viewsignal,
    order,
    last_order,
    exchange,
    tradeguard,
)  # Import tradeguard here

# Load environment variables
load_dotenv()

app = FastAPI()


@app.get("/")
def hello_world():
    return {"message": "Hello, World!"}


# Include the route endpoints from other files
app.include_router(webhook.router)
app.include_router(viewsignal.router)
app.include_router(order.router)
app.include_router(last_order.router)
app.include_router(exchange.router)
app.include_router(user_balance.router)
app.include_router(tradeguard.router)  # Add tradeguard router here
app.include_router(create_order.router)  # Add create_order router here


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
