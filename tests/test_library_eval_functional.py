"""Functional: library eval helpers feed EvaluationEngine and emit CSV artifacts."""

from pathlib import Path

import pandas as pd

from report_analyst.core.benchmark.evaluation_engine import EvaluationEngine
from report_analyst.core.benchmark.library_eval import (
    build_ground_truth_rows,
    build_osa_retrieval_rows,
    build_overlap_table,
    metrics_to_frame,
    write_eval_csvs,
)
from report_analyst.core.benchmark.retrieval_results_loader import load_flexible_dataset_from_csv


def test_retrieval_tables_evaluate_and_export_csvs(tmp_path: Path):
    labels = pd.DataFrame(
        {
            "document": ["Report A", "Report A"],
            "question": ["Q1", "Q1"],
            "relevant": ["Climate board oversight is described.", "Net-zero target for 2050."],
            "relevance_score": [3, 2],
        }
    )
    gt = build_ground_truth_rows(labels, ["Report A"])
    retrieved = {
        ("Report A", "Q1"): [
            {"text": "Preface. Climate board oversight is described. End.", "score": 0.88},
            {"text": "Office recycling bins.", "score": 0.12},
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
    assert metrics.recall_at_k[2] == 0.5
    assert overlap.loc[0, "n_both"] == 1

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
