from datetime import datetime, timedelta
from urllib.parse import urlparse

from fastapi import APIRouter, Depends, Query, Header, HTTPException

from app.api.deps import admin_header, require_admin
from app.data.daily_store import refresh_daily_cache_from_firebase, DAILY_UPDATED_AT_MS
from app.services.sync_service import sync_missing_daily_from_twelve, sync_backfill_gaps_recent
from app.services.maintenance_service import daily_maintenance_run
from app.services.compute_service import clear_compute_caches
from app.core.settings import ADMIN_KEY, FIREBASE_DATABASE_URL
from app.clients.firebase_rtdb import fb_last_key, fb_get_range_days
from app.core.time import prev_trading_day_key
from app.services.fund_refresh import refresh_fundamentals_once
from app.intraday.debug import (
    get_raw_intraday,
    inspect_pipeline_intraday,
    compare_aggregate_cache_vs_rebuild,
)
from app.historical.debug import inspect_pipeline_historical
router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/refresh-ram")
def admin_refresh_ram(x_admin_key: str = Depends(admin_header)):
    require_admin(x_admin_key)
    refresh_daily_cache_from_firebase()
    clear_compute_caches()
    return {"ok": True, "updatedAt": DAILY_UPDATED_AT_MS}


@router.post("/sync-daily")
def admin_sync_daily(x_admin_key: str = Depends(admin_header)):
    require_admin(x_admin_key)
    out = sync_missing_daily_from_twelve()
    clear_compute_caches()
    return out

def _require_admin(x_admin_key: str | None):
    if not x_admin_key or x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")

@router.post("/maintenance/daily")
def admin_daily_maintenance(x_admin_key: str = Depends(admin_header)):
    require_admin(x_admin_key)
    return daily_maintenance_run()


@router.post("/backfill/recent")
def admin_backfill_recent(days_back: int = 50, x_admin_key: str = Depends(admin_header)):
    require_admin(x_admin_key)
    return sync_backfill_gaps_recent(days_back=days_back)

@router.post("/refresh-fund")
def admin_refresh_fund(
    limit: int = Query(0, ge=0, le=5000),
    offset: int = Query(0, ge=0),
    sleep_ms: int = Query(1200, ge=0, le=30_000),
    missing_only: int = Query(1, ge=0, le=1),
    include_earnings: int = Query(1, ge=0, le=1),
    max_per_min: int = Query(500, ge=50, le=600),
    x_admin_key: str | None = Header(default=None, alias="X-Admin-Key"),
):
    _require_admin(x_admin_key)
    return refresh_fundamentals_once(
        limit=limit,
        offset=offset,
        sleep_ms=sleep_ms,
        missing_only=missing_only,
        include_earnings=include_earnings,
        max_per_min=max_per_min,
    )


@router.get("/diag/firebase-last")
def admin_diag_firebase_last(
    symbol: str = Query(...),
    lookback_days: int = Query(30, ge=1, le=365),
    x_admin_key: str = Depends(admin_header),
):
    require_admin(x_admin_key)

    ykey = prev_trading_day_key()
    ydate = datetime.strptime(ykey, "%Y%m%d").date()
    from_key = (ydate - timedelta(days=lookback_days)).strftime("%Y%m%d")

    last = fb_last_key(symbol)
    recent = fb_get_range_days(symbol, from_key, ykey)
    recent_keys = sorted(list((recent or {}).keys()))

    parsed = urlparse(FIREBASE_DATABASE_URL)
    return {
        "ok": True,
        "symbol": symbol,
        "firebaseHost": parsed.netloc,
        "yesterdayKey": ykey,
        "lastKeyInFirebase": last,
        "recentKeysCount": len(recent_keys),
        "recentFirstKey": recent_keys[0] if recent_keys else None,
        "recentLastKey": recent_keys[-1] if recent_keys else None,
    }


@router.get("/test/intraday/raw")
def admin_test_intraday_raw(
    symbol: str = Query(...),
    tf: str = Query("1m"),
    start_ms: int = Query(0),
    end_ms: int = Query(2_147_483_647_000),
    limit: int = Query(500, ge=1, le=5000),
    x_admin_key: str = Depends(admin_header),
):
    require_admin(x_admin_key)
    return get_raw_intraday(symbol=symbol, tf=tf, start_ms=start_ms, end_ms=end_ms, limit=limit)


@router.get("/test/intraday/pipeline")
def admin_test_intraday_pipeline(
    symbol: str = Query(...),
    tf: str = Query("1m"),
    bars_needed: int = Query(120, ge=2, le=2000),
    x_admin_key: str = Depends(admin_header),
):
    require_admin(x_admin_key)
    return inspect_pipeline_intraday(symbol=symbol, tf=tf, bars_needed=bars_needed)


@router.get("/test/intraday/aggregate-check")
def admin_test_intraday_aggregate_check(
    symbol: str = Query(...),
    tf: str = Query("5m"),
    buckets: int = Query(120, ge=5, le=2000),
    x_admin_key: str = Depends(admin_header),
):
    require_admin(x_admin_key)
    return compare_aggregate_cache_vs_rebuild(symbol=symbol, tf=tf, buckets=buckets)


@router.get("/test/historical/pipeline")
def admin_test_historical_pipeline(
    symbol: str = Query(...),
    tf: str = Query("1D"),
    from_key: str = Query("20190101"),
    to_key: str = Query("20991231"),
    bars_needed: int = Query(120, ge=2, le=5000),
    x_admin_key: str = Depends(admin_header),
):
    require_admin(x_admin_key)
    return inspect_pipeline_historical(
        symbol=symbol,
        tf=tf,
        from_key=from_key,
        to_key=to_key,
        bars_needed=bars_needed,
    )
