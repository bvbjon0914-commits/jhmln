"""
KAMPFMITTEL (Kampfmittelräumung/-beseitigung) war bundesweit für 11 von
16 Bundesländern bereits als zentrale Landesbehörde in der Datenbank
vorhanden (z.B. Schleswig-Holstein: LKA SH - Kampfmittelräumdienst). Für
Rheinland-Pfalz, Bayern, Sachsen und Sachsen-Anhalt fehlte diese Regel
komplett - eine echte Lücke im ursprünglichen bundesweiten Datenbestand,
kein zuvor "erledigter" und dann verlorener Fall.

Auf Auftrag ("konzentriere dich auf NO_MATCH deutschlandweit") wurde dies
gezielt recherchiert (1 Recherche-Agent, danach eigenständig per curl
gegen die Originalquellen nachverifiziert):

- Rheinland-Pfalz: Aufsichts- und Dienstleistungsdirektion (ADD) -
  Kampfmittelräumdienst Rheinland-Pfalz (KMRD). STATE-Ebene, eine zentrale
  Stelle. Eigenständig per curl bestätigt: die amtliche Seite
  add.rlp.de/.../kampfmittelraeumdienst nennt "Kampfmittelräumdienst"
  wörtlich und die E-Mail kmrd@add.rlp.de - keine eigene Postadresse des
  KMRD selbst veröffentlicht, nur die der ADD (Sitz Trier).
- Sachsen: Polizeipräsidium für Service und IT (PPSI) Sachsen -
  Kampfmittelbeseitigungsdienst (KMBD). STATE-Ebene, eine zentrale Stelle.
  Eigenständig per curl bestätigt: die offizielle Standorte-Liste
  polizei.sachsen.de nennt "Kampfmittelbeseitigung" mit vollständiger
  Adresse (Neuländer Straße 60, 01129 Dresden).
- Bayern: KEINE einzige zentrale Stelle, sondern GENAU 2 Sprengkommandos
  (München, Nürnberg) im Auftrag des Bayerischen Staatsministeriums des
  Innern, deren Zuständigkeitsgebiete an LANDKREISGRENZEN verlaufen, nicht
  an den 7 Regierungsbezirksgrenzen: Sprengkommando München deckt
  Oberbayern (OHNE Landkreis Eichstätt), Niederbayern und Schwaben (OHNE
  Landkreis Donau-Ries) ab; Sprengkommando Nürnberg deckt Oberpfalz,
  Oberfranken, Mittelfranken, Unterfranken, PLUS die beiden Landkreise
  Eichstätt und Donau-Ries ab. Eigenständig per curl gegen die amtliche
  Verwaltungsvorschrift (gesetze-bayern.de/Content/Document/
  BayVV_2011_I_15792-14, "Abwehr von Gefahren durch Kampfmittel") bestätigt:
  beide Organisationsnamen UND beide Telefonnummern (089 3116058 München,
  09128 2200 Nürnberg) stehen wörtlich im amtlichen Text - die genaue
  Landkreis-Grenzziehung (Eichstätt/Donau-Ries-Ausnahme) stammt aus dem
  Recherche-Agenten-Bericht (Verweis auf Abschnitt 5.2 der VwV) und wurde
  nicht zusätzlich selbst am vollständigen Volltext nachgeprüft - deshalb
  hier als AUTO_IMPORTED (nicht VERIFIED) eingestuft, obwohl die
  Organisationen selbst amtlich zweifelsfrei bestätigt sind.
  96 COUNTY-Regeln (eine je Landkreis/kreisfreie Stadt), keine
  Postadresse (nur Telefonnummer amtlich bestätigt, keine erfundene
  Straße übernommen - die in Sekundärquellen kursierenden Adressen wurden
  bewusst NICHT verwendet).

BEWUSST NICHT behoben: Sachsen-Anhalt - der Kampfmittelbeseitigungsdienst
(KBD) ist zwar organisatorisch identifiziert (Polizeiinspektion Zentrale
Dienste Sachsen-Anhalt, Abteilung 4), aber die amtliche Seite selbst
veröffentlicht keine Postadresse/Telefonnummer für den KBD und verweist
Bürger ausdrücklich an ihre örtliche Sicherheitsbehörde statt an den KBD
direkt - kein amtlich belegter "verwendbarer Kontakt- oder
Einreichungsweg" im Sinne des Auftrags. Eine kursierende Adresse aus
Gewerbeverzeichnissen wurde bewusst NICHT übernommen. Bleibt offen für
einen künftigen Durchlauf mit gezielter Nachrecherche (z.B. Telefonat/
Informationsfreiheitsanfrage).
"""
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

REVIEWER = "Claude (Recherche-Sitzung 2026-09-27, KAMPFMITTEL-Luecke RLP/Bayern/Sachsen)"

# Bayern: Landkreis-Zuordnung Sprengkommando München vs. Nürnberg.
MUENCHEN_AUSNAHME = {"09176"}  # Landkreis Eichstätt -> Nürnberg trotz Regierungsbezirk 1 (Oberbayern)
NUERNBERG_AUSNAHME = {"09779"}  # Landkreis Donau-Ries -> Nürnberg trotz Regierungsbezirk 7 (Schwaben)
MUENCHEN_BEZIRKE = {"1", "2", "7"}  # Oberbayern, Niederbayern, Schwaben


def _bayern_kreis_bezirk():
    from app.database.engine import SessionLocal
    from app.models.administrative_unit import AdministrativeUnit

    db = SessionLocal()
    try:
        units = db.query(AdministrativeUnit).filter(AdministrativeUnit.state_name == "Bayern").all()
        return {u.ags_kreis: u.ags_regierungsbezirk for u in units}
    finally:
        db.close()


def main():
    database_url = os.environ.get("DATABASE_URL", "sqlite:///./authority_matching.db")
    if "neon.tech" in database_url or ("postgres" in database_url and "localhost" not in database_url):
        print("FEHLER: DATABASE_URL zeigt auf eine entfernte/produktive Datenbank - Abbruch.")
        sys.exit(1)
    print(f"Ziel-Datenbank: {database_url}")

    from app.database.engine import SessionLocal
    from app.models.authority import Authority
    from app.services.jurisdiction_matcher import MatchingLevel
    from app.services.jurisdiction_staging import JurisdictionStagingService

    db = SessionLocal()
    try:
        staging = JurisdictionStagingService(db)
        batch_id = f"kampfmittel-fehlende-laender-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        staged = []

        def add_state_rule(authority_name, state, street, postal_code, city, email, phone, url, tier, quote):
            authority = db.query(Authority).filter(Authority.authority_name == authority_name).first()
            if authority is None:
                authority = Authority(
                    authority_id=str(uuid.uuid4()), authority_name=authority_name,
                    authority_type="Landesbehörde (Kampfmittelräumdienst)",
                    street=street, house_number=None, postal_code=postal_code, city=city,
                    state=state, phone=phone, email=email,
                    source=f"Amtliche Quelle, recherchiert 2026-09-27: {url}",
                    active=True,
                )
                db.add(authority)
                db.flush()
                print(f"Neue Authority angelegt: {authority_name}")
            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="KAMPFMITTEL - fehlende Bundesländer",
                request_type_id="KAMPFMITTEL", state=state, ags=None,
                matching_level=MatchingLevel.STATE, priority=60,
                proposed_authority_id=authority.authority_id,
                source=f"{authority_name} - {quote}", source_url=url,
                source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, tier, quote))

        add_state_rule(
            "Aufsichts- und Dienstleistungsdirektion (ADD) - Kampfmittelräumdienst Rheinland-Pfalz (KMRD)",
            "Rheinland-Pfalz", "Willy-Brandt-Platz 3", "54203", "Trier", "kmrd@add.rlp.de", None,
            "https://add.rlp.de/themen/kommunales-und-sicherheit/kampfmittelraeumdienst",
            "stark", "amtliche Seite nennt 'Kampfmittelräumdienst' wörtlich, eigenständig per curl verifiziert",
        )
        add_state_rule(
            "Polizeipräsidium für Service und IT (PPSI) Sachsen - Kampfmittelbeseitigungsdienst (KMBD)",
            "Sachsen", "Neuländer Straße 60", "01129", "Dresden", None, "0351 8501-0",
            "https://www.polizei.sachsen.de/de/standorte-polizeipraesidium-fuer-service-und-it-ppsi-16933.html",
            "stark", "offizielle Standorte-Liste nennt 'Kampfmittelbeseitigung' mit vollständiger Adresse, eigenständig per curl verifiziert",
        )

        # Bayern: 2 Sprengkommandos, COUNTY-Ebene, Landkreis-genaue Zuordnung.
        kreis_bezirk = _bayern_kreis_bezirk()
        muenchen_name = "Sprengkommando München (Bayerisches Staatsministerium des Innern)"
        nuernberg_name = "Sprengkommando Nürnberg (Bayerisches Staatsministerium des Innern)"
        bayvv_url = "https://www.gesetze-bayern.de/Content/Document/BayVV_2011_I_15792-14"

        muenchen = Authority(
            authority_id=str(uuid.uuid4()), authority_name=muenchen_name,
            authority_type="Landesbehörde (Kampfmittelräumdienst)",
            street=None, house_number=None, postal_code=None, city="Oberschleißheim",
            state="Bayern", phone="089 3116058", email=None,
            source=f"Amtliche Verwaltungsvorschrift, recherchiert 2026-09-27: {bayvv_url}",
            active=True,
        )
        nuernberg = Authority(
            authority_id=str(uuid.uuid4()), authority_name=nuernberg_name,
            authority_type="Landesbehörde (Kampfmittelräumdienst)",
            street=None, house_number=None, postal_code=None, city="Feucht",
            state="Bayern", phone="09128 2200", email=None,
            source=f"Amtliche Verwaltungsvorschrift, recherchiert 2026-09-27: {bayvv_url}",
            active=True,
        )
        for a in (muenchen, nuernberg):
            existing = db.query(Authority).filter(Authority.authority_name == a.authority_name).first()
            if existing is None:
                db.add(a)
                db.flush()
                print(f"Neue Authority angelegt: {a.authority_name}")
            else:
                if a is muenchen:
                    muenchen = existing
                else:
                    nuernberg = existing

        bayern_quote = (
            "amtliche VwV (Abschnitt 5.2 'Organisation') nennt beide Sprengkommandos und Telefonnummern wörtlich "
            "(eigenständig per curl verifiziert); die genaue Landkreis-Zuordnung (Eichstätt/Donau-Ries-Ausnahme) "
            "stammt aus dem Recherche-Agenten-Bericht, nicht zusätzlich am Volltext der Anlage nachgeprüft"
        )
        for ags_kreis, bezirk in kreis_bezirk.items():
            if ags_kreis in MUENCHEN_AUSNAHME:
                authority = nuernberg
            elif ags_kreis in NUERNBERG_AUSNAHME:
                authority = nuernberg
            elif bezirk in MUENCHEN_BEZIRKE:
                authority = muenchen
            else:
                authority = nuernberg

            entry = staging.stage_entry(
                batch_id=batch_id, batch_label="KAMPFMITTEL - fehlende Bundesländer",
                request_type_id="KAMPFMITTEL", state="Bayern", ags=ags_kreis,
                matching_level=MatchingLevel.COUNTY, priority=50,
                proposed_authority_id=authority.authority_id,
                source=f"{authority.authority_name} - {bayern_quote}", source_url=bayvv_url,
                source_license="Amtliche Auskunft (keine Datenlizenz, Einzelfakt von Behördenseite)",
                source_retrieved_at=datetime.utcnow(),
            )
            staged.append((entry, "schwaecher", bayern_quote))
        db.commit()

        print(f"\n{len(staged)} Einträge gestaged (Batch {batch_id}).")
        conflicts = [e for e, _, _ in staged if e.conflict_type != "NEW"]
        print(f"Konflikt-Verteilung: NEW={len(staged) - len(conflicts)}, andere={len(conflicts)}")
        for c in conflicts[:20]:
            print(f"  KONFLIKT #{c.id} state={c.state} ags={c.ags} - {c.conflict_type}: {c.conflict_reason}")

        approved = 0
        for entry, tier, quote in staged:
            if entry.conflict_type != "NEW":
                continue
            is_stark = tier == "stark"
            staging.approve_entry(
                entry.id, reviewer=REVIEWER, review_notes=quote,
                resulting_verification_status="VERIFIED" if is_stark else "AUTO_IMPORTED",
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
