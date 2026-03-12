from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")

def market_is_open_now(now: datetime | None = None) -> bool:
    now = now or datetime.now(TZ)

    # weekend
    if now.weekday() >= 5:
        return False

    # regular session 9:30–16:00 ET
    t = now.time()
    return (t >= dtime(9, 30)) and (t < dtime(16, 0))


def market_is_open(now: datetime | None = None) -> bool:
    return market_is_open_now(now)
