import time
import hmac
import hashlib
import asyncio
import websockets
import json
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timezone

load_dotenv()
logging.basicConfig(level=logging.DEBUG)


class CryptoCom:
    def __init__(self):
        self.api_key = os.getenv("CRYPTO_COM_API_KEY")
        self.api_secret = os.getenv("CRYPTO_COM_API_SECRET")
        self.api_secret = bytes(self.api_secret, "utf-8")
        self.environment = os.getenv("ENVIRONMENT")
        self.websocket_url = (
            os.getenv("PRODUCTION_USER_API_WEBSOCKET")
            if self.environment == "PRODUCTION"
            else os.getenv("SANDBOX_USER_API_WEBSOCKET")
        )
        self.request_counter = 0

    def get_nonce(self):
        utc_time = datetime.now(timezone.utc)
        utc_timestamp = utc_time.timestamp()
        return int((utc_timestamp - 5) * 1000)  # Subtract 5 seconds from the nonce

    async def connect(self):
        async with websockets.connect(
            self.websocket_url, ping_interval=None
        ) as websocket:
            logging.debug("Connection to {} established.".format(self.websocket_url))

            # Wait for 1 second after establishing the WebSocket connection
            await asyncio.sleep(1)

            nonce = self.get_nonce()
            params = {"api_key": self.api_key, "nonce": nonce}
            params["sig"] = hmac.new(
                self.api_secret,
                msg=str(params["nonce"]).encode("utf-8"),
                digestmod=hashlib.sha256,
            ).hexdigest()
            message = {"id": nonce, "method": "public/auth", "params": params}
            await websocket.send(json.dumps(message))

            response = await websocket.recv()
            response = json.loads(response)
            if "code" in response and response["code"] == 10007:
                logging.error(
                    "Authentication failed for API key {}. Please check your API key and secret. Response: {}".format(
                        self.api_key, response
                    )
                )
                return

            while True:
                try:
                    response = await websocket.recv()
                    response = json.loads(response)
                    logging.debug(response)

                except websockets.exceptions.ConnectionClosed:
                    logging.error("Connection closed")
                    break


if __name__ == "__main__":
    cryptocom = CryptoCom()
    asyncio.get_event_loop().run_until_complete(cryptocom.connect())
