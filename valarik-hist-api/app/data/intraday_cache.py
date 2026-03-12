from __future__ import annotations

import copy
import os, json, time
import threading
from pathlib import Path
from typing import Any, Dict, List, Optional
from bisect import bisect_left, bisect_right

# =========================
# IN-MEMORY STORE
# =========================
_store: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}  # tf -> symbol -> bars
_store_lock = threading.RLock()


def _normalize_bar(bar: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(bar, dict):
        return None

    try:
        key = int(bar["key"])
        if key <= 0:
            return None

        normalized = {
            "key": key,
            "o": float(bar["o"]),
            "h": float(bar["h"]),
            "l": float(bar["l"]),
            "c": float(bar["c"]),
            "v": float(bar.get("v") or 0.0),
        }
    except (KeyError, TypeError, ValueError):
        return None

    for fld in ("o", "h", "l", "c"):
        if not isinstance(normalized[fld], float):
            return None

    # Preserve known metadata used by realtime/live buckets.
    for fld in ("bucket_tf", "source_tf", "session_anchor", "is_partial"):
        if fld in bar:
            normalized[fld] = bar[fld]

    return normalized


def _sorted_keys(arr: List[Dict[str, Any]]) -> List[int]:
    return [int(x["key"]) for x in arr]


def _sanitize_store(raw_store: Any) -> Dict[str, Dict[str, List[Dict[str, Any]]]]:
    sanitized: Dict[str, Dict[str, List[Dict[str, Any]]]] = {}
    if not isinstance(raw_store, dict):
        return sanitized

    for tf, tf_store in raw_store.items():
        if not isinstance(tf, str) or not isinstance(tf_store, dict):
            continue

        clean_tf: Dict[str, List[Dict[str, Any]]] = {}
        for symbol, bars in tf_store.items():
            if not isinstance(symbol, str) or not isinstance(bars, list):
                continue

            clean_bars = [b for raw_bar in bars if (b := _normalize_bar(raw_bar)) is not None]
            clean_bars.sort(key=lambda x: int(x["key"]))
            if clean_bars:
                clean_tf[symbol] = clean_bars

        if clean_tf:
            sanitized[tf] = clean_tf

    return sanitized

def _arr(tf: str, symbol: str) -> List[Dict[str, Any]]:
    return _store.setdefault(tf, {}).setdefault(symbol, [])

def upsert_bar(tf: str, symbol: str, bar: Dict[str, Any]) -> None:
    """
    Inserta o reemplaza una vela por su key (epoch ms).
    Mantiene la lista ordenada por key.
    """
    normalized = _normalize_bar(bar)
    if normalized is None:
        raise ValueError(f"invalid_intraday_bar tf={tf} symbol={symbol}")

    with _store_lock:
        arr = _arr(tf, symbol)
        k = int(normalized["key"])
        keys = _sorted_keys(arr)
        i = bisect_left(keys, k)
        if i < len(arr) and int(arr[i]["key"]) == k:
            arr[i] = normalized
        else:
            arr.insert(i, normalized)

def get_range(tf: str, symbol: str, start_key: int, end_key: int) -> List[Dict[str, Any]]:
    with _store_lock:
        arr = _arr(tf, symbol)
        if not arr:
            return []
        keys = _sorted_keys(arr)
        i = bisect_left(keys, int(start_key))
        j = bisect_right(keys, int(end_key))
        return arr[i:j]

def get_last(tf: str, symbol: str) -> Optional[Dict[str, Any]]:
    with _store_lock:
        arr = _arr(tf, symbol)
        return arr[-1] if arr else None

def trim_older_than(tf: str, symbol: str, min_key: int) -> None:
    with _store_lock:
        arr = _arr(tf, symbol)
        if not arr:
            return
        keys = _sorted_keys(arr)
        i = bisect_left(keys, int(min_key))
        if i > 0:
            del arr[:i]

def get_global_last_key(tf: str = "1m") -> Optional[int]:
    with _store_lock:
        mx = None
        for _, arr in _store.get(tf, {}).items():
            if arr:
                k = int(arr[-1]["key"])
                mx = k if mx is None else max(mx, k)
        return mx

# =========================
# SNAPSHOT TO DISK
# =========================
DEFAULT_CACHE_DIR = str(Path.home() / ".cache" / "valarik")  # dev-safe default
_configured_cache_dir = Path(os.getenv("CACHE_DIR", DEFAULT_CACHE_DIR))
try:
    _configured_cache_dir.mkdir(parents=True, exist_ok=True)
    CACHE_DIR = _configured_cache_dir
except PermissionError:
    CACHE_DIR = Path("/tmp/valarik_cache")
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    print(f"[SNAPSHOT][WARN] CACHE_DIR not writable: {_configured_cache_dir}. Using {CACHE_DIR}")

SNAPSHOT_FILE = CACHE_DIR / "intraday_store_latest.json"
_snapshot_last = 0

def _atomic_write(path: Path, obj: Any) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False))
    tmp.replace(path)

def save_snapshot_periodic(force: bool = False) -> None:
    """
    Guarda snapshot del _store cada X segundos (default 60s) o force=True
    """
    global _snapshot_last
    every = int(os.getenv("SNAPSHOT_EVERY_SEC", "60"))
    now = time.time()
    if (not force) and (now - _snapshot_last < every):
        return
    try:
        with _store_lock:
            payload = {"savedAt": int(now * 1000), "store": copy.deepcopy(_store)}
        _atomic_write(SNAPSHOT_FILE, payload)
        _snapshot_last = now
    except Exception as e:
        print("[SNAPSHOT][ERR]", repr(e))

def load_snapshot_on_start() -> None:
    """
    Restaura _store desde disco si existe.
    """
    global _store
    if not SNAPSHOT_FILE.exists():
        print("[SNAPSHOT] no snapshot found")
        return
    try:
        payload = json.loads(SNAPSHOT_FILE.read_text())
        store = _sanitize_store(payload.get("store"))
        with _store_lock:
            _store = store
        print("[SNAPSHOT] restored savedAt=", payload.get("savedAt"), "tfs=", len(store))
    except Exception as e:
        print("[SNAPSHOT][ERR] restore", repr(e))
