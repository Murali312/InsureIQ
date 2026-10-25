"""Amazon Bedrock integration placeholders and cloud migration helpers."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from src.config import settings

logger = logging.getLogger(__name__)


class BedrockIntegrationClient:
    """Manages Amazon Bedrock Agent Runtime and Knowledge Base client connections.

    Supports optional AWS cloud migration without blocking local-first execution.
    """

    def __init__(
        self,
        region_name: Optional[str] = None,
        kb_id: Optional[str] = None,
        model_id: Optional[str] = None,
    ):
        self.region = region_name or settings.aws_region
        self.kb_id = kb_id or settings.aws_bedrock_kb_id
        self.model_id = model_id or settings.aws_bedrock_model_id

        self._runtime_client = None
        self._init_client()

    def _init_client(self):
        """Safely attempt to initialize boto3 client without crashing if credentials are absent."""
        if not settings.aws_access_key_id and not settings.aws_bedrock_kb_id:
            logger.info("AWS Bedrock: Running in unconfigured local mode (no credentials provided).")
            return

        try:
            import boto3
            self._runtime_client = boto3.client(
                "bedrock-runtime",
                region_name=self.region,
                aws_access_key_id=settings.aws_access_key_id,
                aws_secret_access_key=settings.aws_secret_access_key,
            )
            logger.info("AWS Bedrock: Successfully initialized bedrock-runtime client.")
        except Exception as e:
            logger.warning("AWS Bedrock: Client initialization skipped: %s", e)
            self._runtime_client = None

    def is_connected(self) -> bool:
        """Return True only if real client was successfully initialized."""
        return self._runtime_client is not None

    def get_connection_status(self) -> Dict[str, Any]:
        """Return clear connection status for UI and diagnostic reporting."""
        return {
            "is_connected": self.is_connected(),
            "region": self.region,
            "knowledge_base_id": self.kb_id or "[NOT CONFIGURED]",
            "model_id": self.model_id,
            "mode": "AWS Managed Cloud" if self.is_connected() else "Local-First Fallback (Offline)",
        }
