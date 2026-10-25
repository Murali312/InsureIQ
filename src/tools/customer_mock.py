"""Mock customer policy and claim integration provider with explicit synthetic test data labeling."""

from __future__ import annotations

import abc
from typing import Optional, Dict, Any, List
from src.models import MockPolicyRecord, MockClaimRecord

SYNTHETIC_WARNING = (
    "⚠️ [SYNTHETIC TEST DATA - LOCAL SIMULATION ONLY] "
    "This record was generated solely for integration testing. "
    "It is NOT a real insurer system response."
)

# Synthetic test records for offline simulation
_SYNTHETIC_POLICIES: Dict[str, MockPolicyRecord] = {
    "POL-HDFC-99214": MockPolicyRecord(
        policy_number="POL-HDFC-99214",
        policyholder_name="Aarav Sharma (Test Persona)",
        insurer_name="HDFC ERGO General Insurance",
        product_name="Optima Secure (Test Mock)",
        sum_insured_inr=1000000.0,
        remaining_sum_insured_inr=850000.0,
        cumulative_bonus_inr=200000.0,
        policy_start_date="2024-01-01",
        policy_end_date="2024-12-31",
        status="Active",
        is_synthetic=True,
    ),
    "POL-STAR-77102": MockPolicyRecord(
        policy_number="POL-STAR-77102",
        policyholder_name="Priya Patel (Test Persona)",
        insurer_name="Star Health and Allied Insurance",
        product_name="Comprehensive Insurance Policy (Test Mock)",
        sum_insured_inr=500000.0,
        remaining_sum_insured_inr=500000.0,
        cumulative_bonus_inr=50000.0,
        policy_start_date="2024-04-01",
        policy_end_date="2025-03-31",
        status="Active",
        is_synthetic=True,
    ),
}

_SYNTHETIC_CLAIMS: Dict[str, MockClaimRecord] = {
    "CLM-2024-8841": MockClaimRecord(
        claim_id="CLM-2024-8841",
        policy_number="POL-HDFC-99214",
        patient_name="Aarav Sharma",
        hospital_name="Apollo Hospital, Bannerghatta (Test Provider)",
        admission_date="2024-06-12",
        claimed_amount_inr=150000.0,
        approved_amount_inr=142000.0,
        claim_status="Approved & Settled",
        last_updated="2024-06-15",
        documents_submitted=["Discharge Summary", "Original Bills", "Pharmacy Receipts", "Investigation Reports"],
        missing_documents=[],
        is_synthetic=True,
    ),
    "CLM-2024-9912": MockClaimRecord(
        claim_id="CLM-2024-9912",
        policy_number="POL-HDFC-99214",
        patient_name="Aarav Sharma",
        hospital_name="Fortis Hospital, Cunningham Road (Test Provider)",
        admission_date="2024-09-02",
        claimed_amount_inr=65000.0,
        approved_amount_inr=None,
        claim_status="Under Assessment - Query Raised",
        last_updated="2024-09-05",
        documents_submitted=["Claim Form A", "Indoor Case Papers"],
        missing_documents=["Original Final Bill with receipt", "Treating Doctor Certificate for past medical history"],
        is_synthetic=True,
    ),
}


class BaseCustomerSystemInterface(abc.ABC):
    """Abstract interface defining required contract for policyholder and claim systems."""

    @abc.abstractmethod
    def get_policy_details(self, policy_number: str) -> Optional[MockPolicyRecord]:
        """Fetch policy details for an authenticated policy number."""
        pass

    @abc.abstractmethod
    def get_claim_status(self, claim_id: str) -> Optional[MockClaimRecord]:
        """Fetch real-time claim status and missing documentation for a claim ID."""
        pass


class MockCustomerProvider(BaseCustomerSystemInterface):
    """Synthetic local mock provider strictly identified with SYNTHETIC TEST DATA labels."""

    def __init__(self):
        self.policies = _SYNTHETIC_POLICIES
        self.claims = _SYNTHETIC_CLAIMS

    def get_policy_details(self, policy_number: str) -> Optional[MockPolicyRecord]:
        clean_num = policy_number.strip().upper()
        return self.policies.get(clean_num)

    def get_claim_status(self, claim_id: str) -> Optional[MockClaimRecord]:
        clean_id = claim_id.strip().upper()
        return self.claims.get(clean_id)

    def list_test_policy_numbers(self) -> List[str]:
        """Return list of available synthetic policy numbers for testing."""
        return list(self.policies.keys())

    def list_test_claim_ids(self) -> List[str]:
        """Return list of available synthetic claim IDs for testing."""
        return list(self.claims.keys())


# Global singleton mock provider instance
customer_service = MockCustomerProvider()
