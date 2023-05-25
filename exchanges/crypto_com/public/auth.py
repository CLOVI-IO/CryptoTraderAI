import time
import hashlib
import hmac
import asyncio
import websockets
import json
import os
import datetime
from dotenv import load_dotenv

load_dotenv()


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

        self.websocket = await websockets.connect(uri)

    async def authenticate(self):
        while True:
            if self.websocket is None or self.websocket.closed:
                await self.connect()

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

            print(f"Last 5 characters of the API key: {api_key[-5:]}")

            send_time = datetime.datetime.utcnow()

            try:
                await self.websocket.send(json.dumps(auth_request))
                response = await self.websocket.recv()
                response = json.loads(response)

                if "id" in response and response["id"] == id:
                    receive_time = datetime.datetime.utcnow()
                    latency = receive_time - send_time
                    print(f"Latency: {latency.total_seconds()} seconds")

                    if "code" in response:
                        if response["code"] == 0:
                            self.authenticated = True
                            print("Authenticated successfully")
                            await asyncio.sleep(
                                60 * 5
                            )  # sleep for 5 minutes before re-authenticating
                        else:
                            self.authenticated = False
                            print(
                                f"Authentication failed with error code: {response['code']}"
                            )
                    else:
                        print("No 'code' field in the response")
            except websockets.exceptions.ConnectionClosedOK:
                print("WebSocket connection closed, reconnecting...")

    async def send_request(self, request: dict):
        if not self.authenticated:
            await self.authenticate()

        # Added check for websocket object
        if self.websocket is None:
            raise Exception("Websocket is not initialized. Please check connection.")

        await self.websocket.send(json.dumps(request))
        response = await self.websocket.recv()
        return json.loads(response)
