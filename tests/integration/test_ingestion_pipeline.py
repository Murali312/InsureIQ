"""Integration tests for the ingestion pipeline: parsing, hashing, chunking, and ChromaDB indexing."""

import pytest
from pathlib import Path

from src.models import ChunkMetadata
from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.registry import SourceRegistry
from src.retrieval.chroma_engine import ChromaRetrievalEngine
from src.retrieval.embeddings import FallbackHashEmbeddingProvider


def test_full_ingestion_pipeline(tmp_path):
    """Verify end-to-end ingestion pipeline with real file extraction and ChromaDB indexing."""
    # Setup test knowledge directory
    knowledge_dir = tmp_path / "knowledge"
    gen_dir = knowledge_dir / "general"
    reg_dir = knowledge_dir / "regulatory"
    gen_dir.mkdir(parents=True)
    reg_dir.mkdir(parents=True)

    # Create general sample FAQ
    faq_file = gen_dir / "test_general_faqs.md"
    faq_file.write_text(
        "# General Health Insurance FAQs\n\n"
        "## What is sum insured?\n"
        "Sum insured is the maximum financial coverage limit under the policy contract.\n\n"
        "## What is a deductible?\n"
        "A deductible is the initial amount the policyholder pays before insurance coverage kicks in.\n",
        encoding="utf-8",
    )

    # Create regulatory circular sample
    reg_file = reg_dir / "test_master_circular.md"
    reg_file.write_text(
        "# Master Circular on Health Insurance (2024)\n\n"
        "## Cashless Discharge Timelines\n"
        "Final discharge authorization must be completed within 3 hours.\n\n"
        "## PED Waiting Period\n"
        "Maximum PED waiting period cannot exceed 36 months.\n",
        encoding="utf-8",
    )

    # Setup isolated Chroma and registry
    chroma_dir = tmp_path / "chroma_integration_db"
    registry_file = tmp_path / "source_registry.csv"
    registry = SourceRegistry(registry_csv_path=registry_file)

    provider = FallbackHashEmbeddingProvider(dimension=64)
    engine = ChromaRetrievalEngine(
        persist_directory=chroma_dir,
        collection_name="integration_coll",
        embedding_provider=provider,
    )

    pipeline = IngestionPipeline(
        knowledge_dir=knowledge_dir,
        retrieval_engine=engine,
        registry=registry,
    )

    report = pipeline.run_ingestion()
    assert report["files_processed"] == 2
    assert report["chunks_extracted"] >= 2
    assert report["chunks_indexed"] == report["chunks_extracted"]

    # Verify query retrieves the indexed chunks
    results = engine.query(
        query_text="What is sum insured?",
        top_k=2,
        min_relevance_score=0.0,
    )
    assert len(results) > 0
    assert any("sum insured" in r.text.lower() for r in results)

    # Verify registry was populated with SHA-256
    sources = registry.load_sources()
    assert len(sources) >= 2
    for s in sources:
        assert s.sha256 is not None
        assert len(s.sha256) == 64
        assert s.retrieved_at_utc is not None
