from datetime import datetime
from typing import Dict, Any, List
from zoneinfo import ZoneInfo

from app.core.settings import TWELVE_API_KEY
from app.clients.http import get_json_url

TD_TZ = ZoneInfo("America/New_York")

def _to_epoch_ms(dt_str: str) -> int:
    # TwelveData intraday: "YYYY-MM-DD HH:MM:SS"
    # El engine intraday usa horario de mercado (ET); tratar esto como UTC
    # desplaza las velas ~4/5 horas y hace parecer que la data "se para" antes.
    dt = datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TD_TZ)
    return int(dt.timestamp() * 1000)

def td_fetch_last_1m(symbol: str, limit: int = 3) -> List[Dict[str, Any]]:
    url = (
        "https://api.twelvedata.com/time_series?"
        f"symbol={symbol}&interval=1min"
        "&timezone=America/New_York"
        f"&outputsize={max(3, limit)}"
        f"&apikey={TWELVE_API_KEY}"
    )

    data = get_json_url(url)

    if not data:
        print("[TD] empty response", symbol)
        return []

    if "values" not in data:
        print("[TD] no values", symbol, "resp=", {k: data.get(k) for k in ["status","code","message"]})
        return []


    values = data["values"]  
    values = list(reversed(values))  # old->new

    out: List[Dict[str, Any]] = []
    for row in values[-limit:]:
        t = _to_epoch_ms(row["datetime"])
        out.append(
            {
                "key": t,  # epoch ms
                "o": float(row["open"]),
                "h": float(row["high"]),
                "l": float(row["low"]),
                "c": float(row["close"]),
                "v": float(row.get("volume") or 0.0),
            }
        )
    return out
