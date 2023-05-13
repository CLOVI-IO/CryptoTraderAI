from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import uvicorn
from dotenv import load_dotenv
import os
import json

load_dotenv()

app = FastAPI()

TRADINGVIEW_IPS = ["52.89.214.238", "34.212.75.30", "54.218.53.128", "52.32.178.7"]

last_signal = None

class Signal(BaseModel):
    symbol: str
    close: str
    volume: str
    interval: str
    strategy: str

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/webhook")
async def webhook(request: Request):
    client_host = request.client.host
    if client_host not in TRADINGVIEW_IPS:
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        global last_signal
        last_signal = await request.json()
        print(f"Received signal: {json.dumps(last_signal, indent=2)}")
        return {"status": "ok"}
    except Exception as e:
        print(f"Failed to store signal: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while storing the signal")

@app.get("/viewsignal")
def view_signal():
    try:
        global last_signal
        print(f"Retrieving signal: {json.dumps(last_signal, indent=2)}")
        if last_signal:
            return {"signal": last_signal}
        else:
            return {"signal": "No signal"}
    except Exception as e:
        print(f"Failed to retrieve signal: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving the signal")

@app.post("/order")
def create_order(signal: Signal):
    global last_signal
    last_signal = signal
    formatted_output = {
        "symbol": last_signal.symbol,
        "close": last_signal.close,
        "volume": last_signal.volume,
        "interval": last_signal.interval,
        "strategy": last_signal.strategy,
        "take_profit": calculate_take_profit(last_signal),
        "stop_loss": calculate_stop_loss(last_signal)
    }
    return formatted_output

def calculate_take_profit(signal: Signal):
    # Implement your logic to calculate the take-profit value
    # based on the signal information
    return "<calculated_take_profit>"

def calculate_stop_loss(signal: Signal):
    # Implement your logic to calculate the stop-loss value
    # based on the signal information
    return "<calculated_stop_loss>"

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
