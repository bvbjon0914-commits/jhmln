"""
BAUAKTENAUSKUNFT und BAULASTENAUSKUNFT fuer SACHSEN. Nach § 57 Abs. 1
SaechsBO (Saechsische Bauordnung) sind "die Landkreise und Kreisfreien
Staedte" untere Bauaufsichtsbehoerden. § 83 Abs. 4 SaechsBO: "Das
Baulastenverzeichnis wird von der Bauaufsichtsbehoerde gefuehrt" -
dieselbe untere Bauaufsichtsbehoerde fuehrt damit auch das
Baulastenverzeichnis (§ 57 Abs. 1 Satz 2: die untere Bauaufsichtsbehoerde
ist fuer den Gesetzesvollzug zustaendig, soweit nichts anderes bestimmt
ist). Beide Zitate per Live-Browser-Abruf direkt gegen revosax.sachsen.de
wort-fuer-wort verifiziert.

Ausnahme (§ 57 Abs. 2 SaechsBO i.V.m. § 2 Abs. 2 SaechsKrGebNG): die 4
im Zuge der Kreisgebietsreform 2008 "eingekreisten" ehemals kreisfreien
Staedte behalten ihre eigene untere Bauaufsichtsbehoerde (und damit auch
das Baulastenverzeichnis), solange sie nicht ausdruecklich verzichten:
Goerlitz (Landkreis Goerlitz), Hoyerswerda (Landkreis Bautzen), Plauen
(Vogtlandkreis), Zwickau (Landkreis Zwickau).

13 neue COUNTY-Regeln je Auskunftsart (eine je Landkreis/kreisfreier
Stadt) + 4 neue MUNICIPALITY-Regeln je Auskunftsart (die 4 eingekreisten
Staedte, nehmen automatisch Vorrang vor der COUNTY-Regel ihres
Landkreises) = 34 Regeln insgesamt.
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauakten-/Baulastenauskunft Sachsen)"
SAECHSBO_URL = "https://www.revosax.sachsen.de/vorschrift/1779-SaechsBO"
QUOTE_KREIS = ("§ 57 Abs. 1 SächsBO: 'Bauaufsichtsbehörden sind 1. die Landkreise und Kreisfreien "
               "Städte als untere Bauaufsichtsbehörden ... Für den Vollzug dieses Gesetzes ... ist "
               "die untere Bauaufsichtsbehörde zuständig, soweit nichts anderes bestimmt ist.' "
               "§ 83 Abs. 4 SächsBO: 'Das Baulastenverzeichnis wird von der Bauaufsichtsbehörde "
               "geführt.'")
QUOTE_AUSNAHME = ("§ 57 Abs. 2 SächsBO: 'Untere Bauaufsichtsbehörden sind auch die nach § 2 Absatz 2 "
                   "des Sächsischen Kreisgebietsneugliederungsgesetzes ... eingekreisten Städte.' "
                   "§ 2 Abs. 2 SächsKrGebNG: 'Die Kreisfreiheit der Städte Görlitz, Hoyerswerda, "
                   "Plauen und Zwickau wird aufgehoben (Einkreisung).'")

# Ausnahme-Stadt -> AGS (aus dem amtlichen Anschriftenverzeichnis ermittelt)
AUSNAHMEN_AGS = {
    "Görlitz": "14626110",
    "Hoyerswerda": "14625240",
    "Plauen": "14523320",
    "Zwickau": "14524330",
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
    sn = df[df["Land_name"] == "Sachsen"]
    kreis_ars_index = build_ars_index(sn[sn["Satzart"] == SATZART_KREIS])
    gem_ars_index = build_ars_index(sn[sn["Satzart"] == SATZART_GEMEINDE])
    ags_to_gem_entry = {e.ags: e for e in gem_ars_index.values() if e.ags}

    db = SessionLocal()
    try:
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Sachsen").all()
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-baulasten-sachsen-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for request_type_id, priority_offset in [("BAUAKTEN", 0), ("BAULASTEN", 0)]:
            for ags_kreis, kreis_name in kreis_names.items():
                addr = kreis_ars_index.get(str(int(ags_kreis)))
                authority_name = f"Landkreis {kreis_name} - Bauaufsichtsbehörde" if "Stadt" not in kreis_name \
                    else f"{kreis_name} - Bauaufsichtsbehörde"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Landkreis/kreisfreie Stadt)",
                        street=addr.strasse if addr else None, house_number=None,
                        postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                        state="Sachsen", phone=None, email=addr.email if addr else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Sachsen - Kreise",
                    request_type_id=request_type_id, state="Sachsen", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_KREIS}", source_url=SAECHSBO_URL,
                    source_license="Amtliche Rechtsgrundlage (SächsBO) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)

            for name, ags in AUSNAHMEN_AGS.items():
                gem_entry = ags_to_gem_entry.get(ags)
                authority_name = f"Stadt {name} - Bauaufsichtsbehörde (eingekreiste Stadt)"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (eingekreiste Stadt, § 57 Abs. 2 SächsBO)",
                        street=gem_entry.strasse if gem_entry else None, house_number=None,
                        postal_code=gem_entry.plz if gem_entry else None, city=gem_entry.ort if gem_entry else None,
                        state="Sachsen", phone=None, email=gem_entry.email if gem_entry else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Sachsen - Ausnahmen",
                    request_type_id=request_type_id, state="Sachsen", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_AUSNAHME}", source_url=SAECHSBO_URL,
                    source_license="Amtliche Rechtsgrundlage (SächsBO) + amtliches Anschriftenverzeichnis",
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
