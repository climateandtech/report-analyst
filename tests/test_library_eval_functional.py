"""Functional: library eval helpers feed EvaluationEngine and emit CSV artifacts."""

import json
from pathlib import Path

import pandas as pd

from report_analyst.core.benchmark.evaluation_engine import EvaluationEngine
from report_analyst.core.benchmark.library_eval import (
    bootstrap_macro_intervals,
    build_ground_truth_rows,
    build_osa_retrieval_rows,
    build_overlap_table,
    metrics_to_frame,
    query_match_metrics,
    ranked_query_metrics,
    write_eval_csvs,
)
from report_analyst.core.benchmark.retrieval_results_loader import load_flexible_dataset_from_csv

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "ct_reit_chunk_matching.json"


def fixture_chunk(fixture, chunk_size: int, chunk_index: int) -> dict:
    chunks = fixture["chunks"][str(chunk_size)]
    return next(chunk for chunk in chunks if chunk["document_chunk_index"] == chunk_index)


def test_retrieval_tables_evaluate_and_export_csvs(tmp_path: Path):
    fixture = json.loads(FIXTURE_PATH.read_text())
    document = fixture["source"]["report"]
    question = fixture["question"]
    labels = pd.DataFrame(
        {
            "document": [document],
            "question": [question],
            "relevant": [fixture["ground_truth"]["text"]],
            "relevance_score": [fixture["ground_truth"]["relevance_score"]],
        }
    )
    gt = build_ground_truth_rows(labels, [document])
    full_match = fixture_chunk(fixture, 200, 77)
    unrelated = fixture_chunk(fixture, 200, 4)
    partial = fixture_chunk(fixture, 200, 49)
    retrieved = {
        (document, question): [
            {"text": full_match["text"], "score": full_match["ground_truth_similarity"]},
            {"text": unrelated["text"], "score": unrelated["ground_truth_similarity"]},
            {"text": partial["text"], "score": partial["ground_truth_similarity"]},
        ]
    }
    osa = build_osa_retrieval_rows(retrieved, gt)
    overlap = build_overlap_table(gt, osa)

    gt_path = tmp_path / "ground_truth.csv"
    osa_path = tmp_path / "osa_retrieval.csv"
    gt.to_csv(gt_path, index=False)
    osa.to_csv(osa_path, index=False)

    reference = load_flexible_dataset_from_csv(csv_path=str(gt_path), dataset_name="climretrieve")
    benchmark = load_flexible_dataset_from_csv(csv_path=str(osa_path), dataset_name="osa")
    metrics = EvaluationEngine().compare_flexible_datasets(reference, benchmark, k_values=[1, 2])

    assert metrics.precision_at_k[1] == 1.0
    assert metrics.recall_at_k[2] == 1.0
    assert overlap.loc[0, "n_both"] == 1
    assert osa.loc[0, "match_relation"] == "retrieved_contains_ground_truth"
    assert not osa.loc[2, "matched_climretrieve"]

    written = write_eval_csvs(
        {
            "climretrieve_ground_truth": gt,
            "osa_retrieval": osa,
            "chunk_overlap": overlap,
            "retrieval_metrics": metrics_to_frame(metrics, config_id="k2"),
        },
        tmp_path / "out",
    )
    for path in written.values():
        assert path.exists()
        assert len(pd.read_csv(path)) >= 1


def test_split_ground_truth_gain_occurs_when_second_adjacent_chunk_arrives():
    fixture = json.loads(FIXTURE_PATH.read_text())
    document = fixture["source"]["report"]
    question = fixture["question"]
    ground_truth = fixture_chunk(fixture, 400, 45)
    first = fixture_chunk(fixture, 200, 76)
    second = fixture_chunk(fixture, 200, 77)
    gt = build_ground_truth_rows(
        pd.DataFrame(
            {
                "document": [document],
                "question": [question],
                "relevant": [ground_truth["text"]],
                "relevance_score": [3],
            }
        ),
        [document],
    )
    retrieved = {
        (document, question): [
            {"text": first["text"], "chunk_order": first["document_chunk_index"], "score": 0.9},
            {"text": second["text"], "chunk_order": second["document_chunk_index"], "score": 0.8},
        ]
    }

    rows = build_osa_retrieval_rows(retrieved, gt)

    assert rows.loc[1, "match_relation"] == "ground_truth_split_across_retrieved"
    assert rows["matched_climretrieve"].tolist() == [False, True]
    summary = query_match_metrics(rows, gt)
    assert summary.loc[0, "strict_recall"] == 1.0
    assert summary.loc[0, "split_hit_count"] == 1
    ranked = ranked_query_metrics(rows, gt, k_values=[1, 2], binary_relevance_min=2)
    assert ranked.loc[ranked["k"] == 1, "recall"].iloc[0] == 0.0
    assert ranked.loc[ranked["k"] == 2, "recall"].iloc[0] == 1.0
    intervals = bootstrap_macro_intervals(ranked, ["recall"], group_columns=["k"], n_bootstrap=100)
    assert intervals.loc[intervals["k"] == 2, "ci_low"].iloc[0] == 1.0
