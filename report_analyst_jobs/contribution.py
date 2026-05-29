"""Publish analysis results to platform (BYOK contribution mode)."""

from __future__ import annotations

import json
import logging
import os
import uuid
from typing import Any, Dict, Optional

import nats

logger = logging.getLogger(__name__)


async def publish_analysis_result(
    resource_id: str,
    results: Dict[str, Any],
    provenance: Optional[Dict[str, Any]] = None,
    analysis_config: Optional[Dict[str, Any]] = None,
    owner_user_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
) -> str:
    """Publish analysis.result.{id} for platform to persist."""
    request_id = str(uuid.uuid4())
    nats_url = os.getenv("NATS_URL", "nats://localhost:4222")
    nats_token = os.getenv("NATS_TOKEN")
    if nats_token and "@" not in nats_url:
        protocol, rest = nats_url.split("://", 1)
        nats_url = f"{protocol}://{nats_token}@{rest}"

    payload = {
        "request_id": request_id,
        "resource_id": resource_id,
        "results": results,
        "results_summary": results,
        "provenance": provenance or {},
        "analysis_config": analysis_config or {},
        "owner_user_id": owner_user_id,
        "duration_ms": duration_ms,
        "source": os.getenv("NATS_USER", "report-analyst"),
    }

    nc = await nats.connect(nats_url, connect_timeout=15)
    try:
        js = nc.jetstream()
        subject = f"analysis.result.{request_id}"
        try:
            await js.publish(subject, json.dumps(payload).encode())
        except Exception:
            await nc.publish(subject, json.dumps(payload).encode())
        logger.info("Published %s for resource %s", subject, resource_id)
        return request_id
    finally:
        await nc.close()
