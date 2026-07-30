"""Unit tests for BYOK contribution publish (analysis.result NATS events)."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from report_analyst_jobs.contribution import publish_analysis_result


@pytest.mark.asyncio
async def test_publish_analysis_result_uses_analysis_result_subject_and_payload(monkeypatch):
    mock_nc = MagicMock()
    mock_js = AsyncMock()
    mock_nc.jetstream.return_value = mock_js
    mock_nc.close = AsyncMock()

    async def fake_connect(url, **kwargs):
        return mock_nc

    monkeypatch.setenv("NATS_URL", "nats://localhost:4222")
    monkeypatch.setenv("NATS_USER", "report-analyst-test")
    monkeypatch.setattr("report_analyst_jobs.contribution.nats.connect", fake_connect)

    request_id = await publish_analysis_result(
        resource_id="res-123",
        results={"answers": ["answer one"], "questions": ["question one"]},
        provenance={"mode": "byok_contribution", "provider": "report_analyst"},
        owner_user_id="user-42",
        duration_ms=1500,
    )

    mock_js.publish.assert_awaited_once()
    subject, payload_bytes = mock_js.publish.call_args[0]
    assert subject == f"analysis.result.{request_id}"
    payload = json.loads(payload_bytes.decode())
    assert payload["request_id"] == request_id
    assert payload["resource_id"] == "res-123"
    assert payload["results"] == {"answers": ["answer one"], "questions": ["question one"]}
    assert payload["results_summary"] == payload["results"]
    assert payload["provenance"]["mode"] == "byok_contribution"
    assert payload["owner_user_id"] == "user-42"
    assert payload["duration_ms"] == 1500
    assert payload["source"] == "report-analyst-test"
    mock_nc.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_publish_analysis_result_falls_back_to_core_publish(monkeypatch):
    mock_nc = MagicMock()
    mock_js = AsyncMock()
    mock_js.publish.side_effect = RuntimeError("jetstream unavailable")
    mock_nc.jetstream.return_value = mock_js
    mock_nc.close = AsyncMock()
    mock_nc.publish = AsyncMock()

    async def fake_connect(url, **kwargs):
        return mock_nc

    monkeypatch.setenv("NATS_URL", "nats://localhost:4222")
    monkeypatch.setattr("report_analyst_jobs.contribution.nats.connect", fake_connect)

    request_id = await publish_analysis_result(
        resource_id="res-456",
        results={"answers": ["a"], "questions": ["q"]},
    )

    mock_nc.publish.assert_awaited_once()
    subject, payload_bytes = mock_nc.publish.call_args[0]
    assert subject == f"analysis.result.{request_id}"
    payload = json.loads(payload_bytes.decode())
    assert payload["resource_id"] == "res-456"
