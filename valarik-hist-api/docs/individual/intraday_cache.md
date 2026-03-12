# `app/data/intraday_cache.py`

## Rol
Cache principal de intradia en memoria, con operaciones por timeframe/simbolo y snapshot en disco.

## Exporta
- `upsert_bar(tf, symbol, bar)`
- `get_range(tf, symbol, start_key, end_key)`
- `get_last(tf, symbol)`
- `trim_older_than(tf, symbol, min_key)`
- `get_global_last_key(tf="1m")`
- `save_snapshot_periodic(force=False)`
- `load_snapshot_on_start()`

## Notas
- Mantiene las listas ordenadas por `key`.
- Valida estructura minima de cada bar en `upsert_bar`; si el bar es invalido, falla la insercion.
- Sanea y reordena el snapshot al restaurar en `load_snapshot_on_start`.
- Usa `RLock` para proteger acceso concurrente dentro del proceso.
- Sigue siendo un cache por proceso; multiples workers no comparten estado en RAM.
- Si `CACHE_DIR` no es escribible, cae a `/tmp/valarik_cache`.
