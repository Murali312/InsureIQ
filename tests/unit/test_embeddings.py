"""Unit tests for embedding providers: dimension checks, normalization, and mock OpenAI embedding calls."""

import numpy as np
import pytest
from unittest.mock import MagicMock, patch

from src.retrieval.embeddings import (
    FallbackHashEmbeddingProvider,
    OpenAIEmbeddingProvider,
    get_embedding_provider,
)


def test_fallback_hash_embedding_provider():
    """Verify fallback embedding generates normalized vectors of requested dimension."""
    provider = FallbackHashEmbeddingProvider(dimension=128)
    assert provider.dimension == 128
    assert provider.provider_name == "fallback"

    texts = ["Health insurance waiting period", "Cashless hospital admission"]
    vectors = provider.embed_texts(texts)
    assert len(vectors) == 2
    assert len(vectors[0]) == 128
    assert len(vectors[1]) == 128

    # Vectors should be normalized (L2 norm ~ 1.0)
    norm0 = np.linalg.norm(vectors[0])
    norm1 = np.linalg.norm(vectors[1])
    assert pytest.approx(norm0, rel=1e-3) == 1.0
    assert pytest.approx(norm1, rel=1e-3) == 1.0

    # Query embedding should match single embed
    query_vec = provider.embed_query(texts[0])
    assert query_vec == vectors[0]


def test_openai_embedding_provider_mock():
    """Verify OpenAIEmbeddingProvider batches calls and parses responses using mock client."""
    mock_resp = MagicMock()
    mock_item_0 = MagicMock()
    mock_item_0.index = 0
    mock_item_0.embedding = [0.1] * 1536

    mock_item_1 = MagicMock()
    mock_item_1.index = 1
    mock_item_1.embedding = [0.2] * 1536

    mock_resp.data = [mock_item_0, mock_item_1]

    with patch("openai.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.embeddings.create.return_value = mock_resp

        provider = OpenAIEmbeddingProvider(
            api_key="sk-test-embedding-key",
            model="text-embedding-3-small",
        )
        assert provider.dimension == 1536
        assert provider.provider_name == "openai"

        res = provider.embed_texts(["Doc 1", "Doc 2"])
        assert len(res) == 2
        assert len(res[0]) == 1536
        mock_client.embeddings.create.assert_called_once()


def test_openai_embedding_provider_missing_key():
    """Ensure OpenAIEmbeddingProvider raises ValueError when key is missing."""
    with pytest.raises(ValueError, match="OPENAI_EMBEDDING_API_KEY is not configured"):
        OpenAIEmbeddingProvider(api_key="", model="text-embedding-3-small")
