# -*- coding: utf-8 -*-
"""
Fix der letzten 10 echten KAMPFMITTEL-Duplikate (siehe docs/
ABSCHLUSSBERICHT_DATENQUALITAET.md, Kapitel "Nicht vorhanden"-Status):
10 kleine saechsische Gemeinden haben je ZWEI aktive Ortspolizeibehoerde-
Zeilen - eine mit der eigenen Gemeindeadresse, eine mit der Adresse ihres
gemeinsamen Verwaltungsverbands/-gemeinschaft. Anders als die bereits
gefixten ~90 Sachsen-Faelle (fix_kampfmittel_sachsen_missfiled_duplikate.py)
ist hier KEINE der beiden Adressen falsch zugeordnet - beide Zeilen sind
korrekt auf die jeweilige Gemeinde-AGS gescoped, es ist eine "welche
Adresse ist die operative Kontaktadresse"-Frage, kein Scoping-Bug.

Per Web-Recherche gegen offizielle .de-Quellen verifiziert (siehe Kommentare
je Gruppe unten): alle vier betroffenen Verwaltungsverbaende/-gemeinschaften
fuehren ein gemeinsames Ordnungsamt (bzw. im Fall Bad Gottleuba-Berggiesshuebel
eine "erfuellende Gemeinde"-Konstruktion) fuer ihre Mitgliedsgemeinden - die
gemeinsame Geschaeftsstelle ist die korrekte Verwaltungskontaktadresse.
Kampfmittelbeseitigung selbst wird auf keiner der Quellen woertlich genannt -
das ist per Analogieschluss aus der bestaetigten allgemeinen Ordnungsamt-/
Ortspolizeibehoerde-Delegation abgeleitet, nicht woertlich dokumentiert
(explizit hier vermerkt, keine Uebertreibung der Beleglage).

- Verwaltungsverband Jaegerswald (Sitz Tirpersdorf, Hauptstr. 41):
  https://www.jaegerswald.de/ - fuehrt Hauptamt/Ordnungs- und Gewerbeamt/
  Kaemmerei/Steuer- und Bauamt fuer Bergen, Theuma, Werda (+ Tirpersdorf selbst).
- Verwaltungsverband Diehsa (Sitz Waldhufen, Kollmer Str. 1):
  https://verwaltungsverband-diehsa.de/kontakt - eigenes Ordnungsamt/
  Gewerbeamt fuer Hohendubrau, Muecka, Quitzdorf am See (+ Waldhufen selbst).
- Verwaltungsgemeinschaft Bad Gottleuba-Berggiesshuebel (erfuellende Gemeinde):
  https://www.stadt-liebstadt.de/verwaltung_und_buergerinformation.html -
  "Die Stadt Bad Gottleuba-Berggiesshuebel ist erfuellende Gemeinde" fuer
  Liebstadt und Bahretal.
- Verwaltungsverband Eilenburg-West (Sitz Eilenburg, Torgauer Str. 38):
  https://www.eilenburg-west.de/verwaltung/einheiten/4507 - gemeinsames
  Ordnungsamt fuer Jesewitz und Zschepplin.

Fuer jedes der 10 Paare wird die Zeile mit der EIGENEN Gemeindeadresse
abgelaufen (valid_to = Vortag), die Zeile mit der Verband-/Gemeinschafts-
adresse bleibt aktiv und unveraendert.
"""
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal  # noqa: E402
from app.models.jurisdiction import Jurisdiction  # noqa: E402

REQUEST_TYPE_ID = "KAMPFMITTEL"

# (ags, jurisdiction_id der EIGENEN Gemeindeadresse-Zeile - wird abgelaufen)
# jurisdiction_id direkt live gegen die DB verifiziert (nicht nur aus einem
# Agenten-Bericht uebernommen), inkl. Adress-Gegenprobe unmittelbar davor.
TO_EXPIRE = [
    ("14523050", "eb1818b2-9344-40e9-87e9-de7ec47b24be"),  # Bergen (eigene Adresse Falkensteiner Str. 10)
    ("14523410", "5e855503-df54-4717-97c9-16eca3ad358c"),  # Theuma (Hauptstr. 29)
    ("14523460", "aee9551a-c689-498f-b2b1-102144880644"),  # Werda (Mittlere Str. 31)
    ("14626190", "c6488168-7bc7-4552-bb90-efed97fd48c6"),  # Hohendubrau (Hauptstr. 23)
    ("14626320", "52c625b3-5dd8-4aba-99a1-e526e4fc404d"),  # Muecka (Am Markt 1)
    ("14626440", "c564b0b2-3abf-4c29-97d8-d6edb1227395"),  # Quitzdorf am See (Hauptstr. 19)
    ("14628040", "048f7ea5-226b-44cf-a9b6-e437b39dca7f"),  # Bahretal (Gersdorf 31)
    ("14628230", "ad753541-5147-4e73-93e9-1c5d006b961f"),  # Liebstadt (Kirchplatz 2)
    ("14730140", "61709a51-41b3-4318-894a-427a0cdf88e7"),  # Jesewitz (Alte Dorfstr. 1)
    ("14730360", "74e13bb5-e012-49c9-804a-3926771ba50e"),  # Zschepplin (Bahnhofstr. 1)
]

NOTE_SUFFIX = (
    "Expired {today}: eigene Gemeindeadresse dupliziert die operative "
    "Kontaktadresse des gemeinsamen Verwaltungsverbands/der Verwaltungs- "
    "gemeinschaft, die laut offizieller Quelle das Ordnungsamt/die "
    "Ortspolizeibehoerde-Funktion fuer diese Gemeinde mit uebernimmt "
    "(siehe Skript-Docstring fuer Quellen je Verband)."
)


def main(apply_changes: bool) -> None:
    db = SessionLocal()
    today = date.today()
    yesterday = today - timedelta(days=1)
    try:
        found = 0
        for ags, jurisdiction_id in TO_EXPIRE:
            row = (
                db.query(Jurisdiction)
                .filter(
                    Jurisdiction.jurisdiction_id == jurisdiction_id,
                    Jurisdiction.request_type_id == REQUEST_TYPE_ID,
                    Jurisdiction.ags == ags,
                    Jurisdiction.active.is_(True),
                )
                .first()
            )
            if row is None:
                print(f"SKIP ags={ags} jurisdiction_id={jurisdiction_id}: nicht gefunden oder schon abgelaufen")
                continue
            found += 1
            print(f"EXPIRE ags={ags} jurisdiction_id={jurisdiction_id} (authority_id={row.authority_id})")
            if apply_changes:
                row.valid_to = yesterday
                row.notes = (row.notes + " | " if row.notes else "") + NOTE_SUFFIX.format(today=today.isoformat())

        if apply_changes:
            db.commit()
            print(f"\nAngewendet: {found} Zeilen abgelaufen.")
        else:
            print(f"\n{found} Kandidaten gefunden. Dry-run only - keine Aenderung. --apply zum Anwenden.")
    finally:
        db.close()


if __name__ == "__main__":
    apply_changes = "--apply" in sys.argv
    main(apply_changes=apply_changes)
