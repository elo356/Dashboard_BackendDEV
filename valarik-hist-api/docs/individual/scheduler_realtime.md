# `app/services/scheduler_realtime.py`

## Rol
Scheduler realtime activo del sistema. Orquesta la ingesta de velas cerradas de `1m`, la actualizacion de agregados y snapshots.

## Exporta
- `start_realtime_scheduler(fetch_1m)`

## Responsabilidades
- restaurar snapshot al iniciar
- congelar ingesta fuera de mercado
- guardar solo la vela cerrada mas reciente
- actualizar agregados derivados
- persistir snapshots periodicos

## Dependencias clave
- `app.services.realtime_service`
- `app.data.intraday_cache`
- `app.core.market`
