"""Unit tests for library evaluation helpers used by the OSA notebook."""

from types import SimpleNamespace

import pandas as pd

from report_analyst.core.benchmark.dataset_mapper import generate_chunk_id, generate_query_id
from report_analyst.core.benchmark.library_eval import (
    build_chunk_dataset_rows,
    build_climretrieve_answer_rows,
    build_ground_truth_rows,
    build_osa_retrieval_rows,
    build_overlap_table,
    build_retrieval_match_table,
    citation_consistency,
    cited_chunk_ids,
    match_question,
    metrics_to_frame,
    parse_osa_score,
    parse_yes_no_answer,
    query_match_metrics,
    ranked_query_metrics,
    retrieved_chunk_ids,
    score_stability,
    select_labelled_reports,
    topk_score_delta,
    write_eval_csvs,
)


def _labels() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Document": [
                "CT REIT 2022 ESG Report",
                "CT REIT 2022 ESG Report",
                "BHP Climate Change Report 2020",
                "Giant Unlabelled Co",
            ],
            "Question": [
                "What are the targets?",
                "What are the targets?",
                "What are the targets?",
                "What are the targets?",
            ],
            "Relevant": [
                "Net-zero by 2050 for operations.",
                "Science-based target for scope 1.",
                "Reduce operational emissions 30%.",
                "Only in spreadsheet, no PDF.",
            ],
            "Core 16 Question": [1, 1, 1, 1],
            "Source Relevance Score": [3, 2, 3, 1],
            "Answer": ["YES. Targets are disclosed."] * 2 + ["NO. No target."] * 2,
        }
    )


def test_match_question_aligns_near_duplicate_wording():
    clim = ["Does the company report climate change scenarios used to test strategy resilience?"]
    osa = "Does the company report the climate change scenarios used to test the resilience of its business strategy?"
    assert match_question(osa, clim) == clim[0]


def test_select_labelled_reports_prefers_named_pdfs_and_requires_labels():
    pdfs = [
        "CT REIT 2022 ESG Report.pdf",
        "BHP Climate Change Report 2020.pdf",
        "Unrelated.pdf",
    ]
    selected = select_labelled_reports(_labels(), pdfs, n=10)
    assert list(selected["pdf_filename"]) == [
        "CT REIT 2022 ESG Report.pdf",
        "BHP Climate Change Report 2020.pdf",
    ]
    assert selected.loc[0, "n_labels"] == 2


def test_build_ground_truth_rows_uses_stable_ids():
    gt = build_ground_truth_rows(_labels(), ["CT REIT 2022 ESG Report"])
    assert len(gt) == 2
    assert gt["query_id"].nunique() == 1
    assert gt.loc[0, "query_id"] == generate_query_id("CT REIT 2022 ESG Report", "What are the targets?")
    assert gt.loc[0, "chunk_id"] == generate_chunk_id("Net-zero by 2050 for operations.")
    assert list(gt["position"]) == [1, 2]


def test_build_osa_retrieval_rows_matches_overlapping_chunk():
    gt = build_ground_truth_rows(_labels(), ["CT REIT 2022 ESG Report"])
    retrieved = {
        ("CT REIT 2022 ESG Report", "What are the targets?"): [
            {"text": "Intro. Net-zero by 2050 for operations. Closing.", "score": 0.91},
            {"text": "Cafeteria menu changes.", "score": 0.11},
        ]
    }
    osa = build_osa_retrieval_rows(retrieved, gt)
    assert bool(osa.loc[0, "matched_climretrieve"]) is True
    assert osa.loc[0, "chunk_id"] == generate_chunk_id("Net-zero by 2050 for operations.")
    assert bool(osa.loc[1, "matched_climretrieve"]) is False


def test_build_chunk_dataset_rows_exports_text_without_embeddings():
    rows = build_chunk_dataset_rows(
        [
            {
                "text": "First generated chunk.",
                "embedding": [0.1, 0.2],
                "metadata": {"chunk_order": 4, "page": 7},
            },
            {"text": "Second generated chunk.", "metadata": {}},
        ],
        document="Report",
        pdf_filename="report.pdf",
        config_id="cs200",
        chunk_size=200,
        chunk_overlap=20,
    )

    assert rows["chunk_order"].tolist() == [4, 1]
    assert rows["page"].iloc[0] == 7
    assert "embedding" not in rows.columns
    assert rows["chunk_id"].nunique() == 2


def test_match_table_preserves_all_ground_truth_spans_for_the_query():
    labels = pd.DataFrame(
        {
            "Document": ["D", "D", "D"],
            "Question": ["Q", "Q", "Other Q"],
            "Relevant": ["alpha evidence", "beta evidence", "gamma evidence"],
            "Source Relevance Score": [2, 3, 3],
        }
    )
    gt = build_ground_truth_rows(labels, ["D"])
    retrieval = build_osa_retrieval_rows(
        {("D", "Q"): [{"text": "alpha evidence and beta evidence plus gamma evidence", "score": 0.9}]},
        gt,
    )

    matches = build_retrieval_match_table(retrieval, gt)

    assert set(matches["ground_truth_chunk_id"]) == {
        generate_chunk_id("alpha evidence"),
        generate_chunk_id("beta evidence"),
    }
    assert matches["relevance_grade"].max() == 3
    query_metrics = query_match_metrics(retrieval, gt, matches=matches)
    assert query_metrics.loc[0, "hit_count"] == 2
    assert query_metrics.loc[0, "strict_recall"] == 1.0
    ranking = ranked_query_metrics(
        retrieval,
        gt,
        matches=matches,
        corpus_matches=matches,
        k_values=[1],
        binary_relevance_min=2,
    )
    assert ranking.loc[0, "precision"] == 1.0
    assert ranking.loc[0, "ndcg"] == 1.0
    overlap = build_overlap_table(gt[gt["question"] == "Q"], retrieval, matches=matches)
    assert overlap.loc[0, "n_both"] == 2


def test_overlap_table_counts_intersection():
    gt = build_ground_truth_rows(_labels(), ["CT REIT 2022 ESG Report"])
    retrieved = {
        ("CT REIT 2022 ESG Report", "What are the targets?"): [
            {"text": "Net-zero by 2050 for operations.", "score": 0.9},
        ]
    }
    overlap = build_overlap_table(gt, build_osa_retrieval_rows(retrieved, gt))
    assert overlap.loc[0, "n_climretrieve"] == 2
    assert overlap.loc[0, "n_both"] == 1
    assert overlap.loc[0, "n_osa"] == 1


def test_parse_osa_score_from_string_and_number():
    assert parse_osa_score(7) == 7.0
    assert parse_osa_score("SCORE: 8.5 / 10") == 8.5
    assert parse_osa_score("n/a") is None


def test_climretrieve_answers_preserve_text_and_parse_explicit_yes_no():
    answers = build_climretrieve_answer_rows(_labels(), ["CT REIT 2022 ESG Report"])

    assert bool(answers.loc[0, "expert_yes_no"]) is True
    assert parse_yes_no_answer("[NO]. No target is disclosed.") is False
    assert parse_yes_no_answer("The report discusses targets.") is None


def test_cited_chunk_ids_use_one_based_sources():
    gt = build_ground_truth_rows(_labels(), ["CT REIT 2022 ESG Report"])
    chunks = [
        {"text": "Net-zero by 2050 for operations."},
        {"text": "Cafeteria menu changes."},
    ]
    ids = cited_chunk_ids({"SOURCES": [1]}, chunks, gt)
    assert ids == [generate_chunk_id("Net-zero by 2050 for operations.")]
    assert retrieved_chunk_ids(chunks, gt)[0] == ids[0]


def test_score_stability_and_topk_delta():
    runs = pd.DataFrame(
        {
            "document": ["A"] * 4,
            "question": ["Q"] * 4,
            "config_id": ["k5", "k5", "k10", "k10"],
            "run_id": [1, 2, 1, 2],
            "score": [6.0, 8.0, 7.0, 9.0],
        }
    )
    stability = score_stability(runs)
    k5 = stability[stability["config_id"] == "k5"].iloc[0]
    assert k5["score_mean"] == 7.0
    assert k5["score_min"] == 6.0
    delta = topk_score_delta(stability, "k5", "k10")
    assert delta.loc[0, "score_delta"] == 1.0


def test_citation_consistency_identical_runs_is_one():
    chunk = generate_chunk_id("same")
    runs = pd.DataFrame(
        {
            "document": ["A", "A"],
            "question": ["Q", "Q"],
            "config_id": ["k5", "k5"],
            "cited_chunk_ids": [chunk, chunk],
        }
    )
    consistency = citation_consistency(runs)
    assert consistency.loc[0, "citation_jaccard"] == 1.0


def test_write_eval_csvs_and_metrics_frame(tmp_path):
    metrics = SimpleNamespace(
        precision_at_k={1: 1.0, 3: 0.5},
        recall_at_k={1: 0.5, 3: 1.0},
        f1_at_k={1: 0.66, 3: 0.66},
        ndcg_at_k={1: 1.0, 3: 0.8},
        mean_average_precision=0.7,
        mean_reciprocal_rank=1.0,
    )
    metrics_df = metrics_to_frame(metrics, config_id="k5")
    assert "precision" in set(metrics_df["metric"])
    assert metrics_df.loc[metrics_df["metric"] == "MAP", "value"].iloc[0] == 0.7
    written = write_eval_csvs({"retrieval_metrics": metrics_df}, tmp_path)
    assert written["retrieval_metrics"].exists()
    loaded = pd.read_csv(written["retrieval_metrics"])
    assert len(loaded) == len(metrics_df)
