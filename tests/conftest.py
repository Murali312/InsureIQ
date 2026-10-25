"""Pytest configuration, environment overrides, and shared fixtures."""

import os
import shutil
from pathlib import Path
import pytest

# Ensure testing configuration before importing application code
os.environ["APP_ENV"] = "test"
os.environ["EMBEDDING_PROVIDER"] = "fallback"
os.environ["CHROMA_PERSIST_DIRECTORY"] = "./tmp_test_chroma"

from src.models import ChunkMetadata, RetrievedChunk
from src.retrieval.embeddings import FallbackHashEmbeddingProvider
from src.retrieval.chroma_engine import ChromaRetrievalEngine


@pytest.fixture
def fallback_embeddings():
    """Provides a deterministic fallback embedding provider."""
    return FallbackHashEmbeddingProvider(dimension=64)


@pytest.fixture
def sample_chunk_metadata() -> ChunkMetadata:
    """Fixture returning a valid, complete ChunkMetadata instance."""
    return ChunkMetadata(
        source_id="IRDAI-CIRCULAR-2024",
        publisher="IRDAI",
        document_type="circular",
        document_title="Master Circular on Health Insurance Business (2024)",
        source_url="https://irdai.gov.in/web/guest/circulars?filterDepartment=HLT",
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        page_number=3,
        section_path="Master Circular > Cashless Claim Timelines",
        status="current",
        content_type="regulatory",
        is_official_source=True,
    )


@pytest.fixture
def temp_chroma_engine(tmp_path, fallback_embeddings):
    """Provides an isolated ChromaRetrievalEngine pointing to a temporary directory."""
    chroma_dir = tmp_path / "chroma_test_store"
    engine = ChromaRetrievalEngine(
        persist_directory=chroma_dir,
        collection_name="test_collection",
        embedding_provider=fallback_embeddings,
    )
    yield engine
    # Cleanup
    if chroma_dir.exists():
        shutil.rmtree(chroma_dir, ignore_errors=True)
