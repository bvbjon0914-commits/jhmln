"""
Tests fuer die automatische Absenderdaten-Befuellung (Name, Telefon,
E-Mail, Funktion, Adresse) aus dem eingeloggten Nutzer-Account in
generierten Dokumenten.
"""
from docx import Document

from app.config import TEMPLATES_DIR
from app.services.document_generator import DocumentGenerationService
from tests.conftest import make_authority, make_building, make_request_type, make_user


class TestBuildContextSenderFields:
    def test_with_sender_includes_personal_fields(self, db_session, tmp_path):
        service = DocumentGenerationService(templates_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        building = make_building(db_session)
        authority = make_authority(db_session)
        request_type = make_request_type(db_session)
        sender = make_user(
            db_session, email="anna@example.com", full_name="Anna Muster",
            phone="0234 123456", function="Sachbearbeiterin",
            street="Kortumstraße", house_number="10", postal_code="44787", city="Bochum",
        )

        context = service.build_context(building, authority, request_type, "AZ-1", sender=sender)

        assert context["sender_name"] == "Anna Muster"
        assert context["sender_phone"] == "0234 123456"
        assert context["sender_email"] == "anna@example.com"
        assert context["sender_function"] == "Sachbearbeiterin"
        assert context["sender_street"] == "Kortumstraße"
        assert context["sender_house_number"] == "10"
        assert context["sender_postal_code"] == "44787"
        assert context["sender_city"] == "Bochum"

    def test_without_sender_returns_empty_strings_not_exception(self, db_session, tmp_path):
        service = DocumentGenerationService(templates_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        building = make_building(db_session)
        authority = make_authority(db_session)
        request_type = make_request_type(db_session)

        context = service.build_context(building, authority, request_type, "AZ-1", sender=None)

        assert context["sender_name"] == ""
        assert context["sender_phone"] == ""
        assert context["sender_email"] == ""
        assert context["sender_function"] == ""
        assert context["sender_street"] == ""


class TestGeneratedDocumentContainsSenderData:
    def test_generated_docx_contains_real_sender_values(self, db_session, tmp_path):
        service = DocumentGenerationService(templates_dir=TEMPLATES_DIR, output_dir=str(tmp_path))
        building = make_building(db_session)
        authority = make_authority(db_session)
        request_type = make_request_type(db_session, code="GRUNDBUCH")
        sender = make_user(
            db_session, email="anna@example.com", full_name="Anna Muster",
            phone="0234 123456", function="Sachbearbeiterin",
        )

        result = service.generate_document(building, authority, request_type, "AZ-1", sender=sender)

        doc = Document(result.filepath)
        full_text = "\n".join(p.text for p in doc.paragraphs)

        assert "Anna Muster" in full_text
        assert "0234 123456" in full_text
        assert "Sachbearbeiterin" in full_text
        # Wenn die Vorlage nicht neu generiert wurde, waere hier noch das
        # literale Jinja-Platzhalter-Tag zu sehen statt eines echten Werts.
        assert "{{ sender_name }}" not in full_text
