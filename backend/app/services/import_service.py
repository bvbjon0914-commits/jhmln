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
from typing import List, Optional

import pandas as pd
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
    def read_file(file_content: bytes, filename: str) -> pd.DataFrame:
        """Liest eine CSV- oder Excel-Datei in einen DataFrame ein."""
        if filename.lower().endswith(".csv"):
            return pd.read_csv(io.BytesIO(file_content), dtype=str, keep_default_na=False)
        elif filename.lower().endswith((".xlsx", ".xls")):
            return pd.read_excel(io.BytesIO(file_content), dtype=str)
        else:
            raise ValueError(f"Nicht unterstütztes Dateiformat: {filename}")

    def preview(self, df: pd.DataFrame, max_rows: int = 5) -> dict:
        """Gibt eine Vorschau der ersten Zeilen zurück."""
        return {
            "total_rows": len(df),
            "columns": list(df.columns),
            "preview_rows": df.head(max_rows).to_dict(orient="records"),
        }

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

        authorities_by_key = {
            (a.authority_name, a.city): a
            for a in self.db.query(Authority).all()
        }
        existing_jurisdictions = {
            (j.authority_id, j.ags)
            for j in self.db.query(Jurisdiction.authority_id, Jurisdiction.ags).filter(
                Jurisdiction.request_type_id == request_type_id
            )
        }

        def mapped(row, field_name: str) -> Optional[str]:
            col = mapping.get(field_name, "")
            if not col:
                return None
            value = str(row.get(col, "")).strip()
            return value or None

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
                authority = authorities_by_key.get(key)

                if authority is None:
                    authority = Authority(
                        authority_id=str(uuid.uuid4()),
                        authority_name=name,
                        city=city,
                        source=mapped(row, "source") or "Import",
                    )
                    self.db.add(authority)
                    authorities_by_key[key] = authority

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
                    jkey = (authority.authority_id, ags)
                    if jkey in existing_jurisdictions:
                        dup_count += 1
                        continue

                    jurisdiction = Jurisdiction(
                        jurisdiction_id=str(uuid.uuid4()),
                        request_type_id=request_type_id,
                        authority_id=authority.authority_id,
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

    # Felder, die bei fill_gaps=True auf bestehenden Behörden nachgetragen werden dürfen.
    _FILLABLE_AUTHORITY_FIELDS = (
        "department_name", "street", "house_number", "postal_code", "state",
        "email", "phone", "website",
    )

    def import_authorities(self, df: pd.DataFrame, mapping: dict, fill_gaps: bool = False) -> ImportSummary:
        """
        Importiert Behörden. Pflichtfeld: authority_name.

        fill_gaps=True (nur Haupt-Account): bei einer bereits existierenden
        Behörde (gleicher Name + Ort) werden NUR aktuell leere Felder aus der
        importierten Zeile nachgetragen (z.B. eine recherchierte E-Mail-
        Adresse) – bereits vorhandene Werte werden nie überschrieben.
        """
        details: List[ImportRowResult] = []
        imported = duplicates = needs_review = errors = updated = 0

        existing_by_key = {
            (a.authority_name, a.city): a
            for a in self.db.query(Authority).all()
        }

        for idx, row in df.iterrows():
            try:
                name = row.get(mapping.get("authority_name", ""), "").strip()
                city = row.get(mapping.get("city", ""), "").strip() or None

                if not name:
                    details.append(ImportRowResult(idx, "NEEDS_REVIEW", "authority_name fehlt"))
                    needs_review += 1
                    continue

                existing = existing_by_key.get((name, city))
                if existing is not None:
                    if not fill_gaps:
                        details.append(ImportRowResult(idx, "DUPLICATE", f"'{name}' in '{city}' existiert bereits"))
                        duplicates += 1
                        continue

                    filled_fields = []
                    for field_name in self._FILLABLE_AUTHORITY_FIELDS:
                        current_value = getattr(existing, field_name)
                        if current_value:
                            continue
                        new_value = row.get(mapping.get(field_name, ""), "").strip()
                        if new_value:
                            setattr(existing, field_name, new_value)
                            filled_fields.append(field_name)

                    if filled_fields:
                        details.append(
                            ImportRowResult(idx, "UPDATED", f"Ergänzt: {', '.join(filled_fields)}")
                        )
                        updated += 1
                    else:
                        details.append(
                            ImportRowResult(idx, "DUPLICATE", f"'{name}' in '{city}' hatte keine Lücken zu füllen")
                        )
                        duplicates += 1
                    continue

                authority = Authority(
                    authority_id=str(uuid.uuid4()),
                    authority_name=name,
                    department_name=row.get(mapping.get("department_name", ""), "").strip() or None,
                    street=row.get(mapping.get("street", ""), "").strip() or None,
                    house_number=row.get(mapping.get("house_number", ""), "").strip() or None,
                    postal_code=row.get(mapping.get("postal_code", ""), "").strip() or None,
                    city=city,
                    state=row.get(mapping.get("state", ""), "").strip() or None,
                    email=row.get(mapping.get("email", ""), "").strip() or None,
                    phone=row.get(mapping.get("phone", ""), "").strip() or None,
                    website=row.get(mapping.get("website", ""), "").strip() or None,
                    source=row.get(mapping.get("source", ""), "").strip() or "Import",
                )
                self.db.add(authority)
                existing_by_key[(name, city)] = authority

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
            updated=updated,
            details=details,
        )
