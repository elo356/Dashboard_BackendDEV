# `app/clients/http.py`

## Rol
Wrapper HTTP comun para llamadas JSON y fusible duro de rate limit hacia TwelveData.

## Exporta
- `_td_guard(url)`
- `get_json_url(url, timeout=20)`

## Notas
- Si excede `TD_MAX_PER_MIN_HARD`, termina el proceso con `os._exit(1)`.
- Solo aplica el guard cuando el dominio contiene `api.twelvedata.com`.
