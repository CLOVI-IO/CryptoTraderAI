from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json
import uvicorn

# Load environment variables
load_dotenv()

app = FastAPI()

# Global variable to store the last signal
last_signal = None

class Signal(BaseModel):
    symbol: str
    close: float
    volume: float
    interval: str
    strategy: str

class Orders(BaseModel):
    take_profit: float
    stop_loss: float

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.post("/webhook")
async def webhook(request: Request):
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
def place_order(signal: Signal):
    try:
        global last_signal
        
        if last_signal:
            # Use the last_signal to format the JSON output in the desired format
            # Replace the following placeholder code with your actual implementation
            symbol = last_signal['symbol']
            close = last_signal['close']
            volume = last_signal['volume']
            interval = last_signal['interval']
            strategy = last_signal['strategy']
            
            api_format = {
                "symbol": symbol,
                "price": close,
                "quantity": volume,
                "interval": interval,
                "strategy": strategy
            }
            
            return api_format
        else:
            raise HTTPException(status_code=404, detail="No signal available")
    except Exception as e:
        print(f"Failed to format order: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while formatting the order")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
