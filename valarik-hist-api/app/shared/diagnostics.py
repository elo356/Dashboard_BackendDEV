from typing import Any, Dict, List, Optional


def momentum_breakdown(closes: List[float]) -> Dict[str, Optional[float]]:
    if not closes:
        return {"p1": None, "p5": None, "p21": None, "momScore": None}

    c = closes[-1]

    def pct(back: int) -> Optional[float]:
        if len(closes) <= back:
            return None
        prev = closes[-1 - back]
        if prev == 0:
            return None
        return ((c / prev) - 1.0) * 100.0

    p1 = pct(1)
    p5 = pct(5)
    p21 = pct(21)
    mom = None
    if p1 is not None and p5 is not None and p21 is not None:
        mom = 0.5 * p1 + 0.3 * p5 + 0.2 * p21
    return {"p1": p1, "p5": p5, "p21": p21, "momScore": mom}


def ptfav_trace(bars: List[Dict[str, Any]]) -> Dict[str, Any]:
    trend = 0
    acc = 0.0
    steps: List[Dict[str, Any]] = []

    for i in range(1, len(bars)):
        cur = bars[i]
        prev = bars[i - 1]
        c = float(cur.get("c") or 0.0)
        ph = float(prev.get("h") or prev.get("c") or 0.0)
        pl = float(prev.get("l") or prev.get("c") or 0.0)

        if c > ph:
            trend = 1
        elif c < pl:
            trend = -1

        v = float(cur.get("v") or 0.0)
        dpt = float(trend) * v
        acc += dpt

        steps.append(
            {
                "i": i,
                "key": cur.get("key"),
                "close": c,
                "prevHigh": ph,
                "prevLow": pl,
                "trend": trend,
                "volume": v,
                "dpt": dpt,
                "ptfavAcc": acc,
            }
        )

    return {
        "trend": trend,
        "dptfav": steps[-1]["dpt"] if steps else 0.0,
        "ptfav": acc,
        "steps": steps,
    }

