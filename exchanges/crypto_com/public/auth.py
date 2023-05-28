# auth.py

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
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
        environment = os.getenv("ENVIRONMENT", "SANDBOX")
        if environment == "PRODUCTION":
            uri = os.getenv("PRODUCTION_USER_API_WEBSOCKET")
        else:
            uri = os.getenv("SANDBOX_USER_API_WEBSOCKET")

        logging.debug("Trying to connect to %s", uri)
        self.status = f"Trying to connect to {uri}"

        try:
            self.websocket = await websockets.connect(uri)
            logging.debug("Successfully connected to %s", uri)
            self.status = f"Successfully connected to {uri}"
        except Exception as e:
            logging.error(f"Failed to establish connection: {e}")
            self.websocket = None
            self.status = f"Failed to establish connection: {e}"

    async def authenticate(self, retries=3):
        for i in range(retries):
            if self.websocket is None or self.websocket.closed:
                await self.connect()

            if self.websocket is None:
                raise AuthenticationError("Unable to connect to the server")

            api_key = os.getenv("CRYPTO_COM_API_KEY")
            secret_key = os.getenv("CRYPTO_COM_API_SECRET")

            if not api_key or not secret_key:
                raise AuthenticationError(
                    "API key or secret key not found in environment variables."
                )

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
            self.status = f"Auth request: {auth_request}"

            send_time = datetime.datetime.utcnow()

            try:
                await self.websocket.send(json.dumps(auth_request))
                logging.debug("Sent auth request")
                self.status = "Sent auth request"
            except Exception as e:
                logging.error(f"Failed to send auth request: {e}")
                self.status = f"Failed to send auth request: {e}"
                continue

            while True:
                try:
                    response = await self.websocket.recv()
                    logging.debug(f"Received auth response: {response}")
                    self.status = f"Received auth response: {response}"
                except Exception as e:
                    logging.error(f"Failed to receive auth response: {e}")
                    self.status = f"Failed to receive auth response: {e}"
                    break

                response = json.loads(response)

                if "id" in response and response["id"] == id:
                    receive_time = datetime.datetime.utcnow()
                    latency = receive_time - send_time
                    logging.debug(f"Latency: {latency.total_seconds()} seconds")
                    self.status = f"Latency: {latency.total_seconds()} seconds"

                    if "code" in response:
                        if response["code"] == 0:
                            self.authenticated = True
                            self.result = {"message": "Authenticated successfully"}
                            return self.result
                        else:
                            self.authenticated = False
                            logging.error(
                                f"Authentication failed with error code: {response['code']}"
                            )
                            self.status = f"Authentication failed with error code: {response['code']}"
                            break
                    else:
                        logging.error("No 'code' field in the response")
                        self.status = "No 'code' field in the response"
                        break

        raise AuthenticationError

    async def send_request(self, method, params=None):
        if params is None:
            params = {}

        if not self.authenticated or self.websocket is None:
            raise AuthenticationError("Not authenticated")

        nonce = str(int(time.time() * 1000))
        id = int(nonce)
        request = {
            "id": id,
            "method": method,
            "params": params,
            "nonce": nonce,
        }

        await self.websocket.send(json.dumps(request))

        while True:
            try:
                response = await self.websocket.recv()
            except websockets.exceptions.ConnectionClosed:
                raise AuthenticationError("Connection closed before receiving response")

            response = json.loads(response)

            # If it's a heartbeat message, ignore it and wait for the next message
            if response.get("method") == "public/heartbeat":
                continue

            if "id" in response and response["id"] == id:
                return response

        raise AuthenticationError("Failed to receive response")


auth = Authentication()


@router.get("/auth")
async def auth_endpoint(background_tasks: BackgroundTasks):
    background_tasks.add_task(auth.authenticate)
    return {"message": "Authentication started"}


@router.get("/auth/status")
async def auth_status():
    return {
        "status": auth.status,
        "result": auth.result,
    }
