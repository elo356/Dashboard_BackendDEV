import os
from dotenv import load_dotenv


def _load_env():
    # busca .env en cwd y parent 
    try:
        load_dotenv(".env")
        load_dotenv("../.env")
    except Exception:
        pass


_load_env()


def must_env(name: str) -> str:
    v = os.getenv(name)
    if not v:
        raise RuntimeError(f"Missing env: {name}")
    return v


TWELVE_API_KEY = os.getenv("TWELVEDATA_API_KEY") or ""
FIREBASE_DATABASE_URL = (os.getenv("FIREBASE_DATABASE_URL") or "").rstrip("/")
FIREBASE_AUTH = os.getenv("FIREBASE_AUTH") or ""  # opcional (db secret / token)

if not TWELVE_API_KEY:
    raise RuntimeError("Missing env: TWELVEDATA_API_KEY")
if not FIREBASE_DATABASE_URL:
    raise RuntimeError("Missing env: FIREBASE_DATABASE_URL")

ADMIN_KEY = os.getenv("ADMIN_KEY") or ""  # recomendado
TABLE_TTL_MS = int(os.getenv("TABLE_TTL_MS", "60000"))
