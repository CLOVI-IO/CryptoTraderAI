# redis_handler.py

import os
import redis


class RedisHandler:
    def __init__(self):
        self.REDIS_HOST = os.getenv("REDIS_HOST")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        # self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
        self.redis_client = redis.StrictRedis(
            host=self.REDIS_HOST,
            port=self.REDIS_PORT
            # , password=self.REDIS_PASSWORD
        )
