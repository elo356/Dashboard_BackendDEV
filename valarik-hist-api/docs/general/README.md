# Valarik Dashboard Backend

Backend API en FastAPI para:
- Datos historicos (`/hist/*`)
- Datos realtime/intraday (`/realtime/*`, `/chart/*`)
- Mantenimiento y diagnostico (`/admin/*`)

## Estructura actual

```
valarik-hist-api/
  app/
    api/          # endpoints HTTP
    clients/      # clientes externos (TwelveData, Firebase, HTTP)
    config/       # configuracion central (incluye timeframes)
    core/         # settings, mercado, CORS, utilidades base
    data/         # cache/store en memoria y snapshots
    debug/        # utilidades de debug usadas por /admin/test/*
    services/     # logica de negocio, compute y schedulers
    shared/       # utilidades compartidas
    main.py       # app FastAPI
```

Nota: `app/config/timeframes.py` y `app/config/timeframes_rt.py` son la fuente unica de timeframes.

## Requisitos

- Python 3.11+
- Dependencias de `valarik-hist-api/requirements.txt`

## Instalacion y ejecucion

```bash
cd valarik-hist-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Endpoints principales

### Salud

- `GET /health`

### Historico (`/hist`)

- `GET /hist/read`
- `GET /hist/mom`
- `GET /hist/ptfav`
- `GET /hist/table`
- `GET /hist/dump`

Timeframes historicos soportados: `1D`, `1W`, `1M`, `1Y`.

### Realtime (`/realtime`)

- `GET /realtime/live/table2`
- `GET /realtime/candles`

Timeframes realtime soportados: `1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `6h`, `12h`.

### Chart (`/chart`)

- `GET /chart/bars`
- `GET /chart/flow-trend`

`/chart/bars` soporta intraday (`1m`, `5m`, `15m`, `30m`, `1h`) y `1D` historico.
`/chart/flow-trend` soporta realtime (`1m`, `5m`, `15m`, `30m`, `1h`, `4h`, `6h`, `12h`) e historico (`1D`, `1W`, `1M`, `1Y`).

### Admin (`/admin`, requiere `X-Admin-Key`)

- `POST /admin/refresh-ram`
- `POST /admin/sync-daily`
- `POST /admin/maintenance/daily`
- `POST /admin/backfill/recent`
- `POST /admin/refresh-fund`
- `GET /admin/diag/firebase-last`
- `GET /admin/test/intraday/raw`
- `GET /admin/test/intraday/pipeline`
- `GET /admin/test/intraday/aggregate-check`
- `GET /admin/test/historical/pipeline`

## Ejemplos rapidos

```bash
# Health
curl "http://localhost:8000/health"

# Tabla historica
curl "http://localhost:8000/hist/table?tf=1D&top=25"

# Candles realtime
curl "http://localhost:8000/realtime/candles?symbol=AAPL&tf=5m&limit=200"

# Chart bars
curl "http://localhost:8000/chart/bars?symbol=AAPL&tf=1m&limit=1000"

# Flow/Trend series (mismo cálculo del backend)
curl "http://localhost:8000/chart/flow-trend?symbol=AAPL&tf=1m&bars_needed=200"

# Debug intraday (admin)
curl -H "X-Admin-Key: $ADMIN_KEY" \
  "http://localhost:8000/admin/test/intraday/aggregate-check?symbol=AAPL&tf=5m&buckets=120"
```

## Notas

- Al iniciar, el servicio carga cache diario y levanta schedulers de sync/realtime.
- Si falta una variable obligatoria, el backend falla al arrancar por seguridad.

## Flujo de arranque
Cuando levanta la aplicacion, [`app/main.py`](../../app/main.py) hace esto:

1. Crea la app FastAPI.
2. Configura CORS.
3. Registra los routers `hist`, `admin`, `realtime` y `chart`.
4. En startup carga el cache historico en RAM con `ensure_daily_cache_loaded()`.
5. Inicia el scheduler diario con `start_daily_scheduler()`.
6. Inicia el scheduler realtime con `start_realtime_scheduler(td_fetch_last_1m)`.
7. El scheduler de fundamentals existe, pero en este momento esta comentado en startup ya que tiene un error el cual sobrecarga la api.

## Capas del backend
### API
- `app/api/*`: endpoints HTTP, validacion de parametros y respuestas.

### Configuracion y nucleo
- `app/config/*`: simbolos y definicion de timeframes.
- `app/core/*`: variables de entorno, CORS, horarios de mercado, modelos y utilidades de tiempo.

### Datos y cache
- `app/data/daily_store.py`: historico diario en RAM.
- `app/data/intraday_cache.py`: intradia en RAM con snapshot en disco.
- `app/data/fund_cache.py`: fundamentals con snapshot en disco.

### Servicios
- `app/services/*`: calculos, agregaciones, schedulers, sincronizacion y mantenimiento.

### Clientes externos
- `app/clients/*`: acceso HTTP, Firebase y TwelveData.

### Diagnostico
- `app/historical/debug.py`
- `app/intraday/debug.py`
- `app/shared/diagnostics.py

## Dependencias externas
Segun [`requirements.txt`](../../requirements.txt):

- `fastapi`
- `uvicorn`
- `firebase-admin`
- `python-dotenv`

## Variables de entorno importantes
Definidas o consumidas principalmente desde [`app/core/settings.py`](../../app/core/settings.py) y los schedulers:

- `TWELVEDATA_API_KEY`
- `FIREBASE_DATABASE_URL`
- `FIREBASE_AUTH`
- `ADMIN_KEY`
- `TABLE_TTL_MS`
- `CACHE_DIR`
- `INGEST_INTERVAL_SEC`
- `CLOSED_SLEEP_SEC`
- `DAILY_SYNC_ENABLED`
- `DAILY_SYNC_HOUR_ET`
- `DAILY_SYNC_MINUTE_ET`
- `FUND_SCHED_ENABLED`
- `FUND_FETCH_EARNINGS`
- `FUND_MAX_PER_MIN`

## Mapa completo de scripts
### API
- [`app/api/deps.py`](../../app/api/deps.py) -> [deps.md](../individual/deps.md)
- [`app/api/routes_admin.py`](../../app/api/routes_admin.py) -> [routes_admin.md](../individual/routes_admin.md)
- [`app/api/routes_chart.py`](../../app/api/routes_chart.py) -> [routes_chart.md](../individual/routes_chart.md)
- [`app/api/routes_hist.py`](../../app/api/routes_hist.py) -> [routes_hist.md](../individual/routes_hist.md)
- [`app/api/routes_realtime.py`](../../app/api/routes_realtime.py) -> [routes_realtime.md](../individual/routes_realtime.md)

### Clients
- [`app/clients/firebase_rtdb.py`](../../app/clients/firebase_rtdb.py) -> [firebase_rtdb.md](../individual/firebase_rtdb.md)
- [`app/clients/http.py`](../../app/clients/http.py) -> [http.md](../individual/http.md)
- [`app/clients/twelvedata.py`](../../app/clients/twelvedata.py) -> [twelvedata.md](../individual/twelvedata.md)
- [`app/clients/twelvedata_fund.py`](../../app/clients/twelvedata_fund.py) -> [twelvedata_fund.md](../individual/twelvedata_fund.md)
- [`app/clients/twelvedata_rt.py`](../../app/clients/twelvedata_rt.py) -> [twelvedata_rt.md](../individual/twelvedata_rt.md)

### Config
- [`app/config/symbols.py`](../../app/config/symbols.py) -> [symbols.md](../individual/symbols.md)
- [`app/config/timeframes.py`](../../app/config/timeframes.py) -> [timeframes.md](../individual/timeframes.md)
- [`app/config/timeframes_rt.py`](../../app/config/timeframes_rt.py) -> [timeframes_rt.md](../individual/timeframes_rt.md)

### Core
- [`app/core/cors.py`](../../app/core/cors.py) -> [cors.md](../individual/cors.md)
- [`app/core/market.py`](../../app/core/market.py) -> [market.md](../individual/market.md)
- [`app/core/models.py`](../../app/core/models.py) -> [models.md](../individual/models.md)
- [`app/core/settings.py`](../../app/core/settings.py) -> [settings.md](../individual/settings.md)
- [`app/core/time.py`](../../app/core/time.py) -> [time.md](../individual/time.md)

### Data
- [`app/data/daily_store.py`](../../app/data/daily_store.py) -> [daily_store.md](../individual/daily_store.md)
- [`app/data/fund_cache.py`](../../app/data/fund_cache.py) -> [fund_cache.md](../individual/fund_cache.md)
- [`app/data/intraday_cache.py`](../../app/data/intraday_cache.py) -> [intraday_cache.md](../individual/intraday_cache.md)

### Historical e Intraday
- [`app/historical/debug.py`](../../app/historical/debug.py) -> [historical_debug.md](../individual/historical_debug.md)
- [`app/historical/timeframes.py`](../../app/historical/timeframes.py) -> [historical_timeframes.md](../individual/historical_timeframes.md)
- [`app/intraday/debug.py`](../../app/intraday/debug.py) -> [intraday_debug.md](../individual/intraday_debug.md)
- [`app/intraday/timeframes.py`](../../app/intraday/timeframes.py) -> [intraday_timeframes.md](../individual/intraday_timeframes.md)

### Services
- [`app/main.py`](../../app/main.py) -> [main.md](../individual/main.md)
- [`app/services/aggregation.py`](../../app/services/aggregation.py) -> [aggregation.md](../individual/aggregation.md)
- [`app/services/aggregation_rt.py`](../../app/services/aggregation_rt.py) -> [aggregation_rt.md](../individual/aggregation_rt.md)
- [`app/services/compute_live_service.py`](../../app/services/compute_live_service.py) -> [compute_live_service.md](../individual/compute_live_service.md)
- [`app/services/compute_service.py`](../../app/services/compute_service.py) -> [compute_service.md](../individual/compute_service.md)
- [`app/services/daily_scheduler.py`](../../app/services/daily_scheduler.py) -> [daily_scheduler.md](../individual/daily_scheduler.md)
- [`app/services/formulas.py`](../../app/services/formulas.py) -> [formulas.md](../individual/formulas.md)
- [`app/services/fund_refresh.py`](../../app/services/fund_refresh.py) -> [fund_refresh.md](../individual/fund_refresh.md)
- [`app/services/fund_scheduler.py`](../../app/services/fund_scheduler.py) -> [fund_scheduler.md](../individual/fund_scheduler.md)
- [`app/services/maintenance_service.py`](../../app/services/maintenance_service.py) -> [maintenance_service.md](../individual/maintenance_service.md)
- [`app/services/metrics_flow_trend.py`](../../app/services/metrics_flow_trend.py) -> [metrics_flow_trend.md](../individual/metrics_flow_trend.md)
- [`app/services/realtime_service.py`](../../app/services/realtime_service.py) -> [realtime_service.md](../individual/realtime_service.md)
- [`app/services/scheduler.py`](../../app/services/scheduler.py) -> [scheduler.md](../individual/scheduler.md)
- [`app/services/scheduler_realtime.py`](../../app/services/scheduler_realtime.py) -> [scheduler_realtime.md](../individual/scheduler_realtime.md)
- [`app/services/sync_service.py`](../../app/services/sync_service.py) -> [sync_service.md](../individual/sync_service.md)

### Shared
- [`app/shared/diagnostics.py`](../../app/shared/diagnostics.py) -> [diagnostics.md](../individual/diagnostics.md)
