from fastapi import FastAPI, Request, HTTPException
from typing import Optional, Union
from pydantic import BaseModel
import uvicorn
from werkzeug.security import check_password_hash
from flask import Flask, request
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

TRADINGVIEW_IPS = ["52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7"]

class Item(BaseModel):
    item_id: int
    q: Optional[str] = None

# Initialize the last_signal as an empty dictionary
last_signal = {}

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

@app.post("/webhook")
async def webhook(request: Request):
    # client_host = request.client.host
    # if client_host not in TRADINGVIEW_IPS:
    #     raise HTTPException(status_code=403, detail="Access denied")
    
    # Update the global variable with the new signal
    global last_signal
    last_signal = await request.json()
    return {"status": "ok"}

@app.get("/viewsignal")
def view_signal():
    # Here you would typically fetch the signal from your database or other data source
    # Now it returns the last signal received
    return last_signal

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
