# `app/services/formulas.py`

## Rol
Contiene formulas base de momentum, PTFAV y señal.

## Exporta
- `mom_score_from_closes(closes)`
- `compute_ptfav(bars)`
- `compute_signal(ptfav, mom)`

## Notas
- `mom_score_from_closes` usa retornos sobre 1, 5 y 21 barras.
- `compute_ptfav` acumula volumen firmado por direccion de ruptura.
