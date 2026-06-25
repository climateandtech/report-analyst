"""Answer workflow via Streamlit AppTest — real st; stub LLM API only."""

from __future__ import annotations

import shutil
import tempfile
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from analyzer_init_helpers import create_document_analyzer_via_init, reset_document_analyzer_singleton
from report_analyst.core.cache_manager import CacheManager
from streamlit_test_helpers import build_report_analyzer_shell, default_session_state
from workflow_apptest_harness import run_answer_workflow_harness


@pytest.fixture(scope="session")
def _workflow_db_template():
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "analysis_template.db"
    CacheManager(str(db_path))
    yield db_path
    shutil.rmtree(temp_dir)


@pytest.fixture
def workflow_db(_workflow_db_template):
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / f"analysis_{uuid.uuid4().hex}.db"
    shutil.copy2(_workflow_db_template, db_path)
    yield db_path
    shutil.rmtree(temp_dir)


def _config(model: str = "gpt-4o-mini") -> dict:
    return {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "model": model,
        "question_set": "tcfd",
    }


def _questions() -> dict:
    return {
        "tcfd_1": {
            "text": "How does the board oversee climate-related risks?",
            "guidelines": "",
            "id": "tcfd_1",
            "number": 1,
        }
    }


def _seed_chunks(cache: CacheManager, file_path: str) -> None:
    cache.save_document_chunks(
        file_path=file_path,
        chunks=[
            {
                "text": "The board oversees climate-related risks and opportunities.",
                "metadata": {"page": 1},
                "embedding": np.array([0.7, 0.8], dtype=np.float32),
            }
        ],
        chunk_size=500,
        chunk_overlap=20,
    )


@pytest.fixture(autouse=True)
def _reset_singleton():
    reset_document_analyzer_singleton()
    yield
    reset_document_analyzer_singleton()


@pytest.fixture
def workflow_stack(monkeypatch, tmp_path, workflow_db):
    doc_analyzer, llm_mock = create_document_analyzer_via_init(monkeypatch, tmp_path)
    doc_analyzer.cache_manager = CacheManager(db_path=str(workflow_db))
    doc_analyzer.llm = llm_mock
    report = build_report_analyzer_shell(doc_analyzer, tmp_path)
    return report, llm_mock, doc_analyzer


def _run_workflow_apptest(workflow_stack, tmp_path, *, reanalyze: bool) -> tuple[AppTest, str, object]:
    report, _llm_mock, doc_analyzer = workflow_stack
    file_path = str(tmp_path / "report.pdf")

    patcher = patch.object(
        doc_analyzer,
        "get_question_by_number",
        return_value={"text": _questions()["tcfd_1"]["text"], "guidelines": ""},
    )
    patcher.start()
    try:
        at = AppTest.from_function(run_answer_workflow_harness)
        for key, value in default_session_state(force_recompute=reanalyze).items():
            at.session_state[key] = value
        at.session_state["_test_workflow_params"] = {
            "analyzer": report,
            "analysis_file_path": file_path,
            "file_path": file_path,
            "questions": _questions(),
            "selected_questions": ["tcfd_1"],
            "config": _config(),
            "max_step": "Answer",
            "reanalyze": reanalyze,
        }
        at.run(timeout=30)
    finally:
        patcher.stop()
    return at, file_path, doc_analyzer


def test_reanalyze_workflow_apptest_persists_and_renders_dataframes(monkeypatch, tmp_path, workflow_stack):
    report, llm_mock, doc_analyzer = workflow_stack
    file_path = str(tmp_path / "report.pdf")
    _seed_chunks(doc_analyzer.cache_manager, file_path)

    llm_mock.achat = AsyncMock(
        return_value=Mock(
            message=Mock(
                content=(
                    '{"ANSWER":"Board provides climate oversight.","SCORE":0.9,'
                    '"EVIDENCE":[],"GAPS":[],"SOURCES":[]}'
                )
            )
        )
    )

    at, file_path, doc_analyzer = _run_workflow_apptest(workflow_stack, tmp_path, reanalyze=True)

    assert not at.exception, str(at.exception)
    cached = doc_analyzer.cache_manager.get_analysis(file_path, _config(), ["tcfd_1"])
    assert cached["tcfd_1"]["result"]["ANSWER"] == "Board provides climate oversight."
    assert len(at.dataframe) >= 1, "real Streamlit should render analysis/chunk tables"
    assert not at.error


def test_analyze_workflow_apptest_persists_via_analyze_document_and_display(
    monkeypatch, tmp_path, workflow_stack
):
    _report, llm_mock, doc_analyzer = workflow_stack
    file_path = str(tmp_path / "report.pdf")
    _seed_chunks(doc_analyzer.cache_manager, file_path)

    llm_mock.achat = AsyncMock(
        return_value=Mock(
            message=Mock(
                content='{"ANSWER":"Management assesses climate risks.","SCORE":0.8,"EVIDENCE":[],"GAPS":[],"SOURCES":[]}'
            )
        )
    )

    at, file_path, doc_analyzer = _run_workflow_apptest(workflow_stack, tmp_path, reanalyze=False)

    assert not at.exception
    cached = doc_analyzer.cache_manager.get_analysis(file_path, _config(), ["tcfd_1"])
    assert "Management assesses climate risks." in cached["tcfd_1"]["result"]["ANSWER"]
    assert len(at.dataframe) >= 1


def test_reanalyze_workflow_apptest_shows_error_not_success_when_llm_fails(
    monkeypatch, tmp_path, workflow_stack
):
    _report, llm_mock, doc_analyzer = workflow_stack
    file_path = str(tmp_path / "report.pdf")
    _seed_chunks(doc_analyzer.cache_manager, file_path)

    llm_mock.achat = AsyncMock(side_effect=TypeError("'str' object is not callable"))

    at, file_path, doc_analyzer = _run_workflow_apptest(workflow_stack, tmp_path, reanalyze=True)

    assert doc_analyzer.cache_manager.get_analysis(file_path, _config(), ["tcfd_1"]) == {}
    assert not any("Analysis complete" in s.value for s in at.success)
    assert len(at.dataframe) >= 1, "chunk table should still render on failure"
    assert at.warning, "expect warning when answer results missing after failure"
