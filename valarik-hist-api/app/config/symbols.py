import json, os
from pathlib import Path


def load_symbols() -> list[str]:
    env = os.getenv("SYMBOLS")
    if env:
        return [s.strip() for s in env.split(",") if s.strip()]

    p = Path(__file__).with_name("symbols.json")
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        return [str(x).strip() for x in data if str(x).strip()]

    return ["AAPL", "TLT", "GLD"]


SYMBOLS = load_symbols()
