"""Unit tests for document text extractors, HTML parsing, and SHA-256 computation."""

import pytest
from pathlib import Path
from src.ingestion.extractors import (
    compute_sha256,
    compute_bytes_sha256,
    extract_markdown_or_txt,
    extract_html_content,
    extract_pdf_pages,
)


def test_compute_sha256(tmp_path):
    """Verify SHA-256 hash matches known hash for test content."""
    test_file = tmp_path / "sample.txt"
    test_file.write_text("IRDAI Health Regulations 2024", encoding="utf-8")
    h = compute_sha256(test_file)
    assert isinstance(h, str)
    assert len(h) == 64
    # Recomputing should produce identical hash
    assert compute_sha256(test_file) == h


def test_compute_bytes_sha256():
    """Verify byte hash computation."""
    data = b"Bima Bharosa Grievance System"
    h1 = compute_bytes_sha256(data)
    h2 = compute_bytes_sha256(data)
    assert h1 == h2
    assert len(h1) == 64


def test_extract_markdown_or_txt(tmp_path):
    """Verify markdown content reading with encoding tolerance."""
    md_file = tmp_path / "sample.md"
    content = "# Health Insurance\n\n- Cashless\n- Reimbursement"
    md_file.write_text(content, encoding="utf-8")
    extracted = extract_markdown_or_txt(md_file)
    assert extracted == content


def test_extract_html_content():
    """Verify HTML parsing strips scripts and extracts text cleanly."""
    html_sample = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>IRDAI Cashless Norms</title>
            <script>console.log("malicious code");</script>
            <style>body { color: red; }</style>
        </head>
        <body>
            <h1>Cashless Guidelines</h1>
            <p>Authorization must be granted within 1 hour.</p>
        </body>
    </html>
    """
    res = extract_html_content(html_sample)
    assert res["title"] == "IRDAI Cashless Norms"
    assert "malicious code" not in res["text"]
    assert "Cashless Guidelines" in res["text"]
    assert "Authorization must be granted within 1 hour." in res["text"]


def test_extract_pdf_non_existent():
    """Verify FileNotFoundError is raised for non-existent PDF."""
    with pytest.raises(FileNotFoundError):
        extract_pdf_pages("non_existent_file_xyz.pdf")
