import redis
import os
import json

REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

pubsub = r.pubsub()  # Create a pubsub instance
pubsub.subscribe("last_signal")  # Subscribe to the 'last_signal' channel
print("Subscribed to 'last_signal' channel")

while True:
    message = pubsub.get_message()
    if message and message["type"] == "message":
        last_signal = json.loads(message["data"])
        print(f"Received last_signal from Redis channel: {last_signal}")
