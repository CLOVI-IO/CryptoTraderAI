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
last_signal = "No signal yet"

class Signal(BaseModel):
    signal: dict

@app.get("/")
def read_root():
    return {"Hello": "World!"}

@app.post("/webhook")
async def webhook(request: Request):
    try:
        global last_signal
        request_body = await request.body()
        request_json = json.loads(request_body)
        last_signal = request_json
        print(f"Received signal:\nHeaders: {dict(request.headers)}\nBody: {request_json}")
        return {"status": "ok"}
    except Exception as e:
        print(f"Failed to store signal: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while storing the signal")

@app.get("/viewsignal")
def view_signal():
    try:
        global last_signal
        print(f"Retrieving signal: {last_signal}")
        if last_signal:
            return {"signal": last_signal}
        else:
            return {"signal": "No signal"}
    except Exception as e:
        print(f"Failed to retrieve signal: {str(e)}")
        raise HTTPException(status_code=500, detail="An error occurred while retrieving the signal")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
