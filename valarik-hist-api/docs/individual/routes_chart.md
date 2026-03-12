# `app/api/routes_chart.py`

## Rol
Entrega series para graficas y metricas de flujo/tendencia combinando fuentes realtime e historicas.

## Endpoints principales
- `GET /chart/bars`
- `GET /chart/flow-trend`

## Responsabilidades
- Normalizar barras intradia y diarias.
- Convertir formatos `key <-> epoch ms`.
- Aplicar reduccion por densidad visual (`LOD`) con `px`.
- Calcular puntos de flow/trend con semantica explicita desde `live_metrics`.

## Dependencias clave
- `app.config.timeframes`
- `app.config.timeframes_rt`
- `app.data.daily_store`
- `app.data.intraday_cache`
- `app.services.aggregation`
- `app.services.metrics_flow_trend`
- `app.shared.diagnostics`

## Notas
- Soporta `1m`, `5m`, `15m`, `30m`, `1h` y `1D` para barras.
- `GET /chart/flow-trend` expone `schemaVersion = 2`.
- Campos canonicos del flow-trend: `flow_raw`, `flow_pct`, `trend_dir`, `mom_score`, `trend_accel_pct`, `is_partial`.
- Los aliases legacy se mantienen temporalmente para compatibilidad (`flow`, `trend`, `momScore`, `ptfav`).
