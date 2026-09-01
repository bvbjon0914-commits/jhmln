"""
Einfache, zustandslose Login-Absicherung.

Kein Nutzer-Konto-System: es gibt genau zwei Passwörter (aus der .env) —
ein geteiltes Passwort für alle und ein Haupt-Passwort mit Extra-Rechten.
Nach erfolgreichem Login wird ein signiertes Cookie gesetzt, das den
Login-Typ (is_main) trägt. Kein Server-seitiger Session-Speicher nötig.
"""

import base64
import hashlib
import hmac
import json
import time

from app.config import AUTH_SECRET_KEY, MAIN_PASSWORD, SHARED_PASSWORD

COOKIE_NAME = "auth_token"
TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 Tage


def _sign(payload_b64: str) -> str:
    signature = hmac.new(AUTH_SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(signature).decode().rstrip("=")


def create_token(is_main: bool) -> str:
    payload = json.dumps({"is_main": is_main, "iat": int(time.time())}).encode()
    payload_b64 = base64.urlsafe_b64encode(payload).decode().rstrip("=")
    return f"{payload_b64}.{_sign(payload_b64)}"


def verify_token(token: str) -> dict | None:
    try:
        payload_b64, signature = token.split(".", 1)
    except ValueError:
        return None

    if not hmac.compare_digest(_sign(payload_b64), signature):
        return None

    try:
        padded = payload_b64 + "=" * (-len(payload_b64) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded))
    except (ValueError, json.JSONDecodeError):
        return None

    if time.time() - payload.get("iat", 0) > TOKEN_MAX_AGE_SECONDS:
        return None

    return payload


def check_password(password: str) -> str | None:
    """Gibt 'main', 'shared' oder None zurück."""
    if hmac.compare_digest(password, MAIN_PASSWORD):
        return "main"
    if hmac.compare_digest(password, SHARED_PASSWORD):
        return "shared"
    return None
