from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.config.timeframes import HIST_TFS
from app.data.daily_store import read_daily_range
from app.services.compute_service import compute_one, compute_table

router = APIRouter(tags=["hist"])


def reject_tf(tf: str):
    return JSONResponse(
        {
            "ok": False,
            "tf": tf,
            "reason": "tf_not_supported_in_hist_v1",
            "supported": ["1D", "1W", "1M", "1Y"],
        },
        status_code=400,
    )


@router.get("/health")
def health():
    # symbols count is in compute_table payload; keep health minimal
    return {"ok": True}


@router.get("/hist/read")
def hist_read(
    symbol: str = Query(...),
    from_key: str = Query("20190101"),
    to_key: str = Query("20991231"),
    n: int = Query(5),
):
    bars = read_daily_range(symbol, from_key, to_key)
    return {
        "symbol": symbol,
        "bars": len(bars),
        "firstKey": bars[0]["key"] if bars else None,
        "lastKey": bars[-1]["key"] if bars else None,
        "sample": bars[: max(0, int(n))],
    }


@router.get("/hist/mom")
def hist_mom(
    symbol: str = Query(...),
    tf: str = Query("1D"),
    from_key: str = Query("20190101"),
    to_key: str = Query("20991231"),
):
    if (tf or "").strip() not in HIST_TFS:
        return reject_tf(tf)
    r = compute_one(symbol, tf, from_key, to_key)
    if r.get("error"):
        return reject_tf(tf)
    return {"symbol": symbol, "tf": tf, "bars": r["barsCount"], "momScore": r["momScore"], "lastKey": r["lastKey"]}


@router.get("/hist/ptfav")
def hist_ptfav(
    symbol: str = Query(...),
    tf: str = Query("1D"),
    from_key: str = Query("20190101"),
    to_key: str = Query("20991231"),
):
    if (tf or "").strip() not in HIST_TFS:
        return reject_tf(tf)
    r = compute_one(symbol, tf, from_key, to_key)
    if r.get("error"):
        return reject_tf(tf)
    return {
        "symbol": symbol,
        "tf": tf,
        "bars": r["barsCount"],
        "ptfav": r["ptfav"],
        "dptfav": r["dptfav"],
        "trend": r["trend"],
        "momScore": r["momScore"],
        "signal": r["signal"],
        "lastKey": r["lastKey"],
    }


@router.get("/hist/table")
def hist_table(tf: str = "1D", top: int = 50, from_key: str = "20190101", to_key: str = "20991231"):
    try:
        payload = compute_table(tf, top, from_key, to_key)
        return {
            "ok": True,
            "tf": payload["tf"],
            "top": payload["top"],
            "updatedAt": payload["updatedAt"],
            "cached": payload["cached"],
            "symbols": payload["symbols"],
        }
    except ValueError:
        return reject_tf(tf)


@router.get("/hist/dump")
def hist_dump(tf: str = Query("1D"), from_key: str = Query("20190101"), to_key: str = Query("20991231")):
    if (tf or "").strip() not in HIST_TFS:
        return reject_tf(tf)
    # full dump without caching
    from app.config.symbols import SYMBOLS  # local import ok
    rows = [compute_one(sym, tf, from_key, to_key) for sym in SYMBOLS]
    return {"ok": True, "tf": tf, "rows": rows}
