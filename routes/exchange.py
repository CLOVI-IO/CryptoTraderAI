from fastapi import APIRouter, HTTPException
import importlib

router = APIRouter()


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
        raise HTTPException(status_code=500, detail=str(e))
