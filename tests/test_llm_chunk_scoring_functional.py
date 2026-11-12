"""Functional: LLM scoring through process_document with a real SQLite cache.

Reproduces the production failure mode where enabling LLM scoring still stores
0.0 for every chunk because ``achat(prompt=...)`` is invalid for LlamaIndex OpenAI.
"""

from __future__ import annotations

import json
import re
from typing import Any, List, Sequence
from unittest.mock import Mock

import pytest
from llama_index.core.llms import ChatMessage

from report_analyst.core.analyzer import DocumentAnalyzer
from report_analyst.core.cache_manager import CacheManager


class MessagesOnlyLLM:
    """LlamaIndex-OpenAI-shaped stub: messages required, prompt= rejected."""

    model = "gpt-4o-mini-test"

    def __init__(self):
        self.score_calls = 0
        self.analyze_calls = 0

    async def achat(self, messages: Sequence[ChatMessage], **kwargs: Any):
        if "prompt" in kwargs:
            raise TypeError("missing a required argument: 'messages'")
        if messages is None:
            raise TypeError("missing a required argument: 'messages'")
        text = "\n".join(getattr(m, "content", "") for m in messages)
        if "Output only the scores" in text or "Output only the numeric score" in text:
            self.score_calls += 1
            # Content-aware scores: numeric target high, vague governance low.
            # Only real fragment headers look like "[CHUNK 1]\n...".
            chunk_bodies = re.findall(r"\[CHUNK \d+\]\n(.*?)(?=\n\[CHUNK \d+\]|\Z)", text, flags=re.S)
            if chunk_bodies:
                lines = ["1.0" if ("0,13" in body or "0.13" in body) else "0.2" for body in chunk_bodies]
                return Mock(message=Mock(content="\n".join(lines)))
            return Mock(message=Mock(content="1.0" if ("0,13" in text or "0.13" in text) else "0.2"))
        self.analyze_calls += 1
        return Mock(
            message=Mock(
                content=json.dumps(
                    {
                        "ANSWER": "Target 0.13 t CO2e by 2035.",
                        "SCORE": "7",
                        "EVIDENCE": [{"text": "0.13 intensity target", "chunk": 1}],
                        "GAPS": [],
                        "SOURCES": [1],
                    }
                )
            )
        )


@pytest.fixture
def functional_analyzer(tmp_path, monkeypatch):
    """Functional: real CacheManager DB, stubbed embeddings + messages-only LLM."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("OPENAI_API_MODEL", "gpt-4o-mini")
    DocumentAnalyzer.reset_instance()

    db_path = tmp_path / "analysis.db"
    storage = tmp_path / "storage"
    (storage / "cache").mkdir(parents=True)
    (storage / "llm_cache").mkdir(parents=True)

    analyzer = DocumentAnalyzer()
    analyzer.storage_path = storage
    analyzer.cache_path = storage / "cache"
    analyzer.llm_cache_path = storage / "llm_cache"
    analyzer.cache_manager = CacheManager(db_path=str(db_path))
    analyzer.llm = MessagesOnlyLLM()
    analyzer.update_question_set("tcfd")
    analyzer.update_parameters(chunk_size=500, chunk_overlap=20, top_k=2)

    # Avoid embedding API: inject precomputed chunks + similar-chunk stub.
    async def fake_similar(query_text, chunks, top_k):
        selected = chunks[:top_k]
        for i, chunk in enumerate(selected):
            chunk = dict(chunk)
            chunk["score"] = 0.8 - (i * 0.01)
            chunk["similarity_score"] = chunk["score"]
            selected[i] = chunk
        # Put the weak chunk first (embedding order), strong target second —
        # LLM scoring should still assign a high score to the target chunk.
        return selected

    analyzer._get_similar_chunks = fake_similar  # type: ignore[method-assign]
    yield analyzer
    DocumentAnalyzer.reset_instance()


@pytest.mark.asyncio
async def test_process_document_llm_scoring_persists_nonzero_scores(functional_analyzer, tmp_path):
    """Functional: with LLM scoring on, stored llm_score must not be all zeros."""
    pdf = tmp_path / "conti-like.pdf"
    pdf.write_bytes(b"%PDF-1.4\n%fixture")

    pre_chunks = [
        {
            "chunk_text": "Governance overview and IRO assessment methodology without numbers.",
            "chunk_metadata": {"page": 1, "source": "fixture"},
        },
        {
            "chunk_text": (
                "Ziele in Bezug auf Scope-1- und Scope-2-Emissionen: Intensitaet von "
                "0,13 t CO2e pro Tonne bis 2035, Zwischenziel 0,17 bis 2030."
            ),
            "chunk_metadata": {"page": 128, "source": "fixture"},
        },
    ]

    results: List[dict] = []
    async for event in functional_analyzer.process_document(
        file_path=str(pdf),
        selected_questions=[11],
        use_llm_scoring=True,
        single_call=True,
        force_recompute=True,
        pre_retrieved_chunks=pre_chunks,
    ):
        results.append(event)

    assert functional_analyzer.llm.score_calls >= 1
    result_events = [event for event in results if "result" in event]
    assert result_events, "expected an analysis result event"

    result = result_events[0]["result"]
    scored_chunks = result.get("chunks") or []
    llm_scores = [
        float(chunk["llm_score"]) for chunk in scored_chunks if isinstance(chunk, dict) and chunk.get("llm_score") is not None
    ]
    assert llm_scores, "expected llm_score values on scored chunks"
    assert max(llm_scores) > 0.0, "LLM scoring must not silently store only 0.0"

    # After re-rank, the numeric target passage should be first for the answer prompt.
    assert "0,13" in scored_chunks[0]["text"] or "0.13" in scored_chunks[0]["text"]

    cached = functional_analyzer.cache_manager.get_analysis(
        str(pdf),
        {
            "chunk_size": 500,
            "chunk_overlap": 20,
            "top_k": 2,
            "model": functional_analyzer.llm.model,
            "question_set": "tcfd",
        },
    )
    assert "tcfd_11" in cached
