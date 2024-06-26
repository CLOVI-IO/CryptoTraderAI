import os
import json
import logging
import asyncio
import traceback
import time
from fastapi import APIRouter
from redis_handler import RedisHandler
from models import Signal, AlertInfo, BarInfo, CurrentInfo, StrategyInfo, Order

router = APIRouter()
redis_handler = RedisHandler()
TRADE_PERCENTAGE = float(os.getenv("TRADE_PERCENTAGE", 5))

logging.basicConfig(level=logging.DEBUG)


async def fetch_order_quantity(ref_price):
    user_balance_data = redis_handler.get("user_balance")
    if not user_balance_data:
        logging.error("User balance not found in Redis.")
        return 0.0

    user_balance = json.loads(user_balance_data)

    usd_balance = next(
        (account for account in user_balance if account["currency"] == "USD"),
        None,
    )

    if not usd_balance:
        logging.error(f"USD not found in user balance. Balance: {user_balance}")
        return 0.0

    amount_available_to_trade = (TRADE_PERCENTAGE / 100) * float(
        usd_balance["available"]
    )
    order_quantity = amount_available_to_trade / float(ref_price)

    return order_quantity


async def subscribe_to_last_signal():
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
                        "id": 1,  # Replace with appropriate ID generation logic
                        "nonce": int(time.time() * 1000),
                        "method": "private/create-order",
                        "params": {
                            "instrument_name": ticker,
                            "side": action,
                            "type": "STOP_LIMIT",
                            "price": str(price),
                            "quantity": str(quantity),
                            "ref_price": str(price * 0.95),  # Example trigger price
                            "ref_price_type": "LAST_PRICE",
                            "client_oid": "unique-client-order-id",  # Unique client order ID
                            "exec_inst": ["TRAILING"],
                            "time_in_force": "GOOD_TILL_CANCEL",
                            "trigger_price": str(
                                price * 0.95
                            ),  # Same as ref_price for triggering stop
                            "callback_rate": 5,  # Example callback rate
                            "take_profit_price": str(
                                price * 1.05
                            ),  # Example take profit price
                            "stop_loss_price": str(
                                price * 0.90
                            ),  # Example stop loss price
                        },
                    }

                    # Store the order in Redis
                    redis_handler.set("last_order", json.dumps(order_payload))
                    logging.info(
                        f"Tradeguard: Stored order in 'last_order': {order_payload}"
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
