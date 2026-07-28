"""Additional coverage for retrieval results loader."""

import sqlite3
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from report_analyst.core.benchmark.retrieval_results_loader import (
    export_retrieval_results_to_csv,
    load_flexible_dataset_from_normalized_df,
    load_retrieval_results_from_csv,
    load_retrieval_results_from_sqlite,
)
from report_analyst.models.benchmark import (
    BenchmarkDataset,
    FlexibleDatasetRow,
)


def test_load_retrieval_results_from_csv_content_and_bytes():
    csv_text = "query_id,chunk_id,position,score\nq1,c1,1,0.9\n"
    ds = load_retrieval_results_from_csv(csv_content=csv_text, dataset_name="up")
    assert len(ds.results) == 1
    assert ds.results[0].query_id == "q1"

    ds_b = load_retrieval_results_from_csv(csv_content=csv_text.encode("utf-8"))
    assert len(ds_b.results) == 1


def test_load_retrieval_results_from_csv_file_and_optional_cols():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        f.write("query_id,report_id,chunk_id,chunk_text,position,score,similarity_score,llm_score,extra\n")
        f.write("q1,r1,c1,hello,1,0.9,0.8,0.7,x\n")
        path = f.name
    try:
        ds = load_retrieval_results_from_csv(csv_path=path, dataset_id="fixed")
        assert ds.dataset_id == "fixed"
        assert ds.results[0].report_id == "r1"
        assert ds.results[0].similarity_score == 0.8
        assert ds.results[0].metadata.get("extra") == "x"
    finally:
        Path(path).unlink()


def test_load_retrieval_results_from_csv_errors(tmp_path):
    with pytest.raises(ValueError, match="Either csv_path"):
        load_retrieval_results_from_csv()
    with pytest.raises(FileNotFoundError):
        load_retrieval_results_from_csv(csv_path=str(tmp_path / "does-not-exist-ra.csv"))
    with pytest.raises(ValueError, match="Missing required"):
        load_retrieval_results_from_csv(csv_content="a,b\n1,2\n")


def test_load_retrieval_results_from_sqlite_and_export():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        db_path = tmp.name
    try:
        conn = sqlite3.connect(db_path)
        conn.execute(
            """
            CREATE TABLE retrieval_results (
                query_id TEXT, report_id TEXT, chunk_id TEXT, chunk_text TEXT,
                position INTEGER, score REAL, similarity_score REAL, llm_score REAL
            )
            """
        )
        conn.execute("INSERT INTO retrieval_results VALUES ('q1','r1','c1','t',1,0.9,0.8,0.7)")
        conn.commit()
        conn.close()

        ds = load_retrieval_results_from_sqlite(db_path, dataset_name="sql")
        assert len(ds.results) == 1
        assert ds.results[0].chunk_id == "c1"
        assert ds.results[0].query_id == "q1"
    finally:
        Path(db_path).unlink(missing_ok=True)


def test_load_flexible_dataset_from_normalized_df():
    df = pd.DataFrame(
        {
            "query_id": ["q1"],
            "chunk_id": ["c1"],
            "position": [1],
            "score": [0.5],
            "paragraph": ["p"],
        }
    )
    ds = load_flexible_dataset_from_normalized_df(df, dataset_id="n1", dataset_name="norm")
    assert ds.dataset_id == "n1"
    assert len(ds.results) == 1
    assert ds.results[0].get_chunk_id() == "c1"

    with pytest.raises(ValueError, match="Missing"):
        load_flexible_dataset_from_normalized_df(pd.DataFrame({"query_id": [1]}))


def test_export_retrieval_results_to_csv_accepts_benchmark_dataset():
    ds = BenchmarkDataset(
        dataset_id="b",
        name="b",
        results=[FlexibleDatasetRow(data={"query_id": "q1", "chunk_id": "c1", "position": 1, "score": 0.1})],
    )
    out = Path(tempfile.mkdtemp()) / "flex.csv"
    export_retrieval_results_to_csv(ds, str(out))
    assert out.exists()
    assert "q1" in out.read_text()
