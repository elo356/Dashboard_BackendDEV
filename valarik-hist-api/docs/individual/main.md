# `app/main.py`

## Rol
Punto de entrada de FastAPI. Crea la aplicacion, registra routers y arranca los procesos en background del backend.

## Elementos principales
- `create_app()`: configura CORS, incluye routers y define el evento `startup`.
- `app = create_app()`: expone la instancia usada por Uvicorn/FastAPI.

## Dependencias clave
- `app.core.cors`
- `app.api.routes_hist`
- `app.api.routes_admin`
- `app.api.routes_realtime`
- `app.api.routes_chart`
- `app.data.daily_store`
- `app.services.daily_scheduler`
- `app.services.scheduler_realtime`
- `app.clients.twelvedata_rt`

## Notas
- El scheduler de fundamentals existe pero esta comentado en startup.
