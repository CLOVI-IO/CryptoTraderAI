import asyncio
import json
import time
import hmac
import hashlib
from dotenv import load_dotenv
import os
import websockets

load_dotenv()

# Fetch environment
environment = os.getenv("ENVIRONMENT")

# Fetch API keys
api_key = os.getenv("API_KEY")
api_secret = os.getenv("API_SECRET")

# Set WebSocket URLs based on environment
if environment == "PRODUCTION":
    user_api_websocket_url = os.getenv("PRODUCTION_USER_API_WEBSOCKET")
else:  # Default to sandbox for safety
    user_api_websocket_url = os.getenv("SANDBOX_USER_API_WEBSOCKET")


class CryptoCom:
    def __init__(self, api_key, api_secret, url):
        self.api_key = api_key
        self.api_secret = api_secret
        self.url = url

    async def connect(self):
        self.websocket = await websockets.connect(self.url)
        await self.authenticate()

    async def authenticate(self):
        nonce = int(time.time() * 1000)
        sig_payload = "GET/users/self/verify" + str(nonce)
        signature = hmac.new(
            bytes(self.api_secret, "utf-8"),
            msg=bytes(sig_payload, "utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        await self.websocket.send(
            json.dumps(
                {
                    "id": 1,
                    "method": "public/auth",
                    "params": {
                        "api_key": self.api_key,
                        "nonce": nonce,
                        "sig": signature,
                    },
                }
            )
        )
        response = await self.websocket.recv()
        print(f"Authentication response: {response}")

    async def keep_alive(self):
        while True:
            await self.websocket.send(json.dumps({"method": "public/ping", "id": 2}))
            response = await self.websocket.recv()
            print(f"Keep alive response: {response}")
            await asyncio.sleep(30)

    async def run(self):
        await self.connect()
        await self.keep_alive()


crypto_com = CryptoCom(api_key, api_secret, user_api_websocket_url)

# Run the client
asyncio.get_event_loop().run_until_complete(crypto_com.run())
