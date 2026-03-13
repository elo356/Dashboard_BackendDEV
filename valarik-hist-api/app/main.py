from fastapi import FastAPI
import os
from app.services.fund_scheduler import start_fund_scheduler

from app.core.cors import setup_cors
from app.api.routes_hist import router as hist_router
from app.api.routes_admin import router as admin_router
from app.api.routes_realtime import router as realtime_router
from app.api.routes_chart import router as chart_router

from app.data.daily_store import ensure_daily_cache_loaded
from app.services.daily_scheduler import start_daily_scheduler

from app.services.scheduler_realtime import start_realtime_scheduler
from app.clients.twelvedata_rt import td_fetch_last_1m

def create_app() -> FastAPI:
    app = FastAPI(title="Valarik Hist API", version="2.0")

    setup_cors(app)

    app.include_router(hist_router)
    app.include_router(admin_router)
    app.include_router(realtime_router)
    app.include_router(chart_router)

    @app.on_event("startup")
    def _startup():
        skip_warmup = os.getenv("SKIP_STARTUP_WARMUP", "0") == "1"
        enable_daily = os.getenv("ENABLE_DAILY_SCHEDULER", "1") == "1"
        enable_realtime = os.getenv("ENABLE_REALTIME_SCHEDULER", "1") == "1"
        enable_fund = os.getenv("ENABLE_FUND_SCHEDULER", "0") == "1"

        if skip_warmup:
            print("[APP] skipping daily cache warmup by SKIP_STARTUP_WARMUP=1")
        else:
            ensure_daily_cache_loaded()

        if enable_daily:
            start_daily_scheduler()
        else:
            print("[APP] daily scheduler disabled by ENABLE_DAILY_SCHEDULER=0")

        if enable_fund:
            start_fund_scheduler()
        else:
            print("[APP] fund scheduler disabled by ENABLE_FUND_SCHEDULER=0")

        if enable_realtime:
            start_realtime_scheduler(td_fetch_last_1m)
        else:
            print("[APP] realtime scheduler disabled by ENABLE_REALTIME_SCHEDULER=0")

        print("[APP] startup complete")
    return app

app = create_app()
