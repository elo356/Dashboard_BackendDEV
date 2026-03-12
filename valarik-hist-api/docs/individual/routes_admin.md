# `app/api/routes_admin.py`

## Rol
Expone endpoints operativos y de diagnostico para refrescar caches, sincronizar historicos, ejecutar mantenimiento y probar pipelines.

## Endpoints principales
- `POST /admin/refresh-ram`
- `POST /admin/sync-daily`
- `POST /admin/maintenance/daily`
- `POST /admin/backfill/recent`
- `POST /admin/refresh-fund`
- `GET /admin/diag/firebase-last`
- `GET /admin/test/intraday/raw`
- `GET /admin/test/intraday/pipeline`
- `GET /admin/test/intraday/aggregate-check`
- `GET /admin/test/historical/pipeline`

## Dependencias clave
- `app.api.deps`
- `app.services.sync_service`
- `app.services.maintenance_service`
- `app.services.compute_service`
- `app.services.fund_refresh`
- `app.intraday.debug`
- `app.historical.debug`

## Notas
- Mezcla operaciones de mantenimiento real con herramientas de inspeccion.
