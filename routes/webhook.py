from fastapi import APIRouter, Request, HTTPException
from dotenv import load_dotenv
import os
import json
import redis

router = APIRouter()

load_dotenv()  # Load environment variables from .env file

# Initialize Redis client (assuming Redis is running on localhost:6379)
r = redis.Redis(host="localhost", port=6379, db=0, decode_responses=True)


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
            payload = await request.text()
            payload = json.loads(payload)  # Convert text payload to JSON
        else:
            raise HTTPException(status_code=415, detail="Unsupported media type")

        # Process the payload or store it as required
        # Assuming payload is serializable via str()
        r.set("last_signal", json.dumps(payload))  # Update the Redis store
        print(f"Received signal: {payload}")

        return {"status": "ok"}

    except Exception as e:
        print(f"Failed to store signal: {e}")
        # Include original error message in HTTPException response
        raise HTTPException(
            status_code=500,
            detail=f"An error occurred while storing the signal: {str(e)}",
        )
