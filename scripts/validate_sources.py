#!/usr/bin/env python3
"""CLI tool to audit and validate official source registry records."""

import sys
import logging
from pathlib import Path

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.registry import SourceRegistry
from src.security import validate_url_for_ssrf

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("validate_sources")


def main():
    registry = SourceRegistry()
    sources = registry.load_sources()

    print("\n" + "=" * 70)
    print("📋 INDIA HEALTH INSURANCE SOURCE REGISTRY AUDIT")
    print("=" * 70)

    official_count = 0
    pending_count = 0
    url_issues = 0

    for s in sources:
        is_safe, err = validate_url_for_ssrf(s.source_url)
        url_status = "✅ ALLOWED" if is_safe else f"⚠️ REJECTED ({err})"
        if not is_safe:
            url_issues += 1

        print(f"\nID:       {s.source_id}")
        print(f"Title:    {s.title}")
        print(f"Type:     {s.document_type}")
        print(f"Status:   {s.source_status.upper()}")
        print(f"URL:      {s.source_url} [{url_status}]")
        print(f"SHA-256:  {s.sha256 or '[Pending ingestion]'}")

        if s.source_status == "official":
            official_count += 1
        elif s.source_status == "pending_verification":
            pending_count += 1

    print("\n" + "=" * 70)
    print(f"SUMMARY: Total: {len(sources)} | Official: {official_count} | Pending: {pending_count} | URL Issues: {url_issues}")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
