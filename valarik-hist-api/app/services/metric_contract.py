from __future__ import annotations

from typing import Any, Dict


def apply_metric_contract(row: Dict[str, Any]) -> Dict[str, Any]:
    ptfav = float(row.get("ptfav") or 0.0)
    flow_pct_total = float(
        row.get("flowPctTotal")
        if row.get("flowPctTotal") is not None
        else (row.get("flowPct") or row.get("flow_pct") or 0.0)
    )
    mom_score = row.get("momScore")
    if mom_score is None:
        mom_score = row.get("mom_score")

    row["liquidityFootprint"] = ptfav
    row["flowPct"] = float(flow_pct_total)
    row["trendAcceleration"] = float(mom_score) if mom_score is not None else None
    return row
