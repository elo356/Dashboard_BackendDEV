# `app/services/sync_service.py`

## Rol
Sincroniza historicos diarios faltantes entre Firebase y TwelveData.

## Exporta
- `split_into_runs(keys_sorted)`
- `sync_missing_daily_from_twelve()`
- `sync_backfill_gaps_recent(days_back=50, refresh_cache=True)`

## Dependencias clave
- `app.config.symbols`
- `app.core.time`
- `app.clients.firebase_rtdb`
- `app.clients.twelvedata`
- `app.data.daily_store`
- `app.services.compute_service`

## Notas
- Tiene un modo incremental y otro modo backfill por ventana reciente.
- `sync_missing_daily_from_twelve()` avanza desde el ultimo dia presente en Firebase.
- `sync_backfill_gaps_recent()` detecta huecos dentro de una ventana reciente y los rellena.
