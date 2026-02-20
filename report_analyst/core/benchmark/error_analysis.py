import logging
from typing import Dict, List

import pandas as pd

from ...models.benchmark import BenchmarkDataset, BenchmarkDatasetContent, RetrievalResultRow

logger = logging.getLogger(__name__)


def build_error_analysis_dataframe(
    ground_truth: BenchmarkDatasetContent,
    retrieval_results: List[RetrievalResultRow],
    top_k: int,
) -> pd.DataFrame:
    """
    Build a per-chunk error-analysis dataframe.

    Each row corresponds to one retrieved chunk within top_k for a given question.
    Columns:
      - report_name
      - question
      - relevant_part_text
      - retrieved_chunk_text
      - position_in_top_k
      - expert_relevance_label
      - model_score
      - is_really_relevant (expert label > 0)
      - query_id
      - chunk_id
    """
    # Index ground truth by question_id and chunk_id for fast lookup
    gt_by_question: Dict[str, Dict[str, float]] = {}
    gt_text_by_question: Dict[str, Dict[str, str]] = {}
    report_by_question: Dict[str, str] = {}
    question_text_by_id: Dict[str, str] = {}

    for q in ground_truth.questions:
        question_id = q.question_id
        question_text_by_id[question_id] = q.text
        # Use first report_id in metadata if available
        report_name = ""
        if q.ground_truth_chunks:
            meta = q.ground_truth_chunks[0].metadata or {}
            report_name = meta.get("document") or meta.get("report") or ""
        report_by_question[question_id] = report_name

        by_chunk: Dict[str, float] = {}
        text_by_chunk: Dict[str, str] = {}
        for chunk in q.ground_truth_chunks:
            by_chunk[chunk.chunk_id] = chunk.relevance_score
            text_by_chunk[chunk.chunk_id] = chunk.text
        gt_by_question[question_id] = by_chunk
        gt_text_by_question[question_id] = text_by_chunk

    rows: List[Dict] = []

    # Group retrieval results by query_id
    results_by_query: Dict[str, List[RetrievalResultRow]] = {}
    for r in retrieval_results:
        results_by_query.setdefault(r.query_id, []).append(r)

    for query_id, rows_for_query in results_by_query.items():
        # Sort by position and take top_k
        sorted_rows = sorted(rows_for_query, key=lambda r: r.position)[:top_k]

        gt_scores = gt_by_question.get(query_id, {})
        gt_texts = gt_text_by_question.get(query_id, {})
        report_name = report_by_question.get(query_id, "")
        question_text = question_text_by_id.get(query_id, "")

        for r in sorted_rows:
            expert_label = gt_scores.get(r.chunk_id, 0.0)
            is_really_relevant = expert_label > 0
            relevant_part_text = gt_texts.get(r.chunk_id, "")

            rows.append(
                {
                    "report_name": report_name,
                    "question_id": query_id,
                    "question": question_text,
                    "relevant_part_text": relevant_part_text,
                    "retrieved_chunk_text": r.chunk_text or "",
                    "position_in_top_k": r.position,
                    "expert_relevance_label": expert_label,
                    "model_score": r.score,
                    "is_really_relevant": is_really_relevant,
                    "chunk_id": r.chunk_id,
                }
            )

    df = pd.DataFrame(rows)
    logger.info(f"Built error-analysis dataframe with {len(df)} rows")
    return df


def build_error_analysis_dataframe_from_flexible(
    ground_truth_dataset: BenchmarkDataset,
    benchmark_dataset: BenchmarkDataset,
    top_k: int,
) -> pd.DataFrame:
    """
    Build a per-chunk error-analysis dataframe from flexible BenchmarkDataset objects.

    Each row corresponds to one retrieved chunk within top_k for a given question.
    Columns:
      - report_name
      - question_id
      - question (if available in ground truth)
      - relevant_part_text (from ground truth)
      - retrieved_chunk_text (from benchmark)
      - position_in_top_k
      - expert_relevance_label (from ground truth score)
      - model_score (from benchmark)
      - is_really_relevant (expert label > 0)
      - chunk_id
    """
    # Index ground truth by query_id and chunk_id
    gt_by_query: Dict[str, Dict[str, Dict]] = {}  # query_id -> chunk_id -> {score, text, report, question}
    # Also create an index by (report, question) pair for fallback lookup
    gt_by_report_question: Dict[str, Dict[str, Dict[str, Dict]]] = {}  # report -> question -> chunk_id -> {score, text, report, question}
    
    for result in ground_truth_dataset.results:
        query_id = result.get_query_id()
        if not query_id:
            continue
        
        chunk_id = result.get_chunk_id()
        if not chunk_id:
            continue
        
        if query_id not in gt_by_query:
            gt_by_query[query_id] = {}
        
        # Extract data from flexible row
        data = result.data
        score = (
            result.get_score()
            or data.get("relevance_label")
            or data.get("relevance_score")
            or 0.0
        )
        # Try to get relevant part text - check for "Relevant" column (case-insensitive) first
        # as user mentioned it should retrieve from "Relevant" column
        text = None
        # Check case-insensitive for "relevant" column
        for key in data.keys():
            if key.lower() == "relevant":
                text = data.get(key)
                break
        # Fallback to other common column names
        if not text:
            text = (
                data.get("context")
                or data.get("chunk_text")
                or data.get("text")
                or ""
            )
        report = (
            data.get("document") or data.get("report") or data.get("report_name") or ""
        )
        question = data.get("question") or ""
        
        gt_entry = {
            "score": float(score) if score else 0.0,
            "text": str(text),
            "report": str(report),
            "question": str(question),
        }
        
        gt_by_query[query_id][chunk_id] = gt_entry
        
        # Also index by (report, question) pair for fallback lookup
        # Normalize report and question to match the normalization used later
        normalized_report = " ".join(str(report).strip().split())
        normalized_question = " ".join(str(question).strip().split())
        if normalized_report and normalized_question:
            if normalized_report not in gt_by_report_question:
                gt_by_report_question[normalized_report] = {}
            if normalized_question not in gt_by_report_question[normalized_report]:
                gt_by_report_question[normalized_report][normalized_question] = {}
            gt_by_report_question[normalized_report][normalized_question][chunk_id] = gt_entry
    
    rows: List[Dict] = []

    # Group benchmark results by query_id (report/question pair)
    # This matches the evaluation logic: group by query_id, sort by similarity score, take top-K
    benchmark_by_query: Dict[str, List] = {}  # query_id -> [all results for this query]
    for result in benchmark_dataset.results:
        query_id = result.get_query_id()
        if not query_id:
            continue
        benchmark_by_query.setdefault(query_id, []).append(result)
    
    # Helper function to get similarity score for ranking
    def get_similarity_score(r):
        data = r.data
        # Use relevant_text_sim as priority for ranking (similarity between retrieved chunk and relevant part)
        # Note: sim_text_relevance is NOT used here - it's an expert-annotated label, not a ranking score
        sim_score = (
            data.get("relevant_text_sim")
            or r.get_score()
            or data.get("score")
            or data.get("relevance_score")
            or 0.0
        )
        return float(sim_score) if sim_score else 0.0
    
    # Group queries by report_name, then by question
    # Structure: report_name -> question -> [query_ids for that (report, question) pair]
    # query_id is typically in format "report|||question" or similar
    queries_by_report_and_question: Dict[str, Dict[str, List[str]]] = {}  # report -> question -> [query_ids]
    
    for query_id, benchmark_results in benchmark_by_query.items():
        # Try to extract report/question from query_id first (common format: "report|||question")
        report_name = ""
        question_text = ""
        
        if "|||" in query_id:
            parts = query_id.split("|||", 1)
            report_name = parts[0] if len(parts) > 0 else ""
            question_text = parts[1] if len(parts) > 1 else ""
        else:
            # Fallback: get from ground truth
            gt_data = gt_by_query.get(query_id, {})
            first_gt = next(iter(gt_data.values())) if gt_data else {}
            report_name = first_gt.get("report", "")
            question_text = first_gt.get("question", "")
        
        # If still empty, try to get from benchmark data
        if not report_name or not question_text:
            sample_result = benchmark_results[0] if benchmark_results else None
            if sample_result:
                data = sample_result.data
                if not report_name:
                    report_name = (
                        data.get("report")
                        or data.get("document")
                        or data.get("report_name")
                        or ""
                    )
                if not question_text:
                    question_text = data.get("question") or ""
        
        if not report_name or not question_text:
            # Skip if we can't determine report/question
            continue
        
        # Normalize report_name and question_text to avoid duplicates due to whitespace/formatting
        # Remove leading/trailing whitespace and normalize internal whitespace
        report_name = " ".join(report_name.strip().split())
        question_text = " ".join(question_text.strip().split())
        
        if report_name not in queries_by_report_and_question:
            queries_by_report_and_question[report_name] = {}
        if question_text not in queries_by_report_and_question[report_name]:
            queries_by_report_and_question[report_name][question_text] = []
        queries_by_report_and_question[report_name][question_text].append(query_id)
    
    # Process in order: report (outer loop) -> question (middle loop) -> top-K chunks (inner loop)
    # This ensures report_name stays constant until all questions are done,
    # and question stays constant until all top-K chunks are shown
    processed_pairs: Dict[tuple, bool] = {}  # Track which pairs have been processed
    
    for report_name in sorted(queries_by_report_and_question.keys()):
        for question_text in sorted(queries_by_report_and_question[report_name].keys()):
            pair_key = (report_name, question_text)
            
            # Skip if we've already processed this exact pair (safeguard against duplicates)
            if pair_key in processed_pairs:
                continue  # Skip this pair - already processed
            
            processed_pairs[pair_key] = True
            query_ids = queries_by_report_and_question[report_name][question_text]
            
            # Check if there's any ground truth for this (report, question) pair
            # If no ground truth exists, skip this pair (can't evaluate without ground truth)
            report_gt_data = gt_by_report_question.get(report_name, {})
            question_gt_data = report_gt_data.get(question_text, {})
            if not question_gt_data:
                # No ground truth for this (report, question) pair - skip it
                logger.debug(
                    f"Skipping (report, question) pair with no ground truth: "
                    f"report='{report_name}', question='{question_text[:50]}...'"
                )
                continue
            
            # For this (report, question) pair, collect all benchmark results
            all_results_for_pair = []
            for query_id in query_ids:
                all_results_for_pair.extend(benchmark_by_query[query_id])
            
            # Deduplicate by (chunk_id, relevant_part_id) - this allows the same chunk to appear
            # multiple times if it matches different relevant parts, but prevents duplicates
            # when it matches the same relevant part or has no relevant part
            chunk_and_part_to_best_result: Dict[tuple, any] = {}
            for result in all_results_for_pair:
                chunk_id = result.get_chunk_id() or ""
                if not chunk_id:
                    continue
                
                data = result.data
                relevant_part_id = data.get("relevant_part_id") or ""
                # Use empty string for "no relevant part" to group those together
                dedup_key = (chunk_id, str(relevant_part_id))
                
                sim_score = get_similarity_score(result)
                if dedup_key not in chunk_and_part_to_best_result:
                    chunk_and_part_to_best_result[dedup_key] = result
                else:
                    # Keep the one with higher similarity score
                    existing_score = get_similarity_score(chunk_and_part_to_best_result[dedup_key])
                    if sim_score > existing_score:
                        chunk_and_part_to_best_result[dedup_key] = result
            
            # Sort by similarity score (descending) and take top-K
            deduplicated_results = list(chunk_and_part_to_best_result.values())
            sorted_results = sorted(
                deduplicated_results, key=get_similarity_score, reverse=True
            )[:top_k]
            
            # Get a representative query_id for this pair (for display purposes)
            query_id = query_ids[0]
            
            # Output all top-K chunks for this (report, question) pair
            for local_rank, r in enumerate(sorted_results, start=1):
                data = r.data
                retrieved_chunk_id = r.get_chunk_id() or ""  # This is the retrieved paragraph ID
                original_position = r.get_position() or 0
                
                # Get similarity score (used for ranking)
                similarity_score = get_similarity_score(r)
                
                # Get model score from benchmark dataset - should be relevant_text_sim for this chunk
                model_score = data.get("relevant_text_sim") or 0.0
                model_score = float(model_score) if model_score else 0.0
                
                chunk_text = (
                    data.get("paragraph")
                    or data.get("chunk_text")
                    or data.get("text")
                    or ""
                )
                
                # Get relevant_part_id to look up ground truth
                relevant_part_id_from_data = data.get("relevant_part_id")
                relevant_part_id = (
                    relevant_part_id_from_data
                    if relevant_part_id_from_data
                    else ""  # Don't fallback to retrieved_chunk_id - if no relevant_part_id, it means no match
                )
                
                # Get the query_id for this specific result (not the grouped one)
                result_query_id = r.get_query_id() or query_id
                
                # Look up ground truth using the result's query_id and relevant_part_id
                # The ground truth is indexed by query_id -> chunk_id (where chunk_id is the relevant part ID)
                gt_chunk = {}
                if relevant_part_id:
                    if result_query_id:
                        # Primary lookup: by query_id
                        result_gt_data = gt_by_query.get(result_query_id, {})
                        gt_chunk = result_gt_data.get(str(relevant_part_id), {})
                    
                    # Fallback lookup: by (report, question) pair if primary lookup failed
                    if not gt_chunk and report_name and question_text:
                        report_gt_data = gt_by_report_question.get(report_name, {})
                        question_gt_data = report_gt_data.get(question_text, {})
                        gt_chunk = question_gt_data.get(str(relevant_part_id), {})
                
                # If still no match by ID, but we have a (report, question) pair,
                # get the most relevant part (highest score) for this pair (as user requested:
                # "retrieve the info about relevant part from ground truth for each question/report pair")
                if not gt_chunk and report_name and question_text:
                    report_gt_data = gt_by_report_question.get(report_name, {})
                    question_gt_data = report_gt_data.get(question_text, {})
                    if question_gt_data:
                        # Use the relevant part with the highest score for this (report, question) pair
                        best_chunk_id = max(
                            question_gt_data.keys(),
                            key=lambda cid: question_gt_data[cid].get("score", 0.0)
                        )
                        gt_chunk = question_gt_data[best_chunk_id]
                
                relevant_part_text = gt_chunk.get("text", "")
                
                # Get relevance from benchmarking dataset (not ground truth)
                # Check for relevance_label or relevance column in benchmark data
                benchmark_relevance = (
                    data.get("relevance_label")
                    or data.get("relevance")
                    or data.get("label")
                    or 0.0
                )
                # Convert to numeric if it's a string
                if isinstance(benchmark_relevance, str):
                    try:
                        benchmark_relevance = float(benchmark_relevance)
                    except (ValueError, TypeError):
                        benchmark_relevance = 0.0
                else:
                    benchmark_relevance = float(benchmark_relevance) if benchmark_relevance else 0.0
                
                # is_really_relevant should be true only if benchmark relevance > 0
                is_really_relevant = benchmark_relevance > 0
                
                rows.append(
                    {
                        "report_name": report_name,
                        "question_id": query_id,  # Keep query_id for reference
                        "question": question_text,
                        "relevant_part_text": relevant_part_text,
                        "retrieved_chunk_text": str(chunk_text),
                        # 1..K rank within top-K for this (report, question) pair
                        "position_in_top_k": local_rank,
                        # Original retrieval rank (if available)
                        "retrieval_rank": original_position,
                        "model_score": model_score,
                        "is_really_relevant": is_really_relevant,
                        "chunk_id": retrieved_chunk_id,  # Store the retrieved paragraph ID
                    }
                )
    
    df = pd.DataFrame(rows)
    # No need to sort - rows are already in the correct order:
    # report (outer loop) -> question (middle loop) -> position_in_top_k (inner loop)
    
    logger.info(f"Built error-analysis dataframe from flexible datasets with {len(df)} rows")
    return df


