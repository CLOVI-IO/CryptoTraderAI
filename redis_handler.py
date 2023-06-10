import os
from rediscluster import RedisCluster
import logging


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
            startup_nodes = [{"host": self.REDIS_HOST, "port": str(self.REDIS_PORT)}]

            # Only use the password if it's provided
            if self.REDIS_PASSWORD:
                self.redis_client = RedisCluster.RedisCluster(
                    startup_nodes=startup_nodes,
                    decode_responses=True,
                    skip_full_coverage_check=True,
                    password=self.REDIS_PASSWORD,
                )
            else:
                self.redis_client = RedisCluster.RedisCluster(
                    startup_nodes=startup_nodes,
                    decode_responses=True,
                    skip_full_coverage_check=True,
                )

            logging.debug("Successfully created RedisCluster.RedisCluster instance")

            # Try a simple operation to check if the connection is established
            if self.redis_client.ping():
                logging.debug("Successfully connected to Redis")
            else:
                logging.error("Failed to connect to Redis")
        except RedisCluster.exceptions.ClusterDownError as e:
            logging.error(f"Redis cluster error: {e}")
        except Exception as e:
            logging.error(f"Error: {e}")
