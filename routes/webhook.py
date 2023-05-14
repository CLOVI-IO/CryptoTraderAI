from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv
import os
import json

router = APIRouter()

load_dotenv()  # Load environment variables from .env file


@router.post("/webhook")
async def webhook(request: Request):
    client_host = request.client.host
    tradingview_ips = os.getenv("TRADINGVIEW_IPS", "").split(",")
    if client_host not in tradingview_ips:
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" in content_type:
            payload = await request.json()
        elif "text/plain" in content_type:
            payload = await request.text()
            payload = json.loads(payload)  # Convert text payload to JSON
        else:
            raise HTTPException(status_code=415, detail="Unsupported media type")

        global last_signal
        last_signal = payload
        print(f"Received signal: {last_signal}")

        return {"status": "ok"}
    except Exception as e:
        print(f"Failed to store signal: {e}")
        raise HTTPException(
            status_code=500, detail="An error occurred while storing the signal"
        )
