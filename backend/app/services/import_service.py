"""
ImportService

Importiert Gebäude-, Behörden- und Zuständigkeitsdaten aus CSV/Excel.

Wichtiges Prinzip: Es wird NIE geraten. Wenn eine Zeile nicht eindeutig
zugeordnet werden kann (z.B. mehrdeutiger Gemeindename ohne Kreis-Angabe),
landet sie im "needs_review"-Topf statt automatisch verknüpft zu werden.
"""

import io
import re
import unicodedata
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import pandas as pd
from sqlalchemy import or_, update, func, bindparam
from sqlalchemy.orm import Session

from app.models.authority import Authority
from app.models.building import Building
from app.models.jurisdiction import Jurisdiction
from app.models.request_type import RequestType
from app.services.address_normalizer import AddressNormalizer

AGS_SPLIT_RE = re.compile(r"[,;/\s]+")

# Länge des (normalisierten) AGS -> Zuständigkeitsebene. 2 = Bundesland,
# 5 = Landkreis/Kreis, 8 = Gemeinde (siehe JurisdictionMatchingService).
_AGS_LEVEL_BY_LENGTH = {2: "STATE", 5: "COUNTY", 8: "MUNICIPALITY"}
# Excel schneidet führende Nullen ab ("05911000" -> "5911000"): diese Längen
# werden eindeutig auf 2/5/8 Stellen aufgefüllt.
_AGS_PAD_LENGTHS = {1: 2, 4: 5, 7: 8}
_AGS_DIGITS_RE = re.compile(r"[0-9]+")


def normalize_ags(value) -> Optional[str]:
    """
    Normalisiert einen einzelnen AGS-Wert: trimmt, entfernt ein angehängtes
    ".0" (Excel-Zahlenformat), verlangt ausschließlich Ziffern und füllt die
    durch Excel abgeschnittenen führenden Nullen auf (1/4/7 -> 2/5/8 Stellen).
    Gültig sind nur 2 (Land), 5 (Kreis) und 8 (Gemeinde) Stellen; alles andere
    liefert None (der Aufrufer macht daraus NEEDS_REVIEW - es wird nie geraten).
    """
    if value is None:
        return None
    text = str(value).strip()
    if text.endswith(".0"):
        text = text[:-2]
    if not _AGS_DIGITS_RE.fullmatch(text):
        return None
    target = _AGS_PAD_LENGTHS.get(len(text))
    if target:
        text = text.zfill(target)
    return text if len(text) in _AGS_LEVEL_BY_LENGTH else None


def infer_matching_level(ags: str, default: str = "MUNICIPALITY") -> str:
    """Leitet die Zuständigkeitsebene aus der AGS-Länge ab (2/5/8), sonst default."""
    return _AGS_LEVEL_BY_LENGTH.get(len(ags), default)


def _fold_umlauts(text: str) -> str:
    """ä->ae, ö->oe, ü->ue, ß->ss, klein, ohne Leerraum."""
    text = text.casefold().replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")
    return re.sub(r"\s+", "", text)


def _strip_diacritics(text: str) -> str:
    """ä->a, ö->o, ü->u, ß->ss, klein, ohne Leerraum (für Eingaben ohne e-Schreibweise)."""
    text = text.casefold().replace("ß", "ss")
    text = "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))
    return re.sub(r"\s+", "", text)


def _request_type_keys(text: str) -> List[str]:
    return list(dict.fromkeys([_fold_umlauts(text), _strip_diacritics(text)]))


@dataclass
class ImportRowResult:
    row_index: int
    status: str  # IMPORTED, UPDATED, DUPLICATE, NEEDS_REVIEW, ERROR
    message: str
    data: dict = field(default_factory=dict)


@dataclass
class ImportSummary:
    total_rows: int
    imported: int
    duplicates: int
    needs_review: int
    errors: int
    updated: int = 0
    # Zeilen ohne Inhalt (z.B. nicht ausgefüllte Zeilen eines Export-Blattes):
    # bewusst weder Fehler noch Prüfbedarf und ohne Eintrag in details.
    skipped: int = 0
    details: List[ImportRowResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_rows": self.total_rows,
            "imported": self.imported,
            "duplicates": self.duplicates,
            "needs_review": self.needs_review,
            "errors": self.errors,
            "updated": self.updated,
            "skipped": self.skipped,
            "details": [
                {"row_index": d.row_index, "status": d.status, "message": d.message}
                for d in self.details
            ],
        }


class ImportService:
    """
    Importiert Massendaten aus CSV/Excel.

    Die eigentliche Spaltenzuordnung (Mapping) wird vom Aufrufer übergeben,
    damit das Frontend dem Benutzer eine Mapping-UI anbieten kann, bevor
    der eigentliche Import läuft.
    """

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def list_sheets(file_content: bytes, filename: str) -> Optional[List[dict]]:
        """
        Liefert bei Excel-Dateien mit mehr als einem Arbeitsblatt dessen Namen
        und Zeilenzahl (None bei CSV oder einblättrigen Excel-Dateien).

        Wichtig, weil das eigene "Als Excel exportieren"-Feature (Datenqualität-
        Tab) mehrblättrige Dateien erzeugt (z.B. "Ohne E-Mail" + "Ohne Adresse")
        - ohne explizite Auswahl würde sonst immer nur das erste Blatt gelesen
        und ein Reimport der Lücken auf einem hinteren Blatt liefe scheinbar
        erfolgreich durch, ohne dass tatsächlich Daten übernommen werden.
        """
        if not filename.lower().endswith((".xlsx", ".xls")):
            return None

        excel_file = pd.ExcelFile(io.BytesIO(file_content))
        if len(excel_file.sheet_names) < 2:
            return None

        sheets = []
        for name in excel_file.sheet_names:
            sheet_df = excel_file.parse(name, dtype=str, nrows=None)
            sheets.append({"name": name, "rows": len(sheet_df)})
        return sheets

    @staticmethod
    def read_file(file_content: bytes, filename: str, sheet_name: Optional[str] = None) -> pd.DataFrame:
        """
        Liest eine CSV- oder Excel-Datei in einen DataFrame ein.

        sheet_name: bei Excel-Dateien mit mehreren Arbeitsblättern das zu
        lesende Blatt. Ohne Angabe wird bei mehreren Blättern das erste mit
        Inhalt gewählt (nie stillschweigend ein leeres erstes Blatt), bei
        genau einem Blatt dieses.
        """
        if filename.lower().endswith(".csv"):
            return pd.read_csv(io.BytesIO(file_content), dtype=str, keep_default_na=False)
        elif filename.lower().endswith((".xlsx", ".xls")):
            if sheet_name is not None:
                return pd.read_excel(
                    io.BytesIO(file_content), sheet_name=sheet_name, dtype=str, keep_default_na=False
                )
            all_sheets = pd.read_excel(io.BytesIO(file_content), sheet_name=None, dtype=str, keep_default_na=False)
            for df in all_sheets.values():
                if len(df) > 0:
                    return df
            return next(iter(all_sheets.values()))
        else:
            raise ValueError(f"Nicht unterstütztes Dateiformat: {filename}")

    def preview(
        self,
        df: pd.DataFrame,
        max_rows: int = 5,
        sheets: Optional[List[dict]] = None,
        selected_sheet: Optional[str] = None,
    ) -> dict:
        """Gibt eine Vorschau der ersten Zeilen zurück."""
        return {
            "total_rows": len(df),
            "columns": list(df.columns),
            "preview_rows": df.head(max_rows).to_dict(orient="records"),
            "sheets": sheets,
            "selected_sheet": selected_sheet or self.pick_default_sheet(sheets),
        }

    @staticmethod
    def pick_default_sheet(sheets: Optional[List[dict]]) -> Optional[str]:
        if not sheets:
            return None
        for s in sheets:
            if s["rows"] > 0:
                return s["name"]
        return sheets[0]["name"]

    @staticmethod
    def _address_key(street: str, house_number: str, postal_code: Optional[str], city: str) -> tuple:
        """
        Normalisierter Adress-Schlüssel für die Dublettenprüfung beim
        Gebäude-Import ohne internal_reference. Nutzt dieselbe Normalisierung
        wie die Matching-Engine (AddressNormalizer), damit z.B. "Musterstr. 12"
        und "Musterstraße 12" als dieselbe Adresse erkannt werden statt als
        vermeintlich unterschiedliche Gebäude.
        """
        normalized = AddressNormalizer.normalize(
            street=street or "", house_number=house_number or "", city=city or "", postal_code=postal_code,
        )
        return (normalized.street, normalized.house_number, normalized.postal_code, normalized.city)

    def import_buildings(self, df: pd.DataFrame, mapping: dict, source_system: Optional[str] = None) -> ImportSummary:
        """
        Importiert Gebäude.

        mapping: {"db_field": "csv_column", ...}
        Pflichtfelder: street, house_number, city (PLZ optional)
        source_system: optionale Kennzeichnung, aus welchem externen System
        dieser Import stammt (z.B. "SAP") - wird nur auf neu angelegten
        Gebäuden gesetzt, siehe Building.source_system.

        Dedublizierung zweistufig (Auditbericht-Folgebericht, Priorität 3,
        Befund "wiederholbare Importe ohne Dubletten"):
        1. internal_reference, wenn vorhanden (wie bisher) - der verlässliche
           Schlüssel, sofern das Quellsystem einen mitliefert.
        2. Fällt internal_reference weg (Feld fehlt in der Datei oder ist für
           diese Zeile leer), zusätzlich die normalisierte Adresse
           (Straße+Hausnummer+PLZ+Ort) gegen den Bestand - verhindert, dass
           ein wiederholter Import derselben Datei ohne stabile Referenz bei
           jedem Lauf stumpf neue Duplikate anlegt. Bewusst KEIN automatisches
           Update der bestehenden Zeile (das wäre Raten, welche der beiden
           Versionen aktuell ist) - die Zeile wird als DUPLICATE geführt,
           damit ein Mensch entscheidet, genau wie bei der bestehenden
           Duplikat-Erkennung im Datenqualitätsmodul.
        """
        required_fields = ["street", "house_number", "city"]
        details: List[ImportRowResult] = []
        imported = duplicates = needs_review = errors = 0

        existing_refs = {
            b.internal_reference for b in self.db.query(Building.internal_reference).all() if b.internal_reference
        }
        existing_addresses = {
            self._address_key(b.street, b.house_number, b.postal_code, b.city)
            for b in self.db.query(
                Building.street, Building.house_number, Building.postal_code, Building.city
            ).all()
        }

        for idx, row in df.iterrows():
            try:
                missing = [f for f in required_fields if not row.get(mapping.get(f, ""), "").strip()]
                if missing:
                    details.append(ImportRowResult(idx, "NEEDS_REVIEW", f"Pflichtfelder fehlen: {missing}"))
                    needs_review += 1
                    continue

                internal_reference = row.get(mapping.get("internal_reference", ""), "").strip() or None
                street = row[mapping["street"]].strip()
                house_number = row[mapping["house_number"]].strip()
                postal_code = row.get(mapping.get("postal_code", ""), "").strip() or None
                city = row[mapping["city"]].strip()

                if internal_reference and internal_reference in existing_refs:
                    details.append(ImportRowResult(idx, "DUPLICATE", f"Referenz '{internal_reference}' existiert bereits"))
                    duplicates += 1
                    continue

                address_key = self._address_key(street, house_number, postal_code, city)
                if not internal_reference and address_key in existing_addresses:
                    details.append(ImportRowResult(
                        idx, "DUPLICATE",
                        f"Adresse '{street} {house_number}, {postal_code or ''} {city}' existiert bereits "
                        "(keine interne Referenz zur eindeutigen Unterscheidung angegeben)",
                    ))
                    duplicates += 1
                    continue

                building = Building(
                    building_id=str(uuid.uuid4()),
                    street=street,
                    house_number=house_number,
                    postal_code=postal_code,
                    city=city,
                    district=row.get(mapping.get("district", ""), "").strip() or None,
                    state=row.get(mapping.get("state", ""), "").strip() or None,
                    ags=row.get(mapping.get("ags", ""), "").strip() or None,
                    property_name=row.get(mapping.get("property_name", ""), "").strip() or None,
                    internal_reference=internal_reference,
                    source_system=source_system,
                )
                self.db.add(building)
                if internal_reference:
                    existing_refs.add(internal_reference)
                existing_addresses.add(address_key)

                details.append(ImportRowResult(idx, "IMPORTED", "OK"))
                imported += 1

            except Exception as exc:
                details.append(ImportRowResult(idx, "ERROR", str(exc)))
                errors += 1

        self.db.commit()

        return ImportSummary(
            total_rows=len(df),
            imported=imported,
            duplicates=duplicates,
            needs_review=needs_review,
            errors=errors,
            details=details,
        )

    def _build_request_type_resolver(self):
        """
        Liefert eine Funktion Rohwert -> request_type_id (oder None).

        Akzeptiert Name, Code oder request_type_id einer Auskunftsart; der
        Vergleich ist unabhängig von Groß-/Kleinschreibung, Leerraum und
        Umlauten/ß ("Erschließungsbeiträge" = "erschliessungsbeitraege").
        Aktive Auskunftsarten haben Vorrang vor inaktiven. Unbekannte Werte
        liefern None - es wird nie geraten.
        """
        index: dict = {}
        rows = self.db.query(
            RequestType.request_type_id, RequestType.code, RequestType.name, RequestType.active
        ).all()
        # Inaktive zuerst eintragen, damit aktive Treffer sie bei Kollision überschreiben.
        for rt_id, code, name, active in sorted(rows, key=lambda r: bool(r[3])):
            for text in (name, code, rt_id):
                if not text:
                    continue
                for key in _request_type_keys(text):
                    index[key] = rt_id

        def resolve(raw: str) -> Optional[str]:
            for key in _request_type_keys(raw):
                if key in index:
                    return index[key]
            return None

        return resolve

    def import_jurisdictions(
        self,
        df: pd.DataFrame,
        mapping: dict,
        request_type_id: Optional[str] = None,
        default_priority: int = 40,
        default_matching_level: str = "MUNICIPALITY",
    ) -> ImportSummary:
        """
        Importiert Zuständigkeiten: pro Zeile eine Behörde (Kontaktdaten werden
        upgeserted, da dieselbe Behörde über mehrere Zeilen/AGS wiederholt sein kann)
        und ein oder mehrere AGS-Schlüssel (Zelle darf mehrere, getrennt durch
        Komma/Semikolon/Leerzeichen, enthalten).

        Pflichtfelder im Mapping: authority_name, ags.

        Auskunftsart: pro Zeile über die optionale Mapping-Spalte "request_type"
        (Name, Code oder ID der Auskunftsart); ist die Zelle leer, gilt das
        Formularfeld request_type_id als Vorgabe für den ganzen Lauf. Fehlt
        beides: NEEDS_REVIEW "Auskunftsart fehlt"; ist der Wert unbekannt:
        NEEDS_REVIEW "Auskunftsart unbekannt: <wert>".

        Nicht ausgefüllte Zeilen (z.B. Export-Blätter der Datenqualität) werden
        nur gezählt (summary.skipped), nicht als Fehler/Prüfbedarf geführt:
        authority_name leer, ODER ags leer bei gemappter, leerer request_type-Zelle.

        AGS: siehe normalize_ags (führende Nullen werden aufgefüllt). Ist EIN
        AGS-Wert einer Zelle ungültig, wird die GANZE Zeile als NEEDS_REVIEW
        geführt und nichts davon importiert (kein Teilimport, nie raten).

        matching_level: ohne gemappten Wert aus der AGS-Länge abgeleitet
        (2 STATE, 5 COUNTY, 8 MUNICIPALITY), sonst default_matching_level.
        """
        details: List[ImportRowResult] = []
        imported = duplicates = needs_review = errors = skipped = 0

        resolve_request_type = self._build_request_type_resolver()
        default_request_type_id: Optional[str] = None
        if request_type_id and str(request_type_id).strip():
            raw_default = str(request_type_id).strip()
            # Wie bisher wird die ID des Formularfelds notfalls unverändert
            # übernommen (rückwärtskompatibel), bevorzugt aber die aufgelöste.
            default_request_type_id = resolve_request_type(raw_default) or raw_default
        request_type_mapped = bool(mapping.get("request_type"))

        # Leichtgewichtiger Lookup (nur IDs) statt voller ORM-Objekte für
        # alle Behörden – siehe import_authorities für die Begründung.
        authority_ids_by_key = {
            (name, city): authority_id
            for authority_id, name, city in self.db.query(
                Authority.authority_id, Authority.authority_name, Authority.city
            ).all()
        }
        # Bestehende (authority_id, ags)-Paare je Auskunftsart, lazy geladen.
        existing_by_request_type: dict = {}

        def existing_jurisdictions_for(rt_id: str) -> set:
            if rt_id not in existing_by_request_type:
                existing_by_request_type[rt_id] = {
                    (j.authority_id, j.ags)
                    for j in self.db.query(Jurisdiction.authority_id, Jurisdiction.ags).filter(
                        Jurisdiction.request_type_id == rt_id
                    )
                }
            return existing_by_request_type[rt_id]

        # Innerhalb eines Batches wiederverwendetes Authority-Objekt, damit
        # dieselbe Behörde (mehrere AGS-Zeilen hintereinander) nicht bei
        # jeder Zeile neu geladen werden muss.
        batch_authority_cache: dict = {}

        def mapped(row, field_name: str) -> Optional[str]:
            col = mapping.get(field_name, "")
            if not col:
                return None
            value = str(row.get(col, "")).strip()
            return value or None

        pending = 0

        for idx, row in df.iterrows():
            try:
                name = mapped(row, "authority_name")
                ags_raw = mapped(row, "ags")
                request_type_cell = mapped(row, "request_type")

                # Nicht ausgefüllte Zeilen: nur zählen, kein details-Eintrag.
                if not name or (not ags_raw and request_type_mapped and not request_type_cell):
                    skipped += 1
                    continue

                ags_tokens = [v for v in AGS_SPLIT_RE.split(ags_raw) if v] if ags_raw else []
                if not ags_tokens:
                    details.append(ImportRowResult(idx, "NEEDS_REVIEW", "AGS fehlt"))
                    needs_review += 1
                    continue

                invalid_ags = [t for t in ags_tokens if normalize_ags(t) is None]
                if invalid_ags:
                    details.append(ImportRowResult(
                        idx, "NEEDS_REVIEW", f"AGS ungültig: {', '.join(invalid_ags)}"
                    ))
                    needs_review += 1
                    continue
                ags_values = [normalize_ags(t) for t in ags_tokens]

                if request_type_cell:
                    row_request_type_id = resolve_request_type(request_type_cell)
                    if row_request_type_id is None:
                        details.append(ImportRowResult(
                            idx, "NEEDS_REVIEW", f"Auskunftsart unbekannt: {request_type_cell}"
                        ))
                        needs_review += 1
                        continue
                else:
                    row_request_type_id = default_request_type_id
                    if row_request_type_id is None:
                        details.append(ImportRowResult(idx, "NEEDS_REVIEW", "Auskunftsart fehlt"))
                        needs_review += 1
                        continue

                city = mapped(row, "city")
                key = (name, city)
                authority_id = authority_ids_by_key.get(key)

                if authority_id is None:
                    authority_id = str(uuid.uuid4())
                    authority = Authority(
                        authority_id=authority_id,
                        authority_name=name,
                        city=city,
                        source=mapped(row, "source") or "Import",
                    )
                    self.db.add(authority)
                    authority_ids_by_key[key] = authority_id
                    batch_authority_cache[authority_id] = authority
                else:
                    authority = batch_authority_cache.get(authority_id)
                    if authority is None:
                        authority = self.db.query(Authority).filter(Authority.authority_id == authority_id).first()
                        batch_authority_cache[authority_id] = authority

                for contact_field in (
                    "department_name", "street", "house_number", "postal_code",
                    "state", "email", "phone", "website",
                ):
                    value = mapped(row, contact_field)
                    if value:
                        setattr(authority, contact_field, value)

                priority = mapped(row, "priority")
                explicit_matching_level = mapped(row, "matching_level")
                existing_jurisdictions = existing_jurisdictions_for(row_request_type_id)

                new_count = dup_count = 0
                for ags in ags_values:
                    jkey = (authority_id, ags)
                    if jkey in existing_jurisdictions:
                        dup_count += 1
                        continue

                    jurisdiction = Jurisdiction(
                        jurisdiction_id=str(uuid.uuid4()),
                        request_type_id=row_request_type_id,
                        authority_id=authority_id,
                        ags=ags,
                        municipality=mapped(row, "municipality"),
                        priority=int(priority) if priority else default_priority,
                        matching_level=explicit_matching_level or infer_matching_level(ags, default_matching_level),
                        source=mapped(row, "source") or "Import",
                        notes=mapped(row, "notes"),
                    )
                    self.db.add(jurisdiction)
                    existing_jurisdictions.add(jkey)
                    new_count += 1

                if new_count == 0:
                    details.append(
                        ImportRowResult(idx, "DUPLICATE", f"Alle {dup_count} AGS bereits verknüpft")
                    )
                    duplicates += 1
                else:
                    msg = f"{new_count} AGS verknüpft"
                    if dup_count:
                        msg += f" ({dup_count} bereits vorhanden)"
                    details.append(ImportRowResult(idx, "IMPORTED", msg))
                    imported += 1

                pending += 1

            except Exception as exc:
                details.append(ImportRowResult(idx, "ERROR", str(exc)))
                errors += 1

            if pending >= self._IMPORT_BATCH_SIZE:
                self.db.commit()
                self.db.expunge_all()
                batch_authority_cache.clear()
                pending = 0

        self.db.commit()

        return ImportSummary(
            total_rows=len(df),
            imported=imported,
            duplicates=duplicates,
            needs_review=needs_review,
            errors=errors,
            skipped=skipped,
            details=details,
        )

    # Felder, die bei fill_gaps=True auf bestehenden Behörden nachgetragen werden dürfen.
    _FILLABLE_AUTHORITY_FIELDS = (
        "department_name", "street", "house_number", "postal_code", "city", "state",
        "email", "phone", "website",
    )

    # Nach so vielen verarbeiteten Zeilen wird zwischen-committet und der
    # SQLAlchemy-Session-Cache geleert – bei mehreren tausend Zeilen sonst
    # ein Speicher- und Transaktions-Risiko (insb. auf speicherbegrenzten
    # Hosting-Instanzen).
    _IMPORT_BATCH_SIZE = 200

    def import_authorities(self, df: pd.DataFrame, mapping: dict, fill_gaps: bool = False) -> ImportSummary:
        """
        Importiert Behörden. Pflichtfeld: authority_name.

        fill_gaps=True (nur Haupt-Account): bei einer bereits existierenden
        Behörde (gleicher Name + Ort) werden NUR aktuell leere Felder aus der
        importierten Zeile nachgetragen (z.B. eine recherchierte E-Mail-
        Adresse) – bereits vorhandene Werte werden nie überschrieben.

        Arbeitet bewusst mit Bulk-Operationen (eine Sammel-Anfrage statt
        einer pro Zeile): bei mehreren tausend Zeilen und einer entfernten
        Datenbank (Neon) summieren sich einzelne Round-Trips sonst zu Minuten
        und riskieren einen Timeout/Absturz auf speicherbegrenzten Hosts.
        """
        details: List[ImportRowResult] = []
        imported = duplicates = needs_review = errors = updated = 0

        # Leichtgewichtiger Lookup (nur IDs, keine vollen ORM-Objekte).
        existing_ids_by_key = {
            (name, city): authority_id
            for authority_id, name, city in self.db.query(
                Authority.authority_id, Authority.authority_name, Authority.city
            ).all()
        }

        # Unlokalisierte Bestandsbehörden (weder Straße noch Ort hinterlegt)
        # zusätzlich nur über den Namen auffindbar machen: sonst würde ein
        # fill_gaps-Import, der für so eine Behörde erstmals eine Adresse
        # mitbringt, die bestehende Zeile über den Name+Ort-Schlüssel nicht
        # finden (Ort war ja bisher leer) und fälschlich eine zweite,
        # doppelte Behörde anlegen. Nur eindeutige Fälle (genau eine
        # unlokalisierte Behörde mit diesem Namen) werden so verknüpft.
        unlocated_ids_by_name: dict = {}
        _ambiguous_names: set = set()
        for authority_id, name in self.db.query(Authority.authority_id, Authority.authority_name).filter(
            or_(Authority.city.is_(None), Authority.city == ""),
            or_(Authority.street.is_(None), Authority.street == ""),
        ).all():
            if name in unlocated_ids_by_name:
                _ambiguous_names.add(name)
            else:
                unlocated_ids_by_name[name] = authority_id
        for name in _ambiguous_names:
            unlocated_ids_by_name.pop(name, None)

        # ---------- Pass 1: Zeilen klassifizieren, ohne DB-Zugriffe ----------
        new_rows: List[tuple] = []  # (idx, name, city, row)
        duplicate_candidates: List[tuple] = []  # (idx, existing_id, name, city, row)

        for idx, row in df.iterrows():
            try:
                name = row.get(mapping.get("authority_name", ""), "").strip()
                city = row.get(mapping.get("city", ""), "").strip() or None

                if not name:
                    details.append(ImportRowResult(idx, "NEEDS_REVIEW", "authority_name fehlt"))
                    needs_review += 1
                    continue

                existing_id = existing_ids_by_key.get((name, city))
                if existing_id is None and city and fill_gaps:
                    existing_id = unlocated_ids_by_name.get(name)
                if existing_id is not None:
                    if not fill_gaps:
                        details.append(ImportRowResult(idx, "DUPLICATE", f"'{name}' in '{city}' existiert bereits"))
                        duplicates += 1
                        continue
                    duplicate_candidates.append((idx, existing_id, name, city, row))
                else:
                    new_rows.append((idx, name, city, row))

            except Exception as exc:
                details.append(ImportRowResult(idx, "ERROR", str(exc)))
                errors += 1

        # ---------- Pass 2: betroffene bestehende Behörden in EINER Anfrage laden ----------
        authorities_by_id = {}
        needed_ids = list({c[1] for c in duplicate_candidates})
        for i in range(0, len(needed_ids), 1000):
            chunk = needed_ids[i:i + 1000]
            for a in self.db.query(Authority).filter(Authority.authority_id.in_(chunk)).all():
                authorities_by_id[a.authority_id] = a

        # ---------- Pass 3: Lücken-Updates im Speicher berechnen ----------
        # WICHTIG: "filled_fields" hier ist nur eine Prognose für die
        # Nutzer-Rückmeldung, basierend auf dem Pass-2-Schnappschuss. Ob ein
        # Feld beim tatsächlichen Schreiben (Pass 5) wirklich noch leer ist,
        # prüft die UPDATE-Anweisung selbst am aktuellen Datenbankstand -
        # siehe Kommentar dort (Race Condition zwischen parallelem manuellem
        # Bearbeiten und diesem Import, siehe Auditbericht).
        now = datetime.utcnow()
        update_params: List[dict] = []
        for idx, existing_id, name, city, row in duplicate_candidates:
            existing = authorities_by_id.get(existing_id)
            if existing is None:
                details.append(ImportRowResult(idx, "ERROR", "Behörde nicht mehr gefunden"))
                errors += 1
                continue

            filled_fields = []
            row_values = {}
            for field_name in self._FILLABLE_AUTHORITY_FIELDS:
                new_value = row.get(mapping.get(field_name, ""), "").strip() or None
                row_values[field_name] = new_value
                if new_value and not getattr(existing, field_name):
                    filled_fields.append(field_name)

            if filled_fields:
                update_params.append({"authority_id": existing_id, **row_values})
                details.append(ImportRowResult(
                    idx, "UPDATED",
                    f"Ergänzt, sofern beim Schreiben noch leer: {', '.join(filled_fields)}",
                ))
                updated += 1
            else:
                details.append(ImportRowResult(idx, "DUPLICATE", f"'{name}' in '{city}' hatte keine Lücken zu füllen"))
                duplicates += 1

        # ---------- Pass 4: neue Behörden vorbereiten ----------
        insert_mappings: List[dict] = []
        for idx, name, city, row in new_rows:
            insert_mappings.append({
                "authority_id": str(uuid.uuid4()),
                "authority_name": name,
                "department_name": row.get(mapping.get("department_name", ""), "").strip() or None,
                "street": row.get(mapping.get("street", ""), "").strip() or None,
                "house_number": row.get(mapping.get("house_number", ""), "").strip() or None,
                "postal_code": row.get(mapping.get("postal_code", ""), "").strip() or None,
                "city": city,
                "state": row.get(mapping.get("state", ""), "").strip() or None,
                "email": row.get(mapping.get("email", ""), "").strip() or None,
                "phone": row.get(mapping.get("phone", ""), "").strip() or None,
                "website": row.get(mapping.get("website", ""), "").strip() or None,
                "source": row.get(mapping.get("source", ""), "").strip() or "Import",
                "active": True,
                "created_at": now,
                "updated_at": now,
            })
            details.append(ImportRowResult(idx, "IMPORTED", "OK"))
            imported += 1

        # ---------- Pass 5: in Batches schreiben (wenige Sammel-Anfragen statt vieler Einzelnen) ----------
        # Bewusst KEIN bulk_update_mappings für die Lücken-Updates: das würde
        # den in Pass 3 im Speicher berechneten Wert blind schreiben, selbst
        # wenn das Feld zwischen dem Einlesen (Pass 2) und dem tatsächlichen
        # Schreiben (hier) durch eine parallele manuelle Bearbeitung bereits
        # gefüllt wurde - eine reale, im Auditbericht dokumentierte Race
        # Condition. Stattdessen prüft die UPDATE-Anweisung selbst den zum
        # Schreibzeitpunkt AKTUELLEN Spaltenwert per COALESCE(NULLIF(...)):
        # nur wenn die Spalte JETZT noch leer ist, wird der Importwert
        # gesetzt; eine zwischenzeitliche, ggf. bessere manuelle Eingabe
        # bleibt unangetastet. Alle Zeilen eines Batches teilen sich dieselbe
        # Anweisungsform (ein "executemany"), das bleibt so schnell wie zuvor.
        if update_params:
            authority_table = Authority.__table__
            set_values = {
                field_name: func.coalesce(func.nullif(authority_table.c[field_name], ""), bindparam(field_name))
                for field_name in self._FILLABLE_AUTHORITY_FIELDS
            }
            set_values["updated_at"] = now
            # Core-Table-Update (nicht update(Authority) auf der ORM-Klasse):
            # ein ORM-Bulk-Update mit zusätzlicher WHERE-Bedingung verlangt in
            # SQLAlchemy 2.0 eine explizite synchronize_session-Strategie und
            # würde versuchen, geladene ORM-Objekte im Session-Identity-Map
            # abzugleichen - hier unnötig, da wir (wie zuvor bei
            # bulk_update_mappings) bewusst ohne ORM-Identity-Map-Refresh
            # schreiben.
            stmt = (
                update(authority_table)
                .where(authority_table.c.authority_id == bindparam("target_id"))
                .values(**set_values)
            )

            for i in range(0, len(update_params), self._IMPORT_BATCH_SIZE):
                batch = update_params[i:i + self._IMPORT_BATCH_SIZE]
                exec_params = [
                    {**{f: p.get(f) for f in self._FILLABLE_AUTHORITY_FIELDS}, "target_id": p["authority_id"]}
                    for p in batch
                ]
                self.db.execute(stmt, exec_params)
                self.db.commit()

        for i in range(0, len(insert_mappings), self._IMPORT_BATCH_SIZE):
            self.db.bulk_insert_mappings(Authority, insert_mappings[i:i + self._IMPORT_BATCH_SIZE])
            self.db.commit()

        details.sort(key=lambda d: d.row_index)

        return ImportSummary(
            total_rows=len(df),
            imported=imported,
            duplicates=duplicates,
            needs_review=needs_review,
            errors=errors,
            updated=updated,
            details=details,
        )
