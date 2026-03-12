import os, time
from typing import Dict, Any, List, Callable, Optional

from app.config.symbols import SYMBOLS
from app.data.fund_cache import get as get_fund, set_symbol, load_snapshot, save_snapshot
from app.clients.twelvedata_fund import td_fetch_profile, td_fetch_earnings


def _now_ms() -> int:
    return int(time.time() * 1000)


def _sleep_ms(ms: int) -> None:
    time.sleep(max(0, ms) / 1000.0)


def _td_error_code(payload: Dict[str, Any]) -> int | None:
    if not isinstance(payload, dict) or not payload.get("_td_error"):
        return None
    code = payload.get("_td_error_code")
    try:
        return int(code)
    except Exception:
        return None


def _is_valid_fetch_payload(payload: Dict[str, Any]) -> bool:
    return isinstance(payload, dict) and len(payload) > 0 and (not payload.get("_td_error"))


def _fetch_with_retry(fn: Callable[[str], dict], sym: str, tries: int = 3) -> dict:
    """
    retry suave con backoff: 0.7s, 1.4s, 2.1s
    """
    out = {}
    for i in range(tries):
        try:
            out = fn(sym) or {}
        except Exception as e:
            print("[FUND][ERR]", sym, fn.__name__, repr(e))
            out = {}

        if _is_valid_fetch_payload(out):
            return out

        code = _td_error_code(out)
        if code == 429:
            cooldown = int(os.getenv("FUND_429_COOLDOWN_SEC", "25"))
            print(f"[FUND][429] {sym} {fn.__name__} cooldown {cooldown}s")
            time.sleep(cooldown)
            continue

        time.sleep(0.7 * (i + 1))
    return {}


def _has_earnings_data(payload: Dict[str, Any]) -> bool:
    if (not isinstance(payload, dict)) or len(payload) == 0 or payload.get("_td_error"):
        return False

    # TwelveData suele responder {"meta": ..., "earnings": [...]}
    rows = payload.get("earnings")
    if isinstance(rows, list):
        return len(rows) > 0

    # fallback para payloads compactos/custom
    return any(payload.get(k) not in (None, "", [], {}) for k in ("last_date", "eps_actual", "eps_estimate"))


class MinuteLimiter:
    """
    Rate limiter por minuto.
    Por ejemplo: max_per_min=500 asegura no pasar 610.
    """
    def __init__(self, max_per_min: int):
        self.max_per_min = max_per_min
        self.count = 0
        self.window_start = time.time()

    def hit(self, n: int = 1):
        now = time.time()
        elapsed = now - self.window_start

        if elapsed >= 60:
            self.window_start = now
            self.count = 0
            elapsed = 0

        if self.count + n > self.max_per_min:
            sleep_left = 60 - elapsed
            if sleep_left > 0:
                print(f"[FUND][RL] sleeping {sleep_left:.1f}s (limit {self.max_per_min}/min)")
                time.sleep(sleep_left)
            self.window_start = time.time()
            self.count = 0

        self.count += n


def refresh_fundamentals_once(
    limit: int = 0,
    offset: int = 0,
    sleep_ms: int = 1200,
    missing_only: int = 1,
    include_earnings: Optional[int] = None,
    max_per_min: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Refresh fundamentals seguro:
    - missing_only=1 => solo símbolos sin profile.name
    - include_earnings=0/1 (default env FUND_FETCH_EARNINGS)
    - max_per_min (default env FUND_MAX_PER_MIN; safe 500)
    - NO pisa data buena con respuestas vacías
    """
    load_snapshot()

    if include_earnings is None:
        include_earnings = 1 if os.getenv("FUND_FETCH_EARNINGS", "0") == "1" else 0

    if max_per_min is None:
        max_per_min = int(os.getenv("FUND_MAX_PER_MIN", "500"))

    limiter = MinuteLimiter(max_per_min=max_per_min)

    # --- build symbol list ---
    base = SYMBOLS[offset:]
    if limit and limit > 0:
        base = base[:limit]

    syms: List[str] = []
    if missing_only:
        for s in base:
            v = get_fund(s) or {}
            prof = (v.get("profile") or {}) if isinstance(v, dict) else {}
            earn = (v.get("earnings") or {}) if isinstance(v, dict) else {}
            missing_profile = not prof.get("name")
            missing_earnings = bool(include_earnings) and (not _has_earnings_data(earn))

            if missing_profile or missing_earnings:
                syms.append(s)
    else:
        syms = list(base)

    n_target = len(syms)
    started = _now_ms()

    updated = 0
    skipped_empty = 0
    still_missing = 0
    fails: List[str] = []
    updated_syms: List[str] = []

    for i, sym in enumerate(syms, start=1):
        existing = get_fund(sym) or {}
        existing_prof = (existing.get("profile") or {}) if isinstance(existing, dict) else {}
        existing_earn = (existing.get("earnings") or {}) if isinstance(existing, dict) else {}
        existing_has_name = bool(existing_prof.get("name"))

        limiter.hit(1)
        profile = _fetch_with_retry(td_fetch_profile, sym, tries=3) or {}

        earnings: Dict[str, Any] = existing_earn if isinstance(existing_earn, dict) else {}
        if include_earnings:
            limiter.hit(1)
            fetched_earnings = _fetch_with_retry(td_fetch_earnings, sym, tries=2) or {}
            if _has_earnings_data(fetched_earnings):
                earnings = fetched_earnings

        has_good_profile = isinstance(profile, dict) and bool(profile.get("name"))
        has_earnings = _has_earnings_data(earnings)
        has_any = has_good_profile or has_earnings

        if not has_any:
            if existing_has_name:
                skipped_empty += 1
                print(f"[FUND][SKIP_EMPTY_KEEP] {sym} ({i}/{n_target})")
            else:
                still_missing += 1
                fails.append(sym)
                print(f"[FUND][MISSING] {sym} ({i}/{n_target})")
            _sleep_ms(sleep_ms)
            continue

        profile_out = profile if has_good_profile else existing_prof
        if not has_good_profile and not existing_has_name:
            profile_out = {}

        payload = {
            "profile": profile_out if isinstance(profile_out, dict) else {},
            "earnings": earnings if isinstance(earnings, dict) else {},
            "updatedAt": _now_ms(),
        }
        set_symbol(sym, payload)
        updated += 1
        updated_syms.append(sym)

        if (i % 10) == 0:
            print(f"[FUND] {i}/{n_target} updated={updated} missing={still_missing} keep={skipped_empty}")

        _sleep_ms(sleep_ms)

    save_snapshot(force=True)

    took = _now_ms() - started
    return {
        "ok": True,
        "offset": offset,
        "limit": limit,
        "sleep_ms": sleep_ms,
        "missing_only": int(bool(missing_only)),
        "include_earnings": int(bool(include_earnings)),
        "max_per_min": max_per_min,
        "symbols_target": n_target,
        "updated": updated,
        "skipped_empty_but_kept_existing": skipped_empty,
        "still_missing": still_missing,
        "fails_sample": fails[:25],
        "updated_sample": updated_syms[:25],
        "took_ms": took,
    }
