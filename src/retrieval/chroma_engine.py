"""ChromaDB implementation of BaseRetrievalEngine with embedding validation and metadata filtering."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings

from src.config import settings
from src.models import ChunkMetadata, RetrievedChunk
from src.retrieval.base import BaseRetrievalEngine
from src.retrieval.embeddings import BaseEmbeddingProvider, get_embedding_provider

logger = logging.getLogger(__name__)


class ChromaRetrievalEngine(BaseRetrievalEngine):
    """ChromaDB persistent retrieval engine."""

    def __init__(
        self,
        persist_directory: Optional[Path | str] = None,
        collection_name: Optional[str] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ):
        self.persist_dir = Path(persist_directory) if persist_directory else settings.get_chroma_path()
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name or settings.collection_name
        self.embedding_provider = embedding_provider or get_embedding_provider()

        # Initialize Chroma persistent client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        self.collection = self._get_or_create_collection()

    def _get_or_create_collection(self):
        """Get or create collection and verify embedding model compatibility."""
        target_meta = {
            "embedding_provider": self.embedding_provider.provider_name,
            "embedding_model": self.embedding_provider.model_name,
            "dimension": self.embedding_provider.dimension,
            "hnsw:space": "cosine",
        }

        # Check existing collections
        existing_collections = [c.name for c in self.client.list_collections()]

        if self.collection_name in existing_collections:
            coll = self.client.get_collection(name=self.collection_name)
            meta = coll.metadata or {}

            saved_model = meta.get("embedding_model")
            saved_dim = meta.get("dimension")

            if saved_model and saved_model != self.embedding_provider.model_name:
                raise ValueError(
                    f"Incompatible embedding model detected! Collection '{self.collection_name}' was created with "
                    f"'{saved_model}' (dim={saved_dim}), but current configuration uses "
                    f"'{self.embedding_provider.model_name}' (dim={self.embedding_provider.dimension}). "
                    f"Please re-index into a separate collection or delete the existing vector store directory."
                )
            return coll

        return self.client.create_collection(
            name=self.collection_name,
            metadata=target_meta,
        )

    def query(
        self,
        query_text: str,
        top_k: int = 4,
        filters: Optional[Dict[str, Any]] = None,
        min_relevance_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        """Query knowledge base with metadata filters and relevance thresholding."""
        if not query_text or not query_text.strip():
            return []

        # Generate query embedding
        query_vec = self.embedding_provider.embed_query(query_text)

        # Build Chroma where filter
        where_conditions: List[Dict[str, Any]] = []

        # Default filter: Exclude superseded documents unless explicitly queried
        include_superseded = False
        if filters and filters.get("include_superseded"):
            include_superseded = True

        if not include_superseded:
            where_conditions.append({"status": {"$ne": "superseded"}})

        if filters:
            if filters.get("content_type"):
                where_conditions.append({"content_type": str(filters["content_type"])})
            if filters.get("insurer_id"):
                where_conditions.append({"insurer_id": str(filters["insurer_id"])})
            if filters.get("product_name"):
                where_conditions.append({"product_name": str(filters["product_name"])})
            if filters.get("document_type"):
                where_conditions.append({"document_type": str(filters["document_type"])})

        where_clause = None
        if len(where_conditions) == 1:
            where_clause = where_conditions[0]
        elif len(where_conditions) > 1:
            where_clause = {"$and": where_conditions}

        logger.info(
            "ChromaDB Query | Collection: '%s' | Provider: '%s' | Model: '%s' (dim=%d) | Top-K: %d | Where: %s",
            self.collection_name,
            self.embedding_provider.provider_name,
            self.embedding_provider.model_name,
            self.embedding_provider.dimension,
            top_k,
            where_clause,
        )

        try:
            results = self.collection.query(
                query_embeddings=[query_vec],
                n_results=top_k,
                where=where_clause if where_clause else None,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:
            logger.error("Chroma query failed: %s", e)
            return []

        threshold = min_relevance_score if min_relevance_score is not None else settings.min_relevance_score

        retrieved_chunks: List[RetrievedChunk] = []
        ids = results.get("ids", [[]])[0]
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0]

        for i, chunk_id in enumerate(ids):
            dist = distances[i] if i < len(distances) else 1.0
            # For cosine distance in Chroma: dist is between 0 and 2.
            # Similarity = max(0.0, 1.0 - (dist / 2.0))
            similarity = max(0.0, min(1.0, 1.0 - (dist / 2.0)))

            if similarity < threshold:
                continue

            meta_dict = metas[i] if i < len(metas) else {}
            chunk_meta = ChunkMetadata.from_chroma_metadata(meta_dict)

            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    text=docs[i] if i < len(docs) else "",
                    metadata=chunk_meta,
                    score=round(similarity, 4),
                )
            )

        source_ids = [c.metadata.source_id for c in retrieved_chunks]
        logger.info(
            "ChromaDB Result | Passed Threshold: %d/%d (threshold=%.2f) | Source IDs: %s",
            len(retrieved_chunks),
            len(ids),
            threshold,
            source_ids,
        )

        return retrieved_chunks

    def index_documents(
        self,
        chunks: List[Dict[str, Any]],
        batch_size: int = 32,
    ) -> int:
        """Batch index chunk dicts with embeddings and metadata."""
        if not chunks:
            return 0

        total_indexed = 0
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            ids = [b["id"] for b in batch]
            texts = [b["text"] for b in batch]
            metadatas = [b["metadata"] for b in batch]

            embeddings = self.embedding_provider.embed_texts(texts)

            self.collection.upsert(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas,
            )
            total_indexed += len(batch)

        return total_indexed

    def get_stats(self) -> Dict[str, Any]:
        """Return collection stats."""
        count = self.collection.count()
        return {
            "collection_name": self.collection_name,
            "document_count": count,
            "persist_directory": str(self.persist_dir),
            "embedding_provider": self.embedding_provider.provider_name,
            "embedding_model": self.embedding_provider.model_name,
            "dimension": self.embedding_provider.dimension,
        }
