from fastapi import FastAPI
from dotenv import load_dotenv
import os
import uvicorn

from routes import webhook, viewsignal  # Import your route modules here

# Load environment variables
load_dotenv()

app = FastAPI()

# Initialize last_signal in the application state
app.state.last_signal = None


@app.get("/")
def hello_world():
    return {"message": "Hello, World!"}


# Include the route endpoints from other files
app.include_router(webhook.router)
app.include_router(viewsignal.router)
# Add the necessary include_router statements for other routes

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)