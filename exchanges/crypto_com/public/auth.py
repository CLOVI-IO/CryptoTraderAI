from fastapi import APIRouter, HTTPException, BackgroundTasks
import websockets.exceptions
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

router = APIRouter()

# Setting up logging to display debug messages
logging.basicConfig(level=logging.DEBUG)


class AuthenticationError(Exception):
    pass


class Authentication:
    def __init__(self):
        self.websocket = None
        self.authenticated = False
        self.pending_requests = {}
        self.status = "Not started"
        self.result = None

    async def connect(self):
        logging.info("Connecting...")
        try:
            self.websocket = await websockets.connect("wss://stream.crypto.com/v2/user")
            logging.info("Connected.")
        except (
            websockets.exceptions.InvalidURI,
            websockets.exceptions.InvalidHandshake,
        ):
            logging.error("Failed to connect due to an invalid URI or handshake.")
            raise AuthenticationError(
                "Failed to connect due to an invalid URI or handshake."
            )
        except Exception as e:
            logging.error(f"Failed to connect: {str(e)}")
            raise AuthenticationError(f"Failed to connect: {str(e)}")

    async def authenticate(self, retries=3):
        logging.info("Authenticating...")

        method = "public/auth"
        nonce = str(int(time.time() * 1000))
        secret_key = os.getenv("SECRET_KEY")
        api_key = os.getenv("API_KEY")
        sig_payload = method + nonce + api_key
        signature = hmac.new(
            bytes(secret_key, "latin-1"),
            msg=bytes(sig_payload, "latin-1"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        id = int(nonce)
        request = {
            "id": id,
            "method": method,
            "params": {
                "api_key": api_key,
                "sig": signature,
                "nonce": nonce,
            },
            "nonce": nonce,
        }
        logging.info("Sending auth request: %s", request)

        while retries > 0:
            try:
                await self.websocket.send(json.dumps(request))
                break  # if request sent successfully, break the loop
            except Exception as e:
                if retries == 1:
                    raise e  # re-raise the exception after all attempts exhausted
                retries -= 1
                await asyncio.sleep(5)  # wait before next attempt

        while True:
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=10)
            except asyncio.TimeoutError:
                logging.error("Timeout error while waiting for auth response.")
                raise AuthenticationError(
                    "Timeout error while waiting for auth response."
                )
            except Exception as e:
                logging.error(f"Error while receiving auth response: {str(e)}")
                raise AuthenticationError(
                    f"Error while receiving auth response: {str(e)}"
                )

            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON auth response: {response}")
                raise AuthenticationError("Invalid JSON auth response")

            logging.debug("Received auth response: %s", response)

            if "id" in response and response["id"] == id:
                if "code" in response and response["code"] == 0:
                    logging.info("Authenticated.")
                    self.authenticated = True
                    return
                else:
                    logging.error(
                        "Error during authentication. Expected: %s, Actual: %s, Full Response: %s",
                        id,
                        response.get("id"),
                        response,
                    )
                    raise AuthenticationError("Error during authentication")
            logging.error(
                "Response id does not match request id. Request id: %s, Request: %s, Response: %s",
                id,
                request,
                response,
            )
            # if it reached here, it means that the response id did not match the request id, which is an error
            raise AuthenticationError("Response id does not match request id")

    async def send_request(self, method, params):
        nonce = str(int(time.time() * 1000))
        secret_key = os.getenv("SECRET_KEY")
        api_key = os.getenv("API_KEY")
        sig_payload = method + nonce + json.dumps(params, separators=(",", ":"))
        signature = hmac.new(
            bytes(secret_key, "latin-1"),
            msg=bytes(sig_payload, "latin-1"),
            digestmod=hashlib.sha256,
        ).hexdigest()
        id = int(nonce)
        request = {
            "id": id,
            "method": method,
            "params": params,
            "nonce": nonce,
            "sig": signature,
        }
        logging.info("Sending request: %s", request)
        try:
            await self.websocket.send(json.dumps(request))
        except Exception as e:
            logging.error(f"Failed to send request: {str(e)}")
            raise e

    async def receive_response(self, id):
        while True:
            response = await self.websocket.recv()
            try:
                response = json.loads(response)
            except json.JSONDecodeError:
                logging.error(f"Invalid JSON response: {response}")
                continue
            logging.debug("Received response: %s", response)

            if "id" in response and response["id"] == id:
                return response

    async def request(self, method, params):
        if not self.websocket or self.websocket.closed:
            await self.connect()
        if not self.authenticated:
            await self.authenticate()
        await self.send_request(method, params)
        response = await self.receive_response(id)
        return response
