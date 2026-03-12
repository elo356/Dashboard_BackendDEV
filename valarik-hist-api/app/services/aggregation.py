from typing import Dict, Any, List

from app.config.timeframes import ensure_hist_tf


def _agg_block(block: List[Dict[str, Any]]) -> Dict[str, Any]:
    o = block[0]["o"]
    c = block[-1]["c"]
    h = max([x["h"] for x in block if x.get("h") is not None] or [c])
    l = min([x["l"] for x in block if x.get("l") is not None] or [c])
    v = sum([float(x.get("v") or 0.0) for x in block])
    key = block[-1]["key"]
    return {"key": key, "o": o, "h": h, "l": l, "c": c, "v": v}


def agg_week(daily: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out, cur = [], []
    for r in daily:
        cur.append(r)
        if len(cur) == 5:
            out.append(_agg_block(cur))
            cur = []
    if cur:
        out.append(_agg_block(cur))
    return out


def agg_month(daily: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out, cur = [], []
    for r in daily:
        cur.append(r)
        if len(cur) == 21:
            out.append(_agg_block(cur))
            cur = []
    if cur:
        out.append(_agg_block(cur))
    return out


def agg_year(daily: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out, cur = [], []
    for r in daily:
        cur.append(r)
        if len(cur) == 252:
            out.append(_agg_block(cur))
            cur = []
    if cur:
        out.append(_agg_block(cur))
    return out


def build_tf_bars(tf: str, daily: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tf = ensure_hist_tf(tf)
    if tf == "1D":
        return daily
    if tf == "1W":
        return agg_week(daily)
    if tf == "1M":
        return agg_month(daily)
    if tf == "1Y":
        return agg_year(daily)
    return []
