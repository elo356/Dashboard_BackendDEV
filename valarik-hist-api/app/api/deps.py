from fastapi import Header, HTTPException
from typing import Optional

from app.core.settings import ADMIN_KEY


def require_admin(x_admin_key: Optional[str]):
    if ADMIN_KEY and x_admin_key != ADMIN_KEY:
        raise HTTPException(status_code=401, detail="unauthorized")


def admin_header(x_admin_key: Optional[str] = Header(None)) -> Optional[str]:
    return x_admin_key
