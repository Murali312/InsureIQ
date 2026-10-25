import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from src.config import BASE_DIR, settings
from src.retrieval.chroma_engine import ChromaRetrievalEngine
from src.retrieval.embeddings import get_embedding_provider
from src.agent.orchestrator import HealthInsuranceAgent

engine = ChromaRetrievalEngine(
    persist_directory=BASE_DIR / "vector_store" / "chroma",
    collection_name=settings.collection_name,
    embedding_provider=get_embedding_provider(),
)
agent = HealthInsuranceAgent(retrieval_engine=engine)
query = "I am 24 years old, suggest me best health insurance for me"
res = agent.handle_query(query)

print("Status: SUCCESS")
print("Query:", query)
print("Intent:", res.classification.intent)
print("Query Type:", getattr(res.classification, "query_type", None))
print("Sources count:", len(res.sources))
print("\nAnswer:\n", res.answer)
