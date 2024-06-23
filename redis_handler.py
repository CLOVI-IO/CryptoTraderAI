import redis
import logging


class RedisHandler:
    def __init__(self, host="redis", port=6379, password=None, db=0):
        self.REDIS_HOST = host
        self.REDIS_PORT = port
        self.REDIS_DB = db
        self.REDIS_PASSWORD = password

        # Use a named logger
        self.logger = logging.getLogger("RedisHandler")

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

        self.logger.info("Connecting to Redis:")
        self.logger.info(f"Host: {self.REDIS_HOST}")
        self.logger.info(f"Port: {self.REDIS_PORT}")
        self.logger.info(f"DB: {self.REDIS_DB}")
        self.logger.info(f"Password: {'******' if self.REDIS_PASSWORD else 'None'}")

        # Test the Redis connection
        try:
            self.logger.info("Testing Redis connection...")
            self.redis_client.ping()
            self.logger.info("Redis connection successful!")
        except Exception as e:
            self.logger.error("Failed to connect to Redis!")
            self.logger.exception(e)

    def set(self, key, value):
        self.logger.info(f"Setting key {key} to Redis with value {value}")
        try:
            self.redis_client.set(key, value)
            self.logger.info(f"Successfully set key {key}")
        except Exception as e:
            self.logger.error(f"Failed to set key {key} to Redis")
            self.logger.exception(e)

    def get(self, key):
        self.logger.info(f"Getting key {key} from Redis")
        try:
            value = self.redis_client.get(key)
            self.logger.info(f"Successfully got key {key} with value {value}")
            return value
        except Exception as e:
            self.logger.error(f"Failed to get key {key} from Redis")
            self.logger.exception(e)
            return None

    def publish(self, channel, message):
        self.logger.info(f"Publishing message to channel {channel}: {message}")
        try:
            result = self.redis_client.publish(channel, message)
            self.logger.info(f"Successfully published message to channel {channel}")
            return result
        except Exception as e:
            self.logger.error(f"Failed to publish message to channel {channel}")
            self.logger.exception(e)
            return None
