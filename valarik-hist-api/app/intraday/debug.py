from typing import Any, Dict, List

from app.config.timeframes_rt import AGG_TFS
from app.data.intraday_cache import get_last, get_range
from app.intraday.timeframes import TF_MS, ensure_rt_tf
from app.services.aggregation_rt import bucket_start, merge_into
from app.shared.diagnostics import momentum_breakdown, ptfav_trace


def get_raw_intraday(symbol: str, tf: str, start_ms: int, end_ms: int, limit: int) -> Dict[str, Any]:
    tf = ensure_rt_tf(tf)
    bars = get_range(tf, symbol, int(start_ms), int(end_ms))
    if limit > 0:
        bars = bars[-limit:]
    return {
        "ok": True,
        "symbol": symbol,
        "tf": tf,
        "barsCount": len(bars),
        "firstKey": bars[0]["key"] if bars else None,
        "lastKey": bars[-1]["key"] if bars else None,
        "bars": bars,
    }


def inspect_pipeline_intraday(symbol: str, tf: str, bars_needed: int = 60) -> Dict[str, Any]:
    tf = ensure_rt_tf(tf)
    last = get_last(tf, symbol)
    if not last:
        return {"ok": True, "symbol": symbol, "tf": tf, "barsCount": 0, "bars": []}

    end_ms = int(last["key"])
    start_ms = end_ms - (max(1, int(bars_needed)) * TF_MS[tf] * 3)
    bars = get_range(tf, symbol, start_ms, end_ms)
    bars = bars[-max(1, int(bars_needed)):] if bars else []

    closes = [float(x["c"]) for x in bars if x.get("c") is not None]
    mom = momentum_breakdown(closes)
    pt = ptfav_trace(bars)

    return {
        "ok": True,
        "symbol": symbol,
        "tf": tf,
        "barsCount": len(bars),
        "bars": bars,
        "closes": closes,
        "momentum": mom,
        "ptfav": {
            "ptfav": pt["ptfav"],
            "dptfav": pt["dptfav"],
            "trend": pt["trend"],
        },
        "trace": pt["steps"],
    }


def _rebuild_tf_from_1m(symbol: str, tf: str, buckets: int) -> List[Dict[str, Any]]:
    if tf not in AGG_TFS:
        return []

    last_1m = get_last("1m", symbol)
    if not last_1m:
        return []

    end_ms = int(last_1m["key"])
    start_ms = end_ms - (max(1, int(buckets)) * TF_MS[tf] * 2)
    src = get_range("1m", symbol, start_ms, end_ms)
    if not src:
        return []

    out: Dict[int, Dict[str, Any]] = {}
    for bar in src:
        bkey = bucket_start(int(bar["key"]), tf)
        out[bkey] = merge_into(out.get(bkey), bar, bkey, tf, "1m")

    keys = sorted(out.keys())
    return [out[k] for k in keys][-max(1, int(buckets)):]


def compare_aggregate_cache_vs_rebuild(symbol: str, tf: str, buckets: int = 120) -> Dict[str, Any]:
    tf = ensure_rt_tf(tf)
    if tf == "1m":
        return {
            "ok": False,
            "symbol": symbol,
            "tf": tf,
            "reason": "aggregate_check_requires_tf_gt_1m",
            "supported": AGG_TFS,
        }

    rebuilt = _rebuild_tf_from_1m(symbol, tf, buckets)
    if not rebuilt:
        return {
            "ok": True,
            "symbol": symbol,
            "tf": tf,
            "rebuiltBars": 0,
            "cachedBars": 0,
            "mismatchCount": 0,
            "mismatches": [],
        }

    start_ms = int(rebuilt[0]["key"])
    end_ms = int(rebuilt[-1]["key"])
    cached = get_range(tf, symbol, start_ms, end_ms)

    c_map = {int(x["key"]): x for x in cached}
    r_map = {int(x["key"]): x for x in rebuilt}
    keys = sorted(set(c_map.keys()) | set(r_map.keys()))

    mismatches = []
    for k in keys:
        c = c_map.get(k)
        r = r_map.get(k)
        if c is None or r is None:
            mismatches.append(
                {
                    "key": k,
                    "kind": "missing_bar",
                    "cachedPresent": c is not None,
                    "rebuiltPresent": r is not None,
                }
            )
            continue

        diffs = {}
        for fld in ("o", "h", "l", "c", "v"):
            cv = float(c.get(fld) or 0.0)
            rv = float(r.get(fld) or 0.0)
            if abs(cv - rv) > 1e-9:
                diffs[fld] = {"cached": cv, "rebuilt": rv, "delta": cv - rv}
        if diffs:
            mismatches.append({"key": k, "kind": "value_diff", "diffs": diffs})

    return {
        "ok": True,
        "symbol": symbol,
        "tf": tf,
        "rebuiltBars": len(rebuilt),
        "cachedBars": len(cached),
        "mismatchCount": len(mismatches),
        "mismatches": mismatches,
        "sampleRebuilt": rebuilt[-5:],
        "sampleCached": cached[-5:],
    }
