"""
BAUAKTENAUSKUNFT und BAULASTENAUSKUNFT fuer BRANDENBURG. Nach § 57
Abs. 1 BbgBO nehmen "die Landkreise, die kreisfreien Staedte sowie die
Grossen kreisangehoerigen Staedte, denen diese Aufgabe uebertragen
ist," die Aufgaben der unteren Bauaufsichtsbehoerde wahr. § 84 Abs. 4
BbgBO: "Das Baulastenverzeichnis wird von der Bauaufsichtsbehoerde
gefuehrt" - dieselbe untere Bauaufsichtsbehoerde fuehrt damit auch das
Baulastenverzeichnis.

WICHTIGE ABGRENZUNG: "Grosse kreisangehoerige Stadt"-Status (nach § 1
Abs. 3 BbgKVerf, nur eine Einwohnerschwelle) und tatsaechliche
UEBERTRAGUNG der unteren Bauaufsichtsbehoerde sind zwei getrennte
Fragen. Bernau bei Berlin, Falkensee und Oranienburg sind zwar per
BestGkSV vom 13.12.2010 Grosse kreisangehoerige Staedte, haben aber
laut der amtlichen Adressliste des Ministeriums fuer Infrastruktur und
Landesplanung (MIL, service.brandenburg.de) die Bauaufsichtsaufgabe
NICHT uebertragen bekommen - dort bleiben die jeweiligen Landkreise
zustaendig. Nur Eberswalde und Schwedt/Oder fuehren laut dieser Liste
tatsaechlich eine eigene "uBAB" (untere Bauaufsichtsbehoerde).

Alle Zitate (§ 57, § 84 BbgBO) wurden in dieser Sitzung direkt gegen
bravors.brandenburg.de wortgleich verifiziert; die Liste der
tatsaechlich beliehenen Staedte (nur Eberswalde/Schwedt, NICHT
Bernau/Falkensee/Oranienburg) wurde direkt gegen die amtliche
MIL-Adressliste auf service.brandenburg.de verifiziert.

18 neue COUNTY-Regeln je Auskunftsart (14 Landkreise + 4 kreisfreie
Staedte) + 2 neue MUNICIPALITY-Regeln je Auskunftsart (Eberswalde und
Schwedt/Oder, nehmen automatisch Vorrang vor der COUNTY-Regel ihres
Landkreises) = 40 Regeln insgesamt (abzueglich etwaiger bereits
bestehender Alt-Abdeckung, die der Konfliktpruefung korrekt als
Duplikat erkannt und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauakten-/Baulastenauskunft Brandenburg)"
BBGBO_URL = "https://bravors.brandenburg.de/gesetze/bbgbo_2016"
MIL_URL = "https://service.brandenburg.de/service/de/adressen/weitere-verzeichnisse/verzeichnisliste/~bauaufsichtsbehoerden-untere"
QUOTE_KREIS = ("§ 57 Abs. 1 BbgBO: 'Die Landkreise, die kreisfreien Städte sowie die Großen "
               "kreisangehörigen Städte, denen diese Aufgabe übertragen ist, nehmen die Aufgaben der "
               "unteren Bauaufsichtsbehörde wahr.' § 84 Abs. 4 BbgBO: 'Das Baulastenverzeichnis wird "
               "von der Bauaufsichtsbehörde geführt.'")
QUOTE_AUSNAHME = ("Amtliche Adressliste des Ministeriums für Infrastruktur und Landesplanung (MIL, "
                   "service.brandenburg.de, Stand 24.08.2026): weist neben den 4 kreisfreien Städten "
                   "und 14 Landkreisen zusätzlich 'uBAB Eberswalde' und 'uBAB Schwedt/Oder' als eigene "
                   "untere Bauaufsichtsbehörden aus (§ 57 Abs. 1 Satz 2 BbgBO: Übertragung auf eine "
                   "Große kreisangehörige Stadt).")

# Beliehene Grosse kreisangehoerige Stadt -> AGS (aus dem amtlichen Anschriftenverzeichnis ermittelt)
AUSNAHMEN_AGS = {
    "Eberswalde": "12060052",
    "Schwedt/Oder": "12073532",
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
    bb = df[df["Land_name"] == "Brandenburg"]
    kreis_ars_index = build_ars_index(bb[bb["Satzart"] == SATZART_KREIS])
    gem_ars_index = build_ars_index(bb[bb["Satzart"] == SATZART_GEMEINDE])
    ags_to_gem_entry = {e.ags: e for e in gem_ars_index.values() if e.ags}

    db = SessionLocal()
    try:
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Brandenburg").all()
        gpk = {}
        for u in kreis_units:
            gpk.setdefault(u.ags_kreis, set()).add(u.ags_gemeinde)
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}
        kreisfreie = {k for k, gset in gpk.items() if len(gset) == 1}

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-baulasten-bb-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for request_type_id in ["BAUAKTEN", "BAULASTEN"]:
            for ags_kreis, kreis_name in kreis_names.items():
                addr = kreis_ars_index.get(str(int(ags_kreis)))
                is_kreisfrei = ags_kreis in kreisfreie
                authority_name = f"{kreis_name} - Bauaufsichtsbehörde" if is_kreisfrei \
                    else f"Landkreis {kreis_name} - Bauaufsichtsbehörde"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Landkreis/kreisfreie Stadt)",
                        street=addr.strasse if addr else None, house_number=None,
                        postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                        state="Brandenburg", phone=None, email=addr.email if addr else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Brandenburg - Kreise",
                    request_type_id=request_type_id, state="Brandenburg", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_KREIS}", source_url=BBGBO_URL,
                    source_license="Amtliche Rechtsgrundlage (BbgBO) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)

            for name, ags in AUSNAHMEN_AGS.items():
                gem_entry = ags_to_gem_entry.get(ags)
                authority_name = f"Stadt {name} - Bauaufsichtsbehörde (Große kreisangehörige Stadt, uBAB)"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Große kreisangehörige Stadt, § 57 Abs. 1 BbgBO)",
                        street=gem_entry.strasse if gem_entry else None, house_number=None,
                        postal_code=gem_entry.plz if gem_entry else None, city=gem_entry.ort if gem_entry else None,
                        state="Brandenburg", phone=None, email=gem_entry.email if gem_entry else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Brandenburg - Beliehene Große kreisangehörige Städte",
                    request_type_id=request_type_id, state="Brandenburg", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_AUSNAHME}", source_url=MIL_URL,
                    source_license="Amtliche Rechtsgrundlage (BbgBO) + amtliche MIL-Adressliste + "
                                   "amtliches Anschriftenverzeichnis",
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
