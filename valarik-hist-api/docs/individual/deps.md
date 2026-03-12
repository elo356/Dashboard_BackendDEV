# `app/api/deps.py`

## Rol
Centraliza la dependencia de autenticacion administrativa para endpoints protegidos.

## Exporta
- `require_admin(x_admin_key)`
- `admin_header(x_admin_key=Header(None))`

## Uso principal
- Consumido por `routes_admin.py`.

## Notas
- Si `ADMIN_KEY` no esta configurado, la validacion queda relajada.
