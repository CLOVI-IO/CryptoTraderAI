# tradeguard.py

from fastapi import APIRouter, HTTPException
import os
import json
import time
from redis_handler import RedisHandler
from exchanges.crypto_com.private.user_balance import fetch_user_balance

router = APIRouter()
redis_handler = RedisHandler()
TRADE_PERCENTAGE = float(os.getenv("TRADE_PERCENTAGE", 5))


async def fetch_order_quantity(ref_price):
    # First update the user balance by fetching it from the exchange
    await fetch_user_balance()

    # Fetch updated user balance from Redis
    user_balance_data = redis_handler.redis_client.get("user_balance")
    if not user_balance_data:
        raise HTTPException(status_code=500, detail="User balance not found in Redis.")

    user_balance = json.loads(user_balance_data)

    # Parse accounts and find USD balance
    usd_balance = None
    for account in user_balance["result"]["accounts"]:
        if account["currency"] == "USD":
            usd_balance = account
            break

    if not usd_balance:
        raise HTTPException(
            status_code=500,
            detail=f"USD not found in user balance. Balance: {user_balance}",
        )

    # Calculating the amount available for trading
    amount_available_to_trade = (TRADE_PERCENTAGE / 100) * float(
        usd_balance["available"]
    )
    # Calculating order quantity
    order_quantity = amount_available_to_trade / float(ref_price)

    return order_quantity


# New endpoint for getting order quantity
@router.get("/order_quantity/{ref_price}")
async def get_order_quantity(ref_price: float):
    start_time = time.time()  # Save the start time

    quantity = await fetch_order_quantity(ref_price)

    end_time = time.time()  # Save the end time
    latency = end_time - start_time  # Calculate the difference, which is the latency
    print(f"Endpoint latency: {latency} seconds")  # Print the latency

    return {
        "quantity": quantity,
        "latency": latency,
    }  # Return the latency along with the quantity
