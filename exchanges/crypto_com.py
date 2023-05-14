import time
import hmac
import hashlib
import asyncio
import websockets
import json
import os
import logging
from dotenv import load_dotenv

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

    async def connect(self):
        async with websockets.connect(
            self.websocket_url, ping_interval=None
        ) as websocket:
            logging.debug("Connection to {} established.".format(self.websocket_url))

            # Prepare the authentication message
            nonce = int(time.time() * 1000)  # Use only timestamp for nonce
            params = {"api_key": self.api_key, "nonce": nonce}

            # Sort the keys and combine them in key-value pairs
            param_string = "".join([f"{k}{v}" for k, v in sorted(params.items())])

            message_string = (
                "public/auth" + str(nonce) + self.api_key + param_string + str(nonce)
            )

            params["sig"] = hmac.new(
                self.api_secret,
                msg=message_string.encode("utf-8"),
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
