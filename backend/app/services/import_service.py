"""
ImportService

Importiert Gebäude-, Behörden- und Zuständigkeitsdaten aus CSV/Excel.

Wichtiges Prinzip: Es wird NIE geraten. Wenn eine Zeile nicht eindeutig
zugeordnet werden kann (z.B. mehrdeutiger Gemeindename ohne Kreis-Angabe),
landet sie im "needs_review"-Topf statt automatisch verknüpft zu werden.
"""

import io
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import pandas as pd
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.authority import Authority
from app.models.building import Building
from app.models.jurisdiction import Jurisdiction

AGS_SPLIT_RE = re.compile(r"[,;/\s]+")


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
    details: List[ImportRowResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_rows": self.total_rows,
            "imported": self.imported,
            "duplicates": self.duplicates,
            "needs_review": self.needs_review,
            "errors": self.errors,
            "updated": self.updated,
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

    def import_buildings(self, df: pd.DataFrame, mapping: dict) -> ImportSummary:
        """
        Importiert Gebäude.

        mapping: {"db_field": "csv_column", ...}
        Pflichtfelder: street, house_number, city (PLZ optional)
        """
        required_fields = ["street", "house_number", "city"]
        details: List[ImportRowResult] = []
        imported = duplicates = needs_review = errors = 0

        existing_refs = {
            b.internal_reference for b in self.db.query(Building.internal_reference).all() if b.internal_reference
        }

        for idx, row in df.iterrows():
            try:
                missing = [f for f in required_fields if not row.get(mapping.get(f, ""), "").strip()]
                if missing:
                    details.append(ImportRowResult(idx, "NEEDS_REVIEW", f"Pflichtfelder fehlen: {missing}"))
                    needs_review += 1
                    continue

                internal_reference = row.get(mapping.get("internal_reference", ""), "").strip() or None

                if internal_reference and internal_reference in existing_refs:
                    details.append(ImportRowResult(idx, "DUPLICATE", f"Referenz '{internal_reference}' existiert bereits"))
                    duplicates += 1
                    continue

                building = Building(
                    building_id=str(uuid.uuid4()),
                    street=row[mapping["street"]].strip(),
                    house_number=row[mapping["house_number"]].strip(),
                    postal_code=row.get(mapping.get("postal_code", ""), "").strip() or None,
                    city=row[mapping["city"]].strip(),
                    district=row.get(mapping.get("district", ""), "").strip() or None,
                    state=row.get(mapping.get("state", ""), "").strip() or None,
                    ags=row.get(mapping.get("ags", ""), "").strip() or None,
                    property_name=row.get(mapping.get("property_name", ""), "").strip() or None,
                    internal_reference=internal_reference,
                )
                self.db.add(building)
                if internal_reference:
                    existing_refs.add(internal_reference)

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

    def import_jurisdictions(
        self,
        df: pd.DataFrame,
        mapping: dict,
        request_type_id: str,
        default_priority: int = 40,
        default_matching_level: str = "MUNICIPALITY",
    ) -> ImportSummary:
        """
        Importiert Zuständigkeiten: pro Zeile eine Behörde (Kontaktdaten werden
        upgeserted, da dieselbe Behörde über mehrere Zeilen/AGS wiederholt sein kann)
        und ein oder mehrere AGS-Schlüssel (Zelle darf mehrere, getrennt durch
        Komma/Semikolon/Leerzeichen, enthalten).

        Pflichtfelder im Mapping: authority_name, ags.
        request_type_id gilt für den gesamten Import-Lauf (eine Datei = eine
        Auskunftsart), da die Auskunftsarten ein festes Set sind.
        """
        details: List[ImportRowResult] = []
        imported = duplicates = needs_review = errors = 0

        # Leichtgewichtiger Lookup (nur IDs) statt voller ORM-Objekte für
        # alle Behörden – siehe import_authorities für die Begründung.
        authority_ids_by_key = {
            (name, city): authority_id
            for authority_id, name, city in self.db.query(
                Authority.authority_id, Authority.authority_name, Authority.city
            ).all()
        }
        existing_jurisdictions = {
            (j.authority_id, j.ags)
            for j in self.db.query(Jurisdiction.authority_id, Jurisdiction.ags).filter(
                Jurisdiction.request_type_id == request_type_id
            )
        }
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

                if not name or not ags_raw:
                    details.append(
                        ImportRowResult(idx, "NEEDS_REVIEW", "authority_name oder ags fehlt")
                    )
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

                ags_values = [v for v in AGS_SPLIT_RE.split(ags_raw) if v]
                priority = mapped(row, "priority")
                matching_level = mapped(row, "matching_level") or default_matching_level

                new_count = dup_count = 0
                for ags in ags_values:
                    jkey = (authority_id, ags)
                    if jkey in existing_jurisdictions:
                        dup_count += 1
                        continue

                    jurisdiction = Jurisdiction(
                        jurisdiction_id=str(uuid.uuid4()),
                        request_type_id=request_type_id,
                        authority_id=authority_id,
                        ags=ags,
                        municipality=mapped(row, "municipality"),
                        priority=int(priority) if priority else default_priority,
                        matching_level=matching_level,
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
        now = datetime.utcnow()
        update_mappings: List[dict] = []
        for idx, existing_id, name, city, row in duplicate_candidates:
            existing = authorities_by_id.get(existing_id)
            if existing is None:
                details.append(ImportRowResult(idx, "ERROR", "Behörde nicht mehr gefunden"))
                errors += 1
                continue

            filled_fields = []
            patch = {"authority_id": existing_id}
            for field_name in self._FILLABLE_AUTHORITY_FIELDS:
                if getattr(existing, field_name):
                    continue
                new_value = row.get(mapping.get(field_name, ""), "").strip()
                if new_value:
                    patch[field_name] = new_value
                    filled_fields.append(field_name)

            if filled_fields:
                patch["updated_at"] = now
                update_mappings.append(patch)
                details.append(ImportRowResult(idx, "UPDATED", f"Ergänzt: {', '.join(filled_fields)}"))
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
        for i in range(0, len(update_mappings), self._IMPORT_BATCH_SIZE):
            self.db.bulk_update_mappings(Authority, update_mappings[i:i + self._IMPORT_BATCH_SIZE])
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
