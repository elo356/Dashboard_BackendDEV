# `app/config/timeframes.py`

## Rol
Define aliases, ventanas y limites para timeframes historicos.

## Exporta
- `HIST_TFS`
- `TF_WINDOW_DAYS`
- `TF_LIMITS`
- `ensure_hist_tf(tf)`
- `needed_daily_for_tf(tf, max_bars)`
- `apply_tf_window(tf, daily)`

## Notas
- Normaliza variantes como `daily`, `weekly`, `monthly`, `yearly`.
