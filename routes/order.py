from fastapi import APIRouter, WebSocket
from starlette.websockets import WebSocketDisconnect
import logging
from models import Payload
from redis_handler import RedisHandler

router = APIRouter()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

redis_handler = RedisHandler()  # Create RedisHandler instance
redis_client = redis_handler.redis_client  # Access redis client from RedisHandler

@router.websocket("/order")  # Change this line
async def websocket_order(websocket: WebSocket):
    await websocket.accept()
    logging.info("Order: WebSocket accepted")

    try:
        while True:
            data = await websocket.receive_text()
            payload = Payload.parse_raw(data)
            logging.info(f"Order: Received payload from client: {payload}")

            # Perform necessary operations with the payload

            await websocket.send_json({"message": "Received payload"})  # Sending acknowledgment to the client
            logging.debug("Order: Sent acknowledgment to client")
    except WebSocketDisconnect:
        logging.error("Order: WebSocket disconnected.")
    except Exception as e:
        logging.error(f"Order: Unexpected error: {str(e)}")
