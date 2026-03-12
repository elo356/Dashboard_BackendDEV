from typing import Any, Dict

from app.data.daily_store import read_daily_range
from app.historical.timeframes import HIST_TFS, ensure_hist_tf
from app.services.aggregation import build_tf_bars
from app.shared.diagnostics import momentum_breakdown, ptfav_trace


def inspect_pipeline_historical(
    symbol: str,
    tf: str,
    from_key: str,
    to_key: str,
    bars_needed: int = 120,
) -> Dict[str, Any]:
    tf = ensure_hist_tf(tf)
    daily = read_daily_range(symbol, from_key, to_key)
    bars = build_tf_bars(tf, daily) if tf in HIST_TFS else []
    if bars_needed > 0:
        bars = bars[-bars_needed:]

    closes = [float(x["c"]) for x in bars if x.get("c") is not None]
    mom = momentum_breakdown(closes)
    pt = ptfav_trace(bars)

    return {
        "ok": True,
        "symbol": symbol,
        "tf": tf,
        "barsCount": len(bars),
        "dailySourceCount": len(daily),
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

