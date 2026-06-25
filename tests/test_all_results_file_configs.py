"""Tests for All Results file listing and chunk resolution."""

from pathlib import Path

from report_analyst.core.cache_manager import CacheManager
from report_analyst.streamlit_app import build_all_results_file_configs


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
