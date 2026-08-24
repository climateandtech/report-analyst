"""Robustness tests for OSA selected chunks and produced scores.

These encode the study checks:
- Are retrieved chunks stable across repeated runs?
- Are k=5 retrieved chunks contained in k=10 when ranking is stable?
- Are cited chunks a subset of retrieved chunks?
- How much do OSA scores move across runs and across top-k?
"""

import pandas as pd

from report_analyst.core.benchmark.library_eval import (
    build_analysis_run_rows,
    citation_subset_rate,
    citations_are_subset,
    generate_run_uid,
    pairwise_chunk_selection,
    retrieved_chunk_consistency,
    score_distribution_summary,
    score_range,
    score_stability,
    topk_retrieved_containment,
    topk_score_delta,
    yes_no_answer_comparison,
)


def _chunk_runs() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "document": ["R1"] * 6,
            "question": ["Q1"] * 6,
            "config_id": ["k5", "k5", "k5", "k10", "k10", "k10"],
            "run_id": [1, 2, 3, 1, 2, 3],
            "retrieved_chunk_ids": [
                "a|b|c|d|e",
                "a|b|c|d|e",
                "a|b|c|d|e",
                "a|b|c|d|e|f|g|h|i|j",
                "a|b|c|d|e|f|g|h|i|j",
                "a|b|c|d|e|f|g|h|i|j",
            ],
            "cited_chunk_ids": ["a|c", "a|c", "a|c", "a|c|f", "a|c|f", "a|c|f"],
            "score": [7.0, 7.0, 7.0, 8.0, 8.0, 8.0],
        }
    )


def test_retrieved_chunks_are_identical_across_repeated_runs():
    consistency = retrieved_chunk_consistency(_chunk_runs())
    k5 = consistency[consistency["config_id"] == "k5"].iloc[0]
    assert k5["n_runs"] == 3
    assert k5["retrieved_jaccard"] == 1.0


def test_retrieved_chunk_jaccard_drops_when_top_k_set_changes():
    runs = pd.DataFrame(
        {
            "document": ["R1", "R1"],
            "question": ["Q1", "Q1"],
            "config_id": ["k5", "k5"],
            "retrieved_chunk_ids": ["a|b|c|d|e", "a|b|c|d|z"],
        }
    )
    consistency = retrieved_chunk_consistency(runs)
    assert consistency.loc[0, "retrieved_jaccard"] < 1.0


def test_retrieved_chunks_at_k5_are_contained_in_k10():
    containment = topk_retrieved_containment(_chunk_runs(), "k5", "k10")
    assert len(containment) == 1
    assert containment.loc[0, "n_low"] == 5
    assert containment.loc[0, "n_high"] == 10
    assert containment.loc[0, "containment"] == 1.0


def test_cited_chunks_are_subset_of_retrieved_chunks():
    assert citations_are_subset(["a", "c"], ["a", "b", "c", "d", "e"])
    assert not citations_are_subset(["a", "z"], ["a", "b", "c"])
    assert citation_subset_rate(_chunk_runs()) == 1.0


def test_osa_scores_are_stable_when_repeated_runs_agree():
    stability = score_stability(_chunk_runs())
    k5 = stability[stability["config_id"] == "k5"].iloc[0]
    assert k5["score_mean"] == 7.0
    assert k5["score_min"] == k5["score_max"]
    assert float(score_range(stability)[k5.name]) == 0.0


def test_osa_scores_shift_when_topk_changes():
    stability = score_stability(_chunk_runs())
    delta = topk_score_delta(stability, "k5", "k10")
    assert delta.loc[0, "score_delta"] == 1.0


def test_analysis_run_rows_capture_answer_and_chunk_scores():
    result = {
        "SCORE": "8 / 10",
        "ANSWER": "The board reviews climate risk.",
        "SOURCES": [1],
        "chunks": [
            {
                "text": "The board reviews climate risk quarterly.",
                "chunk_order": 0,
                "similarity_score": 0.82,
                "llm_score": 0.91,
                "is_evidence": True,
                "evidence_order": 1,
                "metadata": {"page": 12},
            }
        ],
    }
    context = {
        "evaluation_id": "evaluation-1",
        "document": "R1",
        "question": "Q1",
        "config_id": "k5",
        "top_k": 5,
        "run_id": 1,
    }
    answer, chunks = build_analysis_run_rows(result, pd.DataFrame(), context)

    assert answer["answer_score"] == 8.0
    assert answer["run_uid"] == generate_run_uid(context)
    assert chunks[0]["llm_score"] == 0.91
    assert chunks[0]["page"] == 12


def test_run_uid_is_stable_within_evaluation_and_distinct_across_evaluations():
    context = {
        "evaluation_id": "evaluation-1",
        "document": "R1",
        "question": "Q1",
        "config_id": "k5",
        "run_id": 1,
    }
    first = generate_run_uid(context)
    second = generate_run_uid(context)
    other_evaluation = generate_run_uid({**context, "evaluation_id": "evaluation-2"})

    assert first == second
    assert first != other_evaluation


def test_pairwise_chunk_selection_and_ranges_are_boxplot_ready():
    pairs = pairwise_chunk_selection(_chunk_runs())
    summary = score_distribution_summary(pairs, "selection_jaccard")

    assert len(pairs) == 6
    assert set(["q1", "median", "q3", "range"]).issubset(summary.columns)
    assert summary["min"].min() == 1.0


def test_yes_no_answer_comparison_scores_only_explicit_labels():
    runs = pd.DataFrame(
        {
            "config_id": ["cs500_k5"] * 3,
            "chunk_size": [500] * 3,
            "top_k": [5] * 3,
            "expert_yes_no": [True, False, True],
            "answer": ["YES. Disclosed.", "YES. Disclosed.", "Narrative only."],
        }
    )
    detail, metrics = yes_no_answer_comparison(runs)

    assert len(detail) == 2
    assert metrics.loc[0, "accuracy"] == 0.5
