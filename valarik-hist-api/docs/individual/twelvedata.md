# `app/clients/twelvedata.py`

## Rol
Cliente TwelveData para historicos diarios y un acceso compacto a perfil y earnings.

## Exporta
- `td_fetch_daily_range(symbol, start_key, end_key)`
- `td_fetch_profile(symbol)`
- `td_fetch_earnings(symbol)`

## Dependencias clave
- `app.core.settings`
- `app.clients.http`

## Notas
- La ruta diaria devuelve un mapa `{YYYYMMDD -> OHLCV}` listo para persistir.
