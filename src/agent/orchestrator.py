"""Main Health Insurance Agent orchestrator coordinating classification, retrieval, mock tools, and answer generation."""

from __future__ import annotations

import logging
import re
import time
from typing import Optional, List, Dict, Any

from src.config import settings
from src.models import (
    AgentResponse,
    QueryClassification,
    RetrievedChunk,
    ChunkMetadata,
)
from src.security import sanitize_user_input
from src.agent.classifier import IntentClassifier, classifier as default_classifier
from src.agent.prompts import (
    INSUFFICIENT_EVIDENCE_TEMPLATE,
    PRODUCT_PENDING_TEMPLATE,
    PERSONAL_MOCK_BANNER,
)
from src.retrieval.base import BaseRetrievalEngine
from src.retrieval.chroma_engine import ChromaRetrievalEngine
from src.integrations.openai_chat import OpenAIChatService
from src.tools.customer_mock import MockCustomerProvider, customer_service as default_customer_service

# Official domains for pending products
OFFICIAL_DOMAINS = {
    "HDFC_ERGO": "https://www.hdfcergo.com",
    "ICICI_Lombard": "https://www.icicilombard.com",
    "Star_Health": "https://www.starhealth.in",
    "Niva_Bupa": "https://www.nivabupa.com",
    "Care_Health": "https://www.careinsurance.com",
    "Aditya_Birla_Health": "https://www.adityabirlacapital.com/healthinsurance",
}

logger = logging.getLogger(__name__)


class HealthInsuranceAgent:
    """Production-oriented Health Insurance Agent for India jurisdiction."""

    def __init__(
        self,
        retrieval_engine: Optional[BaseRetrievalEngine] = None,
        chat_service: Optional[OpenAIChatService] = None,
        intent_classifier: Optional[IntentClassifier] = None,
        customer_provider: Optional[MockCustomerProvider] = None,
    ):
        self.classifier = intent_classifier or default_classifier
        self.customer_service = customer_provider or default_customer_service
        self.chat_service = chat_service or OpenAIChatService()
        self._retrieval_engine = retrieval_engine

    @property
    def retrieval_engine(self) -> BaseRetrievalEngine:
        """Lazy load retrieval engine to handle startup gracefully."""
        if self._retrieval_engine is None:
            self._retrieval_engine = ChromaRetrievalEngine()
        return self._retrieval_engine

    def handle_query(self, user_query: str) -> AgentResponse:
        """Process user inquiry end-to-end with validation, classification, and safety checks."""
        start_time = time.perf_counter()
        clean_query = sanitize_user_input(user_query)

        if not clean_query:
            return AgentResponse(
                query="",
                classification=QueryClassification(
                    intent="general_faq", confidence=1.0, reasoning="Empty query provided."
                ),
                answer="Please enter a health insurance question, policy query, or claim question.",
                insufficient_evidence=True,
                execution_time_ms=0.0,
            )

        # Step 1: Intent Classification
        classification = self.classifier.classify(clean_query)
        q_type = getattr(classification, "query_type", None) or getattr(classification, "intent", "general_faq")
        logger.info(
            "Agent Query: '%s' | Intent: %s | QueryType: %s | Confidence: %.2f",
            clean_query,
            classification.intent,
            q_type,
            classification.confidence,
        )

        # Step 2: Route Personal / Claim queries to Mock Provider or Authentication Limitation Notice
        if classification.intent == "personal_claim_policy":
            return self._handle_personal_claim_query(clean_query, classification, start_time)

        # Step 3: Handle Product-Specific queries with missing verified documents
        if classification.intent == "product_specific":
            response = self._handle_product_query(clean_query, classification, start_time)
            if response is not None:
                return response

        # Step 4: Knowledge Base Retrieval across active knowledge base
        filters: Dict[str, Any] = {"include_superseded": False}

        retrieved_chunks = self.retrieval_engine.query(
            query_text=clean_query,
            top_k=settings.top_k_results,
            filters=filters,
        )

        if not retrieved_chunks:
            elapsed = (time.perf_counter() - start_time) * 1000
            logger.info("Agent Retrieval returned 0 chunks above threshold for query: '%s'", clean_query)
            return AgentResponse(
                query=clean_query,
                classification=classification,
                answer=INSUFFICIENT_EVIDENCE_TEMPLATE,
                sources=[],
                insufficient_evidence=True,
                execution_time_ms=round(elapsed, 2),
            )

        # Step 5: Generate Answer via Chat Service (or local deterministic summary)
        answer_text = self.chat_service.generate_answer(
            query=clean_query,
            retrieved_chunks=retrieved_chunks,
            query_type=q_type,
        )

        elapsed = (time.perf_counter() - start_time) * 1000
        unique_sources = self._deduplicate_sources([c.metadata for c in retrieved_chunks])
        logger.info(
            "Agent Completed Query in %.2f ms | Chunks: %d | Unique Sources: %d",
            elapsed,
            len(retrieved_chunks),
            len(unique_sources),
        )

        return AgentResponse(
            query=clean_query,
            classification=classification,
            answer=answer_text,
            sources=unique_sources,
            insufficient_evidence=False,
            execution_time_ms=round(elapsed, 2),
        )

    def _handle_personal_claim_query(
        self,
        query: str,
        classification: QueryClassification,
        start_time: float,
    ) -> AgentResponse:
        """Safely handle personal claim or policy inquiries without pretending to access live accounts."""
        # Extract explicit policy or claim numbers (e.g., POL-HDFC-99214, CLM-2024-8841)
        pol_match = re.search(r"\b(POL-[A-Z]+-\d+)\b", query, re.IGNORECASE)
        clm_match = re.search(r"\b(CLM-\d+-\d+)\b", query, re.IGNORECASE)

        policy_id = pol_match.group(1).upper() if pol_match else None
        claim_id = clm_match.group(1).upper() if clm_match else None
        elapsed = (time.perf_counter() - start_time) * 1000

        # If user did NOT provide an explicit test ID, do not fabricate or default to one
        if not policy_id and not claim_id:
            answer = (
                "🔒 **Personal Account Information Limitation:**\n\n"
                "This application is a local informational and educational AI assistant for health insurance policies and regulations. "
                "It is **not connected to live insurer databases or authenticated customer accounts**, and therefore "
                "cannot look up or verify your private policy details, remaining sum insured, or live claim status.\n\n"
                "**How to Check Your Live Policy or Claim Status:**\n"
                "1. **Insurer Official Portal / App:** Log in to your insurer's official mobile application or web portal using your registered mobile number or policy number.\n"
                "2. **Insurer Customer Care Helplines:**\n"
                "   - *HDFC ERGO:* `1800 2666 400` / `care@hdfcergo.com`\n"
                "   - *Star Health:* `1800 425 2255` / `claims@starhealth.in`\n"
                "   - *Care Health:* `1800 102 4488` / `customerfirst@careinsurance.com`\n"
                "   - *Niva Bupa:* `1860 500 8888` / `customercare@nivabupa.com`\n"
                "   - *ICICI Lombard:* `1800 2666` / `customersupport@icicilombard.com`\n"
                "   - *Aditya Birla Health:* `1800 270 7000` / `care.healthinsurance@adityabirlacapital.com`\n"
                "3. **Hospital Insurance Desk:** If you are currently hospitalized, contact the hospital's TPA / Insurance desk for real-time cashless approval status.\n\n"
                "*(For Local Integration Testing Only: You can query synthetic simulation records by including a test ID like `CLM-2024-8841` or `POL-HDFC-99214`).*"
            )
            return AgentResponse(
                query=query,
                classification=classification,
                answer=answer,
                is_mock_data=False,
                execution_time_ms=round(elapsed, 2),
            )

        # Handle explicit claim simulation ID
        if claim_id:
            claim_rec = self.customer_service.get_claim_status(claim_id)
            if claim_rec:
                docs_sub = ", ".join(claim_rec.documents_submitted) or "None"
                missing_docs = ", ".join(claim_rec.missing_documents) or "None (All required documents verified)"
                answer = (
                    f"{PERSONAL_MOCK_BANNER}"
                    f"### Claim Status: `{claim_rec.claim_id}`\n\n"
                    f"- **Status:** **{claim_rec.claim_status}**\n"
                    f"- **Policy Number:** `{claim_rec.policy_number}`\n"
                    f"- **Patient Name:** {claim_rec.patient_name}\n"
                    f"- **Hospital:** {claim_rec.hospital_name}\n"
                    f"- **Admission Date:** {claim_rec.admission_date}\n"
                    f"- **Claimed Amount:** ₹{claim_rec.claimed_amount_inr:,.2f}\n"
                    f"- **Approved / Settled Amount:** "
                    f"{f'₹{claim_rec.approved_amount_inr:,.2f}' if claim_rec.approved_amount_inr else 'Under assessment'}\n"
                    f"- **Last Updated:** {claim_rec.last_updated}\n\n"
                    f"**Document Verification:**\n"
                    f"- *Submitted:* {docs_sub}\n"
                    f"- *Missing / Pending Action:* {missing_docs}\n\n"
                    f"*(Notice: Synthetic simulation record for local test verification only)*"
                )
                return AgentResponse(
                    query=query,
                    classification=classification,
                    answer=answer,
                    is_mock_data=True,
                    mock_notice=claim_rec.notice,
                    execution_time_ms=round(elapsed, 2),
                )

        # Handle explicit policy simulation ID
        if policy_id:
            pol_rec = self.customer_service.get_policy_details(policy_id)
            if pol_rec:
                answer = (
                    f"{PERSONAL_MOCK_BANNER}"
                    f"### Policy Details: `{pol_rec.policy_number}`\n\n"
                    f"- **Insurer:** {pol_rec.insurer_name}\n"
                    f"- **Product:** {pol_rec.product_name}\n"
                    f"- **Policyholder:** {pol_rec.policyholder_name}\n"
                    f"- **Policy Period:** {pol_rec.policy_start_date} to {pol_rec.policy_end_date}\n"
                    f"- **Sum Insured:** ₹{pol_rec.sum_insured_inr:,.2f}\n"
                    f"- **Remaining Balance:** **₹{pol_rec.remaining_sum_insured_inr:,.2f}**\n"
                    f"- **Cumulative Bonus (NCB):** ₹{pol_rec.cumulative_bonus_inr:,.2f}\n"
                    f"- **Policy Status:** {pol_rec.status}\n\n"
                    f"*(Notice: Synthetic simulation record for local test verification only)*"
                )
                return AgentResponse(
                    query=query,
                    classification=classification,
                    answer=answer,
                    is_mock_data=True,
                    mock_notice=pol_rec.notice,
                    execution_time_ms=round(elapsed, 2),
                )

        # If ID not found in synthetic database
        answer = (
            f"{PERSONAL_MOCK_BANNER}"
            f"No synthetic test record was found matching `{policy_id or claim_id}`.\n\n"
            f"**Available Local Test Records:**\n"
            f"- Policies: `{', '.join(self.customer_service.list_test_policy_numbers())}`\n"
            f"- Claims: `{', '.join(self.customer_service.list_test_claim_ids())}`\n\n"
            f"*Security reminder: Never share real passwords, OTPs, or Aadhaar numbers in chat.*"
        )
        return AgentResponse(
            query=query,
            classification=classification,
            answer=answer,
            is_mock_data=True,
            execution_time_ms=round(elapsed, 2),
        )

    def _handle_product_query(
        self,
        query: str,
        classification: QueryClassification,
        start_time: float,
    ) -> Optional[AgentResponse]:
        """Check if product document is verified or pending."""
        query_lower = query.lower()
        # If query is a general plan comparison or buyer recommendation query, let ChromaDB handle it
        comparison_keywords = [
            "compare", "comparison", "recommend", "which", "best", "options",
            "senior citizen", "plans", "list", "checklist", "difference", "vs", "versus", "offer"
        ]
        if any(w in query_lower for w in comparison_keywords):
            return None

        insurer = classification.detected_insurer
        if not insurer:
            return None

        # Search ChromaDB for this specific insurer
        product_filter = {
            "insurer_id": insurer,
            "status": "current",
        }
        matching_chunks = self.retrieval_engine.query(
            query_text=query,
            top_k=settings.top_k_results,
            filters=product_filter,
        )

        # If verified chunks exist for this insurer, proceed with standard generation
        if matching_chunks:
            return None

        # If no verified chunks exist for this insurer, provide helpful pending guidance
        product = classification.detected_product or "Health Plan"
        domain = OFFICIAL_DOMAINS.get(insurer, "https://irdai.gov.in")
        notice = PRODUCT_PENDING_TEMPLATE.format(
            insurer=insurer.replace("_", " "),
            product=product,
            domain=domain,
        )
        elapsed = (time.perf_counter() - start_time) * 1000

        return AgentResponse(
            query=query,
            classification=classification,
            answer=notice,
            sources=[],
            insufficient_evidence=True,
            execution_time_ms=round(elapsed, 2),
        )

    @staticmethod
    def _deduplicate_sources(sources: List[ChunkMetadata]) -> List[ChunkMetadata]:
        seen = set()
        unique = []
        for s in sources:
            key = (s.source_id, s.page_number, s.section_path)
            if key not in seen:
                seen.add(key)
                unique.append(s)
        return unique
