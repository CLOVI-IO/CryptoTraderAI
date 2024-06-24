import asyncio
import json
import os
import time
import hashlib
import hmac
import logging
from datetime import datetime
from dotenv import load_dotenv
import websockets

load_dotenv()

logger = logging.getLogger("websocket_manager")


class WebSocketManager:
    def __init__(self):
        self.websocket = None
        self.authenticated = False
        self.pending_requests = {}

    async def connect(self):
        environment = os.getenv("ENVIRONMENT", "SANDBOX")
        uri = (
            os.getenv("PRODUCTION_USER_API_WEBSOCKET")
            if environment == "PRODUCTION"
            else os.getenv("SANDBOX_USER_API_WEBSOCKET")
        )

        logger.debug(f"Trying to connect to {uri}")
        try:
            self.websocket = await websockets.connect(uri)
            logger.debug(f"Successfully connected to {uri}")
        except Exception as e:
            logger.error(f"Failed to establish connection: {e}")
            self.websocket = None

    async def authenticate(self):
        if self.websocket is None or self.websocket.closed:
            await self.connect()

        if self.websocket is None:
            raise ConnectionError("Unable to connect to the server")

        api_key = os.getenv("CRYPTO_COM_API_KEY")
        secret_key = os.getenv("CRYPTO_COM_API_SECRET")

        if not api_key or not secret_key:
            raise ValueError(
                "API key or secret key not found in environment variables."
            )

        nonce = str(int(time.time() * 1000))
        method = "public/auth"
        id = int(nonce)

        sig_payload = f"{method}{id}{api_key}{nonce}"
        sig = hmac.new(
            secret_key.encode(), sig_payload.encode(), hashlib.sha256
        ).hexdigest()

        auth_request = {
            "id": id,
            "method": method,
            "api_key": api_key,
            "sig": sig,
            "nonce": nonce,
        }

        logger.debug(f"Auth request: {auth_request}")
        await self.websocket.send(json.dumps(auth_request))

        response = await self.websocket.recv()
        response = json.loads(response)
        logger.debug(f"Received auth response: {response}")

        if response.get("id") == id and response.get("code") == 0:
            self.authenticated = True
            logger.info("Authentication successful")
        else:
            logger.authenticated = False
            logger.error(f"Authentication failed with response: {response}")
            raise ConnectionError("Authentication failed")

    async def send_request(self, method, params=None):
        if params is None:
            params = {}

        if not self.authenticated or self.websocket is None:
            raise ConnectionError("Not authenticated")

        nonce = str(int(time.time() * 1000))
        id = int(nonce)
        request = {
            "id": id,
            "method": method,
            "params": params,
            "nonce": nonce,
        }

        logger.debug(f"Sending request: {request}")
        await self.websocket.send(json.dumps(request))

        while True:
            response = await self.websocket.recv()
            response = json.loads(response)
            logger.debug(f"Received response: {response}")

            if response.get("method") == "public/heartbeat":
                await self.respond_heartbeat(response.get("id"))
                continue

            if response.get("id") == id:
                return response

    async def respond_heartbeat(self, id):
        heartbeat_response = {"id": id, "method": "public/respond-heartbeat"}
        await self.websocket.send(json.dumps(heartbeat_response))
        logger.debug(f"Sent heartbeat response: {heartbeat_response}")

    async def subscribe(self, channels):
        await asyncio.sleep(1)  # Avoid rate-limit errors
        await self.send_request("subscribe", {"channels": channels})

    async def handle_messages(self):
        while True:
            try:
                message = await self.websocket.recv()
                message = json.loads(message)
                logger.debug(f"Received message: {message}")
                if message.get("method") == "public/heartbeat":
                    await self.respond_heartbeat(message.get("id"))
                else:
                    # Handle other messages here
                    pass
            except Exception as e:
                logger.error(f"Error handling message: {e}")

    async def run(self, channels):
        await self.connect()
        await self.authenticate()
        await self.subscribe(channels)
        await self.handle_messages()


async def main():
    channels = ["user.order"]
    manager = WebSocketManager()
    await manager.run(channels)


if __name__ == "__main__":
    asyncio.run(main())
