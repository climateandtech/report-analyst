"""Unit tests for error-analysis dataframe builders."""

from types import SimpleNamespace

from report_analyst.core.benchmark.error_analysis import (
    build_error_analysis_dataframe,
    build_error_analysis_dataframe_from_flexible,
)
from report_analyst.models.benchmark import (
    BenchmarkDataset,
    BenchmarkDatasetContent,
    BenchmarkQuestion,
    DatasetType,
    FlexibleDatasetRow,
    GroundTruthChunk,
    RetrievalResultRow,
)


def _ground_truth_content() -> BenchmarkDatasetContent:
    chunks = [
        GroundTruthChunk(
            chunk_id="c1",
            relevance_score=1.0,
            is_evidence=True,
            evidence_order=1,
            annotation_notes="relevant text A",
            text="relevant text A",
            metadata={"document": "Report A"},
        ),
        GroundTruthChunk(
            chunk_id="c2",
            relevance_score=0.0,
            is_evidence=False,
            annotation_notes="noise",
            text="noise",
        ),
    ]
    question = BenchmarkQuestion(
        question_id="q1",
        question_text="What is X?",
        ground_truth_chunks=chunks,
    )
    return BenchmarkDatasetContent(
        dataset_id="gt",
        name="GT",
        description="test",
        version="1.0",
        question_set="tcfd",
        created_at="2024-01-01",
        questions=[question],
    )


def test_build_error_analysis_dataframe_marks_relevant_chunks():
    gt = _ground_truth_content()
    retrieval = [
        RetrievalResultRow(query_id="q1", chunk_id="c1", position=1, score=0.9, chunk_text="hit"),
        RetrievalResultRow(query_id="q1", chunk_id="c2", position=2, score=0.5, chunk_text="miss"),
        RetrievalResultRow(query_id="q1", chunk_id="c3", position=3, score=0.1, chunk_text="extra"),
    ]

    df = build_error_analysis_dataframe(gt, retrieval, top_k=2)

    assert len(df) == 2
    assert list(df["chunk_id"]) == ["c1", "c2"]
    assert bool(df.iloc[0]["is_really_relevant"]) is True
    assert bool(df.iloc[1]["is_really_relevant"]) is False
    assert df.iloc[0]["question"] == "What is X?"
    assert df.iloc[0]["report_name"] == "Report A"
    assert df.iloc[0]["relevant_part_text"] == "relevant text A"


def test_build_error_analysis_dataframe_empty_when_no_results():
    gt = _ground_truth_content()
    df = build_error_analysis_dataframe(gt, [], top_k=5)
    assert df.empty


def test_build_error_analysis_dataframe_from_flexible_main_path():
    query_id = "Report A|||What is X?"
    gt = BenchmarkDataset(
        dataset_id="gt",
        name="GT",
        dataset_type=DatasetType.INFORMATION_RETRIEVAL,
        results=[
            FlexibleDatasetRow(
                data={
                    "query_id": query_id,
                    "chunk_id": "rel1",
                    "Relevant": "gold relevant text",
                    "document": "Report A",
                    "question": "What is X?",
                    "relevance_score": 2.0,
                }
            )
        ],
    )
    bench = BenchmarkDataset(
        dataset_id="bm",
        name="BM",
        dataset_type=DatasetType.INFORMATION_RETRIEVAL,
        results=[
            FlexibleDatasetRow(
                data={
                    "query_id": query_id,
                    "chunk_id": "p1",
                    "paragraph": "retrieved para",
                    "relevant_part_id": "rel1",
                    "relevant_text_sim": 0.99,
                    "relevance_label": 2,
                    "report": "Report A",
                    "question": "What is X?",
                    "position": 1,
                }
            ),
            FlexibleDatasetRow(
                data={
                    "query_id": query_id,
                    "chunk_id": "p2",
                    "paragraph": "other para",
                    "relevant_part_id": "rel1",
                    "relevant_text_sim": 0.5,
                    "relevance_label": "0",
                    "report": "Report A",
                    "question": "What is X?",
                    "position": 2,
                }
            ),
            # Duplicate chunk+part keeps higher sim
            FlexibleDatasetRow(
                data={
                    "query_id": query_id,
                    "chunk_id": "p1",
                    "paragraph": "retrieved para better",
                    "relevant_part_id": "rel1",
                    "relevant_text_sim": 0.995,
                    "relevance_label": 1,
                    "report": "Report A",
                    "question": "What is X?",
                    "position": 1,
                }
            ),
        ],
    )

    df = build_error_analysis_dataframe_from_flexible(gt, bench, top_k=2)

    assert len(df) == 2
    assert df.iloc[0]["chunk_id"] == "p1"
    assert bool(df.iloc[0]["is_really_relevant"]) is True
    assert "gold relevant text" in df.iloc[0]["relevant_part_text"]
    assert df.iloc[0]["position_in_top_k"] == 1


def test_build_error_analysis_dataframe_from_flexible_skips_pairs_without_gt():
    bench = BenchmarkDataset(
        dataset_id="bm",
        name="BM",
        results=[
            FlexibleDatasetRow(
                data={
                    "query_id": "R|||Q",
                    "chunk_id": "p1",
                    "paragraph": "x",
                    "relevant_text_sim": 0.9,
                    "report": "R",
                    "question": "Q",
                }
            )
        ],
    )
    gt = BenchmarkDataset(dataset_id="gt", name="GT", results=[])
    df = build_error_analysis_dataframe_from_flexible(gt, bench, top_k=5)
    assert df.empty


def test_build_error_analysis_dataframe_from_flexible_query_fallback():
    """When report/question cannot be parsed, fall back to query_id matching."""
    gt = BenchmarkDataset(
        dataset_id="gt",
        name="GT",
        results=[
            FlexibleDatasetRow(
                data={
                    "query_id": "q_only",
                    "chunk_id": "c1",
                    "context": "gt text",
                    "score": 1.0,
                }
            )
        ],
    )
    bench = BenchmarkDataset(
        dataset_id="bm",
        name="BM",
        results=[
            FlexibleDatasetRow(
                data={
                    "query_id": "q_only",
                    "chunk_id": "c1",
                    "paragraph": "retrieved",
                    "score": 0.8,
                }
            ),
            FlexibleDatasetRow(
                data={
                    "query_id": "q_only",
                    "chunk_id": "",  # skipped in fallback
                    "paragraph": "no id",
                    "score": 0.7,
                }
            ),
        ],
    )

    df = build_error_analysis_dataframe_from_flexible(gt, bench, top_k=3)

    assert len(df) == 1
    assert df.iloc[0]["chunk_id"] == "c1"
    assert bool(df.iloc[0]["is_really_relevant"]) is True
    assert df.iloc[0]["relevant_part_text"] == "gt text"


def test_build_error_analysis_dataframe_from_flexible_skips_incomplete_gt_rows():
    gt = BenchmarkDataset(
        dataset_id="gt",
        name="GT",
        results=[
            FlexibleDatasetRow(data={"query_id": "", "chunk_id": "c1"}),
            FlexibleDatasetRow(data={"query_id": "q1", "chunk_id": ""}),
        ],
    )
    bench = BenchmarkDataset(
        dataset_id="bm",
        name="BM",
        results=[FlexibleDatasetRow(data={"query_id": "", "chunk_id": "x"})],
    )
    df = build_error_analysis_dataframe_from_flexible(gt, bench, top_k=1)
    assert df.empty


def test_build_error_analysis_dataframe_from_flexible_string_relevance_invalid():
    query_id = "Doc|||Ask"
    gt = BenchmarkDataset(
        dataset_id="gt",
        name="GT",
        results=[
            FlexibleDatasetRow(
                data={
                    "query_id": query_id,
                    "chunk_id": "rel",
                    "relevant": "gold",
                    "document": "Doc",
                    "question": "Ask",
                    "score": 1,
                }
            )
        ],
    )
    bench = BenchmarkDataset(
        dataset_id="bm",
        name="BM",
        results=[
            FlexibleDatasetRow(
                data={
                    "query_id": query_id,
                    "chunk_id": "p1",
                    "paragraph": "p",
                    "relevant_part_id": "other",
                    "relevant_text_sim": 0.2,
                    "relevance_label": "not-a-number",
                    "report": "Doc",
                    "question": "Ask",
                }
            )
        ],
    )
    df = build_error_analysis_dataframe_from_flexible(gt, bench, top_k=1)
    assert len(df) == 1
    assert bool(df.iloc[0]["is_really_relevant"]) is False
    # Falls back to highest-score GT part for the report/question pair
    assert df.iloc[0]["relevant_part_text"] == "gold"


def test_build_error_analysis_uses_simple_namespace_text_attr():
    """Legacy callers may pass objects with `.text` instead of question_text."""
    chunk = SimpleNamespace(chunk_id="c1", relevance_score=0.5, text="t", metadata={"report": "R"})
    question = SimpleNamespace(question_id="q1", text="Q?", ground_truth_chunks=[chunk])
    gt = SimpleNamespace(questions=[question])
    retrieval = [RetrievalResultRow(query_id="q1", chunk_id="c1", position=1, score=0.1)]
    df = build_error_analysis_dataframe(gt, retrieval, top_k=1)  # type: ignore[arg-type]
    assert df.iloc[0]["question"] == "Q?"
    assert df.iloc[0]["report_name"] == "R"
