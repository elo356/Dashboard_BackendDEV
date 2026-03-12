from fastapi import APIRouter, HTTPException, Query
from typing import Any, Dict, List
import time

from app.config.timeframes_rt import ensure_rt_tf
from app.data.intraday_cache import get_range, get_last
from app.core.market import market_is_open
from app.services.compute_live_service import compute_table_live
from app.services.metric_contract import apply_metric_contract
from app.data.fund_cache import get as get_fund

router = APIRouter(prefix="/realtime", tags=["realtime"])


def _symbol_age_sec(tf: str, symbol: str) -> float | None:
    last = get_last(tf, symbol)
    if not last:
        return None
    return (int(time.time() * 1000) - int(last["key"])) / 1000

@router.get("/live/table2")
def live_table2(
    tf: str = Query("1m"),
    top: int = Query(50, ge=1, le=500),
):
    payload = compute_table_live(tf, top)

    rows = payload.get("top") or payload.get("rows") or []

    for r in rows:
        sym = r.get("symbol", "")
        meta = get_fund(sym) or {}
        prof = meta.get("profile", {}) or {}
        earn = meta.get("earnings", {}) or {}

        r["companyName"] = prof.get("name")
        r["sector"] = prof.get("sector")
        r["industry"] = prof.get("industry")
        r["earnings"] = earn
        age = _symbol_age_sec(tf, sym)
        r["ageSec"] = age
        r["staleSymbol"] = (age is None) or (age > 120)
        apply_metric_contract(r)

    stale = (not market_is_open()) or all(bool(r.get("staleSymbol")) for r in rows)

    return {
        "ok": True,
        "tf": payload.get("tf", tf),
        "top": top,
        "updatedAt": payload.get("updatedAt"),
        "cached": payload.get("cached", False),
        "symbols": payload.get("symbols", 0),
        "stale": stale,
        "rows": rows,
    }

@router.get("/candles")
def realtime_candles(
    symbol: str = Query(...),
    tf: str = Query("1m"),
    start_ms: int = Query(0),
    end_ms: int = Query(2_147_483_647_000),
    limit: int = Query(500, ge=1, le=5000),
):
    tf = ensure_rt_tf(tf)

    candles = get_range(tf, symbol, int(start_ms), int(end_ms))
    if candles:
        candles = candles[-limit:]
        return {
            "symbol": symbol,
            "tf": tf,
            "stale": (not market_is_open()),
            "lastKey": candles[-1]["key"],
            "candles": candles,
        }

    last = get_last(tf, symbol)
    if last:
        return {
            "symbol": symbol,
            "tf": tf,
            "stale": True,
            "lastKey": last["key"],
            "candles": [last],
        }

    raise HTTPException(status_code=404, detail="no_realtime_data")
