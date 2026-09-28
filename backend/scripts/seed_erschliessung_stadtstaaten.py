"""
ERSCHLIESSUNGSBEITRAEGE (§ 127 ff. BauGB) fuer die 3 Stadtstaaten
BERLIN, BREMEN (Stadtgemeinden Bremen und Bremerhaven) und HAMBURG -
letzter Baustein der "Phase 2"-Kampagne (siehe
seed_erschliessung_amtsfrei_*.py in dieser Sitzung).

Diese 4 Gemeinden (Berlin, Bremen, Bremerhaven, Hamburg) waren die
einzigen von bundesweit 10749 Gemeinden, die nach Abschluss der
Phase-2-Kampagne fuer alle 13 Flaechenlaender mit echter Restluecke
noch ohne ERSCHLIESSUNG-Regel waren. Rechtsgrundlage identisch zu allen
anderen Gemeinden: § 127 Abs. 1 BauGB - "Die Gemeinden erheben zur
Deckung ihres anderweitig nicht gedeckten Aufwands fuer
Erschliessungsanlagen einen Erschliessungsbeitrag." (Bundesrecht,
gegen gesetze-im-internet.de verifiziert - siehe
seed_erschliessung_amtsfrei_hessen.py fuer dasselbe Zitat/dieselbe
Quelle).

Stadtstaaten sind zugleich Land UND Gemeinde (Bremen sogar zwei
Stadtgemeinden: Bremen und Bremerhaven, vgl. Art. 143 Bremische
Landesverfassung). Anders als bei Bauaufsicht/Bodendenkmalschutz
(dort bezirklich organisiert, siehe Berlin/Hamburg-Ausnahmen an
anderer Stelle in dieser Kampagne) gibt es keinen Hinweis auf eine
bezirkliche Aufspaltung der Erschliessungsbeitrags-Erhebung - diese
ist eine gesamtstaedtische Kaemmerei-/Finanzaufgabe. Verwendet daher
die zentrale Stadt-/Senatsverwaltungsadresse aus dem amtlichen
Anschriftenverzeichnis, konsistent mit dem Vorgehen bei allen anderen
Gemeinden dieser Kampagne.

4 neue MUNICIPALITY-Regeln (abzueglich etwaiger bereits bestehender
Alt-Abdeckung, die der Konfliktpruefung korrekt als Duplikat erkannt
und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Erschließungsbeiträge Stadtstaaten)"
BAUGB_URL = "https://www.gesetze-im-internet.de/bbaug/__127.html"
QUOTE = ("§ 127 Abs. 1 BauGB: 'Die Gemeinden erheben zur Deckung ihres anderweitig nicht gedeckten "
         "Aufwands für Erschließungsanlagen einen Erschließungsbeitrag nach Maßgabe der folgenden "
         "Vorschriften.'")

# ags -> (Gemeinde-Name, Bundesland)
STADTSTAATEN = {
    "02000000": ("Hamburg, Freie und Hansestadt", "Hamburg"),
    "04011000": ("Bremen, Stadt", "Bremen"),
    "04012000": ("Bremerhaven, Stadt", "Bremen"),
    "11000000": ("Berlin, Stadt", "Berlin"),
}


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.authority import Authority
    from app.services.address_directory import SATZART_GEMEINDE, load_address_directory
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    DESTATIS_PATH = r"C:\Users\admin\Downloads\20260131_Anschriften_der_Gemeinde_und_Stadtverwaltungen (1).xlsx"
    df = load_address_directory(DESTATIS_PATH)
    gem = df[df["Satzart"] == SATZART_GEMEINDE]
    ags_to_row = {row["AGS"]: row for _, row in gem.iterrows() if row["AGS"] in STADTSTAATEN}

    db = SessionLocal()
    try:
        staging = JurisdictionStagingService(db)
        batch_id = f"erschliessung-stadtstaaten-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for ags, (name, state) in STADTSTAATEN.items():
            row = ags_to_row.get(ags)
            authority_name = f"{name} - Gemeindeverwaltung (Erschließungsbeiträge)"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Erschließungsbehörde (Gemeinde, § 127 Abs. 1 BauGB)",
                    street=row["Strasse"] if row is not None else None, house_number=None,
                    postal_code=str(int(row["PLZ"])) if row is not None and row["PLZ"] == row["PLZ"] else None,
                    city=row["Ort"] if row is not None else None, state=state, phone=None,
                    email=row["Email"] if row is not None else None,
                    source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                           "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="ERSCHLIESSUNG Stadtstaaten",
                request_type_id="ERSCHLIESSUNG", state=state, ags=ags,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {QUOTE}", source_url=BAUGB_URL,
                source_license="Amtliche Rechtsgrundlage (§ 127 BauGB, Bundesrecht) + amtliches Anschriftenverzeichnis",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append(entry)
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry in staged:
            if entry.conflict_type != "NEW":
                continue
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes="Siehe source-Feld",
                resulting_verification_status="VERIFIED",
            )
            approved += 1
        db.commit()
        print(f"\n{approved} Regeln freigegeben.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
