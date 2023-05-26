# auth.py

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
        if self.websocket is None:
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

        await self.websocket.send(json.dumps(auth_request))

        while True:
            response = await self.websocket.recv()
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
                        return {
                            "message": f"Authentication failed with error code: {response['code']}"
                        }
                else:
                    return {"message": "No 'code' field in the response"}


async def send_request(self, request: dict):
    if not self.authenticated:
        await self.authenticate()

    if self.websocket.closed:
        await self.connect()

    try:
        await self.websocket.send(json.dumps(request))
        while True:
            response = await self.websocket.recv()
            response = json.loads(response)
            # Ignore the heartbeat messages
            if response.get("method") == "public/heartbeat":
                continue
            elif response.get("id") == request.get("id"):
                return response
            else:
                logging.error(
                    f"Response id does not match request id. Request id: {request.get('id')}, Response: {response}"
                )
    except Exception as e:
        logging.error(f"Failed to send request: {e}")
        raise


# When you run python3 -m exchanges.crypto_com.public.auth,
# it should execute the authenticate method of the Authentication
# class and attempt to authenticate the user.

#  if __name__ == "__main__":
#    auth = Authentication()
#    asyncio.get_event_loop().run_until_complete(auth.authenticate())
