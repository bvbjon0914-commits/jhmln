"""
BAUAKTENAUSKUNFT und BAULASTENAUSKUNFT fuer das SAARLAND. Nach § 58
Abs. 1 Satz 2 LBO Saarland (Landesbauordnung vom 18. Februar 2004)
"werden [die Aufgaben der unteren Bauaufsichtsbehoerden] von den
Landkreisen und dem Regionalverband Saarbruecken als
Auftragsangelegenheiten wahrgenommen". § 83 Abs. 4 LBO: "Die Baulasten
sind in ein Verzeichnis (Baulastenverzeichnis) einzutragen, das von der
Bauaufsichtsbehoerde gefuehrt wird" - dieselbe untere
Bauaufsichtsbehoerde fuehrt damit auch das Baulastenverzeichnis. Beide
Zitate per Live-Browser-Abruf direkt gegen recht.saarland.de
wort-fuer-wort verifiziert.

Ausnahme (§ 58 Abs. 2 LBO i.V.m. § 1 Zustaendigkeitsverordnung zur
Landesbauordnung, ZustV-LBO vom 23.06.2008): 6 Staedte mit mehr als
30.000 Einwohnern haben eine eigene untere Bauaufsichtsbehoerde: die
Landeshauptstadt Saarbruecken (deshalb NICHT durch den Regionalverband
Saarbruecken abgedeckt, sondern die Stadt selbst) sowie Homburg,
Neunkirchen, Saarlouis, St. Ingbert und Voelklingen.

6 neue COUNTY-Regeln je Auskunftsart (5 Landkreise + Regionalverband
Saarbruecken) + 6 neue MUNICIPALITY-Regeln je Auskunftsart (die 6
Ausnahme-Staedte, nehmen automatisch Vorrang vor der COUNTY-Regel ihres
Landkreises/Regionalverbands) = 24 Regeln insgesamt (abzueglich
etwaiger bereits bestehender Alt-Abdeckung, die der Konfliktpruefung
korrekt als Duplikat erkannt und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauakten-/Baulastenauskunft Saarland)"
LBO_URL = "https://recht.saarland.de/bssl/document/jlr-NNLSL00009DF9NN00000000222"
QUOTE_KREIS = ("§ 58 Abs. 1 LBO: 'Die Aufgaben der unteren Bauaufsichtsbehörden werden von den "
               "Landkreisen und dem Regionalverband Saarbrücken als Auftragsangelegenheiten "
               "wahrgenommen, soweit in diesem Gesetz oder auf Grund dieses Gesetzes nichts anderes "
               "bestimmt ist.' § 83 Abs. 4 LBO: 'Die Baulasten sind in ein Verzeichnis "
               "(Baulastenverzeichnis) einzutragen, das von der Bauaufsichtsbehörde geführt wird.'")
QUOTE_AUSNAHME = ("§ 1 ZustV-LBO: 'Die Aufgaben der unteren Bauaufsichtsbehörden werden der "
                   "Landeshauptstadt Saarbrücken und den Städten Homburg, Neunkirchen, Saarlouis, "
                   "St. Ingbert und Völklingen übertragen.'")

# Ausnahme-Stadt -> AGS (aus dem amtlichen Anschriftenverzeichnis ermittelt)
AUSNAHMEN_AGS = {
    "Saarbrücken": "10041100",
    "Homburg": "10045114",
    "Neunkirchen": "10043114",
    "Saarlouis": "10044115",
    "St. Ingbert": "10045117",
    "Völklingen": "10041519",
}


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.administrative_unit import AdministrativeUnit
    from app.models.authority import Authority
    from app.services.address_directory import SATZART_GEMEINDE, SATZART_KREIS, build_ars_index, load_address_directory
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    DESTATIS_PATH = r"C:\Users\admin\Downloads\20260131_Anschriften_der_Gemeinde_und_Stadtverwaltungen (1).xlsx"
    df = load_address_directory(DESTATIS_PATH)
    sl = df[df["Land_name"] == "Saarland"]
    kreis_ars_index = build_ars_index(sl[sl["Satzart"] == SATZART_KREIS])
    gem_ars_index = build_ars_index(sl[sl["Satzart"] == SATZART_GEMEINDE])
    ags_to_gem_entry = {e.ags: e for e in gem_ars_index.values() if e.ags}

    db = SessionLocal()
    try:
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Saarland").all()
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-baulasten-saarland-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for request_type_id in ["BAUAKTEN", "BAULASTEN"]:
            for ags_kreis, kreis_name in kreis_names.items():
                addr = kreis_ars_index.get(str(int(ags_kreis)))
                authority_name = f"{kreis_name} - Bauaufsichtsbehörde" if "Regionalverband" in kreis_name \
                    else f"Landkreis {kreis_name} - Bauaufsichtsbehörde"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Landkreis/Regionalverband)",
                        street=addr.strasse if addr else None, house_number=None,
                        postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                        state="Saarland", phone=None, email=addr.email if addr else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Saarland - Kreise",
                    request_type_id=request_type_id, state="Saarland", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_KREIS}", source_url=LBO_URL,
                    source_license="Amtliche Rechtsgrundlage (LBO Saarland) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)

            for name, ags in AUSNAHMEN_AGS.items():
                gem_entry = ags_to_gem_entry.get(ags)
                authority_name = f"Stadt {name} - Bauaufsichtsbehörde (§ 1 ZustV-LBO)"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (kreisangehörige Stadt, § 58 Abs. 2 LBO)",
                        street=gem_entry.strasse if gem_entry else None, house_number=None,
                        postal_code=gem_entry.plz if gem_entry else None, city=gem_entry.ort if gem_entry else None,
                        state="Saarland", phone=None, email=gem_entry.email if gem_entry else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Saarland - Ausnahmen",
                    request_type_id=request_type_id, state="Saarland", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_AUSNAHME}", source_url=LBO_URL,
                    source_license="Amtliche Rechtsgrundlage (ZustV-LBO) + amtliches Anschriftenverzeichnis",
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
