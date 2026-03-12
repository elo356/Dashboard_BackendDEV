from typing import Dict

RT_TFS = {"1m", "5m", "15m", "30m", "1h", "4h", "6h", "12h"}

_RT_TF_ALIASES = {
    "1m": "1m",
    "m1": "1m",
    "1min": "1m",
    "1minute": "1m",
    "5m": "5m",
    "m5": "5m",
    "5min": "5m",
    "5minute": "5m",
    "15m": "15m",
    "m15": "15m",
    "15min": "15m",
    "15minute": "15m",
    "30m": "30m",
    "m30": "30m",
    "30min": "30m",
    "30minute": "30m",
    "1h": "1h",
    "h1": "1h",
    "60m": "1h",
    "60min": "1h",
    "1hr": "1h",
    "1hour": "1h",
    "4h": "4h",
    "h4": "4h",
    "240m": "4h",
    "240min": "4h",
    "4hr": "4h",
    "4hour": "4h",
    "6h": "6h",
    "h6": "6h",
    "360m": "6h",
    "360min": "6h",
    "6hr": "6h",
    "6hour": "6h",
    "12h": "12h",
    "h12": "12h",
    "720m": "12h",
    "720min": "12h",
    "12hr": "12h",
    "12hour": "12h",
}

TF_MS: Dict[str, int] = {
    "1m": 60_000,
    "5m": 5 * 60_000,
    "15m": 15 * 60_000,
    "30m": 30 * 60_000,
    "1h": 60 * 60_000,
    "4h": 4 * 60 * 60_000,
    "6h": 6 * 60 * 60_000,
    "12h": 12 * 60 * 60_000,
}

AGG_TFS = ["5m", "15m", "30m", "1h", "4h", "6h", "12h"]

def ensure_rt_tf(tf: str) -> str:
    raw = (tf or "").strip()
    normalized = _RT_TF_ALIASES.get(raw.lower(), raw.lower())
    if normalized not in RT_TFS:
        raise ValueError("tf_not_supported_in_realtime_v1")
    return normalized
