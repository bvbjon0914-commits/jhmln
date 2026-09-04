"""
Business Logic Services
"""

from .address_normalizer import AddressNormalizer, NormalizedAddress
from .jurisdiction_matcher import JurisdictionMatchingService, MatchingResult, MatchingStatus, MatchingLevel
from .document_generator import DocumentGenerationService, DocumentGenerationError, GeneratedDocument
from .import_service import ImportService, ImportSummary
from .aktenzeichen_service import next_year_number
from .mailgun_service import send_email, MailgunError, SendResult

__all__ = [
    "AddressNormalizer",
    "NormalizedAddress",
    "JurisdictionMatchingService",
    "MatchingResult",
    "MatchingStatus",
    "MatchingLevel",
    "DocumentGenerationService",
    "DocumentGenerationError",
    "GeneratedDocument",
    "ImportService",
    "ImportSummary",
    "next_year_number",
    "send_email",
    "MailgunError",
    "SendResult",
]
