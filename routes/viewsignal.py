# viewsignal.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from shared_state import state  # Import the shared state

# Output json Exemple
# {
# "signal": {
# "alert_info": {
# "exchange": "BINANCE",
# "ticker": "SOLUSDT",
# "price": "20.96",
# "volume": "256.81",
# "interval": "1"
# },
# "bar_info": {
# "open": "20.94",
# "high": "20.96",
# "low": "20.94",
# "close": "20.96",
# "volume": "256.81",
# "time": "2023-05-14T18:32:00Z"
# },
# "current_info": {
# "fire_time": "2023-05-14T18:32:46Z",
# "plots": {
# "plot_0": "20.936280714571126",
# "plot_1": "20.94"
# }
# },
# "strategy_info": {
# "position_size": "{{strategy.position_size}}",
# "order": {
# "action": "Open Long",
# "contracts": "{{strategy.order.contracts}}",
# "price": "{{strategy.order.price}}",
# "id": "{{strategy.order.id}}",
# "comment": "{{strategy.order.comment}}",
# "alert_message": "{{strategy.order.alert_message}}"
# },
# "market_position": "{{strategy.market_position}}",
# "market_position_size": "{{strategy.market_position_size}}",
# "prev_market_position": "{{strategy.prev_market_position}}",
# "prev_market_position_size": "{{strategy.prev_market_position_size}}"
# }
# }
# }


router = APIRouter()


@router.get("/viewsignal")
def view_signal():
    try:
        print(f"Retrieving signal: {state['last_signal']}")
        if state["last_signal"]:
            return {"signal": state["last_signal"]}
        else:
            return {"signal": "No signal"}
    except Exception as e:
        print(f"Failed to retrieve signal: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "An error occurred while retrieving the signal"},
        )
