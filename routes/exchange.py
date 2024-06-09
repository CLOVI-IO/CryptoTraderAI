from fastapi import APIRouter, HTTPException
import importlib
from dotenv import load_dotenv, find_dotenv
import os
import logging
from redis_handler import RedisHandler  # Import RedisHandler if needed in the future

router = APIRouter()

# Load environment variables
load_dotenv(find_dotenv())

# Configure logging
logging.basicConfig(level=logging.INFO)

# Get Redis connection details from environment variables (for future use if needed)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
REDIS_DB = int(os.getenv("REDIS_DB", 0))


@router.get("/exchange/")
def get_enabled_exchanges():
    return {"enabled_exchanges": ["crypto_com"]}


@router.get("/exchange/{exchange_name}")
def get_exchange_data(exchange_name: str):
    try:
        exchange_module = importlib.import_module(f"exchanges.{exchange_name}")
        exchange_class = getattr(exchange_module, exchange_name.capitalize())
        exchange_instance = exchange_class()
        data = exchange_instance.get_data()
        return data
    except ImportError:
        raise HTTPException(status_code=404, detail="Exchange not found")
    except Exception as e:
        logging.error(f"Error retrieving exchange data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
