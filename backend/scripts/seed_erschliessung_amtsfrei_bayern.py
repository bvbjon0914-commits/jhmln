"""
ERSCHLIESSUNGSBEITRAEGE (§ 127 ff. BauGB) fuer BAYERN - "Phase 2":
saemtliche Gemeinden, die NICHT Teil einer Verwaltungsgemeinschaft
sind, der die Erschliessungsbeitrags-Erhebung fuer sie uebernimmt,
sind selbst die zustaendige Erschliessungsbehoerde.

Die urspruengliche Erschliessungsbeitraege-Kampagne fuer Bayern (siehe
docs/ABSCHLUSSBERICHT_DATENQUALITAET.md #19.5) deckte 982 von 2056
bayerischen Gemeinden ueber 311 Verwaltungsgemeinschaften (VGem) ab.
Die verbleibenden 1074 Gemeinden sind "Einheitsgemeinden" bzw. grosse
kreisangehoerige/kreisfreie Staedte, die keiner VGem angehoeren und
sich daher selbst verwalten (Art. 4 Gemeindeordnung Bayern) - fuer sie
gilt: jede Gemeinde ist ihre eigene Erschliessungsbehoerde.

Rechtsgrundlage ist BUNDESRECHT und damit fuer alle 16 Laender
identisch: § 127 Abs. 1 BauGB - "Die Gemeinden erheben zur Deckung
ihres anderweitig nicht gedeckten Aufwands fuer Erschliessungsanlagen
einen Erschliessungsbeitrag." Wortlaut gegen die amtliche Quelle
gesetze-im-internet.de (Bundesministerium der Justiz) wort-fuer-wort
verifiziert (siehe bereits seed_erschliessung_amtsfrei_hessen.py in
dieser Sitzung fuer dieselbe Quelle/dasselbe Zitat).

Datenquelle: dasselbe amtliche, bundesweite Anschriftenverzeichnis
"Anschriften der Gemeinde- und Stadtverwaltungen" (Statistische Aemter
des Bundes und der Laender, Stand 31.01.2026), Satzart 60 (Gemeinde).

Bis zu 1074 neue MUNICIPALITY-Regeln (eine je bayerischer Einheits-
gemeinde, ags = die jeweilige Gemeinde-AGS, abzueglich etwaiger
bereits bestehender Alt-Abdeckung, die der Konfliktpruefung korrekt
als Duplikat erkannt und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Erschließungsbeiträge Bayern - eigenständige Gemeinden)"
BAUGB_URL = "https://www.gesetze-im-internet.de/bbaug/__127.html"
QUOTE = ("§ 127 Abs. 1 BauGB: 'Die Gemeinden erheben zur Deckung ihres anderweitig nicht gedeckten "
         "Aufwands für Erschließungsanlagen einen Erschließungsbeitrag nach Maßgabe der folgenden "
         "Vorschriften.'")
STATE = "Bayern"


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.authority import Authority
    from app.models.jurisdiction import Jurisdiction
    from app.services.address_directory import SATZART_GEMEINDE, load_address_directory
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    DESTATIS_PATH = r"C:\Users\admin\Downloads\20260131_Anschriften_der_Gemeinde_und_Stadtverwaltungen (1).xlsx"
    df = load_address_directory(DESTATIS_PATH)
    gem = df[(df["Land_name"] == STATE) & (df["Satzart"] == SATZART_GEMEINDE)]

    db = SessionLocal()
    try:
        existing = {
            row[0] for row in db.query(Jurisdiction.ags).filter(
                Jurisdiction.active.is_(True),
                Jurisdiction.request_type_id == "ERSCHLIESSUNG",
                Jurisdiction.matching_level == MatchingLevel.MUNICIPALITY,
            ).all()
        }
        print(f"{len(gem)} Gemeinden in Bayern laut Anschriftenverzeichnis, {len(existing)} bundesweit bereits abgedeckt.")

        staging = JurisdictionStagingService(db)
        batch_id = f"erschliessung-amtsfrei-bayern-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []
        skipped_already_covered = 0

        for _, row in gem.iterrows():
            ags = row["AGS"]
            if not ags:
                continue
            if ags in existing:
                skipped_already_covered += 1
                continue
            name = row["Gemeinde"]
            authority_name = f"{name} - Gemeindeverwaltung (Erschließungsbeiträge)"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Erschließungsbehörde (Gemeinde, § 127 Abs. 1 BauGB)",
                    street=row["Strasse"], house_number=None,
                    postal_code=str(int(row["PLZ"])) if row["PLZ"] == row["PLZ"] else None,
                    city=row["Ort"], state=STATE, phone=None, email=row["Email"],
                    source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                           "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="ERSCHLIESSUNG Bayern - eigenständige Gemeinden",
                request_type_id="ERSCHLIESSUNG", state=STATE, ags=ags,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {QUOTE}", source_url=BAUGB_URL,
                source_license="Amtliche Rechtsgrundlage (§ 127 BauGB, Bundesrecht) + amtliches Anschriftenverzeichnis",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append(entry)
        db.commit()

        print(f"\n{skipped_already_covered} Gemeinden bereits abgedeckt (übersprungen, kein Staging-Eintrag).")
        print(f"{len(staged)} Einträge gestaged (Batch {batch_id}).")
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
