"""Shared Streamlit session + ReportAnalyzer shell for workflow integration tests."""

from __future__ import annotations

import types

from report_analyst.core.prompt_manager import PromptManager
from report_analyst.streamlit_app import ReportAnalyzer


class FakeSessionState(dict):
    def get(self, key, default=None):
        return super().get(key, default)

    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self[name] = value


def default_session_state(**overrides) -> FakeSessionState:
    base = {
        "chunk_size": 500,
        "chunk_overlap": 20,
        "top_k": 5,
        "llm_model": "gpt-4o-mini",
        "question_set": "tcfd",
        "force_recompute": False,
        "new_llm_scoring": False,
        "new_chunk_size": 500,
        "new_overlap": 20,
        "new_top_k": 5,
        "new_llm_model": "gpt-4o-mini",
        "new_question_set": "tcfd",
        "new_batch_scoring": True,
        "results": {"answers": {}},
    }
    base.update(overrides)
    return FakeSessionState(base)


def build_report_analyzer_shell(doc_analyzer, tmp_path) -> ReportAnalyzer:
    """ReportAnalyzer wrapper around an already-initialized DocumentAnalyzer (no second singleton)."""
    shell = ReportAnalyzer.__new__(ReportAnalyzer)
    shell.temp_dir = tmp_path / "uploads"
    shell.analyzer = doc_analyzer
    shell.cache_manager = doc_analyzer.cache_manager
    shell.prompt_manager = PromptManager()
    shell.process_document = types.MethodType(ReportAnalyzer.process_document, shell)
    shell.analyze_document = types.MethodType(ReportAnalyzer.analyze_document, shell)
    return shell
