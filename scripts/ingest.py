#!/usr/bin/env python3
"""CLI script to ingest health insurance knowledge documents into ChromaDB."""

import argparse
import sys
import logging
from pathlib import Path

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.config import settings
from src.retrieval.embeddings import get_embedding_provider
from src.retrieval.chroma_engine import ChromaRetrievalEngine
from src.ingestion.pipeline import IngestionPipeline
from src.ingestion.registry import SourceRegistry

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("ingest")


def main():
    parser = argparse.ArgumentParser(description="Ingest health insurance documents into ChromaDB.")
    parser.add_argument(
        "--provider",
        choices=["openai", "local", "fallback"],
        default=None,
        help="Embedding provider override (default: from .env)",
    )
    parser.add_argument(
        "--knowledge-dir",
        type=str,
        default=None,
        help="Path to knowledge directory (default: ./knowledge)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Reset existing vector store before indexing to allow switching embedding models.",
    )
    args = parser.parse_args()

    backup_path = None
    if args.reset:
        chroma_path = settings.get_chroma_path()
        if chroma_path.exists() and any(chroma_path.iterdir()):
            import shutil
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = chroma_path.parent / f"backup_chroma_{timestamp}"
            logger.info("Reset requested. Creating backup of existing vector store to: %s", backup_path)
            shutil.copytree(chroma_path, backup_path, dirs_exist_ok=True)
            logger.info("Backup successfully created. Now clearing %s for fresh re-indexing...", chroma_path)
            shutil.rmtree(chroma_path, ignore_errors=True)

    provider_name = args.provider or settings.embedding_provider
    logger.info("Initializing embedding provider: %s", provider_name)

    try:
        embedding_provider = get_embedding_provider(
            provider_override=args.provider,
            allow_fallback=True,
        )
        logger.info(
            "Embedding provider active: %s (model: %s, dim: %d)",
            embedding_provider.provider_name,
            embedding_provider.model_name,
            embedding_provider.dimension,
        )
    except Exception as e:
        logger.error("Failed to initialize embedding provider: %s", e)
        sys.exit(1)

    try:
        engine = ChromaRetrievalEngine(embedding_provider=embedding_provider)
        pipeline = IngestionPipeline(
            knowledge_dir=args.knowledge_dir,
            retrieval_engine=engine,
        )
        report = pipeline.run_ingestion()

        registry = SourceRegistry()
        stats = registry.get_summary_stats()

        print("\n" + "=" * 65)
        print("🎉 INGESTION COMPLETE & KNOWLEDGE BASE READY")
        print("=" * 65)
        print(f"Total Files Processed:  {report['files_processed']}")
        print(f"Successful Documents:   {len(report.get('successful_docs', []))}")
        for sdoc in report.get("successful_docs", []):
            print(f"   ✓ {sdoc}")
        if report.get("skipped_duplicates"):
            print(f"Skipped Duplicates:     {len(report['skipped_duplicates'])}")
        if report.get("failed_sources"):
            print(f"Failed Sources:         {len(report['failed_sources'])}")
            for fsrc in report["failed_sources"]:
                print(f"   ✗ {fsrc.get('file')}: {fsrc.get('error')}")
        print(f"Chunks Extracted:       {report['chunks_extracted']}")
        print(f"Chunks Indexed:         {report['chunks_indexed']}")
        print(f"Chroma Directory:       {settings.get_chroma_path()}")
        if backup_path:
            print(f"Prior Backup Saved At:  {backup_path}")
        print("-" * 65)
        print(f"Source Registry Summary: {stats['total']} total tracked sources")
        print(f"  - Official / Verified: {stats['official']}")
        print(f"  - Pending Verification: {stats['pending_verification']}")
        print(f"  - Superseded:          {stats['superseded']}")
        print("=" * 65 + "\n")

    except Exception as e:
        logger.error("Ingestion failed: %s", e, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
