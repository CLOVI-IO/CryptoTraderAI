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
        except Exception as e:
            logging.error(f"Failed to connect to the WebSocket: {e}")
            raise

    async def send_auth_request(self):
        api_key = os.getenv("CRYPTO_COM_API_KEY")
        secret_key = os.getenv("CRYPTO_COM_API_SECRET")
        nonce = str(int(time.time() * 1000))
        method = "public/auth"
        id = int(nonce)

        sig_payload = method + str(id) + api_key + nonce
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

        logging.debug(f"Last 5 characters of the API key: {api_key[-5:]}")

        await self.websocket.send(json.dumps(auth_request))
        return id

    async def authenticate(self):
        while True:
            if self.websocket is None or self.websocket.closed:
                await self.connect()

            id = await self.send_auth_request()
            response = await self.websocket.recv()
            response = json.loads(response)

            if "id" in response and response["id"] == id:
                if "code" in response:
                    if response["code"] == 0:
                        self.authenticated = True
                        logging.info("Authenticated successfully")
                        await asyncio.sleep(
                            60 * 5
                        )  # sleep for 5 minutes before re-authenticating
                    else:
                        self.authenticated = False
                        logging.error(
                            f"Authentication failed with error code: {response['code']}"
                        )
                else:
                    logging.error("No 'code' field in the response")
            else:
                logging.error(
                    f"Response id does not match request id. Request id: {id}, Response: {response}"
                )

    async def send_request(self, request: dict):
        if not self.authenticated:
            await self.authenticate()

        if self.websocket is None or self.websocket.closed:
            raise Exception(
                "WebSocket is not initialized or closed. Please check the connection."
            )

        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        return json.loads(response)
