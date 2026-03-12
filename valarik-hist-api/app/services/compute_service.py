import time
from typing import Dict, Any, List

from app.config.symbols import SYMBOLS
from app.config.timeframes import (
    ensure_hist_tf,
    TF_LIMITS,
    needed_daily_for_tf,
    apply_tf_window,
)
from app.data.daily_store import read_daily_range
from app.services.aggregation import build_tf_bars
from app.services.formulas import mom_score_from_closes, compute_ptfav, compute_signal
from app.core.settings import TABLE_TTL_MS


# Per-symbol cache
CACHE: Dict[str, Any] = {}

# Table cache
TABLE_CACHE: Dict[str, Dict[str, Any]] = {}
TABLE_CACHE_MS: Dict[str, int] = {}


def _now_ms() -> int:
    return int(time.time() * 1000)


def clear_compute_caches():
    CACHE.clear()
    TABLE_CACHE.clear()
    TABLE_CACHE_MS.clear()


def _table_cache_valid(cache_id: str) -> bool:
    ts = TABLE_CACHE_MS.get(cache_id, 0)
    return ts > 0 and (_now_ms() - ts) < TABLE_TTL_MS


def _table_cache_get(cache_id: str):
    if _table_cache_valid(cache_id):
        return TABLE_CACHE.get(cache_id)
    return None


def _table_cache_set(cache_id: str, payload: dict):
    TABLE_CACHE[cache_id] = payload
    TABLE_CACHE_MS[cache_id] = _now_ms()


def compute_one(symbol: str, tf: str, from_key: str, to_key: str) -> Dict[str, Any]:
    try:
        tf = ensure_hist_tf(tf)
    except ValueError:
        return {"symbol": symbol, "tf": tf, "error": "tf_not_supported_in_hist_v1"}

    lim = TF_LIMITS[tf]
    maxBars = lim["maxBars"]
    minBars = lim["minBars"]
    needDaily = needed_daily_for_tf(tf, maxBars)

    daily = read_daily_range(symbol, from_key, to_key)
    if not daily:
        return {
            "symbol": symbol,
            "tf": tf,
            "barsCount": 0,
            "ptfav": 0.0,
            "dptfav": 0.0,
            "momScore": None,
            "signal": "HOLD",
            "lastKey": None,
            "dbgLen0": 0,
        }

    daily = apply_tf_window(tf, daily)
    if len(daily) > needDaily:
        daily = daily[-needDaily:]

    bars = build_tf_bars(tf, daily)
    if len(bars) > maxBars:
        bars = bars[-maxBars:]

    if len(bars) < minBars:
        return {
            "symbol": symbol,
            "tf": tf,
            "barsCount": len(bars),
            "ptfav": 0.0,
            "dptfav": 0.0,
            "momScore": None,
            "signal": "HOLD",
            "lastKey": bars[-1]["key"] if bars else None,
            "dbgLen0": len(daily),
        }

    closes = [float(x["c"]) for x in bars if x.get("c") is not None]
    mom = mom_score_from_closes(closes)
    ptfav, dptfav, trend = compute_ptfav(bars)
    sig = compute_signal(ptfav, mom)

    return {
        "symbol": symbol,
        "tf": tf,
        "barsCount": len(bars),
        "ptfav": float(ptfav),
        "dptfav": float(dptfav),
        "trend": int(trend),
        "momScore": float(mom) if mom is not None else None,
        "signal": sig,
        "lastKey": bars[-1]["key"] if bars else None,
        "dbgLen0": len(daily),
        "needDaily": needDaily,
        "limits": lim,
    }


def compute_table(tf: str, top: int, from_key: str, to_key: str) -> Dict[str, Any]:
    tf = ensure_hist_tf(tf)
    cache_id = f"{tf}|{from_key}|{to_key}"

    cached = _table_cache_get(cache_id)
    if cached:
        rows = cached["rows"]
        return {**cached, "top": rows[: max(1, int(top))]}

    rows: List[Dict[str, Any]] = []
    for sym in SYMBOLS:
        ck = f"{sym}|{tf}|{from_key}|{to_key}"
        r = CACHE.get(ck)
        if r is None:
            r = compute_one(sym, tf, from_key, to_key)
            CACHE[ck] = r
        rows.append(r)

    rows.sort(key=lambda x: float(x.get("ptfav") or 0.0), reverse=True)

    pos_sum = sum(
        float(r.get("ptfav") or 0.0)
        for r in rows
        if float(r.get("ptfav") or 0.0) > 0
    )
    for i, r in enumerate(rows, start=1):
        r["rankFlow"] = i
        pt = float(r.get("ptfav") or 0.0)
        r["flowPctTotal"] = (pt / pos_sum) if (pos_sum > 0 and pt > 0) else 0.0
        r["targetWt"] = 0.12 if i <= 3 else float(r["flowPctTotal"])

    payload = {
        "ok": True,
        "tf": tf,
        "symbols": len(SYMBOLS),
        "updatedAt": _now_ms(),
        "cached": True,
        "rows": rows,
        "top": rows[: max(1, int(top))],
    }
    _table_cache_set(cache_id, payload)
    return payload
