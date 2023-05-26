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

        try:
            self.websocket = await websockets.connect(uri)
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

            print(f"Last 5 characters of the API key: {api_key[-5:]}")

            send_time = datetime.datetime.utcnow()

            try:
                await self.websocket.send(json.dumps(auth_request))
            except Exception as e:
                logging.error(f"Failed to send auth request: {e}")
                continue

            while True:
                try:
                    response = await self.websocket.recv()
                except Exception as e:
                    logging.error(f"Failed to receive auth response: {e}")
                    break

                response = json.loads(response)

                if "id" in response and response["id"] == id:
                    receive_time = datetime.datetime.utcnow()
                    latency = receive_time - send_time
                    print(f"Latency: {latency.total_seconds()} seconds")

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

        raise AuthenticationError("Failed to authenticate after multiple attempts")

    async def send_request(self, request: dict):
        if not self.authenticated:
            await self.authenticate()

        if self.websocket.closed:
            await self.connect()

        try:
            self.pending_requests[request["id"]] = request
            await self.websocket.send(json.dumps(request))
            while True:
                response = await self.websocket.recv()
                response = json.loads(response)

                if response.get("method") == "public/heartbeat":
                    continue
                elif response.get("id") in self.pending_requests:
                    del self.pending_requests[response.get("id")]
                    return response
                else:
                    logging.error(
                        f"Received a response with an unknown request ID: {response.get('id')}"
                    )
        except Exception as e:
            logging.error(f"Failed to send or receive a request: {e}")
            return None
