"""Hachage des mots de passe (PBKDF2) et jetons signés (HMAC-SHA256)."""
import base64
import hashlib
import hmac
import json
import secrets
import time

from app import config

PBKDF2_ITERATIONS = 260_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2${PBKDF2_ITERATIONS}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, iterations, salt_hex, digest_hex = stored.split("$")
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), bytes.fromhex(salt_hex), int(iterations)
        )
        return hmac.compare_digest(digest.hex(), digest_hex)
    except (ValueError, TypeError):
        return False


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64decode(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def _sign(payload_b64: str) -> str:
    sig = hmac.new(config.SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256)
    return _b64encode(sig.digest())


def create_token(user_id: int) -> str:
    payload = {
        "uid": user_id,
        "exp": int(time.time()) + config.TOKEN_TTL_HOURS * 3600,
    }
    payload_b64 = _b64encode(json.dumps(payload).encode())
    return f"{payload_b64}.{_sign(payload_b64)}"


def decode_token(token: str) -> int | None:
    """Retourne l'id utilisateur, ou None si le jeton est invalide/expiré."""
    try:
        payload_b64, signature = token.split(".")
    except ValueError:
        return None
    if not hmac.compare_digest(signature, _sign(payload_b64)):
        return None
    try:
        payload = json.loads(_b64decode(payload_b64))
    except (ValueError, json.JSONDecodeError):
        return None
    if payload.get("exp", 0) < time.time():
        return None
    return payload.get("uid")
