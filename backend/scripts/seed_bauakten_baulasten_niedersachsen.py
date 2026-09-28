"""
BAUAKTENAUSKUNFT und BAULASTENAUSKUNFT fuer NIEDERSACHSEN. Nach § 57
Abs. 1 NBauO (Niedersaechsische Bauordnung) "nehmen die Landkreise, die
kreisfreien Staedte und die grossen selbstaendigen Staedte die Aufgaben
der unteren Bauaufsichtsbehoerde wahr" - anders als in den meisten
anderen Laendern ergibt sich die Sonderzustaendigkeit der grossen
selbstaendigen Staedte hier DIREKT aus der Bauordnung selbst, nicht
erst ueber einen allgemeinen Kommunalverfassungs-Verweis. § 81 Abs. 4
NBauO: "Das Baulastenverzeichnis wird von der Bauaufsichtsbehoerde
gefuehrt" - dieselbe untere Bauaufsichtsbehoerde fuehrt damit auch das
Baulastenverzeichnis.

Die 7 "grossen selbstaendigen Staedte" sind nach § 14 Abs. 5 NKomVG
abschliessend benannt: Celle, Cuxhaven, Goslar, Hameln, Hildesheim,
Lingen (Ems) und die Hansestadt Lueneburg - dieselben 7 Staedte, die
bereits bei BODENDENKMALSCHUTZ Niedersachsen in dieser Sitzung als
eigene untere Denkmalschutzbehoerde identifiziert wurden (dort eine
andere Rechtsgrundlage, § 57 NDSchG, zufaellig gleiche Paragraphen-
nummer wie hier bei der Bauordnung).

WICHTIGE EINSCHRAENKUNG (bewusst NICHT umgesetzt, um nicht zu raten):
§ 57 Abs. 2 NBauO erlaubt zusaetzlich, dass EINZELNE weitere
kreisangehoerige Gemeinden ab 30.000 Einwohnern per Antrag/Uebertragung
ebenfalls eigene untere Bauaufsichtsbehoerde werden koennen (mit
Bestandsschutz fuer Faelle vor dem 1.11.2012). Eine offizielle
Ministeriumsseite (Nds. Ministerium fuer Umwelt, Energie, Bauen und
Klimaschutz) bestaetigt, dass es "eine Reihe weiterer Staedte" mit
dieser Sonderzustaendigkeit tatsaechlich gibt, nennt aber keine
vollstaendige Namensliste - eine solche Liste konnte in dieser Sitzung
nicht amtlich verifiziert werden. Fuer diese (unbekannte Anzahl)
weiterer Staedte wuerde die COUNTY-Regel ihres Landkreises daher
faelschlich zutreffen; das ist eine bekannte, dokumentierte
Einschraenkung dieses Skripts, keine stille Luecke.

45 neue COUNTY-Regeln je Auskunftsart (37 Landkreise + 8 kreisfreie
Staedte) + 7 neue MUNICIPALITY-Regeln je Auskunftsart (die 7 grossen
selbstaendigen Staedte, nehmen automatisch Vorrang vor der COUNTY-Regel
ihres Landkreises) = 104 Regeln insgesamt (abzueglich etwaiger bereits
bestehender Alt-Abdeckung, die der Konfliktpruefung korrekt als
Duplikat erkannt und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauakten-/Baulastenauskunft Niedersachsen)"
NBAUO_URL = "https://voris.wolterskluwer-online.de/browse/document/42aa8261-a922-3983-8ed5-e590d2c77cea"
QUOTE_KREIS = ("§ 57 Abs. 1 NBauO: 'Die Landkreise, die kreisfreien Städte und die großen "
               "selbständigen Städte nehmen die Aufgaben der unteren Bauaufsichtsbehörde wahr.' "
               "§ 81 Abs. 4 NBauO: 'Das Baulastenverzeichnis wird von der Bauaufsichtsbehörde "
               "geführt.'")
QUOTE_AUSNAHME = ("§ 14 Abs. 5 NKomVG: 'Große selbständige Städte sind: Celle, Cuxhaven, Goslar, "
                   "Hameln, Hildesheim und Lingen (Ems) sowie die Hansestadt Lüneburg.' § 57 Abs. 1 "
                   "NBauO nennt diese Städte direkt und abschließend als untere "
                   "Bauaufsichtsbehörde neben Landkreisen und kreisfreien Städten.")

# Grosse selbstaendige Stadt -> AGS (aus dem amtlichen Anschriftenverzeichnis ermittelt)
AUSNAHMEN_AGS = {
    "Celle": "03351006",
    "Cuxhaven": "03352011",
    "Goslar": "03153017",
    "Hameln": "03252006",
    "Hildesheim": "03254021",
    "Lingen (Ems)": "03454032",
    "Lüneburg": "03355022",
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
    ni = df[df["Land_name"] == "Niedersachsen"]
    kreis_ars_index = build_ars_index(ni[ni["Satzart"] == SATZART_KREIS])
    gem_ars_index = build_ars_index(ni[ni["Satzart"] == SATZART_GEMEINDE])
    ags_to_gem_entry = {e.ags: e for e in gem_ars_index.values() if e.ags}

    db = SessionLocal()
    try:
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Niedersachsen").all()
        gpk = {}
        for u in kreis_units:
            gpk.setdefault(u.ags_kreis, set()).add(u.ags_gemeinde)
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}
        kreisfreie = {k for k, gset in gpk.items() if len(gset) == 1}

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-baulasten-ni-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        for request_type_id in ["BAUAKTEN", "BAULASTEN"]:
            for ags_kreis, kreis_name in kreis_names.items():
                addr = kreis_ars_index.get(str(int(ags_kreis)))
                is_kreisfrei = ags_kreis in kreisfreie or "Region" in kreis_name
                authority_name = f"{kreis_name} - Bauaufsichtsbehörde" if is_kreisfrei \
                    else f"Landkreis {kreis_name} - Bauaufsichtsbehörde"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Landkreis/kreisfreie Stadt)",
                        street=addr.strasse if addr else None, house_number=None,
                        postal_code=addr.plz if addr else None, city=addr.ort if addr else None,
                        state="Niedersachsen", phone=None, email=addr.email if addr else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Niedersachsen - Kreise",
                    request_type_id=request_type_id, state="Niedersachsen", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_KREIS}", source_url=NBAUO_URL,
                    source_license="Amtliche Rechtsgrundlage (NBauO) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)

            for name, ags in AUSNAHMEN_AGS.items():
                gem_entry = ags_to_gem_entry.get(ags)
                authority_name = f"Stadt {name} - Bauaufsichtsbehörde (Große selbständige Stadt)"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Große selbständige Stadt, § 57 Abs. 1 NBauO)",
                        street=gem_entry.strasse if gem_entry else None, house_number=None,
                        postal_code=gem_entry.plz if gem_entry else None, city=gem_entry.ort if gem_entry else None,
                        state="Niedersachsen", phone=None, email=gem_entry.email if gem_entry else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Niedersachsen - Große selbständige Städte",
                    request_type_id=request_type_id, state="Niedersachsen", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_AUSNAHME}", source_url=NBAUO_URL,
                    source_license="Amtliche Rechtsgrundlage (NKomVG/NBauO) + amtliches Anschriftenverzeichnis",
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
