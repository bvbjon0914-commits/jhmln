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

# Sicherstellen, dass die Ordner existieren
Path(TEMPLATES_DIR).mkdir(parents=True, exist_ok=True)
Path(GENERATED_DIR).mkdir(parents=True, exist_ok=True)
