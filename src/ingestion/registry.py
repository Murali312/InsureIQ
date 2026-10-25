"""Source registry management and verification status tracking."""

from __future__ import annotations

import csv
from pathlib import Path
from typing import List, Optional, Dict
from src.models import SourceRecord
from src.config import BASE_DIR

DEFAULT_REGISTRY_CSV = BASE_DIR / "metadata" / "source_registry.csv"
DEFAULT_INSURER_TEMPLATE_CSV = BASE_DIR / "metadata" / "insurer_product_source_template.csv"


class SourceRegistry:
    """Manages the official source catalogue and verification statuses."""

    def __init__(self, registry_csv_path: Optional[Path | str] = None):
        self.registry_path = Path(registry_csv_path) if registry_csv_path else DEFAULT_REGISTRY_CSV

    def load_sources(self) -> List[SourceRecord]:
        """Load all tracked source records from source_registry.csv."""
        if not self.registry_path.is_file():
            return []

        sources: List[SourceRecord] = []
        with open(self.registry_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Clean whitespace in keys and values
                cleaned_row = {k.strip(): (v.strip() if v else "") for k, v in row.items() if k}
                if not cleaned_row.get("source_id"):
                    continue

                status_raw = cleaned_row.get("source_status", "official").lower()
                if status_raw not in ("official", "pending_verification", "superseded", "under_review"):
                    status_raw = "official"

                sources.append(
                    SourceRecord(
                        source_id=cleaned_row.get("source_id", ""),
                        publisher=cleaned_row.get("publisher", ""),
                        title=cleaned_row.get("title", ""),
                        source_url=cleaned_row.get("source_url", ""),
                        document_type=cleaned_row.get("document_type", "regulatory_faq"),
                        verification_notes=cleaned_row.get("verification_notes") or None,
                        published_or_effective_date=cleaned_row.get("published_or_effective_date") or None,
                        retrieved_at_utc=cleaned_row.get("retrieved_at_utc") or None,
                        source_status=status_raw,  # type: ignore
                        sha256=cleaned_row.get("sha256") or None,
                    )
                )
        return sources

    def get_source_by_id(self, source_id: str) -> Optional[SourceRecord]:
        """Find a source record by its unique source_id."""
        for src in self.load_sources():
            if src.source_id.strip() == source_id.strip():
                return src
        return None

    def get_verified_official_sources(self) -> List[SourceRecord]:
        """Return only sources marked as 'official'."""
        return [s for s in self.load_sources() if s.source_status == "official"]

    def get_pending_sources(self) -> List[SourceRecord]:
        """Return sources marked as 'pending_verification'."""
        return [s for s in self.load_sources() if s.source_status == "pending_verification"]

    def update_source_record(self, updated_record: SourceRecord) -> None:
        """Add or update a source record in the CSV."""
        sources = self.load_sources()
        found = False
        new_list: List[SourceRecord] = []

        for s in sources:
            if s.source_id == updated_record.source_id:
                new_list.append(updated_record)
                found = True
            else:
                new_list.append(s)

        if not found:
            new_list.append(updated_record)

        self.save_sources(new_list)

    def save_sources(self, sources: List[SourceRecord]) -> None:
        """Write source records to the CSV file."""
        self.registry_path.parent.mkdir(parents=True, exist_ok=True)
        fieldnames = [
            "source_id",
            "publisher",
            "title",
            "source_url",
            "document_type",
            "verification_notes",
            "published_or_effective_date",
            "retrieved_at_utc",
            "source_status",
            "sha256",
        ]
        with open(self.registry_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for s in sources:
                writer.writerow(s.model_dump())

    def get_summary_stats(self) -> Dict[str, int]:
        """Return summary count of sources by status."""
        stats = {
            "total": 0,
            "official": 0,
            "pending_verification": 0,
            "superseded": 0,
            "under_review": 0,
        }
        for s in self.load_sources():
            stats["total"] += 1
            st = s.source_status
            if st in stats:
                stats[st] += 1
        return stats
