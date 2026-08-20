"""Tests for All Results file listing and chunk resolution."""

import pandas as pd
import pytest

from report_analyst.core.cache_manager import CacheManager
from report_analyst.streamlit_app import (
    build_all_results_file_configs,
    selected_question_ids_from_editor,
)


def test_build_all_results_file_configs_includes_chunk_only_reports(tmp_path):
    cache = CacheManager(db_path=str(tmp_path / "cache.db"))
    befesa = str(tmp_path / "Befesa_Annual_Report_2025.pdf")
    sustainability = str(tmp_path / "sustainability_report2024.pdf")

    cache.save_text_only_chunks(
        file_path=befesa,
        chunks=[{"text": "Chunk A", "metadata": {}}],
        chunk_size=500,
        chunk_overlap=20,
    )
    cache.save_analysis(
        file_path=sustainability,
        question_id="tcfd_1",
        result={"ANSWER": "Yes", "SCORE": 1.0},
        config={
            "chunk_size": 500,
            "chunk_overlap": 20,
            "top_k": 5,
            "model": "gpt-4o-mini",
            "question_set": "tcfd",
        },
    )

    configs = build_all_results_file_configs(
        cache,
        "tcfd",
        default_top_k=5,
        default_model="gpt-4o-mini",
    )

    assert befesa in configs
    assert configs[befesa][0]["chunks_only"] is True
    assert sustainability in configs
    assert not configs[sustainability][0].get("chunks_only")


def test_resolve_document_chunks_matches_by_filename(tmp_path):
    cache = CacheManager(db_path=str(tmp_path / "cache.db"))
    stored_path = str(tmp_path / "storage" / "uploads" / "Befesa_Annual_Report_2025.pdf")
    lookup_path = str(tmp_path / "temp" / "Befesa_Annual_Report_2025.pdf")

    cache.save_text_only_chunks(
        file_path=stored_path,
        chunks=[{"text": "Same report, different path.", "metadata": {}}],
        chunk_size=500,
        chunk_overlap=20,
    )

    chunks = cache.resolve_document_chunks(lookup_path, chunk_size=500, chunk_overlap=20)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "Same report, different path."


def test_build_all_results_skips_malformed_and_dedupes(tmp_path):
    cache = CacheManager(db_path=str(tmp_path / "cache.db"))
    path = str(tmp_path / "report.pdf")
    cache.save_text_only_chunks(
        file_path=path,
        chunks=[{"text": "Chunk A", "metadata": {}}],
        chunk_size=500,
        chunk_overlap=20,
    )
    cache.save_analysis(
        file_path=path,
        question_id="tcfd_1",
        result={"ANSWER": "Yes", "SCORE": 1.0},
        config={
            "chunk_size": 500,
            "chunk_overlap": 20,
            "top_k": 5,
            "model": "gpt-4o-mini",
            "question_set": "tcfd",
        },
    )

    original = cache.check_cache_status

    def fake_status():
        rows = list(original())
        rows.append(("bad",))
        return rows

    cache.check_cache_status = fake_status
    configs = build_all_results_file_configs(cache, "tcfd", default_top_k=5, default_model="gpt-4o-mini")
    assert path in configs
    assert len(configs[path]) == 1
    assert not configs[path][0].get("chunks_only")


def test_resolve_document_chunks_skips_mismatched_size_and_name(tmp_path):
    cache = CacheManager(db_path=str(tmp_path / "cache.db"))
    stored = str(tmp_path / "storage" / "report.pdf")
    other = str(tmp_path / "storage" / "other.pdf")
    lookup = str(tmp_path / "temp" / "report.pdf")
    cache.save_text_only_chunks(
        file_path=stored,
        chunks=[{"text": "ok", "metadata": {}}],
        chunk_size=500,
        chunk_overlap=20,
    )
    cache.save_text_only_chunks(
        file_path=other,
        chunks=[{"text": "nope", "metadata": {}}],
        chunk_size=500,
        chunk_overlap=20,
    )
    assert cache.resolve_document_chunks(lookup, chunk_size=999, chunk_overlap=20) == []
    assert cache.resolve_document_chunks(str(tmp_path / "temp" / "missing.pdf"), chunk_size=500, chunk_overlap=20) == []
    assert len(cache.resolve_document_chunks(lookup, chunk_size=500, chunk_overlap=20)) == 1


def test_list_document_chunk_configs_returns_empty_on_error(tmp_path, monkeypatch):
    cache = CacheManager(db_path=str(tmp_path / "cache.db"))

    class Boom:
        def __enter__(self):
            raise RuntimeError("db down")

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(cache.db_manager, "get_connection", lambda: Boom())
    assert cache.list_document_chunk_configs() == []


def test_save_text_only_chunks_raises_on_error(tmp_path, monkeypatch):
    cache = CacheManager(db_path=str(tmp_path / "cache.db"))

    class Boom:
        def __enter__(self):
            raise RuntimeError("db down")

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(cache.db_manager, "get_connection", lambda: Boom())
    with pytest.raises(RuntimeError, match="db down"):
        cache.save_text_only_chunks(
            file_path=str(tmp_path / "report.pdf"),
            chunks=[{"text": "x", "metadata": {}}],
            chunk_size=500,
            chunk_overlap=20,
        )


def test_selected_question_ids_from_editor_helpers():
    assert selected_question_ids_from_editor(pd.DataFrame()) == []
    assert selected_question_ids_from_editor(pd.DataFrame({"QID": ["a"]})) == []
    df = pd.DataFrame({"Select": [True, False, False], "QID": ["a", "b", "c"]})
    assert selected_question_ids_from_editor(df) == ["a"]


def test_resolve_document_chunks_direct_hit(tmp_path):
    cache = CacheManager(db_path=str(tmp_path / "cache.db"))
    path = str(tmp_path / "report.pdf")
    cache.save_text_only_chunks(
        file_path=path,
        chunks=[{"text": "direct", "metadata": {}}],
        chunk_size=500,
        chunk_overlap=20,
    )
    chunks = cache.resolve_document_chunks(path, chunk_size=500, chunk_overlap=20)
    assert len(chunks) == 1
    assert chunks[0]["text"] == "direct"


def test_resolve_document_chunks_skips_overlap_mismatch(tmp_path):
    cache = CacheManager(db_path=str(tmp_path / "cache.db"))
    stored = str(tmp_path / "storage" / "report.pdf")
    lookup = str(tmp_path / "temp" / "report.pdf")
    cache.save_text_only_chunks(
        file_path=stored,
        chunks=[{"text": "ok", "metadata": {}}],
        chunk_size=500,
        chunk_overlap=20,
    )
    assert cache.resolve_document_chunks(lookup, chunk_size=500, chunk_overlap=99) == []


def test_save_text_only_chunks_postgres_path(tmp_path, monkeypatch):
    cache = CacheManager(db_path=str(tmp_path / "cache.db"))
    monkeypatch.setattr(cache.db_manager, "is_postgres", lambda: True)
    executed = []

    class FakeConn:
        def execute(self, statement, params=None):
            executed.append((str(statement), params))

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(cache.db_manager, "get_connection", lambda: FakeConn())
    cache.save_text_only_chunks(
        file_path=str(tmp_path / "report.pdf"),
        chunks=[{"text": "pg", "metadata": {"page": 1}}],
        chunk_size=500,
        chunk_overlap=20,
    )
    assert executed
    assert "ON CONFLICT" in executed[0][0]


def test_display_consolidated_results_single_config(monkeypatch):
    from report_analyst import streamlit_app as app

    analyzer = type("A", (), {})()
    analyzer.analyzer = type("Inner", (), {})()
    analyzer.analyzer.cache_manager = object()
    called = {}

    def fake_render(a, qs, fp, config, display_analysis_results=None):
        called["args"] = (qs, fp, config)

    monkeypatch.setattr(app, "render_consolidated_report_view", fake_render)
    monkeypatch.setattr(app.st, "session_state", {"top_k": 5, "llm_model": "gpt-4o-mini"})
    app.display_consolidated_results(
        analyzer,
        "tcfd",
        file_path="report.pdf",
        selected_config={"config": {"chunk_size": 500, "chunk_overlap": 20}},
    )
    assert called["args"][0] == "tcfd"
    assert called["args"][1] == "report.pdf"


def test_display_consolidated_results_empty_configs(monkeypatch):
    from report_analyst import streamlit_app as app

    warnings = []
    analyzer = type("A", (), {})()
    analyzer.analyzer = type("Inner", (), {})()
    analyzer.analyzer.cache_manager = object()
    monkeypatch.setattr(app, "build_all_results_file_configs", lambda *a, **k: {})
    monkeypatch.setattr(app.st, "session_state", {"top_k": 5, "llm_model": "gpt-4o-mini"})
    monkeypatch.setattr(app.st, "warning", lambda m: warnings.append(m))
    app.display_consolidated_results(analyzer, "tcfd")
    assert warnings


def test_is_partial_processing_step_reads_session(monkeypatch):
    from report_analyst import streamlit_app as app

    monkeypatch.setattr(app.st, "session_state", {"processing_steps_slider": "Chunk"})
    assert app.is_partial_processing_step() is True
