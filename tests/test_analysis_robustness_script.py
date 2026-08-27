"""Tests for incremental robustness-evaluation checkpoints."""

import json

import pandas as pd
import pytest
from scripts.evaluate_analysis_robustness import (
    checkpoint_run,
    load_configured_documents,
    map_questions,
    select_configured_reports,
    summarize_evaluation,
    validate_complete_matrix,
)

from report_analyst.core.question_loader import get_question_loader


@pytest.mark.parametrize(
    ("question_set", "expected_reports"),
    [
        ("climretrieve_complete", 13),
        ("climretrieve_complete_6", 8),
    ],
)
def test_complete_benchmark_profiles_have_configured_reports(
    question_set,
    expected_reports,
):
    assert len(load_configured_documents(question_set)) == expected_reports


def test_complete_profile_maps_all_questions_without_limit():
    configured = get_question_loader().get_questions("climretrieve_complete_6")
    labels = pd.DataFrame({"question": [question["text"] for question in configured.values()]})

    assert (
        len(
            map_questions(
                labels,
                "climretrieve_complete_6",
                limit=None,
                exact_only=True,
            )
        )
        == 6
    )


def test_complete_profile_rejects_similar_nonidentical_question():
    configured = get_question_loader().get_questions("climretrieve_complete_6")
    questions = [question["text"] for question in configured.values()]
    questions[0] = questions[0].replace("reference", "refer to")
    labels = pd.DataFrame({"question": questions})

    with pytest.raises(RuntimeError, match="missing exact ClimRetrieve matches"):
        map_questions(
            labels,
            "climretrieve_complete_6",
            limit=None,
            exact_only=True,
        )


def test_checkpoint_run_persists_each_result_before_next_run(tmp_path):
    context = {
        "evaluation_id": "evaluation-1",
        "document": "Report A",
        "pdf_filename": "report-a.pdf",
        "question": "Q1",
        "config_id": "cs500_k5",
        "top_k": 5,
        "chunk_size": 500,
        "chunk_overlap": 50,
        "model": "test-model",
        "run_id": 1,
    }
    result = {
        "SCORE": 7,
        "ANSWER": "Answer one",
        "SOURCES": [1],
        "chunks": [
            {
                "text": "Selected evidence.",
                "similarity_score": 0.8,
                "llm_score": 0.9,
                "is_evidence": True,
                "metadata": {"page": 3},
            }
        ],
    }

    checkpoint_run(tmp_path, result, pd.DataFrame(), context)
    context["run_id"] = 2
    result["SCORE"] = 8
    checkpoint_run(tmp_path, result, pd.DataFrame(), context)

    runs = pd.read_csv(tmp_path / "analysis_runs.csv")
    chunks = pd.read_csv(tmp_path / "chunk_scores.csv")
    combined = pd.read_csv(tmp_path / "all_results.csv")
    raw = [json.loads(line) for line in (tmp_path / "raw_analysis_runs.jsonl").read_text().splitlines()]
    assert list(runs["answer_score"]) == [7.0, 8.0]
    assert runs["run_uid"].nunique() == 2
    assert len(chunks) == 2
    assert len(combined) == 2
    assert {"answer_score", "llm_score", "chunk_id"}.issubset(combined.columns)
    assert [row["run_id"] for row in raw] == [1, 2]

    summarize_evaluation(tmp_path, [5], [500])
    assert (tmp_path / "answer_score_boxplot.png").exists()
    assert (tmp_path / "chunk_llm_score_boxplot.png").exists()
    assert (tmp_path / "chunk_selection_boxplot.png").exists()
    assert (tmp_path / "answer_score_ranges.csv").exists()


def test_summaries_separate_topk_and_chunk_size_factors(tmp_path):
    result = {
        "SCORE": 7,
        "ANSWER": "Answer",
        "SOURCES": [1],
        "chunks": [{"text": "Evidence", "similarity_score": 0.8, "llm_score": 0.9}],
    }
    for chunk_size in (300, 500):
        for top_k in (3, 5):
            for run_id in (1, 2):
                context = {
                    "evaluation_id": "factorial-evaluation",
                    "document": "Report A",
                    "pdf_filename": "report-a.pdf",
                    "question": "Q1",
                    "config_id": f"cs{chunk_size}_k{top_k}",
                    "top_k": top_k,
                    "chunk_size": chunk_size,
                    "chunk_overlap": 50,
                    "model": "test-model",
                    "run_id": run_id,
                }
                checkpoint_run(tmp_path, result, pd.DataFrame(), context)

    summarize_evaluation(tmp_path, [3, 5], [300, 500])
    ranges = pd.read_csv(tmp_path / "answer_score_ranges.csv")

    assert len(ranges) == 4
    assert (tmp_path / "topk_answer_score_delta.csv").exists()
    assert (tmp_path / "chunk_size_answer_score_delta.csv").exists()


def test_configured_reports_fail_when_a_pdf_is_missing():
    labels = pd.DataFrame(
        [
            {
                "Document": document,
                "Question": "Question?",
                "Relevant": "Evidence",
                "Answer": "[YES].",
                "Core 16 Question": 1,
            }
            for document in ("A.pdf", "B.pdf")
        ]
    )

    with pytest.raises(RuntimeError, match=r"missing PDFs: B\.pdf"):
        select_configured_reports(
            labels,
            ["A.pdf"],
            ["A.pdf", "B.pdf"],
        )


def test_configured_reports_fail_when_human_label_pair_is_missing():
    labels = pd.DataFrame([{"document": "A.pdf", "question": "Question one?"}])
    reports = pd.DataFrame({"document": ["A.pdf"]})
    questions = pd.DataFrame({"climretrieve_question": ["Question one?", "Question two?"]})

    with pytest.raises(RuntimeError, match="missing 1 human-labelled pairs"):
        validate_complete_matrix(labels, reports, questions)
