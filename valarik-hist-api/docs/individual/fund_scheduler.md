# `app/services/fund_scheduler.py`

## Rol
Scheduler diario para refrescar fundamentals automaticamente.

## Exporta
- `start_fund_scheduler()`

## Dependencias clave
- `app.services.fund_refresh`

## Notas
- Corre en un thread daemon.
- Existe, pero actualmente no se inicia desde `app/main.py`.
