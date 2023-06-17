import os
import redis
import logging
from rediscluster import RedisCluster
from fastapi import HTTPException


class RedisHandler:
    def __init__(self):
        self.REDIS_HOST = os.getenv(
            "REDIS_HOST", "clustercfg.redis-cluster.5thpsv.apse1.cache.amazonaws.com"
        )
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
        self.redis_client = None

        logging.debug(f"REDIS_HOST={self.REDIS_HOST}")
        logging.debug(f"REDIS_PORT={self.REDIS_PORT}")
        # logging.debug(f"REDIS_PASSWORD={self.REDIS_PASSWORD}")  # Removed for security reasons

    def get_client(self):
        if self.redis_client is None:
            try:
                startup_nodes = [{"host": self.REDIS_HOST, "port": self.REDIS_PORT}]
                if self.REDIS_PASSWORD:
                    self.redis_client = RedisCluster(
                        startup_nodes=startup_nodes,
                        password=self.REDIS_PASSWORD,
                        decode_responses=True,
                    )
                else:
                    self.redis_client = RedisCluster(
                        startup_nodes=startup_nodes,
                        decode_responses=True,
                    )

                logging.debug("Successfully created redis.RedisCluster instance")

                if not self.redis_client.ping():
                    logging.error("Failed to connect to Redis")
                    raise redis.exceptions.ConnectionError("Failed to connect to Redis")
                else:
                    logging.debug("Successfully connected to Redis")

            except redis.exceptions.ConnectionError as e:
                logging.error(f"Redis connection error: {e}")
                raise HTTPException(
                    status_code=500, detail=f"Redis connection error: {e}"
                )
            except Exception as e:
                logging.error(f"Error: {e}")
                raise HTTPException(status_code=500, detail=f"Error: {e}")
        return self.redis_client


# Example usage
redis_handler = RedisHandler()
redis_client = redis_handler.get_client()

# Then, you can use redis_client
# user_balance_redis = redis_client.get("user_balance")
