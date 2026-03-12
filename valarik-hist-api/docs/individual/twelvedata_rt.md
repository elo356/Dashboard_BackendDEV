# `app/clients/twelvedata_rt.py`

## Rol
Cliente TwelveData para obtener las ultimas velas intradia de 1 minuto.

## Exporta
- `_to_epoch_ms(dt_str)`
- `td_fetch_last_1m(symbol, limit=3)`

## Dependencias clave
- `app.core.settings`
- `app.clients.http`

## Notas
- Convierte timestamps de TwelveData usando zona `America/New_York`.
