import time
import hashlib
import hmac
import asyncio
import websockets
import json
import os
import datetime
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)


class Authentication:
    def __init__(self):
        self.websocket = None
        self.loop = asyncio.get_event_loop()
        self.authenticated = False

    async def connect(self):
        environment = os.getenv("ENVIRONMENT", "SANDBOX")
        if environment == "PRODUCTION":
            uri = os.getenv("PRODUCTION_USER_API_WEBSOCKET")
        else:
            uri = os.getenv("SANDBOX_USER_API_WEBSOCKET")

        try:
            self.websocket = await websockets.connect(uri)
            logging.info("Successfully connected to the WebSocket.")
        except Exception as e:
            logging.error(f"Failed to connect to the WebSocket: {e}")
            raise

    async def send_auth_request(self):
        # [The rest of your code here...]

        try:
            await self.websocket.send(json.dumps(auth_request))
        except Exception as e:
            logging.error(f"Failed to send the auth request: {e}")
            raise
        return id

    async def authenticate(self):
        while True:
            if self.websocket is None or self.websocket.closed:
                await self.connect()

            id = await self.send_auth_request()

            try:
                response = await self.websocket.recv()
                response = json.loads(response)
            except Exception as e:
                logging.error(f"Failed to receive the auth response: {e}")
                continue  # Try authenticating again

            # [The rest of your code here...]

    async def send_request(self, request: dict):
        if not self.authenticated:
            await self.authenticate()

        if self.websocket is None or self.websocket.closed:
            raise Exception(
                "WebSocket is not initialized or closed. Please check the connection."
            )

        try:
            await self.websocket.send(json.dumps(request))
            response = await self.websocket.recv()
            return json.loads(response)
        except Exception as e:
            logging.error(f"Failed to send the request or receive the response: {e}")
            raise
