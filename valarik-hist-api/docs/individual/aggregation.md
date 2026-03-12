# `app/services/aggregation.py`

## Rol
Agrega barras diarias a `1W`, `1M` y `1Y`.

## Exporta
- `_agg_block(block)`
- `agg_week(daily)`
- `agg_month(daily)`
- `agg_year(daily)`
- `build_tf_bars(tf, daily)`

## Notas
- Usa aproximaciones fijas: 5 dias, 21 dias y 252 dias.
