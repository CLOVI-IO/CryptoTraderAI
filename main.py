from fastapi import FastAPI, Request, HTTPException
from typing import Optional
from pydantic import BaseModel
import uvicorn
import os
import redis
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

TRADINGVIEW_IPS = ["52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7"]

class Item(BaseModel):
    item_id: int
    q: Optional[str] = None

# Load Redis configuration from environment variables
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_db = os.getenv("REDIS_DB")
redis_password = os.getenv("REDIS_PASSWORD")

# Initialize Redis client
redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, password=redis_password)

def test_redis_connection():
    try:
        # Ping the Redis server to test the connection
        redis_client.ping()
        print("Connected to Redis")
        return True
    except redis.ConnectionError:
        print("Could not connect to Redis")
        return False

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
    redis_client.set('last_signal', request.json())
    return {"status": "ok"}

@app.get("/viewsignal")
def view_signal():
    try:
        last_signal = redis_client.get('last_signal')
        if last_signal:
            return {"signal": last_signal.decode('utf-8')}
        else:
            return {"signal": "No signal"}
    except Exception as e:
        print(f"An error occurred: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving the signal")


if __name__ == "__main__":
    if test_redis_connection():
        uvicorn.run(app, host="0.0.0.0", port=8000)
    else:
        print("Could not start the application because the Redis connection failed")
