from typing import Union
from fastapi import FastAPI, Request
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

#@app.get("/items/{item_id}")
#def read_item(item_id: int, q: Union[str, None] = None):
#    return {"item_id": item_id, "q": q}

@app.post("/tradingview-webhook/")
async def tradingview_webhook(request: Request):
    data = await request.json()
    print(data)  # print the data to the console for now
    return {"message": "Webhook received"}
