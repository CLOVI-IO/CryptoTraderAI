from fastapi import FastAPI

# Include the new modules
from exchanges.crypto_com.public import auth
from exchanges.crypto_com.private import user_balance, create_order
from routes import (
    webhook,
    viewsignal,
    last_order,
    exchange,
    tradeguard,
)

#from routes.order import router as order  # Import the WebSocket router

app = FastAPI()

@app.get("/")
def hello_world():
    return {"message": "Hello, World!"}

# Include the route endpoints from other files
app.include_router(webhook.router)
app.include_router(viewsignal.router)
app.include_router(auth.router)
app.include_router(last_order.router)
app.include_router(exchange.router)
app.include_router(user_balance.router)
app.include_router(tradeguard.router)

#app.include_router(order, prefix="/ws")  # Include the WebSocket router with a prefix

# end of main.py
