import os, time, threading
from typing import Callable, Dict, Any, List

from app.services.realtime_service import symbols, update_aggregates_from_1m
from app.data.intraday_cache import upsert_bar, trim_older_than, save_snapshot_periodic, load_snapshot_on_start
from app.core.market import market_is_open_now  # si no existe, te doy abajo uno rápido

_started = False

def start_realtime_scheduler(fetch_1m: Callable[[str, int], List[Dict[str, Any]]]) -> None:
    global _started
    if _started:
        return
    _started = True

    interval = int(os.getenv("INGEST_INTERVAL_SEC", "60"))
    freeze_sleep = int(os.getenv("CLOSED_SLEEP_SEC", "120"))

    restore_snapshot = os.getenv("LOAD_RT_SNAPSHOT_ON_START", "1") == "1"

    if restore_snapshot:
        try:
            load_snapshot_on_start()
        except Exception as e:
            print("[RT][SNAPSHOT][ERR]", repr(e))
    else:
        print("[RT] snapshot restore disabled by LOAD_RT_SNAPSHOT_ON_START=0")

    last_key_seen: dict[str, int] = {}

    def loop():
        while True:
            # Freeze total fuera de mercado
            if not market_is_open_now():
                # guarda snapshots de vez en cuando aunque esté cerrado
                save_snapshot_periodic()
                time.sleep(freeze_sleep)
                continue

            n_ok = 0
            n_empty = 0

            try:
                for sym in symbols():
                    bars = fetch_1m(sym, 3)
                    if not bars:
                        n_empty += 1
                        continue

                    closed = bars[-2] if len(bars) >= 2 else bars[-1]
                    k = int(closed["key"])

                    if last_key_seen.get(sym) == k:
                        continue
                    last_key_seen[sym] = k

                    # guarda SOLO el cerrado 
                    upsert_bar("1m", sym, closed)
                    days_1m = int(os.getenv("CACHE_DAYS_1M", "7"))
                    trim_older_than(
                        "1m",
                        sym,
                        int(time.time() * 1000) - days_1m * 24 * 3600 * 1000,
                    )

                    update_aggregates_from_1m(sym, closed)

                    n_ok += 1

                save_snapshot_periodic()

                print(f"[RT] ok={n_ok} empty={n_empty} interval={interval}s")
            except Exception as e:
                print("[RT][ERR]", repr(e))

            time.sleep(interval)

    t = threading.Thread(target=loop, daemon=True)
    t.start()
