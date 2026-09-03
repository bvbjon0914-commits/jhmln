"""
DocumentGenerationService

Generiert Word-Anschreiben aus Vorlagen (docxtpl), befüllt mit
Gebäude- und Behördendaten.
"""

import os
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Optional

from docxtpl import DocxTemplate

from app.models.authority import Authority
from app.models.building import Building
from app.models.request_type import RequestType


@dataclass
class GeneratedDocument:
    request_type_id: str
    authority_id: str
    filename: str
    filepath: str


class DocumentGenerationError(Exception):
    """Wird geworfen, wenn ein Dokument nicht generiert werden konnte."""
    pass


class DocumentGenerationService:
    """
    Erstellt DOCX-Anschreiben aus Vorlagen.

    Jede Auskunftsart hat eine eigene Vorlage unter TEMPLATES_DIR,
    die Platzhalter im Jinja2-Format enthält (z.B. {{ authority_name }}).
    """

    def __init__(self, templates_dir: str, output_dir: str):
        self.templates_dir = Path(templates_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _sanitize_filename_part(value: Optional[str]) -> str:
        """Entfernt Zeichen, die in Dateinamen nicht erlaubt sind."""
        if not value:
            return "unbekannt"
        # Nur Buchstaben, Zahlen, Unterstrich und Bindestrich erlauben
        cleaned = re.sub(r"[^\w\-]", "_", value, flags=re.UNICODE)
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")
        return cleaned or "unbekannt"

    def build_filename(self, building: Building, request_type: RequestType, aktenzeichen: str) -> str:
        """
        Erzeugt den Dateinamen im Format:
        {Objekt-ID}_{Auskunft}_{Ort}_{Datum}_{Aktenzeichen}.docx

        Das Aktenzeichen ist je Item eindeutig und stabil - behebt nebenbei,
        dass eine erneute Generierung am selben Tag für dasselbe Gebäude+
        Auskunftsart bisher die vorherige Datei stillschweigend überschrieb.
        """
        object_id = self._sanitize_filename_part(building.building_id)
        request_code = self._sanitize_filename_part(request_type.code)
        city = self._sanitize_filename_part(building.city)
        today = date.today().strftime("%Y-%m-%d")
        az = self._sanitize_filename_part(aktenzeichen)

        return f"{object_id}_{request_code}_{city}_{today}_{az}.docx"

    def build_context(
        self, building: Building, authority: Authority, request_type: RequestType, aktenzeichen: str
    ) -> dict:
        """Stellt den Platzhalter-Kontext für die Vorlage zusammen."""
        return {
            # Behördendaten
            "authority_name": authority.authority_name or "",
            "authority_department": authority.department_name or "",
            "authority_street": authority.street or "",
            "authority_house_number": authority.house_number or "",
            "authority_postal_code": authority.postal_code or "",
            "authority_city": authority.city or "",
            "authority_email": authority.email or "",
            "authority_phone": authority.phone or "",

            # Gebäudedaten
            "building_street": building.street or "",
            "building_house_number": building.house_number or "",
            "building_postal_code": building.postal_code or "",
            "building_city": building.city or "",
            "building_state": building.state or "",
            "building_id": building.building_id or "",
            "internal_reference": building.internal_reference or "",
            "property_name": building.property_name or "",

            # Metadaten
            "current_date": date.today().strftime("%d.%m.%Y"),
            "request_type_name": request_type.name or "",
            "aktenzeichen": aktenzeichen or "",
        }

    def generate_document(
        self,
        building: Building,
        authority: Authority,
        request_type: RequestType,
        aktenzeichen: str,
    ) -> GeneratedDocument:
        """
        Generiert ein einzelnes DOCX-Dokument.

        Wirft DocumentGenerationError, wenn die Vorlage fehlt oder
        die Generierung fehlschlägt - es wird NIE ein leeres oder
        halb-befülltes Dokument stillschweigend zurückgegeben.
        """
        if not request_type.template_filename:
            raise DocumentGenerationError(
                f"Für Auskunftsart '{request_type.request_type_id}' ist keine Vorlage hinterlegt."
            )

        template_path = self.templates_dir / request_type.template_filename
        if not template_path.exists():
            raise DocumentGenerationError(f"Vorlage nicht gefunden: {template_path}")

        try:
            doc = DocxTemplate(str(template_path))
            context = self.build_context(building, authority, request_type, aktenzeichen)
            doc.render(context)
        except Exception as exc:
            raise DocumentGenerationError(f"Fehler beim Rendern der Vorlage: {exc}") from exc

        filename = self.build_filename(building, request_type, aktenzeichen)
        output_path = self.output_dir / filename

        try:
            doc.save(str(output_path))
        except Exception as exc:
            raise DocumentGenerationError(f"Fehler beim Speichern des Dokuments: {exc}") from exc

        return GeneratedDocument(
            request_type_id=request_type.request_type_id,
            authority_id=authority.authority_id,
            filename=filename,
            filepath=str(output_path),
        )
