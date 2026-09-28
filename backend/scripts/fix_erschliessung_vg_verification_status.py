"""
Einmalige Korrektur: die ERSCHLIESSUNG-Regeln für Bitburger Land und
Altenkirchen-Flammersfeld wurden VOR Einführung von
`resulting_verification_status` (siehe app/services/jurisdiction_staging.py)
fälschlich als "VERIFIED" freigegeben, obwohl die Quelle nur die eng
verwandte "Ausbaubeiträge"/"Beiträge für Verkehrsanlagen"-Zuständigkeit
bestätigt, nicht wörtlich "Erschließungsbeiträge" (siehe
scripts/seed_erschliessung_vg_rlp.py, BELEGLAGE_HINWEIS_SCHWAECHER).

Korrigiert NUR den Prüfstatus und ergänzt die Beleglage-Begründung im
`notes`-Feld - KEINE Änderung an Geltungsbereich, Behörde oder Adresse.
Betrifft ausschließlich die beiden genannten Verbandsgemeinden (138 Zeilen),
NICHT Prüm/Arzfeld/Simmern-Rheinböllen (dort "stark", bleibt VERIFIED) und
NICHT Trier (eigener, bereits im Ursprungslauf differenziert dokumentierter
Fall).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BELEGLAGE_HINWEIS = (
    "Quelle bestätigt die Zuständigkeit dieser Organisationseinheit ausdrücklich für '{belegt_fuer}', "
    "NICHT wörtlich für 'Erschließungsbeiträge' (§ 127 ff. BauGB) - beide Beitragsarten werden in der "
    "kommunalen Praxis nahezu durchgängig von derselben Stelle bearbeitet, das ist hier aber nicht "
    "wörtlich einzeln belegt. Nachträglich korrigiert von VERIFIED auf AUTO_IMPORTED, da die "
    "ursprüngliche Freigabe (vor Einführung von resulting_verification_status) die Beleglage zu stark "
    "eingestuft hatte."
)

CASES = {
    "Verbandsgemeindeverwaltung Bitburger Land - Abt. 4 (Bauen und Umwelt)": (
        "Straßenausbaubeiträge/wiederkehrende Beiträge für Verkehrsanlagen (Abt. 4: Bauen und Umwelt)"
    ),
    "Verbandsgemeindeverwaltung Altenkirchen-Flammersfeld - Fachgebiet 3.2 (Beiträge für Verkehrsanlagen, Infrastruktur)": (
        "Fachgebiet 3.2 - Beiträge für Verkehrsanlagen, Infrastruktur (Fachbereich 3: Infrastruktur, Umwelt und Bauen)"
    ),
}


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.authority import Authority
    from app.models.jurisdiction import Jurisdiction

    db = SessionLocal()
    try:
        total_corrected = 0
        for authority_name, belegt_fuer in CASES.items():
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                print(f"WARNUNG: Authority '{authority_name}' nicht gefunden - übersprungen.")
                continue
            rules = (
                db.query(Jurisdiction)
                .filter(
                    Jurisdiction.authority_id == authority.authority_id,
                    Jurisdiction.request_type_id == "ERSCHLIESSUNG",
                    Jurisdiction.verification_status == "VERIFIED",
                )
                .all()
            )
            hinweis = BELEGLAGE_HINWEIS.format(belegt_fuer=belegt_fuer)
            for rule in rules:
                rule.verification_status = "AUTO_IMPORTED"
                rule.notes = (rule.notes + " " if rule.notes else "") + hinweis
            print(f"{authority_name}: {len(rules)} Regeln korrigiert.")
            total_corrected += len(rules)
        db.commit()
        print(f"\nGesamt korrigiert: {total_corrected}")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
