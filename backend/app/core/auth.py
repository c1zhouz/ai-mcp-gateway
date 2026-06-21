import hashlib
import json
import secrets
from datetime import datetime
from typing import Iterable, Optional

from fastapi import HTTPException, Request

from backend.app.models.database import get_db


HASH_PREFIX = "sha256:"


def hash_api_key(api_key: str) -> str:
    return HASH_PREFIX + hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def mask_api_key(stored_value: str) -> str:
    if stored_value.startswith(HASH_PREFIX):
        return "gw-****"
    return stored_value[:8] + "****"


def _load_permissions(raw_permissions: str) -> list[str]:
    try:
        value = json.loads(raw_permissions or "[]")
    except json.JSONDecodeError:
        return []
    return value if isinstance(value, list) else []


def _has_permission(actual: Iterable[str], required: str) -> bool:
    permissions = set(actual)
    return "admin" in permissions or required in permissions


def _is_expired(expires_at: Optional[str]) -> bool:
    if not expires_at:
        return False
    try:
        return datetime.fromisoformat(expires_at) < datetime.now()
    except ValueError:
        return True


def _extract_bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    scheme, _, token = auth.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    return token


async def require_api_key(request: Request, permission: str = "read") -> dict:
    token = _extract_bearer_token(request)
    token_hash = hash_api_key(token)

    db = await get_db()
    rows = await db.execute("SELECT * FROM api_keys WHERE status='active'")
    async for row in rows:
        key = dict(row)
        stored_value = key["key_value"]
        matches_hash = secrets.compare_digest(stored_value, token_hash)
        matches_legacy_plaintext = secrets.compare_digest(stored_value, token)
        if not (matches_hash or matches_legacy_plaintext):
            continue

        if _is_expired(key.get("expires_at")):
            await db.close()
            raise HTTPException(status_code=401, detail="API key expired")

        permissions = _load_permissions(key.get("permissions", "[]"))
        if not _has_permission(permissions, permission):
            await db.close()
            raise HTTPException(status_code=403, detail="Insufficient API key permissions")

        key["permissions"] = permissions
        await db.close()
        return key

    await db.close()
    raise HTTPException(status_code=401, detail="Invalid API key")
