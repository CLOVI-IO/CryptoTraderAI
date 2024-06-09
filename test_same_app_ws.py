from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect
from threading import Thread
import asyncio
import websockets
import time
import uvicorn

app = FastAPI()

@app.websocket_route("/ws/order")
async def websocket_order(websocket: WebSocket):
    await websocket.accept()

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        print("WebSocket disconnected")


async def connect_to_websocket():
    uri = "ws://localhost:8000/ws/order"
    async with websockets.connect(uri) as websocket:
        await websocket.send("Hello world!")
        response = await websocket.recv()
        print(response)

# Start FastAPI app in a new thread
def start_app():
    uvicorn.run(app)

Thread(target=start_app).start()

# Wait for a moment to ensure FastAPI app is up and running
time.sleep(1)

# Then launch the WebSocket client connection
asyncio.run(connect_to_websocket())
