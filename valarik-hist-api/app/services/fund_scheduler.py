import os
import threading
import time
from datetime import datetime, date
from zoneinfo import ZoneInfo

from app.services.fund_refresh import refresh_fundamentals_once

_started = False


def start_fund_scheduler() -> None:
    global _started
    if _started:
        return
    _started = True

    enabled = os.getenv("FUND_SCHED_ENABLED", "1") == "1"
    if not enabled:
        print("[FUND][SCHED] disabled by FUND_SCHED_ENABLED=0")
        return

    tz_name = os.getenv("FUND_SCHED_TZ", "America/New_York")
    hour = int(os.getenv("FUND_SCHED_HOUR", "7"))
    minute = int(os.getenv("FUND_SCHED_MINUTE", "30"))
    limit = int(os.getenv("FUND_SCHED_LIMIT", "0"))
    offset = int(os.getenv("FUND_SCHED_OFFSET", "0"))
    sleep_ms = int(os.getenv("FUND_SCHED_SLEEP_MS", "350"))
    missing_only = 1 if os.getenv("FUND_SCHED_MISSING_ONLY", "1") == "1" else 0
    include_earnings = 1 if os.getenv("FUND_SCHED_INCLUDE_EARNINGS", "0") == "1" else 0
    max_per_min = int(os.getenv("FUND_SCHED_MAX_PER_MIN", "180"))

    tz = ZoneInfo(tz_name)

    def loop():
        last_run_day: date | None = None
        while True:
            now = datetime.now(tz)

            due_now = now.hour == hour and now.minute == minute
            already_ran_today = last_run_day == now.date()

            if due_now and not already_ran_today:
                print(
                    "[FUND][SCHED] start "
                    f"at {now.isoformat()} "
                    f"(missing_only={missing_only}, include_earnings={include_earnings}, max_per_min={max_per_min})"
                )
                try:
                    out = refresh_fundamentals_once(
                        limit=limit,
                        offset=offset,
                        sleep_ms=sleep_ms,
                        missing_only=missing_only,
                        include_earnings=include_earnings,
                        max_per_min=max_per_min,
                    )
                    print("[FUND][SCHED] done", out)
                except Exception as e:
                    print("[FUND][SCHED][ERR]", repr(e))
                last_run_day = now.date()

            time.sleep(20)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
