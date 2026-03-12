# `app/clients/firebase_rtdb.py`

## Rol
Cliente minimo para leer y escribir historicos diarios en Firebase Realtime Database.

## Exporta
- `fb_get(path)`
- `fb_put_day(symbol, day_key, row)`
- `fb_last_key(symbol)`
- `fb_get_range_days(symbol, from_key, to_key)`
- `normalize_daily_row(row)`

## Dependencias clave
- `app.core.settings`
- `app.clients.http`

## Notas
- `normalize_daily_row` estandariza filas con claves cortas o largas.
