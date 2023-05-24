# public/auth.py
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


async def connect():
    environment = os.getenv("ENVIRONMENT", "SANDBOX")
    if environment == "PRODUCTION":
        uri = os.getenv("PRODUCTION_USER_API_WEBSOCKET")
    else:
        uri = os.getenv("SANDBOX_USER_API_WEBSOCKET")

    async with websockets.connect(uri) as websocket:
        api_key = os.getenv("CRYPTO_COM_API_KEY")
        secret_key = os.getenv("CRYPTO_COM_API_SECRET")
        nonce = str(int(time.time() * 1000))
        method = "public/auth"
        id = int(nonce)
        # Generating the sig
        sig_payload = (
            method + str(id) + api_key + nonce
        )  # there are no params in this case
        sig = hmac.new(
            secret_key.encode(), sig_payload.encode(), hashlib.sha256
        ).hexdigest()
        # Preparing the authentication request
        auth_request = {
            "id": id,
            "method": method,
            "api_key": api_key,
            "sig": sig,
            "nonce": nonce,
        }

        # Saving the send time
        send_time = datetime.datetime.utcnow()

        # Sending the authentication request
        await websocket.send(json.dumps(auth_request))

        # Continuously read messages until authentication response is received
        while True:
            response = await websocket.recv()
            response = json.loads(response)

            # If the response id matches the request id, calculate the latency
            if "id" in response and response["id"] == id:
                receive_time = datetime.datetime.utcnow()
                latency = receive_time - send_time
                latency_seconds = latency.total_seconds()

                # Create a dictionary to store the result
                result = {}

                if "code" in response:
                    if response["code"] == 0:
                        result["message"] = "Authenticated successfully"
                    else:
                        result[
                            "message"
                        ] = f"Authentication failed with error code: {response['code']}"
                else:
                    result["message"] = "No 'code' field in the response"

                # Add latency to the result
                result["latency"] = latency_seconds

                # Return the result in JSON format
                return result

            break  # Exit the loop when authentication response is received


# Running the connect coroutine
result = asyncio.get_event_loop().run_until_complete(connect())
print(json.dumps(result))
