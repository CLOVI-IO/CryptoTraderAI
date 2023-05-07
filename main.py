from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from typing import Optional
import uvicorn
import os
import redis
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.

app = FastAPI()

TRADINGVIEW_IPS = ["52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7"]

# Load environment variables
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = os.getenv("REDIS_PORT")
REDIS_DB = os.getenv("REDIS_DB")
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

# Initialize Redis client
redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, password=REDIS_PASSWORD)

class TradingViewSignal(BaseModel):
    ticker: str
    exchange: str
    price: float
    time: str
    # Add more fields based on the payload from TradingView

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/webhook")
async def read_webhook_signal(signal: TradingViewSignal, request: Request, x_secret: Optional[str] = None):
    client_host = request.client.host
    if client_host not in TRADINGVIEW_IPS:
        raise HTTPException(status_code=403, detail="Access denied")

    # Store the signal in Redis
    redis_client.set('last_signal', signal.json())

    return {"status": "ok"}

@app.get("/viewsignal")
async def view_signal():
    last_signal = redis_client.get('last_signal')
    if last_signal is not None:
        last_signal = last_signal.decode('utf-8')
    return {"last_signal": last_signal}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
