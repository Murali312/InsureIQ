"""Embedding provider abstractions supporting OpenAI, local SentenceTransformers, and test fallbacks."""

from __future__ import annotations

import abc
import hashlib
import logging
import math
from typing import List, Optional
import numpy as np

from src.config import settings

logger = logging.getLogger(__name__)


class BaseEmbeddingProvider(abc.ABC):
    """Abstract base class for text embedding generation."""

    @abc.abstractmethod
    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Generate vector embeddings for a list of texts."""
        pass

    @abc.abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generate vector embedding for a single search query."""
        pass

    @property
    @abc.abstractmethod
    def dimension(self) -> int:
        """Vector dimension."""
        pass

    @property
    @abc.abstractmethod
    def model_name(self) -> str:
        """Name of the embedding model."""
        pass

    @property
    @abc.abstractmethod
    def provider_name(self) -> str:
        """Name of the provider (e.g. 'openai', 'local', 'fallback')."""
        pass


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """Embedding provider using OpenAI's API with OPENAI_EMBEDDING_API_KEY."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self._api_key = api_key if api_key is not None else settings.openai_embedding_api_key
        self._model = model or settings.openai_embedding_model
        if not self._api_key or not self._api_key.strip():
            raise ValueError(
                "OPENAI_EMBEDDING_API_KEY is not configured. Please supply a valid key in .env "
                "or switch EMBEDDING_PROVIDER to 'local'."
            )
        try:
            import openai
            self._client = openai.OpenAI(api_key=self._api_key, timeout=settings.request_timeout_seconds)
        except ImportError:
            raise ImportError("openai package is required for OpenAIEmbeddingProvider.")

        # Default dimension for text-embedding-3-small is 1536
        self._dimension = 1536 if "3-small" in self._model else 3072 if "3-large" in self._model else 1536

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def provider_name(self) -> str:
        return "openai"

    def embed_texts(self, texts: List[str], batch_size: int = 64) -> List[List[float]]:
        if not texts:
            return []
        all_embeddings: List[List[float]] = []
        for i in range(0, len(texts), batch_size):
            batch = [t if t.strip() else " " for t in texts[i : i + batch_size]]
            resp = self._client.embeddings.create(input=batch, model=self._model)
            # Sort by index to maintain original order
            sorted_data = sorted(resp.data, key=lambda x: x.index)
            all_embeddings.extend([d.embedding for d in sorted_data])
        return all_embeddings

    def embed_query(self, query: str) -> List[float]:
        res = self.embed_texts([query])
        return res[0]


class LocalSentenceTransformerEmbeddingProvider(BaseEmbeddingProvider):
    """Embedding provider using local SentenceTransformers (all-MiniLM-L6-v2)."""

    def __init__(self, model_name: Optional[str] = None):
        self._model_name = model_name or settings.local_embedding_model
        try:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(self._model_name)
            self._dimension = self._model.get_sentence_embedding_dimension() or 384
        except Exception as e:
            logger.warning("Failed to initialize SentenceTransformer '%s': %s", self._model_name, e)
            raise

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def provider_name(self) -> str:
        return "local"

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []
        embeddings = self._model.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        embedding = self._model.encode(query, convert_to_numpy=True, normalize_embeddings=True)
        return embedding.tolist()


class FallbackHashEmbeddingProvider(BaseEmbeddingProvider):
    """Deterministic normalized 384-d dense embedding provider for offline/fallback test execution."""

    def __init__(self, dimension: int = 384):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    @property
    def model_name(self) -> str:
        return "fallback-hash-384"

    @property
    def provider_name(self) -> str:
        return "fallback"

    def _embed_single(self, text: str) -> List[float]:
        vec = np.zeros(self._dim, dtype=np.float32)
        words = text.lower().split()
        if not words:
            vec[0] = 1.0
            return vec.tolist()

        for w in words:
            # Deterministic hash bucket
            h = int(hashlib.md5(w.encode("utf-8")).hexdigest(), 16)
            idx = h % self._dim
            sign = 1.0 if ((h >> 4) & 1) else -1.0
            vec[idx] += sign

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec /= norm
        return vec.tolist()

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        return [self._embed_single(t) for t in texts]

    def embed_query(self, query: str) -> List[float]:
        return self._embed_single(query)


def get_embedding_provider(
    provider_override: Optional[str] = None,
    allow_fallback: bool = True,
) -> BaseEmbeddingProvider:
    """Factory to return configured embedding provider."""
    target_provider = (provider_override or settings.embedding_provider).lower()

    if target_provider == "openai":
        try:
            return OpenAIEmbeddingProvider()
        except Exception as e:
            logger.warning("OpenAI embedding initialization failed: %s", e)
            if not allow_fallback:
                raise
            logger.info("Attempting local SentenceTransformer fallback...")
            try:
                return LocalSentenceTransformerEmbeddingProvider()
            except Exception as local_err:
                logger.warning("SentenceTransformer fallback failed: %s. Using FallbackHashEmbeddingProvider.", local_err)
                return FallbackHashEmbeddingProvider()

    elif target_provider == "local":
        try:
            return LocalSentenceTransformerEmbeddingProvider()
        except Exception as e:
            logger.warning("SentenceTransformer initialization failed: %s", e)
            if not allow_fallback:
                raise
            return FallbackHashEmbeddingProvider()

    elif target_provider == "fallback":
        return FallbackHashEmbeddingProvider()

    raise ValueError(f"Unknown embedding provider: {target_provider}")
