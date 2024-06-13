import os
import redis
import logging


class RedisHandler:
    def __init__(self, host="redis", port=6379, password=None, db=0):
        self.REDIS_HOST = host
        self.REDIS_PORT = port
        self.REDIS_DB = db
        self.REDIS_PASSWORD = password

        # Initialize logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        ch = logging.StreamHandler()
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        # Log the Redis connection details
        self.logger.info("Connecting to Redis:")
        self.logger.info(f"Host: {self.REDIS_HOST}")
        self.logger.info(f"Port: {self.REDIS_PORT}")
        self.logger.info(f"DB: {self.REDIS_DB}")
        self.logger.info(f"Password: {'******' if self.REDIS_PASSWORD else 'None'}")

        # Only use the password if it's provided
        if self.REDIS_PASSWORD:
            self.redis_client = redis.StrictRedis(
                host=self.REDIS_HOST,
                port=self.REDIS_PORT,
                password=self.REDIS_PASSWORD,
                db=self.REDIS_DB,
                decode_responses=True,  # Ensure responses are decoded as strings
            )
        else:
            self.redis_client = redis.StrictRedis(
                host=self.REDIS_HOST,
                port=self.REDIS_PORT,
                db=self.REDIS_DB,
                decode_responses=True,
            )

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
        self.redis_client.set_response_callback("SET", self.log_response("SET"))
        self.redis_client.set_response_callback("GET", self.log_response("GET"))

    def log_response(self, command):
        def wrapper(response):
            self.logger.info(f"Redis command: {command}, Response: {response}")
            return response  # Ensure the response is returned

        return wrapper
