"""
Pydantic Schemas for API Validation
"""

from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ========== Building Schemas ==========

class BuildingBase(BaseModel):
    """Basis-Schema für Gebäude"""
    street: str
    house_number: str
    postal_code: Optional[str] = None
    city: str
    district: Optional[str] = None
    state: Optional[str] = None
    ags: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_name: Optional[str] = None
    internal_reference: Optional[str] = None
    notes: Optional[str] = None


class BuildingCreate(BuildingBase):
    """Schema zum Erstellen eines Gebäudes"""
    building_id: Optional[str] = None


class BuildingUpdate(BaseModel):
    """Schema zum Aktualisieren eines Gebäudes"""
    street: Optional[str] = None
    house_number: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    ags: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    property_name: Optional[str] = None
    internal_reference: Optional[str] = None
    notes: Optional[str] = None


class BuildingResponse(BuildingBase):
    """Antwort-Schema für Gebäude"""
    building_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== RequestType Schemas ==========

class RequestTypeBase(BaseModel):
    """Basis-Schema für Auskunftsarten"""
    code: str
    name: str
    description: Optional[str] = None
    template_filename: Optional[str] = None
    active: bool = True
    notes: Optional[str] = None


class RequestTypeCreate(RequestTypeBase):
    """Schema zum Erstellen einer Auskunftsart"""
    request_type_id: str


class RequestTypeResponse(RequestTypeBase):
    """Antwort-Schema für Auskunftsart"""
    request_type_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Authority Schemas ==========

class AuthorityBase(BaseModel):
    """Basis-Schema für Behörden"""
    authority_name: str
    department_name: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None
    verified_by: Optional[str] = None
    active: bool = True
    notes: Optional[str] = None


class AuthorityCreate(AuthorityBase):
    """Schema zum Erstellen einer Behörde"""
    authority_id: str


class AuthorityUpdate(BaseModel):
    """Schema zum Aktualisieren einer Behörde"""
    authority_name: Optional[str] = None
    department_name: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    postal_code: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    source: Optional[str] = None
    verified_by: Optional[str] = None
    active: Optional[bool] = None
    notes: Optional[str] = None


class AuthorityResponse(AuthorityBase):
    """Antwort-Schema für Behörde"""
    authority_id: str
    last_verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Jurisdiction Schemas ==========

class JurisdictionBase(BaseModel):
    """Basis-Schema für Zuständigkeitsregel"""
    request_type_id: str
    authority_id: str
    country: str = "DE"
    state: Optional[str] = None
    ags: Optional[str] = None
    municipality: Optional[str] = None
    district: Optional[str] = None
    postal_code: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    priority: int = 100
    matching_level: Optional[str] = None
    source: Optional[str] = None
    verified_by: Optional[str] = None
    active: bool = True
    notes: Optional[str] = None


class JurisdictionCreate(JurisdictionBase):
    """Schema zum Erstellen einer Zuständigkeitsregel"""
    jurisdiction_id: str


class JurisdictionUpdate(BaseModel):
    """Schema zum Aktualisieren einer Zuständigkeitsregel"""
    request_type_id: Optional[str] = None
    authority_id: Optional[str] = None
    state: Optional[str] = None
    ags: Optional[str] = None
    municipality: Optional[str] = None
    district: Optional[str] = None
    postal_code: Optional[str] = None
    street: Optional[str] = None
    house_number: Optional[str] = None
    valid_from: Optional[date] = None
    valid_to: Optional[date] = None
    priority: Optional[int] = None
    matching_level: Optional[str] = None
    source: Optional[str] = None
    verified_by: Optional[str] = None
    active: Optional[bool] = None
    notes: Optional[str] = None


class JurisdictionResponse(JurisdictionBase):
    """Antwort-Schema für Zuständigkeitsregel"""
    jurisdiction_id: str
    last_verified_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ========== Matching Schemas ==========

class MatchingResult(BaseModel):
    """Ergebnis eines Matching-Vorgangs"""
    building_id: str
    request_type_id: str
    authority_id: Optional[str] = None
    matching_level: Optional[str] = None
    matching_status: str  # MATCHED, REVIEW_REQUIRED, NO_MATCH, MULTIPLE_MATCHES
    matching_confidence: float = 0.0
    reason: str
    alternative_authorities: List[str] = []

    class Config:
        from_attributes = True


class MatchingRequest(BaseModel):
    """Request zum Starten eines Matching"""
    building_id: str
    request_type_ids: List[str]


class MatchingResponse(BaseModel):
    """Response mit Matching-Ergebnissen"""
    request_id: str
    building_id: str
    results: List[MatchingResult]
    timestamp: datetime


# ========== Document Schemas ==========

class DocumentGenerationRequest(BaseModel):
    """Request zur Dokumentgenerierung"""
    request_id: str


class DocumentInfo(BaseModel):
    """Info über ein generiertes Dokument"""
    request_item_id: str
    request_type_id: str
    authority_id: str
    filename: str
    filepath: str
    status: str  # PENDING, GENERATED, FAILED
    created_at: datetime


class DocumentGenerationResponse(BaseModel):
    """Response nach Dokumentgenerierung"""
    request_id: str
    documents: List[DocumentInfo]
    timestamp: datetime


# ========== Import Schemas ==========

class ImportMapping(BaseModel):
    """Spaltenzuordnung beim Import"""
    csv_column: str
    db_field: str


class ImportPreview(BaseModel):
    """Vorschau der Importdaten"""
    total_rows: int
    preview_rows: List[dict]
    mappings: List[ImportMapping]


class ImportResult(BaseModel):
    """Ergebnis eines Imports"""
    successful: int
    warnings: int
    duplicates: int
    errors: List[str]


# ========== Request (History) Schemas ==========

class RequestItemResponse(BaseModel):
    """Antwort-Schema für RequestItem"""
    request_item_id: str
    request_type_id: str
    authority_id: Optional[str]
    matching_status: str
    matching_level: Optional[str]
    matching_confidence: float
    alternative_authorities: List[str]
    manually_changed: bool
    manual_change_reason: Optional[str]
    document_path: Optional[str]
    document_status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RequestResponse(BaseModel):
    """Antwort-Schema für Request (komplette Anfrage)"""
    request_id: str
    building_id: str
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    status: str
    notes: Optional[str]
    items: List[RequestItemResponse]

    class Config:
        from_attributes = True
