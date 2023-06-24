import os
import redis
import logging


class RedisHandler:
    def __init__(self):
        self.REDIS_HOST = os.getenv("REDIS_HOST")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

        # Check if a password is set in the environment variables
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

        # Only use the password if it's provided
        if self.REDIS_PASSWORD:
            self.redis_client = redis.StrictRedis(
                host=self.REDIS_HOST, port=self.REDIS_PORT, password=self.REDIS_PASSWORD
            )
        else:
            self.redis_client = redis.StrictRedis(
                host=self.REDIS_HOST, port=self.REDIS_PORT
            )

        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

        # Log the Redis connection details
        self.logger.info("Connecting to Redis:")
        self.logger.info(f"Host: {self.REDIS_HOST}")
        self.logger.info(f"Port: {self.REDIS_PORT}")
        self.logger.info(f"Password: {'******' if self.REDIS_PASSWORD else 'None'}")

        # Log the Redis client instance
        self.logger.info(f"Redis client: {self.redis_client}")

        # Test the Redis connection
        try:
            self.logger.info("Testing Redis connection...")
            self.redis_client.ping()
            self.logger.info("Redis connection successful!")
        except Exception as e:
            self.logger.error("Failed to connect to Redis!")
            self.logger.exception(e)

        # Set logging for Redis commands
        self.redis_client.set_response_callback("SET", self.log_response)
        self.redis_client.set_response_callback("GET", self.log_response)
        # Add other Redis commands as needed

    def log_response(self, command, response):
        self.logger.info(f"Redis command: {command}, Response: {response}")
