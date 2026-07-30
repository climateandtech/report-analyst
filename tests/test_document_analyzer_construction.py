"""Regression tests for DocumentAnalyzer construction API."""

from pathlib import Path


def test_streamlit_app_does_not_pass_cache_manager_to_document_analyzer():
    """DocumentAnalyzer.__init__ takes no kwargs; it builds CacheManager itself.

    Code Quality flagged DocumentAnalyzer(cache_manager=...) on the benchmarking
    page. That call raises TypeError if executed — keep it out of source.
    """
    source = Path("report_analyst/streamlit_app.py").read_text(encoding="utf-8")
    assert "DocumentAnalyzer(cache_manager=" not in source, (
        "Do not pass cache_manager= to DocumentAnalyzer(); use DocumentAnalyzer() "
        "or ReportAnalyzer() and read .cache_manager from the instance."
    )
