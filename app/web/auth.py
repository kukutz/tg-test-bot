from __future__ import annotations

import hashlib
import hmac
from urllib.parse import parse_qsl

from fastapi import HTTPException

from app.config import get_settings


def verify_init_data(init_data: str) -> None:
    settings = get_settings()
    if settings.environment == "development":
        return
    if not init_data:
        raise HTTPException(status_code=401, detail="Missing init data")
    data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = data.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=401, detail="Missing hash")
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data.items()))
    secret_key = hmac.new(
        key=b"WebAppData",
        msg=settings.telegram_bot_token.encode(),
        digestmod=hashlib.sha256,
    ).digest()
    calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid init data")

