from fastapi import FastAPI
from dotenv import load_dotenv
import os
import uvicorn
import redis

from routes import webhook, viewsignal, order

# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize Redis client
r = redis.Redis(host='my-redis-cluster.5thpsv.0001.apse1.cache.amazonaws.com:6379', port=6379, db=0)

# Include the route endpoints from other files
app.include_router(webhook.router)
app.include_router(viewsignal.router)
app.include_router(order.router)

app.state.redis = r  # Store the Redis client in the application state

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
