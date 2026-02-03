#!/usr/bin/env python3
"""
Script to embed chunks from ground truth dataset, compare to criteria embeddings,
and evaluate against ground truth labels (relevance/usefulness).

This script:
1. Loads ground truth dataset (test_data_extended_V6)
2. Embeds chunks and criteria descriptions
3. Computes similarity scores between chunks and criteria
4. Evaluates similarity scores against ground truth labels
5. Calculates metrics: F1@K, nDCG@K, Precision@K, Recall@K
6. Shows confusion matrix (TP, TN, FP, FN)

Usage:
    python3 scripts/s4m_evaluate_embeddings_against_ground_truth.py \
        --input "data/s4m/labels/test_data_extended_V6.xlsx - Sheet1.csv" \
        --ground-truth-col "relevance" \
        --output "data/s4m/results/embedding_evaluation_results.csv" \
        --k 1,3,5,10 \
        --threshold 1.0
    
    Note: Use .csv extension for CSV format output, .txt for text format.
"""

import sys
import logging
from pathlib import Path
from typing import List, Optional
import argparse
import json
import asyncio

import pandas as pd
from dotenv import load_dotenv
from llama_index.core.llms import ChatMessage, MessageRole

# Setup project path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables (checks .env, ok.env.local, etc.)
load_dotenv()  # Loads .env by default
load_dotenv("ok.env.local")  # Also load ok.env.local if it exists

from report_analyst.core.benchmark.s4m_metrics import evaluate_s4m_classification, S4MMetrics
from report_analyst.core.llm_providers import get_llm

# Import embedding functions from s4m_embed_and_compare_criteria to avoid duplication
from report_analyst.core.benchmark.s4m_embed_and_compare_criteria import (
    load_chunks_and_criteria,
    get_analyzer,
    embed_texts,
    compute_similarity_per_row,
    load_embeddings_from_csv
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_llm_scoring_prompt(
    criteria: str,
    description: str,
    text_chunk: str
) -> str:
    """
    Create the LLM prompt for scoring relevance/usefulness.
    
    Args:
        criteria: The criteria name
        description: The criteria description
        text_chunk: The text chunk to evaluate
        
    Returns:
        Formatted prompt string
    """
    # Clean the text chunk (remove extra whitespace)
    text_chunk_clean = " ".join(text_chunk.split())
    
    return f"""<s>[INST] You are a sustainability analyst, and your task is to rate the relevance of a text towards given criteria. You are given a question definition, a paragraph, and need to answer the following question.<question>: Does this text contain information about {criteria}? If it does, is it relevant and or usefull to gain an understanding of the companies sustainability activities?<question_definition>: {description}<paragraph>: {text_chunk_clean}Does the <paragraph> contain relevant information for <question>? Is <paragraph> useful for giving an answering to <question>?Relevance (0-2): Does the paragraph contain information about {criteria}? This means:- 0 = (Not Relevant): The information has little to no connection to the {criteria}. It is off-topic, irrelevant to the specific {criteria}, or consists of general background information that doesn't contribute to the analysis of the {criteria}.- 1 = (Moderately Relevant): The information has some connection to the {criteria} but is not as direct or central. It may contain related keywords or provide background context, but it doesn't fully address the core concepts of the {criteria}.- 2 = (Highly Relevant): The information has a strong and direct connection to the {criteria}. It contains specific keywords, concepts, or themes that are central to the analysis of the {criteria}. The content is explicitly describing the {criteria} or highly related and on-topic.Usefulness (0-2): How useful is this information for understanding {criteria}? This means:- 0 = (Not Useful): The information has little to no practical value. It lacks sufficient content, specific actions, solutions or context to be useful for analysis of the {criteria}. It may be a vague statement, a headline without details, or information that is already readily available elsewhere.- 1 = (Moderately Useful): The information offers some practical value but is less specific or actionable. It may provide general context or mention relevant concepts, but it lacks concrete details, specific actions, solutions or data that can be easily utilized to understand the company's sustainability efforts for the {criteria}.- 2 = (Highly Useful): The information provides significant practical value. It contains clear, actionable insights, specific numbers, concrete achievements, solutions, or detailed plans that can be directly used. The content offers tangible value for understanding the company's efforts related to the {criteria}.SCORING PRIORITIES:- Quantifiable measures and specific technologies = higher scores- Vague statements and distant aspirations = lower scores- Consider operational implementations and concrete near-term plansYou must respond with valid JSON only. Use this exact format:{{"question": "Does this text contain information about {criteria}?", "question_definition": "{description}", "relevance": 0, "usefulness": 0, "relevance_confidence": 1.0, "usefulness_confidence": 1.0}}Replace 0 with scores 0, 1, or 2 only. No negative numbers allowed. [/INST]"""


async def score_chunk_with_llm(
    llm,
    criteria: str,
    description: str,
    text_chunk: str,
    score_type: str = "relevance"
) -> int:
    """
    Score a chunk using LLM with the provided prompt template.
    
    Args:
        llm: LLM instance from get_llm()
        criteria: Criteria name
        description: Criteria description
        text_chunk: Text chunk to score
        score_type: Either "relevance" or "usefulness"
        
    Returns:
        Score (0, 1, or 2)
    """
    prompt = create_llm_scoring_prompt(criteria, description, text_chunk)
    
    try:
        # Convert prompt string to messages format (required for Ollama and some other LLMs)
        messages = [ChatMessage(role=MessageRole.USER, content=prompt)]
        
        response = await llm.achat(messages=messages)
        response_text = response.message.content.strip()
        
        # Try to parse JSON response
        # Sometimes LLM adds extra text, so try to extract JSON
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1
        if json_start >= 0 and json_end > json_start:
            response_text = response_text[json_start:json_end]
        
        result = json.loads(response_text)
        score = int(result.get(score_type, 0))
        
        # Clamp to valid range [0, 2]
        score = max(0, min(2, score))
        return score
        
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON response: {response_text[:200]}... Error: {e}")
        return 0
    except Exception as e:
        logger.warning(f"Error scoring chunk with LLM: {e}")
        return 0


async def score_chunks_with_llm_batch(
    df: pd.DataFrame,
    criteria_col: str,
    description_col: str,
    chunk_col: str,
    score_type: str = "relevance",
    model_name: str = "gpt-4o-mini",
    batch_size: int = 10
) -> pd.Series:
    """
    Score chunks using LLM in batches.
    
    Args:
        df: DataFrame with chunks and criteria
        criteria_col: Column name for criteria
        description_col: Column name for criteria description
        chunk_col: Column name for chunk text
        score_type: Either "relevance" or "usefulness"
        model_name: LLM model name (default: "gpt-4o-mini")
        batch_size: Number of chunks to process in parallel
        
    Returns:
        Series with LLM scores (0, 1, or 2)
    """
    logger.info(f"Initializing LLM model: {model_name}")
    llm = get_llm(model_name)
    
    scores = pd.Series(0, index=df.index, dtype=int)
    
    # Process in batches to avoid overwhelming the API
    total_chunks = len(df)
    logger.info(f"Scoring {total_chunks} chunks with LLM in batches of {batch_size}...")
    
    for batch_start in range(0, total_chunks, batch_size):
        batch_end = min(batch_start + batch_size, total_chunks)
        batch_df = df.iloc[batch_start:batch_end]
        
        # Create tasks for this batch
        tasks = []
        for idx, row in batch_df.iterrows():
            criteria = str(row.get(criteria_col, ""))
            description = str(row.get(description_col, ""))
            chunk_text = str(row.get(chunk_col, ""))
            
            if not chunk_text or chunk_text.strip() == "":
                continue
                
            task = score_chunk_with_llm(
                llm=llm,
                criteria=criteria,
                description=description,
                text_chunk=chunk_text,
                score_type=score_type
            )
            tasks.append((idx, task))
        
        # Execute batch
        if tasks:
            # Extract task coroutines and indices separately
            task_coros = [task for _, task in tasks]
            task_indices = [idx for idx, _ in tasks]
            
            results = await asyncio.gather(*task_coros, return_exceptions=True)
            
            # Match results with their indices
            for idx, result in zip(task_indices, results):
                if isinstance(result, Exception):
                    logger.warning(f"Error scoring chunk at index {idx}: {result}")
                    scores[idx] = 0
                elif isinstance(result, int):
                    # Result is already an integer score
                    scores[idx] = result
                else:
                    logger.warning(f"Unexpected result type for chunk at index {idx}: {type(result)}")
                    scores[idx] = 0
        
        logger.info(f"Processed {batch_end}/{total_chunks} chunks...")
    
    logger.info(f"Completed LLM scoring. Score distribution: {scores.value_counts().to_dict()}")
    return scores


def convert_similarity_to_discrete_labels(
    similarity_scores: pd.Series,
    ground_truth: pd.Series,
    low_threshold: float = None,
    high_threshold: float = None
) -> pd.Series:
    """
    Convert continuous similarity scores (0-1) to discrete labels (0, 1, 2).
    
    If thresholds are not provided, uses quantiles based on similarity score distribution:
    - Scores < 33rd percentile → label 0
    - Scores >= 33rd percentile and < 67th percentile → label 1  
    - Scores >= 67th percentile → label 2
    
    Alternatively, can use ground truth-informed thresholds:
    - Use median similarity for GT=0 as low threshold
    - Use median similarity for GT=2 as high threshold
    
    Args:
        similarity_scores: Continuous similarity scores (0-1)
        ground_truth: Ground truth labels (0, 1, 2)
        low_threshold: Low threshold (if None, uses quantiles)
        high_threshold: High threshold (if None, uses quantiles)
        
    Returns:
        Series with discrete labels (0, 1, 2)
    """
    if low_threshold is None or high_threshold is None:
        # Strategy: Use quantiles of all similarity scores
        all_scores = similarity_scores.dropna()
        if len(all_scores) > 0:
            # Use 33rd and 67th percentiles to create 3 roughly equal bins
            low_threshold = float(all_scores.quantile(0.33))
            high_threshold = float(all_scores.quantile(0.67))
            
            # Log distribution info
            gt_0_scores = similarity_scores[ground_truth == 0].dropna()
            gt_1_scores = similarity_scores[ground_truth == 1].dropna()
            gt_2_scores = similarity_scores[ground_truth == 2].dropna()
            
            logger.info(f"Similarity score distribution:")
            logger.info(f"  All scores: mean={all_scores.mean():.3f}, median={all_scores.median():.3f}")
            if len(gt_0_scores) > 0:
                logger.info(f"  GT=0: mean={gt_0_scores.mean():.3f}, median={gt_0_scores.median():.3f}, count={len(gt_0_scores)}")
            if len(gt_1_scores) > 0:
                logger.info(f"  GT=1: mean={gt_1_scores.mean():.3f}, median={gt_1_scores.median():.3f}, count={len(gt_1_scores)}")
            if len(gt_2_scores) > 0:
                logger.info(f"  GT=2: mean={gt_2_scores.mean():.3f}, median={gt_2_scores.median():.3f}, count={len(gt_2_scores)}")
            logger.info(f"Using quantile-based thresholds: low={low_threshold:.3f}, high={high_threshold:.3f}")
        else:
            # Fallback to fixed thresholds
            low_threshold = 0.33
            high_threshold = 0.67
            logger.warning("No valid similarity scores, using default thresholds")
    else:
        logger.info(f"Using provided thresholds: low={low_threshold:.3f}, high={high_threshold:.3f}")
    
    # Map similarity scores to discrete labels
    discrete_labels = pd.Series(0, index=similarity_scores.index, dtype=int)
    discrete_labels[similarity_scores >= low_threshold] = 1
    discrete_labels[similarity_scores >= high_threshold] = 2
    
    # Log label distribution
    label_counts = discrete_labels.value_counts().sort_index()
    logger.info(f"Discrete label distribution: {dict(label_counts)}")
    
    return discrete_labels


def print_evaluation_results(metrics, ground_truth_col: str, k_values: List[int]):
    """
    Print evaluation results including metrics and confusion matrix.
    
    Args:
        metrics: S4MMetrics object with evaluation results
        ground_truth_col: Name of ground truth column
        k_values: List of K values evaluated
    """
    print("\n" + "="*80)
    print("EVALUATION RESULTS")
    print("="*80)
    print(f"Ground Truth Column: {ground_truth_col}")
    print(f"K Values: {k_values}")
    print()
    
    # Print metrics at different K values
    print("METRICS:")
    print("-"*80)
    print(f"{'K':<6} {'Precision@K':<15} {'Recall@K':<15} {'F1@K':<15} {'nDCG@K':<15}")
    print("-"*80)
    
    for k in k_values:
        prec = metrics.precision_at_k.get(k, 0.0)
        rec = metrics.recall_at_k.get(k, 0.0)
        f1 = metrics.f1_at_k.get(k, 0.0)
        ndcg = metrics.ndcg_at_k.get(k, 0.0)
        print(f"{k:<6} {prec:<15.4f} {rec:<15.4f} {f1:<15.4f} {ndcg:<15.4f}")
    
    print()
    
    # Print accuracy if available
    if metrics.accuracy is not None:
        print(f"Accuracy: {metrics.accuracy:.4f}")
        print()
    
    # Print confusion matrix
    if metrics.confusion_matrix:
        print("CONFUSION MATRIX:")
        print("-"*80)
        
        # Binary confusion matrix (TP, TN, FP, FN)
        if "TP" in metrics.confusion_matrix:
            print("Binary Classification (Relevant vs Not Relevant):")
            print(f"  True Positives (TP):  {metrics.confusion_matrix.get('TP', 0):>8}")
            print(f"  True Negatives (TN):  {metrics.confusion_matrix.get('TN', 0):>8}")
            print(f"  False Positives (FP): {metrics.confusion_matrix.get('FP', 0):>8}")
            print(f"  False Negatives (FN): {metrics.confusion_matrix.get('FN', 0):>8}")
            print()
        
        # Multi-class confusion matrix (if available)
        multi_class_keys = [k for k in metrics.confusion_matrix.keys() if k.startswith("GT_")]
        if multi_class_keys:
            print("Multi-class Classification (0, 1, 2):")
            print(f"{'GT\\Pred':<12} {'0':<12} {'1':<12} {'2':<12}")
            print("-"*50)
            for gt_label in [0, 1, 2]:
                row = f"GT_{gt_label:<8}"
                for pred_label in [0, 1, 2]:
                    key = f"GT_{gt_label}_PRED_{pred_label}"
                    count = metrics.confusion_matrix.get(key, 0)
                    row += f" {count:<11}"
                print(row)
            print()
    
    print("="*80)


def write_metrics_to_csv(
    metrics: S4MMetrics,
    output_path: Path,
    ground_truth_col: str,
    k_values: List[int],
    group_by: Optional[List[str]] = None,
    total_chunks: Optional[int] = None,
    threshold: Optional[float] = None,
    similarity_threshold: Optional[float] = None,
    use_llm: bool = False,
    llm_model: Optional[str] = None,
) -> None:
    """
    Write evaluation metrics to CSV format.
    
    Args:
        metrics: S4MMetrics object with evaluation results
        output_path: Path to output CSV file
        ground_truth_col: Name of ground truth column
        k_values: List of K values evaluated
        group_by: Columns used for grouping (if any)
        total_chunks: Total number of chunks evaluated
        threshold: Relevance threshold used
        similarity_threshold: Similarity threshold used (if applicable)
        use_llm: Whether LLM was used for scoring
        llm_model: LLM model name (if LLM was used)
    """
    import csv
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Write metadata section
        writer.writerow(["# METADATA"])
        writer.writerow(["Ground Truth Column", ground_truth_col])
        writer.writerow(["Group By", ",".join(group_by) if group_by else "criteria,company (default)"])
        writer.writerow(["Total Chunks Evaluated", total_chunks if total_chunks is not None else ""])
        writer.writerow(["Relevance Threshold", threshold if threshold is not None else ""])
        if similarity_threshold is not None:
            writer.writerow(["Similarity Threshold", similarity_threshold])
        writer.writerow(["Scoring Method", "LLM" if use_llm else "Embedding Similarity"])
        if use_llm and llm_model:
            writer.writerow(["LLM Model", llm_model])
        writer.writerow([])  # Empty row
        
        # Write metrics section
        writer.writerow(["# METRICS"])
        writer.writerow(["K", "Precision@K", "Recall@K", "F1@K", "nDCG@K"])
        
        for k in k_values:
            prec = metrics.precision_at_k.get(k, 0.0)
            rec = metrics.recall_at_k.get(k, 0.0)
            f1 = metrics.f1_at_k.get(k, 0.0)
            ndcg = metrics.ndcg_at_k.get(k, 0.0)
            writer.writerow([k, f"{prec:.6f}", f"{rec:.6f}", f"{f1:.6f}", f"{ndcg:.6f}"])
        
        writer.writerow([])  # Empty row
        
        # Write accuracy if available
        if metrics.accuracy is not None:
            writer.writerow(["# ACCURACY"])
            writer.writerow(["Accuracy", f"{metrics.accuracy:.6f}"])
            writer.writerow([])  # Empty row
        
        # Write confusion matrix
        if metrics.confusion_matrix:
            writer.writerow(["# CONFUSION MATRIX"])
            
            # Binary confusion matrix
            if "TP" in metrics.confusion_matrix:
                writer.writerow(["## Binary Classification (Relevant vs Not Relevant)"])
                writer.writerow(["Metric", "Count"])
                writer.writerow(["True Positives (TP)", metrics.confusion_matrix.get("TP", 0)])
                writer.writerow(["True Negatives (TN)", metrics.confusion_matrix.get("TN", 0)])
                writer.writerow(["False Positives (FP)", metrics.confusion_matrix.get("FP", 0)])
                writer.writerow(["False Negatives (FN)", metrics.confusion_matrix.get("FN", 0)])
                writer.writerow([])  # Empty row
            
            # Multi-class confusion matrix
            multi_class_keys = [k for k in metrics.confusion_matrix.keys() if k.startswith("GT_")]
            if multi_class_keys:
                writer.writerow(["## Multi-class Classification (0, 1, 2)"])
                writer.writerow(["Ground Truth", "Predicted 0", "Predicted 1", "Predicted 2"])
                for gt_label in [0, 1, 2]:
                    row = [f"GT_{gt_label}"]
                    for pred_label in [0, 1, 2]:
                        key = f"GT_{gt_label}_PRED_{pred_label}"
                        count = metrics.confusion_matrix.get(key, 0)
                        row.append(count)
                    writer.writerow(row)


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Embed chunks, compare to criteria, and evaluate against ground truth"
    )
    parser.add_argument(
        "--input",
        default="data/s4m/labels/test_data_extended_V6.xlsx - Sheet1.csv",
        help="Path to ground truth CSV file (default: data/s4m/labels/test_data_extended_V6.xlsx - Sheet1.csv)"
    )
    parser.add_argument(
        "--ground-truth-col",
        choices=["relevance", "usefulness"],
        default="relevance",
        help="Ground truth column name (default: relevance)"
    )
    parser.add_argument(
        "--chunk-col",
        default="chunk_text",
        help="Column name for chunk text (default: chunk_text)"
    )
    parser.add_argument(
        "--criteria-col",
        default="criteria",
        help="Column name for criteria (default: criteria)"
    )
    parser.add_argument(
        "--description-col",
        default="description",
        help="Column name for criteria description (default: description)"
    )
    parser.add_argument(
        "--k",
        default="1,3,5,10",
        help="Comma-separated K values (default: 1,3,5,10)"
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1.0,
        help="Relevance threshold for ground truth binary classification (default: 1.0, meaning >= 1 is relevant)"
    )
    parser.add_argument(
        "--similarity-threshold",
        type=float,
        default=0.5,
        help="Similarity threshold for converting similarity scores to binary predictions (default: 0.5, meaning >= 0.5 is relevant)"
    )
    parser.add_argument(
        "--similarity-low-threshold",
        type=float,
        default=None,
        help="Low threshold for mapping similarity scores to 3-class labels (0, 1, 2). If None, uses quantiles based on ground truth distribution. Scores < low_threshold → 0, >= low_threshold and < high_threshold → 1, >= high_threshold → 2"
    )
    parser.add_argument(
        "--similarity-high-threshold",
        type=float,
        default=None,
        help="High threshold for mapping similarity scores to 3-class labels (0, 1, 2). If None, uses quantiles based on ground truth distribution. Scores < low_threshold → 0, >= low_threshold and < high_threshold → 1, >= high_threshold → 2"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for embedding (default: 100)"
    )
    parser.add_argument(
        "--output",
        help="Path to output file for results (optional, prints to stdout if not provided). Use .csv extension for CSV format, .txt for text format."
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Use LLM-based scoring instead of embedding-based similarity (uses the provided prompt template)"
    )
    parser.add_argument(
        "--llm-model",
        default="gpt-4o-mini",
        help="LLM model name for scoring (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--llm-batch-size",
        type=int,
        default=10,
        help="Batch size for LLM scoring (default: 10)"
    )
    parser.add_argument(
        "--similarity-scores-file",
        help="Path to CSV file with pre-computed similarity scores (from embed_and_compare_criteria.py). If provided, skips embedding step and uses existing scores. The file should have 'embedding_similarity_score' column or similarity columns per criteria."
    )
    parser.add_argument(
        "--chunk-embeddings-file",
        help="Path to CSV file with pre-computed chunk embeddings. If provided along with --criteria-embeddings-file, will compute similarity scores from embeddings instead of re-embedding. The file should have columns 'chunk_embedding_0', 'chunk_embedding_1', etc., or a single 'embedding' column."
    )
    parser.add_argument(
        "--criteria-embeddings-file",
        help="Path to CSV file with pre-computed criteria embeddings. Must be provided together with --chunk-embeddings-file. The file should have columns 'criteria_embedding_0', 'criteria_embedding_1', etc., or a single 'embedding' column."
    )
    parser.add_argument(
        "--group-by",
        default="",
        help="Comma-separated column names to group by for per-report/per-query evaluation (e.g., 'company' or 'company,criteria'). Metrics will be calculated per group and macro-averaged. If empty (default), evaluates globally across all chunks. Examples: 'company' for per-report, 'company,criteria' for per-report-per-criteria."
    )
    parser.add_argument(
        "--save-false-negatives",
        help="Path to save CSV file with chunks where ground truth is 2 but model predicted 0 (highly relevant but missed by model). If not provided, false negatives are not saved."
    )
    
    args = parser.parse_args()
    
    try:
        # 1. Load ground truth dataset
        logger.info("Loading ground truth dataset...")
        df = load_chunks_and_criteria(
            csv_path=args.input,
            chunk_col=args.chunk_col,
            criteria_col=args.criteria_col,
            description_col=args.description_col
        )
        
        # Validate ground truth column exists
        if args.ground_truth_col not in df.columns:
            raise ValueError(
                f"Ground truth column '{args.ground_truth_col}' not found. "
                f"Available columns: {list(df.columns)}"
            )
        
        logger.info(f"Loaded {len(df)} rows from ground truth dataset")
        
        # 2. Generate predictions (either LLM-based or embedding-based)
        if args.use_llm:
            # LLM-based scoring
            logger.info("Using LLM-based scoring...")
            logger.info(f"LLM Model: {args.llm_model}")
            logger.info(f"LLM Batch Size: {args.llm_batch_size}")
            
            # Run async LLM scoring
            df_with_predictions = df.copy()
            llm_scores = asyncio.run(
                score_chunks_with_llm_batch(
                    df=df,
                    criteria_col=args.criteria_col,
                    description_col=args.description_col,
                    chunk_col=args.chunk_col,
                    score_type=args.ground_truth_col,  # "relevance" or "usefulness"
                    model_name=args.llm_model,
                    batch_size=args.llm_batch_size
                )
            )
            df_with_predictions["llm_score"] = llm_scores
            df_with_predictions["model_prediction"] = llm_scores  # For evaluation
            
        else:
            # Embedding-based scoring (original approach)
            # Check if we should load pre-computed similarity scores
            if args.similarity_scores_file:
                logger.info(f"Loading pre-computed similarity scores from: {args.similarity_scores_file}")
                similarity_df = pd.read_csv(args.similarity_scores_file)
                
                logger.info(f"Ground truth dataset: {len(df)} rows")
                logger.info(f"Similarity file: {len(similarity_df)} rows")
                
                # Filter out empty chunks from ground truth FIRST (before alignment)
                valid_mask_gt = df[args.chunk_col].notna() & (df[args.chunk_col].astype(str).str.strip() != "")
                # Check if similarity file was created with all rows or only valid chunks
                # embed_and_compare_criteria.py creates files with ALL rows, but only valid chunks have scores
                # So similarity_df should have same or more rows than df
                if len(similarity_df) < len(df):
                    logger.warning(
                        f"Similarity file has fewer rows ({len(similarity_df)}) than ground truth ({len(df)}). "
                        f"This suggests the similarity file was created from a filtered dataset."
                    )
                    # Try to merge on common identifying columns
                    # Prefer company+criteria+chunk_text to avoid duplicates from same chunk_text
                    common_cols = set(df.columns) & set(similarity_df.columns)
                    merge_cols = []
                    
                    # Try company+criteria+chunk_text first (most specific, avoids duplicates)
                    if all(col in common_cols for col in ["company", "criteria", args.chunk_col]):
                        merge_cols = ["company", "criteria", args.chunk_col]
                        logger.info(f"Merging on: {merge_cols} (most specific)")
                    elif args.chunk_col in common_cols:
                        # Fallback to chunk_text only, but warn about potential duplicates
                        merge_cols = [args.chunk_col]
                        logger.warning(f"Only merging on {args.chunk_col} - may create duplicates if same chunk appears multiple times")
                    
                    if merge_cols:
                        # Add a temporary row identifier before merge to track original rows
                        df_with_temp_id = df.copy()
                        df_with_temp_id["_temp_row_id"] = range(len(df_with_temp_id))
                        
                        df_with_predictions = df_with_temp_id.merge(
                            similarity_df,
                            on=merge_cols,
                            how="left",  # Keep all ground truth rows
                            suffixes=("", "_sim")
                        )
                        
                        # Check for duplicates
                        if len(df_with_predictions) > len(df):
                            logger.warning(
                                f"Merge created {len(df_with_predictions) - len(df)} duplicate rows. "
                                f"Taking first match for each ground truth row."
                            )
                            # Deduplicate by keeping first match for each original row using temp_row_id
                            df_with_predictions = df_with_predictions.groupby("_temp_row_id", as_index=False).first()
                        
                        # Remove temporary column if it exists
                        if "_temp_row_id" in df_with_predictions.columns:
                            df_with_predictions = df_with_predictions.drop(columns=["_temp_row_id"])
                        
                        # Check for embedding_similarity_score column (might have _sim suffix or be missing)
                        if "embedding_similarity_score" not in df_with_predictions.columns:
                            # Check if it exists with _sim suffix
                            if "embedding_similarity_score_sim" in df_with_predictions.columns:
                                df_with_predictions["embedding_similarity_score"] = df_with_predictions["embedding_similarity_score_sim"]
                            else:
                                # Check for per-criteria similarity columns
                                similarity_cols = [col for col in df_with_predictions.columns if col.startswith("criteria_embedding_similarity_")]
                                if similarity_cols:
                                    logger.info(f"Computing embedding_similarity_score from {len(similarity_cols)} criteria columns")
                                    df_with_predictions["embedding_similarity_score"] = df_with_predictions[similarity_cols].max(axis=1)
                                else:
                                    logger.warning("No embedding_similarity_score or criteria columns found after merge")
                                    df_with_predictions["embedding_similarity_score"] = 0.0
                else:
                    # Similarity file has same or more rows - use index alignment
                    logger.info(f"Aligning similarity scores by index position (assuming same row order)")
                    df_with_predictions = df.copy()
                    
                    # Check if the file has embedding_similarity_score column
                    if "embedding_similarity_score" in similarity_df.columns:
                        # Copy similarity scores by index position (only for rows that exist in df)
                        df_with_predictions["embedding_similarity_score"] = similarity_df["embedding_similarity_score"].iloc[:len(df)].values
                        logger.info("Loaded embedding_similarity_score column from similarity scores file")
                    else:
                        # Check if it has per-criteria similarity columns and compute max
                        similarity_cols = [col for col in similarity_df.columns if col.startswith("criteria_embedding_similarity_")]
                        if similarity_cols:
                            logger.info(f"Found {len(similarity_cols)} criteria similarity columns, computing max similarity...")
                            # Compute max similarity across all criteria for each row
                            df_with_predictions["embedding_similarity_score"] = similarity_df[similarity_cols].iloc[:len(df)].max(axis=1).values
                            logger.info("Computed embedding_similarity_score as max across criteria")
                        else:
                            raise ValueError(
                                f"Similarity scores file does not contain 'embedding_similarity_score' or 'criteria_embedding_similarity_*' columns. "
                                f"Available columns: {list(similarity_df.columns)}"
                            )
                
                # Filter to only valid chunks for evaluation (same as when computing embeddings)
                valid_mask = df_with_predictions[args.chunk_col].notna() & (df_with_predictions[args.chunk_col].astype(str).str.strip() != "")
                
                # Check if we have similarity scores for valid chunks
                if "embedding_similarity_score" in df_with_predictions.columns:
                    valid_with_scores = valid_mask & df_with_predictions["embedding_similarity_score"].notna()
                    
                    if valid_with_scores.sum() < valid_mask.sum():
                        logger.warning(
                            f"Only {valid_with_scores.sum()} out of {valid_mask.sum()} valid chunks have similarity scores. "
                            f"Missing scores will be set to 0.0"
                        )
                        # Set missing scores to 0.0 for valid chunks
                        df_with_predictions.loc[valid_mask & df_with_predictions["embedding_similarity_score"].isna(), "embedding_similarity_score"] = 0.0
                
                # Filter to only valid chunks for evaluation
                df_with_predictions = df_with_predictions[valid_mask].copy()
                logger.info(f"Final dataset: {len(df_with_predictions)} valid chunks for evaluation")
                
            elif "embedding_similarity_score" in df.columns:
                # Use existing similarity scores from input file
                logger.info("Using existing embedding_similarity_score column from input file")
                df_with_predictions = df.copy()
            elif args.chunk_embeddings_file and args.criteria_embeddings_file:
                # Use pre-computed embeddings to compute similarity scores
                logger.info("Loading pre-computed embeddings and computing similarity scores...")
                logger.info(f"Loading chunk embeddings from: {args.chunk_embeddings_file}")
                logger.info(f"Loading criteria embeddings from: {args.criteria_embeddings_file}")
                
                # Check if files exist
                chunk_file_path = Path(args.chunk_embeddings_file)
                criteria_file_path = Path(args.criteria_embeddings_file)
                
                if not chunk_file_path.exists():
                    logger.warning(f"Chunk embeddings file not found: {args.chunk_embeddings_file}")
                    logger.warning("Falling back to computing embeddings on-the-fly")
                    chunk_embeddings = None
                    criteria_embeddings = None
                elif not criteria_file_path.exists():
                    logger.warning(f"Criteria embeddings file not found: {args.criteria_embeddings_file}")
                    logger.warning("Falling back to computing embeddings on-the-fly")
                    chunk_embeddings = None
                    criteria_embeddings = None
                else:
                    chunk_embeddings = load_embeddings_from_csv(args.chunk_embeddings_file, "chunk_embedding_")
                    criteria_embeddings = load_embeddings_from_csv(args.criteria_embeddings_file, "criteria_embedding_")
                    
                    if chunk_embeddings is None or criteria_embeddings is None:
                        logger.warning("Failed to load embeddings from files. Falling back to computing embeddings on-the-fly")
                        chunk_embeddings = None
                        criteria_embeddings = None
                
                # If embeddings loaded successfully, use them
                if chunk_embeddings is not None and criteria_embeddings is not None:
                    # Filter to valid chunks
                    valid_mask = df[args.chunk_col].notna() & (df[args.chunk_col].astype(str).str.strip() != "")
                    num_valid = valid_mask.sum()
                    
                    # Align embeddings with valid chunks
                    if len(chunk_embeddings) == num_valid:
                        # Embeddings already filtered to valid chunks
                        aligned_chunk_emb = chunk_embeddings
                        aligned_criteria_emb = criteria_embeddings
                    elif len(chunk_embeddings) == len(df):
                        # Embeddings for all rows, filter to valid
                        aligned_chunk_emb = chunk_embeddings[valid_mask.values]
                        aligned_criteria_emb = criteria_embeddings[valid_mask.values]
                    else:
                        raise ValueError(
                            f"Embedding count mismatch: {len(chunk_embeddings)} chunk embeddings and "
                            f"{len(criteria_embeddings)} criteria embeddings for {num_valid} valid chunks "
                            f"(or {len(df)} total rows)"
                        )
                    
                    logger.info(f"Using {len(aligned_chunk_emb)} embeddings to compute similarity scores")
                    
                    # Compute similarity using pre-computed embeddings
                    df_with_predictions = compute_similarity_per_row(
                        df=df,
                        analyzer=None,  # Not needed when embeddings provided
                        chunk_col=args.chunk_col,
                        criteria_col=args.criteria_col,
                        description_col=args.description_col,
                        batch_size=args.batch_size,
                        chunk_embeddings=aligned_chunk_emb,
                        criteria_embeddings=aligned_criteria_emb
                    )
                    logger.info(f"Computed similarity for {len(df_with_predictions)} chunks from pre-computed embeddings")
                else:
                    # Fall through to compute embeddings on-the-fly
                    logger.info("Using embedding-based similarity scoring (fallback)...")
                    logger.info("Computing similarity: each chunk compared with its own criteria description")
                    
                    # Get DocumentAnalyzer (reuses existing embedding infrastructure)
                    logger.info("Initializing embedding model...")
                    analyzer = get_analyzer()
                    
                    # Compute similarity per row (chunk vs its own criteria description)
                    logger.info("Computing similarity scores (chunk vs corresponding criteria description)...")
                    df_with_predictions = compute_similarity_per_row(
                        df=df,
                        analyzer=analyzer,
                        chunk_col=args.chunk_col,
                        criteria_col=args.criteria_col,
                        description_col=args.description_col,
                        batch_size=args.batch_size
                    )
            else:
                # Compute embeddings and similarity scores
                # NEW APPROACH: Compare each chunk with its own criteria description only
                logger.info("Using embedding-based similarity scoring...")
                logger.info("Computing similarity: each chunk compared with its own criteria description")
                
                # 3a. Get DocumentAnalyzer (reuses existing embedding infrastructure)
                logger.info("Initializing embedding model...")
                analyzer = get_analyzer()
                
                # 4. Compute similarity per row (chunk vs its own criteria description)
                logger.info("Computing similarity scores (chunk vs corresponding criteria description)...")
                df_with_predictions = compute_similarity_per_row(
                    df=df,
                    analyzer=analyzer,
                    chunk_col=args.chunk_col,
                    criteria_col=args.criteria_col,
                    description_col=args.description_col,
                    batch_size=args.batch_size
                )
        
        # 8. Parse K values
        k_values = [int(k.strip()) for k in args.k.split(",") if k.strip().isdigit()]
        
        # 9. Prepare predictions for evaluation
        if args.use_llm:
            # LLM scores are already discrete (0, 1, 2), use directly
            logger.info("Using LLM scores directly (already discrete 0-2)...")
            model_pred_col = "llm_score"
        else:
            # Embedding-based: Convert similarity scores to discrete labels (0, 1, 2)
            logger.info("Converting similarity scores to discrete labels (0, 1, 2)...")
            df_with_predictions["embedding_similarity_discrete"] = convert_similarity_to_discrete_labels(
                similarity_scores=df_with_predictions["embedding_similarity_score"],
                ground_truth=df_with_predictions[args.ground_truth_col],
                low_threshold=args.similarity_low_threshold,
                high_threshold=args.similarity_high_threshold
            )
            
            # Also create binary prediction column for binary confusion matrix
            similarity_threshold = args.similarity_threshold
            logger.info(f"Creating binary predictions using threshold: {similarity_threshold}")
            df_with_predictions["embedding_similarity_binary"] = (
                df_with_predictions["embedding_similarity_score"] >= similarity_threshold
            ).astype(int)
            
            # Use discrete labels for confusion matrix, continuous for ranking
            model_pred_col = "embedding_similarity_discrete"
        
        # 10. Parse group_by columns
        if args.group_by and args.group_by.strip():
            group_by_cols = [col.strip() for col in args.group_by.split(",") if col.strip()]
            logger.info(f"Grouping by: {group_by_cols} (metrics calculated per group, then macro-averaged)")
            logger.info(f"  This means: nDCG@K will be calculated per {group_by_cols}, using all chunks in each group for IDCG")
            
            # Validate group_by columns exist
            missing_cols = [col for col in group_by_cols if col not in df_with_predictions.columns]
            if missing_cols:
                raise ValueError(
                    f"Group-by columns not found in dataset: {missing_cols}. "
                    f"Available columns: {list(df_with_predictions.columns)}"
                )
            
            # Show group statistics
            num_groups = df_with_predictions.groupby(group_by_cols).ngroups
            logger.info(f"  Found {num_groups} groups")
            
            # Debug: Show sample groups
            sample_groups = df_with_predictions.groupby(group_by_cols).size().head(5)
            logger.info(f"  Sample group sizes:\n{sample_groups}")
        else:
            group_by_cols = None  # None = use default grouping (criteria, company)
            logger.info("No grouping specified - using default grouping: ['criteria', 'company']")
            # Debug: Show what default grouping would produce
            default_group_by = ["criteria", "company"]
            if all(col in df_with_predictions.columns for col in default_group_by):
                num_groups_default = df_with_predictions.groupby(default_group_by).ngroups
                logger.info(f"  Default grouping would produce {num_groups_default} groups")
        
        # 11. Evaluate against ground truth
        logger.info(f"Evaluating against ground truth column: {args.ground_truth_col}")
        logger.info(f"Using relevance threshold: {args.threshold} (for ground truth)")
        if not args.use_llm:
            logger.info(f"Using similarity threshold: {args.similarity_threshold} (for binary predictions)")
        logger.info(f"K values: {k_values}")
        
        # Evaluate with discrete labels (0, 1, 2) for confusion matrix
        metrics = evaluate_s4m_classification(
            df=df_with_predictions,
            ground_truth_col=args.ground_truth_col,
            model_pred_col=model_pred_col,
            relevance_threshold=args.threshold,
            k_values=k_values,
            group_by=group_by_cols,  # None = default, [] = global, [col1, col2] = custom grouping
        )
        
        # For embedding-based, also evaluate with continuous scores for better ranking
        if not args.use_llm:
            metrics_continuous = evaluate_s4m_classification(
                df=df_with_predictions,
                ground_truth_col=args.ground_truth_col,
                model_pred_col="embedding_similarity_score",  # Continuous scores for ranking
                relevance_threshold=args.threshold,
                k_values=k_values,
                group_by=group_by_cols,
            )
            
            # Use ranking metrics from continuous scores (better for ranking)
            # But keep confusion matrix from discrete labels (proper multi-class)
            # Recalculate confusion matrix with proper binary conversion
            # Ground truth binary: scores 1 and 2 → relevant (1), score 0 → not relevant (0)
            # Prediction binary: discrete labels 1 and 2 → relevant (1), label 0 → not relevant (0)
            gt_binary = (df_with_predictions[args.ground_truth_col] >= 1).astype(int)  # 1 and 2 → 1, 0 → 0
            pred_binary = (df_with_predictions["embedding_similarity_discrete"] >= 1).astype(int)  # 1 and 2 → 1, 0 → 0
            
            # Calculate correct binary confusion matrix
            tp = int(((gt_binary == 1) & (pred_binary == 1)).sum())
            tn = int(((gt_binary == 0) & (pred_binary == 0)).sum())
            fp = int(((gt_binary == 0) & (pred_binary == 1)).sum())
            fn = int(((gt_binary == 1) & (pred_binary == 0)).sum())
            
            # Create updated confusion matrix (since S4MMetrics is frozen, we need to create new dict)
            updated_confusion_matrix = metrics.confusion_matrix.copy() if metrics.confusion_matrix else {}
            updated_confusion_matrix["TP"] = tp
            updated_confusion_matrix["TN"] = tn
            updated_confusion_matrix["FP"] = fp
            updated_confusion_matrix["FN"] = fn
            
            # Create a new metrics object since S4MMetrics is frozen
            metrics = S4MMetrics(
                precision_at_k=metrics_continuous.precision_at_k,
                recall_at_k=metrics_continuous.recall_at_k,
                f1_at_k=metrics_continuous.f1_at_k,
                ndcg_at_k=metrics_continuous.ndcg_at_k,
                accuracy=metrics_continuous.accuracy,
                confusion_matrix=updated_confusion_matrix
            )
        
        # 10. Print results
        output_text = []
        
        # Capture print output
        import io
        from contextlib import redirect_stdout
        
        f = io.StringIO()
        with redirect_stdout(f):
            print_evaluation_results(metrics, args.ground_truth_col, k_values)
        output_text.append(f.getvalue())
        
        # Print to console
        print(output_text[0])
        
        # Save to file if requested
        if args.output:
            output_path = Path(args.output)
            
            # Determine if output should be CSV based on file extension
            if output_path.suffix.lower() == '.csv':
                # Write CSV format
                write_metrics_to_csv(
                    metrics=metrics,
                    output_path=output_path,
                    ground_truth_col=args.ground_truth_col,
                    k_values=k_values,
                    group_by=group_by_cols,
                    total_chunks=len(df_with_predictions),
                    threshold=args.threshold,
                    similarity_threshold=args.similarity_threshold if not args.use_llm else None,
                    use_llm=args.use_llm,
                    llm_model=args.llm_model if args.use_llm else None,
                )
                logger.info(f"Results saved to CSV: {output_path}")
            else:
                # Write text format (for backward compatibility)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'w') as f:
                    f.write(output_text[0])
                logger.info(f"Results saved to: {output_path}")
        
        # Save false negatives (GT=2, Pred=0) if requested
        if args.save_false_negatives:
            # Filter for chunks where ground truth is 2 but model predicted 0
            false_negatives_mask = (
                (df_with_predictions[args.ground_truth_col] == 2) & 
                (df_with_predictions[model_pred_col] == 0)
            )
            false_negatives_df = df_with_predictions[false_negatives_mask].copy()
            
            if len(false_negatives_df) > 0:
                # Add additional useful columns if they exist
                output_cols = [
                    args.chunk_col,
                    args.criteria_col,
                    args.description_col,
                    args.ground_truth_col,
                    model_pred_col,
                ]
                
                # Add similarity score if available
                if "embedding_similarity_score" in false_negatives_df.columns:
                    output_cols.append("embedding_similarity_score")
                
                # Add company and other metadata if available
                for col in ["company", "industry", "explanation"]:
                    if col in false_negatives_df.columns:
                        output_cols.append(col)
                
                # Select only columns that exist
                output_cols = [col for col in output_cols if col in false_negatives_df.columns]
                false_negatives_output = false_negatives_df[output_cols].copy()
                
                # Save to CSV
                output_path = Path(args.save_false_negatives)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                false_negatives_output.to_csv(output_path, index=False)
                
                logger.info(f"\nSaved {len(false_negatives_output)} false negatives (GT=2, Pred=0) to: {output_path}")
                logger.info(f"  These are chunks that were highly relevant (label 2) but the model predicted as not relevant (label 0)")
                
                # Print summary statistics for false negatives
                if "embedding_similarity_score" in false_negatives_output.columns:
                    avg_sim = false_negatives_output["embedding_similarity_score"].mean()
                    logger.info(f"  Average similarity score for false negatives: {avg_sim:.4f}")
                
                if args.criteria_col in false_negatives_output.columns:
                    criteria_counts = false_negatives_output[args.criteria_col].value_counts()
                    logger.info(f"  False negatives by criteria (top 5):")
                    for criteria, count in criteria_counts.head(5).items():
                        logger.info(f"    {criteria}: {count}")
            else:
                logger.info(f"\nNo false negatives found (GT=2, Pred=0). Model correctly identified all highly relevant chunks.")
        
        # Print summary statistics
        logger.info("\nSummary:")
        logger.info(f"  Total chunks evaluated: {len(df_with_predictions)}")
        logger.info(f"  Ground truth column: {args.ground_truth_col}")
        logger.info(f"  F1@10: {metrics.f1_at_k.get(10, 0.0):.4f}")
        logger.info(f"  nDCG@10: {metrics.ndcg_at_k.get(10, 0.0):.4f}")
        if metrics.accuracy is not None:
            logger.info(f"  Accuracy: {metrics.accuracy:.4f}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

