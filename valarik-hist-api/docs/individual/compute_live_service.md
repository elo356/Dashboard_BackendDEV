# `app/services/compute_live_service.py`

## Rol
Calcula metricas live por simbolo y tablas realtime con cache y control de recomputo.

## Exporta
- `compute_one_live(symbol, tf, bars_needed=60)`
- `compute_table_live(tf, top)`

## Responsabilidades
- Evitar recomputos si no cambio el `lastKey` global de `1m`.
- Mezclar top positivos y negativos para la salida live.
- Calcular `flowPctTotal`, `targetWt`, `momScore`, `signal`.

## Dependencias clave
- `app.data.intraday_cache`
- `app.services.formulas`
- `app.core.market`
