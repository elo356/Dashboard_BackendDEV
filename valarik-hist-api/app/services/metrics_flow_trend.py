from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.services.formulas import mom_score_from_closes


def assign_flow_pct_total(rows: List[Dict[str, Any]], mode: str) -> None:
    vals = [float(r.get("ptfav") or 0.0) for r in rows]

    if mode == "hist":
        denom = sum(v for v in vals if v > 0)
        for r, pt in zip(rows, vals):
            r["flowPctTotal"] = (pt / denom) if (denom > 0 and pt > 0) else 0.0
        return

    # realtime/default: signed ratio against ABS sum
    denom = sum(abs(v) for v in vals)
    for r, pt in zip(rows, vals):
        r["flowPctTotal"] = (pt / denom) if denom > 0 else 0.0


def trend_accel_pct(dptfav: float, flow: float) -> float:
    den = abs(float(flow))
    if den <= 0:
        return 0.0
    return (float(dptfav) / den) * 100.0


def compute_pct_series(trace: Dict[str, Any]) -> Tuple[List[float], List[float], List[float]]:
    steps = (trace or {}).get("steps") or []
    if not steps:
        return ([], [], [])

    flow_vals: List[float] = [float(s.get("ptfavAcc") or 0.0) for s in steps]
    dpt_vals: List[float] = [float(s.get("dpt") or 0.0) for s in steps]
    closes: List[float] = [float(s.get("close") or 0.0) for s in steps]

    den = sum(abs(v) for v in flow_vals)
    flow_pct = [(v / den) if den > 0 else 0.0 for v in flow_vals]

    # Reuse existing momentum formula point-by-point to produce trend%.
    trend_pct: List[float] = []
    for i in range(len(closes)):
        m = mom_score_from_closes(closes[: i + 1])
        trend_pct.append(float(m) if m is not None else 0.0)

    trend_accel = [trend_accel_pct(dpt, flow) for dpt, flow in zip(dpt_vals, flow_vals)]
    return (flow_pct, trend_pct, trend_accel)
