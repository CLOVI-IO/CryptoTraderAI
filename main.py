from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

app = FastAPI()

# Global variable to store the last signal
last_signal = "No signal yet"

class Signal(BaseModel):
    signal: dict

@app.get("/")
def read_root():
    return {"Hello": "World!"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        content_type = request.headers.get("Content-Type")
        if content_type == "application/json":
            # Process JSON payload
            global last_signal
            last_signal = await request.json()
            print(f"Received signal: {json.dumps(last_signal, indent=2)}")
            return {"status": "ok"}
        elif content_type == "text/plain":
            # Process plain text payload
            payload = await request.body()
            payload_str = payload.decode("utf-8")
            try:
                signal_dict = json.loads(payload_str)
                global last_signal
                last_signal = signal_dict
                print(f"Received signal: {json.dumps(last_signal, indent=2)}")
                return {"status": "ok"}
            except json.JSONDecodeError as e:
                print(f"Failed to parse signal: {e}")
                raise HTTPException(status_code=400, detail="Invalid JSON payload")
        else:
            raise HTTPException(status_code=415, detail="Unsupported media type")
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
