# India Health Insurance Knowledge Base — Production-Oriented Starter

## Purpose
This starter pack defines a source-controlled, multi-insurer RAG knowledge base for an India-focused health insurance assistant. It deliberately does **not** invent insurer-specific policy terms. The source registry contains official regulator pages; product-specific insurer documents must be added only after their exact product, version and official URL are verified.

## Important distinction
- `knowledge/general/`: general concepts/FAQs that can answer common questions without customer APIs.
- `knowledge/regulatory/`: official IRDAI regulations, circulars, FAQs and policyholder guidance.
- `knowledge/insurers/<INSURER>/<PRODUCT>/<VERSION>/`: exact insurer product wording, Customer Information Sheet (CIS), policy schedule templates if public, add-ons, endorsements and claim procedures. Never mix policy documents from different products.
- Customer-specific facts (claim status, available sum insured, submitted documents, policy dates) belong in authenticated API/database tools, not this RAG knowledge base.

## Verified official seed sources
See `metadata/source_registry.csv`. Seed links are official IRDAI pages discovered during preparation. Check the page for the latest revision before ingestion; publication dates and current status should be read from the source page/document itself, not guessed.

## Source acceptance workflow
1. Open the source URL and confirm the publisher/domain is official.
2. Record exact title, document/product identifier, publication/effective date, retrieval date and URL.
3. Download the original PDF/HTML; do not ingest marketing summaries as if they were contract wording.
4. For insurer products, verify product name, UIN (where present), version/effective date, Customer Information Sheet, base wording and add-on wording.
5. Compute SHA-256 of the downloaded file and store it in the source registry.
6. Extract text and inspect tables/page structure. OCR scanned PDFs and manually spot-check extraction.
7. Chunk by section/clause, preserving page, heading, product and version metadata.
8. Mark older versions as superseded rather than silently deleting history. Retrieval must filter to current/effective documents for current-policy questions.
9. Re-index locally in ChromaDB. During AWS migration, upload the same source originals to S3 and ingest into Bedrock Knowledge Bases or another compatible managed index.
10. Run retrieval and answer evaluations before publishing a new source version.

## Suggested metadata for each chunk
`source_id`, `publisher`, `insurer_id`, `product_name`, `product_uin`, `document_type`, `document_title`, `document_version`, `published_date`, `effective_from`, `effective_to`, `retrieved_at`, `source_url`, `sha256`, `page_number`, `section_path`, `language`, `jurisdiction`, `status` (`current`, `superseded`, `under_review`), `content_type`, `is_official_source`.

## Retrieval rules
- General concepts: search general FAQ/education collection.
- Regulatory questions: prioritize current official IRDAI sources.
- Product coverage questions: require insurer + product identification; filter by current applicable version and cite clause/page.
- If product or version is unknown: ask a clarification question; do not generalize one insurer's terms to another.
- Personal claim/policy status, balances and documents: call authorized authenticated API, never infer from static documents.
- Unsupported/contradictory evidence: state uncertainty and escalate to insurer/customer support.
- Never present an AI answer as a binding coverage/claim decision.

## Proposed environment configuration
Local:
- ChromaDB persistent path: `./vector_store/chroma`
- Local embedding model: `sentence-transformers/all-MiniLM-L6-v2`
- Original documents remain in `knowledge/`
- Keep the index reproducible from source files; do not commit the generated vector database to Git.

AWS:
- Store approved source documents in a versioned S3 bucket.
- Use Bedrock Knowledge Bases or a hosted vector store; re-ingest using the chosen AWS embedding model.
- Preserve the same source metadata and retrieval interface.
- Store secrets in Secrets Manager; apply least-privilege IAM and logging redaction.

## Production warning
This is an architecture and source-catalogue starter, not legal advice or an exhaustive/current corpus. Official regulations and insurer products can change. Before production, verify the current consolidated regulations/circulars and obtain the exact applicable policy documents. No real insurer API access is implied by this knowledge base.
