"""Integration tests for ControlledWebRetriever: SSRF validation, mock HTML fetching, and timeout handling."""

import pytest
from unittest.mock import MagicMock, patch
import requests

from src.tools.web_search import ControlledWebRetriever
from src.security import SecurityError


@pytest.fixture
def retriever():
    return ControlledWebRetriever(timeout=5, max_bytes=500000)


def test_web_retriever_blocks_unauthorized_domain(retriever):
    """Verify retriever raises SecurityError when URL domain is outside allowlist."""
    with pytest.raises(SecurityError, match="not in the approved official domain allowlist"):
        retriever.fetch_verified_url("https://malicious-insurance-site.xyz/claims")


def test_web_retriever_mock_fetch(retriever):
    """Verify retriever fetches approved URL, calculates SHA-256, and extracts clean text."""
    html_content = b"""
    <html>
        <head><title>IRDAI Master Circular</title></head>
        <body><p>PED waiting period is reduced to 36 months.</p></body>
    </html>
    """
    mock_head = MagicMock()
    mock_head.url = "https://irdai.gov.in/circular.html"
    mock_head.headers = {"Content-Length": str(len(html_content))}

    mock_get = MagicMock()
    mock_get.url = "https://irdai.gov.in/circular.html"
    mock_get.status_code = 200
    mock_get.iter_content = MagicMock(return_value=[html_content])

    with patch.object(retriever.session, "head", return_value=mock_head), \
         patch.object(retriever.session, "get", return_value=mock_get):

        res = retriever.fetch_verified_url("https://irdai.gov.in/circular.html")
        assert res["url"] == "https://irdai.gov.in/circular.html"
        assert res["title"] == "IRDAI Master Circular"
        assert "PED waiting period is reduced to 36 months." in res["text"]
        assert len(res["sha256"]) == 64
        assert res["status_code"] == 200


def test_web_retriever_timeout_handling(retriever):
    """Verify connection timeouts raise standard TimeoutError."""
    with patch.object(retriever.session, "head", side_effect=requests.exceptions.Timeout("Connection timed out")):
        with pytest.raises(TimeoutError, match="timed out"):
            retriever.fetch_verified_url("https://irdai.gov.in/slow-page")
