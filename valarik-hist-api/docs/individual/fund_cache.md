# `app/data/fund_cache.py`

## Rol
Guarda fundamentals en memoria y persiste snapshots a disco.

## Exporta
- `load_snapshot()`
- `save_snapshot(force=False)`
- `get(symbol)`
- `set_symbol(symbol, obj)`

## Notas
- Usa `CACHE_DIR` y el archivo `fund_cache_latest.json`.
- El directorio por defecto es `/var/lib/valarik_cache`.
