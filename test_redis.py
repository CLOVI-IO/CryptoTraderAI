import os
import redis

# Get the Redis endpoint from the environment variables
redis_endpoint = os.getenv("REDIS_ENDPOINT")

# Create a connection to the Redis server
try:
    r = redis.Redis(host=redis_endpoint, port=6379, db=0)

    # Test the connection
    r.ping()
    print("Connected to Redis at", redis_endpoint)
except redis.ConnectionError:
    print("Failed to connect to Redis at", redis_endpoint)
