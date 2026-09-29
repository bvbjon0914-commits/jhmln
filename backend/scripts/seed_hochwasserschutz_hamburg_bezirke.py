# -*- coding: utf-8 -*-
"""
Schliesst die letzte verbleibende echte NO_MATCH-Luecke (siehe docs/
ABSCHLUSSBERICHT_DATENQUALITAET.md): HOCHWASSERSCHUTZ (Ueberschwemmungs-
gebiete) in Hamburg war bislang bewusst offen gelassen, weil angenommen
wurde, die Zustaendigkeit haenge vom konkreten, NAMENTLICH benannten
Gewaesser ab und liesse sich nicht auf Gemeinde-/Bezirksebene modellieren.

Per Web-Recherche widerlegt: die offizielle BUKEA/hamburg.de-Quelle
"Wen kann ich ansprechen? - Zustaendige Wasserbehoerden in den Hamburger
Ueberschwemmungsgebieten" (Stand 14.04.2026) listet die Zustaendigkeit
tatsaechlich schlicht PRO BEZIRKSAMT - exakt dieselben 7 Bezirksaemter, die
in dieser Datenbank bereits als "Bezirksamt X - Untere Wasserbehoerde"
existieren (bisher nur fuer WASSERSCHUTZ mit einer anderen Abgrenzung -
"nur Gewaesser II. Ordnung" - verknuepft). BUKEA selbst ist laut der Quelle
nur Rueckfrage-Kontakt, nicht die primaer zustaendige Stelle.
Quelle: https://www.hamburg.de/resource/blob/176844/b363b3eea4c04ce0ef6179a00fd9678c/d-zustaendigewasserbehoerde-uesg-data.pdf

Modelliert nach demselben Muster wie Hamburgs bestehende Bauakten-Bezirke
(matching_level=MUNICIPALITY, ags=02000000, alle 7 Bezirke gleichrangig -
Hamburg hat wie bei Bauakten KEINE Strassen-/Bezirks-Ebene zur automatischen
Auflösung, die Auswahl erfolgt wie dort ueber die bestehende manuelle
Kandidaten-Auswahl im Zuordnungs-Assistenten). Wandelt die einzelne Hamburg-
NO_MATCH-Luecke in ein aufloesbares MULTIPLE_MATCHES um (statt eines toten
Endes ohne jede Kandidaten-Behoerde).

Bewusst NICHT Teil dieser Aenderung: die dokumentierte Hafengebiet-Ausnahme
(zustaendig: Hamburg Port Authority statt Bezirksamt) - dafuer gibt es in
dieser Datenbank keine Moeglichkeit, Gebaeude im Hafengebiet von anderen zu
unterscheiden (kein "Hafengebiet"-Distrikt-Feld gepflegt), daher wuerde ein
zusaetzlicher HPA-Kandidat nur unbegruendetes Rauschen fuer alle anderen
Hamburger Gebaeude erzeugen. Als bekannte, dokumentierte Einschraenkung
vermerkt statt geraten.
"""
import os
import sys
import uuid
from datetime import date, datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal  # noqa: E402
from app.models.jurisdiction import Jurisdiction  # noqa: E402

REQUEST_TYPE_ID = "HOCHWASSERSCHUTZ"
AGS = "02000000"
PRIORITY = 40  # gleiche Prioritaet wie die bestehenden Hamburg-Bauakten-Bezirke
SOURCE = (
    "hamburg.de/BUKEA: 'Wen kann ich ansprechen? - Zustaendige Wasserbehoerden "
    "in den Hamburger Ueberschwemmungsgebieten' (Stand 14.04.2026)"
)
SOURCE_URL = (
    "https://www.hamburg.de/resource/blob/176844/b363b3eea4c04ce0ef6179a00fd9678c/"
    "d-zustaendigewasserbehoerde-uesg-data.pdf"
)
NOTES = (
    "Bezirksamt-Zustaendigkeit fuer Ueberschwemmungsgebiets-/Hochwasserschutz-"
    "Anfragen, siehe offizielle BUKEA-Quelle (source_url). Hafengebiet-Ausnahme "
    "(Hamburg Port Authority) bewusst NICHT abgebildet - siehe Skript-Docstring."
)

# (authority_id der bereits existierenden 'Bezirksamt X - Untere Wasserbehoerde')
BEZIRK_AUTHORITY_IDS = {
    "Altona": "feb47a19-98b1-464e-a053-a95cb15d7ab8",
    "Bergedorf": "e9fc0831-2f93-427f-a6a9-56db50a26c3e",
    "Eimsbüttel": "49638538-430d-4772-955b-d6633dab47dc",
    "Hamburg-Mitte": "996ed697-49c7-4bac-ad06-38d21be383aa",
    "Hamburg-Nord": "0d0d8d7b-ea99-4f93-86ec-9b9ed6e81e7e",
    "Harburg": "87f65e15-439e-4fee-9149-f49a4e9a8a98",
    "Wandsbek": "7da9d8a3-e309-41c0-8f50-54746eb61f71",
}


def main(apply_changes: bool) -> None:
    db = SessionLocal()
    try:
        existing = (
            db.query(Jurisdiction)
            .filter(
                Jurisdiction.request_type_id == REQUEST_TYPE_ID,
                Jurisdiction.ags == AGS,
                Jurisdiction.active.is_(True),
            )
            .count()
        )
        if existing:
            print(f"Bereits {existing} aktive HOCHWASSERSCHUTZ-Zeile(n) fuer Hamburg vorhanden - Abbruch.")
            return

        created = 0
        for bezirk, authority_id in BEZIRK_AUTHORITY_IDS.items():
            print(f"Anlegen: {bezirk} (authority_id={authority_id})")
            if apply_changes:
                row = Jurisdiction(
                    jurisdiction_id=str(uuid.uuid4()),
                    request_type_id=REQUEST_TYPE_ID,
                    authority_id=authority_id,
                    country="DE",
                    state="Hamburg",
                    ags=AGS,
                    municipality="Hamburg",
                    matching_level="MUNICIPALITY",
                    priority=PRIORITY,
                    valid_from=date.today(),
                    source=SOURCE,
                    source_url=SOURCE_URL,
                    verification_status="VERIFIED",
                    last_verified_at=datetime.utcnow(),
                    verified_by="Claude (Struktur-Korrektur, BUKEA-Bezirksliste)",
                    active=True,
                    notes=NOTES,
                )
                db.add(row)
            created += 1

        if apply_changes:
            db.commit()
            print(f"\nAngewendet: {created} Zeilen angelegt.")
        else:
            print(f"\n{created} Kandidaten. Dry-run only - keine Aenderung. --apply zum Anwenden.")
    finally:
        db.close()


if __name__ == "__main__":
    apply_changes = "--apply" in sys.argv
    main(apply_changes=apply_changes)
