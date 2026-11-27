"""Enhanced flow must not publish stub local analysis to the platform."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from report_analyst_search_backend.config import BackendConfig
from report_analyst_search_backend.flow_orchestrator import FlowOrchestrator


@pytest.fixture
def enhanced_config() -> BackendConfig:
    return BackendConfig(
        use_backend=True,
        use_centralized_llm=True,
        use_data_lake=True,
        nats_url="nats://platform-nats:4222",
        owner="sidebar-owner",
    )


def test_enhanced_stub_analysis_does_not_publish(enhanced_config):
    orch = FlowOrchestrator(enhanced_config)
    chunks = [{"resource_id": "res-99", "chunk_text": "climate risk section"}]

    with patch("report_analyst_search_backend.flow_orchestrator.st") as mock_st:
        mock_st.info = MagicMock()
        mock_st.warning = MagicMock()
        with patch(
            "report_analyst_enterprise.contribution.publish_analysis_result",
            new_callable=AsyncMock,
        ) as publish:
            result = orch._analyze_enhanced(chunks, ["What are climate risks?"])

    assert result.success
    assert result.stored_in_backend is False
    publish.assert_not_called()
    mock_st.warning.assert_called_once()


def test_enhanced_sets_stored_in_backend_only_after_successful_publish(enhanced_config):
    orch = FlowOrchestrator(enhanced_config)
    chunks = [{"resource_id": "res-42", "chunk_text": "report body"}]
    publishable_results = {
        "questions": ["Q1"],
        "answers": ["Real grounded answer from DocumentAnalyzer."],
        "method": "document_analyzer",
        "publishable": True,
    }

    with patch.object(orch, "_analyze_local") as mock_local:
        from report_analyst_search_backend.flow_orchestrator import AnalysisResult

        mock_local.return_value = AnalysisResult(success=True, results=publishable_results)
        with patch("report_analyst_search_backend.flow_orchestrator.st"):
            with patch(
                "report_analyst_enterprise.contribution.publish_analysis_result",
                new_callable=AsyncMock,
                return_value="evt-1",
            ) as publish:
                result = orch._analyze_enhanced(chunks, ["Q1"])

    publish.assert_awaited_once()
    call_kwargs = publish.call_args.kwargs
    assert call_kwargs["owner_user_id"] == "sidebar-owner"
    assert call_kwargs["nats_url"] == "nats://platform-nats:4222"
    assert result.stored_in_backend is True


def test_enhanced_no_resource_id_does_not_mark_stored(enhanced_config):
    orch = FlowOrchestrator(enhanced_config)
    publishable_results = {
        "questions": ["Q1"],
        "answers": ["Answer"],
        "method": "document_analyzer",
        "publishable": True,
    }

    with patch.object(orch, "_analyze_local") as mock_local:
        from report_analyst_search_backend.flow_orchestrator import AnalysisResult

        mock_local.return_value = AnalysisResult(success=True, results=publishable_results)
        with patch("report_analyst_search_backend.flow_orchestrator.st"):
            with patch(
                "report_analyst_enterprise.contribution.publish_analysis_result",
                new_callable=AsyncMock,
            ) as publish:
                result = orch._analyze_enhanced([{"chunk_text": "no resource id"}], ["Q1"])

    publish.assert_not_called()
    assert result.stored_in_backend is False
