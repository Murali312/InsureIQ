"""Prompt templates and safety guardrails."""

INSUFFICIENT_EVIDENCE_TEMPLATE = (
    "⚠️ **Insufficient Evidence in Local Knowledge Base:**\n\n"
    "We could not locate verified official documentation in our indexed knowledge base "
    "to answer this specific question with certainty.\n\n"
    "**Why this happens:**\n"
    "- To protect you against fabricated or outdated insurance details, this assistant strictly refuses "
    "to guess or invent policy terms.\n"
    "- Specific individual policy clauses or newly launched riders may be pending verification in our source registry.\n\n"
    "**Recommended Next Steps & Support Contacts:**\n"
    "1. **IRDAI Bima Bharosa National Helpline (Toll-Free):** `155255` or `1800 4254 732` (complaints@irdai.gov.in)\n"
    "2. **Official Regulatory Portal:** https://irdai.gov.in\n"
    "3. **Customer Information Sheet (CIS):** Download the verified CIS directly from your insurer's official website.\n"
    "4. Check the **Source Registry** in the sidebar to review verified vs pending documents."
)

PRODUCT_PENDING_TEMPLATE = (
    "📋 **Product Source Pending Verification:**\n\n"
    "You inquired about **{insurer} - {product}**.\n\n"
    "In accordance with our strict factual verification policy, we do NOT generalize terms from other insurers "
    "or invent coverage details when an official contract document is not yet verified in our corpus.\n\n"
    "**Document Status:** Currently listed in `metadata/insurer_product_source_template.csv` as `pending_manual_verification`.\n\n"
    "**Official Insurer Domain:** {domain}\n\n"
    "**Official Support Channels:**\n"
    "- Please visit the insurer's official website or consult their Customer Information Sheet (CIS).\n"
    "- For urgent policy or claim inquiries, call the insurer's customer care helpline or contact IRDAI Bima Bharosa at **155255** / **1800 4254 732**."
)

PERSONAL_MOCK_BANNER = (
    "> 🧪 **SYNTHETIC TEST DATA DEMO**\n"
    "> *The record below is generated from local synthetic test data for integration verification. "
    "No real insurer credentials or live databases are connected.*\n\n"
)
