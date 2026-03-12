# `app/services/metrics_flow_trend.py`

## Rol
Calcula porcentajes derivados de flujo, tendencia y aceleracion para series de chart.

## Exporta
- `assign_flow_pct_total(rows, mode)`
- `trend_accel_pct(dptfav, flow)`
- `compute_pct_series(trace)`

## Uso principal
- Consumido por `routes_chart.py`.
