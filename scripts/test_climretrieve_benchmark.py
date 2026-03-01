#!/usr/bin/env python3
"""
Script to download and test ClimRetrieve benchmark datasets.

Downloads:
- Reference dataset: Expert-Annotated Relevant Sources Dataset
- Input dataset: Report-Level Dataset

Then compares them using the flexible benchmark evaluation system.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from report_analyst.core.benchmark.evaluation_engine import EvaluationEngine
from report_analyst.core.benchmark.retrieval_results_loader import (
    load_flexible_dataset_from_csv,
)
from report_analyst.models.benchmark import BenchmarkDataset, DatasetType


def download_file_from_github(
    repo: str, file_path: str, output_path: Optional[str] = None, branch: str = "main"
) -> str:
    """
    Download a file from GitHub repository.

    Args:
        repo: Repository in format "owner/repo"
        file_path: Path to file in repository (e.g., "data/dataset.csv")
        output_path: Local path to save file (if None, uses temp file)
        branch: Branch name (default: "main")

    Returns:
        Path to downloaded file
    """
    url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"

    print(f"Downloading from: {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()

    if output_path is None:
        # Create temp file
        suffix = Path(file_path).suffix
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            output_path = tmp.name

    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    # Write file
    with open(output_path, "wb") as f:
        f.write(response.content)

    print(f"Downloaded to: {output_path} ({len(response.content)} bytes)")
    return output_path


def list_github_directory(repo: str, directory_path: str, branch: str = "main") -> list:
    """
    List files in a GitHub directory using GitHub API.

    Args:
        repo: Repository in format "owner/repo"
        directory_path: Path to directory
        branch: Branch name

    Returns:
        List of file/directory names
    """
    url = f"https://api.github.com/repos/{repo}/contents/{directory_path}"
    params = {"ref": branch}

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        contents = response.json()

        # Handle both single file and directory
        if isinstance(contents, dict):
            contents = [contents]

        return [item["name"] for item in contents if item["type"] == "file"]
    except Exception as e:
        print(f"Warning: Could not list directory via API: {e}")
        return []


def find_data_files_in_directory(
    repo: str,
    directory_path: str,
    branch: str = "main",
    extensions: list = [".csv", ".xlsx", ".xls"],
) -> list:
    """
    Find data files (CSV, Excel) in a GitHub directory.

    Returns:
        List of data file paths
    """
    files = list_github_directory(repo, directory_path, branch)
    data_files = [f for f in files if any(f.endswith(ext) for ext in extensions)]
    return data_files


def download_climretrieve_datasets(
    data_dir: Path, repo: str = "tobischimanski/ClimRetrieve"
) -> tuple[str, str]:
    """
    Download ClimRetrieve datasets.

    Args:
        data_dir: Directory to save datasets
        repo: GitHub repository

    Returns:
        Tuple of (reference_dataset_path, input_dataset_path)
    """
    data_dir.mkdir(parents=True, exist_ok=True)

    # Reference dataset: Expert-Annotated Relevant Sources Dataset
    reference_dir = "Expert-Annotated%20Relevant%20Sources%20Dataset"
    reference_files = find_data_files_in_directory(
        repo, reference_dir, extensions=[".csv", ".xlsx", ".xls"]
    )

    if not reference_files:
        # Try alternative path format
        reference_dir = "Expert-Annotated Relevant Sources Dataset"
        reference_files = find_data_files_in_directory(
            repo, reference_dir, extensions=[".csv", ".xlsx", ".xls"]
        )

    if not reference_files:
        raise ValueError(f"Could not find data files in {reference_dir}")

    print(f"Found reference dataset files: {reference_files}")
    # Prefer CSV, but use Excel if available
    reference_file = next(
        (f for f in reference_files if f.endswith(".csv")), reference_files[0]
    )
    reference_path = data_dir / f"climretrieve_reference_{reference_file}"

    if not reference_path.exists():
        download_file_from_github(
            repo, f"{reference_dir}/{reference_file}", str(reference_path)
        )
    else:
        print(f"Reference dataset already exists: {reference_path}")

    # Convert Excel to CSV if needed
    if reference_path.suffix in [".xlsx", ".xls"]:
        csv_path = reference_path.with_suffix(".csv")
        if not csv_path.exists():
            print(f"Converting Excel to CSV: {reference_path} -> {csv_path}")
            df = pd.read_excel(reference_path)
            df.to_csv(csv_path, index=False)
            print(f"Converted to CSV: {csv_path}")
        reference_path = csv_path

    # Input dataset: Report-Level Dataset
    input_dir = "Report-Level%20Dataset"
    input_files = find_data_files_in_directory(
        repo, input_dir, extensions=[".csv", ".xlsx", ".xls"]
    )

    if not input_files:
        # Try alternative path format
        input_dir = "Report-Level Dataset"
        input_files = find_data_files_in_directory(
            repo, input_dir, extensions=[".csv", ".xlsx", ".xls"]
        )

    if not input_files:
        raise ValueError(f"Could not find data files in {input_dir}")

    print(f"Found input dataset files: {input_files}")
    # Prefer CSV, but use Excel if available
    input_file = next((f for f in input_files if f.endswith(".csv")), input_files[0])
    input_path = data_dir / f"climretrieve_input_{input_file}"

    if not input_path.exists():
        download_file_from_github(repo, f"{input_dir}/{input_file}", str(input_path))
    else:
        print(f"Input dataset already exists: {input_path}")

    # Convert Excel to CSV if needed
    if input_path.suffix in [".xlsx", ".xls"]:
        csv_path = input_path.with_suffix(".csv")
        if not csv_path.exists():
            print(f"Converting Excel to CSV: {input_path} -> {csv_path}")
            df = pd.read_excel(input_path)
            df.to_csv(csv_path, index=False)
            print(f"Converted to CSV: {csv_path}")
        input_path = csv_path

    return str(reference_path), str(input_path)


def inspect_dataset_columns(csv_path: str) -> None:
    """Inspect and display dataset columns and sample rows"""
    print(f"\n{'='*60}")
    print(f"Inspecting dataset: {csv_path}")
    print(f"{'='*60}")

    df = pd.read_csv(csv_path, nrows=5)
    print(f"\nColumns: {list(df.columns)}")
    print(f"\nShape: {df.shape}")
    print(f"\nFirst few rows:")
    print(df.head())
    print(f"\nData types:")
    print(df.dtypes)


def run_climretrieve_benchmark(
    reference_path: str, input_path: str, k_values: Optional[list] = None
) -> None:
    """
    Run benchmark comparison between ClimRetrieve datasets.

    Args:
        reference_path: Path to reference dataset CSV
        input_path: Path to input dataset CSV
        k_values: List of K values for evaluation
    """
    print(f"\n{'='*60}")
    print("Loading Datasets")
    print(f"{'='*60}")

    # Inspect datasets first
    inspect_dataset_columns(reference_path)
    inspect_dataset_columns(input_path)

    # Load datasets
    print(f"\n{'='*60}")
    print("Loading Reference Dataset (Expert-Annotated)")
    print(f"{'='*60}")

    # Check if we need to preprocess the CSV for ClimRetrieve format
    df_ref = pd.read_csv(reference_path, nrows=1)
    transformed_path = reference_path.replace(".csv", "_transformed.csv")

    if "Question" in df_ref.columns and "Context" in df_ref.columns:
        # ClimRetrieve reference format - need to transform
        if not Path(transformed_path).exists():
            print("Detected ClimRetrieve reference format, preprocessing...")
            df_ref_full = pd.read_csv(reference_path)
            # Transform: Question -> query_id, Context -> chunk_id (use hash of content for matching)
            # Create position based on row order per question
            import hashlib

            df_ref_full["query_id"] = df_ref_full["Question"]
            # Use hash of Context text as chunk_id for better matching
            df_ref_full["chunk_id"] = df_ref_full["Context"].apply(
                lambda x: (
                    hashlib.md5(str(x).strip().encode()).hexdigest()[:16]
                    if pd.notna(x) and str(x).strip()
                    else f"context_{hash(str(x)) % 10000}"
                )
            )
            df_ref_full["position"] = df_ref_full.groupby("Question").cumcount() + 1
            # Use Source Relevance Score if available, otherwise use Relevant (convert Yes/No to 1.0/0.0)
            if "Source Relevance Score" in df_ref_full.columns:
                df_ref_full["score"] = df_ref_full["Source Relevance Score"].fillna(0.0)
            elif "Relevant" in df_ref_full.columns:
                df_ref_full["score"] = df_ref_full["Relevant"].apply(
                    lambda x: (
                        1.0 if str(x).lower() in ["yes", "y", "1", "true"] else 0.0
                    )
                )
            else:
                df_ref_full["score"] = 1.0
            # Save transformed version
            df_ref_full[
                ["query_id", "chunk_id", "position", "score", "Context", "Question"]
            ].to_csv(transformed_path, index=False)
            print(
                f"Transformed reference dataset saved to: {transformed_path} ({len(df_ref_full)} rows)"
            )
        else:
            print(f"Using existing transformed reference dataset: {transformed_path}")
        reference_path = transformed_path

    reference_dataset = load_flexible_dataset_from_csv(
        csv_path=reference_path,
        dataset_id="climretrieve_reference",
        dataset_name="ClimRetrieve Expert-Annotated Reference",
    )

    print(f"\nLoaded {len(reference_dataset.results)} rows")
    print(f"Dataset type: {reference_dataset.dataset_type}")
    print(f"Unique queries: {len(reference_dataset.get_unique_queries())}")

    print(f"\n{'='*60}")
    print("Loading Input Dataset (Report-Level)")
    print(f"{'='*60}")

    # Check if we need to preprocess the CSV for ClimRetrieve format
    df_input = pd.read_csv(input_path, nrows=1)
    transformed_input_path = input_path.replace(".csv", "_transformed.csv")

    if "question" in df_input.columns and "paragraph" in df_input.columns:
        # ClimRetrieve input format - need to transform
        if not Path(transformed_input_path).exists():
            print("Detected ClimRetrieve input format, preprocessing...")
            df_input_full = pd.read_csv(input_path)
            # Transform: question -> query_id, paragraph/relevant_text -> chunk_id (use hash for matching)
            # Create position based on row order per question
            import hashlib

            df_input_full["query_id"] = df_input_full["question"]
            # Use hash of relevant_text (or paragraph) as chunk_id for matching with reference
            # Prefer relevant_text as it's more likely to match the Context field in reference
            if "relevant_text" in df_input_full.columns:
                content_col = df_input_full["relevant_text"]
            elif "paragraph" in df_input_full.columns:
                content_col = df_input_full["paragraph"]
            else:
                content_col = pd.Series([""] * len(df_input_full))

            df_input_full["chunk_id"] = content_col.apply(
                lambda x: (
                    hashlib.md5(str(x).strip().encode()).hexdigest()[:16]
                    if pd.notna(x) and str(x).strip()
                    else f"para_{hash(str(x)) % 10000}"
                )
            )
            df_input_full["position"] = df_input_full.groupby("question").cumcount() + 1
            # Use relevance or sim_text_relevance as score
            if "relevance" in df_input_full.columns:
                df_input_full["score"] = df_input_full["relevance"].fillna(0.0)
            elif "sim_text_relevance" in df_input_full.columns:
                df_input_full["score"] = (
                    df_input_full["sim_text_relevance"].fillna(0.0) / 3.0
                )  # Normalize 0-3 to 0-1
            else:
                df_input_full["score"] = 1.0
            # Save transformed version
            df_input_full[
                ["query_id", "chunk_id", "position", "score", "paragraph", "question"]
            ].to_csv(transformed_input_path, index=False)
            print(
                f"Transformed input dataset saved to: {transformed_input_path} ({len(df_input_full)} rows)"
            )
        else:
            print(f"Using existing transformed input dataset: {transformed_input_path}")
        input_path = transformed_input_path

    input_dataset = load_flexible_dataset_from_csv(
        csv_path=input_path,
        dataset_id="climretrieve_input",
        dataset_name="ClimRetrieve Report-Level Input",
    )

    print(f"\nLoaded {len(input_dataset.results)} rows")
    print(f"Dataset type: {input_dataset.dataset_type}")
    print(f"Unique queries: {len(input_dataset.get_unique_queries())}")

    # Compare datasets
    print(f"\n{'='*60}")
    print("Running Evaluation")
    print(f"{'='*60}")

    engine = EvaluationEngine()
    metrics = engine.compare_flexible_datasets(
        reference_dataset=reference_dataset,
        input_dataset=input_dataset,
        k_values=k_values or [1, 3, 5, 10],
    )

    # Display results
    print(f"\n{'='*60}")
    print("Evaluation Results")
    print(f"{'='*60}")
    print(f"\nMean Average Precision (MAP): {metrics.mean_average_precision:.4f}")
    print(f"Mean Reciprocal Rank (MRR): {metrics.mean_reciprocal_rank:.4f}")

    print(f"\nPrecision@K:")
    for k, score in sorted(metrics.precision_at_k.items()):
        print(f"  P@{k}: {score:.4f}")

    print(f"\nRecall@K:")
    for k, score in sorted(metrics.recall_at_k.items()):
        print(f"  R@{k}: {score:.4f}")

    print(f"\nF1@K:")
    for k, score in sorted(metrics.f1_at_k.items()):
        print(f"  F1@{k}: {score:.4f}")

    print(f"\nNDCG@K:")
    for k, score in sorted(metrics.ndcg_at_k.items()):
        print(f"  NDCG@{k}: {score:.4f}")

    return metrics


def main():
    """Main function to run ClimRetrieve benchmark test"""
    import argparse

    parser = argparse.ArgumentParser(description="Test ClimRetrieve benchmark datasets")
    parser.add_argument(
        "--data-dir",
        type=str,
        default=str(Path(__file__).parent.parent / "data" / "climretrieve"),
        help="Directory to store downloaded datasets (default: data/climretrieve)",
    )
    parser.add_argument(
        "--reference-path",
        type=str,
        help="Path to reference dataset CSV (skips download if provided)",
    )
    parser.add_argument(
        "--input-path",
        type=str,
        help="Path to input dataset CSV (skips download if provided)",
    )
    parser.add_argument(
        "--repo",
        type=str,
        default="tobischimanski/ClimRetrieve",
        help="GitHub repository",
    )
    parser.add_argument(
        "--k-values",
        type=int,
        nargs="+",
        default=[1, 3, 5, 10],
        help="K values for evaluation",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip downloading and use existing files",
    )

    args = parser.parse_args()

    data_dir = Path(args.data_dir)

    try:
        # Download datasets if not provided
        if args.reference_path and args.input_path:
            reference_path = args.reference_path
            input_path = args.input_path
            print(f"Using provided datasets:")
            print(f"  Reference: {reference_path}")
            print(f"  Input: {input_path}")
        elif args.skip_download:
            # Try to find existing files
            reference_files = list(data_dir.glob("climretrieve_reference_*.csv"))
            input_files = list(data_dir.glob("climretrieve_input_*.csv"))

            if not reference_files or not input_files:
                raise ValueError(
                    "No existing datasets found. Remove --skip-download to download."
                )

            reference_path = str(reference_files[0])
            input_path = str(input_files[0])
            print(f"Using existing datasets:")
            print(f"  Reference: {reference_path}")
            print(f"  Input: {input_path}")
        else:
            print("Downloading ClimRetrieve datasets from GitHub...")
            reference_path, input_path = download_climretrieve_datasets(
                data_dir, args.repo
            )

        # Run benchmark
        metrics = run_climretrieve_benchmark(
            reference_path, input_path, k_values=args.k_values
        )

        print(f"\n{'='*60}")
        print("Benchmark Test Complete!")
        print(f"{'='*60}")

        return 0

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
