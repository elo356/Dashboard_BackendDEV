import json
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from typing import Any, Dict, Optional

from app.core.settings import FIREBASE_DATABASE_URL, FIREBASE_AUTH
from app.clients.http import get_json_url


def fb_get(path: str) -> Any:
    url = f"{FIREBASE_DATABASE_URL}/{path}.json"
    if FIREBASE_AUTH:
        url += f"?auth={FIREBASE_AUTH}"
    try:
        req = Request(url, headers={"User-Agent": "valarik-hist-api"})
        with urlopen(req, timeout=20) as r:
            raw = r.read().decode("utf-8")
            return json.loads(raw) if raw else None
    except Exception as e:
        return {"__error__": f"{type(e).__name__}: {e}"}


def fb_put_day(symbol: str, day_key: str, row: dict):
    url = f"{FIREBASE_DATABASE_URL}/daily/{symbol}/{day_key}.json"
    if FIREBASE_AUTH:
        url += f"?auth={FIREBASE_AUTH}"

    req = Request(
        url,
        data=json.dumps(row).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="PUT",
    )
    with urlopen(req, timeout=20) as r:
        r.read()


def fb_last_key(symbol: str) -> Optional[str]:
    base = f"{FIREBASE_DATABASE_URL}/daily/{symbol}.json"
    qs = {"orderBy": '"$key"', "limitToLast": 1}
    if FIREBASE_AUTH:
        qs["auth"] = FIREBASE_AUTH
    url = base + "?" + urlencode(qs)

    try:
        obj = get_json_url(url)
        if not obj or not isinstance(obj, dict):
            return None
        return next(iter(obj.keys()))
    except Exception:
        return None


def fb_get_range_days(symbol: str, from_key: str, to_key: str) -> Dict[str, Any]:
    base = f"{FIREBASE_DATABASE_URL}/daily/{symbol}.json"
    qs = {
        "orderBy": '"$key"',
        "startAt": f'"{from_key}"',
        "endAt": f'"{to_key}"',
    }
    if FIREBASE_AUTH:
        qs["auth"] = FIREBASE_AUTH
    url = base + "?" + urlencode(qs)
    obj = get_json_url(url)
    return obj if isinstance(obj, dict) else {}


def normalize_daily_row(row: Any) -> Optional[Dict[str, Any]]:
    if not row or not isinstance(row, dict):
        return None
    o = row.get("o", row.get("open"))
    h = row.get("h", row.get("high"))
    l = row.get("l", row.get("low"))
    c = row.get("c", row.get("close"))
    v = row.get("v", row.get("volume"))
    if c is None:
        return None
    return {
        "o": float(o) if o is not None else None,
        "h": float(h) if h is not None else None,
        "l": float(l) if l is not None else None,
        "c": float(c),
        "v": float(v) if v is not None else 0.0,
    }
