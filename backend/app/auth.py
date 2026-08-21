"""
Core auth primitives: password hashing and JWT issuance/validation.
No FastAPI-specific code here — that lives in auth_routes.py and deps.py.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: str, organization_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": user_id, "org": organization_id, "type": "access", "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != "access":
            return None
        return payload
    except JWTError:
        return None


def generate_refresh_token() -> tuple[str, str, datetime]:
    """Returns (raw_token_to_send_to_client, hash_to_store_in_db, expires_at).
    We never store the raw refresh token, only its hash — same principle as
    password storage, so a DB leak alone doesn't let someone impersonate users."""
    raw = secrets.token_urlsafe(48)
    token_hash = hashlib.sha256(raw.encode()).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return raw, token_hash, expires_at


def hash_refresh_token(raw_token: str) -> str:
    return hashlib.sha256(raw_token.encode()).hexdigest()
