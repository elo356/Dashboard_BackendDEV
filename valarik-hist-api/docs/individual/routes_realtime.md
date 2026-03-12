# `app/api/routes_realtime.py`

## Rol
Sirve ranking live y velas intradia desde el cache en memoria.

## Endpoints principales
- `GET /realtime/live/table2`
- `GET /realtime/candles`

## Responsabilidades
- Calcular `stale` cuando el mercado esta cerrado o no hay nuevas barras.
- Enriquecer filas live con fundamentals almacenados en `fund_cache`.

## Dependencias clave
- `app.config.timeframes_rt`
- `app.data.intraday_cache`
- `app.data.fund_cache`
- `app.core.market`
- `app.services.compute_live_service`

## Notas
- Usa el `lastKey` global de `1m` como señal de frescura.
