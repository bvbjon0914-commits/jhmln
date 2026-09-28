"""
ALTLASTEN, HOCHWASSERSCHUTZ und WASSERSCHUTZ fuer die kreisfreie Stadt
KASSEL. Eine bundesweite ags-basierte Luecken-Analyse (Abgleich gegen
alle 401 Kreise/kreisfreien Staedte je Auskunftsart) ergab, dass Kassel
- anders als die uebrigen hessischen kreisfreien Staedte Darmstadt und
Hanau, die bereits korrekt erfasst sind - fuer genau diese 3
Auskunftsarten keine Regel hat. Eine isolierte historische Import-
Luecke, keine strukturelle Besonderheit.

§ 15 Abs. 3 HAltBodSchG: "Die Aufgaben der unteren Bodenschutzbehoerde
werden dem Kreisausschuss und dem Magistrat der kreisfreien Staedte zur
Erfuellung nach Weisung uebertragen." § 64 Abs. 3 HWG: identischer
Wortlaut fuer die untere Wasserbehoerde. Beide Zitate in dieser Sitzung
direkt gegen rv.hessenrecht.hessen.de wort-fuer-wort verifiziert. Kassel
ist kreisfreie Stadt, damit selbst untere Bodenschutz- und
Wasserbehoerde (Fachbereich "Umwelt- und Gartenamt", Untere Wasser- und
Bodenschutzbehoerde).

3 neue MUNICIPALITY-Regeln (abzueglich etwaiger bereits bestehender
Alt-Abdeckung, die der Konfliktpruefung korrekt als Duplikat erkannt
und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Altlasten-/Wasserbehörden-Lücke Kassel)"
KASSEL_AGS = "06611000"

HALTBODSCHG_URL = "https://www.rv.hessenrecht.hessen.de/bshe/document/jlr-NNLHE00005215NN00000000034"
HALTBODSCHG_QUOTE = ("§ 15 Abs. 3 HAltBodSchG: 'Die Aufgaben der unteren Bodenschutzbehörde werden dem "
                      "Kreisausschuss und dem Magistrat der kreisfreien Städte zur Erfüllung nach "
                      "Weisung übertragen.'")
HWG_URL = "https://www.rv.hessenrecht.hessen.de/bshe/document/jlr-NNLHE00005144NN00000000134"
HWG_QUOTE = ("§ 64 Abs. 3 HWG: 'Die Aufgaben der unteren Wasserbehörde werden dem Kreisausschuss und "
             "dem Magistrat der kreisfreien Städte zur Erfüllung nach Weisung übertragen.'")

REQUEST_TYPES = {
    "ALTLASTEN": (HALTBODSCHG_URL, HALTBODSCHG_QUOTE),
    "HOCHWASSERSCHUTZ": (HWG_URL, HWG_QUOTE),
    "WASSERSCHUTZ": (HWG_URL, HWG_QUOTE),
}


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.authority import Authority
    from app.services.address_directory import SATZART_GEMEINDE, build_ars_index, load_address_directory
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    DESTATIS_PATH = r"C:\Users\admin\Downloads\20260131_Anschriften_der_Gemeinde_und_Stadtverwaltungen (1).xlsx"
    df = load_address_directory(DESTATIS_PATH)
    gem_ars_index = build_ars_index(df[df["Satzart"] == SATZART_GEMEINDE])
    ags_to_gem_entry = {e.ags: e for e in gem_ars_index.values() if e.ags}
    gem_entry = ags_to_gem_entry.get(KASSEL_AGS)

    db = SessionLocal()
    try:
        staging = JurisdictionStagingService(db)
        batch_id = f"altlasten-wasser-kassel-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for request_type_id, (source_url, quote) in REQUEST_TYPES.items():
            authority_type = ("Untere Bodenschutzbehörde (kreisfreie Stadt)" if request_type_id == "ALTLASTEN"
                               else "Untere Wasserbehörde (kreisfreie Stadt)")
            authority_name = f"Stadt Kassel - {authority_type.split(' (')[0]}"
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type=authority_type,
                    street=gem_entry.strasse if gem_entry else None, house_number=None,
                    postal_code=gem_entry.plz if gem_entry else None, city=gem_entry.ort if gem_entry else None,
                    state="Hessen", phone=None, email=gem_entry.email if gem_entry else None,
                    source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                           "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                    active=True,
                )
                db.add(authority)
                db.flush()

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="Altlasten/Wasserbehörden-Lücke Kassel",
                request_type_id=request_type_id, state="Hessen", ags=KASSEL_AGS,
                matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {quote}", source_url=source_url,
                source_license="Amtliche Rechtsgrundlage (HAltBodSchG/HWG) + amtliches Anschriftenverzeichnis",
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
