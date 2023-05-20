# test_shared_state.py
from shared_state import state  # Import the shared state

# Test
print(f"Initial state: {state}")

# Update the state
state["last_signal"] = {
    "signal": {
        "alert_info": {
            "exchange": "BINANCE",
            "ticker": "SOLUSDT",
            "price": "20.21",
            "volume": "0.36",
            "interval": "1",
        },
        "strategy_info": {
            "order": {"action": "Close Position", "contracts": "0.25", "price": "20.21"}
        },
    }
}

print(f"Updated state: {state}")
