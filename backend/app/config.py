"""
Zentrale Konfiguration der Anwendung
"""

import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent  # backend/
ENV_FILE = BASE_DIR / ".env"

# Beim allerersten lokalen Start werden Zugangsdaten automatisch generiert und
# in .env gespeichert, falls die Datei noch nicht existiert. So gibt es nie
# einen hartkodierten Standard-Login im Quellcode. Auf einer Plattform wie
# Render kommen die Werte stattdessen als echte Umgebungsvariablen – dann wird
# gar nicht erst versucht, eine (dort ohnehin flüchtige) Datei zu schreiben.
if not ENV_FILE.exists() and "SHARED_PASSWORD" not in os.environ:
    ENV_FILE.write_text(
        "\n".join(
            [
                f"SHARED_PASSWORD={secrets.token_urlsafe(9)}",
                f"MAIN_PASSWORD={secrets.token_urlsafe(9)}",
                f"AUTH_SECRET_KEY={secrets.token_urlsafe(32)}",
                "",
            ]
        ),
        encoding="utf-8",
    )

load_dotenv(ENV_FILE)

TEMPLATES_DIR = os.getenv("TEMPLATES_DIR", str(BASE_DIR / "templates"))
GENERATED_DIR = os.getenv("GENERATED_DIR", str(BASE_DIR / "generated"))

# ========== Login ==========

SHARED_PASSWORD = os.environ["SHARED_PASSWORD"]
MAIN_PASSWORD = os.environ["MAIN_PASSWORD"]
AUTH_SECRET_KEY = os.environ["AUTH_SECRET_KEY"]

# Das Session-Cookie soll in Produktion nur über HTTPS übertragen werden
# (Auditbericht, Befund "Session-Sicherheit"). Default true; für lokale
# Entwicklung ohne TLS (z.B. reines http://localhost) in .env auf false
# setzen - sonst schickt der Browser das Cookie gar nicht erst mit.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "true").lower() == "true"

# CORS: In Produktion werden Frontend und Backend vom selben FastAPI-Prozess
# ausgeliefert (siehe SERVE_FRONTEND in main.py) - dort ist CORS für den
# eigentlichen Betrieb gar nicht nötig (same-origin). Ein Wildcard-Origin
# war trotzdem gesetzt (Auditbericht, Befund "Netzwerksicherheit") und wird
# nur für die lokale Entwicklung gebraucht, wo Vite (Frontend) und Uvicorn
# (Backend) auf unterschiedlichen Ports laufen. ALLOWED_ORIGINS erlaubt eine
# explizite, kommagetrennte Liste; ohne Angabe gilt ein enger Dev-Default.
_allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "").strip()
if _allowed_origins_env:
    ALLOWED_ORIGINS = [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]
else:
    ALLOWED_ORIGINS = [
        "http://localhost:5173", "http://127.0.0.1:5173",  # Vite Dev-Server
        "http://localhost:3000", "http://127.0.0.1:3000",
    ]

# ========== Login-Ratenbegrenzung ==========
# Schützt /api/auth/login vor massenhaften Rateversuchen (Auditbericht,
# Befund "Missbrauchsschutz"). Bewusst ein einfacher In-Memory-Zähler statt
# einer externen Abhängigkeit (Redis o.ä.) - konsistent mit dem übrigen
# Architekturstand (auch der Nominatim-Rate-Limiter in geocoding.py ist
# prozesslokal). Das bedeutet: der Zähler wird bei einem Neustart geleert
# und gilt nicht prozessübergreifend, falls je mit mehreren Worker-Prozessen
# oder Instanzen betrieben wird - für den aktuellen Single-Prozess-Betrieb
# (siehe render.yaml, kein --workers) ausreichend, aber keine verteilte
# Lösung. Bei echtem Mehrprozess-/Mehrinstanzbetrieb müsste dies durch einen
# gemeinsamen Speicher (z.B. die Datenbank oder Redis) ersetzt werden.
LOGIN_RATE_LIMIT_MAX_ATTEMPTS = int(os.getenv("LOGIN_RATE_LIMIT_MAX_ATTEMPTS", "10"))
LOGIN_RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("LOGIN_RATE_LIMIT_WINDOW_SECONDS", str(15 * 60)))

# ========== API-Schlüssel für Systemintegrationen ==========
# Grundlage für Priorität 3 (Integrationsvorbereitung, siehe Auditbericht-
# Folgebericht, Befund "M2M-Zugriff"): bisher gab es keinen eigenständigen
# Zugang für automatisierte Systeme (Nightly-Sync-Job, künftige ERP-
# Anbindung o.ä.) - nur dasselbe geteilte Login-Passwort wie für Menschen im
# Browser. Kommagetrennte Liste statischer Schlüssel, bewusst analog zum
# bestehenden SHARED_PASSWORD/MAIN_PASSWORD-Muster (kein neues Konzept, keine
# neue Abhängigkeit) statt eines vollständigen OAuth2-/Client-Credentials-
# Systems - das bleibt eine spätere, größere Ausbaustufe. Leer per Default:
# das Feature ist inaktiv, bis mindestens ein Schlüssel konfiguriert wird.
_api_keys_env = os.getenv("API_KEYS", "").strip()
API_KEYS = {k.strip() for k in _api_keys_env.split(",") if k.strip()}

# Sicherstellen, dass die Ordner existieren
Path(TEMPLATES_DIR).mkdir(parents=True, exist_ok=True)
Path(GENERATED_DIR).mkdir(parents=True, exist_ok=True)

# ========== Mailgun (Postfach: Versand + Empfang) ==========
# Kein Default für API-Key/Domain/Signing-Key: solange sie fehlen, meldet
# der mailgun_service beim Versand klar "nicht konfiguriert" statt mit einer
# verwirrenden Exception abzustürzen, und der Inbound-Webhook lehnt jeden
# Aufruf ohne gültige Signatur ab (siehe mailbox_inbound.py) statt
# unsignierte Anfragen stillschweigend zu akzeptieren - das Konto/die
# Domain existieren zum Zeitpunkt dieser Änderung noch nicht, die App muss
# trotzdem lauffähig bleiben.
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY", "")
MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN", "")
MAILGUN_FROM_ADDRESS = os.getenv(
    "MAILGUN_FROM_ADDRESS",
    f"Civeloq <anfragen@{MAILGUN_DOMAIN}>" if MAILGUN_DOMAIN else "",
)
# Bei true wird der Versand nur geloggt statt die echte Mailgun-API
# aufzurufen - ermöglicht sicheres lokales Testen ohne laufendes Konto.
MAILGUN_DRY_RUN = os.getenv("MAILGUN_DRY_RUN", "false").lower() == "true"
MAILGUN_WEBHOOK_SIGNING_KEY = os.getenv("MAILGUN_WEBHOOK_SIGNING_KEY", "")
