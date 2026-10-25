"""Unit tests for retrieval filtering, version exclusion, and relevance thresholding."""

import pytest
from src.models import ChunkMetadata
from src.retrieval.chroma_engine import ChromaRetrievalEngine
from src.retrieval.embeddings import FallbackHashEmbeddingProvider


def test_superseded_version_filtering(tmp_path):
    """Verify superseded policy versions are filtered out for current queries."""
    chroma_dir = tmp_path / "chroma_version_test"
    provider = FallbackHashEmbeddingProvider(dimension=64)
    engine = ChromaRetrievalEngine(
        persist_directory=chroma_dir,
        collection_name="version_test_coll",
        embedding_provider=provider,
    )

    # Ingest one current chunk and one superseded chunk
    current_meta = ChunkMetadata(
        source_id="HDFC-OPT-2024",
        publisher="HDFC ERGO",
        document_type="policy_wording",
        document_title="Optima Secure 2024",
        source_url="https://www.hdfcergo.com/policy2024.pdf",
        sha256="abc1",
        status="current",
        content_type="insurer_product",
    )
    superseded_meta = ChunkMetadata(
        source_id="HDFC-OPT-2020",
        publisher="HDFC ERGO",
        document_type="policy_wording",
        document_title="Optima Secure 2020 (Old)",
        source_url="https://www.hdfcergo.com/policy2020.pdf",
        sha256="abc2",
        status="superseded",
        content_type="insurer_product",
    )

    docs = [
        {
            "id": "chunk-current",
            "text": "Waiting period for pre-existing disease is 36 months.",
            "metadata": current_meta.to_chroma_metadata(),
        },
        {
            "id": "chunk-superseded",
            "text": "Waiting period for pre-existing disease was 48 months.",
            "metadata": superseded_meta.to_chroma_metadata(),
        },
    ]
    engine.index_documents(docs)

    # Query with default filters (should exclude superseded)
    results = engine.query(query_text="waiting period", top_k=5, min_relevance_score=0.0)
    result_ids = [r.chunk_id for r in results]
    assert "chunk-current" in result_ids
    assert "chunk-superseded" not in result_ids

    # Query with include_superseded=True
    all_results = engine.query(
        query_text="waiting period",
        top_k=5,
        filters={"include_superseded": True},
        min_relevance_score=0.0,
    )
    all_ids = [r.chunk_id for r in all_results]
    assert "chunk-current" in all_ids
    assert "chunk-superseded" in all_ids


def test_relevance_score_thresholding(tmp_path):
    """Verify chunks below min_relevance_score are filtered out."""
    chroma_dir = tmp_path / "chroma_thresh_test"
    provider = FallbackHashEmbeddingProvider(dimension=64)
    engine = ChromaRetrievalEngine(
        persist_directory=chroma_dir,
        collection_name="thresh_coll",
        embedding_provider=provider,
    )

    meta = ChunkMetadata(
        source_id="IRDAI-FAQ",
        publisher="IRDAI",
        document_type="regulatory_faq",
        document_title="IRDAI FAQ",
        source_url="https://irdai.gov.in/faqs",
        sha256="123",
        status="current",
        content_type="regulatory",
    )
    docs = [
        {
            "id": "relevant-1",
            "text": "Free look period in health insurance is 30 days.",
            "metadata": meta.to_chroma_metadata(),
        }
    ]
    engine.index_documents(docs)

    # Query with impossible threshold (1.0) -> should yield 0 results
    filtered = engine.query("completely unrelated cooking recipe", min_relevance_score=0.99)
    assert len(filtered) == 0


def test_incompatible_embedding_model_detection(tmp_path):
    """Verify ChromaRetrievalEngine detects mismatched model names and raises ValueError."""
    chroma_dir = tmp_path / "chroma_mismatch_test"
    p1 = FallbackHashEmbeddingProvider(dimension=64)
    # First creation
    ChromaRetrievalEngine(
        persist_directory=chroma_dir,
        collection_name="mismatch_coll",
        embedding_provider=p1,
    )

    # Create mock provider with different model_name
    class DifferentProvider(FallbackHashEmbeddingProvider):
        @property
        def model_name(self) -> str:
            return "different-model-name"

    p2 = DifferentProvider(dimension=64)
    with pytest.raises(ValueError, match="Incompatible embedding model detected"):
        ChromaRetrievalEngine(
            persist_directory=chroma_dir,
            collection_name="mismatch_coll",
            embedding_provider=p2,
        )
