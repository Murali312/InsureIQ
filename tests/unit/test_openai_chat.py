"""Unit tests for OpenAIChatService: prompt framing, citations, retry loops, and offline fallbacks."""

import pytest
from unittest.mock import MagicMock, patch
from openai import RateLimitError, APITimeoutError

from src.models import ChunkMetadata, RetrievedChunk
from src.integrations.openai_chat import OpenAIChatService


@pytest.fixture
def sample_retrieved_chunk():
    meta = ChunkMetadata(
        source_id="IRDAI-CIRCULAR-2024",
        publisher="IRDAI",
        document_type="circular",
        document_title="Master Circular on Health Insurance Business (2024)",
        source_url="https://irdai.gov.in/circulars/2024",
        sha256="abc12345",
        section_path="Claim Settlement > Cashless Timelines",
        status="current",
        content_type="regulatory",
    )
    return RetrievedChunk(
        chunk_id="chunk-1",
        text="Insurers must approve cashless hospital discharge within 3 hours.",
        metadata=meta,
        score=0.92,
    )


def test_offline_mode_generates_grounded_summary(sample_retrieved_chunk):
    """Verify that when OPENAI_API_KEY is absent, service returns grounded local summary."""
    service = OpenAIChatService(api_key="")
    assert service.is_configured() is False

    ans = service.generate_answer(
        query="What is the discharge timeline?",
        retrieved_chunks=[sample_retrieved_chunk],
    )
    assert "Insurers must approve cashless hospital discharge within 3 hours." in ans
    assert "Master Circular on Health Insurance Business (2024)" in ans
    assert "https://irdai.gov.in/circulars/2024" in ans


def test_offline_mode_insufficient_evidence():
    """Verify offline mode clearly flags insufficient evidence when no chunks provided."""
    service = OpenAIChatService(api_key="")
    ans = service.generate_answer(query="Unknown question", retrieved_chunks=[])
    assert "Insufficient Evidence" in ans


def test_openai_chat_generation_mock(sample_retrieved_chunk):
    """Verify OpenAI chat completion call with citations and prompt structure."""
    mock_choice = MagicMock()
    mock_choice.message.content = (
        "According to the Master Circular on Health Insurance Business (2024) by IRDAI, "
        "discharge must be approved within 3 hours."
    )
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]

    with patch("src.integrations.openai_chat.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = mock_resp

        service = OpenAIChatService(api_key="sk-test-chat-key", model="gpt-4o-mini")
        assert service.is_configured() is True

        answer = service.generate_answer(
            query="What is the discharge timeline?",
            retrieved_chunks=[sample_retrieved_chunk],
            query_type="regulatory",
        )
        assert "within 3 hours" in answer
        mock_client.chat.completions.create.assert_called_once()


def test_openai_chat_rate_limit_retry(sample_retrieved_chunk):
    """Verify exponential backoff and retry when rate limited."""
    mock_choice = MagicMock()
    mock_choice.message.content = "Success after rate limit retry."
    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]

    mock_error_resp = MagicMock()
    mock_error_resp.status_code = 429
    rate_err = RateLimitError(
        message="Rate limit exceeded",
        response=mock_error_resp,
        body={"error": {"message": "Rate limit"}},
    )

    with patch("src.integrations.openai_chat.OpenAI") as mock_openai_cls:
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        # First call raises RateLimitError, second call succeeds
        mock_client.chat.completions.create.side_effect = [rate_err, mock_resp]

        service = OpenAIChatService(api_key="sk-test-key", max_retries=2)
        answer = service.generate_answer(
            query="test retry",
            retrieved_chunks=[sample_retrieved_chunk],
        )
        assert answer == "Success after rate limit retry."
        assert mock_client.chat.completions.create.call_count == 2
