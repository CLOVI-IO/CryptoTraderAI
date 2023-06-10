from fastapi import APIRouter, HTTPException, BackgroundTasks
from starlette.websockets import WebSocket
import logging
import json
from datetime import datetime
from redis_handler import RedisHandler

# Create an instance of RedisHandler
redis_handler = RedisHandler()

router = APIRouter()

# Setting up logging to display debug messages
logging.basicConfig(level=logging.DEBUG)

connected_websockets = []


@router.websocket("/ws/last_order_updates")
async def websocket_last_order_updates(websocket: WebSocket):
    await websocket.accept()
    connected_websockets.append(websocket)
    try:
        while True:
            message = redis_handler.redis_client.get("last_order_updates")
            if message == b"updated":
                try:
                    last_order = json.loads(
                        redis_handler.redis_client.get("last_order")
                    )
                    if last_order:
                        await websocket.send_text(json.dumps(last_order))
                except Exception as e:
                    logging.error(f"Failed to get last order in websocket: {e}")
    except WebSocket.Disconnect:
        connected_websockets.remove(websocket)


async def listen_for_last_order_updates():
    pubsub = redis_handler.redis_client.pubsub()  # create a pubsub instance
    pubsub.subscribe("last_order_updates")  # subscribe to the channel
    for message in pubsub.listen():  # listen for new messages
        if message["type"] == "message":  # ignore other types of messages
            data = message["data"]
            if data == b"updated":  # check if the message indicates an update
                for websocket in connected_websockets:
                    try:
                        last_order = json.loads(
                            redis_handler.redis_client.get("last_order")
                        )
                        if last_order:
                            await websocket.send_text(json.dumps(last_order))
                    except Exception as e:
                        logging.error(f"Failed to get last order in listener: {e}")


@router.get("/last_order")
async def get_last_order(background_tasks: BackgroundTasks):
    start_time = datetime.utcnow()
    output = {}  # dictionary to hold all relevant details
