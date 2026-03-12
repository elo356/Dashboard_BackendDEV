# `app/data/daily_store.py`

## Rol
Mantiene en RAM el cache historico diario cargado desde Firebase.

## Exporta
- `refresh_daily_cache_from_firebase()`
- `ensure_daily_cache_loaded()`
- `read_daily_range(symbol, from_key, to_key)`
- `put_day_in_ram(symbol, day_key, row)`

## Uso principal
- Consumido por rutas historicas, chart, mantenimiento y sincronizacion.

## Notas
- `DAILY_STORE` guarda `{symbol -> {YYYYMMDD -> row}}`.
