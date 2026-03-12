# `app/services/daily_scheduler.py`

## Rol
Programa el mantenimiento diario fuera de linea para sincronizar historicos y refrescar caches.

## Exporta
- `_today_key(now)`
- `start_daily_scheduler(hour_et=None, minute_et=None)`

## Dependencias clave
- `app.services.maintenance_service`

## Notas
- Corre en un thread daemon.
- Usa `DAILY_SYNC_*` para horario y polling.
- El mantenimiento diario ejecuta sync incremental y backfill reciente de huecos.
- La ventana de backfill reciente se controla con `DAILY_GAP_BACKFILL_DAYS` (default `90`).
