"""
API Routes: Datenqualität

Liefert eine Übersicht über Lücken in den Stammdaten (z.B. Behörden ohne
E-Mail-Adresse oder Behörden, die in keiner Zuständigkeit referenziert
werden), damit diese proaktiv gepflegt werden können statt erst beim
Matching als NO_MATCH/"keine E-Mail" aufzufallen.
"""

import io
from datetime import datetime, timedelta
from operator import attrgetter
from typing import Iterable, List, Optional, Set

from openpyxl import Workbook
from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font
from openpyxl.utils import get_column_letter
from fastapi import APIRouter, Depends, Response
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.api.auth import require_main
from app.api.geo import _geocode_and_cache_building
from app.database import get_db_session
from app.models.authority import Authority
from app.models.authority_location import AuthorityLocation
from app.models.building import Building
from app.models.case import CaseBuilding
from app.models.jurisdiction import Jurisdiction
from app.models.request import Request, RequestItem
from app.models.request_item_progress import RequestItemProgress
from app.models.request_type import RequestType
from app.services import JurisdictionMatchingService, MatchingStatus
from app.services.building_cleanup import delete_building_with_dependents
from app.services.dq_cache import clear_data_quality_cache, get_or_compute

__all__ = ["router", "clear_data_quality_cache"]

router = APIRouter()

MAX_ITEMS = 200

# Ab diesem Alter gilt eine Verifizierung als abgelaufen und die Behörde
# taucht wieder unter "nicht verifiziert" auf - last_verified_at soll ein
# Datenstand bestätigen, keine einmalige Momentaufnahme für immer sein.
_VERIFICATION_STALE_DAYS = 365

# Felder, die beim Zusammenführen von Duplikaten von der zu löschenden
# Zeile auf die verbleibende übertragen werden, sofern dort noch leer.
_MERGE_FIELDS = (
    "department_name", "street", "house_number", "postal_code", "city",
    "state", "email", "phone", "website", "source",
)

_BUILDING_MERGE_FIELDS = ("property_name", "district", "state", "ags", "notes", "internal_reference")

# Maximale absolute Levenshtein-Distanz, ab der ein Behörden-Namenspaar als
# möglicher Tippfehler-Duplikat gilt. Bewusst ein ABSOLUTER Wert statt eines
# Ähnlichkeits-Prozentsatzes: ein echter Tippfehler ist immer eine kleine
# feste Anzahl Zeichenänderungen (typischerweise 1-2), unabhängig davon, wie
# lang der Name ist. Ein Ähnlichkeits-Prozentsatz würde dagegen bei langen
# Namen, die sich nur in einem ganzen Wort unterscheiden (z.B.
# "Kreisverwaltung X" vs. "Stadtverwaltung X" - zwei tatsächlich
# UNTERSCHIEDLICHE, real existierende Behörden, keine Duplikate), fälschlich
# einen hohen Wert ergeben, weil das eine abweichende Wort nur einen kleinen
# Anteil der Gesamtlänge ausmacht. Nur ein Hinweis, nie automatisch
# zusammengeführt - siehe _fuzzy_duplicate_authority_pairs.
_FUZZY_MAX_EDIT_DISTANCE = 2
# Kürzere normalisierte Namen als das werden ausgeklammert, damit kurze,
# generische Namensfragmente nicht zufällig als "ähnlich" durchrutschen.
_FUZZY_MIN_NAME_LENGTH = 8

_UMLAUT_FOLD = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})


def _normalize_for_similarity(value: Optional[str]) -> str:
    """Falzt Umlaute/ß aus und vereinheitlicht Whitespace, damit reine
    Schreibvarianten (z.B. 'Köln' vs 'Koeln', doppelte Leerzeichen) nicht
    schon als Tippfehler gewertet werden."""
    if not value:
        return ""
    return " ".join(value.strip().lower().translate(_UMLAUT_FOLD).split())


def _levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    previous_row = list(range(len(b) + 1))
    for i, char_a in enumerate(a, start=1):
        current_row = [i] + [0] * len(b)
        for j, char_b in enumerate(b, start=1):
            current_row[j] = min(
                current_row[j - 1] + 1,  # Einfügen
                previous_row[j] + 1,  # Löschen
                previous_row[j - 1] + (0 if char_a == char_b else 1),  # Ersetzen
            )
        previous_row = current_row
    return previous_row[-1]


def _levenshtein_within(a: str, b: str, max_distance: int) -> int:
    """
    Wie _levenshtein, bricht aber ab, sobald die Distanz sicher größer als
    `max_distance` ist, und liefert dann `max_distance + 1`. Ist die Distanz
    <= max_distance, ist das Ergebnis EXAKT dieselbe Zahl wie _levenshtein.

    Drei verlustfreie Abkürzungen: (1) der Längenunterschied ist eine untere
    Schranke der Distanz; (2) gemeinsames Präfix/Suffix ändert die Distanz
    nicht und kann abgeschnitten werden (bei Tippfehlern bleibt meist nur
    ein winziger Rest); (3) für den Rest genügt ein schmales Band der Breite
    2*max_distance+1 um die Diagonale (Ukkonen-Schnitt) mit frühem Abbruch.
    """
    if a == b:
        return 0
    limit = max_distance + 1
    if abs(len(a) - len(b)) > max_distance:
        return limit

    start = 0
    shortest = min(len(a), len(b))
    while start < shortest and a[start] == b[start]:
        start += 1
    end_a, end_b = len(a), len(b)
    while end_a > start and end_b > start and a[end_a - 1] == b[end_b - 1]:
        end_a -= 1
        end_b -= 1
    a = a[start:end_a]
    b = b[start:end_b]

    if not a:
        return min(len(b), limit)
    if not b:
        return min(len(a), limit)

    len_a, len_b = len(a), len(b)
    previous = [j if j <= max_distance else limit for j in range(len_b + 1)]
    for i in range(1, len_a + 1):
        char_a = a[i - 1]
        low = max(1, i - max_distance)
        high = min(len_b, i + max_distance)
        current = [limit] * (len_b + 1)
        best = limit
        if i <= max_distance:
            current[0] = i
            best = i
        for j in range(low, high + 1):
            value = previous[j - 1] + (char_a != b[j - 1])
            candidate = previous[j] + 1
            if candidate < value:
                value = candidate
            candidate = current[j - 1] + 1
            if candidate < value:
                value = candidate
            if value > limit:
                value = limit
            current[j] = value
            if value < best:
                best = value
        if best > max_distance:
            return limit
        previous = current
    return min(previous[len_b], limit)


def _name_similarity(a: str, b: str, distance: Optional[int] = None) -> float:
    """
    1.0 = identisch, 0.0 = maximal unterschiedlich (normierte Levenshtein-Distanz).
    `distance` kann übergeben werden, wenn die Distanz schon bekannt ist.
    """
    if not a and not b:
        return 1.0
    if distance is None:
        distance = _levenshtein(a, b)
    return 1 - distance / max(len(a), len(b))


# Geografische Felder, die den fachlichen Geltungsbereich einer Zuständig-
# keitsregel ausmachen. Zwei Regeln mit identischem authority_id+request_
# type_id UND identischem Geltungsbereich sind derselbe fachliche Fall.
_JURISDICTION_GEO_FIELDS = ("ags", "municipality", "district", "postal_code", "street", "house_number", "state")
# Innerhalb einer solchen Gruppe: nur wenn auch diese Felder identisch sind,
# ist es ein echtes Duplikat (z.B. versehentlich zweimal importiert) - weichen
# sie ab, ist unklar welche Zeile korrekt ist (nie raten).
_JURISDICTION_COMPARE_FIELDS = ("priority", "matching_level", "valid_from", "valid_to")


def _serialize(a: Authority) -> dict:
    return {
        "authority_id": a.authority_id,
        "authority_name": a.authority_name,
        "city": a.city,
    }


def _serialize_building(b: Building) -> dict:
    return {
        "building_id": b.building_id,
        "street": b.street,
        "house_number": b.house_number,
        "postal_code": b.postal_code,
        "city": b.city,
    }


def _serialize_jurisdictions(
    jurisdictions: List[Jurisdiction], db: Session, limit: int
) -> List[dict]:
    """Reichert eine (schon auf `limit` gekürzte) Liste um Anzeige-Kontext an."""
    subset = jurisdictions[:limit]
    authority_ids = {j.authority_id for j in subset}
    request_type_ids = {j.request_type_id for j in subset}
    # Nur die zwei benötigten Spalten statt voller ORM-Zeilen laden; je eine
    # gebündelte IN-Abfrage (kein Query pro Zeile).
    authorities_by_id = {
        row.authority_id: row.authority_name
        for row in db.query(Authority.authority_id, Authority.authority_name)
        .filter(Authority.authority_id.in_(authority_ids))
        .all()
    } if authority_ids else {}
    request_types_by_id = {
        row.request_type_id: row.name
        for row in db.query(RequestType.request_type_id, RequestType.name)
        .filter(RequestType.request_type_id.in_(request_type_ids))
        .all()
    } if request_type_ids else {}
    return [
        {
            "jurisdiction_id": j.jurisdiction_id,
            "authority_name": authorities_by_id.get(j.authority_id, j.authority_id),
            "request_type_name": request_types_by_id.get(j.request_type_id, j.request_type_id),
            "ags": j.ags,
            "municipality": j.municipality,
        }
        for j in subset
    ]


# Spalten, die die Übersichts-Berechnung von einer Behörde tatsächlich braucht
# (Anzeige: id/name/Ort; Duplikat-Erkennung: zusätzlich Straße). Im
# "slim"-Modus werden nur sie geladen (als Row-Objekte mit denselben
# Attributnamen) statt der vollen ORM-Zeile mit allen ~20 Spalten.
_AUTHORITY_SLIM_COLUMNS = (
    Authority.authority_id, Authority.authority_name, Authority.city, Authority.street,
)


def _authority_query(db: Session, slim: bool):
    return db.query(*_AUTHORITY_SLIM_COLUMNS) if slim else db.query(Authority)


def _active_authorities(db: Session, slim: bool = False) -> list:
    return _authority_query(db, slim).filter(Authority.active.is_(True)).all()


def _jurisdiction_authority_ids(db: Session) -> Set[str]:
    """authority_id aller Behörden, auf die mindestens eine Zuständigkeitsregel zeigt."""
    return {row[0] for row in db.query(Jurisdiction.authority_id).distinct().all()}


def _authorities_without_email(db: Session, slim: bool = False) -> list:
    return (
        _authority_query(db, slim)
        .filter(Authority.active.is_(True))
        .filter(or_(Authority.email.is_(None), Authority.email == ""))
        .order_by(Authority.authority_name)
        .all()
    )


def _authorities_without_jurisdiction(
    db: Session,
    slim: bool = False,
    active_authorities: Optional[list] = None,
    referenced_ids: Optional[Set[str]] = None,
) -> list:
    """`active_authorities`/`referenced_ids` können übergeben werden, wenn der
    Aufrufer sie ohnehin schon geladen hat (spart je eine Abfrage)."""
    if referenced_ids is None:
        referenced_ids = _jurisdiction_authority_ids(db)
    if active_authorities is None:
        active_authorities = _active_authorities(db, slim)
    without_jurisdiction = [a for a in active_authorities if a.authority_id not in referenced_ids]
    without_jurisdiction.sort(key=lambda a: a.authority_name or "")
    return without_jurisdiction


def _authorities_without_address(db: Session, slim: bool = False) -> list:
    """
    Behörden ganz ohne Straße UND Ort. Wichtig: genau diese führen beim
    Kartenpin-Geocoding sonst zu einer irreführenden Auflösung auf den
    geografischen Mittelpunkt Deutschlands (siehe get_authority_location).
    """
    return (
        _authority_query(db, slim)
        .filter(Authority.active.is_(True))
        .filter(or_(Authority.street.is_(None), Authority.street == ""))
        .filter(or_(Authority.city.is_(None), Authority.city == ""))
        .order_by(Authority.authority_name)
        .all()
    )


def _is_unlocated(a) -> bool:
    return not (a.street and a.street.strip()) and not (a.city and a.city.strip())


def _find_duplicate_authority_groups(
    db: Session,
    slim: bool = False,
    active_authorities: Optional[list] = None,
    jurisdiction_authority_ids: Optional[Set[str]] = None,
):
    """
    Findet Namens-Gruppen mit genau einer "unlokalisierten" Behörde (weder
    Straße noch Ort hinterlegt) und mindestens einer weiteren, aktiven
    Behörde gleichen Namens, die eine Adresse hat.

    Typischer Entstehungsweg: ein Import ohne Ortsangabe legt eine Behörde
    ohne Adresse an; ein späterer fill_gaps-Import mit dieser Behörde
    (jetzt mit Ort) findet die alte Zeile nicht (Abgleich lief über
    Name+Ort) und legt fälschlich eine zweite, doppelte Behörde an. Die
    unlokalisierte Zeile bleibt i.d.R. die "echte", weil Zuständigkeits-
    regeln bereits auf sie zeigen können - deshalb wird in sie gemergt,
    nicht umgekehrt.

    Gibt (resolvable, needs_review) zurück. Aufgelöst wird nur, wenn die zu
    löschende(n) Zeile(n) nachweislich von keiner Zuständigkeitsregel und
    keinem Anfrage-Item referenziert werden - alle anderen Fälle landen in
    needs_review statt geraten zu werden.

    slim=True liefert Row-Objekte (id/name/Ort/Straße) statt voller ORM-Zeilen
    - für reine Anzeige/ID-Auswertung; die Merge-Endpunkte brauchen die
    vollständigen Entities (slim=False). `active_authorities` und
    `jurisdiction_authority_ids` können vom Aufrufer vorgeladen übergeben
    werden, um doppelte Abfragen zu sparen.
    """
    active = active_authorities if active_authorities is not None else _active_authorities(db, slim)
    if jurisdiction_authority_ids is None:
        jurisdiction_authority_ids = _jurisdiction_authority_ids(db)
    referenced_ids = set(jurisdiction_authority_ids)
    referenced_ids |= {
        row[0]
        for row in db.query(RequestItem.authority_id).filter(RequestItem.authority_id.isnot(None)).distinct().all()
    }

    groups: dict = {}
    for a in active:
        groups.setdefault((a.authority_name or "").strip().lower(), []).append(a)

    resolvable = []
    needs_review = []

    for rows in groups.values():
        if len(rows) < 2:
            continue
        stubs = [a for a in rows if _is_unlocated(a)]
        full = [a for a in rows if not _is_unlocated(a)]
        if len(stubs) != 1 or not full:
            continue

        keep = stubs[0]
        if any(dup.authority_id in referenced_ids for dup in full):
            needs_review.append(keep)
            continue

        resolvable.append({"keep": keep, "remove": full})

    return resolvable, needs_review


def _duplicate_authority_ids(db: Session, active_authorities: Optional[list] = None) -> set:
    """authority_id aller Behörden, die in einer erkannten Duplikat-Gruppe stecken (auflösbar oder nicht)."""
    resolvable, needs_review = _find_duplicate_authority_groups(
        db, slim=True, active_authorities=active_authorities
    )
    ids = set()
    for group in resolvable:
        ids.add(group["keep"].authority_id)
        ids.update(a.authority_id for a in group["remove"])
    ids.update(a.authority_id for a in needs_review)
    return ids


def _fuzzy_duplicate_authority_pairs(db: Session) -> List[dict]:
    """
    Findet Behörden-Paare mit sehr ähnlichem Namen (Tippfehler, abweichende
    Umlaut-Schreibweise, doppelte Leerzeichen) innerhalb derselben Stadt, die
    von der exakten Duplikat-Erkennung (_find_duplicate_authority_groups -
    erkennt nur identische normalisierte Namen) übersehen werden.

    Um die Anzahl der Vergleiche gering zu halten, wird nur innerhalb
    derselben Stadt verglichen (Duplikate teilen sich fast immer den Ort;
    das reduziert eine sonst quadratische Prüfung über alle ~4700 aktiven
    Behörden auf kleine Gruppen pro Stadt).

    Rein informativ, NIE automatisch zusammengeführt: anders als bei exakt
    identischen Namen ist bei bloßer Ähnlichkeit nicht sicher, ob es
    tatsächlich dieselbe Behörde ist oder zwei unterschiedliche mit
    ähnlichem Namen (z.B. verschiedene Fachbereiche) - das muss ein Mensch
    entscheiden.
    """
    active = _active_authorities(db, slim=True)
    already_flagged = _duplicate_authority_ids(db, active_authorities=active)

    by_city: dict = {}
    for a in active:
        normalized = _normalize_for_similarity(a.authority_name)
        if len(normalized) < _FUZZY_MIN_NAME_LENGTH:
            continue
        by_city.setdefault((a.city or "").strip().lower(), []).append((a, normalized))

    max_distance = _FUZZY_MAX_EDIT_DISTANCE
    pairs = []
    for group in by_city.values():
        if len(group) < 2:
            continue
        # Namen + Längen einmal vorab auslesen, damit die innere Schleife (bis
        # zu ~n^2/2 Durchläufe in großen Städten) nur noch int-Vergleiche
        # macht und die teure Distanzberechnung selten erreicht wird.
        entries = [(a, name, len(name), a.authority_id in already_flagged) for a, name in group]
        for i in range(len(entries)):
            a, name_a, len_a, flagged_a = entries[i]
            for j in range(i + 1, len(entries)):
                b, name_b, len_b, flagged_b = entries[j]
                # Günstiger Vorabtest: die Levenshtein-Distanz kann nie kleiner
                # sein als der Längenunterschied - ist der allein schon zu groß,
                # lohnt sich die teure Berechnung nicht.
                if abs(len_a - len_b) > max_distance:
                    continue
                if flagged_a and flagged_b:
                    continue
                if name_a == name_b:
                    continue  # bereits über die exakte Erkennung abgedeckt
                distance = _levenshtein_within(name_a, name_b, max_distance)
                if distance <= max_distance:
                    pairs.append(
                        {
                            "authority_id_a": a.authority_id,
                            "authority_name_a": a.authority_name,
                            "authority_id_b": b.authority_id,
                            "authority_name_b": b.authority_name,
                            "city": a.city,
                            "similarity": round(_name_similarity(name_a, name_b, distance), 2),
                        }
                    )

    return sorted(pairs, key=lambda p: -p["similarity"])


def _buildings_with_review_required(db: Session) -> List[Building]:
    """
    Gebäude, deren zuletzt durchgeführtes Matching (neuester Request) für
    mindestens eine Auskunftsart "Prüfung nötig" (REVIEW_REQUIRED) ergab -
    also keine eindeutige Behörde gefunden wurde.
    """
    latest_per_building = (
        db.query(Request.building_id, func.max(Request.created_at).label("latest_at"))
        .group_by(Request.building_id)
        .subquery()
    )
    latest_requests = (
        db.query(Request.request_id, Request.building_id)
        .join(
            latest_per_building,
            (Request.building_id == latest_per_building.c.building_id)
            & (Request.created_at == latest_per_building.c.latest_at),
        )
        .all()
    )
    if not latest_requests:
        return []

    request_to_building = {r.request_id: r.building_id for r in latest_requests}
    review_request_ids = {
        row[0]
        for row in db.query(RequestItem.request_id)
        .filter(RequestItem.request_id.in_(request_to_building.keys()))
        .filter(RequestItem.matching_status == "REVIEW_REQUIRED")
        .distinct()
        .all()
    }
    building_ids = {request_to_building[rid] for rid in review_request_ids}
    if not building_ids:
        return []

    return (
        db.query(Building)
        .filter(Building.building_id.in_(building_ids))
        .order_by(Building.city, Building.street)
        .all()
    )


def _buildings_without_coordinates(db: Session) -> List[Building]:
    """
    Gebäude ohne gecachte Kartenkoordinaten - entweder nie geocodiert
    (z.B. noch nie im Wizard/der Kartenansicht geöffnet) oder die
    Geokodierung ist fehlgeschlagen (siehe geocode_address: es wird nicht
    geraten, ein Fehlschlag bleibt dauerhaft NULL statt eines Platzhalters).
    """
    return (
        db.query(Building)
        .filter(or_(Building.latitude.is_(None), Building.longitude.is_(None)))
        .order_by(Building.city, Building.street)
        .all()
    )


def _coverage_gaps(db: Session) -> List[dict]:
    """
    Prüft für jedes aktive Gebäude mit AGS und jede aktive Auskunftsart über
    die echte Matching-Engine (JurisdictionMatchingService - dieselbe Logik
    wie beim tatsächlichen Matching, kein eigenes Regelwerk), ob aktuell eine
    Zuständigkeit gefunden würde. Ergebnis sind Lücken, die eine ECHTE
    Anfrage heute als NO_MATCH beenden würden - bevor das jemandem im
    laufenden Betrieb passiert.

    Gebäude ohne AGS werden ausgeklammert: ihr Fehlschlag läge an fehlenden
    Gebäudedaten, nicht an einer fehlenden Zuständigkeitsregel - das ist ein
    eigenes, bereits vorhandenes Datenproblem ("Ohne AGS"-Filter), keine
    Abdeckungslücke.

    Treffer werden nach (AGS, Auskunftsart) gruppiert, damit eine Lücke, die
    mehrere Gebäude derselben Gemeinde betrifft, nicht pro Gebäude einzeln
    auftaucht. Rein informativ - eine fehlende Regel kann nicht automatisch
    erfunden werden, das erfordert echtes Wissen über die zuständige Behörde.
    """
    buildings = db.query(Building).filter(Building.ags.isnot(None), Building.ags != "").all()
    request_types = db.query(RequestType).filter(RequestType.active.is_(True)).all()
    if not buildings or not request_types:
        return []

    # Zwei gebündelte Vorab-Abfragen (statt Matching-Abfragen pro Gebäude):
    #
    # 1. Auskunftsarten, für die es überhaupt keine aktive Regel gibt: jede
    #    Matching-Stufe filtert auf request_type_id + active (siehe
    #    JurisdictionMatchingService._base_query) - das Ergebnis ist für jedes
    #    Gebäude zwingend NO_MATCH, die Matching-Engine muss nicht laufen.
    # 2. AGS mit mindestens einer aktiven Regel auf Straßen- oder Bezirks-
    #    ebene: nur dann können die Stufen STREET_NUMBER/STREET/DISTRICT
    #    überhaupt etwas finden (sie verlangen Regel-Zeilen mit nicht-leerer
    #    Straße bzw. nicht-leerem Bezirk in genau dieser AGS). Für alle
    #    anderen AGS sind Straße/Hausnummer/Bezirk des Gebäudes für das
    #    Ergebnis irrelevant und müssen nicht in den Cache-Schlüssel.
    request_types_with_rules = {
        row[0]
        for row in db.query(Jurisdiction.request_type_id).filter(Jurisdiction.active.is_(True)).distinct().all()
    }
    building_ags = {b.ags for b in buildings}
    ags_with_street_rules: Set[str] = set()
    for chunk in _chunks(building_ags):
        ags_with_street_rules.update(
            row[0]
            for row in db.query(Jurisdiction.ags)
            .filter(Jurisdiction.active.is_(True), Jurisdiction.ags.in_(chunk))
            .filter(
                or_(
                    (Jurisdiction.street.isnot(None)) & (Jurisdiction.street != ""),
                    (Jurisdiction.district.isnot(None)) & (Jurisdiction.district != ""),
                )
            )
            .distinct()
            .all()
        )

    matcher = JurisdictionMatchingService(db)
    gaps: dict = {}

    # Ergebnis-Cache je (Auskunftsart, alle für das Matching relevanten
    # Rohfelder): zwei Gebäude mit identischen Werten in genau diesen Feldern
    # durchlaufen zwangsläufig dieselben sieben Matching-Stufen und landen
    # beim selben Ergebnis (JurisdictionMatchingService.match_authority ist
    # eine reine Funktion dieser Felder plus des DB-Standes) - der zweite
    # Aufruf braucht dann keine erneute Matching-Engine-Ausführung.
    #
    # Ohne diesen Cache: bis zu 2.000 Gebäude x 11 Auskunftsarten x 7 Stufen
    # sind in einer Messung mit synthetischen Daten (siehe
    # scripts/benchmark_matching_scale.py) ~74.700 SQL-Abfragen und rund zwei
    # Minuten allein lokal ohne Netzwerklatenz - für eine einzelne, synchrone
    # HTTP-Anfrage (die Datenqualitäts-Übersicht) unrealistisch, insbesondere
    # gegen eine entfernte Datenbank (Neon) mit echter Netzwerklatenz pro
    # Abfrage. Der Cache ersetzt keinen Bulk-Endpunkt/Hintergrundjob (siehe
    # Auditbericht-Folgebericht), reduziert die tatsächliche Last aber genau
    # für den in der Praxis häufigsten Fall: viele Gebäude teilen sich eine
    # Gemeinde und damit i.d.R. auch dieselbe Zuständigkeit.
    #
    # Schlüssel: Straße/Hausnummer/Bezirk nur dort, wo die AGS überhaupt
    # Regeln auf dieser Ebene hat (siehe Punkt 2 oben) - sonst genügt ein
    # Matching je (AGS, Bundesland, PLZ, Auskunftsart) für alle Gebäude der
    # Gemeinde.
    result_cache: dict = {}

    for building in buildings:
        if building.ags in ags_with_street_rules:
            address_part = (building.street, building.house_number, building.district)
        else:
            address_part = None
        for request_type in request_types:
            if request_type.request_type_id not in request_types_with_rules:
                status = MatchingStatus.NO_MATCH
            else:
                cache_key = (
                    request_type.request_type_id, building.ags, address_part,
                    building.postal_code, building.state,
                )
                if cache_key in result_cache:
                    status = result_cache[cache_key]
                else:
                    status = matcher.match_authority(building, request_type.request_type_id).matching_status
                    result_cache[cache_key] = status

            if status != MatchingStatus.NO_MATCH:
                continue
            key = (building.ags, request_type.request_type_id)
            entry = gaps.setdefault(
                key,
                {
                    "ags": building.ags,
                    "municipality": building.city,
                    "request_type_name": request_type.name,
                    "building_ids": set(),
                },
            )
            entry["building_ids"].add(building.building_id)

    return sorted(
        (
            {
                "ags": g["ags"],
                "municipality": g["municipality"],
                "request_type_name": g["request_type_name"],
                "building_count": len(g["building_ids"]),
            }
            for g in gaps.values()
        ),
        key=lambda g: (g["municipality"] or "", g["request_type_name"]),
    )


_IN_CHUNK = 500


def _chunks(values: Iterable[str], size: int = _IN_CHUNK):
    values = list(values)
    for start in range(0, len(values), size):
        yield values[start:start + size]


def _buildings_with_real_progress(db: Session, building_ids: Iterable[str]) -> Set[str]:
    """
    Teilmenge von `building_ids`, für die schon einmal ein Schreiben tatsächlich
    als versendet markiert wurde oder eine Antwort hinterlegt ist - solche
    Gebäude werden von der automatischen Bereinigung übersprungen, auch wenn
    das aktuelle Matching "Prüfung nötig" zeigt (nie echte Arbeit löschen).

    Eine gebündelte Join-Abfrage je 500 Gebäude statt drei Abfragen pro Gebäude
    (wichtig gegen eine entfernte Datenbank: jede Abfrage kostet einen
    Netzwerk-Roundtrip).
    """
    result: Set[str] = set()
    for chunk in _chunks(building_ids):
        rows = (
            db.query(Request.building_id)
            .join(RequestItem, RequestItem.request_id == Request.request_id)
            .join(RequestItemProgress, RequestItemProgress.request_item_id == RequestItem.request_item_id)
            .filter(Request.building_id.in_(chunk))
            .filter(or_(RequestItemProgress.sent_at.isnot(None), RequestItemProgress.response_received_at.isnot(None)))
            .distinct()
            .all()
        )
        result.update(row[0] for row in rows)
    return result


def _building_has_real_progress(db: Session, building_id: str) -> bool:
    """Einzel-Variante von _buildings_with_real_progress."""
    return building_id in _buildings_with_real_progress(db, [building_id])


def _authorities_unverified(db: Session, slim: bool = False) -> list:
    """
    Aktive Behörden, die noch nie oder vor mehr als _VERIFICATION_STALE_DAYS
    Tagen zuletzt als aktuell/korrekt bestätigt wurden.
    """
    cutoff = datetime.utcnow() - timedelta(days=_VERIFICATION_STALE_DAYS)
    return (
        _authority_query(db, slim)
        .filter(Authority.active.is_(True))
        .filter(or_(Authority.last_verified_at.is_(None), Authority.last_verified_at < cutoff))
        .order_by(Authority.authority_name)
        .all()
    )


# Spalten, die die Übersicht für Zuständigkeitsregeln braucht: Anzeige
# (_serialize_jurisdictions) plus - für die Duplikat-Erkennung - die
# Geltungsbereichs- und Vergleichsfelder sowie created_at. Im "slim"-Modus nur
# diese (als Row-Objekte), statt alle ~25 Spalten inkl. Textfeldern von bis zu
# ~16.000 Regeln zu laden.
_JURISDICTION_DISPLAY_COLUMNS = (
    Jurisdiction.jurisdiction_id, Jurisdiction.authority_id, Jurisdiction.request_type_id,
    Jurisdiction.ags, Jurisdiction.municipality,
)


def _jurisdictions_orphaned(db: Session, slim: bool = False) -> list:
    """
    Aktive Zuständigkeitsregeln, deren Behörde inzwischen deaktiviert wurde.
    Rein informativ (keine Auto-Aktion): unklar, ob die Regel deaktiviert
    oder die Behörde reaktiviert werden sollte - das muss ein Mensch
    entscheiden.
    """
    inactive_ids = db.query(Authority.authority_id).filter(Authority.active.is_(False)).scalar_subquery()
    query = db.query(*_JURISDICTION_DISPLAY_COLUMNS) if slim else db.query(Jurisdiction)
    return (
        query
        .filter(Jurisdiction.active.is_(True))
        .filter(Jurisdiction.authority_id.in_(inactive_ids))
        .order_by(Jurisdiction.jurisdiction_id)
        .all()
    )


def _find_duplicate_jurisdiction_groups(db: Session, slim: bool = False):
    """
    Findet Gruppen aktiver Zuständigkeitsregeln mit identischem authority_id
    + request_type_id + identischem Geltungsbereich (_JURISDICTION_GEO_FIELDS).
    Weder Datenbank noch Import verhindern das aktuell strukturell - es gibt
    keine Unique-Constraint auf diese Kombination.

    Nur wenn zusätzlich _JURISDICTION_COMPARE_FIELDS (priority, matching_level,
    Gültigkeitszeitraum) ebenfalls übereinstimmen, ist es ein echtes Duplikat
    (z.B. versehentlich zweimal importiert) -> resolvable, älteste Zeile
    bleibt erhalten. Weichen diese Felder voneinander ab, ist unklar, welche
    Zeile korrekt ist -> needs_review, nie raten.

    slim=True liefert Row-Objekte mit nur den benötigten Spalten (für die
    reine Anzeige/ID-Auswertung); die Merge-Endpunkte brauchen die
    vollständigen Entities (slim=False).
    """
    if slim:
        columns = {c.key: c for c in _JURISDICTION_DISPLAY_COLUMNS}
        for name in _JURISDICTION_GEO_FIELDS + _JURISDICTION_COMPARE_FIELDS + ("created_at",):
            columns[name] = getattr(Jurisdiction, name)
        active = db.query(*columns.values()).filter(Jurisdiction.active.is_(True)).all()
    else:
        active = db.query(Jurisdiction).filter(Jurisdiction.active.is_(True)).all()

    # attrgetter + Mengen-Normalisierung statt getattr je Feld: bei ~16.000
    # Regeln x 9 Feldern ist das die heißeste Schleife dieser Funktion.
    geo_values = attrgetter(*_JURISDICTION_GEO_FIELDS)
    groups: dict = {}
    for j in active:
        key = (j.authority_id, j.request_type_id) + tuple(
            [v.strip() if isinstance(v, str) else v for v in geo_values(j)]
        )
        groups.setdefault(key, []).append(j)

    resolvable = []
    needs_review = []

    for rows in groups.values():
        if len(rows) < 2:
            continue
        rows_sorted = sorted(rows, key=lambda j: j.created_at or datetime.min)
        keep = rows_sorted[0]
        remove = rows_sorted[1:]

        identical = all(
            all(getattr(dup, f) == getattr(keep, f) for f in _JURISDICTION_COMPARE_FIELDS) for dup in remove
        )
        if identical:
            resolvable.append({"keep": keep, "remove": remove})
        else:
            needs_review.append(keep)

    return resolvable, needs_review


def _duplicate_jurisdiction_ids(db: Session) -> set:
    """jurisdiction_id aller Regeln, die in einer erkannten Duplikat-Gruppe stecken (auflösbar oder nicht)."""
    resolvable, needs_review = _find_duplicate_jurisdiction_groups(db, slim=True)
    ids = set()
    for group in resolvable:
        ids.add(group["keep"].jurisdiction_id)
        ids.update(j.jurisdiction_id for j in group["remove"])
    ids.update(j.jurisdiction_id for j in needs_review)
    return ids


def _find_duplicate_building_groups(db: Session):
    """
    Findet Gebäude mit identischer normalisierter Adresse (Straße, Haus-
    nummer, PLZ, Ort) unter verschiedenen building_ids. Weder Datenbank noch
    Import verhindern das aktuell strukturell - nur internal_reference ist
    eindeutig, und das ist nullable.

    Nur auflösbar, wenn GENAU EIN Gebäude der Gruppe bereits referenziert ist
    (Request oder Auftrag) - dieses bleibt erhalten, die referenzlosen werden
    gelöscht (fehlende Felder vorher übernommen, siehe _BUILDING_MERGE_FIELDS).
    Sind mehrere Gebäude der Gruppe JEWEILS referenziert, würde ein Automerge
    zwei unabhängige Anfrage-Historien stillschweigend zusammenwerfen - das
    landet in needs_review statt geraten zu werden. Bewusst konservativ bei
    postal_code: unterschiedliche (nicht nur fehlende) PLZ gruppieren nicht
    zusammen, auch wenn Straße/Hausnummer/Ort übereinstimmen.
    """
    buildings = db.query(Building).all()

    groups: dict = {}
    for b in buildings:
        key = (
            (b.street or "").strip().lower(),
            (b.house_number or "").strip().lower(),
            (b.postal_code or "").strip(),
            (b.city or "").strip().lower(),
        )
        groups.setdefault(key, []).append(b)

    referenced_ids = {row[0] for row in db.query(Request.building_id).distinct().all()}
    referenced_ids |= {row[0] for row in db.query(CaseBuilding.building_id).distinct().all()}

    resolvable = []
    needs_review = []

    for rows in groups.values():
        if len(rows) < 2:
            continue
        referenced = [b for b in rows if b.building_id in referenced_ids]

        if len(referenced) >= 2:
            needs_review.append(rows[0])
            continue

        if len(referenced) == 1:
            keep = referenced[0]
            remove = [b for b in rows if b.building_id != keep.building_id]
        else:
            rows_sorted = sorted(rows, key=lambda b: b.created_at or datetime.min)
            keep = rows_sorted[0]
            remove = rows_sorted[1:]

        resolvable.append({"keep": keep, "remove": remove})

    return resolvable, needs_review


def _duplicate_building_ids(db: Session) -> set:
    """building_id aller Gebäude, die in einer erkannten Duplikat-Gruppe stecken (auflösbar oder nicht)."""
    resolvable, needs_review = _find_duplicate_building_groups(db)
    ids = set()
    for group in resolvable:
        ids.add(group["keep"].building_id)
        ids.update(b.building_id for b in group["remove"])
    ids.update(b.building_id for b in needs_review)
    return ids


def _compute_light_summary(db: Session) -> dict:
    """
    Alle "billigen" Kategorien der Übersicht (ohne coverage_gaps und
    fuzzy_duplicate_authorities, siehe _compute_heavy_summary). Verwendet die
    "slim"-Varianten der Helfer (nur benötigte Spalten) und lädt Behörden/
    Zuständigkeits-Referenzen nur einmal für alle Prüfungen.
    """
    active_authorities = _active_authorities(db, slim=True)
    jurisdiction_authority_ids = _jurisdiction_authority_ids(db)

    total_authorities = len(active_authorities)
    without_email = _authorities_without_email(db, slim=True)
    without_jurisdiction = _authorities_without_jurisdiction(
        db, active_authorities=active_authorities, referenced_ids=jurisdiction_authority_ids
    )
    without_address = _authorities_without_address(db, slim=True)
    duplicate_groups, needs_review_groups = _find_duplicate_authority_groups(
        db, slim=True, active_authorities=active_authorities,
        jurisdiction_authority_ids=jurisdiction_authority_ids,
    )
    duplicate_items = [dup for g in duplicate_groups for dup in g["remove"]]
    review_buildings = _buildings_with_review_required(db)
    review_buildings_skipped = len(
        _buildings_with_real_progress(db, [b.building_id for b in review_buildings])
    )

    unverified = _authorities_unverified(db, slim=True)
    orphaned_jurisdictions = _jurisdictions_orphaned(db, slim=True)
    dup_jurisdiction_groups, dup_jurisdiction_needs_review = _find_duplicate_jurisdiction_groups(db, slim=True)
    dup_jurisdiction_items = [dup for g in dup_jurisdiction_groups for dup in g["remove"]]
    dup_building_groups, dup_building_needs_review = _find_duplicate_building_groups(db)
    dup_building_items = [dup for g in dup_building_groups for dup in g["remove"]]
    without_coordinates = _buildings_without_coordinates(db)

    return {
        "total_authorities": total_authorities,
        "authorities_without_email": {
            "count": len(without_email),
            "items": [_serialize(a) for a in without_email[:MAX_ITEMS]],
        },
        "authorities_without_jurisdiction": {
            "count": len(without_jurisdiction),
            "items": [_serialize(a) for a in without_jurisdiction[:MAX_ITEMS]],
        },
        "authorities_without_address": {
            "count": len(without_address),
            "items": [_serialize(a) for a in without_address[:MAX_ITEMS]],
        },
        "duplicate_authorities": {
            "count": len(duplicate_items),
            "items": [_serialize(a) for a in duplicate_items[:MAX_ITEMS]],
            "needs_review_count": len(needs_review_groups),
        },
        "buildings_review_required": {
            "count": len(review_buildings),
            "items": [_serialize_building(b) for b in review_buildings[:MAX_ITEMS]],
            "needs_review_count": review_buildings_skipped,
        },
        "authorities_unverified": {
            "count": len(unverified),
            "items": [_serialize(a) for a in unverified[:MAX_ITEMS]],
        },
        "jurisdictions_orphaned": {
            "count": len(orphaned_jurisdictions),
            "items": _serialize_jurisdictions(orphaned_jurisdictions, db, MAX_ITEMS),
        },
        "duplicate_jurisdictions": {
            "count": len(dup_jurisdiction_items),
            "items": _serialize_jurisdictions(dup_jurisdiction_items, db, MAX_ITEMS),
            "needs_review_count": len(dup_jurisdiction_needs_review),
        },
        "duplicate_buildings": {
            "count": len(dup_building_items),
            "items": [_serialize_building(b) for b in dup_building_items[:MAX_ITEMS]],
            "needs_review_count": len(dup_building_needs_review),
        },
        "buildings_without_coordinates": {
            "count": len(without_coordinates),
            "items": [_serialize_building(b) for b in without_coordinates[:MAX_ITEMS]],
        },
    }


def _compute_heavy_summary(db: Session) -> dict:
    """Die zwei teuren Kategorien: Abdeckungslücken (echtes Matching) und Namens-Ähnlichkeit."""
    coverage_gaps = _coverage_gaps(db)
    fuzzy_duplicate_authorities = _fuzzy_duplicate_authority_pairs(db)
    return {
        "coverage_gaps": {
            "count": len(coverage_gaps),
            "items": coverage_gaps[:MAX_ITEMS],
        },
        "fuzzy_duplicate_authorities": {
            "count": len(fuzzy_duplicate_authorities),
            "items": fuzzy_duplicate_authorities[:MAX_ITEMS],
        },
    }


_LIGHT_CACHE_KEY = "summary-light"
_HEAVY_CACHE_KEY = "summary-heavy"


def _light_summary(db: Session, refresh: bool) -> dict:
    return get_or_compute(_LIGHT_CACHE_KEY, lambda: _compute_light_summary(db), refresh=refresh)


def _heavy_summary(db: Session, refresh: bool) -> dict:
    return get_or_compute(_HEAVY_CACHE_KEY, lambda: _compute_heavy_summary(db), refresh=refresh)


@router.get("/data-quality/summary", tags=["DataQuality"])
def data_quality_summary(light: bool = False, refresh: bool = False, db: Session = Depends(get_db_session)):
    """
    Übersicht aller Datenqualitäts-Kategorien.

    light=true: die zwei teuren Gruppen (coverage_gaps,
    fuzzy_duplicate_authorities) werden NICHT berechnet, sondern als leere
    Platzhalter ({"count": 0, "items": []}) geliefert und `heavy_pending: true`
    gesetzt - die Zahlen dafür holt der Client separat über
    GET /data-quality/heavy. Ohne light enthält die Antwort wie bisher alles.

    refresh=true umgeht den serverseitigen Cache (siehe app/services/dq_cache.py).
    """
    summary = dict(_light_summary(db, refresh))
    if light:
        summary["coverage_gaps"] = {"count": 0, "items": []}
        summary["fuzzy_duplicate_authorities"] = {"count": 0, "items": []}
        summary["heavy_pending"] = True
        return summary
    summary.update(_heavy_summary(db, refresh))
    return summary


@router.get("/data-quality/heavy", tags=["DataQuality"])
def data_quality_heavy(refresh: bool = False, db: Session = Depends(get_db_session)):
    """Die zwei teuren Gruppen (coverage_gaps, fuzzy_duplicate_authorities) einzeln."""
    return _heavy_summary(db, refresh)


@router.post("/data-quality/merge-duplicate-authorities", tags=["DataQuality"])
def merge_duplicate_authorities(db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """
    Nur Haupt-Account: löst automatisch erkennbare Behörden-Duplikate auf
    (siehe _find_duplicate_authority_groups). Die unlokalisierte Zeile
    bleibt bestehen und wird um die Felder der Duplikat-Zeile ergänzt
    (nur dort, wo sie selbst noch leer ist); die Duplikat-Zeile(n) werden
    danach gelöscht.
    """
    resolvable, needs_review = _find_duplicate_authority_groups(db)

    now = datetime.utcnow()
    removed = 0
    for group in resolvable:
        keep = group["keep"]
        for dup in group["remove"]:
            for field_name in _MERGE_FIELDS:
                if not getattr(keep, field_name) and getattr(dup, field_name):
                    setattr(keep, field_name, getattr(dup, field_name))
            delete_building_with_dependents(db, dup.building_id)
            removed += 1
        keep.updated_at = now

    db.commit()
    clear_data_quality_cache()
    return {"merged_groups": len(resolvable), "removed": removed, "needs_review": len(needs_review)}


@router.post("/data-quality/merge-duplicate-jurisdictions", tags=["DataQuality"])
def merge_duplicate_jurisdictions(db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """
    Nur Haupt-Account: löst automatisch erkennbare Zuständigkeits-Duplikate
    auf (siehe _find_duplicate_jurisdiction_groups). Die älteste Zeile pro
    Gruppe bleibt erhalten, die restlichen (nachweislich identischen)
    Duplikate werden gelöscht.
    """
    resolvable, needs_review = _find_duplicate_jurisdiction_groups(db)

    now = datetime.utcnow()
    removed = 0
    for group in resolvable:
        for dup in group["remove"]:
            db.delete(dup)
            removed += 1
        group["keep"].updated_at = now

    db.commit()
    clear_data_quality_cache()
    return {"merged_groups": len(resolvable), "removed": removed, "needs_review": len(needs_review)}


@router.post("/data-quality/merge-duplicate-buildings", tags=["DataQuality"])
def merge_duplicate_buildings(db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """
    Nur Haupt-Account: löst automatisch erkennbare Gebäude-Duplikate auf
    (siehe _find_duplicate_building_groups). Das referenzierte (oder bei
    keiner Referenz: älteste) Gebäude bleibt erhalten und wird um fehlende
    Felder aus den Duplikaten ergänzt; die referenzlosen Duplikate werden
    gelöscht.
    """
    resolvable, needs_review = _find_duplicate_building_groups(db)

    now = datetime.utcnow()
    removed = 0
    for group in resolvable:
        keep = group["keep"]
        for dup in group["remove"]:
            for field_name in _BUILDING_MERGE_FIELDS:
                if not getattr(keep, field_name) and getattr(dup, field_name):
                    setattr(keep, field_name, getattr(dup, field_name))
            db.delete(dup)
            removed += 1
        keep.updated_at = now

    db.commit()
    clear_data_quality_cache()
    return {"merged_groups": len(resolvable), "removed": removed, "needs_review": len(needs_review)}


@router.post("/data-quality/delete-review-required-buildings", tags=["DataQuality"])
def delete_review_required_buildings(db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """
    Nur Haupt-Account: löscht Gebäude, deren zuletzt ermittelte Zuständigkeit
    als "Prüfung nötig" markiert ist (siehe _buildings_with_review_required),
    zusammen mit ihrer Anfrage-Historie (Requests/RequestItems/Progress) und
    Auftrags-Verknüpfungen. Gebäude, für die schon einmal ein Schreiben real
    versendet wurde oder eine Antwort hinterlegt ist, werden übersprungen und
    bleiben zur manuellen Prüfung stehen (nie echte Arbeit löschen).
    """
    candidates = _buildings_with_review_required(db)
    buildings_with_progress = _buildings_with_real_progress(db, [b.building_id for b in candidates])

    deleted = 0
    skipped = 0
    for building in candidates:
        if building.building_id in buildings_with_progress:
            skipped += 1
            continue

        delete_building_with_dependents(db, building.building_id)
        deleted += 1

    db.commit()
    clear_data_quality_cache()
    return {"deleted": deleted, "skipped": skipped}


@router.post("/data-quality/clear-bad-geocoding", tags=["DataQuality"])
def clear_bad_geocoding(db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """
    Nur Haupt-Account: entfernt gecachte Kartenkoordinaten von Behörden ohne
    hinterlegte Adresse. Bis zu einem Fix in get_authority_location konnten
    solche Behörden fälschlich auf den geografischen Mittelpunkt Deutschlands
    (nahe Erfurt) geocodiert werden – dieser Aufruf räumt bereits gecachte
    Fehltreffer auf, damit die Karte sie danach korrekt als "keine Adresse"
    behandelt statt einen falschen Pin zu zeigen.
    """
    affected_ids = [a.authority_id for a in _authorities_without_address(db, slim=True)]
    if not affected_ids:
        return {"deleted": 0}

    deleted = (
        db.query(AuthorityLocation)
        .filter(AuthorityLocation.authority_id.in_(affected_ids))
        .delete(synchronize_session=False)
    )
    db.commit()
    clear_data_quality_cache()
    return {"deleted": deleted}


# Nominatim erlaubt max. 1 Anfrage/Sekunde (siehe geocoding.py) - ein
# größerer Batch würde den synchronen Request zu lange blocken/timeouten.
# Bei mehr offenen Gebäuden als das Limit einfach erneut aufrufen.
_GEOCODE_BATCH_LIMIT = 20


@router.post("/data-quality/geocode-missing-buildings", tags=["DataQuality"])
def geocode_missing_buildings(db: Session = Depends(get_db_session), _: None = Depends(require_main)):
    """
    Nur Haupt-Account: versucht für bis zu _GEOCODE_BATCH_LIMIT Gebäude ohne
    Kartenkoordinaten erneut eine Geokodierung über Nominatim. Es wird
    nirgends geraten - schlägt eine Adresse fehl, bleibt sie ohne Koordinaten
    und taucht beim nächsten Aufruf wieder auf.
    """
    missing = _buildings_without_coordinates(db)[:_GEOCODE_BATCH_LIMIT]
    geocoded = 0
    for building in missing:
        if _geocode_and_cache_building(building):
            geocoded += 1
    db.commit()
    clear_data_quality_cache()
    remaining = len(_buildings_without_coordinates(db))
    return {"geocoded": geocoded, "failed": len(missing) - geocoded, "remaining": remaining}


_EXPORT_CACHE_KEY = "export-xlsx"

_EXPORT_AUTHORITY_COLUMNS = [
    "Behörde", "Abteilung", "Straße", "Hausnummer", "PLZ", "Ort",
    "Bundesland", "E-Mail", "Telefon", "Website",
]
_EXPORT_BUILDING_COLUMNS = ["Straße", "Hausnummer", "PLZ", "Ort"]
_EXPORT_JURISDICTION_COLUMNS = ["Behörde", "Auskunftsart", "AGS", "Gemeinde"]


def _export_authority_rows(authorities: list) -> list:
    return [
        [
            a.authority_name, a.department_name, a.street, a.house_number, a.postal_code,
            a.city, a.state, a.email, a.phone, a.website,
        ]
        for a in authorities
    ]


def _export_building_rows(buildings: list) -> list:
    return [[b.street, b.house_number, b.postal_code, b.city] for b in buildings]


def _export_jurisdiction_rows(jurisdictions: list, db: Session) -> list:
    serialized = _serialize_jurisdictions(jurisdictions, db, len(jurisdictions))
    return [[j["authority_name"], j["request_type_name"], j["ags"], j["municipality"]] for j in serialized]


def _build_export_sheets(db: Session) -> List[tuple]:
    """(Blattname, Spaltenüberschriften, Zeilen als Listen) je Kategorie."""
    duplicate_authority_groups, _ = _find_duplicate_authority_groups(db)
    duplicate_authority_items = [dup for g in duplicate_authority_groups for dup in g["remove"]]
    duplicate_jurisdiction_groups, _ = _find_duplicate_jurisdiction_groups(db, slim=True)
    duplicate_jurisdiction_items = [dup for g in duplicate_jurisdiction_groups for dup in g["remove"]]
    duplicate_building_groups, _ = _find_duplicate_building_groups(db)
    duplicate_building_items = [dup for g in duplicate_building_groups for dup in g["remove"]]

    return [
        ("Ohne E-Mail", _EXPORT_AUTHORITY_COLUMNS, _export_authority_rows(_authorities_without_email(db))),
        (
            "Ohne Zuständigkeit",
            _EXPORT_AUTHORITY_COLUMNS,
            _export_authority_rows(_authorities_without_jurisdiction(db)),
        ),
        ("Ohne Adresse", _EXPORT_AUTHORITY_COLUMNS, _export_authority_rows(_authorities_without_address(db))),
        ("Nicht verifiziert", _EXPORT_AUTHORITY_COLUMNS, _export_authority_rows(_authorities_unverified(db))),
        ("Behörden-Duplikate", _EXPORT_AUTHORITY_COLUMNS, _export_authority_rows(duplicate_authority_items)),
        (
            "Zuständigkeits-Duplikate",
            _EXPORT_JURISDICTION_COLUMNS,
            _export_jurisdiction_rows(duplicate_jurisdiction_items, db),
        ),
        (
            "Verwaiste Zuständigkeiten",
            _EXPORT_JURISDICTION_COLUMNS,
            _export_jurisdiction_rows(_jurisdictions_orphaned(db, slim=True), db),
        ),
        ("Gebäude-Duplikate", _EXPORT_BUILDING_COLUMNS, _export_building_rows(duplicate_building_items)),
        (
            "Gebäude Prüfung nötig",
            _EXPORT_BUILDING_COLUMNS,
            _export_building_rows(_buildings_with_review_required(db)),
        ),
        (
            "Ohne Kartenkoordinaten",
            _EXPORT_BUILDING_COLUMNS,
            _export_building_rows(_buildings_without_coordinates(db)),
        ),
        (
            "Abdeckungslücken",
            ["AGS", "Gemeinde", "Auskunftsart", "Betroffene Gebäude"],
            [[g["ags"], g["municipality"], g["request_type_name"], g["building_count"]] for g in _coverage_gaps(db)],
        ),
        (
            "Mögliche Duplikate (ähnlich)",
            ["Behörde A", "Behörde B", "Ort", "Ähnlichkeit"],
            [
                [p["authority_name_a"], p["authority_name_b"], p["city"], p["similarity"]]
                for p in _fuzzy_duplicate_authority_pairs(db)
            ],
        ),
    ]


def _render_export_xlsx(sheets: List[tuple]) -> bytes:
    """Schreibt die Blätter mit openpyxl im write_only-Modus (Zeile für Zeile,
    ohne Zellobjekte im Speicher). Das ist um ein Vielfaches schneller als
    pandas.DataFrame.to_excel - bei ~100.000 Zellen der Unterschied zwischen
    Sekunden und Minuten auf dem kleinen Produktions-Server."""
    workbook = Workbook(write_only=True)
    bold = Font(bold=True)
    for sheet_name, columns, rows in sheets:
        sheet = workbook.create_sheet(title=sheet_name)
        for index, column in enumerate(columns, start=1):
            sheet.column_dimensions[get_column_letter(index)].width = max(14, min(48, len(column) + 6))
        header = []
        for column in columns:
            cell = WriteOnlyCell(sheet, value=column)
            cell.font = bold
            header.append(cell)
        sheet.append(header)
        for row in rows:
            sheet.append(row)
    buffer = io.BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


@router.get("/data-quality/export-xlsx", tags=["DataQuality"])
def export_data_quality_xlsx(refresh: bool = False, db: Session = Depends(get_db_session)):
    """
    Exportiert alle Datenqualität-Kategorien als Excel-Datei mit einem
    Arbeitsblatt pro Kategorie – zur Weitergabe an Kolleg:innen, die die
    Lücken pflegen sollen. Die fertige Datei wird (wie die Übersicht) kurz
    zwischengespeichert; refresh=true erzwingt eine Neuberechnung.
    """
    content = get_or_compute(
        _EXPORT_CACHE_KEY,
        lambda: _render_export_xlsx(_build_export_sheets(db)),
        refresh=refresh,
    )
    return Response(
        content=content,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=datenqualitaet_luecken.xlsx"},
    )
