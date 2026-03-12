# `app/core/settings.py`

## Rol
Carga variables de entorno requeridas y expone configuracion global del backend.

## Exporta
- `_load_env()`
- `must_env(name)`
- `TWELVE_API_KEY`
- `FIREBASE_DATABASE_URL`
- `FIREBASE_AUTH`
- `ADMIN_KEY`
- `TABLE_TTL_MS`

## Notas
- Lanza `RuntimeError` si faltan `TWELVEDATA_API_KEY` o `FIREBASE_DATABASE_URL`.
