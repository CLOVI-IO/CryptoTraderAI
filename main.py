from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = FastAPI()

# List of allowed TradingView IPs
TRADINGVIEW_IPS = ["52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7"]

# Initialize global variable for storing the last signal
last_signal = None

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/webhook")
def webhook(request: Request):
    global last_signal
    client_host = request.client.host
    if client_host not in TRADINGVIEW_IPS:
        raise HTTPException(status_code=403, detail="Access denied")
    # Store the signal in the global variable
    try:
        last_signal = request.json()
        return {"status": "ok"}
    except Exception as e:
        print(f"Failed to store signal: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while storing the signal")

@app.get("/viewsignal")
def view_signal():
    global last_signal
    try:
        if last_signal:
            return {"signal": last_signal}
        else:
            return {"signal": "No signal"}
    except Exception as e:
        print(f"Failed to retrieve signal: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving the signal")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
