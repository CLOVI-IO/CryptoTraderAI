from fastapi import APIRouter, Request, HTTPException
import os

router = APIRouter()
tradingview_ips = (os.getenv("TRADINGVIEW_IPS") or "").split(",")

# Global variable to store the last signal
# Note: Consider using a shared state (like a database or in-memory data store) if this app needs to scale
last_signal = None

@router.post("/webhook")
async def webhook(request: Request):
    client_host = request.client.host
    if client_host not in tradingview_ips:
        raise HTTPException(status_code=403, detail="Access denied")

    global last_signal
    try:
        last_signal = await request.json()
        print(f"Received signal: {last_signal}")
        return {"status": "ok"}
    except Exception as e:
        print(f"Failed to store signal: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while storing the signal")
