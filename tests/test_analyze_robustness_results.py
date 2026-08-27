"""Tests for analysis of denormalized robustness results."""

import pandas as pd
from scripts.analyze_robustness_results import (
    build_all_evaluation_metrics,
    build_answer_robustness_metrics,
    build_answer_robustness_summary,
    build_benchmark_manifest_frames,
    build_overall_classification_metrics,
    build_pairwise_citation_overlap,
    build_question_summary,
    build_topk_comparison,
    build_topk_containment,
    calculate_direct_retrieval_metrics,
    plot_all_evaluation_metrics_table,
    plot_answer_confusion_matrix,
    plot_answer_label_robustness,
    plot_answer_robustness_metrics_table,
    plot_citation_overlap_by_run_pair,
    plot_overall_performance_metrics,
    plot_paper_robustness_figure,
    plot_robustness_boxplots,
    plot_score_quantile_intervals_by_run,
    reconstruct_tables,
    run_sanity_checks,
)


def _raw_rows() -> pd.DataFrame:
    rows = []
    chunks_by_k = {
        2: ["a", "b"],
        3: ["a", "b", "c"],
    }
    for top_k, chunk_ids in chunks_by_k.items():
        run_uid = f"run-k{top_k}"
        for rank, chunk_id in enumerate(chunk_ids, start=1):
            rows.append(
                {
                    "evaluation_id": "evaluation",
                    "run_uid": run_uid,
                    "document": "Report.pdf",
                    "pdf_filename": "Report.pdf",
                    "question": "Question?",
                    "osa_question_id": "q1",
                    "config_id": f"cs200_k{top_k}",
                    "top_k": top_k,
                    "chunk_size": 200,
                    "chunk_overlap": 20,
                    "model": "test",
                    "run_id": 1,
                    "expert_answer": "Yes",
                    "expert_yes_no": True,
                    "answer_score": 6 + top_k,
                    "answer": "Yes",
                    "answer_yes_no": True,
                    "gaps": "[]",
                    "sources": "[1]",
                    "evidence": "[]",
                    "question_text": "Question?",
                    "guidelines": "",
                    "retrieved_chunk_ids": "|".join(chunk_ids),
                    "cited_chunk_ids": "a",
                    "n_retrieved": top_k,
                    "chunk_id": chunk_id,
                    "retrieval_rank": rank,
                    "chunk_order": rank,
                    "similarity_score": 1 / rank,
                    "llm_score": 1 / rank,
                    "is_evidence": chunk_id == "a",
                    "evidence_order": 1 if chunk_id == "a" else None,
                    "page": 1,
                    "chunk_text": f"Chunk {chunk_id}",
                }
            )
    return pd.DataFrame(rows)


def test_reconstruct_tables_does_not_count_answer_once_per_chunk():
    answers, chunks = reconstruct_tables(_raw_rows())

    assert len(answers) == 2
    assert answers["run_uid"].is_unique
    assert len(chunks) == 5


def test_topk_comparison_pairs_same_question_chunk_size_and_run():
    answers, _ = reconstruct_tables(_raw_rows())

    paired = build_topk_comparison(answers)
    containment = build_topk_containment(answers)

    assert paired.loc[0, "score_delta"] == 1
    assert not paired.loc[0, "answer_changed"]
    assert containment.loc[0, "containment"] == 1


def test_sanity_checks_accept_structurally_consistent_rows():
    raw = _raw_rows()
    answers, chunks = reconstruct_tables(raw)

    checks = run_sanity_checks(raw, answers, chunks)

    assert checks["passed"].all(), checks.loc[~checks["passed"], "detail"].tolist()


def test_question_summary_counts_unclear_as_answer_and_incorrect():
    answers, _ = reconstruct_tables(_raw_rows())
    unclear = answers.iloc[0].copy()
    unclear["run_uid"] = "unclear-run"
    unclear["run_id"] = 2
    unclear["answer"] = "Unclear"
    unclear["answer_yes_no"] = None
    answers = pd.concat([answers.iloc[[0]], unclear.to_frame().T], ignore_index=True)

    summary = build_question_summary(answers)

    assert summary.loc[0, "answer_agreement"] == 0.5
    assert summary.loc[0, "answer_accuracy"] == 0.5


def test_paper_robustness_figure_is_written(tmp_path):
    answers, _ = reconstruct_tables(_raw_rows())
    citations = answers[["document", "question", "config_id", "chunk_size", "top_k"]].copy()
    citations["n_runs"] = 1
    citations["citation_jaccard"] = 1.0

    plot_paper_robustness_figure(
        answers,
        citations,
        pd.DataFrame(),
        tmp_path,
    )

    assert (tmp_path / "paper_robustness_figure.png").exists()


def test_answer_confusion_matrix_counts_each_pair_configuration_once(tmp_path):
    answers, _ = reconstruct_tables(_raw_rows())

    plot_answer_confusion_matrix(answers, tmp_path)

    assert (tmp_path / "answer_confusion_matrix.png").exists()


def test_robustness_boxplots_are_written(tmp_path):
    answers, _ = reconstruct_tables(_raw_rows())
    citations = answers[["document", "question", "config_id"]].copy()
    citations["citation_jaccard"] = 1.0

    plot_robustness_boxplots(answers, citations, tmp_path)

    assert (tmp_path / "paper_robustness_boxplots.png").exists()


def test_score_quantile_interval_plot_is_written(tmp_path):
    answers, _ = reconstruct_tables(_raw_rows())

    plot_score_quantile_intervals_by_run(answers, tmp_path)

    assert (tmp_path / "answer_score_quantile_interval_plot.png").exists()


def test_pairwise_citation_overlap_and_plot(tmp_path):
    answers, _ = reconstruct_tables(_raw_rows())
    repeated = answers.iloc[[0]].copy()
    repeated["run_uid"] = "repeat"
    repeated["run_id"] = 2
    repeated["cited_chunk_ids"] = "b"
    answers = pd.concat([answers.iloc[[0]], repeated], ignore_index=True)

    overlaps = build_pairwise_citation_overlap(answers)
    plot_citation_overlap_by_run_pair(answers, tmp_path)

    assert overlaps.loc[0, "citation_jaccard"] == 0
    assert overlaps.loc[0, "citation_change"] == 1
    assert overlaps.loc[0, "changed_chunk_count"] == 2
    assert (tmp_path / "citation_chunk_change_by_run_pair.png").exists()


def test_direct_retrieval_metrics_use_annotated_pairs_only():
    answers, chunks = reconstruct_tables(_raw_rows())
    labels = pd.DataFrame(
        [
            {
                "Document": "Report.pdf",
                "Question": "Question?",
                "Context": "Chunk",
                "Relevant": "Chunk",
                "Answer": "Yes.",
                "Source Relevance Score": 3,
                "Core 16 Question": 1,
            }
        ]
    )

    frames = calculate_direct_retrieval_metrics(answers, chunks, labels)

    assert len(frames["direct_query_ranking_metrics"]) == 2
    assert frames["direct_query_ranking_metrics"]["hit"].all()
    assert frames["direct_query_ranking_metrics"]["ndcg"].eq(1).all()
    assert sorted(frames["direct_query_ranking_metrics"]["precision"]) == [1 / 3, 1 / 2]
    assert frames["direct_query_ranking_metrics"]["recall"].eq(1).all()
    assert frames["direct_query_match_metrics"]["strict_recall"].eq(1).all()


def test_overall_classification_metrics_count_unclear_as_incorrect():
    answers = pd.DataFrame(
        [
            {
                "document": document,
                "question": "Question?",
                "config_id": "config",
                "answer_yes_no": prediction,
                "answer": answer,
                "expert_yes_no": expert,
                "expert_answer": "Yes" if expert else "No",
            }
            for document, prediction, answer, expert in [
                ("yes.pdf", None, "Unclear", True),
                ("no.pdf", False, "No", False),
            ]
        ]
    )

    metrics = build_overall_classification_metrics(answers).iloc[0]

    assert metrics["coverage"] == 0.5
    assert metrics["accuracy"] == 0.5
    assert metrics["answered_accuracy"] == 1
    assert metrics["balanced_accuracy"] == 0.5
    assert metrics["macro_f1"] == 0.5


def test_overall_performance_metrics_plot_is_written(tmp_path):
    answers, chunks = reconstruct_tables(_raw_rows())
    labels = pd.DataFrame(
        [
            {
                "Document": "Report.pdf",
                "Question": "Question?",
                "Context": "Chunk a",
                "Relevant": "Chunk a",
                "Answer": "Yes.",
                "Source Relevance Score": 3,
                "Core 16 Question": 1,
            }
        ]
    )
    retrieval = calculate_direct_retrieval_metrics(
        answers,
        chunks,
        labels,
    )

    classification = build_overall_classification_metrics(answers)
    ranking = retrieval["direct_ranking_summary"]
    robustness = build_answer_robustness_summary(answers)
    metrics = build_all_evaluation_metrics(
        classification,
        robustness,
        ranking,
    )
    plot_overall_performance_metrics(classification, ranking, tmp_path)
    plot_all_evaluation_metrics_table(metrics, tmp_path)

    assert (tmp_path / "overall_performance_metrics.png").exists()
    assert (tmp_path / "all_evaluation_metrics_table.png").exists()
    assert set(metrics["section"]) == {
        "Classification",
        "Direct retrieval",
        "Robustness",
    }


def test_answer_label_robustness_plot_is_written(tmp_path):
    answers, _ = reconstruct_tables(_raw_rows())

    plot_answer_label_robustness(answers, tmp_path)
    summary = build_answer_robustness_summary(answers)
    metrics = build_answer_robustness_metrics(answers)
    plot_answer_robustness_metrics_table(metrics, tmp_path)

    assert (tmp_path / "answer_label_robustness.png").exists()
    assert (tmp_path / "answer_robustness_metrics_table.png").exists()
    assert summary["label_stability_rate"].eq(1).all()
    assert summary["answer_text_stability_rate"].eq(1).all()
    assert metrics["changed_pairs"].eq(0).all()


def test_benchmark_manifest_emits_and_validates_full_matrix(tmp_path):
    manifest = tmp_path / "questions.yaml"
    manifest.write_text(
        """
documents:
  - A.pdf
  - B.pdf
questions:
  - id: q1
    text: Question one?
  - id: q2
    text: Question two?
"""
    )
    labels = pd.DataFrame(
        [
            {
                "Document": "A.pdf",
                "Question": "Question one?",
                "Relevant": "Evidence.",
                "Answer": "[YES].",
            }
        ]
    )

    frames = build_benchmark_manifest_frames(labels, manifest)

    assert frames["benchmark_reports"]["document"].tolist() == [
        "A.pdf",
        "B.pdf",
    ]
    assert len(frames["benchmark_pair_coverage"]) == 4
    assert frames["benchmark_pair_coverage"]["has_human_label"].sum() == 1
