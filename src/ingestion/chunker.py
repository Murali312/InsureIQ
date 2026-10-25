"""Document chunker preserving section headings, page numbers, and structural context."""

from __future__ import annotations

import re
from typing import List, Dict, Any, Optional


def split_text_into_chunks(
    text: str,
    target_chunk_size: int = 700,
    overlap_size: int = 100,
    section_prefix: Optional[str] = None,
    page_number: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Split text into semantic chunks respecting paragraphs and headings where possible.

    Returns a list of dicts with:
    - 'text': chunk string
    - 'section_path': current heading path
    - 'page_number': page number (if provided)
    """
    if not text or not text.strip():
        return []

    lines = text.splitlines()
    chunks: List[Dict[str, Any]] = []

    current_section = section_prefix or ""
    current_buffer: List[str] = []
    current_char_count = 0

    heading_pattern = re.compile(r"^(#{1,6}\s+.+|\d+\.\s+[A-Z].+|[A-Z\s]{4,}:)")

    def flush_buffer():
        nonlocal current_buffer, current_char_count
        if current_buffer:
            combined_text = "\n".join(current_buffer).strip()
            if combined_text:
                chunks.append({
                    "text": combined_text,
                    "section_path": current_section or "General",
                    "page_number": page_number,
                })
            # Overlap: keep the last 1-2 lines if they fit in overlap_size
            overlap_lines: List[str] = []
            overlap_chars = 0
            for l in reversed(current_buffer):
                if overlap_chars + len(l) <= overlap_size:
                    overlap_lines.insert(0, l)
                    overlap_chars += len(l)
                else:
                    break
            current_buffer = overlap_lines
            current_char_count = overlap_chars

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_char_count >= target_chunk_size:
                flush_buffer()
            else:
                current_buffer.append("")
            continue

        # Check for heading
        if heading_pattern.match(stripped):
            # If buffer has enough content, flush before entering new heading
            if current_char_count > 200:
                flush_buffer()
            clean_heading = re.sub(r"^#+\s*", "", stripped).strip()
            current_section = f"{section_prefix} > {clean_heading}" if section_prefix else clean_heading

        current_buffer.append(stripped)
        current_char_count += len(stripped)

        if current_char_count >= target_chunk_size:
            flush_buffer()

    if current_buffer:
        flush_buffer()

    return chunks


def chunk_markdown_document(
    markdown_text: str,
    target_chunk_size: int = 700,
    overlap_size: int = 100,
) -> List[Dict[str, Any]]:
    """Chunk a markdown document, extracting top-level and section headings."""
    return split_text_into_chunks(
        text=markdown_text,
        target_chunk_size=target_chunk_size,
        overlap_size=overlap_size,
        page_number=None,
    )


def chunk_pdf_pages(
    pages: List[tuple[int, str]],
    target_chunk_size: int = 700,
    overlap_size: int = 100,
) -> List[Dict[str, Any]]:
    """Chunk multiple extracted PDF pages preserving page numbers."""
    all_chunks: List[Dict[str, Any]] = []
    for page_num, page_text in pages:
        page_chunks = split_text_into_chunks(
            text=page_text,
            target_chunk_size=target_chunk_size,
            overlap_size=overlap_size,
            section_prefix=f"Page {page_num}",
            page_number=page_num,
        )
        all_chunks.extend(page_chunks)
    return all_chunks
