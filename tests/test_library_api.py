"""Unit tests for the public library API used by custom host apps."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import yaml

from report_analyst.core.library import (
    GroundedAnswer,
    analyze_report,
    build_topic_brief,
    load_questions_from_yaml,
    resolve_questions,
)


def test_load_questions_from_yaml(tmp_path: Path):
    path = tmp_path / "water_questions.yaml"
    path.write_text(
        yaml.dump(
            {
                "name": "Water",
                "questions": [
                    {"id": "water_1", "text": "Water targets?", "guidelines": "Look for m3"},
                    {"id": "water_2", "text": "Water stress sites?"},
                ],
            }
        ),
        encoding="utf-8",
    )
    questions = load_questions_from_yaml(path)
    assert list(questions) == ["water_1", "water_2"]
    assert questions["water_1"]["number"] == 1
    assert questions["water_2"]["text"] == "Water stress sites?"


def test_resolve_questions_from_dict():
    questions, set_id = resolve_questions(
        {"topic_1": {"text": "A?", "guidelines": ""}},
        question_set_id="topic",
    )
    assert set_id == "topic"
    assert questions["topic_1"]["number"] == 1


def test_build_topic_brief_counts_evidence():
    answers = [
        GroundedAnswer(
            question_id="q1",
            question_text="Q1?",
            answer="Yes",
            score=0.8,
            evidence=["quote"],
        ),
        GroundedAnswer(
            question_id="q2",
            question_text="Q2?",
            answer="",
            score=0.0,
            evidence=[],
            gaps=["missing"],
        ),
    ]
    brief = build_topic_brief(answers, topic="Water risk")
    assert brief["topic"] == "Water risk"
    assert brief["answered_count"] == 1
    assert brief["evidence_backed_count"] == 1
    assert brief["findings"][0]["evidence"] == ["quote"]


@pytest.mark.asyncio
async def test_analyze_report_returns_grounded_answers(tmp_path: Path):
    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"%PDF-1.4 demo")

    async def fake_process(_path, selected, **_kwargs):
        yield {"status": "starting"}
        yield {
            "question_number": selected[0],
            "question_id": "water_1",
            "result": {
                "ANSWER": "Net water reduction of 20%.",
                "SCORE": 0.9,
                "EVIDENCE": ["page 12: reduced withdrawal"],
                "GAPS": [],
                "SOURCES": ["p.12"],
            },
        }

    analyzer = MagicMock()
    analyzer.process_document = fake_process
    analyzer.update_parameters = MagicMock()
    analyzer.default_model = "gpt-4o-mini"

    with patch("report_analyst.core.analyzer.DocumentAnalyzer", return_value=analyzer):
        answers = await analyze_report(
            pdf,
            {"water_1": {"text": "Water targets?", "guidelines": ""}},
            question_set_id="water",
        )

    assert len(answers) == 1
    assert answers[0].answer.startswith("Net water")
    assert answers[0].evidence == ["page 12: reduced withdrawal"]
    assert answers[0].score == 0.9


@pytest.mark.asyncio
async def test_analyze_report_rejects_missing_pdf(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        await analyze_report(tmp_path / "missing.pdf", {"q_1": {"text": "Q?"}})


@pytest.mark.asyncio
async def test_analyze_report_propagates_analyzer_error(tmp_path: Path):
    pdf = tmp_path / "report.pdf"
    pdf.write_bytes(b"%PDF-1.4 demo")

    async def fake_process(_path, _selected, **_kwargs):
        yield {"error": "No API key configured"}

    analyzer = MagicMock()
    analyzer.process_document = fake_process
    analyzer.update_parameters = MagicMock()

    with patch("report_analyst.core.analyzer.DocumentAnalyzer", return_value=analyzer):
        with pytest.raises(RuntimeError, match="No API key"):
            await analyze_report(
                pdf,
                {"water_1": {"text": "Water targets?"}},
                question_set_id="water",
            )
