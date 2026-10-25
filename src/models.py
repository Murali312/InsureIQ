"""Pydantic data models for knowledge chunks, source registry, queries, and responses."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ChunkMetadata(BaseModel):
    """Metadata schema attached to every indexed chunk, strictly aligned with chunk_metadata_schema.json."""

    source_id: str = Field(..., description="Unique source identifier")
    publisher: str = Field(..., description="Official issuing organization (e.g. IRDAI, HDFC ERGO)")
    insurer_id: Optional[str] = Field(None, description="Insurer slug or None for regulatory/general")
    product_name: Optional[str] = Field(None, description="Exact product name or None")
    product_uin: Optional[str] = Field(None, description="Product UIN if present")
    document_type: str = Field(
        ...,
        description="regulation | circular | policy_wording | CIS | claim_guide | general_faq | insurer_directory",
    )
    document_title: str = Field(..., description="Exact official title")
    document_version: Optional[str] = Field(None, description="Exact version/revision or None")
    published_date: Optional[str] = Field(None, description="YYYY-MM-DD or None")
    effective_from: Optional[str] = Field(None, description="YYYY-MM-DD or None")
    effective_to: Optional[str] = Field(None, description="YYYY-MM-DD or None")
    retrieved_at_utc: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO-8601 retrieval timestamp",
    )
    source_url: str = Field(..., description="Exact official source URL")
    sha256: str = Field(..., description="Checksum of original downloaded file")
    page_number: Optional[int] = Field(None, description="Page number where available")
    section_path: Optional[str] = Field(None, description="Heading hierarchy or clause path")
    jurisdiction: str = Field(default="IN", description="Jurisdiction code (IN for India)")
    language: str = Field(default="en", description="Language code")
    status: Literal["current", "superseded", "under_review"] = Field(
        default="current", description="Status of the document"
    )
    content_type: Literal["general_faq", "regulatory", "insurer_product", "claims_process"] = Field(
        ..., description="Content category"
    )
    is_official_source: bool = Field(default=True, description="Whether source is official")

    def to_chroma_metadata(self) -> Dict[str, Any]:
        """Convert metadata to flat dictionary for ChromaDB compatibility."""
        data = self.model_dump()
        flat = {}
        for k, v in data.items():
            if v is None:
                flat[k] = ""
            elif isinstance(v, bool):
                flat[k] = int(v)  # Chroma boolean filter support
            else:
                flat[k] = str(v)
        return flat

    @classmethod
    def from_chroma_metadata(cls, d: Dict[str, Any]) -> ChunkMetadata:
        """Reconstruct ChunkMetadata from ChromaDB flat dictionary."""
        converted: Dict[str, Any] = {}
        for k, v in d.items():
            if v == "":
                converted[k] = None
            elif k == "is_official_source":
                converted[k] = bool(int(v)) if isinstance(v, (int, str)) and str(v).isdigit() else bool(v)
            elif k == "page_number":
                converted[k] = int(v) if v and str(v).isdigit() else None
            else:
                converted[k] = v
        return cls(**converted)


class SourceRecord(BaseModel):
    """Source registry entry schema representing a tracked document or web page."""

    source_id: str
    publisher: str
    title: str
    source_url: str
    document_type: str
    verification_notes: Optional[str] = None
    published_or_effective_date: Optional[str] = None
    retrieved_at_utc: Optional[str] = None
    source_status: Literal["official", "pending_verification", "superseded", "under_review"] = "official"
    sha256: Optional[str] = None


class RetrievedChunk(BaseModel):
    """A retrieved knowledge chunk with its relevance score."""

    chunk_id: str
    text: str
    metadata: ChunkMetadata
    score: float = Field(..., description="Relevance score (higher is better, normalized 0.0 to 1.0)")


class QueryClassification(BaseModel):
    """Result of classifying user query intent."""

    intent: Literal[
        "general_faq",
        "regulatory",
        "product_specific",
        "personal_claim_policy",
        "out_of_scope",
    ]
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    query_type: Optional[str] = Field(
        default=None,
        description="Type 1 (General Education), Type 2 (Recommendations/Comparisons), Type 3 (Regulatory/Policy), Type 4 (Personal Account/Claim), or Type 5 (Grievances/Disputes)",
    )
    detected_insurer: Optional[str] = None
    detected_product: Optional[str] = None
    reasoning: str = ""


class AgentResponse(BaseModel):
    """Structured response from the Health Insurance AI Agent."""

    query: str
    classification: QueryClassification
    answer: str
    sources: List[ChunkMetadata] = Field(default_factory=list)
    insufficient_evidence: bool = False
    is_mock_data: bool = False
    mock_notice: Optional[str] = None
    execution_time_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MockPolicyRecord(BaseModel):
    """Synthetic policyholder mock record for local integration testing."""

    policy_number: str
    policyholder_name: str
    insurer_name: str
    product_name: str
    sum_insured_inr: float
    remaining_sum_insured_inr: float
    cumulative_bonus_inr: float
    policy_start_date: str
    policy_end_date: str
    status: str
    is_synthetic: bool = True
    notice: str = "SYNTHETIC TEST DATA - FOR LOCAL TESTING ONLY. NOT A REAL INSURER RECORD."


class MockClaimRecord(BaseModel):
    """Synthetic claim mock record for local integration testing."""

    claim_id: str
    policy_number: str
    patient_name: str
    hospital_name: str
    admission_date: str
    claimed_amount_inr: float
    approved_amount_inr: Optional[float]
    claim_status: str  # e.g., "Under Assessment", "Approved", "Query Raised"
    last_updated: str
    documents_submitted: List[str]
    missing_documents: List[str]
    is_synthetic: bool = True
    notice: str = "SYNTHETIC TEST DATA - FOR LOCAL TESTING ONLY. NOT A REAL INSURER RECORD."
