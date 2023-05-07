from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import os
import redis

# Load environment variables
load_dotenv()

app = FastAPI()

# List of allowed TradingView IPs
TRADINGVIEW_IPS = ["52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7"]

# Retrieve Redis connection parameters from environment variables
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_db = os.getenv("REDIS_DB")
redis_password = os.getenv("REDIS_PASSWORD")

# Initialize Redis client and verify connection
try:
    redis_client = redis.Redis(host=redis_host, port=int(redis_port), db=int(redis_db), password=redis_password)
    if redis_client.ping():
        print(f"Connected to Redis server at {redis_host}:{redis_port}")
except Exception as e:
    print(f"Failed to connect to Redis server: {e}")

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/webhook")
def webhook(request: Request):
    client_host = request.client.host
    if client_host not in TRADINGVIEW_IPS:
        raise HTTPException(status_code=403, detail="Access denied")
    # Store the signal in Redis
    try:
        redis_client.set('last_signal', request.json())
        return {"status": "ok"}
    except Exception as e:
        print(f"Failed to store signal in Redis: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while storing the signal")

@app.get("/viewsignal")
def view_signal():
    try:
        last_signal = redis_client.get('last_signal')
        if last_signal:
            return {"signal": last_signal.decode('utf-8')}
        else:
            return {"signal": "No signal"}
    except Exception as e:
        print(f"Failed to retrieve signal from Redis: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving the signal")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
