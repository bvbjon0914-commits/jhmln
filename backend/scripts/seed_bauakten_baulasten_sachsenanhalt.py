"""
BAUAKTENAUSKUNFT und BAULASTENAUSKUNFT fuer SACHSEN-ANHALT. Nach § 56
Abs. 1 BauO LSA sind Bauaufsichtsbehoerden "die Landkreise und
kreisfreien Staedte als untere Bauaufsichtsbehoerden". § 82 Abs. 4
BauO LSA: "Das Baulastenverzeichnis wird von der Bauaufsichtsbehoerde
gefuehrt" - dieselbe untere Bauaufsichtsbehoerde fuehrt damit auch das
Baulastenverzeichnis.

Zusaetzlich gibt es einen Bestandsschutz-Sonderfall: § 87 Abs. 3
BauO LSA ordnet an, dass fuer Staedte und Gemeinden, denen VOR der
Neufassung 2013 (nach dem frueheren § 63 Abs. 1 Satz 2 BauO LSA a. F.
i. V. m. Art. 6 Abs. 2 Satz 1 Drittes Investitionserleichterungsgesetz)
die Aufgaben der unteren Bauaufsichtsbehoerde ganz oder teilweise
uebertragen worden waren, diese Uebertragung fortbesteht. Das
Ministerium fuer Infrastruktur und Digitales Sachsen-Anhalt bestaetigt
auf seiner amtlichen Seite (mid.sachsen-anhalt.de) abschliessend, dass
dies die Staedte Koethen (Anhalt), Naumburg (Saale), die Hansestadt
Stendal, Weissenfels und Zeitz betrifft.

Alle Zitate (§ 56, § 82, § 87 Abs. 3 BauO LSA sowie die Staedteliste)
wurden in dieser Sitzung direkt gegen landesrecht.sachsen-anhalt.de
bzw. mid.sachsen-anhalt.de wortgleich verifiziert.

14 neue COUNTY-Regeln je Auskunftsart (11 Landkreise + 3 kreisfreie
Staedte) + 5 neue MUNICIPALITY-Regeln je Auskunftsart (die 5
Bestandsschutz-Staedte, nehmen automatisch Vorrang vor der
COUNTY-Regel ihres Landkreises) = 38 Regeln insgesamt (abzueglich
etwaiger bereits bestehender Alt-Abdeckung, die der Konfliktpruefung
korrekt als Duplikat erkannt und uebersprungen wird).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-28, Bauakten-/Baulastenauskunft Sachsen-Anhalt)"
BAUO_URL = "https://www.landesrecht.sachsen-anhalt.de/bsst/document/jlr-NNLST000040E3NN00000000119"
UEBERGANG_URL = "https://mid.sachsen-anhalt.de/bauen-und-wohnen/bauen/page/bauaufsichtsbehoerden"
QUOTE_KREIS = ("§ 56 Abs. 1 BauO LSA: 'Bauaufsichtsbehörden sind 1. die Landkreise und kreisfreien "
               "Städte als untere Bauaufsichtsbehörden ...' § 82 Abs. 4 BauO LSA: 'Das "
               "Baulastenverzeichnis wird von der Bauaufsichtsbehörde geführt.'")
QUOTE_AUSNAHME = ("Ministerium für Infrastruktur und Digitales Sachsen-Anhalt (mid.sachsen-anhalt.de): "
                   "'Die Bauordnungsämter der kreisfreien Städte, der Landkreise sowie der Städte "
                   "Köthen, Naumburg, Stendal, Weißenfels und Zeitz sind die unteren "
                   "Bauaufsichtsbehörden in Sachsen-Anhalt.' Rechtsgrundlage: § 87 Abs. 3 BauO LSA "
                   "(Bestandsschutz für vor 2013 nach § 63 Abs. 1 Satz 2 BauO LSA a. F. übertragene "
                   "Zuständigkeiten).")

# Bestandsschutz-Stadt -> AGS (aus dem amtlichen Anschriftenverzeichnis ermittelt)
AUSNAHMEN_AGS = {
    "Köthen (Anhalt)": "15082180",
    "Naumburg (Saale)": "15084355",
    "Stendal": "15090535",
    "Weißenfels": "15084550",
    "Zeitz": "15084590",
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
    lsa = df[df["Land_name"] == "Sachsen-Anhalt"]
    kreis_ars_index = build_ars_index(lsa[lsa["Satzart"] == SATZART_KREIS])
    gem_ars_index = build_ars_index(lsa[lsa["Satzart"] == SATZART_GEMEINDE])
    ags_to_gem_entry = {e.ags: e for e in gem_ars_index.values() if e.ags}

    db = SessionLocal()
    try:
        kreis_units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Sachsen-Anhalt").all()
        gpk = {}
        for u in kreis_units:
            gpk.setdefault(u.ags_kreis, set()).add(u.ags_gemeinde)
        kreis_names = {u.ags_kreis: u.county_name for u in kreis_units}
        kreisfreie = {k for k, gset in gpk.items() if len(gset) == 1}

        staging = JurisdictionStagingService(db)
        batch_id = f"bauakten-baulasten-lsa-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
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
                        state="Sachsen-Anhalt", phone=None, email=addr.email if addr else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Sachsen-Anhalt - Kreise",
                    request_type_id=request_type_id, state="Sachsen-Anhalt", ags=ags_kreis,
                    matching_level=MatchingLevel.COUNTY, priority=50,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_KREIS}", source_url=BAUO_URL,
                    source_license="Amtliche Rechtsgrundlage (BauO LSA) + amtliches Anschriftenverzeichnis",
                    source_retrieved_at=datetime.utcnow(),
                )
                staged.append(entry)

            for name, ags in AUSNAHMEN_AGS.items():
                gem_entry = ags_to_gem_entry.get(ags)
                authority_name = f"Stadt {name} - Bauaufsichtsbehörde (§ 87 Abs. 3 BauO LSA, Bestandsschutz)"
                authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()), authority_name=authority_name,
                        authority_type="Untere Bauaufsichtsbehörde (Bestandsschutz-Stadt, § 87 Abs. 3 BauO LSA)",
                        street=gem_entry.strasse if gem_entry else None, house_number=None,
                        postal_code=gem_entry.plz if gem_entry else None, city=gem_entry.ort if gem_entry else None,
                        state="Sachsen-Anhalt", phone=None, email=gem_entry.email if gem_entry else None,
                        source="Amtliches Anschriftenverzeichnis der Gemeinde- und Stadtverwaltungen "
                               "(Statistische Ämter des Bundes und der Länder, Stand 31.01.2026)",
                        active=True,
                    )
                    db.add(authority)
                    db.flush()

                entry = staging.stage_entry(
                    batch_id=batch_id, batch_label=f"{request_type_id} Sachsen-Anhalt - Bestandsschutz-Städte",
                    request_type_id=request_type_id, state="Sachsen-Anhalt", ags=ags,
                    matching_level=MatchingLevel.MUNICIPALITY, priority=40,
                    proposed_authority_id=authority.authority_id,
                    source=f"{authority_name} - {QUOTE_AUSNAHME}", source_url=UEBERGANG_URL,
                    source_license="Amtliche Rechtsgrundlage (BauO LSA) + amtliche Ministeriumsseite + "
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
