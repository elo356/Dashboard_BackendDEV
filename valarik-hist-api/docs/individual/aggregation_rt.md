# `app/services/aggregation_rt.py`

## Rol
Construye barras intradia agregadas a partir de barras base, principalmente `1m` y `1h`.

## Exporta
- `bucket_start(ts_ms, tf)`
- `merge_into(existing, bar_1m, bucket_key, tf, source_tf)`

## Notas
- Para `12h` usa una vela por sesion NYSE completa.
- Para `6h` usa dos bloques intrasesion anclados a `09:30` y `12:30` NY.
- Para `4h` usa dos bloques intrasesion anclados a sesion NYSE.
- Las barras agregadas realtime agregan metadata: `is_partial`, `source_tf`, `bucket_tf`.
- Los buckets anclados a sesion tambien agregan `session_anchor`.
- Para timeframes regulares usa truncamiento por `TF_MS`.
