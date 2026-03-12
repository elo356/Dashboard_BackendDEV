import json
import os
import threading
import time
from urllib.request import urlopen, Request


_TD_DOMAIN = "api.twelvedata.com"
_TD_LOCK = threading.Lock()
_TD_WINDOW_START = time.time()
_TD_COUNT = 0


def _td_guard(url: str) -> None:
    global _TD_WINDOW_START, _TD_COUNT
    if _TD_DOMAIN not in url:
        return

    max_per_min = int(os.getenv("TD_MAX_PER_MIN_HARD", "500"))
    now = time.time()

    with _TD_LOCK:
        elapsed = now - _TD_WINDOW_START
        if elapsed >= 60:
            _TD_WINDOW_START = now
            _TD_COUNT = 0

        _TD_COUNT += 1
        if _TD_COUNT > max_per_min:
            msg = (
                f"[TD][FUSE] hard limit exceeded: {_TD_COUNT}/{max_per_min} req/min. "
                "Shutting down process."
            )
            print(msg)
            os._exit(1)


def get_json_url(url: str, timeout: int = 20) -> object:
    _td_guard(url)
    req = Request(url, headers={"User-Agent": "valarik-hist-api"})
    with urlopen(req, timeout=timeout) as r:
        raw = r.read().decode("utf-8")
        return json.loads(raw) if raw else None
