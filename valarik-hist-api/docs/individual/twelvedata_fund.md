# `app/clients/twelvedata_fund.py`

## Rol
Cliente TwelveData especializado en fundamentals con manejo explicito de errores de API.

## Exporta
- `_err_payload(data)`
- `_td_error_obj(data, scope)`
- `td_fetch_profile(symbol)`
- `td_fetch_earnings(symbol)`

## Uso principal
- Consumido por `fund_refresh.py`.

## Notas
- Devuelve payloads marcados con `_td_error` cuando TwelveData responde error.
