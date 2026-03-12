from typing import Optional, List, Dict, Tuple, Any


def mom_score_from_closes(closes: List[float]) -> Optional[float]:
    if not closes:
        return None
    c = closes[-1]

    def pct(back: int) -> Optional[float]:
        if len(closes) <= back:
            return None
        prev = closes[-1 - back]
        if prev == 0:
            return None
        return (c / prev - 1.0) * 100.0

    p1 = pct(1)
    p5 = pct(5)
    p21 = pct(21)

    vals = [x for x in [p1, p5, p21] if x is not None]
    return (sum(vals) / len(vals)) if vals else None


def compute_ptfav(bars: List[Dict[str, Any]]) -> Tuple[float, float, int]:
    if len(bars) < 2:
        return (0.0, 0.0, 0)

    trend = 0
    acc = 0.0
    last_dpt = 0.0

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
        last_dpt = dpt

    return (acc, last_dpt, trend)


def compute_signal(ptfav: float, mom: Optional[float]) -> str:
    if mom is None:
        return "HOLD"
    if ptfav > 0:
        return "BUY" if mom > 0 else "HOLD"
    return "ROTATE" if mom < 0 else "HOLD"
