"""Integration tests for the HealthInsuranceAgent orchestrator: routing, citations, and synthetic labels."""

import pytest
from src.agent.orchestrator import HealthInsuranceAgent
from src.agent.classifier import IntentClassifier
from src.retrieval.chroma_engine import ChromaRetrievalEngine
from src.retrieval.embeddings import FallbackHashEmbeddingProvider
from src.models import ChunkMetadata
from src.tools.customer_mock import MockCustomerProvider


@pytest.fixture
def agent_with_test_kb(tmp_path):
    """Setup HealthInsuranceAgent with a temporary ChromaDB populated with sample regulatory chunks."""
    chroma_dir = tmp_path / "agent_test_chroma"
    provider = FallbackHashEmbeddingProvider(dimension=64)
    engine = ChromaRetrievalEngine(
        persist_directory=chroma_dir,
        collection_name="agent_test_coll",
        embedding_provider=provider,
    )

    # Ingest regulatory chunk
    reg_meta = ChunkMetadata(
        source_id="IRDAI-CIRCULAR-2024",
        publisher="IRDAI",
        document_type="circular",
        document_title="Master Circular on Health Insurance Business (2024)",
        source_url="https://irdai.gov.in/circulars/2024",
        sha256="12345678",
        section_path="Master Circular > Timelines",
        status="current",
        content_type="regulatory",
        is_official_source=True,
    )
    docs = [
        {
            "id": "reg-1",
            "text": "Insurers must approve cashless hospital discharge within 3 hours of receiving final bills.",
            "metadata": reg_meta.to_chroma_metadata(),
        }
    ]
    engine.index_documents(docs)

    return HealthInsuranceAgent(
        retrieval_engine=engine,
        intent_classifier=IntentClassifier(),
        customer_provider=MockCustomerProvider(),
    )


def test_agent_routes_personal_claim_to_synthetic_mock(agent_with_test_kb):
    """Verify personal claim query returns synthetic data clearly labelled."""
    resp = agent_with_test_kb.handle_query("Check status for claim CLM-2024-8841")
    assert resp.classification.intent == "personal_claim_policy"
    assert resp.is_mock_data is True
    assert "SYNTHETIC TEST DATA" in resp.answer
    assert "Approved & Settled" in resp.answer
    assert "₹142,000.00" in resp.answer


def test_agent_refuses_to_invent_unverified_product_terms(agent_with_test_kb):
    """Verify agent refuses to invent terms for an unverified insurer product and warns user."""
    resp = agent_with_test_kb.handle_query("What is the room rent limit for HDFC Optima Secure?")
    assert resp.classification.intent == "product_specific"
    assert "Pending Verification" in resp.answer
    assert "https://www.hdfcergo.com" in resp.answer
    assert resp.insufficient_evidence is True


def test_agent_answers_regulatory_query_with_citations(agent_with_test_kb):
    """Verify agent retrieves regulatory chunk and cites IRDAI."""
    resp = agent_with_test_kb.handle_query("What is the IRDAI 3 hour discharge rule?")
    assert resp.classification.intent == "regulatory"
    assert "3 hours" in resp.answer
    assert len(resp.sources) > 0
    assert resp.sources[0].publisher == "IRDAI"
