"""Base retrieval engine interface supporting ChromaDB and future Bedrock Knowledge Bases."""

from __future__ import annotations

import abc
from typing import List, Optional, Dict, Any
from src.models import RetrievedChunk


class BaseRetrievalEngine(abc.ABC):
    """Abstract retrieval engine interface.

    Allows interchangeable vector backends (e.g. local ChromaDB vs. Amazon Bedrock Knowledge Bases)
    without modifying agent orchestrator logic.
    """

    @abc.abstractmethod
    def query(
        self,
        query_text: str,
        top_k: int = 4,
        filters: Optional[Dict[str, Any]] = None,
        min_relevance_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        """Query the knowledge base for relevant chunks matching filters and threshold."""
        pass

    @abc.abstractmethod
    def index_documents(
        self,
        chunks: List[Dict[str, Any]],
    ) -> int:
        """Index a list of chunk dicts into the underlying vector store."""
        pass

    @abc.abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Return collection size, active provider, model name, and metadata stats."""
        pass
