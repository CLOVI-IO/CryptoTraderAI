import os
import redis
import logging
from fastapi.responses import JSONResponse
from rediscluster import RedisCluster


class RedisHandler:
    def __init__(self):
        self.REDIS_HOST = os.getenv("REDIS_HOST")
        self.REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))

        logging.debug(f"REDIS_HOST={self.REDIS_HOST}")
        logging.debug(f"REDIS_PORT={self.REDIS_PORT}")

        # Check if a password is set in the environment variables
        self.REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")

        logging.debug(f"REDIS_PASSWORD={self.REDIS_PASSWORD}")

        try:
            startup_nodes = [{"host": self.REDIS_HOST, "port": self.REDIS_PORT}]
            # Only use the password if it's provided
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

            # Try a simple operation to check if the connection is established
            if self.redis_client.ping():
                logging.debug("Successfully connected to Redis")
            else:
                logging.error("Failed to connect to Redis")
        except redis.exceptions.ConnectionError as e:
            logging.error(f"Redis connection error: {e}")
            raise JSONResponse(
                content={"detail": f"Redis connection error: {e}"}, status_code=500
            )
        except Exception as e:
            logging.error(f"Error: {e}")
            raise JSONResponse(content={"detail": f"Error: {e}"}, status_code=500)
