"""Application configuration with validated environment variables.

Supports separate credentials for OpenAI Chat and OpenAI Embeddings,
local SentenceTransformers fallback, and optional AWS Bedrock settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Base directory for the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env if present
load_dotenv(dotenv_path=BASE_DIR / ".env", override=False)


def mask_secret(secret: Optional[str]) -> str:
    """Mask sensitive credentials for safe logging and status display."""
    if not secret:
        return "[NOT SET]"
    if len(secret) <= 8:
        return "****"
    return f"{secret[:3]}...{secret[-4:]}"


class Settings(BaseSettings):
    """Validated application settings."""

    # Chat / Answer Generation Settings
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", alias="OPENAI_MODEL")

    # Embedding Settings
    embedding_provider: Literal["openai", "local"] = Field(
        default="openai", alias="EMBEDDING_PROVIDER"
    )
    openai_embedding_api_key: Optional[str] = Field(
        default=None, alias="OPENAI_EMBEDDING_API_KEY"
    )
    openai_embedding_model: str = Field(
        default="text-embedding-3-small", alias="OPENAI_EMBEDDING_MODEL"
    )
    local_embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        alias="LOCAL_EMBEDDING_MODEL",
    )

    # Vector Store Settings
    chroma_persist_directory: str = Field(
        default=str(BASE_DIR / "vector_store" / "chroma"),
        alias="CHROMA_PERSIST_DIRECTORY",
    )
    collection_name: str = Field(
        default="india_health_insurance_kb", alias="COLLECTION_NAME"
    )

    # Retrieval Thresholds
    min_relevance_score: float = Field(default=0.35, alias="MIN_RELEVANCE_SCORE")
    top_k_results: int = Field(default=6, alias="TOP_K_RESULTS")

    # Live Web Search & SSRF Guard Settings
    allow_web_lookup: bool = Field(default=True, alias="ALLOW_WEB_LOOKUP")
    request_timeout_seconds: int = Field(default=10, alias="REQUEST_TIMEOUT_SECONDS")
    max_web_fetch_bytes: int = Field(default=1048576, alias="MAX_WEB_FETCH_BYTES")  # 1MB limit

    # Approved Official Domain Allowlist for Live Web Lookup
    approved_domains: list[str] = Field(
        default_factory=lambda: [
            "irdai.gov.in",
            "bimabharosa.irdai.gov.in",
            "hdfcergo.com",
            "www.hdfcergo.com",
            "icicilombard.com",
            "www.icicilombard.com",
            "starhealth.in",
            "www.starhealth.in",
            "nivabupa.com",
            "www.nivabupa.com",
            "careinsurance.com",
            "www.careinsurance.com",
            "adityabirlacapital.com",
            "www.adityabirlacapital.com",
        ]
    )

    # Optional AWS Bedrock Settings (not required for base local execution)
    aws_region: str = Field(default="us-east-1", alias="AWS_REGION")
    aws_bedrock_kb_id: Optional[str] = Field(default=None, alias="AWS_BEDROCK_KB_ID")
    aws_bedrock_model_id: str = Field(
        default="anthropic.claude-3-sonnet-20240229-v1:0",
        alias="AWS_BEDROCK_MODEL_ID",
    )
    aws_access_key_id: Optional[str] = Field(default=None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = Field(
        default=None, alias="AWS_SECRET_ACCESS_KEY"
    )

    # General Settings
    app_env: str = Field(default="development", alias="APP_ENV")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("embedding_provider", mode="before")
    @classmethod
    def sanitize_provider(cls, v: str) -> str:
        if isinstance(v, str):
            v_lower = v.strip().lower()
            if v_lower in ("openai", "local"):
                return v_lower
        return "openai"

    def get_chroma_path(self) -> Path:
        """Resolve persistence directory path relative to project root if needed."""
        p = Path(self.chroma_persist_directory)
        if not p.is_absolute():
            return (BASE_DIR / p).resolve()
        return p.resolve()

    def validate_chat_credentials(self) -> None:
        """Validate chat generation credentials without printing them."""
        if not self.openai_api_key or not self.openai_api_key.strip():
            raise ValueError(
                "OPENAI_API_KEY is missing or empty. Please set it in your .env file "
                "or environment variables for chat answer generation."
            )

    def validate_embedding_credentials(self) -> None:
        """Validate embedding credentials depending on provider."""
        if self.embedding_provider == "openai":
            if (
                not self.openai_embedding_api_key
                or not self.openai_embedding_api_key.strip()
            ):
                raise ValueError(
                    "OPENAI_EMBEDDING_API_KEY is missing or empty while EMBEDDING_PROVIDER is 'openai'. "
                    "Please set OPENAI_EMBEDDING_API_KEY in your .env file or switch "
                    "EMBEDDING_PROVIDER to 'local' for local sentence-transformers."
                )

    def is_chat_ready(self) -> bool:
        """Check if chat API key is configured."""
        return bool(self.openai_api_key and self.openai_api_key.strip())

    def is_embedding_ready(self) -> bool:
        """Check if selected embedding provider is configured."""
        if self.embedding_provider == "openai":
            return bool(
                self.openai_embedding_api_key
                and self.openai_embedding_api_key.strip()
            )
        return True  # Local embedding doesn't require API key


# Global singleton settings instance
settings = Settings()
