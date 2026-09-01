"""
AddressNormalizer Service

Normalisiert Adressdaten, damit das Matching konsistent funktioniert,
unabhängig von Schreibweise, Groß-/Kleinschreibung oder Abkürzungen.
"""

import re
from dataclasses import dataclass, field
from typing import Optional


# Häufige Straßenabkürzungen -> vollständige Form
STREET_ABBREVIATIONS = {
    r"\bstr\.?\b": "straße",
    r"\bstrasse\b": "straße",
    r"\bpl\.?\b": "platz",
    r"\ballee\b": "allee",
    r"\bweg\b": "weg",
}

# Häufige Rechtsform-/Ortszusätze, die für den Namensvergleich ignoriert werden
CITY_NOISE_PATTERNS = [
    r"\bstadt\b",
    r"\bgemeinde\b",
    r"\bkreisfreie stadt\b",
]


@dataclass
class NormalizedAddress:
    """Ergebnis der Adressnormalisierung."""

    street: str
    house_number: str
    house_number_suffix: str
    postal_code: Optional[str]
    city: str
    district: Optional[str]
    quality_flags: list = field(default_factory=list)

    def is_complete(self) -> bool:
        return "MISSING_POSTAL_CODE" not in self.quality_flags and "MISSING_CITY" not in self.quality_flags


class AddressNormalizer:
    """
    Normalisiert Adressbestandteile für ein konsistentes Matching.

    Diese Klasse verändert NIE die Originaldaten in der Datenbank,
    sondern erzeugt nur eine normalisierte Sicht für den Matching-Vorgang.
    """

    @staticmethod
    def _strip_and_collapse_whitespace(value: str) -> str:
        """Entfernt führende/nachgestellte Leerzeichen und mehrfache Leerzeichen."""
        if not value:
            return ""
        return re.sub(r"\s+", " ", value.strip())

    @staticmethod
    def _title_case_german(value: str) -> str:
        """
        Wendet deutsche Groß-/Kleinschreibung an (erster Buchstabe jedes
        Wortes groß), ohne Umlaute oder ß zu verändern.
        """
        if not value:
            return ""
        return " ".join(word[:1].upper() + word[1:].lower() if word else "" for word in value.split(" "))

    @staticmethod
    def normalize_street(street: str) -> str:
        """
        Normalisiert einen Straßennamen:
        - Leerzeichen bereinigen
        - Abkürzungen auflösen (Str. -> Straße)
        - Groß-/Kleinschreibung vereinheitlichen
        """
        if not street:
            return ""

        normalized = AddressNormalizer._strip_and_collapse_whitespace(street)
        normalized_lower = normalized.lower()

        for pattern, replacement in STREET_ABBREVIATIONS.items():
            normalized_lower = re.sub(pattern, replacement, normalized_lower, flags=re.IGNORECASE)

        # Zusammengeschriebene Straßennamen mit "straße" am Ende sauber behandeln
        # z.B. "musterstr" (ohne Punkt) -> "musterstraße"
        normalized_lower = re.sub(r"(\w)str\b(?!aße)", r"\1straße", normalized_lower)

        return AddressNormalizer._title_case_german(normalized_lower)

    @staticmethod
    def split_house_number(house_number: str) -> tuple[str, str]:
        """
        Trennt Hausnummer und Zusatz.

        Beispiele:
            "12"     -> ("12", "")
            "12a"    -> ("12", "a")
            "12 a"   -> ("12", "a")
            "12-14"  -> ("12-14", "")   # Bereichsangaben bleiben zusammen
        """
        if not house_number:
            return "", ""

        value = AddressNormalizer._strip_and_collapse_whitespace(house_number)

        # Bereichsangaben (12-14) nicht aufsplitten
        if re.match(r"^\d+\s*-\s*\d+$", value):
            return value.replace(" ", ""), ""

        match = re.match(r"^(\d+)\s*([a-zA-Z]?)$", value)
        if match:
            number, suffix = match.groups()
            return number, suffix.lower()

        # Fallback: konnte nicht sauber geparst werden, unverändert zurückgeben
        return value, ""

    @staticmethod
    def normalize_city(city: str) -> str:
        """Normalisiert einen Ortsnamen (Groß-/Kleinschreibung, Leerzeichen)."""
        if not city:
            return ""
        normalized = AddressNormalizer._strip_and_collapse_whitespace(city)
        return AddressNormalizer._title_case_german(normalized.lower())

    @staticmethod
    def normalize_district(district: Optional[str]) -> Optional[str]:
        """Normalisiert einen Stadtteil-/Bezirksnamen."""
        if not district:
            return None
        normalized = AddressNormalizer._strip_and_collapse_whitespace(district)
        return AddressNormalizer._title_case_german(normalized.lower())

    @staticmethod
    def validate_postal_code(postal_code: Optional[str]) -> Optional[str]:
        """
        Validiert eine deutsche Postleitzahl (5 Ziffern).
        Gibt None zurück, wenn ungültig.
        """
        if not postal_code:
            return None

        cleaned = re.sub(r"\s+", "", postal_code)

        if re.match(r"^\d{5}$", cleaned):
            return cleaned

        return None

    @classmethod
    def normalize(
        cls,
        street: str,
        house_number: str,
        city: str,
        postal_code: Optional[str] = None,
        district: Optional[str] = None,
    ) -> NormalizedAddress:
        """
        Führt die vollständige Normalisierung einer Adresse durch.

        Wirft niemals eine Exception bei unvollständigen Daten -
        stattdessen werden quality_flags gesetzt, damit der Aufrufer
        entscheiden kann, wie damit umgegangen wird.
        """
        quality_flags = []

        normalized_street = cls.normalize_street(street)
        if not normalized_street:
            quality_flags.append("MISSING_STREET")

        house_num, suffix = cls.split_house_number(house_number)
        if not house_num:
            quality_flags.append("MISSING_HOUSE_NUMBER")

        normalized_city = cls.normalize_city(city)
        if not normalized_city:
            quality_flags.append("MISSING_CITY")

        normalized_postal_code = cls.validate_postal_code(postal_code)
        if postal_code and not normalized_postal_code:
            quality_flags.append("INVALID_POSTAL_CODE")
        elif not postal_code:
            quality_flags.append("MISSING_POSTAL_CODE")

        normalized_district = cls.normalize_district(district)

        if not quality_flags:
            quality_flags.append("COMPLETE")

        return NormalizedAddress(
            street=normalized_street,
            house_number=house_num,
            house_number_suffix=suffix,
            postal_code=normalized_postal_code,
            city=normalized_city,
            district=normalized_district,
            quality_flags=quality_flags,
        )
