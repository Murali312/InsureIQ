"""Intent classification and entity extraction for insurance queries."""

from __future__ import annotations

import re
from typing import Optional, Tuple
from src.models import QueryClassification

# Known Indian Health Insurers and variations
INSURERS_MAP = {
    "hdfc": "HDFC_ERGO",
    "hdfc ergo": "HDFC_ERGO",
    "icici": "ICICI_Lombard",
    "icici lombard": "ICICI_Lombard",
    "star": "Star_Health",
    "star health": "Star_Health",
    "niva": "Niva_Bupa",
    "niva bupa": "Niva_Bupa",
    "max bupa": "Niva_Bupa",
    "care": "Care_Health",
    "care health": "Care_Health",
    "religare": "Care_Health",
    "aditya birla": "Aditya_Birla_Health",
    "aditya birla health": "Aditya_Birla_Health",
}

# Known products
PRODUCTS_LIST = [
    "optima secure",
    "optima restore",
    "comprehensive",
    "family health optima",
    "reassure",
    "health companion",
    "care supreme",
    "care advantage",
    "activ health",
    "activ fit",
    "elevate",
]

GRIEVANCE_PATTERNS = [
    r"\b(reject|rejected|rejection)\b",
    r"\b(denied|denial)\b",
    r"\b(delay|delayed)\b",
    r"\brepudiat\w*\b",
    r"\b(dispute|disputed)\b",
    r"\bgrievance\b",
    r"\bombudsman\b",
    r"\bbima\s+bharosa\b",
    r"\bigms\b",
    r"\bescalat\w*\b",
    r"\bcomplain\w*\b",
]

PERSONAL_PATTERNS = [
    r"\bclaim\s+status\b",
    r"\bstatus\s+of\s+my\b",
    r"\btrack\s+my\b",
    r"\bhow\s+much\s+(sum\s+insured|balance|money)\s+(do\s+i\s+have|left|remaining)\b",
    r"\bremaining\s+sum\s+insured\b",
    r"\bdocuments?\s+(have\s+i\s+submitted|submitted)\b",
    r"\bmy\s+claim\b",
    r"\bmy\s+policy\b",
    r"\bmy\s+policy\s+(details|status|number)\b",
    r"\bstatus\s+of\s+my\s+personal\s+claim\b",
    r"\bmy\s+personal\s+claim\b",
    r"\bclm-\d+",
    r"\bpol-\w+-\d+",
]

RECOMMENDATION_PATTERNS = [
    r"\bcompare\b",
    r"\bcomparison\b",
    r"\brecommend\w*\b",
    r"\bwhich\s+(health\s+insurance|plan|policy|insurers?)\b",
    r"\bbest\s+(health\s+insurance|plan|policy|for\s+senior)\b",
    r"\bshould\s+i\s+(buy|choose|compare)\b",
    r"\bwhat\s+should\s+i\s+check\b",
    r"\bwhich\s+is\s+better\b",
    r"\bsuitable\s+for\b",
]

REGULATORY_PATTERNS = [
    r"\birdai\b",
    r"\bcircular\b",
    r"\bmaster\s+circular\b",
    r"\bfree\s+look\b",
    r"\bgrace\s+period\b",
    r"\bportability\b",
    r"\bmigration\b",
    r"\b1\s*hour\b",
    r"\b3\s*hours?\b",
    r"\bmoratorium\b",
    r"\bsection\s+45\b",
    r"\bcis\b",
    r"\bcustomer\s+information\s+sheet\b",
    r"\bmax(imum)?\s+ped\s+waiting\b",
]


class IntentClassifier:
    """Classifies user queries into 5 structured insurance types:
    Type 1 — General Health Insurance Education
    Type 2 — Plan Recommendations or Comparisons
    Type 3 — Regulatory & Official Policy Rules
    Type 4 — Personal Account / Claim Details
    Type 5 — Grievances & Claim Disputes
    """

    def classify(self, query: str) -> QueryClassification:
        query_clean = query.strip()
        query_lower = query_clean.lower()

        detected_insurer: Optional[str] = None
        for key, slug in INSURERS_MAP.items():
            pattern = rf"\b{re.escape(key)}\b"
            if re.search(pattern, query_lower):
                detected_insurer = slug
                break

        detected_product: Optional[str] = None
        for prod in PRODUCTS_LIST:
            if prod in query_lower:
                detected_product = prod.title()
                break

        # Check for explicit policy/claim IDs first
        has_explicit_id = bool(re.search(r"\b(clm-\d+|pol-\w+-\d+)\b", query_lower))

        # Check for Grievance & Dispute Redressal intent (Type 5 - e.g. "My claim was rejected. What should I do?")
        for pat in GRIEVANCE_PATTERNS:
            if re.search(pat, query_lower) and not has_explicit_id:
                return QueryClassification(
                    intent="regulatory",
                    confidence=0.95,
                    query_type="Type 5 — Grievances & Claim Disputes",
                    detected_insurer=detected_insurer,
                    detected_product=detected_product,
                    reasoning="Query relates to claim rejection, delay, dispute, or grievance escalation (GRO / Bima Bharosa / Ombudsman).",
                )

        # Check for explicit policy/claim IDs or personal claim tracking (Type 4)
        if has_explicit_id:
            return QueryClassification(
                intent="personal_claim_policy",
                confidence=0.98,
                query_type="Type 4 — Personal Account / Claim Details",
                detected_insurer=detected_insurer,
                detected_product=detected_product,
                reasoning="Query provides an explicit policy or claim tracking number.",
            )

        for pat in PERSONAL_PATTERNS:
            if re.search(pat, query_lower):
                return QueryClassification(
                    intent="personal_claim_policy",
                    confidence=0.92,
                    query_type="Type 4 — Personal Account / Claim Details",
                    detected_insurer=detected_insurer,
                    detected_product=detected_product,
                    reasoning="Query requests personal account/claim status or remaining sum insured.",
                )

        # Check for Recommendation & Comparison intent (Type 2)
        for pat in RECOMMENDATION_PATTERNS:
            if re.search(pat, query_lower):
                return QueryClassification(
                    intent="product_specific",
                    confidence=0.90,
                    query_type="Type 2 — Plan Recommendations or Comparisons",
                    detected_insurer=detected_insurer,
                    detected_product=detected_product,
                    reasoning="Query seeks health insurance plan comparison, senior citizen recommendations, or buying checklist.",
                )

        # Check for Regulatory & Policy Rules intent (Type 3)
        for pat in REGULATORY_PATTERNS:
            if re.search(pat, query_lower):
                return QueryClassification(
                    intent="regulatory",
                    confidence=0.90,
                    query_type="Type 3 — Regulatory & Policy Rules",
                    detected_insurer=detected_insurer,
                    detected_product=detected_product,
                    reasoning="Query references IRDAI regulations, Master Circulars, statutory waiting periods, or CIS requirements.",
                )

        # Check for product-specific intent (insurer or product detected without comparison words)
        if detected_insurer or detected_product:
            return QueryClassification(
                intent="product_specific",
                confidence=0.90,
                query_type="Type 2 — Plan Recommendations or Comparisons",
                detected_insurer=detected_insurer,
                detected_product=detected_product,
                reasoning=f"Identified insurer '{detected_insurer}' or product '{detected_product}'.",
            )

        # General health insurance FAQ keywords (Type 1)
        general_keywords = [
            "premium", "sum insured", "deductible", "co-pay", "copay", "co-payment",
            "waiting period", "pre-existing", "ped", "cashless", "reimbursement",
            "network hospital", "sub-limit", "sublimit", "family floater", "individual policy",
            "tpa", "critical illness", "opd", "day care", "daycare", "domiciliary",
            "health insurance", "no claim bonus", "ncb", "claim", "coverage", "apply",
            "condition", "eligibility", "senior citizen", "senior citizens", "diabetes",
            "hypertension", "blood pressure", "documents", "document", "insurers", "companies"
        ]
        for kw in general_keywords:
            if kw in query_lower:
                return QueryClassification(
                    intent="general_faq",
                    confidence=0.88,
                    query_type="Type 1 — General Health Insurance Education",
                    reasoning=f"Identified standard health insurance concept '{kw}'.",
                )

        # If general interrogative question about health or insurance
        if any(w in query_lower for w in ["what", "how", "why", "can", "is", "where", "does", "which"]):
            return QueryClassification(
                intent="general_faq",
                confidence=0.75,
                query_type="Type 1 — General Health Insurance Education",
                reasoning="General inquiry regarding health insurance terminology or rules.",
            )

        return QueryClassification(
            intent="out_of_scope",
            confidence=0.50,
            query_type="Out of Scope",
            reasoning="Query does not appear related to Indian health insurance concepts, policies, or regulations.",
        )


# Global singleton classifier instance
classifier = IntentClassifier()
