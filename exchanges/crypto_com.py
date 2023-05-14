import os
import asyncio
import hmac
import hashlib
import time
import websockets
import json
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.DEBUG)

API_KEY = os.getenv("CRYPTO_COM_API_KEY")
API_SECRET = os.getenv("CRYPTO_COM_API_SECRET")
WEBSOCKET_URL = os.getenv("WEBSOCKET_URL")


class CryptoCom:
    def __init__(self, api_key, api_secret, websocket_url):
        self.api_key = api_key
        self.api_secret = api_secret
        self.websocket_url = websocket_url
        self.connection = None

    async def connect(self):
        logging.debug(f"Connecting to {self.websocket_url} with API key {self.api_key}")
        self.connection = await websockets.connect(self.websocket_url)
        logging.debug(f"Connected to {self.websocket_url}")

    async def authenticate(self):
        nonce = int(time.time() * 1000)
        sig_payload = f"{self.api_key}{nonce}"
        signature = hmac.new(
            bytes(self.api_secret, "utf-8"),
            msg=sig_payload.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).hexdigest()

        auth_request = {
            "id": 11,
            "method": "public/auth",
            "params": {"api_key": self.api_key, "nonce": nonce, "signature": signature},
        }

        await self.send(auth_request)
        response = await self.receive()
        if response.get("result") == "OK":
            logging.debug(f"Authentication successful")
        else:
            logging.error(f"Authentication failed: {response}")

    async def send(self, message):
        await self.connection.send(json.dumps(message))

    async def receive(self):
        response = await self.connection.recv()
        data = json.loads(response)
        if data.get("method") == "public/auth":
            if data.get("result") != "OK":
                logging.error(f"Failed to authenticate: {data}")
            else:
                logging.debug("Successfully authenticated")
        else:
            logging.debug(f"Received data: {data}")
        return data

    async def run(self):
        await self.connect()
        await self.authenticate()


crypto_com = CryptoCom(API_KEY, API_SECRET, WEBSOCKET_URL)
asyncio.get_event_loop().run_until_complete(crypto_com.run())
