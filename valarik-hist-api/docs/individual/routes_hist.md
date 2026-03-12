# `app/api/routes_hist.py`

## Rol
Expone endpoints historicos basados en cache diario y calculos PTFAV/Momentum.

## Endpoints principales
- `GET /health`
- `GET /hist/read`
- `GET /hist/mom`
- `GET /hist/ptfav`
- `GET /hist/table`
- `GET /hist/dump`

## Dependencias clave
- `app.config.timeframes`
- `app.data.daily_store`
- `app.services.compute_service`

## Notas
- Rechaza timeframes no historicos mediante `reject_tf`.
