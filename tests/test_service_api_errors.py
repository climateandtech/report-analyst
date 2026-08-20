"""Error-path coverage for shared service API helpers."""

from unittest.mock import MagicMock, patch

from report_analyst.core import service as service_mod


def test_get_reports_for_api_returns_empty_on_failure():
    with patch(
        "report_analyst.core.report_data_client.ReportDataClient",
        side_effect=RuntimeError("boom"),
    ):
        assert service_mod.get_reports_for_api() == []


def test_get_analysis_keys_for_api_returns_empty_on_failure():
    with patch.object(service_mod, "get_reports_for_api", side_effect=RuntimeError("boom")):
        assert service_mod.get_analysis_keys_for_api() == []


def test_get_consolidated_results_handles_bad_json_and_db_failure():
    cache = MagicMock()
    conn = MagicMock()
    conn.__enter__ = MagicMock(return_value=conn)
    conn.__exit__ = MagicMock(return_value=False)
    conn.execute.return_value.fetchall.return_value = [
        ("/tmp/r.pdf", "tcfd", "q1", "{not-json"),
    ]
    cache.db_manager.get_connection.return_value = conn

    with patch("report_analyst.core.cache_manager.CacheManager", return_value=cache):
        rows = service_mod.get_consolidated_results_for_api()
    assert len(rows) == 1
    assert rows[0]["analysis"] == ""
    assert rows[0]["question_id"] == "q1"

    with patch(
        "report_analyst.core.cache_manager.CacheManager",
        side_effect=RuntimeError("db down"),
    ):
        assert service_mod.get_consolidated_results_for_api() == []
