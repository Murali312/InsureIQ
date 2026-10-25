"""Text extraction utilities for PDF, Markdown, TXT, and HTML files with SHA-256 computation."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
from bs4 import BeautifulSoup
import pypdf


def compute_sha256(file_path: Path | str) -> str:
    """Compute SHA-256 hash of a file on disk."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"File not found for hash calculation: {file_path}")

    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_bytes_sha256(data: bytes) -> str:
    """Compute SHA-256 hash of raw bytes."""
    return hashlib.sha256(data).hexdigest()


def extract_pdf_pages(file_path: Path | str) -> List[Tuple[int, str]]:
    """Extract text from a PDF file page by page using pypdf.

    Returns a list of (page_number_1_indexed, page_text).
    Handles empty pages, encrypted files, and corrupted streams gracefully.
    """
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"PDF file not found: {file_path}")

    extracted_pages: List[Tuple[int, str]] = []
    try:
        reader = pypdf.PdfReader(str(p))
        if reader.is_encrypted:
            try:
                reader.decrypt("")
            except Exception as dec_err:
                raise ValueError(f"Cannot decrypt protected PDF: {dec_err}") from dec_err

        for page_idx, page in enumerate(reader.pages):
            page_num = page_idx + 1
            try:
                text = page.extract_text() or ""
                text = text.strip()
                if text:
                    extracted_pages.append((page_num, text))
            except Exception as page_err:
                # Log page extraction error but continue with other pages
                extracted_pages.append((page_num, f"[Extraction error on page {page_num}: {page_err}]"))

    except Exception as e:
        raise ValueError(f"Failed to parse PDF {p.name}: {e}") from e

    return extracted_pages


def extract_markdown_or_txt(file_path: Path | str) -> str:
    """Read a Markdown or plain text document safely."""
    p = Path(file_path)
    if not p.is_file():
        raise FileNotFoundError(f"Text file not found: {file_path}")

    encodings = ["utf-8", "utf-8-sig", "latin-1", "cp1252"]
    for enc in encodings:
        try:
            with open(p, "r", encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue

    with open(p, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def extract_html_content(html_content: str | bytes) -> Dict[str, Any]:
    """Parse HTML and extract clean text, stripping scripts, styles, and unwanted markup.

    Returns dict with keys: 'title', 'text', 'headings'.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Remove script, style, meta, noscript, header, footer, nav
    for tag in soup(["script", "style", "meta", "noscript", "svg", "nav", "footer"]):
        tag.decompose()

    title = ""
    if soup.title and soup.title.string:
        title = soup.title.string.strip()

    # Collect headings
    headings = [h.get_text(strip=True) for h in soup.find_all(["h1", "h2", "h3", "h4"])]

    # Get body or full text
    body = soup.body or soup
    text = body.get_text(separator="\n", strip=True)

    return {
        "title": title,
        "text": text,
        "headings": headings,
    }
