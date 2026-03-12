# `app/services/realtime_service.py`

## Rol
Gestiona la ingesta realtime y la propagacion de agregados desde barras `1m`.

## Exporta
- `symbols()`
- `ingest_1m(symbol, fetch_1m)`
- `update_aggregates_from_1m(symbol, bar_1m)`

## Dependencias clave
- `app.data.intraday_cache`
- `app.config.timeframes_rt`
- `app.services.aggregation_rt`
- `app.config.symbols`

## Notas
- Agrega `5m/15m/30m/1h` desde `1m`.
- Agrega `4h/6h/12h` usando como base el bucket `1h` vivo disponible.
- `4h/6h/12h` se mantienen como barras vivas intrasesion y no como barras cerradas tradicionales.
- La metadata de barra viva se expone desde `aggregation_rt` mediante campos como `is_partial`, `source_tf` y `bucket_tf`.
