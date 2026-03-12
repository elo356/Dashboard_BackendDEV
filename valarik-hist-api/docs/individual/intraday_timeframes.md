# `app/intraday/timeframes.py`

## Rol
Modulo intradia de timeframes equivalente a `app/config/timeframes_rt.py`, pero con otra lista `AGG_TFS`.

## Exporta
- `RT_TFS`
- `TF_MS`
- `AGG_TFS`
- `ensure_rt_tf(tf)`

## Notas
- Aqui `AGG_TFS` llega hasta `1h`.
- Se usa en `intraday/debug.py`.
