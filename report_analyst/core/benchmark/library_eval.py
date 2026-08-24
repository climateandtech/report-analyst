"""Helpers for using report-analyst as a library against ClimRetrieve."""

from __future__ import annotations

import json
import re
import uuid
from itertools import combinations
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import pandas as pd

from report_analyst.core.benchmark.dataset_mapper import generate_chunk_id, generate_query_id
from report_analyst.core.benchmark.text_overlap import best_overlap, normalize_text, token_jaccard

PREFERRED_CLIMRETRIEVE_PDFS = (
    "CT REIT 2022 ESG Report.pdf",
    "BHP Climate Transition Action Plan.pdf",
    "BHP Climate Change Report 2020.pdf",
    "CostCo Climate Action Plan.pdf",
    "AstraZeneca Sustainability Report 2023.pdf",
    "Veolia ESG Report 2023.pdf",
    "Walmart ESG Highlights 2023.pdf",
    "Schneider Sustainability Report.pdf",
    "Boeing 2023 Sustainability Report.pdf",
    "PayPal Global Impact Report 2023.pdf",
)

_COLUMN_ALIASES = {
    "document": ("document", "report", "report_name"),
    "question": ("question", "query"),
    "relevant": ("relevant", "relevant_text", "context"),
    "answer": ("answer", "expert_answer"),
    "core_16": ("core 16 question", "core_16_question", "core16"),
    "relevance_score": ("source relevance score", "relevance", "label"),
}


def _alias_lookup(columns: Iterable[str], aliases: Sequence[str]) -> str | None:
    lowered = {str(col).strip().lower(): col for col in columns}
    for alias in aliases:
        if alias in lowered:
            return lowered[alias]
    return None


def normalize_climretrieve_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Map ClimRetrieve expert-label columns onto a stable schema."""
    out = df.copy()
    document_col = _alias_lookup(out.columns, _COLUMN_ALIASES["document"])
    question_col = _alias_lookup(out.columns, _COLUMN_ALIASES["question"])
    relevant_col = _alias_lookup(out.columns, _COLUMN_ALIASES["relevant"])
    if not document_col or not question_col or not relevant_col:
        raise ValueError(f"ClimRetrieve labels missing required columns: {list(out.columns)}")
    core_col = _alias_lookup(out.columns, _COLUMN_ALIASES["core_16"])
    score_col = _alias_lookup(out.columns, _COLUMN_ALIASES["relevance_score"])
    renamed = {
        document_col: "document",
        question_col: "question",
        relevant_col: "relevant",
    }
    if core_col:
        renamed[core_col] = "core_16"
    if score_col:
        renamed[score_col] = "relevance_score"
    answer_col = _alias_lookup(out.columns, _COLUMN_ALIASES["answer"])
    if answer_col:
        renamed[answer_col] = "answer"
    return out.rename(columns=renamed)


def _truthy(value: Any) -> bool:
    if pd.isna(value):
        return False
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value == 1
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def filter_core_questions(df: pd.DataFrame) -> pd.DataFrame:
    """Keep Core-16 rows when that flag exists; otherwise keep all rows."""
    if "core_16" not in df.columns:
        return df
    return df[df["core_16"].map(_truthy)].copy()


def stem_name(value: str | None) -> str:
    """Filename stem used to match PDF names to ClimRetrieve documents."""
    text = normalize_text(value)
    text = re.sub(r"\.pdf$", "", text)
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def pdf_matches_document(pdf_filename: str, document: str) -> bool:
    """True when a PDF filename and a ClimRetrieve document name refer to the same report."""
    pdf_stem = stem_name(pdf_filename)
    doc_stem = stem_name(document)
    if not pdf_stem or not doc_stem:
        return False
    return pdf_stem == doc_stem or pdf_stem in doc_stem or doc_stem in pdf_stem


def match_question(osa_question: str, climretrieve_questions: Sequence[str], *, min_jaccard: float = 0.7) -> str | None:
    """Map an OSA question onto a ClimRetrieve question by text overlap."""
    osa_norm = normalize_text(osa_question)
    for question in climretrieve_questions:
        if normalize_text(question) == osa_norm:
            return question
        if token_jaccard(osa_question, question) >= min_jaccard:
            return question
    return None


def match_document_to_pdf(document: str, pdf_filenames: Sequence[str]) -> str | None:
    """Return the PDF filename that matches a labelled document, if any."""
    for name in pdf_filenames:
        if pdf_matches_document(name, document):
            return name
    return None


def select_labelled_reports(
    labels: pd.DataFrame,
    pdf_filenames: Sequence[str],
    *,
    n: int = 10,
    preferred_pdfs: Sequence[str] = PREFERRED_CLIMRETRIEVE_PDFS,
) -> pd.DataFrame:
    """Pick n labelled ClimRetrieve reports that also have PDFs."""
    labelled = filter_core_questions(normalize_climretrieve_columns(labels))
    counts = labelled.groupby("document", dropna=False).size().rename("n_labels").reset_index()
    rows: list[dict[str, Any]] = []
    for _, row in counts.iterrows():
        pdf_name = match_document_to_pdf(str(row["document"]), pdf_filenames)
        if pdf_name is None:
            continue
        rows.append(
            {
                "document": row["document"],
                "pdf_filename": pdf_name,
                "n_labels": int(row["n_labels"]),
                "preferred": pdf_name in set(preferred_pdfs),
            }
        )
    matched = pd.DataFrame(rows)
    if matched.empty:
        return matched
    preferred = matched[matched["preferred"]].sort_values(["n_labels", "document"], ascending=[False, True])
    rest = matched[~matched["preferred"]].sort_values(["n_labels", "document"], ascending=[False, True])
    ordered = pd.concat([preferred, rest], ignore_index=True)
    return ordered.head(n).reset_index(drop=True)


def build_ground_truth_rows(labels: pd.DataFrame, selected_documents: Sequence[str]) -> pd.DataFrame:
    """IR ground-truth rows for EvaluationEngine.compare_flexible_datasets."""
    labelled = filter_core_questions(normalize_climretrieve_columns(labels))
    subset = labelled[labelled["document"].isin(set(selected_documents))].copy()
    if subset.empty:
        return pd.DataFrame(columns=["query_id", "chunk_id", "position", "score", "document", "question", "chunk_text"])
    if "relevance_score" in subset.columns:
        subset["score"] = pd.to_numeric(subset["relevance_score"], errors="coerce").fillna(1.0)
    else:
        subset["score"] = 1.0
    subset["query_id"] = [generate_query_id(doc, q) for doc, q in zip(subset["document"], subset["question"], strict=True)]
    subset["chunk_id"] = subset["relevant"].map(generate_chunk_id)
    subset["chunk_text"] = subset["relevant"]
    subset["position"] = subset.groupby("query_id").cumcount() + 1
    return subset[["query_id", "chunk_id", "position", "score", "document", "question", "chunk_text"]].reset_index(drop=True)


def parse_yes_no_answer(value: Any) -> bool | None:
    """Parse an explicit leading YES/NO label without inferring narrative text."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    text = str(value).strip()
    text = re.sub(r"^[\s\[\]()*_`#]+", "", text)
    match = re.match(r"(?i)^(yes|no)\b", text)
    if not match:
        return None
    return match.group(1).lower() == "yes"


def build_climretrieve_answer_rows(
    labels: pd.DataFrame,
    selected_documents: Sequence[str],
    selected_questions: Sequence[str] | None = None,
) -> pd.DataFrame:
    """One expert answer and optional explicit yes/no label per report/question."""
    normalized = filter_core_questions(normalize_climretrieve_columns(labels))
    if "answer" not in normalized.columns:
        return pd.DataFrame(columns=["document", "question", "expert_answer", "expert_yes_no"])
    subset = normalized[normalized["document"].isin(set(selected_documents))].copy()
    if selected_questions is not None:
        subset = subset[subset["question"].isin(set(selected_questions))]
    subset = subset.dropna(subset=["answer"])
    subset["answer"] = subset["answer"].astype(str).str.strip()
    subset = subset[subset["answer"] != ""].drop_duplicates(["document", "question", "answer"])
    rows = subset.groupby(["document", "question"], dropna=False)["answer"].first().reset_index()
    rows = rows.rename(columns={"answer": "expert_answer"})
    rows["expert_yes_no"] = rows["expert_answer"].map(parse_yes_no_answer)
    return rows


def _chunk_text(chunk: Mapping[str, Any]) -> str:
    return str(chunk.get("text") or chunk.get("chunk_text") or "")


def match_retrieved_to_ground_truth(
    retrieved_text: str,
    gt_rows: pd.DataFrame,
) -> tuple[str, bool, float]:
    """Map an OSA chunk onto a ClimRetrieve chunk_id when overlap is high enough."""
    if gt_rows.empty:
        return generate_chunk_id(retrieved_text), False, 0.0
    matched_text, score = best_overlap(retrieved_text, gt_rows["chunk_text"].tolist())
    if matched_text is None:
        return generate_chunk_id(retrieved_text), False, score
    matched = gt_rows.loc[gt_rows["chunk_text"] == matched_text].iloc[0]
    return str(matched["chunk_id"]), True, score


def build_osa_retrieval_rows(
    retrieved_by_query: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]],
    ground_truth: pd.DataFrame,
) -> pd.DataFrame:
    """Build an IR results table from OSA retrieved chunks."""
    rows: list[dict[str, Any]] = []
    for (document, question), chunks in retrieved_by_query.items():
        query_id = generate_query_id(document, question)
        gt = ground_truth[ground_truth["query_id"] == query_id]
        for position, chunk in enumerate(chunks, start=1):
            text = _chunk_text(chunk)
            chunk_id, matched, overlap = match_retrieved_to_ground_truth(text, gt)
            rows.append(
                {
                    "query_id": query_id,
                    "document": document,
                    "question": question,
                    "chunk_id": chunk_id,
                    "position": position,
                    "score": float(chunk.get("score") or chunk.get("similarity_score") or chunk.get("similarity") or 0.0),
                    "chunk_text": text,
                    "matched_climretrieve": matched,
                    "overlap_score": overlap,
                }
            )
    return pd.DataFrame(rows)


def overlap_row(gt_ids: set[str], osa_ids: set[str], *, query_id: str, document: str, question: str) -> dict[str, Any]:
    """Set-overlap stats for one query."""
    both = gt_ids & osa_ids
    union = gt_ids | osa_ids
    return {
        "query_id": query_id,
        "document": document,
        "question": question,
        "n_climretrieve": len(gt_ids),
        "n_osa": len(osa_ids),
        "n_both": len(both),
        "n_climretrieve_only": len(gt_ids - osa_ids),
        "n_osa_only": len(osa_ids - gt_ids),
        "jaccard": (len(both) / len(union)) if union else 0.0,
    }


def build_overlap_table(ground_truth: pd.DataFrame, osa_retrieval: pd.DataFrame) -> pd.DataFrame:
    """Per-query overlap of ClimRetrieve relevant chunks vs OSA retrieved chunks."""
    rows: list[dict[str, Any]] = []
    for query_id, gt_group in ground_truth.groupby("query_id"):
        osa_group = osa_retrieval[osa_retrieval["query_id"] == query_id]
        document = str(gt_group["document"].iloc[0])
        question = str(gt_group["question"].iloc[0])
        gt_ids = set(gt_group["chunk_id"].astype(str))
        osa_ids = set(osa_group.loc[osa_group["matched_climretrieve"], "chunk_id"].astype(str))
        rows.append(overlap_row(gt_ids, osa_ids, query_id=str(query_id), document=document, question=question))
    return pd.DataFrame(rows)


def parse_osa_score(value: Any) -> float | None:
    """Parse OSA SCORE fields that may be numeric or embedded in text."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    match = re.search(r"(\d+(?:\.\d+)?)", str(value))
    if not match:
        return None
    return float(match.group(1))


def cited_texts(result: Mapping[str, Any], retrieved_chunks: Sequence[Mapping[str, Any]]) -> list[str]:
    """Resolve SOURCES / EVIDENCE chunk numbers to retrieved chunk texts."""
    sources = result.get("SOURCES") or []
    texts: list[str] = []
    for source in sources:
        try:
            index = int(source) - 1
        except (TypeError, ValueError):
            continue
        if 0 <= index < len(retrieved_chunks):
            texts.append(_chunk_text(retrieved_chunks[index]))
    if texts:
        return texts
    evidence = result.get("EVIDENCE") or []
    return [str(item.get("chunk_text") or item.get("text") or "") for item in evidence if isinstance(item, dict)]


def cited_chunk_ids(
    result: Mapping[str, Any],
    retrieved_chunks: Sequence[Mapping[str, Any]],
    gt_rows: pd.DataFrame,
) -> list[str]:
    """Chunk IDs for citations, aligned to ClimRetrieve when texts overlap."""
    ids: list[str] = []
    for text in cited_texts(result, retrieved_chunks):
        chunk_id, _, _ = match_retrieved_to_ground_truth(text, gt_rows)
        ids.append(chunk_id)
    return ids


def retrieved_chunk_ids(
    retrieved_chunks: Sequence[Mapping[str, Any]],
    gt_rows: pd.DataFrame,
) -> list[str]:
    """Chunk IDs for the retrieved top-k, aligned to ClimRetrieve when texts overlap."""
    ids: list[str] = []
    for chunk in retrieved_chunks:
        chunk_id, _, _ = match_retrieved_to_ground_truth(_chunk_text(chunk), gt_rows)
        ids.append(chunk_id)
    return ids


def generate_run_uid(context: Mapping[str, Any]) -> str:
    """Generate a stable unique ID for one analysis run inside an evaluation."""
    required = ("evaluation_id", "document", "question", "config_id", "run_id")
    missing = [key for key in required if context.get(key) in (None, "")]
    if missing:
        raise ValueError(f"Run context missing ID fields: {missing}")
    identity = json.dumps({key: context[key] for key in required}, sort_keys=True, default=str)
    return uuid.uuid5(uuid.NAMESPACE_URL, identity).hex


def build_analysis_run_rows(
    result: Mapping[str, Any],
    gt_rows: pd.DataFrame,
    context: Mapping[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Flatten one answer and its selected chunks into CSV-friendly rows."""
    chunks = result.get("chunks") or []
    selected_ids = retrieved_chunk_ids(chunks, gt_rows)
    cited_ids = cited_chunk_ids(result, chunks, gt_rows)
    run_uid = str(context.get("run_uid") or generate_run_uid(context))
    base = {
        "evaluation_id": context["evaluation_id"],
        "run_uid": run_uid,
        "document": context["document"],
        "pdf_filename": context.get("pdf_filename"),
        "question": context["question"],
        "osa_question_id": context.get("osa_question_id"),
        "config_id": context["config_id"],
        "top_k": context["top_k"],
        "chunk_size": context.get("chunk_size"),
        "chunk_overlap": context.get("chunk_overlap"),
        "model": context.get("model"),
        "run_id": context["run_id"],
        "expert_answer": context.get("expert_answer"),
        "expert_yes_no": context.get("expert_yes_no"),
    }
    answer_row = {
        **base,
        "answer_score": parse_osa_score(result.get("SCORE")),
        "answer": result.get("ANSWER"),
        "answer_yes_no": parse_yes_no_answer(result.get("ANSWER")),
        "gaps": json.dumps(result.get("GAPS") or [], default=str),
        "sources": json.dumps(result.get("SOURCES") or [], default=str),
        "evidence": json.dumps(result.get("EVIDENCE") or [], default=str),
        "question_text": result.get("question_text"),
        "guidelines": result.get("guidelines"),
        "retrieved_chunk_ids": "|".join(selected_ids),
        "cited_chunk_ids": "|".join(cited_ids),
        "n_retrieved": len(chunks),
    }
    chunk_rows = []
    for index, (chunk, chunk_id) in enumerate(zip(chunks, selected_ids, strict=True), start=1):
        metadata = chunk.get("metadata") or {}
        chunk_rows.append(
            {
                **base,
                "chunk_id": chunk_id,
                "retrieval_rank": index,
                "chunk_order": chunk.get("chunk_order", index - 1),
                "similarity_score": chunk.get("similarity_score", chunk.get("score")),
                "llm_score": chunk.get("llm_score"),
                "is_evidence": bool(chunk.get("is_evidence", False)),
                "evidence_order": chunk.get("evidence_order"),
                "page": metadata.get("page") or metadata.get("page_number"),
                "chunk_text": _chunk_text(chunk),
            }
        )
    return answer_row, chunk_rows


def combine_analysis_run_rows(
    answer_row: Mapping[str, Any],
    chunk_rows: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Denormalize one answer and its chunks into a single-table representation."""
    if chunk_rows:
        return [{**answer_row, **chunk} for chunk in chunk_rows]
    empty_chunk = {
        "chunk_id": None,
        "retrieval_rank": None,
        "chunk_order": None,
        "similarity_score": None,
        "llm_score": None,
        "is_evidence": False,
        "evidence_order": None,
        "page": None,
        "chunk_text": None,
    }
    return [{**answer_row, **empty_chunk}]


def yes_no_answer_comparison(runs: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Compare explicit OSA and expert yes/no answers by experimental config."""
    detail = runs.copy()
    if "answer_yes_no" not in detail.columns:
        detail["answer_yes_no"] = detail["answer"].map(parse_yes_no_answer)
    detail = detail.dropna(subset=["expert_yes_no", "answer_yes_no"]).copy()
    detail["expert_yes_no"] = detail["expert_yes_no"].map(_coerce_bool)
    detail["answer_yes_no"] = detail["answer_yes_no"].map(_coerce_bool)
    detail["yes_no_match"] = detail["expert_yes_no"] == detail["answer_yes_no"]
    rows = []
    for config_id, group in detail.groupby("config_id", dropna=False):
        truth = group["expert_yes_no"]
        predicted = group["answer_yes_no"]
        tp = int((truth & predicted).sum())
        tn = int((~truth & ~predicted).sum())
        fp = int((~truth & predicted).sum())
        fn = int((truth & ~predicted).sum())
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        rows.append(
            {
                "config_id": config_id,
                "chunk_size": group["chunk_size"].iloc[0] if "chunk_size" in group else None,
                "top_k": group["top_k"].iloc[0] if "top_k" in group else None,
                "n": len(group),
                "tp": tp,
                "tn": tn,
                "fp": fp,
                "fn": fn,
                "accuracy": (tp + tn) / len(group),
                "precision_yes": precision,
                "recall_yes": recall,
                "f1_yes": (2 * precision * recall / (precision + recall)) if precision + recall else 0.0,
            }
        )
    return detail, pd.DataFrame(rows)


def _coerce_bool(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def score_stability(runs: pd.DataFrame) -> pd.DataFrame:
    """Score mean/std/range across repeated runs of the same config."""
    working = runs.copy()
    score_column = "answer_score" if "answer_score" in working.columns else "score"
    working[score_column] = working[score_column].map(parse_osa_score)
    grouped = working.groupby(["document", "question", "config_id"], dropna=False)[score_column]
    return grouped.agg(n_runs="count", score_mean="mean", score_std="std", score_min="min", score_max="max").reset_index()


def _split_ids(value: Any) -> set[str]:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return set()
    if isinstance(value, (list, tuple, set)):
        return {str(item) for item in value if str(item)}
    return {part for part in str(value).split("|") if part}


def _mean_pairwise_jaccard(id_sets: Sequence[set[str]]) -> float:
    if len(id_sets) < 2:
        return 1.0 if id_sets and id_sets[0] else 0.0
    scores: list[float] = []
    for i, left in enumerate(id_sets):
        for right in id_sets[i + 1 :]:
            union = left | right
            scores.append((len(left & right) / len(union)) if union else 1.0)
    return sum(scores) / len(scores)


def _id_column_consistency(runs: pd.DataFrame, column: str, metric_name: str) -> pd.DataFrame:
    """Pairwise Jaccard of ID sets across runs of the same config."""
    rows: list[dict[str, Any]] = []
    grouped = runs.groupby(["document", "question", "config_id"], dropna=False)
    for (document, question, config_id), group in grouped:
        id_sets = [_split_ids(value) for value in group[column]]
        rows.append(
            {
                "document": document,
                "question": question,
                "config_id": config_id,
                "n_runs": len(group),
                metric_name: _mean_pairwise_jaccard(id_sets),
            }
        )
    return pd.DataFrame(rows)


def citation_consistency(runs: pd.DataFrame) -> pd.DataFrame:
    """How often repeated runs cite the same ClimRetrieve-aligned chunks."""
    return _id_column_consistency(runs, "cited_chunk_ids", "citation_jaccard")


def retrieved_chunk_consistency(runs: pd.DataFrame) -> pd.DataFrame:
    """How often repeated runs retrieve the same chunk set (same top-k)."""
    return _id_column_consistency(runs, "retrieved_chunk_ids", "retrieved_jaccard")


def pairwise_chunk_selection(runs: pd.DataFrame) -> pd.DataFrame:
    """Pairwise selected-chunk Jaccard rows suitable for box plots."""
    rows: list[dict[str, Any]] = []
    grouped = runs.groupby(["document", "question", "config_id"], dropna=False)
    for (document, question, config_id), group in grouped:
        dimensions = {
            key: group[key].iloc[0]
            for key in ("chunk_size", "top_k")
            if key in group.columns
        }
        run_sets = [
            (row.run_id, _split_ids(row.retrieved_chunk_ids))
            for row in group[["run_id", "retrieved_chunk_ids"]].itertuples(index=False)
        ]
        for (run_a, ids_a), (run_b, ids_b) in combinations(run_sets, 2):
            union = ids_a | ids_b
            rows.append(
                {
                    "document": document,
                    "question": question,
                    "config_id": config_id,
                    **dimensions,
                    "run_a": run_a,
                    "run_b": run_b,
                    "selection_jaccard": (len(ids_a & ids_b) / len(union)) if union else 1.0,
                }
            )
    return pd.DataFrame(rows)


def score_distribution_summary(
    frame: pd.DataFrame,
    value_column: str,
    group_columns: Sequence[str] = ("config_id",),
) -> pd.DataFrame:
    """Count, quartiles, extrema, and range for box-plot source values."""
    working = frame.copy()
    working[value_column] = pd.to_numeric(working[value_column], errors="coerce")
    working = working.dropna(subset=[value_column])
    columns = [*group_columns, "count", "mean", "std", "min", "q1", "median", "q3", "max", "range"]
    if working.empty:
        return pd.DataFrame(columns=columns)
    grouped = working.groupby(list(group_columns), dropna=False)[value_column]
    summary = grouped.agg(
        count="count",
        mean="mean",
        std="std",
        min="min",
        q1=lambda values: values.quantile(0.25),
        median="median",
        q3=lambda values: values.quantile(0.75),
        max="max",
    ).reset_index()
    summary["range"] = summary["max"] - summary["min"]
    return summary


def topk_retrieved_containment(
    runs: pd.DataFrame,
    low_config: str,
    high_config: str,
) -> pd.DataFrame:
    """Share of low-k retrieved chunks that also appear in the high-k set."""
    rows: list[dict[str, Any]] = []
    low = runs[runs["config_id"] == low_config]
    high = runs[runs["config_id"] == high_config]
    keys = ["document", "question"]
    low_groups = low.groupby(keys, dropna=False)
    high_groups = high.groupby(keys, dropna=False)
    for key, low_group in low_groups:
        high_group = high_groups.get_group(key) if key in high_groups.groups else None
        if high_group is None:
            continue
        low_ids = _split_ids(low_group["retrieved_chunk_ids"].iloc[0])
        high_ids = _split_ids(high_group["retrieved_chunk_ids"].iloc[0])
        shared = low_ids & high_ids
        containment = (len(shared) / len(low_ids)) if low_ids else 1.0
        document, question = key
        rows.append(
            {
                "document": document,
                "question": question,
                "n_low": len(low_ids),
                "n_high": len(high_ids),
                "n_shared": len(shared),
                "containment": containment,
            }
        )
    return pd.DataFrame(rows)


def citations_are_subset(cited_ids: Sequence[str], retrieved_ids: Sequence[str]) -> bool:
    """True when every cited chunk was in the retrieved top-k."""
    return set(cited_ids).issubset(set(retrieved_ids))


def citation_subset_rate(runs: pd.DataFrame) -> float:
    """Share of runs whose cited chunks are all in the retrieved set."""
    if runs.empty:
        return 1.0
    flags = [
        citations_are_subset(_split_ids(cited), _split_ids(retrieved))
        for cited, retrieved in zip(runs["cited_chunk_ids"], runs["retrieved_chunk_ids"], strict=True)
    ]
    return sum(flags) / len(flags)


def score_range(stability: pd.DataFrame) -> pd.Series:
    """Per-group score span (max - min) from a score_stability table."""
    return stability["score_max"] - stability["score_min"]


def topk_score_delta(stability: pd.DataFrame, low_config: str, high_config: str) -> pd.DataFrame:
    """Compare mean OSA scores between two top-k configs."""
    low = stability[stability["config_id"] == low_config][["document", "question", "score_mean"]]
    high = stability[stability["config_id"] == high_config][["document", "question", "score_mean"]]
    merged = low.merge(high, on=["document", "question"], suffixes=(f"_{low_config}", f"_{high_config}"))
    low_col = f"score_mean_{low_config}"
    high_col = f"score_mean_{high_config}"
    merged["score_delta"] = merged[high_col] - merged[low_col]
    return merged


def metrics_to_frame(metrics: Any, *, config_id: str = "default") -> pd.DataFrame:
    """Flatten EvaluationMetrics into a long CSV-friendly table."""
    rows: list[dict[str, Any]] = []
    for attr, name in (
        ("precision_at_k", "precision"),
        ("recall_at_k", "recall"),
        ("f1_at_k", "f1"),
        ("ndcg_at_k", "ndcg"),
    ):
        values = getattr(metrics, attr, {}) or {}
        for k, value in values.items():
            rows.append({"config_id": config_id, "k": k, "metric": name, "value": value})
    rows.append({"config_id": config_id, "k": None, "metric": "MAP", "value": metrics.mean_average_precision})
    rows.append({"config_id": config_id, "k": None, "metric": "MRR", "value": metrics.mean_reciprocal_rank})
    return pd.DataFrame(rows)


def write_eval_csvs(frames: Mapping[str, pd.DataFrame], output_dir: str | Path) -> dict[str, Path]:
    """Write every analysis frame to CSV. Returns the paths written."""
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for name, frame in frames.items():
        path = directory / f"{name}.csv"
        frame.to_csv(path, index=False)
        written[name] = path
    return written
