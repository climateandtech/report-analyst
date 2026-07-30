"""Additional coverage for evaluation engine dataset comparison."""

import pytest

from report_analyst.core.benchmark.evaluation_engine import EvaluationEngine
from report_analyst.core.benchmark.retrieval_results_loader import load_flexible_dataset_from_csv
from report_analyst.models.benchmark import (
    EvaluationMetrics,
    RetrievalResultRow,
    RetrievalResultsDataset,
)


def _legacy_ds(dataset_id: str, rows):
    return RetrievalResultsDataset(
        dataset_id=dataset_id,
        name=dataset_id,
        source="csv",
        results=rows,
    )


def test_compare_datasets_legacy_matching():
    engine = EvaluationEngine()
    reference = _legacy_ds(
        "ref",
        [
            RetrievalResultRow(query_id="q1", chunk_id="c1", position=1, score=1.0),
            RetrievalResultRow(query_id="q1", chunk_id="c2", position=2, score=0.5),
        ],
    )
    input_ds = _legacy_ds(
        "inp",
        [
            RetrievalResultRow(
                query_id="q1",
                chunk_id="c1",
                position=1,
                score=0.9,
                metadata={"relevant_text_sim": 0.99},
            ),
            RetrievalResultRow(
                query_id="q1",
                chunk_id="c99",
                position=2,
                score=0.8,
                metadata={"relevant_text_sim": 0.1},
            ),
        ],
    )
    metrics = engine.compare_datasets(reference, input_ds, k_values=[1, 2])
    assert metrics.precision_at_k[1] > 0
    assert 2 in metrics.precision_at_k


def test_compare_datasets_no_common_queries():
    engine = EvaluationEngine()
    reference = _legacy_ds(
        "ref",
        [RetrievalResultRow(query_id="q1", chunk_id="c1", position=1, score=1.0)],
    )
    input_ds = _legacy_ds(
        "inp",
        [RetrievalResultRow(query_id="q2", chunk_id="c1", position=1, score=1.0)],
    )
    metrics = engine.compare_datasets(reference, input_ds)
    assert metrics.mean_average_precision == 0.0


def test_compare_flexible_with_relevant_part_id_and_sim_scores():
    engine = EvaluationEngine()
    reference_csv = """query_id,chunk_id,position,score,relevant_part_id
q1,gt1,1,1.0,gt1
q1,gt2,2,0.5,gt2"""
    input_csv = """query_id,chunk_id,position,score,relevant_part_id,relevant_text_sim
q1,p1,1,0.1,gt1,0.99
q1,p2,2,0.1,gt2,0.5"""
    reference = load_flexible_dataset_from_csv(csv_content=reference_csv)
    input_dataset = load_flexible_dataset_from_csv(csv_content=input_csv)
    metrics = engine.compare_flexible_datasets(reference, input_dataset, k_values=[1, 2])
    assert metrics.precision_at_k[1] == 1.0


def test_compare_evaluations_reports_improvements():
    engine = EvaluationEngine()
    e1 = EvaluationMetrics(
        precision_at_k={1: 0.5},
        recall_at_k={1: 0.4},
        f1_at_k={1: 0.45},
        mean_reciprocal_rank=0.5,
        mean_average_precision=0.4,
        ndcg_at_k={1: 0.3},
    )
    e2 = EvaluationMetrics(
        precision_at_k={1: 0.8},
        recall_at_k={1: 0.7},
        f1_at_k={1: 0.75},
        mean_reciprocal_rank=0.9,
        mean_average_precision=0.8,
        ndcg_at_k={1: 0.6},
    )
    diff = engine.compare_evaluations(e1, e2)
    assert diff["precision_at_1_improvement"] == pytest.approx(0.3)
    assert diff["mrr_improvement"] == pytest.approx(0.4)
