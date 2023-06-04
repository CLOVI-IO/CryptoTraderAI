from pydantic import BaseModel, Field
from typing import Optional, List


class Order(BaseModel):
    action: Optional[str]
    contracts: Optional[str]
    price: Optional[str]
    id: Optional[str]
    comment: Optional[str]
    alert_message: Optional[str]


class StrategyInfo(BaseModel):
    position_size: Optional[str]
    order: Order
    market_position: Optional[str]
    market_position_size: Optional[str]
    prev_market_position: Optional[str]
    prev_market_position_size: Optional[str]


class Plots(BaseModel):
    plot_0: Optional[str]
    plot_1: Optional[str]


class CurrentInfo(BaseModel):
    fire_time: Optional[str]
    plots: Plots


class BarInfo(BaseModel):
    open: Optional[str]
    high: Optional[str]
    low: Optional[str]
    close: Optional[str]
    volume: Optional[str]
    time: Optional[str]


class AlertInfo(BaseModel):
    exchange: Optional[str]
    ticker: Optional[str]
    price: Optional[str]
    volume: Optional[str]
    interval: Optional[str]


class Signal(BaseModel):
    alert_info: AlertInfo
    bar_info: BarInfo
    current_info: CurrentInfo
    strategy_info: StrategyInfo


class Payload(BaseModel):
    signal: Signal
