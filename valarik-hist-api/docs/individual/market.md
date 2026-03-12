# `app/core/market.py`

## Rol
Determina si el mercado estadounidense esta abierto en horario regular.

## Exporta
- `market_is_open_now(now=None)`
- `market_is_open(now=None)`

## Reglas
- Zona horaria: `America/New_York`
- Dias habiles: lunes a viernes
- Sesion regular: `09:30` a `16:00`
