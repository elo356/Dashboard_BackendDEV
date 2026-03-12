from typing import Dict, Any
from app.core.settings import TWELVE_API_KEY
from app.clients.http import get_json_url


def _err_payload(data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "status": data.get("status"),
        "code": data.get("code"),
        "message": data.get("message"),
    }


def _td_error_obj(data: Dict[str, Any], scope: str) -> Dict[str, Any]:
    err = _err_payload(data)
    return {
        "_td_error": True,
        "_td_error_scope": scope,
        "_td_error_code": err.get("code"),
        "_td_error_message": err.get("message"),
        "_td_error_status": err.get("status"),
    }


def td_fetch_profile(symbol: str) -> Dict[str, Any]:
    url = f"https://api.twelvedata.com/profile?symbol={symbol}&apikey={TWELVE_API_KEY}"
    data = get_json_url(url)

    if not data:
        print("[TD][PROFILE] empty", symbol)
        return {}

    # TwelveData error format
    if data.get("status") == "error":
        print("[TD][PROFILE][ERR]", symbol, _err_payload(data))
        return _td_error_obj(data, "profile")

    if not isinstance(data, dict) or not data.get("name"):
        if data.get("message"):
            print("[TD][PROFILE][WARN]", symbol, _err_payload(data))
        return {}

    return data


def td_fetch_earnings(symbol: str) -> Dict[str, Any]:
    url = f"https://api.twelvedata.com/earnings?symbol={symbol}&apikey={TWELVE_API_KEY}"
    data = get_json_url(url)

    if not data:
        print("[TD][EARN] empty", symbol)
        return {}

    if data.get("status") == "error":
        print("[TD][EARN][ERR]", symbol, _err_payload(data))
        return _td_error_obj(data, "earnings")

    if not isinstance(data, dict) or len(data) == 0:
        return {}

    return data
