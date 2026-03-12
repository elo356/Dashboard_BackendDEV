import os
import threading
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.maintenance_service import daily_maintenance_run

TZ = ZoneInfo("America/New_York")
_started = False


def _today_key(now: datetime) -> str:
    return now.strftime("%Y%m%d")


def start_daily_scheduler(hour_et: int | None = None, minute_et: int | None = None) -> None:
    global _started
    if _started:
        return
    _started = True

    enabled = int(os.getenv("DAILY_SYNC_ENABLED", "1"))
    if not enabled:
        print("[DAILY] scheduler disabled by DAILY_SYNC_ENABLED=0")
        return

    target_hour = int(os.getenv("DAILY_SYNC_HOUR_ET", "18")) if hour_et is None else int(hour_et)
    target_minute = int(os.getenv("DAILY_SYNC_MINUTE_ET", "5")) if minute_et is None else int(minute_et)
    poll_sec = int(os.getenv("DAILY_SYNC_POLL_SEC", "30"))

    last_run_day: str | None = None

    def loop():
        nonlocal last_run_day
        while True:
            now = datetime.now(TZ)
            day_key = _today_key(now)
            due = (now.hour > target_hour) or (now.hour == target_hour and now.minute >= target_minute)

            if due and last_run_day != day_key:
                print(f"[DAILY] running maintenance at {now.isoformat()}")
                try:
                    out = daily_maintenance_run()
                    updated = len((out.get("sync") or {}).get("updated") or {})
                    print(f"[DAILY] done updated_symbols={updated}")
                except Exception as e:
                    print("[DAILY][ERR]", repr(e))
                finally:
                    last_run_day = day_key

            time.sleep(max(5, poll_sec))

    t = threading.Thread(target=loop, daemon=True)
    t.start()
