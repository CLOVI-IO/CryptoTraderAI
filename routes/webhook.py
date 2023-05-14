from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi import FastAPI
import os
import json

router = APIRouter()
tradingview_ips = os.getenv("TRADINGVIEW_IPS").split(",")

@router.post("/webhook")
async def webhook(request: Request, app: FastAPI = Depends()):
    client_host = request.client.host
    if client_host not in tradingview_ips:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        app.state.last_signal = await request.json()  # Update the last_signal in the application state
        print(f"Received signal: {app.state.last_signal}")
        return {"status": "ok"}
    except Exception as e:
        print(f"Failed to store signal: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while storing the signal")
