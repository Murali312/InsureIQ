"""Ingestion pipeline coordinator for document scanning, chunking, hashing, and indexing."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import settings, BASE_DIR
from src.models import ChunkMetadata, SourceRecord
from src.ingestion.extractors import compute_sha256, extract_markdown_or_txt, extract_pdf_pages
from src.ingestion.chunker import chunk_markdown_document, chunk_pdf_pages
from src.ingestion.registry import SourceRegistry
from src.retrieval.base import BaseRetrievalEngine
from src.retrieval.chroma_engine import ChromaRetrievalEngine

logger = logging.getLogger(__name__)


OFFICIAL_INSURER_DOMAINS = {
    "HDFC_ERGO": "https://www.hdfcergo.com",
    "Star_Health": "https://www.starhealth.in",
    "Care_Health": "https://www.careinsurance.com",
    "Niva_Bupa": "https://www.nivabupa.com",
    "ICICI_Lombard": "https://www.icicilombard.com",
    "Aditya_Birla_Health": "https://www.adityabirlacapital.com/healthinsurance",
}


class IngestionPipeline:
    """Discovers, validates, chunks, hashes, and indexes health insurance knowledge files."""

    def __init__(
        self,
        knowledge_dir: Optional[Path | str] = None,
        retrieval_engine: Optional[BaseRetrievalEngine] = None,
        registry: Optional[SourceRegistry] = None,
    ):
        self.knowledge_dir = Path(knowledge_dir) if knowledge_dir else (BASE_DIR / "knowledge")
        self.registry = registry or SourceRegistry()
        self._retrieval_engine = retrieval_engine

    @property
    def retrieval_engine(self) -> BaseRetrievalEngine:
        if self._retrieval_engine is None:
            self._retrieval_engine = ChromaRetrievalEngine()
        return self._retrieval_engine

    def run_ingestion(self) -> Dict[str, Any]:
        """Execute full ingestion workflow across all knowledge directories.

        Returns summary report.
        """
        logger.info("Starting knowledge base ingestion from %s", self.knowledge_dir)
        all_chunks: List[Dict[str, Any]] = []
        files_processed = 0
        successful_docs: List[str] = []
        skipped_duplicates: List[str] = []
        failed_sources: List[Dict[str, str]] = []

        # 1. Ingest General FAQs & Guides
        general_dir = self.knowledge_dir / "general"
        if general_dir.exists():
            for f in sorted(general_dir.glob("*.md")):
                try:
                    chunks = self._process_file(
                        file_path=f,
                        default_content_type="general_faq",
                        default_doc_type="general_faq",
                        publisher="IRDAI / Educational",
                    )
                    all_chunks.extend(chunks)
                    files_processed += 1
                    successful_docs.append(str(f.relative_to(self.knowledge_dir)))
                except Exception as ex:
                    logger.error("Failed to process general knowledge file %s: %s", f.name, ex)
                    failed_sources.append({"file": f.name, "error": str(ex)})

        # 2. Ingest Regulatory Documents
        reg_dir = self.knowledge_dir / "regulatory"
        if reg_dir.exists():
            for f in sorted(reg_dir.glob("*.md")):
                try:
                    chunks = self._process_file(
                        file_path=f,
                        default_content_type="regulatory",
                        default_doc_type="circular" if "circular" in f.name else "regulatory_guidance",
                        publisher="IRDAI",
                    )
                    all_chunks.extend(chunks)
                    files_processed += 1
                    successful_docs.append(str(f.relative_to(self.knowledge_dir)))
                except Exception as ex:
                    logger.error("Failed to process regulatory file %s: %s", f.name, ex)
                    failed_sources.append({"file": f.name, "error": str(ex)})

        # 3. Ingest Insurer Product Documents (PDFs and Markdown)
        insurers_dir = self.knowledge_dir / "insurers"
        if insurers_dir.exists():
            for insurer_folder in sorted(insurers_dir.iterdir()):
                if insurer_folder.is_dir():
                    for f in sorted(insurer_folder.rglob("*")):
                        if f.is_file() and f.suffix.lower() in (".md", ".txt", ".pdf"):
                            if f.name.lower() == "readme.md":
                                continue  # Skip directory placeholder readmes
                            try:
                                chunks = self._process_insurer_file(f, insurer_folder.name)
                                all_chunks.extend(chunks)
                                files_processed += 1
                                successful_docs.append(str(f.relative_to(self.knowledge_dir)))
                            except Exception as ex:
                                logger.error("Failed to process insurer file %s: %s", f.name, ex)
                                failed_sources.append({"file": f.name, "error": str(ex)})

        # 4. Vector Store Indexing
        indexed_count = 0
        if all_chunks:
            logger.info("Indexing %d chunks into ChromaDB...", len(all_chunks))
            indexed_count = self.retrieval_engine.index_documents(all_chunks)

        logger.info(
            "Ingestion completed: %d files processed (%d successful, %d failed), %d chunks indexed.",
            files_processed,
            len(successful_docs),
            len(failed_sources),
            indexed_count,
        )
        return {
            "files_processed": files_processed,
            "successful_docs": successful_docs,
            "skipped_duplicates": skipped_duplicates,
            "failed_sources": failed_sources,
            "chunks_extracted": len(all_chunks),
            "chunks_indexed": indexed_count,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _process_file(
        self,
        file_path: Path,
        default_content_type: str,
        default_doc_type: str,
        publisher: str,
    ) -> List[Dict[str, Any]]:
        """Process a general or regulatory markdown file."""
        sha256_hash = compute_sha256(file_path)
        text = extract_markdown_or_txt(file_path)
        raw_chunks = chunk_markdown_document(text)

        source_id = file_path.stem.upper().replace("_", "-")
        title = file_path.stem.replace("_", " ").title()

        # Update source registry record with real hash and timestamp
        existing_src = self.registry.get_source_by_id(source_id)
        retrieval_time = datetime.now(timezone.utc).isoformat()
        if existing_src:
            existing_src.sha256 = sha256_hash
            existing_src.retrieved_at_utc = retrieval_time
            self.registry.update_source_record(existing_src)
            source_url = existing_src.source_url
            doc_type = existing_src.document_type
        else:
            source_url = f"https://irdai.gov.in/{file_path.name}"
            doc_type = default_doc_type
            new_src = SourceRecord(
                source_id=source_id,
                publisher=publisher,
                title=title,
                source_url=source_url,
                document_type=doc_type,
                sha256=sha256_hash,
                retrieved_at_utc=retrieval_time,
                source_status="official",
            )
            self.registry.update_source_record(new_src)

        indexed_chunks = []
        for idx, rc in enumerate(raw_chunks):
            meta = ChunkMetadata(
                source_id=source_id,
                publisher=publisher,
                document_type=doc_type,
                document_title=title,
                source_url=source_url,
                sha256=sha256_hash,
                section_path=rc.get("section_path"),
                page_number=rc.get("page_number"),
                status="current",
                content_type=default_content_type,  # type: ignore
                is_official_source=True,
            )
            indexed_chunks.append({
                "id": f"{source_id}-{idx:04d}",
                "text": rc["text"],
                "metadata": meta.to_chroma_metadata(),
            })

        return indexed_chunks

    def _process_insurer_file(self, file_path: Path, insurer_name: str) -> List[Dict[str, Any]]:
        """Process an insurer product file."""
        sha256_hash = compute_sha256(file_path)
        source_id = f"{insurer_name.upper()}-{file_path.stem.upper()}"
        title = f"{insurer_name.replace('_', ' ')} - {file_path.stem.replace('_', ' ').title()}"
        domain = OFFICIAL_INSURER_DOMAINS.get(insurer_name, "https://irdai.gov.in")
        source_url = f"{domain}/{file_path.name}"
        retrieval_time = datetime.now(timezone.utc).isoformat()

        # Update or register in source registry
        existing_src = self.registry.get_source_by_id(source_id)
        if existing_src:
            existing_src.sha256 = sha256_hash
            existing_src.retrieved_at_utc = retrieval_time
            self.registry.update_source_record(existing_src)
        else:
            new_src = SourceRecord(
                source_id=source_id,
                publisher=insurer_name.replace("_", " "),
                title=title,
                source_url=source_url,
                document_type="policy_wording",
                sha256=sha256_hash,
                retrieved_at_utc=retrieval_time,
                source_status="official",
            )
            self.registry.update_source_record(new_src)

        if file_path.suffix.lower() == ".pdf":
            pages = extract_pdf_pages(file_path)
            raw_chunks = chunk_pdf_pages(pages)
        else:
            text = extract_markdown_or_txt(file_path)
            raw_chunks = chunk_markdown_document(text)

        indexed_chunks = []
        for idx, rc in enumerate(raw_chunks):
            meta = ChunkMetadata(
                source_id=source_id,
                publisher=insurer_name.replace("_", " "),
                insurer_id=insurer_name,
                product_name=file_path.stem.replace("_", " "),
                document_type="policy_wording",
                document_title=title,
                source_url=source_url,
                sha256=sha256_hash,
                section_path=rc.get("section_path"),
                page_number=rc.get("page_number"),
                status="current",
                content_type="insurer_product",
                is_official_source=True,
            )
            indexed_chunks.append({
                "id": f"{source_id}-{idx:04d}",
                "text": rc["text"],
                "metadata": meta.to_chroma_metadata(),
            })

        return indexed_chunks
