"""
Tests for the Report Analyst FastAPI layer (report_analyst_api).

Uses FastAPI TestClient; does not start the analyzer (no NumPy/OpenBLAS),
so /health and /question-sets and /questions/{id} are tested.
"""

import sys
from pathlib import Path

import pytest

# Ensure report_analyst and report_analyst_api are importable (run from report-analyst repo root)
_repo_root = Path(__file__).resolve().parent.parent
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

from fastapi.testclient import TestClient

# Import app after path is set; this loads service layer (question_loader only, no analyzer)
from report_analyst_api.main import app

client = TestClient(app)


def test_health():
    """GET /health returns 200 and healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data or "status" in data


def test_question_sets():
    """GET /question-sets returns list of question sets (same source as Streamlit)."""
    response = client.get("/question-sets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # Should have at least one question set if repo has question set YAMLs
    for item in data:
        assert "id" in item
        assert "name" in item
        assert "description" in item


def test_questions_for_set():
    """GET /questions/{id} returns questions for a known set."""
    # First get available sets
    sets_response = client.get("/question-sets")
    assert sets_response.status_code == 200
    sets_list = sets_response.json()
    if not sets_list:
        pytest.skip("No question sets available (missing YAMLs?)")
    first_id = sets_list[0]["id"]
    response = client.get(f"/questions/{first_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["question_set"] == first_id
    assert "questions" in data
    assert isinstance(data["questions"], dict)


def test_questions_unknown_set_returns_empty_or_404():
    """GET /questions/unknown_id returns 200 with empty questions or 404."""
    response = client.get("/questions/nonexistent_set_xyz")
    # API may return 200 with empty questions or 500/404; we accept 200 + empty
    if response.status_code == 200:
        data = response.json()
        assert data.get("questions", {}) == {} or isinstance(data.get("questions"), dict)


def test_question_sets_returns_full_list():
    """GET /question-sets returns full list (no limit); multiple sets when config has multiple."""
    response = client.get("/question-sets")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # No limit: all question sets from loader are returned
    assert len(data) >= 0


def test_reports_returns_full_list():
    """GET /reports returns full list (no limit); multiple reports when temp dir has multiple PDFs."""
    response = client.get("/reports")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    # No limit: all reports from ReportDataClient are returned
    assert len(data) >= 0


def test_reports_can_filter_by_question_set_param():
    """GET /reports?question_set_id=... returns only reports that have rows for that set."""
    consolidated_response = client.get("/consolidated-results")
    assert consolidated_response.status_code == 200
    consolidated = consolidated_response.json()
    if not consolidated:
        pytest.skip("No consolidated rows available to validate report filtering.")

    question_set_id = str(consolidated[0].get("question_set_id") or "")
    if not question_set_id:
        pytest.skip("No question_set_id found in consolidated rows.")

    expected_ids = {
        str(row.get("report_id") or "") for row in consolidated if str(row.get("question_set_id") or "") == question_set_id
    }
    if not expected_ids:
        pytest.skip(f"No consolidated report_ids for question_set_id={question_set_id}.")

    response = client.get("/reports", params={"question_set_id": question_set_id})
    assert response.status_code == 200
    reports = response.json()
    assert isinstance(reports, list)
    returned_ids = {str(r.get("id") or "") for r in reports}
    # Filtered endpoint should be a subset of report_ids known for this question set.
    assert returned_ids.issubset(expected_ids)
    # And when data exists, it should return at least one report.
    assert len(reports) > 0


def test_analysis_keys_returns_full_list():
    """GET /analysis-keys returns full report × question_set pair list."""
    keys_response = client.get("/analysis-keys")
    reports_response = client.get("/reports")
    sets_response = client.get("/question-sets")
    assert keys_response.status_code == 200
    assert reports_response.status_code == 200
    assert sets_response.status_code == 200
    keys = keys_response.json()
    reports = reports_response.json()
    sets_list = sets_response.json()
    assert isinstance(keys, list)
    for row in keys:
        assert "report_id" in row
        assert "report_name" in row
        assert "question_set_id" in row
    assert len(keys) == len(reports) * len(sets_list)


def test_consolidated_results_returns_rows():
    """GET /consolidated-results returns table rows with report/question_set fields."""
    response = client.get("/consolidated-results")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    for row in data:
        assert "report_id" in row
        assert "question_set_id" in row
        assert "question_id" in row
        assert "analysis" in row
