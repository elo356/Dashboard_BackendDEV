from pydantic import BaseModel
from typing import Optional

class Candle(BaseModel):
    t: int  # epoch ms
    o: float
    h: float
    l: float
    c: float
    v: float
    complete: bool = True

class CandleResponse(BaseModel):
    symbol: str
    timeframe: str
    stale: bool
    last_timestamp: Optional[int]
    candles: list[Candle]
