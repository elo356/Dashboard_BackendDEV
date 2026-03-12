from __future__ import annotations

from typing import Any, Dict, List

from app.shared.diagnostics import ptfav_trace
from app.services.formulas import compute_ptfav, mom_score_from_closes
from app.services.metrics_flow_trend import trend_accel_pct


def compute_live_metrics(bars: List[Dict[str, Any]]) -> Dict[str, Any]:
    closes = [float(x["c"]) for x in bars if x.get("c") is not None]
    mom = mom_score_from_closes(closes)
    ptfav, dptfav, trend = compute_ptfav(bars)

    trace = ptfav_trace(bars)
    steps = trace.get("steps") or []
    flow_abs = sum(abs(float(x.get("ptfavAcc") or 0.0)) for x in steps)
    flow_pct = (float(ptfav) / flow_abs) if flow_abs else 0.0
    trend_accel = trend_accel_pct(float(dptfav), float(ptfav))

    return {
        "ptfav": float(ptfav),
        "dptfav": float(dptfav),
        "trend_dir": int(trend),
        "mom_score": float(mom) if mom is not None else None,
        "flow_pct": float(flow_pct),
        "trend_accel_pct": float(trend_accel),
    }


def compute_live_metrics_series(bars: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    series: List[Dict[str, Any]] = []
    for idx in range(1, len(bars)):
        metrics = compute_live_metrics(bars[: idx + 1])
        series.append(
            {
                "key": bars[idx].get("key"),
                "ptfavAcc": metrics["ptfav"],
                "dpt": metrics["dptfav"],
                "trend": metrics["trend_dir"],
                "close": float(bars[idx].get("c") or 0.0),
                "volume": float(bars[idx].get("v") or 0.0),
                "flow_pct": metrics["flow_pct"],
                "mom_score": metrics["mom_score"],
                "trend_accel_pct": metrics["trend_accel_pct"],
            }
        )
    return series
