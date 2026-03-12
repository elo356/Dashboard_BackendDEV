import os, time, threading
from typing import Callable, Dict, Any, List

from app.services.realtime_service import symbols, update_aggregates_from_1m
from app.data.intraday_cache import upsert_bar, trim_older_than

_started = False

def start_realtime_scheduler(fetch_1m: Callable[[str, int], List[Dict[str, Any]]]) -> None:
    global _started
    if _started:
        return
    _started = True

    interval = int(os.getenv("INGEST_INTERVAL_SEC", "60"))

    def loop():
        while True:
            n_ok = 0
            n_empty = 0
            try:
                for sym in symbols():

                    bars = fetch_1m(sym, 3)

                    if not bars:
                        n_empty += 1
                        continue


                    for b in bars:
                        upsert_bar("1m", sym, b)
                        days_1m = int(os.getenv("CACHE_DAYS_1M", "7"))
                        trim_older_than(
                            "1m",
                            sym,
                            int(time.time() * 1000) - days_1m * 24 * 3600 * 1000,
                        )

                    last = bars[-1]
                    update_aggregates_from_1m(sym, last)

                    n_ok += 1

                print(f"[RT] ok={n_ok} empty={n_empty} interval={interval}s")
            except Exception as e:
                print("[RT][ERR]", repr(e))

            time.sleep(interval)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
