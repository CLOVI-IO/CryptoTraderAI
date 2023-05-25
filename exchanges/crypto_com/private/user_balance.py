# user-balance.py

from fastapi import APIRouter, HTTPException
import asyncio
import time
import json
from exchanges.crypto_com.public.auth import Authentication

auth = Authentication()

router = APIRouter()


async def fetch_user_balance():
    # authenticate when required
    if not auth.authenticated:
        print("Authenticating...")
        await auth.authenticate()

    nonce = str(int(time.time() * 1000))
    method = "private/user-balance"
    id = int(nonce)

    request = {
        "id": id,
        "method": method,
        "params": {},
        "nonce": nonce,
    }

    print("Sending request:", request)
    response = await auth.send_request(request)
    print("Received response:", response)

    if "id" in response and response["id"] == id:
        if "code" in response and response["code"] == 0:
            return response
        else:
            raise Exception("Error fetching user balance")

    raise Exception("Response id does not match request id")


@router.post("/exchanges/crypto_com/private/user-balance")
async def get_user_balance():
    try:
        response = await fetch_user_balance()
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
