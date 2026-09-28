# -*- coding: utf-8 -*-
"""
Legt EINMALIG den ersten Haupt-Account (is_main=True) an, wenn nach der
Einfuehrung des echten Mehrbenutzer-Kontosystems noch keine users-Zeile
existiert. Danach kann sich dieser Account einloggen und ueber die neue
Nutzerverwaltung (/api/users) weitere Personen-Accounts anlegen - ein
zweiter Lauf dieses Skripts ist normalerweise nicht noetig (bricht ab,
wenn die angegebene E-Mail schon existiert).

Voraussetzung: `alembic upgrade head` wurde bereits gegen die Ziel-
Datenbank ausgefuehrt (siehe die zuletzt angewendete Migration
f37109f1de46_nutzer_konten_users_tabelle.py). Gegen eine bereits
produktive Datenbank IMMER zuerst Backup + Schema-Check, genau wie bei
jeder anderen Migration in diesem Projekt - dieses Skript selbst prueft
nur, ob die Tabelle/E-Mail schon existiert, nichts weiter.

Nutzung (lokal oder gegen Produktion via DATABASE_URL):
    python scripts/seed_first_admin_user.py \
        --email admin@example.com --name "Max Mustermann" \
        --phone "0234 12345" --function "Geschaeftsfuehrung" \
        --street "Musterstrasse" --house-number "1" \
        --postal-code "12345" --city "Musterstadt"

Das Passwort wird interaktiv abgefragt (nicht als Kommandozeilenargument,
damit es nicht in der Shell-History landet).
"""
import argparse
import getpass
import os
import secrets
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.auth import hash_password  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--email", required=True)
    parser.add_argument("--name", required=True, help="Voller Name, z.B. 'Max Mustermann'")
    parser.add_argument("--phone", required=True)
    parser.add_argument("--function", required=True, help="z.B. 'Geschaeftsfuehrung'")
    parser.add_argument("--street", required=True)
    parser.add_argument("--house-number", required=True)
    parser.add_argument("--postal-code", required=True)
    parser.add_argument("--city", required=True)
    args = parser.parse_args()

    email = args.email.strip().lower()
    db = SessionLocal()
    try:
        if db.query(User).filter(User.email == email).first():
            print(f"Nutzer {email} existiert bereits - Abbruch.")
            return

        password = getpass.getpass("Passwort fuer den neuen Haupt-Account: ")
        confirm = getpass.getpass("Passwort wiederholen: ")
        if not password:
            print("Passwort darf nicht leer sein - Abbruch.")
            return
        if password != confirm:
            print("Passwoerter stimmen nicht ueberein - Abbruch.")
            return

        user = User(
            user_id=f"USR-{secrets.token_hex(6)}",
            email=email,
            password_hash=hash_password(password),
            full_name=args.name,
            phone=args.phone,
            function=args.function,
            street=args.street,
            house_number=args.house_number,
            postal_code=args.postal_code,
            city=args.city,
            is_main=True,
            active=True,
        )
        db.add(user)
        db.commit()
        print(f"Haupt-Account angelegt: {email} ({user.user_id})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
