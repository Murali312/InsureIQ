"""Unit tests for synthetic customer policy and claim integration provider."""

import pytest
from src.tools.customer_mock import MockCustomerProvider, SYNTHETIC_WARNING


@pytest.fixture
def provider():
    return MockCustomerProvider()


def test_mock_policy_returns_synthetic_label(provider):
    """Verify mock policies are explicitly marked as synthetic test data."""
    policy = provider.get_policy_details("POL-HDFC-99214")
    assert policy is not None
    assert policy.is_synthetic is True
    assert "SYNTHETIC TEST DATA" in policy.notice
    assert policy.policy_number == "POL-HDFC-99214"
    assert policy.sum_insured_inr == 1000000.0
    assert policy.remaining_sum_insured_inr == 850000.0


def test_mock_claim_returns_synthetic_label(provider):
    """Verify mock claims are explicitly marked as synthetic test data."""
    claim = provider.get_claim_status("CLM-2024-8841")
    assert claim is not None
    assert claim.is_synthetic is True
    assert "SYNTHETIC TEST DATA" in claim.notice
    assert claim.claim_id == "CLM-2024-8841"
    assert claim.claim_status == "Approved & Settled"
    assert claim.approved_amount_inr == 142000.0


def test_unknown_id_returns_none(provider):
    """Verify non-existent policy or claim returns None without throwing exceptions."""
    assert provider.get_policy_details("POL-NONEXISTENT-0000") is None
    assert provider.get_claim_status("CLM-NONEXISTENT-9999") is None


def test_no_secret_or_password_requirements():
    """Verify the mock customer interface requires only policy/claim identifiers and no secrets/passwords."""
    provider = MockCustomerProvider()
    # The interface should only accept string identifiers
    import inspect
    sig = inspect.signature(provider.get_policy_details)
    assert list(sig.parameters.keys()) == ["policy_number"]

    sig_claim = inspect.signature(provider.get_claim_status)
    assert list(sig_claim.parameters.keys()) == ["claim_id"]
