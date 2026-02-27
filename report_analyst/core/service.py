"""
Shared service layer used by both the Streamlit app and the Report Analyst API.

Wraps the same question_loader and DocumentAnalyzer so the API is a thin HTTP
wrapper over the same code path as the Streamlit app. The analyzer is created
lazy (on first use) and OPENBLAS_NUM_THREADS is set before importing NumPy
to avoid SIGSEGV on macOS/ARM.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from sqlalchemy import text

from report_analyst.core.question_loader import get_question_loader

logger = logging.getLogger(__name__)

_analyzer = None


def get_question_sets_for_api() -> List[Dict[str, Any]]:
    """Return question sets in API shape: list of {id, name, description}. Same source as Streamlit."""
    loader = get_question_loader()
    question_sets = loader.get_question_sets()
    return [{"id": qset.id, "name": qset.name, "description": qset.description} for qset in question_sets.values()]


def get_questions_for_api(question_set_id: str) -> Dict[str, Any]:
    """Return questions for a set: {question_id: {text, guidelines, ...}}. Same source as Streamlit."""
    loader = get_question_loader()
    return loader.get_questions(question_set_id)


def get_report_temp_dir():
    """Return the directory used for local report PDFs (async uploads and report_path). Same as API _resolve_analyze_path."""
    from pathlib import Path

    path = os.environ.get("REPORT_ANALYST_TEMP")
    if path:
        return Path(os.path.realpath(path))
    # Default: project/temp (relative to report_analyst package parent)
    root = Path(__file__).resolve().parent.parent.parent
    return root / "temp"


def get_reports_for_api(question_set_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return list of reports (local + any configured backends). Same source as Streamlit via ReportDataClient."""
    try:
        from report_analyst.core.report_data_client import ReportDataClient

        temp_dir = get_report_temp_dir()
        client = ReportDataClient(temp_dir=temp_dir)
        # backend_configs=None so we only list local reports; avoids hard dep on report_analyst_search_backend
        resources = client.list_reports(backend_configs=None)
        reports = [
            {
                "id": r.uri,
                "name": r.name,
                "uri": r.uri,
                "date": r.date,
                "size": r.size,
                "metadata": r.metadata or {},
            }
            for r in resources
        ]
        if not question_set_id:
            return reports

        # Keep only reports that actually have cached consolidated rows for this question set.
        consolidated = get_consolidated_results_for_api(question_set_id=question_set_id)
        allowed_ids = {str(row.get("report_id") or "") for row in consolidated}
        if not allowed_ids:
            return []
        return [r for r in reports if str(r.get("id") or "") in allowed_ids]
    except Exception as e:
        logger.warning("get_reports_for_api failed: %s", e)
        return []


def get_analysis_keys_for_api() -> List[Dict[str, Any]]:
    """Return full report × question_set pairs for selectors.

    This endpoint is intentionally not limited to stored cache keys so UI selectors
    can present all available combinations.
    """
    try:
        reports = get_reports_for_api()
        question_sets = get_question_sets_for_api()

        def normalize_report_id(report: Dict[str, Any]) -> str:
            # Use the same id format as /reports so selectors and results filters align.
            rid = str(report.get("id") or report.get("uri") or "")
            return rid

        out: List[Dict[str, Any]] = []
        for report in reports:
            report_id = normalize_report_id(report)
            report_name = str(report.get("name") or report_id)
            for qset in question_sets:
                qset_id = str(qset.get("id") or "")
                if not report_id or not qset_id:
                    continue
                out.append(
                    {
                        "report_id": report_id,
                        "report_name": report_name,
                        "question_set_id": qset_id,
                    }
                )
        return out
    except Exception as e:
        logger.warning("get_analysis_keys_for_api failed: %s", e)
        return []


def get_consolidated_results_for_api(
    question_set_id: Optional[str] = None,
    report_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return all cached analysis rows in UI table shape.

    Each row includes report/question_set so UI can filter by current selectors.
    """
    try:
        from report_analyst.core.cache_manager import CacheManager

        cache = CacheManager()
        with cache.db_manager.get_connection() as conn:
            sql = """
                SELECT file_path, question_set, question_id, result
                FROM analysis_cache
            """
            where: List[str] = []
            params: Dict[str, Any] = {}
            if question_set_id:
                where.append("question_set = :question_set_id")
                params["question_set_id"] = question_set_id
            if report_id:
                # DB stores file_path without file:// prefix.
                normalized = str(report_id)
                if normalized.startswith("file://"):
                    normalized = normalized.replace("file://", "", 1)
                where.append("file_path = :file_path")
                params["file_path"] = normalized
            if where:
                sql += " WHERE " + " AND ".join(where)
            sql += " ORDER BY file_path, question_set, question_id"

            result_obj = conn.execute(text(sql), params)
            rows = result_obj.fetchall()

        out: List[Dict[str, Any]] = []
        for file_path, question_set, question_id, result_json in rows:
            try:
                result = json.loads(result_json) if isinstance(result_json, str) else (result_json or {})
            except Exception:
                result = {}
            answer = str(result.get("ANSWER") or result.get("answer") or result.get("analysis") or "")
            score = result.get("SCORE", result.get("score", result.get("confidence_score", 0)))
            report_id = str(file_path)
            if report_id and not report_id.startswith("file://"):
                report_id = f"file://{report_id}"
            out.append(
                {
                    "report_id": report_id,
                    "question_set_id": str(question_set or ""),
                    "question_id": str(question_id or ""),
                    "analysis": answer,
                    "score": score,
                }
            )
        return out
    except Exception as e:
        logger.warning("get_consolidated_results_for_api failed: %s", e)
        return []


def get_document_analyzer():
    """Return the shared DocumentAnalyzer instance. Lazy-import to avoid loading NumPy/OpenBLAS at process startup."""
    global _analyzer
    if _analyzer is None:
        # Reduce risk of OpenBLAS stack overflow (SIGSEGV) on macOS/ARM before any NumPy use
        if "OPENBLAS_NUM_THREADS" not in os.environ:
            os.environ["OPENBLAS_NUM_THREADS"] = "1"
        from report_analyst.core.analyzer import DocumentAnalyzer

        _analyzer = DocumentAnalyzer()
    return _analyzer
