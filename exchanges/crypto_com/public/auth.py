import asyncio
import websockets
import os
import time
import hashlib
import hmac
import json
from dotenv import load_dotenv

load_dotenv()


class Authentication:
    def __init__(self):
        self.websocket = None
        self.loop = asyncio.get_event_loop()
        self.authenticated = False

    async def connect(self):
        uri = os.getenv("USER_API_WEBSOCKET")
        self.websocket = await websockets.connect(uri)

    async def authenticate(self, system_label=None):
        api_key = os.getenv("CRYPTO_COM_API_KEY")
        secret_key = os.getenv("CRYPTO_COM_API_SECRET")
        nonce = str(int(time.time() * 1000))
        method = "public/auth"
        id = int(nonce)

        sig_payload = method + nonce + api_key
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

        if system_label:
            auth_request["params"] = {"system_label": system_label}

        await self.websocket.send(json.dumps(auth_request))

        response = await self.websocket.recv()
        response = json.loads(response)

        if response.get("code") == 0:
            self.authenticated = True
            print("Authenticated successfully")
        else:
            self.authenticated = False
            print(f"Authentication failed with error code: {response['code']}")

    async def send_request(self, request: dict):
        if not self.authenticated:
            await self.authenticate()

        await self.websocket.send(json.dumps(request))

        response = await self.websocket.recv()
        response = json.loads(response)

        return response


if __name__ == "__main__":
    auth = Authentication()
    asyncio.get_event_loop().run_until_complete(auth.authenticate())
