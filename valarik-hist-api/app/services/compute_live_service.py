import time
from typing import Dict, Any, List, Optional

from app.config.symbols import SYMBOLS
from app.config.timeframes_rt import ensure_rt_tf

from app.data.intraday_cache import get_last, get_range
from app.services.formulas import compute_signal
from app.services.live_metrics import compute_live_metrics
from app.services.metric_contract import apply_metric_contract
from app.core.settings import TABLE_TTL_MS
from app.core.market import market_is_open
from app.data.intraday_cache import get_global_last_key
from app.config.timeframes_rt import TF_MS

# Table cache (similar a hist)
TABLE_CACHE: Dict[str, Dict[str, Any]] = {}
TABLE_CACHE_MS: Dict[str, int] = {}

# recuerda última key que causó recompute por tf
_LAST_KEY_SEEN: Dict[str, int] = {}
_LAST_PAYLOAD: Dict[str, Dict[str, Any]] = {}

def _can_recompute(tf: str) -> bool:
    """
    True si:
    - mercado abierto
    - y hay un lastKey global nuevo (cambió)
    """
    if not market_is_open():
        return False

    k = get_global_last_key("1m")  # tu engine live depende de 1m como fuente
    if not k:
        return False

    prev = _LAST_KEY_SEEN.get(tf)
    if prev == int(k):
        return False

    _LAST_KEY_SEEN[tf] = int(k)
    return True

def _now_ms() -> int:
    return int(time.time() * 1000)


def _table_cache_valid(cache_id: str) -> bool:
    ts = TABLE_CACHE_MS.get(cache_id, 0)
    return ts > 0 and (_now_ms() - ts) < TABLE_TTL_MS


def _table_cache_get(cache_id: str):
    if _table_cache_valid(cache_id):
        return TABLE_CACHE.get(cache_id)
    return None


def _table_cache_set(cache_id: str, payload: dict):
    TABLE_CACHE[cache_id] = payload
    TABLE_CACHE_MS[cache_id] = _now_ms()


def _get_last_n_bars(tf: str, symbol: str, n: int) -> List[Dict[str, Any]]:
    """
    Devuelve las últimas n barras del tf desde el cache intradía.
    Usa range por key (epoch ms) alrededor del lastKey.
    """
    last = get_last(tf, symbol)
    if not last:
        return []

    end_ms = int(last["key"])

    
    start_ms = end_ms - (n * TF_MS[tf] * 3)
    bars = get_range(tf, symbol, start_ms, end_ms)
    return bars[-n:] if bars else []


def compute_one_live(symbol: str, tf: str, bars_needed: int = 60) -> Dict[str, Any]:
    """
    Calcula ptfav/dptfav/mom/signal  con barras realtime.
    """
    try:
        tf = ensure_rt_tf(tf)
    except ValueError:
        return {"symbol": symbol, "tf": tf, "error": "tf_not_supported_in_realtime_v1"}

    bars = _get_last_n_bars(tf, symbol, bars_needed)
    if len(bars) < 2:
        return {
            "symbol": symbol,
            "tf": tf,
            "barsCount": len(bars),
            "ptfav": 0.0,
            "dptfav": 0.0,
            "trend": 0,
            "momScore": None,
            "signal": "HOLD",
            "lastKey": bars[-1]["key"] if bars else None,
        }

    metrics = compute_live_metrics(bars)
    sig = compute_signal(metrics["ptfav"], metrics["mom_score"])

    return {
        "symbol": symbol,
        "tf": tf,
        "barsCount": len(bars),
        "ptfav": metrics["ptfav"],
        "dptfav": metrics["dptfav"],
        "trend": metrics["trend_dir"],
        "trend_dir": metrics["trend_dir"],
        "momScore": metrics["mom_score"],
        "flowPct": metrics["flow_pct"],
        "trendAccelPct": metrics["trend_accel_pct"],
        "signal": sig,
        "lastKey": bars[-1]["key"] if bars else None,
    }


def compute_table_live(tf: str, top: int) -> Dict[str, Any]:
    tf = ensure_rt_tf(tf)
    cache_id = f"live|{tf}"

    def _make_top_mix(all_rows: List[Dict[str, Any]], top_n: int) -> List[Dict[str, Any]]:
        # all_rows expected already sorted by ptfav desc
        positives = [r for r in all_rows if float(r.get("ptfav") or 0.0) > 0]
        negatives = [r for r in all_rows if float(r.get("ptfav") or 0.0) < 0]
        negatives.sort(key=lambda x: float(x.get("ptfav") or 0.0))  # más negativo primero

        top_n = max(1, int(top_n))
        half = max(1, top_n // 2)

        top_mix = positives[:half] + negatives[: (top_n - half)]

        # fallback: si no hay suficientes negativos/positivos, rellena con el resto por magnitud
        if len(top_mix) < top_n:
            used = set(id(x) for x in top_mix)
            rest = [r for r in all_rows if id(r) not in used]
            rest.sort(key=lambda x: abs(float(x.get("ptfav") or 0.0)), reverse=True)
            top_mix += rest[: (top_n - len(top_mix))]

        return top_mix[:top_n]

    # ---------------- cached path ----------------
    if not _can_recompute(tf):
        cached = _table_cache_get(cache_id)
        if cached:
            rows = cached["rows"]
            # re-armar top mixto desde rows (por si top cambia)
            # (asegura orden ptfav desc)
            rows_sorted = sorted(rows, key=lambda x: float(x.get("ptfav") or 0.0), reverse=True)
            top_mix = _make_top_mix(rows_sorted, top)

            out = {**cached, "top": top_mix, "cached": True}
            _LAST_PAYLOAD[tf] = out
            return out

        lastp = _LAST_PAYLOAD.get(tf)
        if lastp:
            rows = lastp["rows"]
            rows_sorted = sorted(rows, key=lambda x: float(x.get("ptfav") or 0.0), reverse=True)
            top_mix = _make_top_mix(rows_sorted, top)
            return {**lastp, "top": top_mix, "cached": True}

    # ---------------- recompute path ----------------
    rows: List[Dict[str, Any]] = []
    for sym in SYMBOLS:
        r = compute_one_live(sym, tf, bars_needed=60)
        rows.append(r)

    # orden global (rank/rows)
    rows.sort(key=lambda x: float(x.get("ptfav") or 0.0), reverse=True)

    # Flow%: usar suma ABS para que negativos también tengan porcentaje (con signo)
    abs_sum = sum(abs(float(r.get("ptfav") or 0.0)) for r in rows)

    for i, r in enumerate(rows, start=1):
        r["rankFlow"] = i
        pt = float(r.get("ptfav") or 0.0)

        # flow% firmado: negativos salen negativos
        r["flowPctTotal"] = (pt / abs_sum) if abs_sum > 0 else 0.0

        # targetWt: si quieres LONG-only, deja siempre positivo:
        r["targetWt"] = 0.12 if (i <= 3 and pt > 0) else abs(float(r["flowPctTotal"]))
        apply_metric_contract(r)

        # Si en vez de eso quieres targetWt con signo (para short):
        # r["targetWt"] = 0.12 if (i <= 3 and pt > 0) else float(r["flowPctTotal"])

    top_mix = _make_top_mix(rows, top)

    payload = {
        "ok": True,
        "tf": tf,
        "symbols": len(SYMBOLS),
        "updatedAt": _now_ms(),
        "cached": False,
        "rows": rows,
        "top": top_mix,
    }

    _table_cache_set(cache_id, payload)
    _LAST_PAYLOAD[tf] = payload
    return payload
