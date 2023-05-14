import os
import hmac
import hashlib
import time
import json
import asyncio
import websockets
from dotenv import load_dotenv


class CryptoCom:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("CRYPTO_COM_API_KEY")
        self.api_secret = os.getenv("CRYPTO_COM_API_SECRET")
        environment = os.getenv("ENVIRONMENT")

        if environment == "PRODUCTION":
            self.websocket_url = os.getenv("PRODUCTION_USER_API_WEBSOCKET")
        else:  # Default to sandbox if ENVIRONMENT is not set to PRODUCTION
            self.websocket_url = os.getenv("SANDBOX_USER_API_WEBSOCKET")

        self.connection = None

    async def connect(self):
        self.connection = await websockets.connect(self.websocket_url)
        if self.connection.open:
            print("Connection established.")
            await self.authenticate()

    async def authenticate(self):
        nonce = int(time.time() * 1000)
        signature = hmac.new(
            bytes(self.api_secret, "utf-8"),
            msg=f"{self.api_key}{nonce}".encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        auth_payload = {
            "method": "public/auth",
            "params": {"api_key": self.api_key, "nonce": nonce, "sig": signature},
            "id": 1,
        }
        await self.connection.send(json.dumps(auth_payload))
        response = await self.connection.recv()
        data = json.loads(response)
        if data.get("result") == "ok":
            print("Authentication successful.")
        else:
            print("Authentication failed. Please check your API key and secret.")

    async def subscribe(self, channel):
        subscription_payload = {
            "method": "subscribe",
            "params": {"channels": [channel]},
            "id": 2,
        }
        await self.connection.send(json.dumps(subscription_payload))
        response = await self.connection.recv()
        print(f"Response to subscription request: {response}")

    async def run(self):
        await self.connect()


if __name__ == "__main__":
    crypto_com = CryptoCom()
    asyncio.get_event_loop().run_until_complete(crypto_com.run())
