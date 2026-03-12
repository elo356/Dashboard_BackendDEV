from datetime import datetime
from typing import Dict

from app.core.settings import TWELVE_API_KEY
from app.clients.http import get_json_url
from typing import Any

def td_fetch_daily_range(symbol: str, start_key: str, end_key: str) -> Dict[str, dict]:
    start = datetime.strptime(start_key, "%Y%m%d").strftime("%Y-%m-%d")
    end = datetime.strptime(end_key, "%Y%m%d").strftime("%Y-%m-%d")

    url = (
        "https://api.twelvedata.com/time_series?"
        f"symbol={symbol}&interval=1day"
        f"&start_date={start}&end_date={end}"
        f"&apikey={TWELVE_API_KEY}"
    )

    data = get_json_url(url)
    if not data or "values" not in data:
        return {}

    out: Dict[str, dict] = {}
    for row in data["values"]:
        dt = row["datetime"][:10].replace("-", "")
        out[dt] = {
            "o": float(row["open"]),
            "h": float(row["high"]),
            "l": float(row["low"]),
            "c": float(row["close"]),
            "v": float(row.get("volume") or 0.0),
        }
    return out


# -----------------------------
# PROFILE (company info)
# -----------------------------
def td_fetch_profile(symbol: str) -> Dict[str, Any]:
    url = (
        "https://api.twelvedata.com/profile?"
        f"symbol={symbol}&apikey={TWELVE_API_KEY}"
    )

    data = get_json_url(url)
    if not data or "name" not in data:
        return {}

    return {
        "name": data.get("name"),
        "sector": data.get("sector"),
        "industry": data.get("industry"),
        "exchange": data.get("exchange"),
    }


# -----------------------------
# EARNINGS (historical EPS)
# -----------------------------
def td_fetch_earnings(symbol: str) -> Dict[str, Any]:
    url = (
        "https://api.twelvedata.com/earnings?"
        f"symbol={symbol}&apikey={TWELVE_API_KEY}"
    )

    data = get_json_url(url)
    if not data or "earnings" not in data:
        return {}

    earnings = data.get("earnings", [])

    if not earnings:
        return {}

    latest = earnings[0]

    return {
        "last_date": latest.get("date"),
        "eps_actual": latest.get("eps"),
        "eps_estimate": latest.get("eps_estimated"),
    }
