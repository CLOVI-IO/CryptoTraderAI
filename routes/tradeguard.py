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


async def fetch_order_quantity(ref_price: float):
    # Fetch user balance
    user_balance_response = await fetch_user_balance()
    if (
        "result" not in user_balance_response
        or "USDT" not in user_balance_response["result"]
        or "available" not in user_balance_response["result"]["USDT"]
    ):
        raise HTTPException(status_code=500, detail="Unable to fetch user balance")

    user_balance = user_balance_response["result"]["USDT"]["available"]

    # Calculating the amount available for trading
    amount_available_to_trade = (TRADE_PERCENTAGE / 100) * float(user_balance)

    # Calculating order quantity
    order_quantity = amount_available_to_trade / float(ref_price)

    return order_quantity
