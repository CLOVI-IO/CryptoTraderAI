import logging
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

# Setting up logging to display debug messages
logging.basicConfig(level=logging.DEBUG)


class AuthenticationError(Exception):
    pass


class Authentication:
    def __init__(self):
        self.websocket = None
        self.loop = asyncio.get_event_loop()
        self.authenticated = False
        self.pending_requests = {}

    async def connect(self):
        environment = os.getenv("ENVIRONMENT", "SANDBOX")
        if environment == "PRODUCTION":
            uri = os.getenv("PRODUCTION_USER_API_WEBSOCKET")
        else:
            uri = os.getenv("SANDBOX_USER_API_WEBSOCKET")

        logging.debug("Trying to connect to %s", uri)

        try:
            self.websocket = await websockets.connect(uri)
            logging.debug("Successfully connected to %s", uri)
        except Exception as e:
            logging.error(f"Failed to establish connection: {e}")
            self.websocket = None

    async def authenticate(self, retries=3):
        for i in range(retries):
            if self.websocket is None or self.websocket.closed:
                await self.connect()

            if self.websocket is None:
                raise AuthenticationError("Unable to connect to the server")

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

            logging.debug(f"Auth request: {auth_request}")

            send_time = datetime.datetime.utcnow()

            try:
                await self.websocket.send(json.dumps(auth_request))
                logging.debug("Sent auth request")
            except Exception as e:
                logging.error(f"Failed to send auth request: {e}")
                continue

            while True:
                try:
                    response = await self.websocket.recv()
                    logging.debug(f"Received auth response: {response}")
                except Exception as e:
                    logging.error(f"Failed to receive auth response: {e}")
                    break

                response = json.loads(response)

                if "id" in response and response["id"] == id:
                    receive_time = datetime.datetime.utcnow()
                    latency = receive_time - send_time
                    logging.debug(f"Latency: {latency.total_seconds()} seconds")

                    if "code" in response:
                        if response["code"] == 0:
                            self.authenticated = True
                            return {"message": "Authenticated successfully"}
                        else:
                            self.authenticated = False
                            logging.error(
                                f"Authentication failed with error code: {response['code']}"
                            )
                            break
                    else:
                        logging.error("No 'code' field in the response")
                        break

        raise AuthenticationError


if __name__ == "__main__":
    auth = Authentication()
    asyncio.run(auth.authenticate())
