#!/usr/bin/env python3
"""
Script to embed report chunks and criteria descriptions, compute similarity scores,
and output results in benchmark-compatible format.

This script uses the existing DocumentAnalyzer from report_analyst to reuse
embedding infrastructure.

Usage:
    # Compute embeddings and similarity scores
    python3 -m report_analyst.core.benchmark.s4m_embed_and_compare_criteria \
        --input "data/s4m/labels/test_data_extended_V6.xlsx - Sheet1.csv" \
        --chunk-col "chunk_text" \
        --criteria-col "criteria" \
        --description-col "description" \
        --output "data/s4m/results/chunks_with_criteria_similarities.csv" \
        --batch-size 100
    
    # Use pre-computed embeddings (skip embedding computation)
    python3 -m report_analyst.core.benchmark.s4m_embed_and_compare_criteria \
        --input "data/s4m/labels/test_data_extended_V6.xlsx - Sheet1.csv" \
        --chunk-embeddings-file "data/s4m/results/chunk_embeddings.csv" \
        --criteria-embeddings-file "data/s4m/results/criteria_embeddings.csv" \
        --output "data/s4m/results/chunks_with_criteria_similarities.csv"
    
    # Save embeddings when computing (for future reuse)
    python3 -m report_analyst.core.benchmark.s4m_embed_and_compare_criteria \
        --input "data/s4m/labels/test_data_extended_V6.xlsx - Sheet1.csv" \
        --output "data/s4m/results/chunks_with_criteria_similarities.csv" \
        --save-embeddings
"""

import sys
import logging
from pathlib import Path
from typing import List, Optional, Tuple
import argparse
import json

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from dotenv import load_dotenv

# Setup project path (go up 3 levels from report_analyst/core/benchmark/ to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables (checks .env, ok.env.local, etc.)
load_dotenv()  # Loads .env by default
load_dotenv("ok.env.local")  # Also load ok.env.local if it exists

from report_analyst.core.analyzer import DocumentAnalyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_chunks_and_criteria(
    csv_path: str,
    chunk_col: str = "chunk_text",
    criteria_col: str = "criteria",
    description_col: str = "description"
) -> pd.DataFrame:
    """
    Load CSV with chunks and criteria.
    
    Args:
        csv_path: Path to CSV file
        chunk_col: Column name for chunk text
        criteria_col: Column name for criteria
        description_col: Column name for criteria description
        
    Returns:
        DataFrame with loaded data
    """
    logger.info(f"Loading data from: {csv_path}")
    
    if not Path(csv_path).exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    # Load CSV
    df = pd.read_csv(csv_path)
    logger.info(f"Loaded {len(df)} rows")
    
    # Validate required columns
    if chunk_col not in df.columns:
        raise ValueError(f"Column '{chunk_col}' not found in CSV. Available columns: {list(df.columns)}")
    if criteria_col not in df.columns:
        raise ValueError(f"Column '{criteria_col}' not found in CSV. Available columns: {list(df.columns)}")
    
    # Check for empty chunks
    empty_chunks = df[chunk_col].isna() | (df[chunk_col].astype(str).str.strip() == "")
    if empty_chunks.any():
        logger.warning(f"Found {empty_chunks.sum()} empty chunks. They will be skipped.")
    
    logger.info(f"Data loaded successfully. Columns: {list(df.columns)}")
    return df


def get_analyzer() -> DocumentAnalyzer:
    """
    Get DocumentAnalyzer instance (reuses existing embedding infrastructure).
    
    Returns:
        DocumentAnalyzer instance with embeddings initialized
    """
    analyzer = DocumentAnalyzer()
    if analyzer.embeddings is None:
        raise ValueError(
            "Embeddings not available in DocumentAnalyzer. "
            "Please ensure OPENAI_API_KEY is set in your .env file or environment."
        )
    logger.info("Using DocumentAnalyzer with existing embedding infrastructure")
    return analyzer


def embed_texts(
    texts: List[str],
    analyzer: DocumentAnalyzer,
    batch_size: int = 100,
    description: str = "texts"
) -> np.ndarray:
    """
    Embed texts in batches.
    
    Args:
        texts: List of text strings to embed
        embeddings_model: Initialized embedding model
        batch_size: Batch size for processing
        description: Description for logging
        
    Returns:
        NumPy array of embeddings (shape: [num_texts, embedding_dim])
    """
    if not texts:
        logger.warning(f"No {description} to embed")
        return np.array([])
    
    # Clean and validate texts
    cleaned_texts = []
    valid_indices = []
    for i, text in enumerate(texts):
        if pd.isna(text):
            continue
        text_str = str(text).strip()
        if text_str and len(text_str) > 0:
            # Remove null characters and normalize whitespace
            text_str = " ".join(text_str.replace("\x00", "").split())
            cleaned_texts.append(text_str)
            valid_indices.append(i)
    
    if not cleaned_texts:
        logger.warning(f"No valid {description} to embed after cleaning")
        return np.array([])
    
    logger.info(f"Embedding {len(cleaned_texts)} {description} in batches of {batch_size}")
    
    all_embeddings = []
    num_batches = (len(cleaned_texts) - 1) // batch_size + 1
    
    for i in range(0, len(cleaned_texts), batch_size):
        batch = cleaned_texts[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        logger.info(f"Processing batch {batch_num}/{num_batches} ({len(batch)} {description})")
        
        try:
            batch_embeddings = analyzer.embeddings.get_text_embedding_batch(batch)
            
            # Convert to numpy array
            batch_embeddings_array = np.array(batch_embeddings, dtype=np.float32)
            all_embeddings.append(batch_embeddings_array)
            
            logger.info(f"Successfully embedded batch {batch_num}/{num_batches}")
            
        except Exception as e:
            logger.error(f"Error embedding batch {batch_num}: {e}")
            raise
    
    if not all_embeddings:
        return np.array([])
    
    # Concatenate all embeddings
    embeddings = np.vstack(all_embeddings)
    logger.info(f"Successfully embedded {len(embeddings)} {description}. Shape: {embeddings.shape}")
    
    return embeddings


def load_embeddings_from_csv(
    csv_path: str,
    embedding_prefix: str = "embedding_"
) -> Optional[np.ndarray]:
    """
    Load embeddings from CSV file.
    
    CSV can have:
    - Columns named 'embedding_0', 'embedding_1', ... 'embedding_N'
    - Or a single 'embedding' column with comma-separated values
    - Or a single 'embedding' column with JSON arrays
    
    Args:
        csv_path: Path to CSV file with embeddings
        embedding_prefix: Prefix for embedding columns (default: "embedding_")
        
    Returns:
        NumPy array of embeddings [num_rows, embedding_dim] or None if not found
    """
    try:
        df = pd.read_csv(csv_path)
        
        # Try to find embedding columns
        embedding_cols = [col for col in df.columns if col.startswith(embedding_prefix)]
        
        if embedding_cols:
            # Load from multiple columns
            embeddings = df[embedding_cols].values.astype(np.float32)
            logger.info(f"Loaded {len(embeddings)} embeddings from {len(embedding_cols)} columns")
            return embeddings
        
        # Try single 'embedding' column with comma-separated values
        if "embedding" in df.columns:
            embeddings_list = []
            for val in df["embedding"]:
                if pd.isna(val):
                    continue
                # Try parsing as comma-separated string
                try:
                    if isinstance(val, str):
                        # Try JSON first
                        try:
                            emb = json.loads(val)
                        except:
                            # Try comma-separated
                            emb = [float(x.strip()) for x in val.split(",")]
                        embeddings_list.append(emb)
                    else:
                        embeddings_list.append(val)
                except Exception as e:
                    logger.warning(f"Failed to parse embedding: {e}")
                    continue
            
            if embeddings_list:
                embeddings = np.array(embeddings_list, dtype=np.float32)
                logger.info(f"Loaded {len(embeddings)} embeddings from 'embedding' column")
                return embeddings
        
        logger.warning(f"No embedding columns found in {csv_path}")
        return None
        
    except Exception as e:
        logger.error(f"Error loading embeddings from {csv_path}: {e}")
        return None


def save_embeddings_to_csv(
    embeddings: np.ndarray,
    output_path: Path,
    prefix: str = "embedding_"
) -> None:
    """
    Save embeddings to CSV file.
    
    Args:
        embeddings: NumPy array of embeddings [num_rows, embedding_dim]
        output_path: Path to output CSV file
        prefix: Prefix for embedding column names
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create DataFrame with embedding columns
    embedding_cols = {f"{prefix}{i}": embeddings[:, i] for i in range(embeddings.shape[1])}
    df = pd.DataFrame(embedding_cols)
    
    df.to_csv(output_path, index=False)
    logger.info(f"Saved {len(embeddings)} embeddings ({embeddings.shape[1]} dimensions) to {output_path}")


def compute_similarity_per_row(
    df: pd.DataFrame,
    analyzer,
    chunk_col: str = "chunk_text",
    criteria_col: str = "criteria",
    description_col: str = "description",
    batch_size: int = 100,
    chunk_embeddings: Optional[np.ndarray] = None,
    criteria_embeddings: Optional[np.ndarray] = None
) -> pd.DataFrame:
    """
    Compute similarity between each chunk and its corresponding criteria description.
    Each row's chunk is compared only with its own criteria description.
    
    Args:
        df: DataFrame with chunks, criteria, and descriptions
        analyzer: DocumentAnalyzer instance for embeddings (required if embeddings not provided)
        chunk_col: Column name for chunk text
        criteria_col: Column name for criteria
        description_col: Column name for criteria description
        batch_size: Batch size for embedding
        chunk_embeddings: Optional pre-computed chunk embeddings [num_valid_chunks, embedding_dim]
        criteria_embeddings: Optional pre-computed criteria embeddings [num_valid_chunks, embedding_dim]
        
    Returns:
        DataFrame with added 'embedding_similarity_score' column
    """
    df = df.copy()
    
    # Filter to rows with valid chunks
    valid_mask = df[chunk_col].notna() & (df[chunk_col].astype(str).str.strip() != "")
    num_valid = valid_mask.sum()
    
    if num_valid == 0:
        logger.warning("No valid chunks found")
        df["embedding_similarity_score"] = 0.0
        return df
    
    logger.info(f"Computing similarity for {num_valid} chunks (each with its own criteria description)")
    
    # Initialize prediction column
    df["embedding_similarity_score"] = 0.0
    
    valid_df = df[valid_mask].copy()
    
    # Use pre-computed embeddings if provided, otherwise compute them
    if chunk_embeddings is not None and criteria_embeddings is not None:
        logger.info("Using pre-computed embeddings")
        if len(chunk_embeddings) != num_valid or len(criteria_embeddings) != num_valid:
            raise ValueError(
                f"Embedding count mismatch: {len(chunk_embeddings)} chunk embeddings and "
                f"{len(criteria_embeddings)} criteria embeddings for {num_valid} valid chunks"
            )
        
        # Compute similarity for each pair
        similarities = []
        for i in range(num_valid):
            chunk_emb = chunk_embeddings[i].reshape(1, -1)
            criteria_emb = criteria_embeddings[i].reshape(1, -1)
            similarity = float(cosine_similarity(chunk_emb, criteria_emb)[0, 0])
            similarities.append(similarity)
    
    else:
        # Compute embeddings on the fly
        if analyzer is None:
            raise ValueError("analyzer is required when embeddings are not provided")
        
        similarities = []
        
        for batch_start in range(0, num_valid, batch_size):
            batch_end = min(batch_start + batch_size, num_valid)
            batch_df = valid_df.iloc[batch_start:batch_end]
            
            # Prepare texts for this batch
            chunk_texts = []
            criteria_descriptions = []
            
            for _, row in batch_df.iterrows():
                chunk_text = str(row.get(chunk_col, ""))
                criteria_name = str(row.get(criteria_col, ""))
                description = str(row.get(description_col, ""))
                
                # Create criteria description text
                if pd.notna(description) and str(description).strip():
                    criteria_text = f"{criteria_name}: {description}"
                else:
                    criteria_text = str(criteria_name)
                
                chunk_texts.append(chunk_text)
                criteria_descriptions.append(criteria_text)
            
            # Embed chunks and criteria descriptions for this batch
            batch_chunk_embeddings = embed_texts(
                texts=chunk_texts,
                analyzer=analyzer,
                batch_size=len(chunk_texts),
                description=f"chunks (batch {batch_start//batch_size + 1})"
            )
            
            batch_criteria_embeddings = embed_texts(
                texts=criteria_descriptions,
                analyzer=analyzer,
                batch_size=len(criteria_descriptions),
                description=f"criteria descriptions (batch {batch_start//batch_size + 1})"
            )
            
            # Compute similarity for each pair (chunk[i] with criteria[i])
            for i in range(len(chunk_texts)):
                chunk_emb = batch_chunk_embeddings[i].reshape(1, -1)
                criteria_emb = batch_criteria_embeddings[i].reshape(1, -1)
                similarity = float(cosine_similarity(chunk_emb, criteria_emb)[0, 0])
                similarities.append(similarity)
            
            logger.info(f"Processed batch {batch_start//batch_size + 1} ({batch_end}/{num_valid} chunks)")
    
    # Assign similarities to valid rows
    for i, (idx, _) in enumerate(valid_df.iterrows()):
        df.at[idx, "embedding_similarity_score"] = similarities[i]
    
    logger.info(f"Computed similarity scores for {num_valid} chunks")
    return df


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Embed chunks and criteria, compute similarity scores"
    )
    parser.add_argument(
        "--input",
        required=False,
        help="Path to input CSV file with chunks and criteria. Optional if --chunk-embeddings-file and --criteria-embeddings-file are provided (will create minimal structure from embeddings)."
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to output CSV file with similarity scores"
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
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for embedding (default: 100)"
    )
    parser.add_argument(
        "--chunk-embeddings-file",
        help="Path to CSV file with pre-computed chunk embeddings. The file should have columns 'chunk_embedding_0', 'chunk_embedding_1', etc., or a single 'chunk_embedding' column with comma-separated values. If provided, skips chunk embedding computation."
    )
    parser.add_argument(
        "--criteria-embeddings-file",
        help="Path to CSV file with pre-computed criteria embeddings. The file should have columns matching criteria names with embedding columns. If provided, skips criteria embedding computation."
    )
    parser.add_argument(
        "--save-embeddings",
        action="store_true",
        help="Save computed embeddings to CSV files (chunk_embeddings.csv and criteria_embeddings.csv in output directory)"
    )
    
    args = parser.parse_args()
    
    try:
        # 1. Load pre-computed embeddings if provided
        chunk_embeddings = None
        criteria_embeddings = None
        
        # Check if we can skip input file (both embeddings provided)
        if args.chunk_embeddings_file and args.criteria_embeddings_file:
            if not args.input:
                logger.info("Both embeddings files provided, creating minimal DataFrame from embeddings")
                # Load embeddings to determine structure
                chunk_emb = load_embeddings_from_csv(args.chunk_embeddings_file, "chunk_embedding_")
                criteria_emb = load_embeddings_from_csv(args.criteria_embeddings_file, "criteria_embedding_")
                
                if chunk_emb is None or criteria_emb is None:
                    raise ValueError("Failed to load embeddings files. Cannot proceed without input file.")
                
                # Create minimal DataFrame with same number of rows as embeddings
                # Use placeholder text so rows are considered "valid" (not empty)
                num_rows = len(chunk_emb)
                df = pd.DataFrame({
                    args.chunk_col: ["placeholder"] * num_rows,  # Placeholder (not used when embeddings provided)
                    args.criteria_col: [f"criteria_{i}" for i in range(num_rows)],
                    args.description_col: [""] * num_rows
                })
                logger.info(f"Created minimal DataFrame with {num_rows} rows from embeddings")
                chunk_embeddings = chunk_emb
                criteria_embeddings = criteria_emb
            else:
                # Load input file normally
                df = load_chunks_and_criteria(
                    csv_path=args.input,
                    chunk_col=args.chunk_col,
                    criteria_col=args.criteria_col,
                    description_col=args.description_col
                )
        elif args.input:
            # Load input file (required if embeddings not provided)
            df = load_chunks_and_criteria(
                csv_path=args.input,
                chunk_col=args.chunk_col,
                criteria_col=args.criteria_col,
                description_col=args.description_col
            )
        else:
            raise ValueError(
                "Either --input must be provided, or both --chunk-embeddings-file and --criteria-embeddings-file must be provided"
            )
        
        # 2. Load pre-computed embeddings if provided (skip if already loaded above)
        if chunk_embeddings is None and args.chunk_embeddings_file:
            logger.info(f"Loading chunk embeddings from: {args.chunk_embeddings_file}")
            loaded_chunk_embeddings = load_embeddings_from_csv(args.chunk_embeddings_file, "chunk_embedding_")
            if loaded_chunk_embeddings is not None:
                # Filter to valid chunks only (same as what compute_similarity_per_row will do)
                valid_mask = df[args.chunk_col].notna() & (df[args.chunk_col].astype(str).str.strip() != "")
                num_valid = valid_mask.sum()
                
                if len(loaded_chunk_embeddings) == num_valid:
                    chunk_embeddings = loaded_chunk_embeddings
                    logger.info(f"Loaded {len(chunk_embeddings)} chunk embeddings matching {num_valid} valid chunks")
                elif len(loaded_chunk_embeddings) == len(df):
                    # Embeddings for all rows, filter to valid
                    chunk_embeddings = loaded_chunk_embeddings[valid_mask.values]
                    logger.info(f"Filtered {len(loaded_chunk_embeddings)} embeddings to {len(chunk_embeddings)} valid chunks")
                else:
                    logger.warning(
                        f"Embedding count mismatch: {len(loaded_chunk_embeddings)} embeddings for "
                        f"{num_valid} valid chunks (or {len(df)} total rows). Will compute embeddings."
                    )
            else:
                logger.warning("Failed to load chunk embeddings, will compute them")
        
        if criteria_embeddings is None and args.criteria_embeddings_file:
            logger.info(f"Loading criteria embeddings from: {args.criteria_embeddings_file}")
            loaded_criteria_embeddings = load_embeddings_from_csv(args.criteria_embeddings_file, "criteria_embedding_")
            if loaded_criteria_embeddings is not None:
                # Filter to valid chunks only
                valid_mask = df[args.chunk_col].notna() & (df[args.chunk_col].astype(str).str.strip() != "")
                num_valid = valid_mask.sum()
                
                if len(loaded_criteria_embeddings) == num_valid:
                    criteria_embeddings = loaded_criteria_embeddings
                    logger.info(f"Loaded {len(criteria_embeddings)} criteria embeddings matching {num_valid} valid chunks")
                elif len(loaded_criteria_embeddings) == len(df):
                    # Embeddings for all rows, filter to valid
                    criteria_embeddings = loaded_criteria_embeddings[valid_mask.values]
                    logger.info(f"Filtered {len(loaded_criteria_embeddings)} embeddings to {len(criteria_embeddings)} valid chunks")
                else:
                    logger.warning(
                        f"Embedding count mismatch: {len(loaded_criteria_embeddings)} embeddings for "
                        f"{num_valid} valid chunks (or {len(df)} total rows). Will compute embeddings."
                    )
            else:
                logger.warning("Failed to load criteria embeddings, will compute them")
        
        # 3. Get DocumentAnalyzer if we need to compute embeddings
        analyzer = None
        if chunk_embeddings is None or criteria_embeddings is None:
            analyzer = get_analyzer()
        
        # 4. Compute similarity per row (each chunk with its own criteria description)
        logger.info("Computing similarity: each chunk compared with its own criteria description")
        df_output = compute_similarity_per_row(
            df=df,
            analyzer=analyzer,
            chunk_col=args.chunk_col,
            criteria_col=args.criteria_col,
            description_col=args.description_col,
            batch_size=args.batch_size,
            chunk_embeddings=chunk_embeddings,
            criteria_embeddings=criteria_embeddings
        )
        
        # 5. Save embeddings if requested
        if args.save_embeddings:
            output_path = Path(args.output)
            output_dir = output_path.parent
            
            # Extract embeddings from compute_similarity_per_row if they were computed
            # Note: We need to recompute embeddings to save them, or use the ones we already have
            if chunk_embeddings is None or criteria_embeddings is None:
                # Embeddings were computed inside compute_similarity_per_row, but not stored
                # We need to recompute them to save
                logger.warning(
                    "Embeddings were computed but not stored. To save embeddings, "
                    "they need to be computed separately. Re-computing embeddings for saving..."
                )
                if analyzer is None:
                    analyzer = get_analyzer()
                
                # Re-compute embeddings for saving
                valid_mask = df_output[args.chunk_col].notna() & (df_output[args.chunk_col].astype(str).str.strip() != "")
                valid_df = df_output[valid_mask].copy()
                
                chunk_texts = []
                criteria_descriptions = []
                for _, row in valid_df.iterrows():
                    chunk_text = str(row.get(args.chunk_col, ""))
                    criteria_name = str(row.get(args.criteria_col, ""))
                    description = str(row.get(args.description_col, ""))
                    
                    if pd.notna(description) and str(description).strip():
                        criteria_text = f"{criteria_name}: {description}"
                    else:
                        criteria_text = str(criteria_name)
                    
                    chunk_texts.append(chunk_text)
                    criteria_descriptions.append(criteria_text)
                
                # Embed in batches
                all_chunk_embeddings = []
                all_criteria_embeddings = []
                for i in range(0, len(chunk_texts), args.batch_size):
                    batch_chunks = chunk_texts[i:i + args.batch_size]
                    batch_criteria = criteria_descriptions[i:i + args.batch_size]
                    
                    chunk_emb = embed_texts(batch_chunks, analyzer, batch_size=len(batch_chunks), description="chunks")
                    criteria_emb = embed_texts(batch_criteria, analyzer, batch_size=len(batch_criteria), description="criteria")
                    
                    all_chunk_embeddings.append(chunk_emb)
                    all_criteria_embeddings.append(criteria_emb)
                
                chunk_embeddings = np.vstack(all_chunk_embeddings) if all_chunk_embeddings else np.array([])
                criteria_embeddings = np.vstack(all_criteria_embeddings) if all_criteria_embeddings else np.array([])
            
            # Save embeddings if we have them
            if chunk_embeddings is not None and criteria_embeddings is not None and len(chunk_embeddings) > 0:
                chunk_emb_path = output_dir / "chunk_embeddings.csv"
                criteria_emb_path = output_dir / "criteria_embeddings.csv"
                save_embeddings_to_csv(chunk_embeddings, chunk_emb_path, "chunk_embedding_")
                save_embeddings_to_csv(criteria_embeddings, criteria_emb_path, "criteria_embedding_")
                logger.info(f"Saved embeddings to {chunk_emb_path} and {criteria_emb_path}")
            else:
                logger.warning("Could not save embeddings: embeddings not available")
        
        # 8. Save output CSV
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Saving output to: {output_path}")
        df_output.to_csv(output_path, index=False)
        
        logger.info(f"Successfully saved {len(df_output)} rows to {output_path}")
        logger.info(f"Added embedding_similarity_score column (each chunk compared with its own criteria)")
        
        # Print summary statistics
        if "embedding_similarity_score" in df_output.columns:
            valid_scores = df_output["embedding_similarity_score"].dropna()
            if len(valid_scores) > 0:
                logger.info(f"\nSimilarity Score Statistics:")
                logger.info(f"  Mean: {valid_scores.mean():.4f}")
                logger.info(f"  Median: {valid_scores.median():.4f}")
                logger.info(f"  Min: {valid_scores.min():.4f}")
                logger.info(f"  Max: {valid_scores.max():.4f}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())


