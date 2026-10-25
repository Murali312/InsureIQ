"""Unit tests for configuration validation, secret masking, and independent credentials."""

import pytest
from src.config import Settings, mask_secret


def test_mask_secret():
    """Verify secrets are masked and never exposed in full."""
    assert mask_secret(None) == "[NOT SET]"
    assert mask_secret("") == "[NOT SET]"
    assert mask_secret("short") == "****"
    masked = mask_secret("sk-proj-1234567890abcdef")
    assert masked == "sk-...cdef"
    assert "1234567890" not in masked


def test_independent_credentials():
    """Ensure chat credentials and embedding credentials are kept completely distinct."""
    s = Settings(
        OPENAI_API_KEY="sk-chat-key-1111",
        OPENAI_MODEL="gpt-4o-mini",
        EMBEDDING_PROVIDER="openai",
        OPENAI_EMBEDDING_API_KEY="sk-emb-key-9999",
        OPENAI_EMBEDDING_MODEL="text-embedding-3-small",
    )
    assert s.openai_api_key == "sk-chat-key-1111"
    assert s.openai_embedding_api_key == "sk-emb-key-9999"
    assert s.openai_api_key != s.openai_embedding_api_key


def test_missing_chat_credential_validation():
    """Ensure missing chat credentials trigger explicit ValueError."""
    s = Settings(OPENAI_API_KEY=None)
    with pytest.raises(ValueError, match="OPENAI_API_KEY is missing or empty"):
        s.validate_chat_credentials()


def test_missing_embedding_credential_validation():
    """Ensure missing embedding credentials trigger explicit ValueError when provider is openai."""
    s = Settings(
        EMBEDDING_PROVIDER="openai",
        OPENAI_EMBEDDING_API_KEY=None,
    )
    with pytest.raises(ValueError, match="OPENAI_EMBEDDING_API_KEY is missing or empty"):
        s.validate_embedding_credentials()


def test_local_embedding_provider_does_not_require_api_key():
    """Local embedding provider does not require OPENAI_EMBEDDING_API_KEY."""
    s = Settings(
        EMBEDDING_PROVIDER="local",
        OPENAI_EMBEDDING_API_KEY=None,
    )
    # Should not raise
    s.validate_embedding_credentials()
    assert s.is_embedding_ready() is True
