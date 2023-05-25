from fastapi import FastAPI
from dotenv import load_dotenv
import os
import uvicorn

# Include the new module
from exchanges.crypto_com.private import user_balance

from routes import webhook, viewsignal, order, last_order, exchange

# Load environment variables
load_dotenv()

app = FastAPI()


@app.get("/")
def hello_world():
    return {"message": "Hello, World!"}


# Include the route endpoints from other files
app.include_router(webhook.router)
app.include_router(viewsignal.router)
app.include_router(order.router)
app.include_router(last_order.router)
app.include_router(exchange.router)
app.include_router(user_balance.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
