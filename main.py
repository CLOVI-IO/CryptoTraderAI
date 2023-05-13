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
    return {"Hello": "World!"}

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

@app.get("/orders/{symbol}")
def get_orders(symbol: str):
    try:
        # Perform logic to calculate take-profit and stop-loss orders based on the symbol and Crypto.com exchange
        # Replace the following placeholder code with your actual implementation
        take_profit = calculate_take_profit(symbol)
        stop_loss = calculate_stop_loss(symbol)
        
        orders = Orders(take_profit=take_profit, stop_loss=stop_loss)
        
        return orders.dict()
    except Exception as e:
        print(f"Failed to calculate orders: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while calculating orders")

def calculate_take_profit(symbol: str) -> float:
    # Implement your logic to calculate the take-profit based on the symbol and Crypto.com exchange
    # You can use an API or library to fetch the necessary data and calculate the take-profit price
    # Replace the placeholder code below with your actual implementation
    return 1.03 * last_signal['close']  # 3% take-profit

def calculate_stop_loss(symbol: str) -> float:
    # Implement your logic to calculate the stop-loss based on the symbol and Crypto.com exchange
    # You can use an API or library to fetch the necessary data and calculate the stop-loss price
    # Replace the placeholder code below with your actual implementation
    return 0.97 * last_signal['close']  # 3% stop-loss

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
