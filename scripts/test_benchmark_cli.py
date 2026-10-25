"""Run 15 benchmark questions through the real agent and print results."""
import sys
from pathlib import Path

# Add project root and configure UTF-8 output
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import BASE_DIR, settings
from src.retrieval.chroma_engine import ChromaRetrievalEngine
from src.retrieval.embeddings import get_embedding_provider
from src.agent.orchestrator import HealthInsuranceAgent

real_chroma_dir = BASE_DIR / "vector_store" / "chroma"
emb_provider = get_embedding_provider()
engine = ChromaRetrievalEngine(
    persist_directory=real_chroma_dir,
    collection_name=settings.collection_name,
    embedding_provider=emb_provider,
)
agent = HealthInsuranceAgent(retrieval_engine=engine)

questions = [
    "What is health insurance?",
    "What conditions do I need to meet to apply for health insurance in India?",
    "Can a senior citizen buy health insurance?",
    "Which health insurance plans should senior citizens compare?",
    "Can someone with diabetes apply for health insurance?",
    "What is a pre-existing disease waiting period?",
    "What is the difference between an individual policy and a family floater?",
    "What is a co-payment?",
    "What documents are generally needed to apply?",
    "What should I check before choosing a health insurance policy?",
    "How does a cashless claim work?",
    "Which insurers offer health insurance in India?",
    "Compare senior citizen policies from the supported insurers.",
    "My claim was rejected. What should I do?",
    "What is the status of my personal claim?",
]

print("\n" + "=" * 70)
print("TESTING 15 BENCHMARK QUESTIONS AGAINST REAL KNOWLEDGE BASE")
print("=" * 70)

for idx, q in enumerate(questions, 1):
    res = agent.handle_query(q)
    print(f"\n[Question {idx}] {q}")
    print(f"Intent:       {res.classification.intent} | Type: {res.classification.query_type}")
    print(f"Chunks:       {len(res.sources)} | Insufficient Evidence: {res.insufficient_evidence} | Mock Data: {res.is_mock_data}")
    print(f"Answer:\n{res.answer[:280]}...")
    print("-" * 70)
