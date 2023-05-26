import time
import hashlib
import hmac
import asyncio
import websockets
import json
import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)


class Authentication:
    def __init__(self):
        self.websocket = None
        self.loop = asyncio.get_event_loop()
        self.authenticated = False
        self.api_key = os.getenv("CRYPTO_COM_API_KEY")
        self.secret_key = os.getenv("CRYPTO_COM_API_SECRET")
        self.environment = os.getenv("ENVIRONMENT", "SANDBOX")

    async def connect(self):
        uri = (
            os.getenv("PRODUCTION_USER_API_WEBSOCKET")
            if self.environment == "PRODUCTION"
            else os.getenv("SANDBOX_USER_API_WEBSOCKET")
        )

        try:
            self.websocket = await websockets.connect(uri)
            logging.info("Successfully connected to the WebSocket.")
        except Exception as e:
            logging.error(f"Failed to connect to the WebSocket: {e}")
            raise

    async def send_auth_request(self):
        nonce = str(int(time.time() * 1000))
        method = "public/auth"
        id = int(nonce)

        sig_payload = method + str(id) + self.api_key + nonce
        sig = hmac.new(
            self.secret_key.encode(), sig_payload.encode(), hashlib.sha256
        ).hexdigest()

        auth_request = {
            "id": id,
            "method": method,
            "api_key": self.api_key,
            "sig": sig,
            "nonce": nonce,
        }

        logging.debug(f"Last 5 characters of the API key: {self.api_key[-5:]}")

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

            if "id" in response and response["id"] == id:
                if "code" in response and response["code"] == 0:
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

        try:
            await self.websocket.send(json.dumps(request))
            response = await self.websocket.recv()
            return json.loads(response)
        except Exception as e:
            logging.error(f"Failed to send the request or receive the response: {e}")
            raise


# if __name__ == "__main__":
#    auth = Authentication()
#    loop = asyncio.get_event_loop()
#    loop.run_until_complete(auth.authenticate())
