import os

# Get the Redis endpoint from the environment variables
redis_endpoint = os.getenv("REDIS_ENDPOINT")

# Print the Redis endpoint
print("Redis Endpoint:", redis_endpoint)
