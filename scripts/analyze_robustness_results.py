#!/usr/bin/env python3
"""Analyze a denormalized OSA robustness CSV and render comparison charts."""

from __future__ import annotations

import argparse
import re
import sys
import textwrap
from itertools import combinations
from pathlib import Path
from typing import Any

import matplotlib
import numpy as np
import pandas as pd
import yaml

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import PercentFormatter

sys.path.insert(0, str(Path(__file__).parent.parent))

from report_analyst.core.benchmark.library_eval import (
    build_ground_truth_rows,
    build_retrieval_match_table,
    citation_consistency,
    generate_chunk_id,
    generate_query_id,
    normalize_climretrieve_columns,
    query_match_metrics,
    retrieved_chunk_consistency,
    summarize_query_match_metrics,
    summarize_ranked_query_metrics,
)

ANSWER_COLUMNS = [
    "evaluation_id",
    "run_uid",
    "document",
    "pdf_filename",
    "question",
    "osa_question_id",
    "config_id",
    "top_k",
    "chunk_size",
    "chunk_overlap",
    "model",
    "run_id",
    "expert_answer",
    "expert_yes_no",
    "answer_score",
    "answer",
    "answer_yes_no",
    "gaps",
    "sources",
    "evidence",
    "question_text",
    "guidelines",
    "retrieved_chunk_ids",
    "cited_chunk_ids",
    "n_retrieved",
]
CHUNK_COLUMNS = [
    "run_uid",
    "document",
    "question",
    "config_id",
    "top_k",
    "chunk_size",
    "run_id",
    "chunk_id",
    "retrieval_rank",
    "chunk_order",
    "similarity_score",
    "llm_score",
    "is_evidence",
    "evidence_order",
    "page",
    "chunk_text",
]
DEFAULT_BENCHMARK_QUESTION_SET = (
    Path(__file__).parent.parent / "report_analyst" / "questionsets" / "climretrieve_complete_questions.yaml"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_csv", type=Path)
    parser.add_argument(
        "--labels",
        type=Path,
        help="Optional ClimRetrieve CSV/XLSX for direct-match retrieval metrics",
    )
    parser.add_argument(
        "--benchmark-question-set",
        type=Path,
        default=DEFAULT_BENCHMARK_QUESTION_SET,
        help="Question-set manifest used to emit the valid benchmark matrix",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("evaluation_output/robustness_analysis"),
    )
    return parser.parse_args()


def require_columns(frame: pd.DataFrame) -> None:
    required = {
        "run_uid",
        "document",
        "question",
        "config_id",
        "top_k",
        "chunk_size",
        "run_id",
        "answer_score",
        "answer_yes_no",
        "expert_yes_no",
        "retrieved_chunk_ids",
        "cited_chunk_ids",
        "n_retrieved",
        "chunk_id",
        "retrieval_rank",
    }
    missing = sorted(required - set(frame.columns))
    if missing:
        raise ValueError(f"Input CSV is missing required columns: {', '.join(missing)}")


def reconstruct_tables(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Recover one answer row per run and one row per retrieved chunk."""
    require_columns(raw)
    answer_columns = [column for column in ANSWER_COLUMNS if column in raw.columns]
    chunk_columns = [column for column in CHUNK_COLUMNS if column in raw.columns]
    answers = (
        raw.sort_values(["run_uid", "retrieval_rank"], na_position="last")
        .drop_duplicates("run_uid")[answer_columns]
        .reset_index(drop=True)
    )
    chunks = (
        raw.dropna(subset=["chunk_id"])[chunk_columns].drop_duplicates(["run_uid", "retrieval_rank"]).reset_index(drop=True)
    )
    return answers, chunks


def split_ids(value: Any) -> set[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return set()
    return {part for part in str(value).split("|") if part}


def normalize_answer_label(binary_value: Any, answer: Any = None) -> str | None:
    """Preserve non-binary answers instead of dropping them from agreement."""
    if not pd.isna(binary_value):
        if isinstance(binary_value, bool):
            return "Yes" if binary_value else "No"
        normalized = str(binary_value).strip().lower()
        if normalized in {"true", "yes", "1"}:
            return "Yes"
        if normalized in {"false", "no", "0"}:
            return "No"
    if answer is None or pd.isna(answer):
        return None
    normalized_answer = str(answer).strip().lower()
    if normalized_answer.startswith("yes"):
        return "Yes"
    if normalized_answer.startswith("no"):
        return "No"
    if normalized_answer.startswith("unclear"):
        return "Unclear"
    if normalized_answer.startswith("not disclosed"):
        return "Not disclosed"
    return "Other"


def build_pair_classifications(answers: pd.DataFrame) -> pd.DataFrame:
    """Collapse repeated runs to one modal classification per labelled pair."""
    working = answers.copy()
    working["osa_label"] = [
        normalize_answer_label(binary, answer)
        for binary, answer in zip(
            working["answer_yes_no"],
            working["answer"],
            strict=True,
        )
    ]
    working["expert_label"] = [
        normalize_answer_label(binary, answer)
        for binary, answer in zip(
            working["expert_yes_no"],
            working["expert_answer"],
            strict=True,
        )
    ]
    rows = []
    for key, group in working.groupby(
        ["document", "question", "config_id"],
        dropna=False,
    ):
        predictions = group["osa_label"].dropna()
        expert_labels = group["expert_label"].dropna()
        if predictions.empty or expert_labels.empty:
            continue
        rows.append(
            {
                "document": key[0],
                "question": key[1],
                "config_id": key[2],
                "expert_label": expert_labels.iloc[0],
                "osa_label": predictions.mode().iloc[0],
            }
        )
    pairs = pd.DataFrame(rows)
    if pairs.empty:
        return pairs
    return pairs[pairs["expert_label"].isin({"Yes", "No"})].reset_index(drop=True)


def build_overall_classification_metrics(
    answers: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate pair-level binary metrics with abstentions as errors."""
    pairs = build_pair_classifications(answers)
    if pairs.empty:
        return pd.DataFrame()
    rows = []
    for config_id, group in pairs.groupby("config_id", dropna=False):
        expert_yes = group["expert_label"].eq("Yes")
        expert_no = group["expert_label"].eq("No")
        predicted_yes = group["osa_label"].eq("Yes")
        predicted_no = group["osa_label"].eq("No")
        answered = predicted_yes | predicted_no
        correct = group["osa_label"].eq(group["expert_label"])
        yes_tp = int((expert_yes & predicted_yes).sum())
        yes_fp = int((expert_no & predicted_yes).sum())
        yes_fn = int((expert_yes & ~predicted_yes).sum())
        no_tp = int((expert_no & predicted_no).sum())
        no_fp = int((expert_yes & predicted_no).sum())
        no_fn = int((expert_no & ~predicted_no).sum())
        yes_precision = yes_tp / (yes_tp + yes_fp) if yes_tp + yes_fp else 0.0
        yes_recall = yes_tp / (yes_tp + yes_fn) if yes_tp + yes_fn else 0.0
        no_precision = no_tp / (no_tp + no_fp) if no_tp + no_fp else 0.0
        no_recall = no_tp / (no_tp + no_fn) if no_tp + no_fn else 0.0
        yes_f1 = 2 * yes_precision * yes_recall / (yes_precision + yes_recall) if yes_precision + yes_recall else 0.0
        no_f1 = 2 * no_precision * no_recall / (no_precision + no_recall) if no_precision + no_recall else 0.0
        rows.append(
            {
                "config_id": config_id,
                "n_labelled_pairs": len(group),
                "n_answered": int(answered.sum()),
                "n_unclear_or_other": int((~answered).sum()),
                "coverage": answered.mean(),
                "accuracy": correct.mean(),
                "answered_accuracy": (correct[answered].mean() if answered.any() else 0.0),
                "balanced_accuracy": (yes_recall + no_recall) / 2,
                "macro_f1": (yes_f1 + no_f1) / 2,
                "yes_precision": yes_precision,
                "yes_recall": yes_recall,
                "yes_f1": yes_f1,
                "no_precision": no_precision,
                "no_recall": no_recall,
                "no_f1": no_f1,
            }
        )
    return pd.DataFrame(rows)


def build_answer_robustness_summary(
    answers: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize exact run-to-run stability for answer outputs."""
    working = answers.copy()
    working["answer_label"] = [
        normalize_answer_label(binary, answer)
        for binary, answer in zip(
            working["answer_yes_no"],
            working["answer"],
            strict=True,
        )
    ]
    pair_metrics = (
        working.groupby(["document", "question", "config_id"])
        .agg(
            label_stable=(
                "answer_label",
                lambda values: values.nunique(dropna=False) == 1,
            ),
            answer_text_stable=(
                "answer",
                lambda values: values.nunique(dropna=False) == 1,
            ),
            score_stable=(
                "answer_score",
                lambda values: values.nunique(dropna=False) == 1,
            ),
            citation_set_stable=(
                "cited_chunk_ids",
                lambda values: values.nunique(dropna=False) == 1,
            ),
        )
        .reset_index()
    )
    return (
        pair_metrics.groupby("config_id")
        .agg(
            n_pairs=("label_stable", "size"),
            label_stability_rate=("label_stable", "mean"),
            answer_text_stability_rate=("answer_text_stable", "mean"),
            score_stability_rate=("score_stable", "mean"),
            citation_set_stability_rate=("citation_set_stable", "mean"),
        )
        .reset_index()
    )


def build_answer_robustness_metrics(
    answers: pd.DataFrame,
) -> pd.DataFrame:
    """Return presentation-ready stability counts and rates."""
    summary = build_answer_robustness_summary(answers)
    metric_columns = [
        ("Answer label", "label_stability_rate"),
        ("Exact answer text", "answer_text_stability_rate"),
        ("Answer score", "score_stability_rate"),
        ("Citation set", "citation_set_stability_rate"),
    ]
    rows = []
    for result in summary.itertuples(index=False):
        for metric, column in metric_columns:
            rate = float(getattr(result, column))
            stable_pairs = round(result.n_pairs * rate)
            rows.append(
                {
                    "config_id": result.config_id,
                    "metric": metric,
                    "stable_pairs": stable_pairs,
                    "changed_pairs": result.n_pairs - stable_pairs,
                    "total_pairs": result.n_pairs,
                    "stability_rate": rate,
                }
            )
    return pd.DataFrame(rows)


def _append_evaluation_metrics(
    rows: list[dict[str, Any]],
    *,
    config_id: str,
    section: str,
    result: pd.Series,
    metrics: list[tuple[str, str]],
    count_column: str,
    scope: str,
) -> None:
    for metric, column in metrics:
        rows.append(
            {
                "config_id": config_id,
                "section": section,
                "metric": metric,
                "value": float(result[column]),
                "n_pairs": int(result[count_column]),
                "scope": scope,
            }
        )


def build_all_evaluation_metrics(
    classification: pd.DataFrame,
    robustness: pd.DataFrame,
    retrieval: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Combine classification, retrieval, and robustness by configuration."""
    frames = [classification, robustness]
    if retrieval is not None:
        frames.append(retrieval)
    config_ids = sorted(
        {str(config_id) for frame in frames if not frame.empty for config_id in frame["config_id"].dropna().unique()}
    )
    rows: list[dict[str, Any]] = []
    for config_id in config_ids:
        selected = classification[classification["config_id"].eq(config_id)]
        if not selected.empty:
            _append_evaluation_metrics(
                rows,
                config_id=config_id,
                section="Classification",
                result=selected.iloc[0],
                metrics=[
                    ("Accuracy", "accuracy"),
                    ("Answered-only accuracy", "answered_accuracy"),
                    ("Balanced accuracy", "balanced_accuracy"),
                    ("Macro F1", "macro_f1"),
                    ("Answer coverage", "coverage"),
                    ("Yes precision", "yes_precision"),
                    ("Yes recall", "yes_recall"),
                    ("Yes F1", "yes_f1"),
                    ("No precision", "no_precision"),
                    ("No recall", "no_recall"),
                    ("No F1", "no_f1"),
                ],
                count_column="n_labelled_pairs",
                scope="Human-labelled pairs",
            )
        if retrieval is not None:
            selected = retrieval[retrieval["config_id"].eq(config_id)]
            if not selected.empty:
                result = selected.iloc[0]
                cutoff = int(result["k"])
                _append_evaluation_metrics(
                    rows,
                    config_id=config_id,
                    section="Direct retrieval",
                    result=result,
                    metrics=[
                        (f"Precision@{cutoff}", "precision"),
                        (f"Evidence recall@{cutoff}", "recall"),
                        (f"F1@{cutoff}", "f1"),
                        (f"nDCG@{cutoff}", "ndcg"),
                        (f"Hit rate@{cutoff}", "hit_rate"),
                        (f"Complete-set hit@{cutoff}", "complete_set_hit_rate"),
                        (f"MAP@{cutoff}", "MAP"),
                        (f"MRR@{cutoff}", "MRR"),
                    ],
                    count_column="n_queries",
                    scope="Human-annotated queries",
                )
        selected = robustness[robustness["config_id"].eq(config_id)]
        if not selected.empty:
            _append_evaluation_metrics(
                rows,
                config_id=config_id,
                section="Robustness",
                result=selected.iloc[0],
                metrics=[
                    ("Answer-label stability", "label_stability_rate"),
                    ("Exact-text stability", "answer_text_stability_rate"),
                    ("Answer-score stability", "score_stability_rate"),
                    ("Citation-set stability", "citation_set_stability_rate"),
                ],
                count_column="n_pairs",
                scope="Repeated report-question pairs",
            )
    return pd.DataFrame(rows)


def build_question_summary(answers: pd.DataFrame) -> pd.DataFrame:
    """Summarize all answer categories and score variation by configuration."""
    working = answers.copy()
    working["predicted_label"] = [
        normalize_answer_label(binary, answer)
        for binary, answer in zip(
            working["answer_yes_no"],
            working["answer"],
            strict=True,
        )
    ]
    working["expert_label"] = [
        normalize_answer_label(binary, answer)
        for binary, answer in zip(
            working["expert_yes_no"],
            working["expert_answer"],
            strict=True,
        )
    ]
    working["answer_score"] = pd.to_numeric(working["answer_score"], errors="coerce")
    group_columns = ["document", "question", "config_id", "chunk_size", "top_k"]
    rows = []
    for key, group in working.groupby(group_columns, dropna=False):
        predictions = group["predicted_label"].dropna()
        modal = predictions.mode()
        labelled = group.dropna(subset=["expert_label"])
        rows.append(
            {
                **dict(zip(group_columns, key, strict=True)),
                "n_runs": len(group),
                "mean_answer_score": group["answer_score"].mean(),
                "answer_score_std": group["answer_score"].std(),
                "modal_answer": modal.iloc[0] if not modal.empty else None,
                "answer_agreement": (
                    predictions.value_counts(normalize=True).iloc[0] if not predictions.empty else float("nan")
                ),
                "answer_accuracy": (
                    (labelled["predicted_label"] == labelled["expert_label"]).mean() if not labelled.empty else float("nan")
                ),
                "n_expert_labelled_runs": len(labelled),
            }
        )
    return pd.DataFrame(rows)


def build_topk_comparison(answers: pd.DataFrame) -> pd.DataFrame:
    """Pair answer scores at different top-k values within each repeated run."""
    keys = ["document", "question", "chunk_size", "run_id"]
    score_rows = answers.copy()
    score_rows["answer_score"] = pd.to_numeric(score_rows["answer_score"], errors="coerce")
    score_pivot = score_rows.pivot_table(
        index=keys,
        columns="top_k",
        values="answer_score",
        aggfunc="first",
    )
    answer_pivot = score_rows.pivot_table(
        index=keys,
        columns="top_k",
        values="answer_yes_no",
        aggfunc="first",
    )
    top_values = sorted(score_rows["top_k"].dropna().astype(int).unique())
    if len(top_values) < 2:
        return pd.DataFrame()
    low_k, high_k = top_values[0], top_values[-1]
    paired = score_pivot.reset_index()
    if low_k not in paired or high_k not in paired:
        return pd.DataFrame()
    paired["low_k"] = low_k
    paired["high_k"] = high_k
    paired["score_delta"] = paired[high_k] - paired[low_k]
    answer_pairs = answer_pivot.reset_index()
    if low_k in answer_pairs and high_k in answer_pairs:
        answer_pairs["answer_changed"] = (
            answer_pairs[low_k].notna()
            & answer_pairs[high_k].notna()
            & (answer_pairs[low_k].astype(str) != answer_pairs[high_k].astype(str))
        )
        paired = paired.merge(
            answer_pairs[[*keys, "answer_changed"]],
            on=keys,
            how="left",
        )
    return paired


def build_topk_containment(answers: pd.DataFrame) -> pd.DataFrame:
    """Measure whether low-k selected chunks remain in the high-k result."""
    keys = ["document", "question", "chunk_size", "run_id"]
    top_values = sorted(answers["top_k"].dropna().astype(int).unique())
    if len(top_values) < 2:
        return pd.DataFrame()
    low_k, high_k = top_values[0], top_values[-1]
    low = answers[answers["top_k"] == low_k].set_index(keys)
    high = answers[answers["top_k"] == high_k].set_index(keys)
    rows = []
    for key in low.index.intersection(high.index):
        low_ids = split_ids(low.loc[key, "retrieved_chunk_ids"])
        high_ids = split_ids(high.loc[key, "retrieved_chunk_ids"])
        shared = low_ids & high_ids
        values = key if isinstance(key, tuple) else (key,)
        rows.append(
            {
                **dict(zip(keys, values, strict=True)),
                "low_k": low_k,
                "high_k": high_k,
                "n_low": len(low_ids),
                "n_high": len(high_ids),
                "n_shared": len(shared),
                "containment": len(shared) / len(low_ids) if low_ids else 1.0,
            }
        )
    return pd.DataFrame(rows)


def _check(name: str, passed: bool, detail: str) -> dict[str, Any]:
    return {"check": name, "passed": bool(passed), "detail": detail}


def run_sanity_checks(
    raw: pd.DataFrame,
    answers: pd.DataFrame,
    chunks: pd.DataFrame,
) -> pd.DataFrame:
    """Return machine-readable structural checks for manual review."""
    checks = []
    checks.append(
        _check(
            "one_answer_per_run_uid",
            answers["run_uid"].is_unique,
            f"{len(answers)} reconstructed runs",
        )
    )
    config_pattern = re.compile(r"^cs(?P<size>\d+)_k(?P<k>\d+)$")
    config_matches = answers["config_id"].astype(str).str.extract(config_pattern)
    config_ok = (
        config_matches["size"].astype(float).eq(pd.to_numeric(answers["chunk_size"])).all()
        and config_matches["k"].astype(float).eq(pd.to_numeric(answers["top_k"])).all()
    )
    checks.append(_check("config_id_matches_parameters", config_ok, "cs<size>_k<top-k>"))

    actual_counts = chunks.groupby("run_uid").size()
    expected_counts = answers.set_index("run_uid")["n_retrieved"].astype(int)
    aligned_counts = (
        expected_counts.to_frame("expected")
        .join(
            actual_counts.rename("actual"),
            how="left",
        )
        .fillna({"actual": 0})
    )
    count_ok = aligned_counts["expected"].eq(aligned_counts["actual"]).all()
    checks.append(
        _check(
            "chunk_count_matches_n_retrieved",
            count_ok,
            f"{int((~aligned_counts['expected'].eq(aligned_counts['actual'])).sum())} mismatches",
        )
    )

    rank_ok = all(
        sorted(group["retrieval_rank"].astype(int).tolist()) == list(range(1, len(group) + 1))
        for _, group in chunks.groupby("run_uid")
    )
    checks.append(_check("retrieval_ranks_are_contiguous", rank_ok, "expected ranks 1..k"))

    citation_flags = [
        split_ids(cited).issubset(split_ids(retrieved))
        for cited, retrieved in zip(
            answers["cited_chunk_ids"],
            answers["retrieved_chunk_ids"],
            strict=True,
        )
    ]
    checks.append(
        _check(
            "citations_are_retrieved",
            all(citation_flags),
            f"{citation_flags.count(False)} runs cite a non-retrieved chunk",
        )
    )

    run_counts = answers.groupby(["document", "question", "config_id"])["run_id"].nunique()
    checks.append(
        _check(
            "balanced_repeat_counts",
            run_counts.nunique() == 1,
            f"repeat counts range {run_counts.min()}-{run_counts.max()}",
        )
    )
    duplicate_rows = raw.duplicated(["run_uid", "retrieval_rank"]).sum()
    checks.append(
        _check(
            "no_duplicate_run_rank_rows",
            duplicate_rows == 0,
            f"{int(duplicate_rows)} duplicate run/rank rows",
        )
    )
    return pd.DataFrame(checks)


def config_metadata(answers: pd.DataFrame) -> pd.DataFrame:
    return (
        answers[["config_id", "chunk_size", "top_k"]]
        .drop_duplicates()
        .sort_values(["chunk_size", "top_k", "config_id"])
        .reset_index(drop=True)
    )


def pivot_metric(
    frame: pd.DataFrame,
    document: str,
    questions: list[str],
    configs: list[str],
    metric: str,
) -> pd.DataFrame:
    subset = frame[frame["document"] == document]
    return subset.pivot(index="question", columns="config_id", values=metric).reindex(
        index=questions,
        columns=configs,
    )


def draw_heatmap(
    ax: Any,
    matrix: pd.DataFrame,
    title: str,
    x_labels: list[str],
    y_labels: list[str],
) -> Any:
    image = ax.imshow(matrix, aspect="auto", cmap="viridis", vmin=0, vmax=1)
    ax.set_title(title)
    ax.set_xticks(range(len(x_labels)), x_labels, rotation=35, ha="right")
    ax.set_yticks(range(len(y_labels)), y_labels)
    for row_index in range(len(y_labels)):
        for column_index in range(len(x_labels)):
            value = matrix.iloc[row_index, column_index]
            label = "-" if pd.isna(value) else f"{value:.2f}"
            ax.text(column_index, row_index, label, ha="center", va="center", fontsize=8)
    return image


def plot_configuration_heatmaps(
    answers: pd.DataFrame,
    summary: pd.DataFrame,
    retrieved: pd.DataFrame,
    citations: pd.DataFrame,
    output_dir: Path,
) -> None:
    metadata = config_metadata(answers)
    configs = metadata["config_id"].tolist()
    x_labels = [f"{row.chunk_size} / k={row.top_k}" for row in metadata.itertuples(index=False)]
    retrieved_summary = summary.merge(
        retrieved[["document", "question", "config_id", "retrieved_jaccard"]],
        on=["document", "question", "config_id"],
        how="left",
    ).merge(
        citations[["document", "question", "config_id", "citation_jaccard"]],
        on=["document", "question", "config_id"],
        how="left",
    )
    for document in sorted(summary["document"].dropna().unique()):
        questions = summary.loc[summary["document"] == document, "question"].drop_duplicates().tolist()
        y_labels = [textwrap.shorten(question, width=58, placeholder="…") for question in questions]
        metrics = [
            ("answer_accuracy", "Answer correctness"),
            ("answer_agreement", "Answer agreement"),
            ("retrieved_jaccard", "Retrieved-chunk stability"),
            ("citation_jaccard", "Citation stability"),
        ]
        height = max(5.0, len(questions) * 0.65)
        fig, axes = plt.subplots(1, 4, figsize=(22, height), sharey=True)
        for ax, (metric, title) in zip(axes, metrics, strict=True):
            matrix = pivot_metric(
                retrieved_summary,
                document,
                questions,
                configs,
                metric,
            )
            image = draw_heatmap(ax, matrix, title, x_labels, y_labels)
            fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04, label="Rate (0-1)")
        axes[0].set_ylabel("Question")
        fig.suptitle(f"Answer and chunk-selection robustness — {document}")
        fig.tight_layout()
        name = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(document).stem).strip("_")
        fig.savefig(output_dir / f"configuration_heatmaps_{name}.png", dpi=180)
        plt.close(fig)


def plot_score_stability(
    answers: pd.DataFrame,
    output_dir: Path,
) -> None:
    metadata = config_metadata(answers)
    for document in sorted(answers["document"].dropna().unique()):
        subset = answers[answers["document"] == document]
        questions = subset["question"].drop_duplicates().tolist()
        labels = [textwrap.shorten(question, width=42, placeholder="…") for question in questions]
        x = np.arange(len(questions))
        fig, ax = plt.subplots(figsize=(max(11, len(questions) * 2.1), 5.5))
        offsets = np.linspace(-0.24, 0.24, len(metadata))
        for offset, config in zip(offsets, metadata.itertuples(index=False), strict=True):
            config_rows = subset[subset["config_id"] == config.config_id]
            grouped = config_rows.groupby("question")["answer_score"]
            mean = grouped.mean().reindex(questions)
            minimum = grouped.min().reindex(questions)
            maximum = grouped.max().reindex(questions)
            yerr = np.vstack([mean - minimum, maximum - mean])
            ax.errorbar(
                x + offset,
                mean,
                yerr=yerr,
                marker="o",
                capsize=3,
                linestyle="none",
                label=f"{config.chunk_size} / k={config.top_k}",
            )
        ax.set_xticks(x, labels, rotation=25, ha="right")
        ax.set(
            xlabel="Question",
            ylabel="Answer score (mean and run range)",
            title=f"Answer-score stability — {document}",
        )
        ax.grid(axis="y", alpha=0.3)
        ax.legend(title="Configuration")
        fig.tight_layout()
        name = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(document).stem).strip("_")
        fig.savefig(output_dir / f"answer_score_stability_{name}.png", dpi=180)
        plt.close(fig)


def plot_topk_sensitivity(paired: pd.DataFrame, output_dir: Path) -> None:
    if paired.empty:
        return
    summary = paired.groupby(["document", "question", "chunk_size"])["score_delta"].mean().reset_index()
    limit = max(1.0, float(summary["score_delta"].abs().max()))
    for document in sorted(summary["document"].dropna().unique()):
        subset = summary[summary["document"] == document]
        questions = subset["question"].drop_duplicates().tolist()
        chunk_sizes = sorted(subset["chunk_size"].unique())
        matrix = subset.pivot(
            index="question",
            columns="chunk_size",
            values="score_delta",
        ).reindex(index=questions, columns=chunk_sizes)
        labels = [textwrap.shorten(question, width=58, placeholder="…") for question in questions]
        fig, ax = plt.subplots(figsize=(7, max(4.5, len(questions) * 0.65)))
        image = ax.imshow(
            matrix,
            aspect="auto",
            cmap="coolwarm",
            vmin=-limit,
            vmax=limit,
        )
        ax.set_xticks(range(len(chunk_sizes)), [f"{size} tokens" for size in chunk_sizes])
        ax.set_yticks(range(len(labels)), labels)
        ax.set(
            xlabel="Chunk size",
            ylabel="Question",
            title="Mean answer-score change: high-k minus low-k",
        )
        for row_index in range(len(labels)):
            for column_index in range(len(chunk_sizes)):
                value = matrix.iloc[row_index, column_index]
                label = "-" if pd.isna(value) else f"{value:+.2f}"
                ax.text(column_index, row_index, label, ha="center", va="center")
        fig.colorbar(image, ax=ax, label="Mean score difference")
        fig.tight_layout()
        name = re.sub(r"[^A-Za-z0-9_-]+", "_", Path(document).stem).strip("_")
        fig.savefig(output_dir / f"topk_score_sensitivity_{name}.png", dpi=180)
        plt.close(fig)


def _plot_score_ranges(ax: Any, answers: pd.DataFrame) -> None:
    group_columns = ["document", "question", "config_id"]
    ranges = answers.groupby(group_columns)["answer_score"].agg(["mean", "min", "max"]).reset_index()
    ranges["score_range"] = ranges["max"] - ranges["min"]
    groups = list(ranges.groupby(["document", "config_id"], sort=True))
    multiple_configs = ranges["config_id"].nunique() > 1
    labels = []
    for index, ((document, config_id), rows) in enumerate(groups):
        values = rows["score_range"].dropna().to_numpy()
        x = np.linspace(index - 0.16, index + 0.16, len(values))
        ax.scatter(x, values, color="#4C78A8", alpha=0.55, s=24)
        median = float(np.median(values))
        q1, q3 = np.quantile(values, [0.25, 0.75])
        ax.errorbar(
            index,
            median,
            yerr=[[median - q1], [q3 - median]],
            marker="D",
            linestyle="none",
            capsize=5,
            color="#173F5F",
            markersize=7,
        )
        label = textwrap.shorten(Path(document).stem, width=22, placeholder="...")
        labels.append(f"{label}\n{config_id}" if multiple_configs else label)
    ax.set_xticks(range(len(labels)), labels, rotation=25, ha="right")
    ax.set(
        title="A. Run-to-run score variation",
        xlabel="Report",
        ylabel="Score range within each question",
    )
    ax.grid(axis="y", alpha=0.25)


def _plot_topk_panel(ax: Any, paired: pd.DataFrame, answers: pd.DataFrame) -> None:
    if paired.empty:
        top_values = ", ".join(str(value) for value in sorted(answers["top_k"].dropna().astype(int).unique()))
        ax.text(
            0.5,
            0.5,
            f"Unavailable in current data\nObserved top-k: {top_values}",
            ha="center",
            va="center",
            fontsize=12,
        )
        ax.set_title("B. Top-k score sensitivity")
        ax.set_axis_off()
        return
    chunk_sizes = sorted(paired["chunk_size"].dropna().unique())
    values = [paired.loc[paired["chunk_size"] == chunk_size, "score_delta"].dropna() for chunk_size in chunk_sizes]
    ax.boxplot(values, tick_labels=[f"{size} tokens" for size in chunk_sizes])
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set(
        title="B. Top-k score sensitivity",
        xlabel="Chunk size",
        ylabel="High-k minus low-k score",
    )
    ax.grid(axis="y", alpha=0.25)


def _plot_citation_distributions(
    ax: Any,
    answers: pd.DataFrame,
    citations: pd.DataFrame,
    panel_label: str,
) -> None:
    metadata = answers[["document", "config_id"]].drop_duplicates()
    values = citations.merge(metadata, on=["document", "config_id"], how="inner")
    groups = list(values.groupby(["document", "config_id"], sort=True))
    multiple_configs = values["config_id"].nunique() > 1
    labels = []
    for index, ((document, config_id), rows) in enumerate(groups):
        scores = rows["citation_jaccard"].dropna().to_numpy()
        x = np.linspace(index - 0.16, index + 0.16, len(scores))
        ax.scatter(x, scores, color="#F58518", alpha=0.55, s=24)
        median = float(np.median(scores))
        q1, q3 = np.quantile(scores, [0.25, 0.75])
        ax.errorbar(
            index,
            median,
            yerr=[[median - q1], [q3 - median]],
            marker="D",
            linestyle="none",
            capsize=5,
            color="#8C3B00",
            markersize=7,
        )
        label = textwrap.shorten(Path(document).stem, width=22, placeholder="...")
        labels.append(f"{label}\n{config_id}" if multiple_configs else label)
    ax.set_xticks(range(len(labels)), labels, rotation=25, ha="right")
    ax.set_ylim(-0.03, 1.05)
    ax.set(
        title=f"{panel_label}. Citation overlap across repeated runs",
        xlabel="Report",
        ylabel="Citation-set Jaccard",
    )
    ax.grid(axis="y", alpha=0.25)


def _plot_exact_stability_rates(
    ax: Any,
    answers: pd.DataFrame,
    citations: pd.DataFrame,
) -> None:
    score_pairs = answers.groupby(["document", "question", "config_id"])["answer_score"].agg(["min", "max"]).reset_index()
    score_pairs["score_stable"] = score_pairs["min"].eq(score_pairs["max"])
    score_summary = (
        score_pairs.groupby(["document", "config_id"])["score_stable"]
        .agg(["sum", "count", "mean"])
        .reset_index()
        .rename(
            columns={
                "sum": "score_stable_count",
                "count": "question_count",
                "mean": "score_stable_rate",
            }
        )
    )
    citation_pairs = citations.copy()
    citation_pairs["citation_stable"] = citation_pairs["citation_jaccard"].eq(1.0)
    citation_summary = (
        citation_pairs.groupby(["document", "config_id"])["citation_stable"]
        .agg(["sum", "mean"])
        .reset_index()
        .rename(
            columns={
                "sum": "citation_stable_count",
                "mean": "citation_stable_rate",
            }
        )
    )
    summary = score_summary.merge(
        citation_summary,
        on=["document", "config_id"],
        how="inner",
    ).sort_values(["document", "config_id"])
    multiple_configs = summary["config_id"].nunique() > 1
    labels = [
        (
            f"{textwrap.shorten(Path(row.document).stem, width=22, placeholder='...')}\n{row.config_id}"
            if multiple_configs
            else textwrap.shorten(Path(row.document).stem, width=22, placeholder="...")
        )
        for row in summary.itertuples(index=False)
    ]
    x = np.arange(len(summary))
    width = 0.36
    score_bars = ax.bar(
        x - width / 2,
        summary["score_stable_rate"],
        width,
        color="#4C78A8",
        label="Identical score",
    )
    citation_bars = ax.bar(
        x + width / 2,
        summary["citation_stable_rate"],
        width,
        color="#F58518",
        label="Identical citation set",
    )
    for bar, row in zip(score_bars, summary.itertuples(index=False), strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.015,
            f"{int(row.score_stable_count)}/{int(row.question_count)}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    for bar, row in zip(citation_bars, summary.itertuples(index=False), strict=True):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.015,
            f"{int(row.citation_stable_count)}/{int(row.question_count)}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    ax.set_xticks(x, labels, rotation=25, ha="right")
    ax.set_ylim(0, 1.12)
    ax.set(
        title="Exact stability across repeated runs",
        xlabel="Report",
        ylabel="Share of questions",
    )
    ax.yaxis.set_major_formatter(lambda value, _position: f"{value:.0%}")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="lower left")


def plot_answer_confusion_matrix(
    answers: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Plot one modal-answer confusion matrix per configuration."""
    pairs = build_pair_classifications(answers)
    if pairs.empty:
        return
    expert_order = ["Yes", "No"]
    osa_order = ["Yes", "No", "Unclear"]
    config_ids = sorted(pairs["config_id"].unique())
    fig, axes = plt.subplots(
        1,
        len(config_ids),
        figsize=(6 * len(config_ids), 4.8),
        squeeze=False,
        sharey=True,
        constrained_layout=True,
    )
    image = None
    for ax, config_id in zip(axes[0], config_ids, strict=True):
        selected = pairs[pairs["config_id"].eq(config_id)]
        counts = pd.crosstab(selected["expert_label"], selected["osa_label"]).reindex(
            index=expert_order,
            columns=osa_order,
            fill_value=0,
        )
        proportions = counts.div(counts.sum(axis=1), axis=0)
        image = ax.imshow(proportions, cmap="Blues", vmin=0, vmax=1)
        ax.set_xticks(range(len(osa_order)), osa_order)
        ax.set_yticks(range(len(expert_order)), expert_order)
        ax.set(
            xlabel="OSA answer",
            title=f"{config_id} ({len(selected)} labelled pairs)",
        )
        for row_index in range(len(expert_order)):
            for column_index in range(len(osa_order)):
                count = int(counts.iloc[row_index, column_index])
                proportion = proportions.iloc[row_index, column_index]
                color = "white" if proportion > 0.55 else "black"
                ax.text(
                    column_index,
                    row_index,
                    f"{count}\n({proportion:.0%})",
                    ha="center",
                    va="center",
                    color=color,
                    fontsize=11,
                )
    axes[0, 0].set_ylabel("ClimRetrieve expert answer")
    if image is not None:
        fig.colorbar(image, ax=axes.ravel().tolist(), label="Share within expert class")
    fig.suptitle("Answer confusion matrices by configuration")
    fig.savefig(output_dir / "answer_confusion_matrix.png", dpi=200)
    plt.close(fig)


def plot_answer_label_robustness(
    answers: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Compare categorical composition and stability across configurations."""
    working = answers.copy()
    working["answer_label"] = [
        normalize_answer_label(binary, answer)
        for binary, answer in zip(
            working["answer_yes_no"],
            working["answer"],
            strict=True,
        )
    ]
    label_order = ["Yes", "No", "Unclear", "Not disclosed", "Other"]
    composition = (
        pd.crosstab(
            working["config_id"],
            working["answer_label"],
            normalize="index",
        )
        .reindex(columns=label_order, fill_value=0)
        .sort_index()
    )
    summary = build_answer_robustness_summary(answers).sort_values("config_id")
    colors = {
        "Yes": "#4C78A8",
        "No": "#F58518",
        "Unclear": "#B279A2",
        "Not disclosed": "#E45756",
        "Other": "#9D9D9D",
    }
    fig, axes = plt.subplots(1, 2, figsize=(13, 5.3))
    bottom = np.zeros(len(composition))
    for label in label_order:
        values = composition[label].to_numpy()
        if not values.any():
            continue
        axes[0].bar(
            composition.index,
            values,
            bottom=bottom,
            label=label,
            color=colors[label],
        )
        bottom += values
    axes[0].set(
        title="A. Answer-label composition by configuration",
        xlabel="Configuration",
        ylabel="Share of model answers",
    )
    axes[0].yaxis.set_major_formatter(PercentFormatter(1))
    axes[0].legend(title="OSA answer")
    stability_metrics = [
        ("Answer\nlabel", "label_stability_rate"),
        ("Exact answer\ntext", "answer_text_stability_rate"),
        ("Answer\nscore", "score_stability_rate"),
        ("Citation\nset", "citation_set_stability_rate"),
    ]
    metric_labels = [label for label, _ in stability_metrics]
    x = np.arange(len(metric_labels))
    width = 0.8 / len(summary)
    for index, row in enumerate(summary.itertuples(index=False)):
        values = [getattr(row, column) for _, column in stability_metrics]
        axes[1].bar(
            x + index * width,
            values,
            width,
            label=row.config_id,
            alpha=0.85,
        )
    axes[1].set_xticks(
        x + width * (len(summary) - 1) / 2,
        metric_labels,
    )
    axes[1].set(
        title="B. Exact stability by configuration",
        xlabel="Output component",
        ylabel="Pairs with identical output",
        ylim=(0, 1.08),
    )
    axes[1].yaxis.set_major_formatter(PercentFormatter(1))
    axes[1].legend(title="Configuration")
    for ax in axes:
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle(
        "OSA Yes/No/Unclear robustness",
        fontsize=14,
        fontweight="bold",
    )
    fig.tight_layout()
    fig.savefig(output_dir / "answer_label_robustness.png", dpi=200)
    plt.close(fig)


def plot_answer_robustness_metrics_table(
    metrics: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Render all configuration-specific robustness counts in one table."""
    if metrics.empty:
        return
    cells = [
        [
            row.config_id,
            row.metric,
            f"{int(row.stable_pairs)}/{int(row.total_pairs)}",
            str(int(row.changed_pairs)),
            f"{row.stability_rate:.1%}",
        ]
        for row in metrics.sort_values(["config_id", "metric"]).itertuples(index=False)
    ]
    fig, ax = plt.subplots(figsize=(10.5, max(3.5, 0.38 * len(cells))))
    ax.axis("off")
    table = ax.table(
        cellText=cells,
        colLabels=[
            "Configuration",
            "Output component",
            "Stable pairs",
            "Changed pairs",
            "Stability rate",
        ],
        cellLoc="center",
        colLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.55)
    for column in range(5):
        table[(0, column)].set_facecolor("#4C78A8")
        table[(0, column)].set_text_props(color="white", weight="bold")
    for row in range(1, len(cells) + 1):
        table[(row, 1)].set_text_props(ha="left")
        if row % 2 == 0:
            for column in range(5):
                table[(row, column)].set_facecolor("#F2F2F2")
    ax.set_title(
        "OSA robustness metrics across repeated runs",
        fontsize=13,
        fontweight="bold",
        pad=12,
    )
    fig.tight_layout()
    fig.savefig(
        output_dir / "answer_robustness_metrics_table.png",
        dpi=200,
        bbox_inches="tight",
    )
    plt.close(fig)


def plot_all_evaluation_metrics_table(
    metrics: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Render one primary evaluation table per configuration."""
    if metrics.empty:
        return
    for config_id, selected in metrics.groupby("config_id", sort=True):
        cells = [
            [
                row.section,
                row.metric,
                f"{row.value:.1%}",
                str(int(row.n_pairs)),
                row.scope,
            ]
            for row in selected.itertuples(index=False)
        ]
        fig, ax = plt.subplots(figsize=(12, 10))
        ax.axis("off")
        table = ax.table(
            cellText=cells,
            colLabels=["Section", "Metric", "Value", "N", "Evaluation scope"],
            cellLoc="center",
            colLoc="center",
            colWidths=[0.15, 0.25, 0.1, 0.08, 0.32],
            loc="center",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(9.5)
        table.scale(1, 1.35)
        for column in range(5):
            table[(0, column)].set_facecolor("#355C7D")
            table[(0, column)].set_text_props(color="white", weight="bold")
        section_colors = {
            "Classification": "#EAF2F8",
            "Direct retrieval": "#FEF1E6",
            "Robustness": "#EAF5E7",
        }
        for row_index, row in enumerate(selected.itertuples(index=False), start=1):
            for column in range(5):
                table[(row_index, column)].set_facecolor(section_colors[row.section])
            table[(row_index, 0)].set_text_props(weight="bold", ha="left")
            table[(row_index, 1)].set_text_props(ha="left")
            table[(row_index, 4)].set_text_props(ha="left")
        ax.set_title(
            f"OSA evaluation metrics — {config_id}",
            fontsize=14,
            fontweight="bold",
            pad=14,
        )
        fig.tight_layout()
        safe_config = re.sub(r"[^A-Za-z0-9_-]+", "_", str(config_id)).strip("_")
        fig.savefig(
            output_dir / f"all_evaluation_metrics_table_{safe_config}.png",
            dpi=200,
            bbox_inches="tight",
        )
        plt.close(fig)


def plot_overall_performance_metrics(
    classification: pd.DataFrame,
    retrieval: pd.DataFrame | None,
    output_dir: Path,
) -> None:
    """Compare classification and retrieval metrics across configurations."""
    if classification.empty:
        return
    has_retrieval = retrieval is not None and not retrieval.empty
    fig, axes = plt.subplots(
        1,
        2 if has_retrieval else 1,
        figsize=(14 if has_retrieval else 7, 5.5),
        squeeze=False,
    )
    classification_metrics = [
        ("Accuracy", "accuracy"),
        ("Balanced\naccuracy", "balanced_accuracy"),
        ("Macro F1", "macro_f1"),
        ("Coverage", "coverage"),
    ]
    retrieval_metrics = [
        ("Precision", "precision"),
        ("Recall", "recall"),
        ("Hit", "hit_rate"),
        ("Complete\nhit", "complete_set_hit_rate"),
        ("nDCG", "ndcg"),
        ("MAP", "MAP"),
        ("MRR", "MRR"),
    ]
    panels = [
        (
            axes[0, 0],
            classification.sort_values("config_id"),
            classification_metrics,
            "A. Overall answer classification",
            False,
        )
    ]
    if has_retrieval and retrieval is not None:
        panels.append(
            (
                axes[0, 1],
                retrieval.sort_values("config_id"),
                retrieval_metrics,
                "B. Direct evidence retrieval at configured k",
                True,
            )
        )
    for ax, frame, metrics, title, include_cutoff in panels:
        x = np.arange(len(metrics))
        width = 0.8 / len(frame)
        colors = plt.cm.Set2(np.linspace(0, 1, len(frame)))
        for index, (row, color) in enumerate(zip(frame.itertuples(index=False), colors, strict=True)):
            values = [float(getattr(row, column)) for _, column in metrics]
            label = row.config_id
            if include_cutoff:
                label = f"{label} (@{int(row.k)})"
            ax.bar(
                x + index * width,
                values,
                width,
                label=label,
                color=color,
                alpha=0.9,
            )
        ax.set_xticks(
            x + width * (len(frame) - 1) / 2,
            [label for label, _ in metrics],
        )
        ax.set(
            title=title,
            ylabel="Rate",
            ylim=(0, 1.08),
        )
        ax.yaxis.set_major_formatter(PercentFormatter(1))
        ax.grid(axis="y", alpha=0.25)
        ax.tick_params(axis="x", labelrotation=15)
        ax.legend(title="Configuration")
    fig.suptitle("OSA evaluation summary by configuration", fontsize=14, fontweight="bold")
    fig.tight_layout()
    fig.savefig(output_dir / "overall_performance_metrics.png", dpi=200)
    plt.close(fig)


def plot_robustness_boxplots(
    answers: pd.DataFrame,
    citations: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Show score and citation stability distributions by configuration."""
    score_pairs = answers.groupby(["document", "question", "config_id"])["answer_score"].agg(["min", "max"]).reset_index()
    score_pairs["score_range"] = score_pairs["max"] - score_pairs["min"]
    config_ids = sorted(answers["config_id"].dropna().unique())
    score_values = [
        score_pairs.loc[score_pairs["config_id"].eq(config_id), "score_range"].dropna() for config_id in config_ids
    ]
    citation_values = [
        citations.loc[citations["config_id"].eq(config_id), "citation_jaccard"].dropna() for config_id in config_ids
    ]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.5))
    panels = [
        (
            axes[0],
            score_values,
            "#4C78A8",
            "A. Run-to-run score variation",
            "Score range within each question",
        ),
        (
            axes[1],
            citation_values,
            "#F58518",
            "B. Citation overlap across repeated runs",
            "Citation-set Jaccard",
        ),
    ]
    for ax, values, color, title, ylabel in panels:
        plot = ax.boxplot(
            values,
            tick_labels=config_ids,
            patch_artist=True,
            showfliers=False,
            medianprops={"color": "black"},
        )
        for box in plot["boxes"]:
            box.set_facecolor(color)
            box.set_alpha(0.35)
        for index, group_values in enumerate(values, start=1):
            x = np.linspace(index - 0.12, index + 0.12, len(group_values))
            ax.scatter(x, group_values, color=color, alpha=0.75, s=25)
        ax.set_xticks(range(1, len(config_ids) + 1), config_ids, rotation=15, ha="right")
        ax.set(title=title, xlabel="Configuration", ylabel=ylabel)
        ax.grid(axis="y", alpha=0.25)
    axes[1].set_ylim(-0.03, 1.05)
    fig.suptitle("Question-level OSA robustness distributions")
    fig.tight_layout()
    fig.savefig(output_dir / "paper_robustness_boxplots.png", dpi=200)
    plt.close(fig)


def _score_comparison_specs(metadata: pd.DataFrame) -> list[tuple[str, str, str]]:
    specs = []
    for chunk_size, group in metadata.groupby("chunk_size", sort=True):
        ordered = group.sort_values("top_k")
        if len(ordered) > 1:
            specs.append(
                (
                    f"Top-k effect\nk{int(ordered.iloc[-1]['top_k'])} - "
                    f"k{int(ordered.iloc[0]['top_k'])}\n({int(chunk_size)} tokens)",
                    str(ordered.iloc[0]["config_id"]),
                    str(ordered.iloc[-1]["config_id"]),
                )
            )
            break
    for top_k, group in metadata.groupby("top_k", sort=True):
        ordered = group.sort_values("chunk_size")
        if len(ordered) > 1:
            specs.append(
                (
                    f"Chunk-size effect\n{int(ordered.iloc[-1]['chunk_size'])} - "
                    f"{int(ordered.iloc[0]['chunk_size'])}\n(k={int(top_k)})",
                    str(ordered.iloc[0]["config_id"]),
                    str(ordered.iloc[-1]["config_id"]),
                )
            )
            break
    return specs


def plot_answer_scores_by_configuration(
    answers: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Compare pair-level mean scores and paired configuration deltas."""
    metadata = (
        answers[["config_id", "chunk_size", "top_k"]].drop_duplicates().sort_values(["chunk_size", "top_k", "config_id"])
    )
    pair_means = (
        answers.groupby(["document", "question", "config_id"])["answer_score"].mean().rename("mean_score").reset_index()
    )
    config_ids = metadata["config_id"].astype(str).tolist()
    score_values = [pair_means.loc[pair_means["config_id"].eq(config_id), "mean_score"].dropna() for config_id in config_ids]
    wide = pair_means.pivot(
        index=["document", "question"],
        columns="config_id",
        values="mean_score",
    )
    comparisons = _score_comparison_specs(metadata)
    fig, axes = plt.subplots(
        1,
        2 if comparisons else 1,
        figsize=(14 if comparisons else 7, 5.5),
        squeeze=False,
    )
    score_plot = axes[0, 0].boxplot(
        score_values,
        tick_labels=config_ids,
        patch_artist=True,
        showfliers=False,
        medianprops={"color": "black"},
    )
    colors = plt.cm.Set2(np.linspace(0, 1, len(config_ids)))
    for position, (box, values, color) in enumerate(
        zip(score_plot["boxes"], score_values, colors, strict=True),
        start=1,
    ):
        box.set_facecolor(color)
        box.set_alpha(0.7)
        offsets = np.linspace(-0.12, 0.12, len(values))
        axes[0, 0].scatter(
            position + offsets,
            values,
            color=color,
            edgecolor="black",
            linewidth=0.25,
            alpha=0.65,
            s=22,
        )
    axes[0, 0].set(
        title="A. Mean answer scores by configuration",
        xlabel="Configuration",
        ylabel="Three-run mean OSA score per report-question pair",
    )
    axes[0, 0].grid(axis="y", alpha=0.25)

    if comparisons:
        delta_values = [(wide[high_config] - wide[low_config]).dropna() for _, low_config, high_config in comparisons]
        delta_plot = axes[0, 1].boxplot(
            delta_values,
            tick_labels=[label for label, _, _ in comparisons],
            patch_artist=True,
            showfliers=False,
            medianprops={"color": "black"},
        )
        for position, (box, values, color) in enumerate(
            zip(
                delta_plot["boxes"],
                delta_values,
                plt.cm.Set2(np.linspace(0, 1, len(delta_values))),
                strict=True,
            ),
            start=1,
        ):
            box.set_facecolor(color)
            box.set_alpha(0.7)
            offsets = np.linspace(-0.12, 0.12, len(values))
            axes[0, 1].scatter(
                position + offsets,
                values,
                color=color,
                edgecolor="black",
                linewidth=0.25,
                alpha=0.65,
                s=22,
            )
        axes[0, 1].axhline(0, color="black", linewidth=0.9)
        axes[0, 1].set(
            title="B. Paired score changes between configurations",
            xlabel="Controlled ablation",
            ylabel="Mean-score difference per report-question pair",
        )
        axes[0, 1].grid(axis="y", alpha=0.25)
    fig.suptitle("OSA answer-score sensitivity to retrieval configuration")
    fig.tight_layout()
    fig.savefig(output_dir / "answer_score_by_configuration.png", dpi=200)
    plt.close(fig)


def plot_score_quantile_intervals_by_run(
    answers: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Compare run score distributions within each configuration."""
    config_ids = sorted(answers["config_id"].dropna().unique())
    run_ids = sorted(answers["run_id"].dropna().unique())
    colors = plt.cm.Set2(np.linspace(0, 1, len(run_ids)))
    fig, axes = plt.subplots(
        1,
        len(config_ids),
        figsize=(6 * len(config_ids), 5.5),
        squeeze=False,
        sharey=True,
    )
    for ax, config_id in zip(axes[0], config_ids, strict=True):
        values = [
            answers.loc[
                answers["config_id"].eq(config_id) & answers["run_id"].eq(run_id),
                "answer_score",
            ].dropna()
            for run_id in run_ids
        ]
        statistics = [
            {
                "med": float(np.median(group_values)),
                "q1": float(np.quantile(group_values, 0.1)),
                "q3": float(np.quantile(group_values, 0.9)),
                "whislo": float(np.min(group_values)),
                "whishi": float(np.max(group_values)),
                "fliers": [],
            }
            for group_values in values
        ]
        plot = ax.bxp(
            statistics,
            positions=np.arange(len(run_ids)),
            widths=0.5,
            patch_artist=True,
            showfliers=False,
            medianprops={"color": "black"},
        )
        for box, color in zip(plot["boxes"], colors, strict=True):
            box.set_facecolor(color)
            box.set_alpha(0.75)
        for position, group_values, color in zip(
            np.arange(len(run_ids)),
            values,
            colors,
            strict=True,
        ):
            point_offsets = np.linspace(-0.12, 0.12, len(group_values))
            ax.scatter(
                position + point_offsets,
                group_values,
                color=color,
                edgecolor="black",
                linewidth=0.25,
                alpha=0.7,
                s=20,
                zorder=3,
            )
        ax.set_xticks(
            range(len(run_ids)),
            [f"Run {int(run_id)}" for run_id in run_ids],
        )
        ax.set(
            title=config_id,
            xlabel="Repeated analysis",
            ylabel="OSA answer score",
        )
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("OSA score distributions by configuration: central 80% intervals")
    fig.tight_layout()
    fig.savefig(output_dir / "answer_score_quantile_interval_plot.png", dpi=200)
    plt.close(fig)


def build_pairwise_citation_overlap(answers: pd.DataFrame) -> pd.DataFrame:
    """Calculate citation-set overlap for each pair of repeated runs."""
    rows = []
    group_columns = ["document", "question", "config_id"]
    for key, group in answers.groupby(group_columns, dropna=False):
        run_sets = [
            (row.run_id, split_ids(row.cited_chunk_ids))
            for row in group.sort_values("run_id")[["run_id", "cited_chunk_ids"]].itertuples(index=False)
        ]
        for (run_a, ids_a), (run_b, ids_b) in combinations(run_sets, 2):
            union = ids_a | ids_b
            jaccard = len(ids_a & ids_b) / len(union) if union else 1.0
            rows.append(
                {
                    **dict(zip(group_columns, key, strict=True)),
                    "run_pair": f"{int(run_a)}-{int(run_b)}",
                    "citation_jaccard": jaccard,
                    "citation_change": 1 - jaccard,
                    "changed_chunk_count": len(ids_a ^ ids_b),
                }
            )
    return pd.DataFrame(rows)


def plot_citation_overlap_by_run_pair(
    answers: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Plot citation change by run pair within each configuration."""
    overlaps = build_pairwise_citation_overlap(answers)
    if overlaps.empty:
        return
    config_ids = sorted(overlaps["config_id"].dropna().unique())
    run_pairs = sorted(overlaps["run_pair"].dropna().unique())
    colors = plt.cm.Set2(np.linspace(0, 1, len(run_pairs)))
    fig, axes = plt.subplots(
        1,
        len(config_ids),
        figsize=(6 * len(config_ids), 5.5),
        squeeze=False,
        sharey=True,
    )
    for ax, config_id in zip(axes[0], config_ids, strict=True):
        values = [
            overlaps.loc[
                overlaps["config_id"].eq(config_id) & overlaps["run_pair"].eq(run_pair),
                "citation_change",
            ].dropna()
            for run_pair in run_pairs
        ]
        plot = ax.boxplot(
            values,
            positions=np.arange(len(run_pairs)),
            widths=0.5,
            patch_artist=True,
            showfliers=False,
            medianprops={"color": "black"},
        )
        for box, color in zip(plot["boxes"], colors, strict=True):
            box.set_facecolor(color)
            box.set_alpha(0.75)
        for position, group_values, color in zip(
            np.arange(len(run_pairs)),
            values,
            colors,
            strict=True,
        ):
            point_offsets = np.linspace(-0.12, 0.12, len(group_values))
            ax.scatter(
                position + point_offsets,
                group_values,
                color=color,
                edgecolor="black",
                linewidth=0.25,
                alpha=0.7,
                s=20,
                zorder=3,
            )
        ax.set_xticks(
            range(len(run_pairs)),
            [f"Runs {run_pair}" for run_pair in run_pairs],
        )
        ax.set_ylim(-0.03, 1.05)
        ax.set(
            title=config_id,
            xlabel="Run comparison",
            ylabel="Citation change (1 - Jaccard)",
        )
        ax.yaxis.set_major_formatter(lambda value, _position: f"{value:.0%}")
        ax.grid(axis="y", alpha=0.25)
    fig.suptitle("Citation chunk-set change by configuration")
    fig.tight_layout()
    fig.savefig(output_dir / "citation_chunk_change_by_run_pair.png", dpi=200)
    plt.close(fig)


def plot_paper_robustness_figure(
    answers: pd.DataFrame,
    citations: pd.DataFrame,
    paired: pd.DataFrame,
    output_dir: Path,
) -> None:
    """Render the proposed score, top-k, and citation robustness figure."""
    if paired.empty:
        fig, ax = plt.subplots(figsize=(11, 5.5))
        _plot_exact_stability_rates(ax, answers, citations)
        fig.suptitle("OSA score and citation stability")
        fig.tight_layout()
        fig.savefig(output_dir / "paper_robustness_figure.png", dpi=200)
        plt.close(fig)
        return
    fig, axes = plt.subplots(1, 3, figsize=(19, 6), gridspec_kw={"width_ratios": [1.25, 0.85, 1.4]})
    _plot_score_ranges(axes[0], answers)
    _plot_topk_panel(axes[1], paired, answers)
    _plot_citation_distributions(axes[2], answers, citations, panel_label="C")
    fig.suptitle("OSA robustness: score, top-k sensitivity, and citation selection")
    fig.tight_layout()
    fig.savefig(output_dir / "paper_robustness_figure.png", dpi=200)
    plt.close(fig)


def load_labels(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, low_memory=False)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported labels format: {path.suffix}")


def build_benchmark_manifest_frames(
    labels: pd.DataFrame,
    question_set_path: Path,
) -> dict[str, pd.DataFrame]:
    """Build and validate the configured report-by-question benchmark matrix."""
    with question_set_path.open() as handle:
        manifest = yaml.safe_load(handle)
    reports = pd.DataFrame({"document": manifest.get("documents", [])})
    questions = pd.DataFrame(
        [{"osa_question_id": item["id"], "question": item["text"]} for item in manifest.get("questions", [])]
    )
    expected = reports.merge(questions, how="cross")
    normalized = normalize_climretrieve_columns(labels)
    normalized["has_human_label"] = (
        normalized.get("answer", pd.Series(index=normalized.index)).fillna("").astype(str).str.strip().ne("")
    )
    source_pairs = normalized.groupby(["document", "question"], as_index=False)["has_human_label"].any()
    coverage = expected.merge(
        source_pairs,
        on=["document", "question"],
        how="left",
    )
    coverage["has_human_label"] = coverage["has_human_label"].eq(True)
    return {
        "benchmark_reports": reports,
        "benchmark_questions": questions,
        "benchmark_pair_coverage": coverage,
    }


def build_direct_retrieval_rows(
    answers: pd.DataFrame,
    chunks: pd.DataFrame,
    ground_truth: pd.DataFrame,
) -> pd.DataFrame:
    """Select one deterministic retrieval per pair and disable split matching."""
    first_runs = answers.sort_values("run_id").drop_duplicates(["document", "question", "config_id"])["run_uid"]
    rows = chunks[chunks["run_uid"].isin(set(first_runs))].copy()
    rows["query_id"] = [
        generate_query_id(document, question)
        for document, question in zip(
            rows["document"],
            rows["question"],
            strict=True,
        )
    ]
    valid_query_ids = set(ground_truth["query_id"])
    rows = rows[rows["query_id"].isin(valid_query_ids)].copy()
    rows["retrieved_chunk_id"] = rows["chunk_text"].map(generate_chunk_id)
    rows["position"] = rows["retrieval_rank"].astype(int)
    rows["chunk_order"] = np.nan
    rows["match_relation"] = "not_evaluated"
    columns = [
        "config_id",
        "chunk_size",
        "top_k",
        "query_id",
        "document",
        "question",
        "retrieved_chunk_id",
        "position",
        "chunk_order",
        "similarity_score",
        "chunk_text",
        "match_relation",
    ]
    if "chunk_overlap" in answers:
        overlap = answers[["run_uid", "chunk_overlap"]].drop_duplicates("run_uid")
        rows = rows.merge(overlap, on="run_uid", how="left")
        columns.insert(2, "chunk_overlap")
    return rows[columns].sort_values(["document", "question", "config_id", "position"]).reset_index(drop=True)


def direct_ranked_query_metrics(
    retrieval_rows: pd.DataFrame,
    ground_truth: pd.DataFrame,
    matches: pd.DataFrame,
) -> pd.DataFrame:
    """Rank metrics with each annotated evidence span credited at most once."""
    config_columns = [column for column in ("config_id", "chunk_size", "chunk_overlap", "top_k") if column in retrieval_rows]
    rows = []
    group_columns = [*config_columns, "query_id", "document", "question"]
    for key, group in retrieval_rows.groupby(group_columns, dropna=False):
        dimensions = dict(zip(group_columns, key, strict=True))
        query_gt = ground_truth[ground_truth["query_id"] == dimensions["query_id"]]
        query_matches = matches[matches["query_id"] == dimensions["query_id"]]
        for column in config_columns:
            query_matches = query_matches[query_matches[column] == dimensions[column]]
        credited_ids: set[str] = set()
        ranked_gains = []
        for result in group.sort_values("position").itertuples(index=False):
            candidates = query_matches[
                query_matches["retrieval_position"].eq(result.position)
                & ~query_matches["ground_truth_chunk_id"].astype(str).isin(credited_ids)
            ]
            if candidates.empty:
                ranked_gains.append(0.0)
                continue
            best = candidates.sort_values(
                "relevance_grade",
                ascending=False,
            ).iloc[0]
            credited_ids.add(str(best["ground_truth_chunk_id"]))
            ranked_gains.append(float(best["relevance_grade"]))
        relevant_ids = set(query_gt.loc[query_gt["score"].ge(2), "chunk_id"].astype(str))
        matched_relevant_ids = set(
            query_matches.loc[
                query_matches["relevance_grade"].ge(2),
                "ground_truth_chunk_id",
            ].astype(str)
        )
        binary = [int(gain >= 2) for gain in ranked_gains]
        k = int(dimensions["top_k"])
        relevant_at_k = sum(binary[:k])
        precision = relevant_at_k / k
        recall = len(matched_relevant_ids) / len(relevant_ids) if relevant_ids else 0.0
        ideal_gains = sorted(
            query_gt["score"].astype(float),
            reverse=True,
        )
        dcg = sum(gain / np.log2(rank + 1) for rank, gain in enumerate(ranked_gains[:k], start=1))
        idcg = sum(gain / np.log2(rank + 1) for rank, gain in enumerate(ideal_gains[:k], start=1))
        hits = 0
        average_precision = 0.0
        for rank, relevant in enumerate(binary[:k], start=1):
            if relevant:
                hits += 1
                average_precision += hits / rank
        average_precision = average_precision / len(relevant_ids) if relevant_ids else 0.0
        reciprocal_rank = next(
            (1.0 / rank for rank, relevant in enumerate(binary, start=1) if relevant),
            0.0,
        )
        rows.append(
            {
                **dimensions,
                "k": k,
                "precision": precision,
                "recall": recall,
                "f1": (2 * precision * recall / (precision + recall) if precision + recall else 0.0),
                "ndcg": dcg / idcg if idcg else 0.0,
                "hit": bool(matched_relevant_ids),
                "complete_set_hit": bool(relevant_ids and matched_relevant_ids == relevant_ids),
                "average_precision": average_precision,
                "reciprocal_rank": reciprocal_rank,
            }
        )
    return pd.DataFrame(rows)


def calculate_direct_retrieval_metrics(
    answers: pd.DataFrame,
    chunks: pd.DataFrame,
    labels: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Calculate cutoff metrics using direct text matches to annotated evidence."""
    ground_truth = build_ground_truth_rows(
        labels,
        answers["document"].dropna().unique(),
    )
    query_ids = {
        generate_query_id(document, question)
        for document, question in answers[["document", "question"]].drop_duplicates().itertuples(index=False)
    }
    ground_truth = ground_truth[ground_truth["query_id"].isin(query_ids)].reset_index(drop=True)
    retrieval_rows = build_direct_retrieval_rows(
        answers,
        chunks,
        ground_truth,
    )
    matches = build_retrieval_match_table(retrieval_rows, ground_truth)
    match_metrics = query_match_metrics(
        retrieval_rows,
        ground_truth,
        matches=matches,
    )
    ranking_metrics = direct_ranked_query_metrics(
        retrieval_rows,
        ground_truth,
        matches,
    )
    return {
        "direct_ground_truth": ground_truth,
        "direct_retrieval_rows": retrieval_rows,
        "direct_retrieval_matches": matches,
        "direct_query_match_metrics": match_metrics,
        "direct_match_summary": summarize_query_match_metrics(match_metrics),
        "direct_query_ranking_metrics": ranking_metrics,
        "direct_ranking_summary": summarize_ranked_query_metrics(ranking_metrics),
    }


def write_outputs(
    output_dir: Path,
    frames: dict[str, pd.DataFrame],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, frame in frames.items():
        frame.to_csv(output_dir / f"{name}.csv", index=False)


def analyze(
    input_csv: Path,
    output_dir: Path,
    labels_path: Path | None = None,
    benchmark_question_set: Path = DEFAULT_BENCHMARK_QUESTION_SET,
) -> dict[str, pd.DataFrame]:
    raw = pd.read_csv(input_csv, low_memory=False)
    answers, chunks = reconstruct_tables(raw)
    question_summary = build_question_summary(answers)
    retrieved = retrieved_chunk_consistency(answers)
    citations = citation_consistency(answers)
    topk_comparison = build_topk_comparison(answers)
    containment = build_topk_containment(answers)
    checks = run_sanity_checks(raw, answers, chunks)
    pair_classifications = build_pair_classifications(answers)
    frames = {
        "answer_runs": answers,
        "chunk_rows": chunks,
        "question_configuration_summary": question_summary,
        "pair_classifications": pair_classifications,
        "answer_robustness_summary": build_answer_robustness_summary(answers),
        "answer_robustness_metrics": build_answer_robustness_metrics(answers),
        "overall_classification_metrics": (build_overall_classification_metrics(answers)),
        "retrieved_chunk_consistency": retrieved,
        "citation_consistency": citations,
        "topk_comparison": topk_comparison,
        "topk_containment": containment,
        "sanity_checks": checks,
    }
    if labels_path is not None:
        labels = load_labels(labels_path)
        frames.update(
            calculate_direct_retrieval_metrics(
                answers,
                chunks,
                labels,
            )
        )
        frames.update(
            build_benchmark_manifest_frames(
                labels,
                benchmark_question_set,
            )
        )
    frames["all_evaluation_metrics"] = build_all_evaluation_metrics(
        frames["overall_classification_metrics"],
        frames["answer_robustness_summary"],
        frames.get("direct_ranking_summary"),
    )
    write_outputs(output_dir, frames)
    plot_configuration_heatmaps(
        answers,
        question_summary,
        retrieved,
        citations,
        output_dir,
    )
    plot_score_stability(answers, output_dir)
    plot_topk_sensitivity(topk_comparison, output_dir)
    plot_paper_robustness_figure(
        answers,
        citations,
        topk_comparison,
        output_dir,
    )
    plot_answer_confusion_matrix(answers, output_dir)
    plot_answer_label_robustness(answers, output_dir)
    plot_answer_robustness_metrics_table(
        frames["answer_robustness_metrics"],
        output_dir,
    )
    plot_all_evaluation_metrics_table(
        frames["all_evaluation_metrics"],
        output_dir,
    )
    plot_overall_performance_metrics(
        frames["overall_classification_metrics"],
        frames.get("direct_ranking_summary"),
        output_dir,
    )
    plot_robustness_boxplots(answers, citations, output_dir)
    plot_answer_scores_by_configuration(answers, output_dir)
    plot_score_quantile_intervals_by_run(answers, output_dir)
    plot_citation_overlap_by_run_pair(answers, output_dir)
    return frames


def main() -> None:
    args = parse_args()
    frames = analyze(
        args.input_csv,
        args.output_dir,
        args.labels,
        args.benchmark_question_set,
    )
    answers = frames["answer_runs"]
    checks = frames["sanity_checks"]
    print(
        f"Analyzed {len(answers)} runs: "
        f"{answers['document'].nunique()} documents, "
        f"{answers['question'].nunique()} questions, "
        f"{answers['config_id'].nunique()} configurations."
    )
    failed = checks.loc[~checks["passed"], "check"].tolist()
    print(f"Sanity checks: {len(checks) - len(failed)}/{len(checks)} passed.")
    if failed:
        print("Failed checks:", ", ".join(failed))
    if "direct_ranking_summary" in frames:
        print(
            "Direct retrieval metrics:",
            len(frames["direct_query_ranking_metrics"]),
            "annotated query-configurations.",
        )
        covered = frames["benchmark_pair_coverage"]["has_human_label"].sum()
        expected = len(frames["benchmark_pair_coverage"])
        print(f"Benchmark matrix: {covered}/{expected} pairs have human labels.")
    print(f"Wrote analysis to {args.output_dir}")


if __name__ == "__main__":
    main()
