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
                last_order = json.loads(redis_handler.redis_client.get("last_order"))
                if last_order:
                    await websocket.send_text(json.dumps(last_order))
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
                    last_order = json.loads(
                        redis_handler.redis_client.get("last_order")
                    )
                    if last_order:
                        await websocket.send_text(json.dumps(last_order))


@router.get("/last_order")
async def get_last_order(background_tasks: BackgroundTasks):
    start_time = datetime.utcnow()
    output = {}  # dictionary to hold all relevant details

    last_order = redis_handler.redis_client.get("last_order")
    if not last_order:
        output.update(
            {
                "message": "No last order in Redis. Starting to listen for last order updates...",
                "timestamp": start_time.isoformat(),
                "latency": "N/A",
            }
        )
        background_tasks.add_task(listen_for_last_order_updates)
        return output

    try:
        last_order = json.loads(last_order)  # Parse into JSON only if not None
        end_time = datetime.utcnow()
        latency = (end_time - start_time).total_seconds()

        output.update(
            {
                "message": "Successfully fetched last order",
                "order": last_order,
                "timestamp": end_time.isoformat(),
                "latency": f"{latency} seconds",
            }
        )

        return output

    except Exception as e:
        end_time = datetime.utcnow()
        latency = (end_time - start_time).total_seconds()
        output.update(
            {
                "error": f"Failed to get last order: {str(e)}",
                "timestamp": end_time.isoformat(),
                "latency": f"{latency} seconds",
            }
        )
        return output