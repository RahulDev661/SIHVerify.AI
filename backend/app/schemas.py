"""
Pydantic models for API request/response bodies.

Kept separate from ai_service so the ML package stays framework
agnostic — ai_service never imports FastAPI/Pydantic, only plain
dicts, which keeps it reusable outside a web context (CLI scripts,
batch jobs, notebooks, etc.).
"""

from typing import Any, Optional

from pydantic import BaseModel, EmailStr, Field


# --- Auth ---------------------------------------------------------------


class UserRegister(BaseModel):
    name: str
    email: EmailStr
    officerId: str
    password: str = Field(min_length=6)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserPublic(BaseModel):
    """User data safe to send back to the client — never includes the hash."""

    id: str
    name: str
    email: EmailStr
    officerId: str


class TokenResponse(BaseModel):
    accessToken: str
    tokenType: str = "bearer"
    user: UserPublic


class MRZStructureValidation(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)


class PassportOCRResult(BaseModel):
    passportNumber: Optional[str] = None
    surname: Optional[str] = None
    givenNames: Optional[str] = None
    nationality: Optional[str] = None
    dob: Optional[str] = None
    sex: Optional[str] = None
    expiry: Optional[str] = None
    structureValidation: MRZStructureValidation


class FaceMatchResult(BaseModel):
    similarity: float
    threshold: float
    matched: bool


class DocumentValidationResult(BaseModel):
    valid: bool
    documentType: Optional[str] = None
    confidence: float
    errors: list[str] = Field(default_factory=list)


class TamperingAnalysisResult(BaseModel):
    """
    Module 3 — Image forensics / tampering screening.

    `analysis`, `metadata`, `stampAnalysis`, `photoAnalysis`, and
    `textAnalysis` are left as loosely-typed dicts (rather than fully
    nested models) since `ai_service.tampering.detector` is a
    heuristic forensic pipeline whose sub-analysis shapes are still
    evolving — the top-level score/status/reasons contract is what
    the rest of the app relies on.
    """

    tamperingScore: float
    status: str  # "LOW_RISK" | "SUSPICIOUS" | "HIGH_RISK"
    reasons: list[str] = Field(default_factory=list)
    imageInfo: dict[str, Any] = Field(default_factory=dict)
    analysis: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    stampAnalysis: dict[str, Any] = Field(default_factory=dict)
    photoAnalysis: dict[str, Any] = Field(default_factory=dict)
    textAnalysis: dict[str, Any] = Field(default_factory=dict)


class VisiblePassportFields(BaseModel):
    """OCR'd values from the visible (non-MRZ) printed passport fields."""

    passportNumber: Optional[str] = None
    nationality: Optional[str] = None
    dob: Optional[str] = None
    expiry: Optional[str] = None
    sex: Optional[str] = None


class FieldConsistencyResult(BaseModel):
    """Cross-check between the visible printed fields and the parsed MRZ."""

    consistencyScore: float
    status: str  # "CONSISTENT" | "REVIEW_REQUIRED" | "INCONSISTENT"
    checks: dict[str, bool] = Field(default_factory=dict)
    mismatches: list[str] = Field(default_factory=list)
    normalizedValues: dict[str, Any] = Field(default_factory=dict)


class PassportVerificationResponse(BaseModel):
    """Response for POST /api/v1/passport/verify"""

    ocr: PassportOCRResult
    faceMatch: Optional[FaceMatchResult] = None
    documentValidation: Optional[DocumentValidationResult] = None
    tamperingAnalysis: Optional[TamperingAnalysisResult] = None
    visibleFields: Optional[VisiblePassportFields] = None
    fieldConsistency: Optional[FieldConsistencyResult] = None
    verified: bool
    historyId: Optional[str] = None


# --- Scan history ---------------------------------------------------------


class ScanHistorySummary(BaseModel):
    """One row in the screening history list."""

    id: str
    createdAt: str
    documentType: str = "Passport"
    passportNumber: Optional[str] = None
    name: Optional[str] = None
    nationality: Optional[str] = None
    officerName: str
    verified: bool
    score: int
    risk: str  # "LOW" | "MEDIUM" | "HIGH"


class ScanHistoryDetail(ScanHistorySummary):
    """Full record, including the original verification response."""

    result: PassportVerificationResponse


class ErrorResponse(BaseModel):
    detail: str
