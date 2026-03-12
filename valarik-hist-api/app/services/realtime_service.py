import os, time
from typing import Callable, Dict, Any, List, Optional

from app.data.intraday_cache import upsert_bar, get_last, trim_older_than
from app.config.timeframes_rt import AGG_TFS, TF_MS
from app.services.aggregation_rt import bucket_start, merge_into
from app.config.symbols import SYMBOLS
def _now_ms() -> int:
    return int(time.time() * 1000)



def symbols() -> List[str]:
    return SYMBOLS


def ingest_1m(symbol: str, fetch_1m: Callable[[str, int], List[Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    # Traes 3 velas y elegimos lacerra = penúltima (actual -1 min)
    bars = fetch_1m(symbol, 3)
    if not bars:
        return None

    closed = bars[-2] if len(bars) >= 2 else bars[-1]

    upsert_bar("1m", symbol, closed)

    # Trim 1m (default 7 días)
    days_1m = int(os.getenv("CACHE_DAYS_1M", "7"))
    trim_older_than("1m", symbol, _now_ms() - days_1m * 24 * 3600 * 1000)

    return closed

def update_aggregates_from_1m(symbol: str, bar_1m: Dict[str, Any]) -> None:
    """
    - Agrega TFs chicos desde 1m: 5m/15m/30m/1h
    - Agrega TFs grandes desde el bucket 1h vivo: 4h/6h/12h
    - Los TFs grandes se mantienen como barras vivas intrasesión, no como barras cerradas tradicionales
    """

    # 1) Primero actualiza los TFs chicos directamente con 1m
    small_tfs = ["5m", "15m", "30m", "1h"]
    for tf in small_tfs:
        bkey = bucket_start(int(bar_1m["key"]), tf)

        last = get_last(tf, symbol)
        if last is not None and int(last["key"]) != int(bkey):
            last = None

        merged = merge_into(last, bar_1m, bkey, tf, "1m")
        upsert_bar(tf, symbol, merged)

        days_tf = int(os.getenv("CACHE_DAYS_TF", "30"))
        trim_older_than(tf, symbol, _now_ms() - days_tf * 24 * 3600 * 1000)

    # 2) Luego actualiza TFs grandes usando el último 1h vivo disponible.
    # Esto mantiene 4h/6h/12h como buckets intrasesión vivos y etiquetados con metadata.
    last_1h = get_last("1h", symbol)
    if not last_1h:
        return

    bar_1h = last_1h

    big_tfs = ["4h", "6h", "12h"]
    for tf in big_tfs:
        bkey = bucket_start(int(bar_1h["key"]), tf)

        last = get_last(tf, symbol)
        if last is not None and int(last["key"]) != int(bkey):
            last = None

        merged = merge_into(last, bar_1h, bkey, tf, "1h")
        upsert_bar(tf, symbol, merged)

        days_tf = int(os.getenv("CACHE_DAYS_TF", "30"))
        trim_older_than(tf, symbol, _now_ms() - days_tf * 24 * 3600 * 1000)
