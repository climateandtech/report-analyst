import json
import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

from ...models.benchmark import (
    BenchmarkDataset,
    BenchmarkDatasetContent,
    BenchmarkEvaluation,
    DatasetType,
    EvaluationMetrics,
    RetrievalConfig,
    RetrievalResultsDataset,
)

logger = logging.getLogger(__name__)


class EvaluationEngine:
    """Engine for evaluating retrieval performance against benchmark datasets"""

    def __init__(self):
        self.default_k_values = [1, 3, 5, 10]

    def evaluate_retrieval(
        self,
        dataset: BenchmarkDatasetContent,
        retrieval_results: Dict[str, List[Dict]],
        config: RetrievalConfig,
        k_values: Optional[List[int]] = None,
    ) -> EvaluationMetrics:
        """
        Evaluate retrieval results against ground truth

        Args:
            dataset: Benchmark dataset with ground truth
            retrieval_results: Dict mapping question_id to list of retrieved chunks
            config: Retrieval configuration used
            k_values: List of K values to compute metrics for

        Returns:
            EvaluationMetrics with computed scores
        """
        if k_values is None:
            k_values = self.default_k_values

        logger.info(f"Evaluating retrieval for {len(dataset.questions)} questions")

        # Collect results per question
        question_results = []
        for question in dataset.questions:
            if question.question_id not in retrieval_results:
                logger.warning(
                    f"No retrieval results for question {question.question_id}"
                )
                continue

            retrieved_chunks = retrieval_results[question.question_id]
            ground_truth = {
                chunk.chunk_id: chunk.relevance_score
                for chunk in question.ground_truth_chunks
            }

            result = self._evaluate_single_question(
                retrieved_chunks, ground_truth, k_values
            )
            question_results.append(result)

        # Aggregate metrics
        return self._aggregate_metrics(question_results, k_values)

    def _evaluate_single_question(
        self,
        retrieved_chunks: List[Dict],
        ground_truth: Dict[str, float],
        k_values: List[int],
    ) -> Dict:
        """Evaluate a single question's retrieval results"""

        # Extract relevant part IDs in retrieval order
        # Note: "id" field contains relevant_part_id (for matching to ground truth)
        # chunk_id is the unique paragraph identifier (for reference)
        # Multiple retrieved paragraphs can legitimately match the same relevant part
        retrieved_ids_raw = [
            chunk.get("id", chunk.get("chunk_id", "")) for chunk in retrieved_chunks
        ]

        # Deduplicate relevant parts while preserving order (keep first occurrence)
        # This ensures each unique relevant part is counted only once in recall/NDCG
        # Multiple retrieved paragraphs matching the same relevant part is valid, but we only
        # count the relevant part once to prevent recall > 1.0
        seen = set()
        retrieved_ids = []
        for relevant_part_id in retrieved_ids_raw:
            if relevant_part_id not in seen:
                retrieved_ids.append(relevant_part_id)
                seen.add(relevant_part_id)

        # #region agent log
        log_path = Path("/home/yauheni/Documents/my_main/.cursor/debug.log")
        try:
            with open(log_path, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "location": "evaluation_engine.py:_evaluate_single_question:82",
                            "message": "Retrieved relevant part IDs analysis (after deduplication)",
                            "data": {
                                "total_retrieved_paragraphs": len(retrieved_chunks),
                                "total_relevant_parts_before": len(retrieved_ids_raw),
                                "total_relevant_parts_after": len(retrieved_ids),
                                "unique_relevant_parts": len(set(retrieved_ids)),
                                "has_duplicates_before": len(retrieved_ids_raw)
                                != len(set(retrieved_ids_raw)),
                                "has_duplicates_after": len(retrieved_ids)
                                != len(set(retrieved_ids)),
                                "retrieved_relevant_part_ids_sample": retrieved_ids[:10],
                                "ground_truth_keys_count": len(ground_truth),
                                "ground_truth_keys_sample": list(ground_truth.keys())[
                                    :5
                                ],
                            },
                            "timestamp": int(__import__("time").time() * 1000),
                            "runId": "new-alignment",
                            "hypothesisId": "A",
                        }
                    )
                    + "\n"
                )
        except Exception:
            pass
        # #endregion

        # Get relevance scores for retrieved chunks (after deduplication)
        retrieved_relevance = [
            ground_truth.get(chunk_id, 0.0) for chunk_id in retrieved_ids
        ]

        # Binary relevance (relevant if score > 0)
        binary_relevance = [1 if score > 0 else 0 for score in retrieved_relevance]

        # Total relevant chunks in ground truth
        total_relevant = sum(1 for score in ground_truth.values() if score > 0)

        result = {
            "retrieved_ids": retrieved_ids,
            "retrieved_relevance": retrieved_relevance,
            "binary_relevance": binary_relevance,
            "total_relevant": total_relevant,
            "precision_at_k": {},
            "recall_at_k": {},
            "f1_at_k": {},
            "ndcg_at_k": {},
            "reciprocal_rank": 0.0,
            "average_precision": 0.0,
        }

        # Compute metrics at different K values
        # NOTE: Metrics should be calculated for ALL k values, even if k > len(retrieved_ids)
        # When k > len(retrieved_ids), recall@k equals the maximum recall (all relevant items found)
        # and precision@k is calculated with k as denominator (correctly lower when fewer items retrieved)
        for k in k_values:
            precision_k = self._precision_at_k(binary_relevance, k)
            recall_k = self._recall_at_k(binary_relevance, total_relevant, k)
            f1_k = self._f1_at_k(precision_k, recall_k)
            ndcg_k = self._ndcg_at_k(retrieved_relevance, ground_truth, k)
            result["precision_at_k"][k] = precision_k
            result["recall_at_k"][k] = recall_k
            result["f1_at_k"][k] = f1_k
            result["ndcg_at_k"][k] = ndcg_k

            # #region agent log
            log_path = Path("/home/yauheni/Documents/my_main/.cursor/debug.log")
            try:
                with open(log_path, "a") as f:
                    f.write(
                        json.dumps(
                            {
                                "location": "evaluation_engine.py:_evaluate_single_question:162",
                                "message": f"Metrics at K={k} (using relevant_part_id matching)",
                                "data": {
                                    "k": k,
                                    "precision": precision_k,
                                    "recall": recall_k,
                                    "f1": f1_k,
                                    "ndcg": ndcg_k,
                                    "relevant_at_k": sum(binary_relevance[:k]),
                                    "total_relevant": total_relevant,
                                    "retrieved_at_k": min(k, len(retrieved_ids)),
                                    "total_retrieved": len(retrieved_ids),
                                    "k_greater_than_retrieved": k > len(retrieved_ids),
                                    "has_metrics_gt_1": any(
                                        [
                                            precision_k > 1,
                                            recall_k > 1,
                                            f1_k > 1,
                                            ndcg_k > 1,
                                        ]
                                    ),
                                },
                                "timestamp": int(__import__("time").time() * 1000),
                                "runId": "recall-debug",
                                "hypothesisId": "A",
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass
            # #endregion

        # Compute MRR and MAP
        result["reciprocal_rank"] = self._reciprocal_rank(binary_relevance)
        result["average_precision"] = self._average_precision(binary_relevance)

        return result

    def _precision_at_k(self, binary_relevance: List[int], k: int) -> float:
        """Compute precision at K"""
        if k == 0:
            return 0.0
        relevant_at_k = sum(binary_relevance[:k])
        return relevant_at_k / k

    def _recall_at_k(
        self, binary_relevance: List[int], total_relevant: int, k: int
    ) -> float:
        """Compute recall at K"""
        if total_relevant == 0:
            return 0.0
        relevant_at_k = sum(binary_relevance[:k])
        return relevant_at_k / total_relevant

    def _f1_at_k(self, precision: float, recall: float) -> float:
        """Compute F1 score from precision and recall"""
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)

    def _ndcg_at_k(
        self, retrieved_relevance: List[float], ground_truth: Dict[str, float], k: int
    ) -> float:
        """Compute Normalized Discounted Cumulative Gain at K"""
        if k == 0:
            return 0.0

        # DCG at K
        dcg = 0.0
        for i in range(min(k, len(retrieved_relevance))):
            if i == 0:
                dcg += retrieved_relevance[i]
            else:
                dcg += retrieved_relevance[i] / np.log2(i + 1)

        # Ideal DCG at K (sort ground truth scores in descending order)
        ideal_scores = sorted(ground_truth.values(), reverse=True)
        idcg = 0.0
        for i in range(min(k, len(ideal_scores))):
            if i == 0:
                idcg += ideal_scores[i]
            else:
                idcg += ideal_scores[i] / np.log2(i + 1)

        # #region agent log
        log_path = Path("/home/yauheni/Documents/my_main/.cursor/debug.log")
        try:
            with open(log_path, "a") as f:
                f.write(
                    json.dumps(
                        {
                            "location": "evaluation_engine.py:_ndcg_at_k:179",
                            "message": "NDCG calculation details (using relevant_part_id matching)",
                            "data": {
                                "k": k,
                                "dcg": dcg,
                                "idcg": idcg,
                                "ndcg": dcg / idcg if idcg > 0 else 0.0,
                                "retrieved_relevance_sample": retrieved_relevance[:k],
                                "ideal_scores_sample": ideal_scores[:k],
                                "ground_truth_unique_count": len(ground_truth),
                                "ndcg_gt_1": (dcg / idcg if idcg > 0 else 0.0) > 1.0,
                            },
                            "timestamp": int(__import__("time").time() * 1000),
                            "runId": "post-fix",
                            "hypothesisId": "C",
                        }
                    )
                    + "\n"
                )
        except Exception:
            pass
        # #endregion

        if idcg == 0:
            return 0.0

        return dcg / idcg

    def _reciprocal_rank(self, binary_relevance: List[int]) -> float:
        """Compute reciprocal rank (1/rank of first relevant item)"""
        for i, rel in enumerate(binary_relevance):
            if rel == 1:
                return 1.0 / (i + 1)
        return 0.0

    def _average_precision(self, binary_relevance: List[int]) -> float:
        """Compute average precision"""
        if not any(binary_relevance):
            return 0.0

        ap = 0.0
        relevant_count = 0

        for i, rel in enumerate(binary_relevance):
            if rel == 1:
                relevant_count += 1
                precision_at_i = relevant_count / (i + 1)
                ap += precision_at_i

        total_relevant = sum(binary_relevance)
        return ap / total_relevant if total_relevant > 0 else 0.0

    def _aggregate_metrics(
        self, question_results: List[Dict], k_values: List[int]
    ) -> EvaluationMetrics:
        """Aggregate metrics across all questions"""
        if not question_results:
            return EvaluationMetrics()

        metrics = EvaluationMetrics()

        # Aggregate precision, recall, F1, and NDCG at K
        for k in k_values:
            precisions = [r["precision_at_k"].get(k, 0.0) for r in question_results]
            recalls = [r["recall_at_k"].get(k, 0.0) for r in question_results]
            f1s = [r["f1_at_k"].get(k, 0.0) for r in question_results]
            ndcgs = [r["ndcg_at_k"].get(k, 0.0) for r in question_results]

            # #region agent log
            log_path = Path("/home/yauheni/Documents/my_main/.cursor/debug.log")
            try:
                with open(log_path, "a") as f:
                    f.write(
                        json.dumps(
                            {
                                "location": "evaluation_engine.py:_aggregate_metrics:331",
                                "message": f"Aggregating metrics at K={k}",
                                "data": {
                                    "k": k,
                                    "num_questions": len(question_results),
                                    "precisions_count": len(precisions),
                                    "recalls_count": len(recalls),
                                    "precisions_with_value": sum(1 for p in precisions if p > 0),
                                    "recalls_with_value": sum(1 for r in recalls if r > 0),
                                    "precisions_sample": precisions[:5],
                                    "recalls_sample": recalls[:5],
                                    "mean_precision": np.mean(precisions),
                                    "mean_recall": np.mean(recalls),
                                    "recall_is_decreasing": False,  # Will check in analysis
                                },
                                "timestamp": int(__import__("time").time() * 1000),
                                "runId": "recall-debug",
                                "hypothesisId": "B",
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass
            # #endregion

            metrics.precision_at_k[k] = np.mean(precisions)
            metrics.recall_at_k[k] = np.mean(recalls)
            metrics.f1_at_k[k] = np.mean(f1s)
            metrics.ndcg_at_k[k] = np.mean(ndcgs)

        # Aggregate MRR and MAP
        reciprocal_ranks = [r["reciprocal_rank"] for r in question_results]
        average_precisions = [r["average_precision"] for r in question_results]

        metrics.mean_reciprocal_rank = np.mean(reciprocal_ranks)
        metrics.mean_average_precision = np.mean(average_precisions)

        logger.info(
            f"Evaluation complete. MAP: {metrics.mean_average_precision:.3f}, MRR: {metrics.mean_reciprocal_rank:.3f}"
        )

        return metrics

    def compare_evaluations(
        self, eval1: EvaluationMetrics, eval2: EvaluationMetrics
    ) -> Dict[str, float]:
        """Compare two evaluations and return improvement metrics"""
        comparison = {}

        # Compare MAP and MRR
        comparison["map_improvement"] = (
            eval2.mean_average_precision - eval1.mean_average_precision
        )
        comparison["mrr_improvement"] = (
            eval2.mean_reciprocal_rank - eval1.mean_reciprocal_rank
        )

        # Compare metrics at K
        for k in eval1.precision_at_k.keys():
            if k in eval2.precision_at_k:
                comparison[f"precision_at_{k}_improvement"] = (
                    eval2.precision_at_k[k] - eval1.precision_at_k[k]
                )
                comparison[f"recall_at_{k}_improvement"] = (
                    eval2.recall_at_k[k] - eval1.recall_at_k[k]
                )
                comparison[f"f1_at_{k}_improvement"] = (
                    eval2.f1_at_k[k] - eval1.f1_at_k[k]
                )
                comparison[f"ndcg_at_{k}_improvement"] = (
                    eval2.ndcg_at_k[k] - eval1.ndcg_at_k[k]
                )

        return comparison

    def compare_flexible_datasets(
        self,
        reference_dataset: BenchmarkDataset,
        input_dataset: BenchmarkDataset,
        k_values: Optional[List[int]] = None,
    ) -> EvaluationMetrics:
        """
        Compare two flexible benchmark datasets (supports both IR and IE).

        The reference dataset is treated as ground truth (e.g., "climretrieve", "chatreport").
        The input dataset contains the actual results to evaluate.

        For IR datasets: Compares retrieved chunks (by chunk_id and position).
        For IE datasets: Compares answers/analysis (by query_id, comparing text similarity).

        Args:
            reference_dataset: Reference dataset (ground truth)
            input_dataset: Input dataset (actual results) to evaluate
            k_values: List of K values to compute metrics for (only used for IR)

        Returns:
            EvaluationMetrics comparing input_dataset against reference_dataset
        """
        if reference_dataset.dataset_type != input_dataset.dataset_type:
            logger.warning(
                f"Dataset type mismatch: reference={reference_dataset.dataset_type.value}, "
                f"input={input_dataset.dataset_type.value}. Attempting comparison anyway."
            )

        if reference_dataset.dataset_type == DatasetType.INFORMATION_RETRIEVAL:
            return self._compare_ir_datasets(reference_dataset, input_dataset, k_values)
        elif reference_dataset.dataset_type == DatasetType.INFORMATION_EXTRACTION:
            return self._compare_ie_datasets(reference_dataset, input_dataset)
        else:
            raise ValueError(
                f"Unsupported dataset type: {reference_dataset.dataset_type}"
            )

    def _compare_ir_datasets(
        self,
        reference_dataset: BenchmarkDataset,
        input_dataset: BenchmarkDataset,
        k_values: Optional[List[int]] = None,
    ) -> EvaluationMetrics:
        """Compare two Information Retrieval datasets"""
        if k_values is None:
            k_values = self.default_k_values

        # Get common queries
        reference_queries = set(reference_dataset.get_unique_queries())
        input_queries = set(input_dataset.get_unique_queries())
        common_queries = reference_queries.intersection(input_queries)

        if not common_queries:
            logger.warning(
                "No common queries found between reference and input datasets"
            )
            return EvaluationMetrics()

        logger.info(f"Found {len(common_queries)} common queries for IR comparison")

        # Collect results per question
        question_results = []
        for query_id in common_queries:
            # Get reference results (ground truth)
            reference_results = reference_dataset.get_results_by_query(query_id)
            reference_results = sorted(
                reference_results, key=lambda x: x.get_position() or 999
            )

            # Build ground truth mapping: chunk_id -> relevance_score
            ground_truth = {}
            duplicate_chunk_ids = []
            for i, ref_result in enumerate(reference_results):
                chunk_id = ref_result.get_chunk_id()
                if chunk_id:
                    if chunk_id in ground_truth:
                        duplicate_chunk_ids.append(chunk_id)
                    score = ref_result.get_score()
                    # Use score if available, otherwise use inverse position
                    relevance_score = (
                        score if score is not None else max(0.0, 1.0 - (i * 0.1))
                    )
                    ground_truth[chunk_id] = relevance_score

            # #region agent log
            log_path = Path("/home/yauheni/Documents/my_main/.cursor/debug.log")
            try:
                with open(log_path, "a") as f:
                    f.write(
                        json.dumps(
                            {
                                "location": "evaluation_engine.py:_compare_ir_datasets:351",
                                "message": "Ground truth mapping analysis",
                                "data": {
                                    "query_id": query_id,
                                    "reference_results_count": len(reference_results),
                                    "ground_truth_unique_chunks": len(ground_truth),
                                    "has_duplicate_chunk_ids": len(duplicate_chunk_ids)
                                    > 0,
                                    "duplicate_chunk_ids": duplicate_chunk_ids[:5],
                                    "ground_truth_scores_sample": dict(
                                        list(ground_truth.items())[:5]
                                    ),
                                },
                                "timestamp": int(__import__("time").time() * 1000),
                                "runId": "new-alignment",
                                "hypothesisId": "D",
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass
            # #endregion

            # Get input results (actual retrieval)
            input_results = input_dataset.get_results_by_query(query_id)
            input_results = sorted(input_results, key=lambda x: x.get_position() or 999)

            # Convert to format expected by _evaluate_single_question
            # Use relevant_part_id for matching to ground truth (if available), otherwise fallback to chunk_id
            retrieved_chunks = []
            retrieved_chunk_ids_list = []
            for result in input_results:
                chunk_id = result.get_chunk_id()  # Unique paragraph identifier
                relevant_part_id = result.get(
                    "relevant_part_id"
                )  # For matching to ground truth
                # Fallback: if no relevant_part_id, use chunk_id (backward compatibility)
                match_id = relevant_part_id if relevant_part_id else chunk_id
                score = result.get_score() or 0.0
                position = result.get_position() or 999

                chunk_dict = {
                    "id": match_id
                    or f"unknown_{position}",  # Use relevant_part_id for matching
                    "chunk_id": chunk_id
                    or f"unknown_{position}",  # Keep original chunk_id for reference
                    "relevant_part_id": match_id
                    or f"unknown_{position}",  # Store for logging
                    "score": score,
                    "position": position,
                }
                retrieved_chunks.append(chunk_dict)
                retrieved_chunk_ids_list.append(match_id or f"unknown_{position}")

            # #region agent log
            log_path = Path("/home/yauheni/Documents/my_main/.cursor/debug.log")
            try:
                with open(log_path, "a") as f:
                    f.write(
                        json.dumps(
                            {
                                "location": "evaluation_engine.py:_compare_ir_datasets:370",
                                "message": "Retrieved chunks analysis",
                                "data": {
                                    "query_id": query_id,
                                    "input_results_count": len(input_results),
                                    "retrieved_chunks_count": len(retrieved_chunks),
                                    "retrieved_chunk_ids_unique": len(
                                        set(retrieved_chunk_ids_list)
                                    ),
                                    "retrieved_chunk_ids_total": len(
                                        retrieved_chunk_ids_list
                                    ),
                                    "has_duplicate_retrieved_ids": len(
                                        set(retrieved_chunk_ids_list)
                                    )
                                    < len(retrieved_chunk_ids_list),
                                    "duplicate_ids_sample": [
                                        x
                                        for x in set(retrieved_chunk_ids_list)
                                        if retrieved_chunk_ids_list.count(x) > 1
                                    ][:5],
                                },
                                "timestamp": int(__import__("time").time() * 1000),
                                "runId": "new-alignment",
                                "hypothesisId": "E",
                            }
                        )
                        + "\n"
                    )
            except Exception:
                pass
            # #endregion

            # Evaluate this question
            result = self._evaluate_single_question(
                retrieved_chunks, ground_truth, k_values
            )
            question_results.append(result)

        # Aggregate metrics
        return self._aggregate_metrics(question_results, k_values)

    def _compare_ie_datasets(
        self, reference_dataset: BenchmarkDataset, input_dataset: BenchmarkDataset
    ) -> EvaluationMetrics:
        """
        Compare two Information Extraction datasets.

        Compares answers/analysis text using similarity metrics.
        For structured fields (categories, extracted values), uses exact match.
        """
        # Get common queries
        reference_queries = set(reference_dataset.get_unique_queries())
        input_queries = set(input_dataset.get_unique_queries())
        common_queries = reference_queries.intersection(input_queries)

        if not common_queries:
            logger.warning(
                "No common queries found between reference and input datasets"
            )
            return EvaluationMetrics()

        logger.info(f"Found {len(common_queries)} common queries for IE comparison")

        # For IE, we compare answers/analysis per query
        # Metrics: Exact match, F1 (token-level), BLEU, ROUGE, etc.
        exact_matches = 0
        total_queries = len(common_queries)

        # Simple comparison: exact match for now
        # TODO: Add more sophisticated metrics (F1, BLEU, ROUGE, semantic similarity)
        for query_id in common_queries:
            reference_results = reference_dataset.get_results_by_query(query_id)
            input_results = input_dataset.get_results_by_query(query_id)

            if not reference_results or not input_results:
                continue

            # Get first result for each (assuming one answer per query)
            ref_answer = reference_results[0].get_answer()
            input_answer = input_results[0].get_answer()

            if ref_answer and input_answer:
                # Normalize and compare
                ref_normalized = ref_answer.strip().lower()
                input_normalized = input_answer.strip().lower()

                if ref_normalized == input_normalized:
                    exact_matches += 1

        # Create metrics (simplified for IE)
        metrics = EvaluationMetrics()
        if total_queries > 0:
            exact_match_rate = exact_matches / total_queries
            # For IE, we use exact_match_rate as the primary metric
            # Map to precision@1 for consistency with IR metrics
            metrics.precision_at_k[1] = exact_match_rate
            metrics.mean_average_precision = exact_match_rate
            metrics.mean_reciprocal_rank = (
                exact_match_rate if exact_matches > 0 else 0.0
            )

        logger.info(
            f"IE comparison complete. Exact match rate: {exact_matches}/{total_queries} = {metrics.precision_at_k.get(1, 0.0):.3f}"
        )

        return metrics

    def compare_datasets(
        self,
        reference_dataset: RetrievalResultsDataset,
        input_dataset: RetrievalResultsDataset,
        k_values: Optional[List[int]] = None,
        match_on_chunk_id: bool = True,
    ) -> EvaluationMetrics:
        """
        Compare two retrieval results datasets.

        The reference dataset is treated as ground truth (e.g., "climretrieve").
        The input dataset contains the actual retrieval results to evaluate.

        Args:
            reference_dataset: Reference dataset (ground truth) - e.g., climretrieve
            input_dataset: Input dataset (actual retrieval results) to evaluate
            k_values: List of K values to compute metrics for
            match_on_chunk_id: If True, match chunks by chunk_id. If False, match by position only.

        Returns:
            EvaluationMetrics comparing input_dataset against reference_dataset
        """
        if k_values is None:
            k_values = self.default_k_values

        logger.info(
            f"Comparing datasets: reference='{reference_dataset.dataset_id}' vs input='{input_dataset.dataset_id}'"
        )

        # Get common queries
        reference_queries = set(reference_dataset.get_unique_queries())
        input_queries = set(input_dataset.get_unique_queries())
        common_queries = reference_queries.intersection(input_queries)

        if not common_queries:
            logger.warning(
                "No common queries found between reference and input datasets"
            )
            return EvaluationMetrics()

        logger.info(f"Found {len(common_queries)} common queries")

        # Collect results per question
        question_results = []
        for query_id in common_queries:
            # Get reference results (ground truth)
            reference_results = reference_dataset.get_results_by_query(query_id)
            # Sort by position to get ground truth order
            reference_results = sorted(reference_results, key=lambda x: x.position)

            # Build ground truth mapping: chunk_id -> relevance_score
            # Use position as relevance score (higher position = lower relevance)
            # Or use actual score if available
            ground_truth = {}
            for i, ref_result in enumerate(reference_results):
                chunk_id = ref_result.chunk_id
                # Use score if available, otherwise use inverse position (1.0 for position 1, 0.9 for position 2, etc.)
                relevance_score = (
                    ref_result.score
                    if ref_result.score > 0
                    else max(0.0, 1.0 - (i * 0.1))
                )
                ground_truth[chunk_id] = relevance_score

            # Get input results (actual retrieval)
            input_results = input_dataset.get_results_by_query(query_id)
            # Sort by position
            input_results = sorted(input_results, key=lambda x: x.position)

            # Convert to format expected by _evaluate_single_question
            retrieved_chunks = []
            for result in input_results:
                chunk_dict = {
                    "id": result.chunk_id,
                    "chunk_id": result.chunk_id,
                    "score": result.score,
                    "position": result.position,
                }
                retrieved_chunks.append(chunk_dict)

            # Evaluate this question
            result = self._evaluate_single_question(
                retrieved_chunks, ground_truth, k_values
            )
            question_results.append(result)

        # Aggregate metrics
        return self._aggregate_metrics(question_results, k_values)
