from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ClaimStatus = Literal[
    "PENDING",
    "VERIFIED",
    "OUTDATED",
    "INACCURATE",
    "FALSE",
    "INSUFFICIENT EVIDENCE",
]


class EvidenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    title: str
    url: str
    snippet: str | None = None
    source_type: str = "web"


class ExtractedClaim(BaseModel):
    claim: str
    type: str = Field(default="general")
    page: int | None = None


class ClaimOut(BaseModel):
    id: int | None = None
    claim: str
    type: str = Field(alias="claim_type")
    page: int | None = None
    status: ClaimStatus = "PENDING"
    confidence: int = 0
    correct_value: str | None = None
    explanation: str | None = None
    evidence: list[EvidenceOut] = []

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ReportSummary(BaseModel):
    total: int = 0
    verified: int = 0
    outdated: int = 0
    inaccurate: int = 0
    false: int = 0
    insufficient_evidence: int = 0
    pending: int = 0


class ReportOut(BaseModel):
    id: str
    filename: str
    status: str
    current_step: str
    progress: int
    error: str | None = None
    summary: ReportSummary
    claims: list[ClaimOut] = []
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None
    downloads: dict[str, str] = {}


class UploadResponse(BaseModel):
    id: str
    status: str
    current_step: str
    progress: int


class ExtractClaimsResponse(BaseModel):
    claims: list[ExtractedClaim]
    character_count: int
    page_count: int


class VerifyRequest(BaseModel):
    claims: list[ExtractedClaim]


class VerifiedClaim(BaseModel):
    claim: str
    type: str
    status: ClaimStatus
    confidence: int
    correct_value: str | None = None
    explanation: str
    sources: list[EvidenceOut] = []


class VerifyResponse(BaseModel):
    results: list[VerifiedClaim]

