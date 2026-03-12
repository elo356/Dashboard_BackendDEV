from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple, Optional

from app.config.symbols import SYMBOLS
from app.core.time import prev_trading_day_key, date_range_keys, expected_weekday_keys
from app.clients.firebase_rtdb import fb_last_key, fb_put_day, fb_get_range_days
from app.clients.twelvedata import td_fetch_daily_range
from app.data.daily_store import put_day_in_ram, refresh_daily_cache_from_firebase
from app.services.compute_service import clear_compute_caches


def split_into_runs(keys_sorted: List[str]) -> List[Tuple[str, str]]:
    if not keys_sorted:
        return []
    runs: List[Tuple[str, str]] = []
    cur_start = keys_sorted[0]
    cur_prev = keys_sorted[0]

    def next_day(k: str) -> str:
        dt = datetime.strptime(k, "%Y%m%d").date() + timedelta(days=1)
        return dt.strftime("%Y%m%d")

    for k in keys_sorted[1:]:
        if k == next_day(cur_prev):
            cur_prev = k
            continue
        runs.append((cur_start, cur_prev))
        cur_start = k
        cur_prev = k
    runs.append((cur_start, cur_prev))
    return runs


def sync_missing_daily_from_twelve() -> Dict[str, Any]:
    yesterday_key = prev_trading_day_key()

    result = {
        "updated": {},
        "errors": {},
        "skippedNoLastKey": [],
        "symbolsChecked": len(SYMBOLS),
        "yesterdayKey": yesterday_key,
    }

    for sym in SYMBOLS:
        try:
            last_fb = fb_last_key(sym)
            if not last_fb:
                result["skippedNoLastKey"].append(sym)
                continue

            if last_fb >= yesterday_key:
                continue

            missing_keys = date_range_keys(
                (datetime.strptime(last_fb, "%Y%m%d") + timedelta(days=1)).strftime("%Y%m%d"),
                yesterday_key,
            )
            if not missing_keys:
                continue

            new_data = td_fetch_daily_range(sym, missing_keys[0], missing_keys[-1])
            saved_days: List[str] = []

            for day_key in missing_keys:
                row = new_data.get(day_key)
                if not row:
                    continue
                fb_put_day(sym, day_key, row)
                put_day_in_ram(sym, day_key, row)
                saved_days.append(day_key)

            if saved_days:
                result["updated"][sym] = saved_days
        except Exception as e:
            result["errors"][sym] = f"{type(e).__name__}: {e}"

    return result


def sync_backfill_gaps_recent(days_back: int = 50, refresh_cache: bool = True) -> Dict[str, Any]:
    ykey = prev_trading_day_key()
    ydate = datetime.strptime(ykey, "%Y%m%d").date()
    from_date = ydate - timedelta(days=days_back)
    from_key = from_date.strftime("%Y%m%d")

    result = {
        "ok": True,
        "window": {"from": from_key, "to": ykey, "days_back": days_back},
        "symbolsChecked": len(SYMBOLS),
        "missing": {},
        "updated": {},
        "skipped": {},
    }

    expected = expected_weekday_keys(from_key, ykey)
    expected_set = set(expected)

    for sym in SYMBOLS:
        existing = fb_get_range_days(sym, from_key, ykey)
        existing_keys = set(existing.keys())

        missing_keys = sorted(list(expected_set - existing_keys))
        if not missing_keys:
            continue

        result["missing"][sym] = missing_keys

        runs = split_into_runs(missing_keys)
        saved: List[str] = []
        skipped: List[str] = []

        for a, b in runs:
            fetched = td_fetch_daily_range(sym, a, b)
            for k in date_range_keys(a, b):
                row = fetched.get(k)
                if not row:
                    skipped.append(k)
                    continue
                fb_put_day(sym, k, row)
                put_day_in_ram(sym, k, row)
                saved.append(k)

        if saved:
            result["updated"][sym] = saved
        if skipped:
            result["skipped"][sym] = skipped

    if refresh_cache:
        # seguridad: recarga RAM completa + limpia caches
        refresh_daily_cache_from_firebase()
        clear_compute_caches()

    return result
