import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone
from typing import Any

from app.core.config import settings


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64decode(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return f"pbkdf2_sha256${_b64encode(salt)}${_b64encode(digest)}"


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, salt_b64, digest_b64 = password_hash.split("$")
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False

    salt = _b64decode(salt_b64)
    expected = _b64decode(digest_b64)
    actual = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 120_000)
    return hmac.compare_digest(actual, expected)


def create_access_token(payload: dict[str, Any]) -> str:
    now = datetime.now(timezone.utc)
    exp = now + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    claims = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int(exp.timestamp()),
    }

    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode())
    payload_b64 = _b64encode(json.dumps(claims, separators=(",", ":")).encode())
    signing_input = f"{header_b64}.{payload_b64}".encode()
    signature = hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        signing_input,
        hashlib.sha256,
    ).digest()
    return f"{header_b64}.{payload_b64}.{_b64encode(signature)}"


def decode_access_token(token: str) -> dict[str, Any]:
    header_b64, payload_b64, signature_b64 = token.split(".")
    signing_input = f"{header_b64}.{payload_b64}".encode()
    expected = hmac.new(
        settings.JWT_SECRET_KEY.encode(),
        signing_input,
        hashlib.sha256,
    ).digest()
    actual = _b64decode(signature_b64)
    if not hmac.compare_digest(actual, expected):
        raise ValueError("Invalid token signature")

    payload = json.loads(_b64decode(payload_b64))
    if int(payload["exp"]) < int(time.time()):
        raise ValueError("Token expired")
    return payload
