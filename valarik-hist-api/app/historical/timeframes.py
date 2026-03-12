from typing import Dict

HIST_TFS = {"1D", "1W", "1M", "1Y"}

_HIST_TF_ALIASES = {
    "1d": "1D",
    "d": "1D",
    "day": "1D",
    "1day": "1D",
    "daily": "1D",
    "1w": "1W",
    "w": "1W",
    "week": "1W",
    "1week": "1W",
    "weekly": "1W",
    "1m": "1M",
    "m": "1M",
    "mo": "1M",
    "month": "1M",
    "1month": "1M",
    "monthly": "1M",
    "1y": "1Y",
    "y": "1Y",
    "year": "1Y",
    "1year": "1Y",
    "yearly": "1Y",
}

TF_WINDOW_DAYS: Dict[str, int] = {"1D": 180, "1W": 260, "1M": 1000, "1Y": 1800}

TF_LIMITS = {
    "1D": {"maxBars": 120, "minBars": 60},
    "1W": {"maxBars": 60, "minBars": 30},
    "1M": {"maxBars": 60, "minBars": 20},
    "1Y": {"maxBars": 10, "minBars": 5},
}


def ensure_hist_tf(tf: str) -> str:
    raw = (tf or "").strip()
    normalized = _HIST_TF_ALIASES.get(raw.lower(), raw.upper())
    if normalized not in HIST_TFS:
        raise ValueError("tf_not_supported_in_hist_v1")
    return normalized


def needed_daily_for_tf(tf: str, max_bars: int) -> int:
    if tf == "1D":
        return int(max_bars * 1.5)
    if tf == "1W":
        return int(max_bars * 5 * 1.25)
    if tf == "1M":
        return int(max_bars * 21 * 1.15)
    if tf == "1Y":
        return int(max_bars * 252 * 1.05)
    return int(max_bars * 2)


def apply_tf_window(tf: str, daily: list[dict]) -> list[dict]:
    win = TF_WINDOW_DAYS.get(tf)
    if not win or len(daily) <= win:
        return daily
    return daily[-win:]
