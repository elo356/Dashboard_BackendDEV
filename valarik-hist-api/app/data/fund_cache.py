import os, json, time
from pathlib import Path
from typing import Any, Dict, Optional

CACHE_DIR = Path(os.getenv("CACHE_DIR", "/var/lib/valarik_cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)

SNAPSHOT_FILE = CACHE_DIR / "fund_cache_latest.json"

_fund: Dict[str, Dict[str, Any]] = {}
_last_save = 0.0


def _atomic_write(path: Path, obj: Any) -> None:
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False))
    tmp.replace(path)


def load_snapshot() -> None:
    global _fund
    if not SNAPSHOT_FILE.exists():
        print("[FUND] no snapshot found")
        return
    try:
        payload = json.loads(SNAPSHOT_FILE.read_text())
        data = payload.get("fund")
        if isinstance(data, dict):
            _fund = data
            print("[FUND] restored savedAt=", payload.get("savedAt"))
    except Exception as e:
        print("[FUND][ERR] restore", repr(e))


def save_snapshot(force: bool = False) -> None:
    global _last_save
    every = int(os.getenv("FUND_SNAPSHOT_EVERY_SEC", "60"))
    now = time.time()
    if (not force) and (now - _last_save < every):
        return
    try:
        payload = {"savedAt": int(now * 1000), "fund": _fund}
        _atomic_write(SNAPSHOT_FILE, payload)
        _last_save = now
    except Exception as e:
        print("[FUND][ERR] save", repr(e))


def get(symbol: str) -> Optional[Dict[str, Any]]:
    return _fund.get(symbol)


def set_symbol(symbol: str, obj: Dict[str, Any]) -> None:
    _fund[symbol] = obj
