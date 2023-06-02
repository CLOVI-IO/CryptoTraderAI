import redis
import os
import json

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

# Let's suppose this is your payload
payload = {
    "alert_info": {
        "exchange": "BINANCE",
        "ticker": "SOLUSDT",
        "price": "21.26",
        "volume": "260.54",
        "interval": "1",
    }
}

# Publish to Redis
r.publish("last_signal", json.dumps(payload))
print("Published 'last_signal' to Redis")
