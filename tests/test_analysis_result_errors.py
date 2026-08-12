"""Tests for failed-analysis detection and cache filtering."""

import json
import shutil
import sqlite3
import tempfile
from pathlib import Path

import pytest

from report_analyst.core.analysis_result_utils import (
    is_stored_analysis_error,
    normalize_results_container,
    session_answers_map,
    split_analysis_results,
)
from report_analyst.core.cache_manager import CacheManager


@pytest.fixture
def temp_db():
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test_cache.db"
    cache_manager = CacheManager(str(db_path))
    yield cache_manager
    shutil.rmtree(temp_dir)


def test_is_stored_analysis_error_detects_exception_answer():
    assert is_stored_analysis_error({"ANSWER": "Error analyzing document: 'str' object is not callable"})


def test_is_stored_analysis_error_detects_parse_failure_answer():
    assert is_stored_analysis_error({"ANSWER": "Error parsing analysis: invalid JSON"})


def test_is_stored_analysis_error_ignores_valid_answer():
    assert not is_stored_analysis_error({"ANSWER": "The board oversees climate risk.", "SCORE": 0.8})


def test_split_analysis_results_separates_failures():
    results = {
        "tcfd_1": {"result": {"ANSWER": "Error analyzing document: boom", "SCORE": 0}},
        "tcfd_2": {"result": {"ANSWER": "Valid answer", "SCORE": 1}},
    }
    successes, failures = split_analysis_results(results)
    assert list(successes) == ["tcfd_2"]
    assert failures["tcfd_1"].startswith("Error analyzing document:")


def test_cache_manager_refuses_to_save_error_result(temp_db):
    error_result = {
        "ANSWER": "Error analyzing document: boom",
        "SCORE": 0,
        "EVIDENCE": [],
        "GAPS": ["Error during analysis"],
        "SOURCES": [],
    }
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4o-mini",
        "question_set": "tcfd",
    }
    temp_db.save_analysis("test.pdf", "tcfd_1", error_result, config)
    cached = temp_db.get_analysis("test.pdf", config, question_ids=["tcfd_1"])
    assert cached == {}


def test_cache_manager_filters_legacy_error_results(temp_db):
    error_result = {
        "ANSWER": "Error analyzing document: legacy failure",
        "SCORE": 0,
        "EVIDENCE": [],
        "GAPS": ["Error during analysis"],
        "SOURCES": [],
    }
    good_result = {
        "ANSWER": "Board oversees climate risks.",
        "SCORE": 0.9,
        "EVIDENCE": [],
        "GAPS": [],
        "SOURCES": [],
        "chunks": [],
    }
    config = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": "gpt-4o-mini",
        "question_set": "tcfd",
    }
    with sqlite3.connect(temp_db.db_path) as conn:
        conn.execute(
            """
            INSERT INTO analysis_cache
            (file_path, question_id, chunk_size, chunk_overlap, top_k, model, question_set, result, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
            """,
            (
                "test.pdf",
                "tcfd_1",
                config["chunk_size"],
                config["chunk_overlap"],
                config["top_k"],
                config["model"],
                config["question_set"],
                json.dumps(error_result),
            ),
        )
    temp_db.save_analysis("test.pdf", "tcfd_2", good_result, config)
    cached = temp_db.get_analysis("test.pdf", config, question_ids=["tcfd_1", "tcfd_2"])
    assert "tcfd_1" not in cached
    assert "tcfd_2" in cached


def test_normalize_results_container_wraps_legacy_flat_shape():
    flat = {"tcfd_2": {"result": {"ANSWER": "yes"}}}
    assert normalize_results_container(flat) == {"answers": flat}


def test_normalize_results_container_preserves_nested_shape():
    nested = {"answers": {"tcfd_1": {"result": {"ANSWER": "ok"}}}}
    assert normalize_results_container(nested) == nested


def test_session_answers_map_reads_flat_or_nested():
    flat = {"tcfd_2": {"result": {"ANSWER": "flat"}}}
    nested = {"answers": {"tcfd_2": {"result": {"ANSWER": "nested"}}}}
    assert session_answers_map(flat) == flat
    assert session_answers_map(nested) == nested["answers"]
