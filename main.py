from fastapi import FastAPI
from dotenv import load_dotenv
import os

load_dotenv()

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World!"}

# Include other imports and configurations here

# Include route imports here
from routes import webhook, viewsignal, order

# Include route registrations here
app.include_router(webhook.router)
app.include_router(viewsignal.router)
app.include_router(order.router)
