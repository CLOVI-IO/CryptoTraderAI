# webhook.py
from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv
import os
import json
from shared_state import state  # Import the shared state

router = APIRouter()

load_dotenv()  # Load environment variables from .env file


@router.post("/webhook")
async def webhook(request: Request):
    client_host = request.client.host
    print(f"Client host: {client_host}")  # Debug print

    tradingview_ips = os.getenv("TRADINGVIEW_IPS", "").split(",")
    print(f"TradingView IPs: {tradingview_ips}")  # Debug print

    if client_host not in tradingview_ips:
        raise HTTPException(status_code=403, detail="Access denied")

    try:
        content_type = request.headers.get("content-type", "")
        print(f"Content type: {content_type}")  # Debug print

        if "application/json" in content_type:
            payload = await request.json()
        elif "text/plain" in content_type:
            body = await request.body()
            payload = body.decode()  # Decode bytes to string
            payload = json.loads(payload)  # Convert text payload to JSON
        else:
            raise HTTPException(status_code=415, detail="Unsupported media type")

        # Process the payload or store it as required
        state["last_signal"] = payload  # Update the shared state
        print(f"Received signal: {state['last_signal']}")

        return {"status": "ok"}

    except Exception as e:
        print(f"Failed to store signal: {e}")
        raise HTTPException(
            status_code=500, detail="An error occurred while storing the signal"
        )
