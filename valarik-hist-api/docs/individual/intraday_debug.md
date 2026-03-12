# `app/intraday/debug.py`

## Rol
Herramientas de diagnostico para inspeccionar barras intradia y validar agregaciones derivadas desde `1m`.

## Exporta
- `get_raw_intraday(symbol, tf, start_ms, end_ms, limit)`
- `inspect_pipeline_intraday(symbol, tf, bars_needed=60)`
- `compare_aggregate_cache_vs_rebuild(symbol, tf, buckets=120)`

## Dependencias clave
- `app.data.intraday_cache`
- `app.intraday.timeframes`
- `app.services.aggregation_rt`
- `app.shared.diagnostics`

## Notas
- `compare_aggregate_cache_vs_rebuild` reconstruye agregados desde `1m` y los compara con cache.
