# Import necessary libraries
from fastapi import FastAPI, Request, HTTPException
from typing import Optional
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import os
import redis

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Define allowed IPs for TradingView
TRADINGVIEW_IPS = ["52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7"]

# Define data model for items
class Item(BaseModel):
    item_id: int
    q: Optional[str] = None

# Load Redis configuration from environment variables
redis_host = os.getenv("REDIS_HOST")
redis_port = os.getenv("REDIS_PORT")
redis_db = os.getenv("REDIS_DB")
redis_password = os.getenv("REDIS_PASSWORD")

# Initialize Redis client
try:
    redis_client = redis.Redis(host=redis_host, port=redis_port, db=redis_db, password=redis_password)
    print("Connected to Redis")
except Exception as e:
    print(f"Failed to connect to Redis: {e}")

# Define root endpoint
@app.get("/")
def read_root():
    return {"Hello": "World"}

# Define item endpoint
@app.get("/items/{item_id}")
def read_item(item_id: int, q: Optional[str] = None):
    return {"item_id": item_id, "q": q}

# Define webhook endpoint for TradingView signals
@app.post("/webhook")
def webhook(request: Request):
    client_host = request.client.host
    if client_host not in TRADINGVIEW_IPS:
        raise HTTPException(status_code=403, detail="Access denied")
    # Store the signal in Redis
    try:
        redis_client.set('last_signal', request.json())
        print("Stored signal in Redis")
    except Exception as e:
        print(f"Failed to store signal in Redis: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while storing the signal")
    return {"status": "ok"}

# Define endpoint to view the last signal
@app.get("/viewsignal")
def view_signal():
    try:
        # Try to get the last signal from Redis
        last_signal = redis_client.get('last_signal')
        if last_signal is None:
            # If the key does not exist, return a custom error message
            return {"detail": "No signal found in Redis"}
        else:
            # If the key exists, decode the value and return it
            return {"signal": last_signal.decode('utf-8')}
    except redis.exceptions.ConnectionError:
        # If there's a connection error, return a custom error message
        return {"detail": "Error connecting to Redis"}
    except Exception as e:
        # If there's any other exception, return a custom error message
        return {"detail": f"An unexpected error occurred: {str(e)}"}


# Run the server if this script is run directly
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
