from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from typing import Optional, List

NY = ZoneInfo("America/New_York")


def prev_trading_day_key(now: Optional[datetime] = None) -> str:
    if now is None:
        now = datetime.now(NY)
    d = now.date() - timedelta(days=1)
    while d.weekday() >= 5:  # Sat/Sun
        d -= timedelta(days=1)
    return d.strftime("%Y%m%d")


def date_range_keys(from_key: str, to_key: str) -> List[str]:
    start = datetime.strptime(from_key, "%Y%m%d").date()
    end = datetime.strptime(to_key, "%Y%m%d").date()
    out: List[str] = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            out.append(d.strftime("%Y%m%d"))
        d += timedelta(days=1)
    return out


def expected_weekday_keys(from_key: str, to_key: str) -> List[str]:
    start = datetime.strptime(from_key, "%Y%m%d").date()
    end = datetime.strptime(to_key, "%Y%m%d").date()
    out: List[str] = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            out.append(d.strftime("%Y%m%d"))
        d += timedelta(days=1)
    return out
