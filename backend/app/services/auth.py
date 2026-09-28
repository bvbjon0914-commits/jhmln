"""
Einfache, zustandslose Login-Absicherung.

Zwei parallele Login-Wege: die urspruenglichen zwei geteilten Passwoerter
(aus der .env - ein geteiltes Passwort fuer alle und ein Haupt-Passwort mit
Extra-Rechten) UND echte Nutzer-Accounts (Tabelle `users`, E-Mail+Passwort,
siehe check_user_credentials). Die geteilten Passwoerter bleiben bewusst als
"Break-Glass"-Fallback bestehen, damit die Einfuehrung echter Accounts
niemanden aussperrt. Nach erfolgreichem Login wird ein signiertes Cookie
gesetzt, das den Login-Typ (is_main) und - bei einem echten Account - die
user_id traegt. Kein Server-seitiger Session-Speicher noetig.
"""

import base64
import hashlib
import hmac
import json
import secrets
import time
from typing import TYPE_CHECKING, Optional

from app.config import API_KEYS, AUTH_SECRET_KEY, MAIN_PASSWORD, SHARED_PASSWORD

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from app.models.user import User

COOKIE_NAME = "auth_token"
TOKEN_MAX_AGE_SECONDS = 60 * 60 * 24 * 30  # 30 Tage

# Passwort-Hashing fuer echte Nutzer-Accounts: bewusst Stdlib-PBKDF2 statt
# eines neuen Pakets (passlib/bcrypt) - passt zum Rest dieser Datei, die
# ausschliesslich hashlib/hmac/base64 nutzt. Die Iterationszahl steht im
# Hash-String selbst, damit eine spaetere Erhoehung bestehende Hashes nicht
# ungueltig macht (beim Verify wird die gespeicherte Zahl verwendet).
PBKDF2_ALGORITHM = "sha256"
PBKDF2_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    """Erzeugt 'pbkdf2_sha256$<iterationen>$<salt_b64>$<hash_b64>'."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode(), salt, PBKDF2_ITERATIONS)
    return (
        f"pbkdf2_sha256${PBKDF2_ITERATIONS}$"
        f"{base64.urlsafe_b64encode(salt).decode()}${base64.urlsafe_b64encode(digest).decode()}"
    )


def verify_password(password: str, stored_hash: str) -> bool:
    """Zeitkonstanter Vergleich gegen einen per hash_password() erzeugten Hash."""
    try:
        scheme, iterations_str, salt_b64, hash_b64 = stored_hash.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_b64)
        expected = base64.urlsafe_b64decode(hash_b64)
    except (ValueError, TypeError):
        return False
    candidate = hashlib.pbkdf2_hmac(PBKDF2_ALGORITHM, password.encode(), salt, int(iterations_str))
    return hmac.compare_digest(candidate, expected)


def check_user_credentials(db: "Session", email: str, password: str) -> Optional["User"]:
    """
    Sucht den aktiven Nutzer per E-Mail (case-insensitive) und prueft das
    Passwort. Gibt None zurueck bei unbekannter E-Mail, falschem Passwort
    ODER deaktiviertem Account - bewusst KEINE unterschiedlichen
    Fehlermeldungen nach aussen (verhindert User-Enumeration).
    """
    from app.models.user import User

    user = db.query(User).filter(User.email == email.strip().lower(), User.active.is_(True)).first()
    if user is None:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def _sign(payload_b64: str) -> str:
    signature = hmac.new(AUTH_SECRET_KEY.encode(), payload_b64.encode(), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(signature).decode().rstrip("=")


def create_token(is_main: bool, user_id: Optional[str] = None) -> str:
    payload = json.dumps({"is_main": is_main, "user_id": user_id, "iat": int(time.time())}).encode()
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


def check_api_key(key: str) -> bool:
    """
    Separater Zugang für Systemintegrationen (X-API-Key-Header) statt des
    Cookie-Logins für Menschen. Zeitkonstanter Vergleich gegen JEDEN
    konfigurierten Schlüssel (nicht nur den ersten Treffer abbrechen wäre
    zwar unnötig, aber compare_digest je Kandidat bleibt trotzdem
    zeitkonstant pro Vergleich) - bei leerer API_KEYS-Konfiguration immer
    False, das Feature ist dann vollständig inaktiv.
    """
    if not key:
        return False
    return any(hmac.compare_digest(key, candidate) for candidate in API_KEYS)
