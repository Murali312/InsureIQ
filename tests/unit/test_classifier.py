"""Unit tests for user intent classification and entity extraction."""

import pytest
from src.agent.classifier import IntentClassifier


@pytest.fixture
def classifier():
    return IntentClassifier()


def test_classify_general_faq(classifier):
    """Verify general terminology and concept inquiries are classified as general_faq."""
    queries = [
        "What is a deductible in health insurance?",
        "What is the difference between copay and sum insured?",
        "How does a family floater policy work?",
        "What documents are required for health insurance reimbursement?",
        "What is cashless hospital treatment?",
    ]
    for q in queries:
        res = classifier.classify(q)
        assert res.intent == "general_faq", f"Failed on query: '{q}', got '{res.intent}'"


def test_classify_regulatory(classifier):
    """Verify official IRDAI, Master Circular, and grievance queries are classified as regulatory."""
    queries = [
        "What is the IRDAI 3 hour discharge authorization rule?",
        "Explain the Bima Bharosa grievance escalation procedure.",
        "What is the maximum PED waiting period under IRDAI 2024 Master Circular?",
        "How long is the free look period under IRDAI regulations?",
        "Can I approach the Insurance Ombudsman if the insurer rejects my claim?",
    ]
    for q in queries:
        res = classifier.classify(q)
        assert res.intent == "regulatory", f"Failed on query: '{q}', got '{res.intent}'"


def test_classify_product_specific(classifier):
    """Verify queries mentioning specific insurers and products are classified as product_specific."""
    queries = [
        ("What is the waiting period for HDFC Optima Secure?", "HDFC_ERGO"),
        ("Does Star Health Comprehensive cover bariatric surgery?", "Star_Health"),
        ("What are the room rent limits in Care Supreme?", "Care_Health"),
        ("What is the NCB in Niva Bupa ReAssure?", "Niva_Bupa"),
    ]
    for q, expected_insurer in queries:
        res = classifier.classify(q)
        assert res.intent == "product_specific", f"Failed on query: '{q}', got '{res.intent}'"
        assert res.detected_insurer == expected_insurer


def test_classify_personal_claim_and_policy(classifier):
    """Verify queries asking about personal balances or claim tracking are classified as personal."""
    queries = [
        "What is my claim status?",
        "How much sum insured do I have left?",
        "Check status for CLM-2024-8841",
        "Show remaining balance for POL-HDFC-99214",
        "What documents have I submitted for my claim?",
    ]
    for q in queries:
        res = classifier.classify(q)
        assert res.intent == "personal_claim_policy", f"Failed on query: '{q}', got '{res.intent}'"


def test_classify_out_of_scope(classifier):
    """Verify non-insurance queries are flagged out of scope."""
    res = classifier.classify("Who won the cricket match yesterday?")
    assert res.intent == "out_of_scope"
