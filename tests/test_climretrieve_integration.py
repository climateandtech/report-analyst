"""
Integration test for ClimRetrieve benchmark datasets.

This test downloads datasets from GitHub and runs the benchmark evaluation.
"""

import sys
import tempfile
from pathlib import Path
from typing import Optional

import pytest
import requests

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from report_analyst.core.benchmark.evaluation_engine import EvaluationEngine
from report_analyst.core.benchmark.retrieval_results_loader import (
    load_flexible_dataset_from_csv,
)


@pytest.fixture
def climretrieve_data_dir(tmp_path):
    """Create temporary directory for ClimRetrieve datasets"""
    data_dir = tmp_path / "climretrieve"
    data_dir.mkdir()
    return data_dir


def download_github_file(repo: str, file_path: str, output_path: Path) -> Path:
    """Download a file from GitHub raw content"""
    url = f"https://raw.githubusercontent.com/{repo}/main/{file_path}"

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)

        return output_path
    except requests.RequestException as e:
        pytest.skip(f"Could not download from GitHub: {e}")


def find_csv_in_directory(repo: str, directory: str) -> Optional[str]:
    """Find first CSV file in a GitHub directory"""
    # Try GitHub API first
    api_url = f"https://api.github.com/repos/{repo}/contents/{directory}"
    try:
        response = requests.get(api_url, timeout=30)
        response.raise_for_status()
        contents = response.json()

        if isinstance(contents, dict):
            contents = [contents]

        csv_files = [
            item["name"]
            for item in contents
            if item.get("type") == "file" and item["name"].endswith(".csv")
        ]

        if csv_files:
            return csv_files[0]
    except:
        pass

    # Fallback: try common names
    common_names = ["dataset.csv", "data.csv", "results.csv", "benchmark.csv"]
    for name in common_names:
        test_url = f"https://raw.githubusercontent.com/{repo}/main/{directory}/{name}"
        try:
            response = requests.head(test_url, timeout=10)
            if response.status_code == 200:
                return name
        except:
            continue

    return None


@pytest.mark.integration
def test_climretrieve_reference_dataset_download(climretrieve_data_dir):
    """Test downloading ClimRetrieve reference dataset"""
    repo = "tobischimanski/ClimRetrieve"
    directory = "Expert-Annotated Relevant Sources Dataset"

    csv_file = find_csv_in_directory(repo, directory)
    if csv_file is None:
        pytest.skip("Could not find CSV file in reference dataset directory")

    file_path = f"{directory}/{csv_file}"
    output_path = climretrieve_data_dir / f"reference_{csv_file}"

    downloaded = download_github_file(repo, file_path, output_path)

    assert downloaded.exists()
    assert downloaded.stat().st_size > 0


@pytest.mark.integration
def test_climretrieve_input_dataset_download(climretrieve_data_dir):
    """Test downloading ClimRetrieve input dataset"""
    repo = "tobischimanski/ClimRetrieve"
    directory = "Report-Level Dataset"

    csv_file = find_csv_in_directory(repo, directory)
    if csv_file is None:
        pytest.skip("Could not find CSV file in input dataset directory")

    file_path = f"{directory}/{csv_file}"
    output_path = climretrieve_data_dir / f"input_{csv_file}"

    downloaded = download_github_file(repo, file_path, output_path)

    assert downloaded.exists()
    assert downloaded.stat().st_size > 0


@pytest.mark.integration
def test_climretrieve_dataset_loading(climretrieve_data_dir):
    """Test loading ClimRetrieve datasets"""
    repo = "tobischimanski/ClimRetrieve"

    # Download reference dataset
    ref_dir = "Expert-Annotated Relevant Sources Dataset"
    ref_csv = find_csv_in_directory(repo, ref_dir)
    if ref_csv is None:
        pytest.skip("Could not find reference dataset")

    ref_path = climretrieve_data_dir / f"reference_{ref_csv}"
    download_github_file(repo, f"{ref_dir}/{ref_csv}", ref_path)

    # Download input dataset
    input_dir = "Report-Level Dataset"
    input_csv = find_csv_in_directory(repo, input_dir)
    if input_csv is None:
        pytest.skip("Could not find input dataset")

    input_path = climretrieve_data_dir / f"input_{input_csv}"
    download_github_file(repo, f"{input_dir}/{input_csv}", input_path)

    # Load datasets
    reference = load_flexible_dataset_from_csv(
        csv_path=str(ref_path),
        dataset_id="climretrieve_reference",
        dataset_name="ClimRetrieve Reference",
    )

    assert reference is not None
    assert len(reference.results) > 0

    input_dataset = load_flexible_dataset_from_csv(
        csv_path=str(input_path),
        dataset_id="climretrieve_input",
        dataset_name="ClimRetrieve Input",
    )

    assert input_dataset is not None
    assert len(input_dataset.results) > 0


@pytest.mark.integration
def test_climretrieve_benchmark_evaluation(climretrieve_data_dir):
    """Test running benchmark evaluation on ClimRetrieve datasets"""
    repo = "tobischimanski/ClimRetrieve"

    # Download reference dataset
    ref_dir = "Expert-Annotated Relevant Sources Dataset"
    ref_csv = find_csv_in_directory(repo, ref_dir)
    if ref_csv is None:
        pytest.skip("Could not find reference dataset")

    ref_path = climretrieve_data_dir / f"reference_{ref_csv}"
    download_github_file(repo, f"{ref_dir}/{ref_csv}", ref_path)

    # Download input dataset
    input_dir = "Report-Level Dataset"
    input_csv = find_csv_in_directory(repo, input_dir)
    if input_csv is None:
        pytest.skip("Could not find input dataset")

    input_path = climretrieve_data_dir / f"input_{input_csv}"
    download_github_file(repo, f"{input_dir}/{input_csv}", input_path)

    # Load datasets
    reference = load_flexible_dataset_from_csv(
        csv_path=str(ref_path),
        dataset_id="climretrieve_reference",
        dataset_name="ClimRetrieve Reference",
    )

    input_dataset = load_flexible_dataset_from_csv(
        csv_path=str(input_path),
        dataset_id="climretrieve_input",
        dataset_name="ClimRetrieve Input",
    )

    # Run evaluation
    engine = EvaluationEngine()
    metrics = engine.compare_flexible_datasets(
        reference_dataset=reference, input_dataset=input_dataset, k_values=[1, 3, 5, 10]
    )

    # Assertions
    assert metrics is not None
    assert metrics.mean_average_precision >= 0.0
    assert metrics.mean_average_precision <= 1.0
    assert metrics.mean_reciprocal_rank >= 0.0
    assert metrics.mean_reciprocal_rank <= 1.0

    # Check that we have metrics for at least one K value
    assert len(metrics.precision_at_k) > 0
    assert len(metrics.recall_at_k) > 0

    # Verify metrics are in valid range
    for k, score in metrics.precision_at_k.items():
        assert 0.0 <= score <= 1.0, f"Precision@{k} out of range: {score}"

    for k, score in metrics.recall_at_k.items():
        assert 0.0 <= score <= 1.0, f"Recall@{k} out of range: {score}"
