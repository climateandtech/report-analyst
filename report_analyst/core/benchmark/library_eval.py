"""Helpers for using report-analyst as a library against ClimRetrieve."""

from __future__ import annotations

import json
import re
import uuid
from itertools import combinations, pairwise
from math import log2
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

from report_analyst.core.benchmark.dataset_mapper import generate_chunk_id, generate_query_id
from report_analyst.core.benchmark.text_overlap import (
    MatchRelation,
    TextMatch,
    best_overlap,
    classify_chunk_group_match,
    classify_text_match,
    is_ground_truth_hit,
    normalize_text,
    token_jaccard,
)

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


def _chunk_order(chunk: Mapping[str, Any]) -> int | None:
    value = chunk.get("chunk_order")
    if value is None:
        value = (chunk.get("metadata") or {}).get("chunk_order")
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def match_retrieved_to_ground_truth(
    retrieved_text: str,
    gt_rows: pd.DataFrame,
) -> tuple[str, bool, float]:
    """Map an OSA chunk onto one ClimRetrieve evidence-span ID."""
    chunk_id, matched, score, _ = _match_retrieved_to_ground_truth(retrieved_text, gt_rows)
    return chunk_id, matched, score


def _match_retrieved_to_ground_truth(
    retrieved_text: str,
    gt_rows: pd.DataFrame,
) -> tuple[str, bool, float, TextMatch]:
    if gt_rows.empty:
        no_match = TextMatch(MatchRelation.NO_MATCH, 0.0, 0.0, 0.0)
        return generate_chunk_id(retrieved_text), False, 0.0, no_match
    matched_text, score = best_overlap(retrieved_text, gt_rows["chunk_text"].tolist())
    if matched_text is None:
        no_match = TextMatch(MatchRelation.NO_MATCH, score, 0.0, 0.0)
        return generate_chunk_id(retrieved_text), False, score, no_match
    matched = gt_rows.loc[gt_rows["chunk_text"] == matched_text].iloc[0]
    relation = classify_text_match(retrieved_text, matched_text)
    if is_ground_truth_hit(relation):
        return str(matched["chunk_id"]), True, score, relation
    return generate_chunk_id(retrieved_text), False, score, relation


def build_osa_retrieval_rows(
    retrieved_by_query: Mapping[tuple[str, str], Sequence[Mapping[str, Any]]],
    ground_truth: pd.DataFrame,
) -> pd.DataFrame:
    """Build an IR results table from OSA retrieved chunks."""
    rows: list[dict[str, Any]] = []
    for (document, question), chunks in retrieved_by_query.items():
        query_id = generate_query_id(document, question)
        gt = ground_truth[ground_truth["query_id"] == query_id]
        query_rows: list[dict[str, Any]] = []
        for position, chunk in enumerate(chunks, start=1):
            text = _chunk_text(chunk)
            chunk_id, matched, overlap, relation = _match_retrieved_to_ground_truth(text, gt)
            query_rows.append(
                {
                    "query_id": query_id,
                    "document": document,
                    "question": question,
                    "chunk_id": chunk_id,
                    "retrieved_chunk_id": generate_chunk_id(text),
                    "position": position,
                    "chunk_order": _chunk_order(chunk),
                    "score": float(chunk.get("score") or chunk.get("similarity_score") or chunk.get("similarity") or 0.0),
                    "chunk_text": text,
                    "matched_climretrieve": matched,
                    "overlap_score": overlap,
                    "match_relation": relation.relation.value,
                    "match_jaccard": relation.jaccard,
                    "retrieved_coverage": relation.retrieved_coverage,
                    "ground_truth_coverage": relation.ground_truth_coverage,
                    "split_component_ranks": None,
                }
            )
        rows.extend(_apply_split_ground_truth_hits(query_rows, gt))
    return pd.DataFrame(rows)


def _apply_split_ground_truth_hits(
    rows: list[dict[str, Any]],
    gt_rows: pd.DataFrame,
) -> list[dict[str, Any]]:
    """Credit a ground-truth span when two adjacent retrieved chunks reconstruct it."""
    matched_ids = {str(row["chunk_id"]) for row in rows if row["matched_climretrieve"]}
    ordered_indices = sorted(
        (index for index, row in enumerate(rows) if row["chunk_order"] is not None),
        key=lambda index: rows[index]["chunk_order"],
    )
    for gt in gt_rows.itertuples(index=False):
        ground_truth_id = str(gt.chunk_id)
        if ground_truth_id in matched_ids:
            continue
        candidates: list[tuple[int, tuple[int, int], TextMatch]] = []
        for left_index, right_index in pairwise(ordered_indices):
            left = rows[left_index]
            right = rows[right_index]
            if right["chunk_order"] != left["chunk_order"] + 1:
                continue
            match = classify_chunk_group_match(
                [str(left["chunk_text"]), str(right["chunk_text"])],
                [str(gt.chunk_text)],
            )
            if match.relation is MatchRelation.GROUND_TRUTH_SPLIT_ACROSS_RETRIEVED:
                completion_rank = max(int(left["position"]), int(right["position"]))
                candidates.append((completion_rank, (left_index, right_index), match))
        if not candidates:
            continue
        _, component_indices, match = min(candidates, key=lambda candidate: candidate[0])
        completion_index = max(component_indices, key=lambda index: int(rows[index]["position"]))
        completion = rows[completion_index]
        if completion["matched_climretrieve"]:
            continue
        completion.update(
            {
                "chunk_id": ground_truth_id,
                "matched_climretrieve": True,
                "match_relation": match.relation.value,
                "match_jaccard": match.jaccard,
                "retrieved_coverage": match.retrieved_coverage,
                "ground_truth_coverage": match.ground_truth_coverage,
                "split_component_ranks": "|".join(
                    str(rows[index]["position"]) for index in component_indices
                ),
            }
        )
        matched_ids.add(ground_truth_id)
    return rows


def build_retrieval_match_table(
    retrieval_rows: pd.DataFrame,
    ground_truth: pd.DataFrame,
) -> pd.DataFrame:
    """Explode all query-scoped retrieved-chunk-to-evidence matches."""
    if retrieval_rows.empty or ground_truth.empty:
        return pd.DataFrame()
    config_columns = [
        column
        for column in ("config_id", "chunk_size", "chunk_overlap", "top_k")
        if column in retrieval_rows.columns
    ]
    matches: list[dict[str, Any]] = []
    group_columns = [*config_columns, "query_id"]
    for key, query_results in retrieval_rows.groupby(group_columns, dropna=False):
        query_id = key[-1] if isinstance(key, tuple) else key
        query_gt = ground_truth[ground_truth["query_id"] == query_id]
        if query_gt.empty:
            continue
        for result in query_results.itertuples(index=False):
            for evidence in query_gt.itertuples(index=False):
                match = classify_text_match(str(result.chunk_text), str(evidence.chunk_text))
                if is_ground_truth_hit(match):
                    matches.append(_match_row(result, evidence, match, config_columns, [int(result.position)]))
        ordered = query_results.dropna(subset=["chunk_order"]).sort_values("chunk_order")
        ordered_rows = list(ordered.itertuples(index=False))
        for left, right in pairwise(ordered_rows):
            if int(right.chunk_order) != int(left.chunk_order) + 1:
                continue
            for evidence in query_gt.itertuples(index=False):
                match = classify_chunk_group_match(
                    [str(left.chunk_text), str(right.chunk_text)],
                    [str(evidence.chunk_text)],
                )
                if match.relation is not MatchRelation.GROUND_TRUTH_SPLIT_ACROSS_RETRIEVED:
                    continue
                completion = max((left, right), key=lambda row: int(row.position))
                matches.append(
                    _match_row(
                        completion,
                        evidence,
                        match,
                        config_columns,
                        [int(left.position), int(right.position)],
                    )
                )
    if not matches:
        return pd.DataFrame()
    frame = pd.DataFrame(matches)
    frame["relation_priority"] = frame["is_split"].astype(int)
    frame = frame.sort_values(["retrieval_position", "relation_priority"])
    frame = frame.drop_duplicates(
        [*config_columns, "query_id", "retrieval_position", "ground_truth_chunk_id"],
        keep="first",
    )
    return frame.drop(columns="relation_priority").reset_index(drop=True)


def _match_row(
    result: Any,
    evidence: Any,
    match: TextMatch,
    config_columns: Sequence[str],
    component_positions: Sequence[int],
) -> dict[str, Any]:
    return {
        **{column: getattr(result, column) for column in config_columns},
        "query_id": str(result.query_id),
        "document": str(result.document),
        "question": str(result.question),
        "retrieved_chunk_id": str(result.retrieved_chunk_id),
        "retrieval_position": int(result.position),
        "chunk_order": result.chunk_order,
        "ground_truth_chunk_id": str(evidence.chunk_id),
        "relevance_grade": float(evidence.score),
        "match_relation": match.relation.value,
        "match_jaccard": match.jaccard,
        "retrieved_coverage": match.retrieved_coverage,
        "ground_truth_coverage": match.ground_truth_coverage,
        "component_positions": json.dumps(list(component_positions)),
        "is_split": len(component_positions) > 1,
    }


def query_match_metrics(
    retrieval_rows: pd.DataFrame,
    ground_truth: pd.DataFrame,
    *,
    matches: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Per-query strict coverage and chunk-boundary diagnostics."""
    if retrieval_rows.empty:
        return pd.DataFrame()
    match_table = build_retrieval_match_table(retrieval_rows, ground_truth) if matches is None else matches
    config_columns = [
        column
        for column in ("config_id", "chunk_size", "chunk_overlap", "top_k")
        if column in retrieval_rows.columns
    ]
    query_columns = ["query_id", "document", "question"]
    rows: list[dict[str, Any]] = []
    for key, group in retrieval_rows.groupby([*config_columns, *query_columns], dropna=False):
        values = key if isinstance(key, tuple) else (key,)
        dimensions = dict(zip([*config_columns, *query_columns], values, strict=True))
        query_gt = ground_truth[ground_truth["query_id"] == dimensions["query_id"]]
        if query_gt.empty:
            continue
        n_ground_truth = query_gt["chunk_id"].astype(str).nunique()
        query_matches = _match_rows_for_dimensions(match_table, dimensions, config_columns)
        evidence_hits = (
            query_matches.sort_values("retrieval_position").drop_duplicates("ground_truth_chunk_id")
            if not query_matches.empty
            else query_matches
        )
        hit_count = evidence_hits["ground_truth_chunk_id"].astype(str).nunique() if not evidence_hits.empty else 0
        relevant_chunk_count = query_matches["retrieval_position"].nunique() if not query_matches.empty else 0
        rows.append(
            {
                **dimensions,
                "n_ground_truth": n_ground_truth,
                "n_retrieved": len(group),
                "hit_count": hit_count,
                "strict_precision": relevant_chunk_count / len(group) if len(group) else 0.0,
                "strict_recall": hit_count / n_ground_truth if n_ground_truth else 0.0,
                "complete_set_hit": bool(n_ground_truth and hit_count == n_ground_truth),
                "exact_hit_count": (
                    int((evidence_hits["match_relation"] == MatchRelation.EXACT.value).sum())
                    if not evidence_hits.empty
                    else 0
                ),
                "contained_hit_count": int(
                    (evidence_hits["match_relation"] == MatchRelation.RETRIEVED_CONTAINS_GROUND_TRUTH.value).sum()
                )
                if not evidence_hits.empty
                else 0,
                "split_hit_count": int(
                    (
                        evidence_hits["match_relation"]
                        == MatchRelation.GROUND_TRUTH_SPLIT_ACROSS_RETRIEVED.value
                    ).sum()
                )
                if not evidence_hits.empty
                else 0,
                "partial_candidate_count": int(
                    (group["match_relation"] == MatchRelation.PARTIAL_OVERLAP.value).sum()
                ),
                "mean_hit_retrieved_coverage": (
                    evidence_hits["retrieved_coverage"].mean() if not evidence_hits.empty else float("nan")
                ),
                "mean_hit_ground_truth_coverage": (
                    evidence_hits["ground_truth_coverage"].mean() if not evidence_hits.empty else float("nan")
                ),
            }
        )
    return pd.DataFrame(rows)


def _match_rows_for_dimensions(
    matches: pd.DataFrame,
    dimensions: Mapping[str, Any],
    config_columns: Sequence[str],
) -> pd.DataFrame:
    if matches.empty:
        return matches
    selected = matches[matches["query_id"] == dimensions["query_id"]]
    for column in config_columns:
        selected = selected[selected[column] == dimensions[column]]
    return selected


def summarize_query_match_metrics(query_metrics: pd.DataFrame) -> pd.DataFrame:
    """Macro-average strict query metrics for side-by-side configurations."""
    if query_metrics.empty:
        return pd.DataFrame()
    config_columns = [
        column
        for column in ("config_id", "chunk_size", "chunk_overlap", "top_k")
        if column in query_metrics.columns
    ]
    grouped = query_metrics.groupby(config_columns, dropna=False) if config_columns else [((), query_metrics)]
    rows: list[dict[str, Any]] = []
    for key, group in grouped:
        values = key if isinstance(key, tuple) else (key,)
        dimensions = dict(zip(config_columns, values, strict=True))
        rows.append(
            {
                **dimensions,
                "n_queries": len(group),
                "macro_strict_precision": group["strict_precision"].mean(),
                "macro_strict_recall": group["strict_recall"].mean(),
                "complete_set_hit_rate": group["complete_set_hit"].mean(),
                "total_exact_hits": group["exact_hit_count"].sum(),
                "total_contained_hits": group["contained_hit_count"].sum(),
                "total_split_hits": group["split_hit_count"].sum(),
                "mean_hit_retrieved_coverage": group["mean_hit_retrieved_coverage"].mean(),
                "mean_hit_ground_truth_coverage": group["mean_hit_ground_truth_coverage"].mean(),
            }
        )
    return pd.DataFrame(rows)


def ranked_query_metrics(
    retrieval_rows: pd.DataFrame,
    ground_truth: pd.DataFrame,
    *,
    matches: pd.DataFrame | None = None,
    corpus_matches: pd.DataFrame | None = None,
    k_values: Sequence[int],
    binary_relevance_min: float = 2.0,
) -> pd.DataFrame:
    """Per-query IR metrics with one maximum relevance grade per ranked chunk."""
    if retrieval_rows.empty:
        return pd.DataFrame()
    retrieval_matches = build_retrieval_match_table(retrieval_rows, ground_truth) if matches is None else matches
    ideal_matches = retrieval_matches if corpus_matches is None else corpus_matches
    config_columns = [
        column
        for column in ("config_id", "chunk_size", "chunk_overlap", "top_k")
        if column in retrieval_rows.columns
    ]
    query_columns = ["query_id", "document", "question"]
    rows: list[dict[str, Any]] = []
    for key, group in retrieval_rows.groupby([*config_columns, *query_columns], dropna=False):
        values = key if isinstance(key, tuple) else (key,)
        dimensions = dict(zip([*config_columns, *query_columns], values, strict=True))
        query_gt = ground_truth[ground_truth["query_id"] == dimensions["query_id"]]
        if query_gt.empty:
            continue
        query_matches = _match_rows_for_dimensions(retrieval_matches, dimensions, config_columns)
        rank_gains = (
            query_matches.groupby("retrieval_position")["relevance_grade"].max().to_dict()
            if not query_matches.empty
            else {}
        )
        ranked_gains: list[float] = []
        for result in group.sort_values("position").itertuples(index=False):
            ranked_gains.append(float(rank_gains.get(int(result.position), 0.0)))
        query_ideal_matches = _match_rows_for_dimensions(ideal_matches, dimensions, config_columns)
        ideal_gains = (
            query_ideal_matches.groupby("retrieval_position")["relevance_grade"].max().sort_values(ascending=False).tolist()
            if not query_ideal_matches.empty
            else []
        )
        binary = [int(gain >= binary_relevance_min) for gain in ranked_gains]
        total_relevant = sum(gain >= binary_relevance_min for gain in ideal_gains)
        average_precision = _average_precision(binary, total_relevant)
        reciprocal_rank = next((1.0 / rank for rank, rel in enumerate(binary, start=1) if rel), 0.0)
        for k in k_values:
            relevant_at_k = sum(binary[:k])
            precision = relevant_at_k / k if k else 0.0
            recall = relevant_at_k / total_relevant if total_relevant else 0.0
            dcg = sum(gain / log2(rank + 1) for rank, gain in enumerate(ranked_gains[:k], start=1))
            idcg = sum(gain / log2(rank + 1) for rank, gain in enumerate(ideal_gains[:k], start=1))
            rows.append(
                {
                    **dimensions,
                    "k": k,
                    "precision": precision,
                    "recall": recall,
                    "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0.0,
                    "ndcg": dcg / idcg if idcg else 0.0,
                    "hit": bool(relevant_at_k),
                    "complete_set_hit": bool(total_relevant and relevant_at_k == total_relevant),
                    "average_precision": average_precision,
                    "reciprocal_rank": reciprocal_rank,
                }
            )
    return pd.DataFrame(rows)


def _average_precision(binary_relevance: Sequence[int], total_relevant: int) -> float:
    if not total_relevant:
        return 0.0
    hits = 0
    score = 0.0
    for rank, relevant in enumerate(binary_relevance, start=1):
        if relevant:
            hits += 1
            score += hits / rank
    return score / total_relevant


def summarize_ranked_query_metrics(query_metrics: pd.DataFrame) -> pd.DataFrame:
    """Macro-average paper ranking metrics by retrieval configuration and k."""
    if query_metrics.empty:
        return pd.DataFrame()
    dimensions = [
        column
        for column in ("config_id", "chunk_size", "chunk_overlap", "top_k", "k")
        if column in query_metrics.columns
    ]
    return (
        query_metrics.groupby(dimensions, dropna=False)
        .agg(
            n_queries=("query_id", "nunique"),
            precision=("precision", "mean"),
            recall=("recall", "mean"),
            f1=("f1", "mean"),
            ndcg=("ndcg", "mean"),
            hit_rate=("hit", "mean"),
            complete_set_hit_rate=("complete_set_hit", "mean"),
            MAP=("average_precision", "mean"),
            MRR=("reciprocal_rank", "mean"),
        )
        .reset_index()
    )


def bootstrap_macro_intervals(
    query_metrics: pd.DataFrame,
    value_columns: Sequence[str],
    *,
    group_columns: Sequence[str],
    n_bootstrap: int = 2000,
    seed: int = 42,
) -> pd.DataFrame:
    """Query-level bootstrap means and 95% confidence intervals."""
    if query_metrics.empty:
        return pd.DataFrame()
    rng = np.random.default_rng(seed)
    grouped = query_metrics.groupby(list(group_columns), dropna=False) if group_columns else [((), query_metrics)]
    rows: list[dict[str, Any]] = []
    for key, group in grouped:
        values = key if isinstance(key, tuple) else (key,)
        dimensions = dict(zip(group_columns, values, strict=True))
        for column in value_columns:
            metric_values = group[column].dropna().astype(float).to_numpy()
            if not len(metric_values):
                continue
            samples = rng.choice(metric_values, size=(n_bootstrap, len(metric_values)), replace=True).mean(axis=1)
            rows.append(
                {
                    **dimensions,
                    "metric": column,
                    "n_queries": len(metric_values),
                    "mean": float(metric_values.mean()),
                    "ci_low": float(np.quantile(samples, 0.025)),
                    "ci_high": float(np.quantile(samples, 0.975)),
                    "n_bootstrap": n_bootstrap,
                    "seed": seed,
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


def build_overlap_table(
    ground_truth: pd.DataFrame,
    osa_retrieval: pd.DataFrame,
    *,
    matches: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Per-query overlap of ClimRetrieve relevant chunks vs OSA retrieved chunks."""
    rows: list[dict[str, Any]] = []
    for query_id, gt_group in ground_truth.groupby("query_id"):
        osa_group = osa_retrieval[osa_retrieval["query_id"] == query_id]
        document = str(gt_group["document"].iloc[0])
        question = str(gt_group["question"].iloc[0])
        gt_ids = set(gt_group["chunk_id"].astype(str))
        if matches is None:
            osa_ids = set(osa_group.loc[osa_group["matched_climretrieve"], "chunk_id"].astype(str))
        else:
            osa_ids = set(
                matches.loc[matches["query_id"] == query_id, "ground_truth_chunk_id"].astype(str)
            )
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
