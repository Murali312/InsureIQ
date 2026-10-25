# System Architecture: India Health Insurance AI Agent

This document details the architectural design, component interactions, security boundaries, and AWS cloud migration path for the India Health Insurance AI Agent.

---

## 1. High-Level Architecture Diagram

```mermaid
flowchart TD
    subgraph Frontend["Streamlit Web UI (app.py)"]
        UI_Chat["Interactive Chat Interface"]
        UI_Status["System Health & Registry Panel"]
        UI_Persona["Synthetic Simulator Personas"]
    end

    subgraph Security["Security & Safety Guards (src/security.py)"]
        SSRF["SSRF Guard & Domain Allowlist"]
        Sanitizer["Input Sanitizer & Length Guard"]
        Fence["Untrusted Context Fence"]
    end

    subgraph CoreAgent["Agent Orchestration (src/agent/)"]
        Orchestrator["HealthInsuranceAgent"]
        Classifier["IntentClassifier"]
        PromptEngine["Grounded Prompt Engine"]
    end

    subgraph RetrievalLayer["Retrieval Abstraction (src/retrieval/)"]
        BaseEngine["BaseRetrievalEngine (Interface)"]
        ChromaEngine["ChromaRetrievalEngine (Local)"]
        BedrockEngine["BedrockKnowledgeBaseEngine (AWS)"]
        EmbeddingFactory["Embedding Provider Factory"]
    end

    subgraph Providers["Embedding Providers"]
        OpenAIEmb["OpenAI text-embedding-3-small"]
        LocalEmb["SentenceTransformers MiniLM-L6-v2"]
        FallbackEmb["Fallback Deterministic Hash"]
    end

    subgraph Knowledge["Local Knowledge Base (knowledge/)"]
        GenFAQ["knowledge/general/ (25+ FAQs)"]
        RegCirculars["knowledge/regulatory/ (IRDAI Circulars)"]
        Insurers["knowledge/insurers/ (Pending / CIS)"]
        Registry["metadata/source_registry.csv"]
    end

    subgraph Integrations["External & Integration Services"]
        OpenAIChat["OpenAIChatService (gpt-4o-mini)"]
        MockCustomer["MockCustomerProvider (Synthetic)"]
        WebRetriever["ControlledWebRetriever"]
    end

    UI_Chat --> Sanitizer --> Orchestrator
    Orchestrator --> Classifier

    Classifier -->|personal_claim_policy| MockCustomer
    Classifier -->|product_specific unverified| PromptEngine
    Classifier -->|general_faq or regulatory| BaseEngine

    BaseEngine --> ChromaEngine
    BaseEngine -.-> BedrockEngine
    ChromaEngine --> EmbeddingFactory
    EmbeddingFactory --> OpenAIEmb
    EmbeddingFactory --> LocalEmb
    EmbeddingFactory --> FallbackEmb

    ChromaEngine --> Knowledge
    Orchestrator --> Fence --> OpenAIChat
    OpenAIChat --> UI_Chat
    MockCustomer -->|SYNTHETIC DATA BANNER| UI_Chat
    WebRetriever --> SSRF
```

---

## 2. Sequence Diagram: Query Processing Flow

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Streamlit as Streamlit Frontend (app.py)
    participant Sanitizer as Security Sanitizer
    participant Agent as HealthInsuranceAgent
    participant Classifier as IntentClassifier
    participant Chroma as ChromaRetrievalEngine
    participant ChatService as OpenAIChatService
    participant MockAPI as MockCustomerProvider

    User->>Streamlit: Enters Query
    Streamlit->>Sanitizer: Sanitize Input (strip control chars, length limit)
    Sanitizer->>Agent: Clean Query Text
    Agent->>Classifier: Classify Intent (General, Regulatory, Product, Personal)

    alt Personal Claim / Policy Query
        Classifier-->>Agent: personal_claim_policy
        Agent->>MockAPI: Fetch Policy/Claim by ID
        MockAPI-->>Agent: Synthetic Record + SYNTHETIC TEST DATA Notice
        Agent-->>Streamlit: Return Response with Synthetic Banner
    else Unverified Product Query
        Classifier-->>Agent: product_specific (Missing verified CIS)
        Agent-->>Streamlit: Refuse to fabricate + point to official insurer portal
    else General FAQ or Regulatory Query
        Classifier-->>Agent: general_faq / regulatory
        Agent->>Chroma: Query Knowledge Base with Category & Version Filter
        Chroma-->>Agent: Relevant Verified Chunks (above relevance threshold)
        alt Low Relevance / No Chunks
            Agent-->>Streamlit: Return Insufficient Evidence Notice
        else Chunks Found
            Agent->>ChatService: Generate Grounded Answer (Wrapped in Untrusted Context)
            ChatService-->>Agent: Factual Answer + Citations (Title, Publisher, Section, URL)
            Agent-->>Streamlit: AgentResponse (Answer + Verified Sources)
        end
    end
    Streamlit-->>User: Display Formatted Message, Intent Tag & Citation Card
```

---

## 3. Dual Independent Credential Architecture

To prevent cross-service key leakage and support separate OpenAI organization accounts or rate limits:

| Environment Variable | Service Responsibility | Default Value | Notes |
| :--- | :--- | :--- | :--- |
| `OPENAI_API_KEY` | Chat Answer Generation | None (Required for LLM generation) | Read exclusively by `OpenAIChatService` |
| `OPENAI_MODEL` | Chat Completion Model | `gpt-4o-mini` | Low temperature (0.1) for factual precision |
| `EMBEDDING_PROVIDER` | Embedding Mode Selector | `openai` | Options: `openai` or `local` |
| `OPENAI_EMBEDDING_API_KEY` | Vector Embeddings | None (Required if `openai` provider) | Read exclusively by `OpenAIEmbeddingProvider` |
| `OPENAI_EMBEDDING_MODEL` | Vector Embedding Model | `text-embedding-3-small` | 1536-dimensional embeddings |
| `LOCAL_EMBEDDING_MODEL` | Local Offline Model | `sentence-transformers/all-MiniLM-L6-v2` | Used when `EMBEDDING_PROVIDER=local` |

### Embedding Model Compatibility Check
When `ChromaRetrievalEngine` connects to a persistent collection, it checks collection metadata (`embedding_model` and `dimension`). If a mismatch is detected (e.g., trying to query a `text-embedding-3-small` collection with `all-MiniLM-L6-v2`), the engine raises an explicit `ValueError`, preventing silent dimension corruption.

---

## 4. Controlled Public Web Retrieval & SSRF Defense

When optional live web retrieval is invoked:
1. **Pre-flight SSRF Validation:** `validate_url_for_ssrf(url)` checks scheme (`http`/`https`), ensures destination is in the approved official domain allowlist (`irdai.gov.in`, `bimabharosa.irdai.gov.in`, etc.), and resolves DNS to ensure the destination IP is not private (`10.0.0.0/8`, `192.168.0.0/16`, `172.16.0.0/12`), loopback (`127.0.0.1`), or AWS instance metadata (`169.254.169.254`).
2. **Redirect Safety:** Head responses are inspected; if redirected, the target URL is re-validated through the complete SSRF check.
3. **Resource Capping:** Maximum content download is capped at `1,048,576 bytes` (1 MB) with connection timeout enforcement.
4. **Untrusted Wrapper:** Downloaded text is treated as untrusted data, wrapped in context tags, and never executed as prompt instructions.

---

## 5. AWS Cloud Migration Architecture

When migrating from local ChromaDB to AWS:

```
[Approved Source Documents] 
         │
         ▼
[Amazon S3 Bucket (Versioned & Encrypted)]
         │
         ▼
[Amazon Bedrock Knowledge Base] ── Titan Embeddings
         │
         ▼
[Bedrock Knowledge Base Runtime Retrieve API]
         │
         ▼
[BedrockKnowledgeBaseEngine] (Implements BaseRetrievalEngine)
         │
         ▼
[Agent Orchestrator]
```

- **S3 Bucket:** Hosts approved official circulars and verified Customer Information Sheets (CIS) with SSE-S3 encryption.
- **Bedrock Knowledge Bases:** Managed vector store (OpenSearch Serverless or Aurora PostgreSQL pgvector).
- **Secrets Manager:** Stores external API credentials with automatic secret rotation.
- **IAM Policies:** Follow least-privilege principles (`bedrock:Retrieve` only for knowledge base role).
