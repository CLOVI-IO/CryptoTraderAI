from fastapi import APIRouter, HTTPException
import os
import json
import time
import logging
import asyncio
import traceback
from redis_handler import RedisHandler
from models import Signal, AlertInfo, BarInfo, CurrentInfo, StrategyInfo, Order

router = APIRouter()
redis_handler = RedisHandler()
TRADE_PERCENTAGE = float(os.getenv("TRADE_PERCENTAGE", 5))


async def fetch_order_quantity(ref_price):
    # Fetch updated user balance from Redis
    user_balance_data = redis_handler.redis_client.get("user_balance")
    if not user_balance_data:
        logging.error("User balance not found in Redis.")
        # Default to zero or raise a specific custom exception instead
        return 0.0

    user_balance = json.loads(user_balance_data)

    # Parse accounts and find USD balance
    usd_balance = next(
        (
            account
            for account in user_balance["result"]["accounts"]
            if account["currency"] == "USD"
        ),
        None,
    )

    if not usd_balance:
        logging.error(f"USD not found in user balance. Balance: {user_balance}")
        # Default to zero or raise a specific custom exception instead
        return 0.0

    # Calculating the amount available for trading
    amount_available_to_trade = (TRADE_PERCENTAGE / 100) * float(
        usd_balance["available"]
    )
    # Calculating order quantity
    order_quantity = amount_available_to_trade / float(ref_price)

    return order_quantity


async def subscribe_to_last_order(redis_handler: RedisHandler):
    pubsub = redis_handler.redis_client.pubsub()
    pubsub.subscribe("last_signal")
    logging.info("Tradeguard: Subscribed to 'last_signal' channel")

    try:
        while True:
            message = pubsub.get_message()
            if message and message["type"] == "message":
                try:
                    signal_data = json.loads(message["data"])
                    logging.info(
                        f"Tradeguard: Received last_signal from Redis channel: {signal_data}"
                    )

                    # Parse the signal data
                    alert_info = AlertInfo(**signal_data["signal"]["alert_info"])
                    bar_info = BarInfo(**signal_data["signal"]["bar_info"])
                    current_info = CurrentInfo(**signal_data["signal"]["current_info"])
                    order_info = Order(
                        **signal_data["signal"]["strategy_info"]["order"]
                    )
                    strategy_info = StrategyInfo(order=order_info)

                    signal = Signal(
                        alert_info=alert_info,
                        bar_info=bar_info,
                        current_info=current_info,
                        strategy_info=strategy_info,
                    )

                    # Extract relevant information from the last_signal
                    ticker = signal.alert_info.ticker
                    price = float(signal.alert_info.price)
                    action = signal.strategy_info.order.action.upper()

                    # Fetch order quantity based on the current price
                    quantity = await fetch_order_quantity(price)

                    if quantity == 0.0:
                        logging.error(
                            "Order quantity is zero. Skipping order creation."
                        )
                        continue

                    # Create the order using the template
                    order_payload = {
                        "instrument_name": ticker,
                        "side": action,
                        "type": "LIMIT",  # Assuming a limit order; adjust as needed
                        "price": price,
                        "quantity": quantity,
                        "trigger_price": price * 0.95,  # Example trigger price
                        "callback_rate": 5,  # Example callback rate
                        "distance": 0.02,  # Example distance
                        "take_profit_price": price * 1.05,  # Example take profit price
                        "stop_loss_price": price * 0.90,  # Example stop loss price
                    }

                    # Publish the order to Redis
                    redis_handler.redis_client.publish(
                        "last_order", json.dumps(order_payload)
                    )
                    logging.info(
                        f"Tradeguard: Published order to 'last_order': {order_payload}"
                    )

                except KeyError as e:
                    logging.error(f"Tradeguard: Key error: {str(e)}")
                    logging.error(f"Signal data: {signal_data}")
                except ValueError as e:
                    logging.error(f"Tradeguard: Value error: {str(e)}")
                    logging.error(f"Signal data: {signal_data}")
                except Exception as e:
                    logging.error(f"Tradeguard: Unexpected error: {str(e)}")
                    logging.error(f"Signal data: {signal_data}")
                    logging.error(traceback.format_exc())

            await asyncio.sleep(0.1)
    except Exception as e:
        logging.error(f"Tradeguard: Unexpected error in subscription loop: {str(e)}")
        logging.error(traceback.format_exc())


# If you don't use the endpoint for order quantity, you can remove it as requested.
# @router.get("/order_quantity/{ref_price}")
# async def get_order_quantity(ref_price: float):
#     start_time = time.time()  # Save the start time

#     quantity = await fetch_order_quantity(ref_price)

#     end_time = time.time()  # Save the end time
#     latency = end_time - start_time  # Calculate the difference, which is the latency
#     print(f"Endpoint latency: {latency} seconds")  # Print the latency

#     return {"quantity": quantity, "latency": latency}
