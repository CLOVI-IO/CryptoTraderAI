from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi import FastAPI
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

router = APIRouter()
tradingview_ips = os.getenv("TRADINGVIEW_IPS").split(",")

@router.post("/webhook")
async def webhook(request: Request, app: FastAPI = Depends()):
    client_host = request.client.host
    if client_host not in tradingview_ips:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        last_signal = await request.json()
        print(f"Received signal: {last_signal}")
        # Store the last signal in Redis
        app.state.redis.set('last_signal', json.dumps(last_signal))
        return {"status": "ok"}
    except Exception as e:
        print(f"Failed to store signal: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while storing the signal")
