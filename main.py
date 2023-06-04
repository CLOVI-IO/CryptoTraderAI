# main.py

from fastapi import FastAPI
from dotenv import load_dotenv
import os
import uvicorn

from routes import webhook, viewsignal, order, exchange

#from routes.order import router as order  # Import the WebSocket router

app = FastAPI()

# Initialize last_signal in the application state
app.state.last_signal = None


@app.get("/")
def hello_world():
    return {"message": "Hello, World!"}

# Include the route endpoints from other files
app.include_router(webhook.router)
app.include_router(viewsignal.router)
app.include_router(order.router)
app.include_router(exchange.router)

# end of main.py
