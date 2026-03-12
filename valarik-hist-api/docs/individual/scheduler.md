# `app/services/scheduler.py`

## Rol
Version alternativa o anterior del scheduler realtime.

## Exporta
- `start_realtime_scheduler(fetch_1m)`

## Diferencias frente al scheduler activo
- Inserta todas las barras recibidas en `1m`.
- No congela la ingesta fuera de mercado.
- No restaura ni guarda snapshots periodicos.

## Notas
- `app/main.py` no lo usa actualmente.
