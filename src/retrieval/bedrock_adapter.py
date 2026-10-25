"""Amazon Bedrock Knowledge Bases adapter implementing BaseRetrievalEngine for AWS migration."""

from __future__ import annotations

import logging
from typing import List, Optional, Dict, Any
from src.config import settings
from src.models import ChunkMetadata, RetrievedChunk
from src.retrieval.base import BaseRetrievalEngine

logger = logging.getLogger(__name__)


class BedrockKnowledgeBaseEngine(BaseRetrievalEngine):
    """Adapter for Amazon Bedrock Knowledge Bases retrieval API.

    Allows cloud deployment to replace local ChromaDB while preserving identical interfaces.
    """

    def __init__(
        self,
        knowledge_base_id: Optional[str] = None,
        region_name: Optional[str] = None,
        model_arn: Optional[str] = None,
    ):
        self.kb_id = knowledge_base_id or settings.aws_bedrock_kb_id
        self.region = region_name or settings.aws_region
        self.model_arn = model_arn or settings.aws_bedrock_model_id

        if not self.kb_id:
            logger.info("BedrockKnowledgeBaseEngine initialized without AWS_BEDROCK_KB_ID (placeholder mode).")

        self._client = None
        if self.kb_id and settings.aws_access_key_id:
            try:
                import boto3
                self._client = boto3.client(
                    "bedrock-agent-runtime",
                    region_name=self.region,
                    aws_access_key_id=settings.aws_access_key_id,
                    aws_secret_access_key=settings.aws_secret_access_key,
                )
            except Exception as e:
                logger.warning("Boto3 Bedrock client initialization failed: %s", e)

    def query(
        self,
        query_text: str,
        top_k: int = 4,
        filters: Optional[Dict[str, Any]] = None,
        min_relevance_score: Optional[float] = None,
    ) -> List[RetrievedChunk]:
        """Query Amazon Bedrock Knowledge Base using Bedrock Agent Runtime retrieve API."""
        if not self._client or not self.kb_id:
            raise RuntimeError(
                "Amazon Bedrock Knowledge Base is not configured with active AWS credentials. "
                "For local execution, use the default local ChromaDB retrieval engine."
            )

        # Build Bedrock retrieval configuration
        retrieval_query = {"text": query_text}
        retrieval_config: Dict[str, Any] = {
            "vectorSearchConfiguration": {
                "numberOfResults": top_k,
            }
        }

        # Apply metadata filter in Bedrock format if provided
        if filters:
            bedrock_filters = []
            for k, v in filters.items():
                if k not in ("include_superseded",):
                    bedrock_filters.append({
                        "equals": {
                            "key": k,
                            "value": str(v),
                        }
                    })
            if len(bedrock_filters) == 1:
                retrieval_config["vectorSearchConfiguration"]["filter"] = bedrock_filters[0]
            elif len(bedrock_filters) > 1:
                retrieval_config["vectorSearchConfiguration"]["filter"] = {"andAll": bedrock_filters}

        response = self._client.retrieve(
            knowledgeBaseId=self.kb_id,
            retrievalQuery=retrieval_query,
            retrievalConfiguration=retrieval_config,
        )

        results: List[RetrievedChunk] = []
        raw_results = response.get("retrievalResults", [])
        threshold = min_relevance_score or settings.min_relevance_score

        for idx, item in enumerate(raw_results):
            score = item.get("score", 1.0)
            if score < threshold:
                continue

            content = item.get("content", {}).get("text", "")
            location = item.get("location", {})
            s3_uri = location.get("s3Location", {}).get("uri", "")
            metadata_dict = item.get("metadata", {})

            # Map Bedrock metadata to ChunkMetadata
            chunk_meta = ChunkMetadata(
                source_id=metadata_dict.get("source_id", f"bedrock-{idx}"),
                publisher=metadata_dict.get("publisher", "IRDAI/Insurer"),
                document_type=metadata_dict.get("document_type", "regulatory"),
                document_title=metadata_dict.get("document_title", s3_uri),
                source_url=s3_uri or metadata_dict.get("source_url", ""),
                sha256=metadata_dict.get("sha256", "cloud-managed"),
                content_type=metadata_dict.get("content_type", "regulatory"),
            )

            results.append(
                RetrievedChunk(
                    chunk_id=f"bedrock-{idx}",
                    text=content,
                    metadata=chunk_meta,
                    score=float(score),
                )
            )

        return results

    def index_documents(self, chunks: List[Dict[str, Any]]) -> int:
        """Bedrock Knowledge Bases ingest via S3 sync or data source sync jobs."""
        raise NotImplementedError(
            "Bedrock indexing is executed in AWS via S3 sync jobs. "
            "Upload files to S3 bucket and trigger Bedrock start_ingestion_job."
        )

    def get_stats(self) -> Dict[str, Any]:
        return {
            "engine": "Amazon Bedrock Knowledge Bases",
            "knowledge_base_id": self.kb_id or "[NOT CONFIGURED]",
            "region": self.region,
            "status": "ready" if self._client else "placeholder_mode",
        }
