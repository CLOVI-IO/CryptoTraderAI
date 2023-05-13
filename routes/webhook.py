from fastapi import APIRouter, Request, HTTPException

router = APIRouter()

@router.post("/webhook")
async def webhook(request: Request):
    client_host = request.client.host
    if client_host not in TRADINGVIEW_IPS:
        raise HTTPException(status_code=403, detail="Access denied")
    try:
        global last_signal
        last_signal = await request.json()
        print(f"Received signal: {last_signal}")
        return {"status": "ok"}
    except Exception as e:
        print(f"Failed to store signal: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while storing the signal")
