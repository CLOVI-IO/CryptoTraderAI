import redis
from dotenv import load_dotenv
import os

# load environment variables from .env file
load_dotenv()

# get environment variables
REDIS_HOST = os.getenv("REDIS_HOST")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))  # use 6379 as default if not set
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")  # will be None if not set

try:
    # create a redis client
    r = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, password=REDIS_PASSWORD)

    # run a command to test the connection
    response = r.ping()

    # if the connection is successful and Redis is responsive, this will print "PONG"
    print(response)
except Exception as e:
    # print any connection errors
    print(f"Error: {str(e)}")
