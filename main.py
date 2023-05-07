from typing import Optional, Union
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import uvicorn
from werkzeug.security import check_password_hash
from flask import Flask, request
from dotenv import load_dotenv
import os
import redis

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

TRADINGVIEW_IPS = ["52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7"]

# Connect to Redis
r = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=0)

class Item(BaseModel):
    item_id: int
    q: Optional[str] = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.post("/webhook")
def webhook(request: Request):
    client_host = request.client.host
    if client_host not in TRADINGVIEW_IPS:
        raise HTTPException(status_code=403, detail="Access denied")
    # Store the signal in Redis
    r.set("signal", request.json())
    return {"status": "ok"}

@app.get("/viewsignal")
def view_signal():
    # Fetch the signal from Redis
    signal = r.get("signal")
    if signal is None:
        return {"signal": "No signal"}
    else:
        return {"signal": signal.decode("utf-8")}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
