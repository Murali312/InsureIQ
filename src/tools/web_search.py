"""Controlled public web retriever with SSRF protection, domain allowlist, and redirect checks."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import requests

from src.config import settings
from src.security import validate_url_for_ssrf, SecurityError
from src.ingestion.extractors import extract_html_content, compute_bytes_sha256

logger = logging.getLogger(__name__)


class ControlledWebRetriever:
    """Safe, controlled web content retriever for approved official domains only."""

    def __init__(
        self,
        timeout: Optional[int] = None,
        max_bytes: Optional[int] = None,
    ):
        self.timeout = timeout or settings.request_timeout_seconds
        self.max_bytes = max_bytes or settings.max_web_fetch_bytes
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "IndiaHealthInsuranceAIAgent-Verifier/1.0 (+https://irdai.gov.in-verifier)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        })

    def fetch_verified_url(self, url: str) -> Dict[str, Any]:
        """Fetch and extract text from an approved official URL with strict SSRF guards.

        Returns dict containing:
        - 'url': final validated URL
        - 'title': extracted page title
        - 'text': cleaned readable body text
        - 'sha256': sha256 checksum of raw body
        - 'retrieved_at_utc': ISO 8601 timestamp
        - 'status_code': HTTP status code
        """
        # Step 1: Pre-flight SSRF check
        is_safe, error_msg = validate_url_for_ssrf(url)
        if not is_safe:
            raise SecurityError(f"Security policy rejected URL: {error_msg}")

        try:
            # Step 2: Fetch headers first to verify content-type and length
            head_resp = self.session.head(
                url,
                timeout=self.timeout,
                allow_redirects=True,
            )

            # Validate redirect destination if redirected
            if head_resp.url != url:
                redir_safe, redir_err = validate_url_for_ssrf(head_resp.url)
                if not redir_safe:
                    raise SecurityError(f"Redirected to prohibited destination: {redir_err}")

            content_length = head_resp.headers.get("Content-Length")
            if content_length and int(content_length) > self.max_bytes:
                raise ValueError(
                    f"Remote resource size ({content_length} bytes) exceeds safety limit of {self.max_bytes} bytes."
                )

            # Step 3: Stream download with byte limit
            resp = self.session.get(
                url,
                timeout=self.timeout,
                stream=True,
                allow_redirects=True,
            )

            # Check final URL again
            if resp.url != url:
                final_safe, final_err = validate_url_for_ssrf(resp.url)
                if not final_safe:
                    raise SecurityError(f"Final URL violates security policy: {final_err}")

            raw_bytes = bytearray()
            for chunk in resp.iter_content(chunk_size=8192):
                raw_bytes.extend(chunk)
                if len(raw_bytes) > self.max_bytes:
                    raise ValueError(f"Downloaded content exceeded size limit of {self.max_bytes} bytes.")

            content_bytes = bytes(raw_bytes)
            sha256_hash = compute_bytes_sha256(content_bytes)

            # Step 4: Parse HTML
            extracted = extract_html_content(content_bytes)

            return {
                "url": resp.url,
                "title": extracted.get("title") or "Official Web Page",
                "text": extracted.get("text", ""),
                "sha256": sha256_hash,
                "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
                "status_code": resp.status_code,
            }

        except requests.exceptions.Timeout as te:
            raise TimeoutError(f"Connection timed out while fetching {url}: {te}") from te
        except requests.exceptions.RequestException as re:
            raise RuntimeError(f"Network error accessing official source {url}: {re}") from re


# Global singleton retriever instance
web_retriever = ControlledWebRetriever()
