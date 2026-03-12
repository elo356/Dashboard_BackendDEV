# `app/services/fund_refresh.py`

## Rol
Refresca fundamentals y earnings de manera segura, con retry, rate limiting y persistencia.

## Elementos principales
- `_fetch_with_retry(...)`
- `_has_earnings_data(payload)`
- `MinuteLimiter`
- `refresh_fundamentals_once(...)`

## Dependencias clave
- `app.config.symbols`
- `app.data.fund_cache`
- `app.clients.twelvedata_fund`

## Notas
- Evita sobreescribir data buena con respuestas vacias.
- Soporta `missing_only`, `include_earnings` y `max_per_min`.
