from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Tuple
from zoneinfo import ZoneInfo

from fastapi import APIRouter, HTTPException, Query

from app.config.timeframes import (
    TF_LIMITS,
    apply_tf_window,
    ensure_hist_tf,
    needed_daily_for_tf,
)
from app.config.timeframes_rt import TF_MS, ensure_rt_tf
from app.core.market import market_is_open
from app.data.daily_store import read_daily_range
from app.data.intraday_cache import get_last, get_range
from app.services.aggregation import build_tf_bars
from app.services.live_metrics import compute_live_metrics, compute_live_metrics_series
from app.services.metric_contract import apply_metric_contract

router = APIRouter(prefix="/chart", tags=["chart"])

INTRADAY_TFS = {"1m", "5m", "15m", "30m", "1h"}
DEFAULT_FROM_KEY = "19000101"
DEFAULT_TO_KEY = "20991231"

# Configurable mapper: ajusta listas para aceptar variantes de tus datos.
CANDLE_MAPPER: Dict[str, List[str]] = {
    "t": ["key", "t", "time", "timestamp", "ts"],
    "o": ["o", "open"],
    "h": ["h", "high"],
    "l": ["l", "low"],
    "c": ["c", "close"],
    "v": ["v", "volume", "vol"],
}


def _pick(raw: Dict[str, Any], keys: List[str], default: Any = None) -> Any:
    for key in keys:
        if key in raw and raw.get(key) is not None:
            return raw.get(key)
    return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _ms_to_day_key(ms: int) -> str:
    dt = datetime.fromtimestamp(ms / 1000, tz=ZoneInfo("America/New_York"))
    return dt.strftime("%Y%m%d")


def _daily_key_to_ms(key: str) -> int:
    dt = datetime.strptime(key, "%Y%m%d").replace(tzinfo=ZoneInfo("America/New_York"))
    return int(dt.timestamp() * 1000)


def _key_to_ms(key: Any) -> int | None:
    if key is None:
        return None
    if isinstance(key, int):
        return key
    if isinstance(key, float):
        return int(key)
    if isinstance(key, str):
        raw = key.strip()
        if raw.isdigit():
            if len(raw) == 8:
                try:
                    return _daily_key_to_ms(raw)
                except ValueError:
                    return None
            try:
                return int(raw)
            except ValueError:
                return None
    return None


def _normalize_intraday(raw_bars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in raw_bars:
        t = _safe_int(_pick(row, CANDLE_MAPPER["t"]))
        c_raw = _pick(row, CANDLE_MAPPER["c"])
        if t <= 0 or c_raw is None:
            continue
        out.append(
            {
                "t": t,
                "o": _safe_float(_pick(row, CANDLE_MAPPER["o"], c_raw), _safe_float(c_raw)),
                "h": _safe_float(_pick(row, CANDLE_MAPPER["h"], c_raw), _safe_float(c_raw)),
                "l": _safe_float(_pick(row, CANDLE_MAPPER["l"], c_raw), _safe_float(c_raw)),
                "c": _safe_float(c_raw),
                "v": _safe_float(_pick(row, CANDLE_MAPPER["v"], 0.0), 0.0),
            }
        )
    out.sort(key=lambda x: x["t"])
    return out


def _normalize_daily(raw_bars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in raw_bars:
        key = row.get("key")
        c = row.get("c")
        if not isinstance(key, str) or c is None:
            continue
        try:
            t = _daily_key_to_ms(key)
        except ValueError:
            continue
        out.append(
            {
                "t": t,
                "o": _safe_float(row.get("o", c), _safe_float(c)),
                "h": _safe_float(row.get("h", c), _safe_float(c)),
                "l": _safe_float(row.get("l", c), _safe_float(c)),
                "c": _safe_float(c),
                "v": _safe_float(row.get("v", 0.0), 0.0),
            }
        )
    out.sort(key=lambda x: x["t"])
    return out


def _to_columnar(bars: List[Dict[str, Any]]) -> Dict[str, List[Any]]:
    return {
        "t": [bar["t"] for bar in bars],
        "o": [bar["o"] for bar in bars],
        "h": [bar["h"] for bar in bars],
        "l": [bar["l"] for bar in bars],
        "c": [bar["c"] for bar in bars],
        "v": [bar["v"] for bar in bars],
    }


def _apply_lod(bars: List[Dict[str, Any]], px: int | None, tf_used: str) -> Tuple[List[Dict[str, Any]], str, int | None]:
    if px is None or px <= 0:
        return bars, "raw", None

    max_bars = px * 2
    if len(bars) <= max_bars:
        return bars, "raw", None

    bucket_size = max(1, (len(bars) + max_bars - 1) // max_bars)
    reduced: List[Dict[str, Any]] = []
    for i in range(0, len(bars), bucket_size):
        chunk = bars[i : i + bucket_size]
        if not chunk:
            continue
        reduced.append(
            {
                "t": chunk[0]["t"],
                "o": chunk[0]["o"],
                "h": max(x["h"] for x in chunk),
                "l": min(x["l"] for x in chunk),
                "c": chunk[-1]["c"],
                "v": sum(x["v"] for x in chunk),
            }
        )

    tf_ms = TF_MS.get(tf_used) if tf_used in TF_MS else (86_400_000 if tf_used == "1D" else None)
    bucket_ms = (tf_ms * bucket_size) if tf_ms else None
    return reduced, "lod", bucket_ms


@router.get("/bars")
def chart_bars(
    symbol: str = Query(...),
    tf: str = Query("1m"),
    from_ms: int = Query(0),
    to_ms: int = Query(2_147_483_647_000),
    limit: int = Query(2000, ge=1, le=20000),
    px: int | None = Query(None, ge=1),
):
    raw_tf = (tf or "").strip()
    tf_lc = raw_tf.lower()
    tf_is_1d = raw_tf == "1D" or tf_lc == "1d"

    bars: List[Dict[str, Any]] = []
    source = "realtime"
    tf_used = raw_tf

    if tf_lc in INTRADAY_TFS:
        try:
            tf_used = ensure_rt_tf(raw_tf)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc))

        bars = _normalize_intraday(get_range(tf_used, symbol, int(from_ms), int(to_ms)))
        if not bars:
            last = get_last(tf_used, symbol)
            if last:
                bars = _normalize_intraday([last])
    elif tf_is_1d:
        source = "historical"
        tf_used = "1D"
        try:
            from_key = _ms_to_day_key(int(from_ms))
            to_key = _ms_to_day_key(int(to_ms))
        except (TypeError, ValueError, OSError, OverflowError):
            from_key = DEFAULT_FROM_KEY
            to_key = DEFAULT_TO_KEY
        bars = _normalize_daily(read_daily_range(symbol, from_key, to_key))
    else:
        raise HTTPException(status_code=400, detail="tf_not_supported_in_chart")

    if bars:
        bars = bars[-limit:]

    bars, mode, bucket_ms = _apply_lod(bars, px, tf_used)
    cols = _to_columnar(bars)
    last_key = cols["t"][-1] if cols["t"] else None

    payload: Dict[str, Any] = {
        "ok": True,
        "symbol": symbol,
        "tf_used": tf_used,
        "source": source,
        "stale": (not market_is_open()) if source == "realtime" else False,
        "lastKey": last_key,
        "t": cols["t"],
        "o": cols["o"],
        "h": cols["h"],
        "l": cols["l"],
        "c": cols["c"],
        "v": cols["v"],
        "mode": mode,
    }
    if bucket_ms is not None:
        payload["bucket_ms"] = bucket_ms
    return payload


@router.get("/flow-trend")
def chart_flow_trend(
    symbol: str = Query(...),
    tf: str = Query("1m"),
    bars_needed: int = Query(120, ge=2, le=5000),
    from_key: str = Query(DEFAULT_FROM_KEY),
    to_key: str = Query(DEFAULT_TO_KEY),
):
    raw_tf = (tf or "").strip()
    source = "realtime"
    tf_used = raw_tf
    bars: List[Dict[str, Any]] = []

    try:
        tf_used = ensure_rt_tf(raw_tf)
        last = get_last(tf_used, symbol)
        if last:
            end_ms = int(last["key"])
            start_ms = end_ms - (max(1, int(bars_needed)) * TF_MS[tf_used] * 3)
            bars = get_range(tf_used, symbol, start_ms, end_ms)
            bars = bars[-max(1, int(bars_needed)):] if bars else []
    except ValueError:
        try:
            tf_used = ensure_hist_tf(raw_tf)
        except ValueError:
            raise HTTPException(status_code=400, detail="tf_not_supported_in_chart")

        source = "historical"
        daily = read_daily_range(symbol, from_key, to_key)
        if daily:
            lim = TF_LIMITS[tf_used]
            need_daily = needed_daily_for_tf(tf_used, lim["maxBars"])
            daily = apply_tf_window(tf_used, daily)
            if len(daily) > need_daily:
                daily = daily[-need_daily:]
            bars = build_tf_bars(tf_used, daily)
            if len(bars) > lim["maxBars"]:
                bars = bars[-lim["maxBars"]:]
            bars = bars[-max(1, int(bars_needed)):] if bars else []

    metric_steps = compute_live_metrics_series(bars)
    summary = compute_live_metrics(bars) if len(bars) >= 2 else {
        "ptfav": 0.0,
        "dptfav": 0.0,
        "trend_dir": 0,
        "mom_score": 0.0,
        "flow_pct": 0.0,
        "trend_accel_pct": 0.0,
    }

    points: List[Dict[str, Any]] = []
    for idx, step in enumerate(metric_steps):
        bar = bars[idx + 1] if (idx + 1) < len(bars) else {}
        key = step.get("key")
        t = _key_to_ms(key)
        flow_pct = float(step.get("flow_pct") or 0.0)
        dptfav = float(step.get("dpt") or 0.0)
        trend_dir = int(step.get("trend") or 0)
        mom_score = float(step.get("mom_score") or 0.0)
        trend_accel = float(step.get("trend_accel_pct") or 0.0)
        ptfav = float(step.get("ptfavAcc") or 0.0)
        is_partial = bool(bar.get("is_partial", source == "realtime"))

        point = {
            "key": key,
            "t": t,
            "time": t,
            "flow_raw": ptfav,
            "flow_pct": flow_pct,
            "trend_dir": trend_dir,
            "mom_score": mom_score,
            "trend_accel_pct": trend_accel,
            "is_partial": is_partial,
            "flow": ptfav,
            "trend": mom_score,
            "momScore": mom_score,
            "dptfav": dptfav,
            # Compat: en frontend "trend" es realmente momScore.
            "trendValue": mom_score,
            "dptfavValue": dptfav,
            # Compatibilidad con el frontend anterior.
            "mom_accel_pct": trend_accel,
            "volume": float(step.get("volume") or 0.0),
            "close": float(step.get("close") or 0.0),
            "open": float(bar.get("o") or step.get("close") or 0.0),
            "high": float(bar.get("h") or step.get("close") or 0.0),
            "low": float(bar.get("l") or step.get("close") or 0.0),
        }
        point["ptfav"] = ptfav
        point["flowPctTotal"] = flow_pct
        points.append(apply_metric_contract(point))

    is_partial = bool(bars[-1].get("is_partial", source == "realtime")) if bars else False
    payload = {
        "ok": True,
        "schemaVersion": 2,
        "symbol": symbol,
        "tf_used": tf_used,
        "source": source,
        "barsCount": len(bars),
        "lastKey": bars[-1]["key"] if bars else None,
        "stale": (not market_is_open()) if source == "realtime" else False,
        "flow_raw": summary["ptfav"],
        "flow_pct": summary["flow_pct"],
        "trend_dir": summary["trend_dir"],
        "mom_score": summary["mom_score"],
        "trend_accel_pct": summary["trend_accel_pct"],
        "is_partial": is_partial,
        "ptfav": summary["ptfav"],
        "dptfav": summary["dptfav"],
        "flow": points[-1]["flow"] if points else 0.0,
        "trend": points[-1]["trend"] if points else 0.0,
        "legacyAliases": {
            "flow": "flow_raw",
            "trend": "mom_score",
            "momScore": "mom_score",
            "ptfav": "flow_raw",
        },
        "points": points,
    }
    payload["flowPctTotal"] = payload["flow_pct"]
    payload["momScore"] = payload["mom_score"]
    apply_metric_contract(payload)
    return payload
