from fastapi import FastAPI, Depends
from dotenv import load_dotenv
from routes import webhook, viewsignal
from shared import SharedState

# Load environment variables
load_dotenv()

app = FastAPI()
shared_state = SharedState()


@app.on_event("startup")
async def startup_event():
    # Any startup logic, if needed
    pass


@app.on_event("shutdown")
async def shutdown_event():
    # Any shutdown logic, if needed
    pass


@app.get("/")
def hello_world(shared: SharedState = Depends()):
    return {"message": "Hello, World!"}


# Use shared state in other routes or endpoints
@app.post("/update_signal")
def update_signal(signal, shared: SharedState = Depends()):
    shared.update_last_signal(signal)
    return {"message": "Signal updated"}


@app.get("/get_last_signal")
def get_last_signal(shared: SharedState = Depends()):
    last_signal = shared.get_last_signal()
    return {"last_signal": last_signal}


# Include the route endpoints from other files
app.include_router(webhook.router)
app.include_router(viewsignal.router)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
