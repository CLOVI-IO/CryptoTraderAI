# tradeguard.py

from fastapi import APIRouter, HTTPException
import os
import json
from redis_handler import RedisHandler
from exchanges.crypto_com.private.user_balance import fetch_user_balance

router = APIRouter()
redis_handler = RedisHandler()
TRADE_PERCENTAGE = float(
    os.getenv("TRADE_PERCENTAGE", 5)
)  # get trade percentage from environment variable


async def fetch_order_quantity(ref_price):
    # Fetch user balance from Redis
    user_balance_data = redis_handler.redis_client.get("user_balance")
    if not user_balance_data:
        raise HTTPException(status_code=500, detail="User balance not found in Redis.")

    user_balance = json.loads(user_balance_data)

    # Find USD account in the list of accounts
    usd_account = None
    for account in user_balance["result"]["accounts"]:
        if account["currency"] == "USD":
            usd_account = account
            break

    if not usd_account:
        raise HTTPException(
            status_code=500,
            detail=f"USD not found in user balance. Balance: {user_balance}",
        )

    # Calculating the amount available for trading
    amount_available_to_trade = (TRADE_PERCENTAGE / 100) * float(
        usd_account["available"]
    )
    # Calculating order quantity
    order_quantity = amount_available_to_trade / float(ref_price)

    return order_quantity


# New endpoint for getting order quantity
@router.get("/order_quantity/{ref_price}")
async def get_order_quantity(ref_price: float):
    quantity = await fetch_order_quantity(ref_price)
    return {"quantity": quantity}
