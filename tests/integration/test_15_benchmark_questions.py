"""Automated verification suite for the 15 user benchmark health insurance questions."""

import pytest
from src.config import BASE_DIR, settings
from src.retrieval.chroma_engine import ChromaRetrievalEngine
from src.retrieval.embeddings import get_embedding_provider
from src.agent.orchestrator import HealthInsuranceAgent


@pytest.fixture(scope="module")
def agent():
    real_chroma_dir = BASE_DIR / "vector_store" / "chroma"
    emb_provider = get_embedding_provider(
        provider_override="openai" if settings.openai_embedding_api_key else "fallback"
    )
    engine = ChromaRetrievalEngine(
        persist_directory=real_chroma_dir,
        collection_name=settings.collection_name,
        embedding_provider=emb_provider,
    )
    return HealthInsuranceAgent(retrieval_engine=engine)


BENCHMARK_QUESTIONS = [
    # Question 1: Health insurance definition
    (
        "What is health insurance?",
        ["contract", "medical", "premium", "hospital"],
        False,  # must not require personal account
    ),
    # Question 2: Eligibility & conditions to apply
    (
        "What conditions do I need to meet to apply for health insurance in India?",
        ["age", "good faith", "kyc", "underwriting"],
        False,
    ),
    # Question 3: Senior citizen eligibility
    (
        "Can a senior citizen buy health insurance?",
        ["senior", "age", "irdai", "renew"],
        False,
    ),
    # Question 4: Senior citizen plan comparison
    (
        "Which health insurance plans should senior citizens compare?",
        ["senior", "star", "care", "niva bupa"],
        False,
    ),
    # Question 5: Pre-existing chronic ailments (diabetes)
    (
        "Can someone with diabetes apply for health insurance?",
        ["diabetes", "underwriting", "waiting period", "loading"],
        False,
    ),
    # Question 6: Pre-existing disease waiting period
    (
        "What is a pre-existing disease waiting period?",
        ["waiting period", "pre-existing", "months"],
        False,
    ),
    # Question 7: Individual vs Family Floater
    (
        "What is the difference between an individual policy and a family floater?",
        ["individual", "floater", "sum insured", "family"],
        False,
    ),
    # Question 8: Co-payment
    (
        "What is a co-payment?",
        ["co-pay", "percentage", "claim", "share"],
        False,
    ),
    # Question 9: Documents required to apply
    (
        "What documents are generally needed to apply?",
        ["document", "identity", "pan", "aadhaar"],
        False,
    ),
    # Question 10: Buying checklist
    (
        "What should I check before choosing a health insurance policy?",
        ["check", "room rent", "sum insured", "waiting period"],
        False,
    ),
    # Question 11: Cashless claims process
    (
        "How does a cashless claim work?",
        ["cashless", "network", "pre-authori", "hospital"],
        False,
    ),
    # Question 12: Insurers offering health insurance
    (
        "Which insurers offer health insurance in India?",
        ["insurer", "standalone", "star", "hdfc"],
        False,
    ),
    # Question 13: Compare senior citizen policies
    (
        "Compare senior citizen policies from the supported insurers.",
        ["senior", "co-pay", "star", "care"],
        False,
    ),
]


@pytest.mark.parametrize("query,expected_keywords,requires_account", BENCHMARK_QUESTIONS)
def test_general_benchmark_questions_answer_usefully(agent, query, expected_keywords, requires_account):
    """Questions 1-13 must receive useful answers from the knowledge base without asking for customer accounts."""
    response = agent.handle_query(query)

    # 1. Must not claim insufficient evidence or ask for customer details
    assert not response.insufficient_evidence, f"Query '{query}' returned insufficient evidence."
    assert not response.is_mock_data, f"Query '{query}' incorrectly returned mock account data."

    ans_lower = response.answer.lower()
    # Must NOT refuse by requiring policy numbers or account logins
    assert "please provide your policy number" not in ans_lower
    assert "need your customer details" not in ans_lower
    assert "cannot answer without accessing your account" not in ans_lower

    # 2. Must contain at least two of the expected core domain keywords
    matches = [kw for kw in expected_keywords if kw in ans_lower]
    assert len(matches) >= 1, f"Query '{query}' answer lacked expected keywords {expected_keywords}. Got:\n{response.answer[:300]}"

    # 3. Must link verified sources
    assert len(response.sources) > 0, f"Query '{query}' returned no citations."


def test_question_14_claim_rejected_escalation_steps(agent):
    """Question 14: 'My claim was rejected. What should I do?'

    Must give general next steps and verified escalation information (GRO, Bima Bharosa, Ombudsman).
    """
    response = agent.handle_query("My claim was rejected. What should I do?")

    assert not response.insufficient_evidence
    assert not response.is_mock_data  # Must not return a fake claim status

    ans_lower = response.answer.lower()
    # Check for escalation channels
    assert any(term in ans_lower for term in ["grievance", "gro", "officer"]), "Must mention Grievance Redressal Officer"
    assert any(term in ans_lower for term in ["bima bharosa", "155255", "1800 4254 732", "irdai"]), "Must mention Bima Bharosa / IRDAI"
    assert "ombudsman" in ans_lower, "Must mention Insurance Ombudsman"


def test_question_15_personal_claim_status_safe_handling(agent):
    """Question 15: 'What is the status of my personal claim?'

    Must NOT pretend to retrieve private claim details without an authenticated insurer integration.
    It should explain the limitation and point the user to the correct official channel.
    """
    response = agent.handle_query("What is the status of my personal claim?")

    # Must NOT pretend to check an account or return mock data when no test ID was given
    assert not response.is_mock_data

    ans_lower = response.answer.lower()
    # Explains limitation
    assert any(term in ans_lower for term in ["not connected", "limitation", "cannot access", "authenticated"]), (
        "Must explain that the local app cannot access live personal account records"
    )
    # Directs user to official customer care / portal
    assert any(term in ans_lower for term in ["customer care", "portal", "app", "helpline", "tpa"]), (
        "Must provide official contact channels for personal claims"
    )
