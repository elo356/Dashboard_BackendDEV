from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from app.config.timeframes_rt import TF_MS

NY = ZoneInfo("America/New_York")


def _previous_trading_day(dt: datetime) -> datetime:
    prev = dt
    while True:
        prev -= timedelta(days=1)
        if prev.weekday() < 5:
            return prev


def _session_start_ms(ts_ms: int) -> int:
    dt = datetime.fromtimestamp(ts_ms / 1000, NY)
    session_start = dt.replace(hour=9, minute=30, second=0, microsecond=0)
    if dt < session_start:
        session_start = _previous_trading_day(session_start)
    return int(session_start.timestamp() * 1000)


def bucket_start(ts_ms: int, tf: str) -> int:
    if tf in ("4h", "6h", "12h"):
        dt = datetime.fromtimestamp(ts_ms / 1000, NY)
        session_start_ms = _session_start_ms(ts_ms)
        session_start = datetime.fromtimestamp(session_start_ms / 1000, NY)

        if tf == "12h":
            # 1 vela por sesión completa
            return session_start_ms

        if tf == "6h":
            # 2 bloques intrasesión para diferenciarlo de 12h.
            mid_block = session_start + timedelta(hours=3)
            if dt >= mid_block:
                return int(mid_block.timestamp() * 1000)
            return int(session_start.timestamp() * 1000)

        if tf == "4h":
            # 2 velas por sesión
            second_block = session_start + timedelta(hours=4)
            if dt >= second_block:
                return int(second_block.timestamp() * 1000)
            return int(session_start.timestamp() * 1000)

    # TF normales (1m,5m,15m,30m,1h)
    tf_ms = TF_MS[tf]
    return (int(ts_ms) // tf_ms) * tf_ms

def _bucket_metadata(ts_ms: int, tf: str, source_tf: str) -> Dict[str, Any]:
    meta: Dict[str, Any] = {
        "bucket_tf": tf,
        "source_tf": source_tf,
        # Las barras agregadas realtime son barras vivas mientras el bucket siga abierto.
        "is_partial": True,
    }
    if tf in ("4h", "6h", "12h"):
        meta["session_anchor"] = _session_start_ms(ts_ms)
    return meta


def merge_into(
    existing: Optional[Dict[str, Any]],
    bar_1m: Dict[str, Any],
    bucket_key: int,
    tf: str,
    source_tf: str,
) -> Dict[str, Any]:
    merged = {
        "key": bucket_key,
        "o": float(bar_1m["o"]) if existing is None else float(existing["o"]),
        "h": float(bar_1m["h"]) if existing is None else max(float(existing["h"]), float(bar_1m["h"])),
        "l": float(bar_1m["l"]) if existing is None else min(float(existing["l"]), float(bar_1m["l"])),
        "c": float(bar_1m["c"]),
        "v": float(bar_1m.get("v") or 0.0)
        if existing is None
        else float(existing.get("v") or 0.0) + float(bar_1m.get("v") or 0.0),
    }
    merged.update(_bucket_metadata(int(bar_1m["key"]), tf, source_tf))
    return merged
