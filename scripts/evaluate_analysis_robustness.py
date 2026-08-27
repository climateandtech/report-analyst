#!/usr/bin/env python3
"""Run OSA analysis repeatedly and persist robustness data after every run."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yaml
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from report_analyst.core.analyzer import DocumentAnalyzer
from report_analyst.core.benchmark.library_eval import (
    build_analysis_run_rows,
    build_climretrieve_answer_rows,
    build_ground_truth_rows,
    citation_consistency,
    citation_subset_rate,
    combine_analysis_run_rows,
    filter_core_questions,
    match_document_to_pdf,
    match_question,
    normalize_climretrieve_columns,
    pairwise_chunk_selection,
    retrieved_chunk_consistency,
    score_distribution_summary,
    score_stability,
    select_labelled_reports,
    topk_retrieved_containment,
    topk_score_delta,
    yes_no_answer_comparison,
)
from report_analyst.core.question_loader import get_question_loader

CHECKPOINT_FILES = (
    "all_results.csv",
    "analysis_runs.csv",
    "chunk_scores.csv",
    "evaluation_manifest.json",
    "raw_analysis_runs.jsonl",
)
QUESTION_SET_DIRECTORY = Path(__file__).parent.parent / "report_analyst" / "questionsets"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, required=True, help="ClimRetrieve labels (.csv or .xlsx)")
    parser.add_argument("--reports-dir", type=Path, required=True, help="Directory containing labelled PDFs")
    parser.add_argument("--output-dir", type=Path, default=Path("evaluation_output"))
    parser.add_argument("--runs", type=int, default=3, help="Independent LLM runs per report/question/config")
    parser.add_argument("--top-k", type=int, nargs="+", default=[5, 10])
    parser.add_argument("--reports", type=int, default=10, help="Maximum matched reports")
    parser.add_argument("--questions", type=int, default=16, help="Maximum mapped questions")
    parser.add_argument("--question-set", default="climretrieve")
    parser.add_argument("--chunk-size", type=int, default=500)
    parser.add_argument(
        "--chunk-sizes",
        type=int,
        nargs="+",
        help="Optional chunk-size experiment; overrides --chunk-size",
    )
    parser.add_argument("--chunk-overlap", type=int, default=50)
    parser.add_argument("--model", help="Optional LLM model override")
    parser.add_argument("--individual-chunk-calls", action="store_true", help="Score chunks with one LLM call each")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing evaluation")
    return parser.parse_args()


def load_labels(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    raise ValueError(f"Unsupported labels format: {path.suffix}")


def map_questions(
    labels: pd.DataFrame,
    question_set: str,
    limit: int | None,
) -> pd.DataFrame:
    osa_questions = get_question_loader().get_questions(question_set)
    clim_questions = sorted(labels["question"].dropna().unique())
    rows = []
    for question_id, payload in osa_questions.items():
        clim_question = match_question(payload["text"], clim_questions)
        if clim_question:
            rows.append(
                {
                    "osa_question_id": question_id,
                    "osa_question_number": int(str(question_id).rsplit("_", 1)[-1]),
                    "osa_text": payload["text"],
                    "climretrieve_question": clim_question,
                }
            )
    mapped = pd.DataFrame(rows).drop_duplicates("climretrieve_question")
    return mapped.head(limit) if limit is not None else mapped


def load_configured_documents(question_set: str) -> list[str]:
    """Read an optional authoritative document list from a question set."""
    path = QUESTION_SET_DIRECTORY / f"{question_set}_questions.yaml"
    if not path.exists():
        return []
    with path.open() as handle:
        config = yaml.safe_load(handle)
    documents = config.get("documents", [])
    if len(documents) != len(set(documents)):
        raise ValueError(f"Duplicate documents in {path}")
    return documents


def select_configured_reports(
    labels: pd.DataFrame,
    pdf_filenames: list[str],
    documents: list[str],
) -> pd.DataFrame:
    """Resolve every configured document or fail before evaluation starts."""
    normalized = filter_core_questions(normalize_climretrieve_columns(labels))
    counts = normalized.groupby("document").size().to_dict()
    missing_labels = [document for document in documents if document not in counts]
    rows = []
    missing_pdfs = []
    for document in documents:
        pdf_filename = match_document_to_pdf(document, pdf_filenames)
        if pdf_filename is None:
            missing_pdfs.append(document)
            continue
        rows.append(
            {
                "document": document,
                "pdf_filename": pdf_filename,
                "n_labels": int(counts.get(document, 0)),
                "configured": True,
            }
        )
    errors = []
    if missing_labels:
        errors.append("missing from ClimRetrieve labels: " + ", ".join(missing_labels))
    if missing_pdfs:
        errors.append("missing PDFs: " + ", ".join(missing_pdfs))
    if errors:
        raise RuntimeError("Configured benchmark reports are incomplete; " + "; ".join(errors))
    return pd.DataFrame(rows)


def validate_complete_matrix(
    labels: pd.DataFrame,
    reports: pd.DataFrame,
    questions: pd.DataFrame,
) -> None:
    """Require a human-labelled row for every configured report/question."""
    available = set(labels[["document", "question"]].drop_duplicates().itertuples(index=False, name=None))
    expected = {(document, question) for document in reports["document"] for question in questions["climretrieve_question"]}
    missing = sorted(expected - available)
    if missing:
        preview = ", ".join(f"{document} / {question}" for document, question in missing[:3])
        suffix = f" (+{len(missing) - 3} more)" if len(missing) > 3 else ""
        raise RuntimeError(f"Configured benchmark matrix is missing {len(missing)} human-labelled pairs: {preview}{suffix}")


def prepare_output(directory: Path, overwrite: bool) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    existing = [directory / name for name in CHECKPOINT_FILES if (directory / name).exists()]
    if existing and not overwrite:
        names = ", ".join(path.name for path in existing)
        raise FileExistsError(f"Evaluation output already exists ({names}); pass --overwrite")
    for path in existing:
        path.unlink()


def _json_default(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, Path):
        return str(value)
    raise TypeError(f"Cannot serialize {type(value).__name__}")


def append_frame(path: Path, frame: pd.DataFrame) -> None:
    """Append one checkpoint frame, writing its header only once."""
    frame.to_csv(path, mode="a", header=not path.exists(), index=False)


def checkpoint_run(
    output_dir: Path,
    result: dict[str, Any],
    ground_truth: pd.DataFrame,
    context: dict[str, Any],
) -> None:
    """Persist raw and flattened data before the next run can overwrite the DB."""
    raw_record = {**context, "result": result}
    with (output_dir / "raw_analysis_runs.jsonl").open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(raw_record, default=_json_default) + "\n")

    answer_row, chunk_rows = build_analysis_run_rows(result, ground_truth, context)
    append_frame(output_dir / "analysis_runs.csv", pd.DataFrame([answer_row]))
    if chunk_rows:
        append_frame(output_dir / "chunk_scores.csv", pd.DataFrame(chunk_rows))
    combined_rows = combine_analysis_run_rows(answer_row, chunk_rows)
    append_frame(output_dir / "all_results.csv", pd.DataFrame(combined_rows))


async def collect_result(
    analyzer: DocumentAnalyzer,
    pdf_path: Path,
    question_number: int,
    *,
    individual_chunk_calls: bool,
) -> dict[str, Any]:
    async for item in analyzer.process_document(
        file_path=str(pdf_path),
        selected_questions=[question_number],
        use_llm_scoring=True,
        single_call=not individual_chunk_calls,
        force_recompute=True,
    ):
        if "error" in item:
            raise RuntimeError(item["error"])
        if "result" in item:
            result = item["result"]
            gaps = {str(gap).lower() for gap in result.get("GAPS") or []}
            if "error during analysis" in gaps or str(result.get("ANSWER", "")).startswith("Error analyzing document:"):
                raise RuntimeError(str(result.get("ANSWER") or result.get("GAPS")))
            return result
    raise RuntimeError(f"No analysis result for {pdf_path.name}, question {question_number}")


async def run_evaluation(args: argparse.Namespace) -> None:
    load_dotenv()
    prepare_output(args.output_dir, args.overwrite)
    evaluation_id = uuid.uuid4().hex
    manifest = {**vars(args), "evaluation_id": evaluation_id}
    (args.output_dir / "evaluation_manifest.json").write_text(
        json.dumps(manifest, indent=2, default=_json_default),
        encoding="utf-8",
    )
    raw_labels = load_labels(args.labels)
    labels = filter_core_questions(normalize_climretrieve_columns(raw_labels))
    pdf_names = sorted(path.name for path in args.reports_dir.glob("*.pdf"))
    configured_documents = load_configured_documents(args.question_set)
    reports = (
        select_configured_reports(
            raw_labels,
            pdf_names,
            configured_documents,
        )
        if configured_documents
        else select_labelled_reports(raw_labels, pdf_names, n=args.reports)
    )
    questions = map_questions(
        labels,
        args.question_set,
        None if configured_documents else args.questions,
    )
    if reports.empty:
        raise RuntimeError("No labelled reports matched PDFs in --reports-dir")
    if questions.empty:
        raise RuntimeError(f"No {args.question_set} questions matched ClimRetrieve labels")
    if configured_documents:
        validate_complete_matrix(labels, reports, questions)

    reports.to_csv(args.output_dir / "selected_reports.csv", index=False)
    questions.to_csv(args.output_dir / "question_map.csv", index=False)
    ground_truth = build_ground_truth_rows(raw_labels, reports["document"].tolist())
    ground_truth = ground_truth[ground_truth["question"].isin(set(questions["climretrieve_question"]))]
    ground_truth.to_csv(args.output_dir / "climretrieve_ground_truth.csv", index=False)
    expert_answers = build_climretrieve_answer_rows(
        raw_labels,
        reports["document"].tolist(),
        questions["climretrieve_question"].tolist(),
    )
    expert_answers.to_csv(args.output_dir / "climretrieve_answers.csv", index=False)
    expert_lookup = {(row.document, row.question): row for row in expert_answers.itertuples(index=False)}

    DocumentAnalyzer.reset_instance()
    analyzer = DocumentAnalyzer()
    analyzer.update_question_set(args.question_set)
    analyzer.use_cache = False
    if args.model:
        analyzer.update_llm_model(args.model)
    if analyzer.llm is None:
        raise RuntimeError("No LLM configured; set OPENAI_API_KEY or GOOGLE_API_KEY")

    chunk_sizes = args.chunk_sizes or [args.chunk_size]
    total = len(reports) * len(questions) * len(args.top_k) * len(chunk_sizes) * args.runs
    completed = 0
    for chunk_size in chunk_sizes:
        for top_k in args.top_k:
            config_id = f"cs{chunk_size}_k{top_k}"
            analyzer.update_parameters(chunk_size, args.chunk_overlap, top_k)
            for _, report in reports.iterrows():
                pdf_path = args.reports_dir / report["pdf_filename"]
                for _, question in questions.iterrows():
                    expert = expert_lookup.get((report["document"], question["climretrieve_question"]))
                    gt_rows = ground_truth[
                        (ground_truth["document"] == report["document"])
                        & (ground_truth["question"] == question["climretrieve_question"])
                    ]
                    for run_id in range(1, args.runs + 1):
                        result = await collect_result(
                            analyzer,
                            pdf_path,
                            int(question["osa_question_number"]),
                            individual_chunk_calls=args.individual_chunk_calls,
                        )
                        context = {
                            "evaluation_id": evaluation_id,
                            "document": report["document"],
                            "pdf_filename": report["pdf_filename"],
                            "question": question["climretrieve_question"],
                            "osa_question_id": question["osa_question_id"],
                            "config_id": config_id,
                            "top_k": top_k,
                            "chunk_size": chunk_size,
                            "chunk_overlap": args.chunk_overlap,
                            "model": analyzer.default_model,
                            "run_id": run_id,
                            "expert_answer": getattr(expert, "expert_answer", None),
                            "expert_yes_no": getattr(expert, "expert_yes_no", None),
                        }
                        checkpoint_run(args.output_dir, result, gt_rows, context)
                        completed += 1
                        print(
                            f"[{completed}/{total}] saved {pdf_path.name} "
                            f"{question['osa_question_id']} {config_id} run={run_id}"
                        )

    summarize_evaluation(args.output_dir, args.top_k, chunk_sizes)


def boxplot(frame: pd.DataFrame, value: str, output: Path, ylabel: str) -> None:
    groups = [(name, group[value].dropna()) for name, group in frame.groupby("config_id")]
    groups = [(name, values) for name, values in groups if not values.empty]
    if not groups:
        return
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.boxplot([values for _, values in groups], tick_labels=[name for name, _ in groups])
    ax.set_xlabel("Configuration")
    ax.set_ylabel(ylabel)
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def _write_factor_deltas(
    output_dir: Path,
    stability: pd.DataFrame,
    runs: pd.DataFrame,
    top_k_values: list[int],
    chunk_size_values: list[int],
) -> None:
    if len(top_k_values) >= 2:
        low_k, high_k = top_k_values[:2]
        score_frames = []
        containment_frames = []
        for chunk_size in chunk_size_values:
            low, high = f"cs{chunk_size}_k{low_k}", f"cs{chunk_size}_k{high_k}"
            score_frames.append(topk_score_delta(stability, low, high).assign(chunk_size=chunk_size))
            containment_frames.append(topk_retrieved_containment(runs, low, high).assign(chunk_size=chunk_size))
        pd.concat(score_frames, ignore_index=True).to_csv(output_dir / "topk_answer_score_delta.csv", index=False)
        pd.concat(containment_frames, ignore_index=True).to_csv(output_dir / "topk_retrieved_containment.csv", index=False)

    if len(chunk_size_values) >= 2:
        low_size, high_size = chunk_size_values[:2]
        frames = []
        for top_k in top_k_values:
            low, high = f"cs{low_size}_k{top_k}", f"cs{high_size}_k{top_k}"
            frames.append(topk_score_delta(stability, low, high).assign(top_k=top_k))
        pd.concat(frames, ignore_index=True).to_csv(output_dir / "chunk_size_answer_score_delta.csv", index=False)


def summarize_evaluation(
    output_dir: Path,
    top_k_values: list[int],
    chunk_size_values: list[int] | None = None,
) -> None:
    runs = pd.read_csv(output_dir / "analysis_runs.csv")
    chunks = pd.read_csv(output_dir / "chunk_scores.csv")
    chunk_size_values = chunk_size_values or sorted(runs["chunk_size"].dropna().astype(int).unique())
    stability = score_stability(runs)
    citations = citation_consistency(runs)
    retrieved = retrieved_chunk_consistency(runs)
    selections = pairwise_chunk_selection(runs)

    stability.to_csv(output_dir / "answer_score_stability.csv", index=False)
    citations.to_csv(output_dir / "citation_consistency.csv", index=False)
    retrieved.to_csv(output_dir / "retrieved_chunk_consistency.csv", index=False)
    selections.to_csv(output_dir / "chunk_selection_pairs.csv", index=False)
    yes_no_detail, yes_no_metrics = yes_no_answer_comparison(runs)
    yes_no_detail.to_csv(output_dir / "yes_no_answer_comparison.csv", index=False)
    yes_no_metrics.to_csv(output_dir / "yes_no_answer_metrics.csv", index=False)
    distribution_groups = ("chunk_size", "top_k", "config_id")
    score_distribution_summary(runs, "answer_score", distribution_groups).to_csv(
        output_dir / "answer_score_ranges.csv", index=False
    )
    score_distribution_summary(chunks, "llm_score", (*distribution_groups, "is_evidence")).to_csv(
        output_dir / "chunk_llm_score_ranges.csv", index=False
    )
    score_distribution_summary(selections, "selection_jaccard", distribution_groups).to_csv(
        output_dir / "chunk_selection_ranges.csv", index=False
    )

    _write_factor_deltas(output_dir, stability, runs, top_k_values, chunk_size_values)
    pd.DataFrame([{"citation_subset_rate": citation_subset_rate(runs)}]).to_csv(
        output_dir / "citation_subset_rate.csv", index=False
    )

    boxplot(runs, "answer_score", output_dir / "answer_score_boxplot.png", "OSA answer score")
    boxplot(chunks, "llm_score", output_dir / "chunk_llm_score_boxplot.png", "Chunk LLM score")
    boxplot(
        selections,
        "selection_jaccard",
        output_dir / "chunk_selection_boxplot.png",
        "Pairwise selected-chunk Jaccard",
    )


def main() -> None:
    args = parse_args()
    if args.runs < 2:
        raise ValueError("--runs must be at least 2 for robustness evaluation")
    asyncio.run(run_evaluation(args))


if __name__ == "__main__":
    main()
