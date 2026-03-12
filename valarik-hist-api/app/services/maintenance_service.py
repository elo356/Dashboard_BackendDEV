import os
from typing import Dict, Any

from app.services.sync_service import sync_missing_daily_from_twelve, sync_backfill_gaps_recent
from app.data.daily_store import refresh_daily_cache_from_firebase, DAILY_UPDATED_AT_MS
from app.services.compute_service import clear_compute_caches


def daily_maintenance_run() -> Dict[str, Any]:
    backfill_days = int(os.getenv("DAILY_GAP_BACKFILL_DAYS", "90"))

    sync_out = sync_missing_daily_from_twelve()
    backfill_out = sync_backfill_gaps_recent(days_back=backfill_days, refresh_cache=False)

    refresh_daily_cache_from_firebase()
    clear_compute_caches()

    return {
        "ok": True,
        "sync": sync_out,
        "backfill": backfill_out,
        "ramRefreshedAt": DAILY_UPDATED_AT_MS,
        "clearedCaches": True,
    }
