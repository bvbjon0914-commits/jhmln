"""
Regressionstests für AddressNormalizer.

Deckt die in docs/PHASE2_MATCHING_ENGINE.md ursprünglich vorgesehenen
Normalisierungsfälle ab (Leerzeichen, Abkürzungen, Groß-/Kleinschreibung,
Hausnummer-Splitting, PLZ-Validierung), die nie als automatisierte Tests
umgesetzt wurden.
"""
from app.services.address_normalizer import AddressNormalizer


class TestNormalizeStreet:
    def test_strips_and_collapses_whitespace(self):
        assert AddressNormalizer.normalize_street("  Musterstraße   12  ") == "Musterstraße 12"

    def test_resolves_str_abbreviation_with_period(self):
        assert AddressNormalizer.normalize_street("Muster Str.") == "Muster Straße"

    def test_resolves_concatenated_str_without_period(self):
        assert AddressNormalizer.normalize_street("Musterstr") == "Musterstraße"

    def test_does_not_mangle_already_full_strasse(self):
        assert AddressNormalizer.normalize_street("Musterstraße") == "Musterstraße"

    def test_normalizes_case(self):
        assert AddressNormalizer.normalize_street("MUSTERSTRASSE") == "Musterstraße"

    def test_empty_input(self):
        assert AddressNormalizer.normalize_street("") == ""
        assert AddressNormalizer.normalize_street(None) == ""


class TestSplitHouseNumber:
    def test_plain_number(self):
        assert AddressNormalizer.split_house_number("12") == ("12", "")

    def test_number_with_letter_suffix_no_space(self):
        assert AddressNormalizer.split_house_number("12a") == ("12", "a")

    def test_number_with_letter_suffix_with_space(self):
        assert AddressNormalizer.split_house_number("12 a") == ("12", "a")

    def test_suffix_lowercased(self):
        assert AddressNormalizer.split_house_number("12A") == ("12", "a")

    def test_range_stays_together(self):
        assert AddressNormalizer.split_house_number("12-14") == ("12-14", "")

    def test_range_with_spaces_stays_together(self):
        assert AddressNormalizer.split_house_number("12 - 14") == ("12-14", "")

    def test_empty_input(self):
        assert AddressNormalizer.split_house_number("") == ("", "")

    def test_unparseable_falls_back_unchanged(self):
        # bewusst kein Raten - unparsebare Eingabe kommt unverändert zurück,
        # nie eine Exception
        assert AddressNormalizer.split_house_number("Erdgeschoss") == ("Erdgeschoss", "")


class TestValidatePostalCode:
    def test_valid_five_digit(self):
        assert AddressNormalizer.validate_postal_code("44787") == "44787"

    def test_strips_whitespace(self):
        assert AddressNormalizer.validate_postal_code(" 44787 ") == "44787"

    def test_invalid_too_short_returns_none(self):
        assert AddressNormalizer.validate_postal_code("447") is None

    def test_invalid_non_numeric_returns_none(self):
        assert AddressNormalizer.validate_postal_code("ABCDE") is None

    def test_empty_returns_none(self):
        assert AddressNormalizer.validate_postal_code("") is None
        assert AddressNormalizer.validate_postal_code(None) is None


class TestNormalizeFullAddress:
    def test_complete_address_has_complete_flag(self):
        result = AddressNormalizer.normalize(
            street="Musterstr.", house_number="12a", city="BOCHUM", postal_code="44787",
        )
        assert result.street == "Musterstraße"
        assert result.house_number == "12"
        assert result.house_number_suffix == "a"
        assert result.city == "Bochum"
        assert result.postal_code == "44787"
        assert result.quality_flags == ["COMPLETE"]
        assert result.is_complete()

    def test_missing_street_flagged(self):
        result = AddressNormalizer.normalize(street="", house_number="12", city="Bochum", postal_code="44787")
        assert "MISSING_STREET" in result.quality_flags

    def test_missing_postal_code_flagged_and_incomplete(self):
        result = AddressNormalizer.normalize(street="Musterstraße", house_number="12", city="Bochum")
        assert "MISSING_POSTAL_CODE" in result.quality_flags
        assert not result.is_complete()

    def test_invalid_postal_code_flagged_distinctly_from_missing(self):
        result = AddressNormalizer.normalize(
            street="Musterstraße", house_number="12", city="Bochum", postal_code="ABC",
        )
        assert "INVALID_POSTAL_CODE" in result.quality_flags
        assert "MISSING_POSTAL_CODE" not in result.quality_flags

    def test_never_raises_on_missing_data(self):
        # Kernprinzip laut Docstring: nie eine Exception bei unvollständigen Daten
        result = AddressNormalizer.normalize(street="", house_number="", city="")
        assert isinstance(result.quality_flags, list)
        assert len(result.quality_flags) > 0
