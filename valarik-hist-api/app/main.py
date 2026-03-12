from fastapi import FastAPI
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
        ensure_daily_cache_loaded()
        start_daily_scheduler()
        #start_fund_scheduler()
        start_realtime_scheduler(td_fetch_last_1m)
        print("[APP] startup complete")
    return app

app = create_app()
