# `app/services/compute_service.py`

## Rol
Calcula metricas historicas por simbolo y arma rankings historicos con cache.

## Exporta
- `clear_compute_caches()`
- `compute_one(symbol, tf, from_key, to_key)`
- `compute_table(tf, top, from_key, to_key)`

## Dependencias clave
- `app.config.symbols`
- `app.config.timeframes`
- `app.data.daily_store`
- `app.services.aggregation`
- `app.services.formulas`

## Notas
- Mantiene cache por simbolo y cache de tabla por combinacion `tf|from|to`.
