import threading, time
from typing import Dict, Any, List

from app.config.symbols import SYMBOLS
from app.clients.firebase_rtdb import fb_get, normalize_daily_row

CACHE_REFRESH_SECS = 24 * 60 * 60  # 1 día

DAILY_STORE: Dict[str, Dict[str, Any]] = {}  # symbol -> { YYYYMMDD -> bar }
DAILY_UPDATED_AT_MS: int = 0
_cache_lock = threading.Lock()


def _now_ms() -> int:
    return int(time.time() * 1000)


def refresh_daily_cache_from_firebase() -> None:
    global DAILY_STORE, DAILY_UPDATED_AT_MS
    new_store: Dict[str, Dict[str, Any]] = {}
    for sym in SYMBOLS:
        data = fb_get(f"daily/{sym}")
        new_store[sym] = data if isinstance(data, dict) else {}
    with _cache_lock:
        DAILY_STORE = new_store
        DAILY_UPDATED_AT_MS = _now_ms()


def ensure_daily_cache_loaded() -> None:
    global DAILY_UPDATED_AT_MS
    if DAILY_UPDATED_AT_MS > 0:
        return
    refresh_daily_cache_from_firebase()


def read_daily_range(symbol: str, from_key: str, to_key: str) -> List[Dict[str, Any]]:
    ensure_daily_cache_loaded()
    with _cache_lock:
        data = DAILY_STORE.get(symbol) or {}

    if not data or not isinstance(data, dict):
        return []

    keys = [k for k in data.keys() if isinstance(k, str) and from_key <= k <= to_key]
    keys.sort()

    out: List[Dict[str, Any]] = []
    for k in keys:
        row = data.get(k) or {}
        norm = normalize_daily_row(row)
        if not norm:
            continue
        out.append({"key": k, **norm})
    return out


def put_day_in_ram(symbol: str, day_key: str, row: dict):
    with _cache_lock:
        DAILY_STORE.setdefault(symbol, {})
        DAILY_STORE[symbol][day_key] = row
