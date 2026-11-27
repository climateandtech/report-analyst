import pandas as pd

from report_analyst.core.benchmark.dataset_mapper import (
    DatasetMapperFactory,
    DefaultDatasetMapper,
    list_available_dataset_ids,
)


def test_list_available_dataset_ids_includes_climretrieve():
    dataset_ids = list_available_dataset_ids()
    assert "climretrieve" in dataset_ids


def test_factory_returns_default_mapper_for_climretrieve():
    mapper = DatasetMapperFactory.get_mapper("climretrieve")
    assert isinstance(mapper, DefaultDatasetMapper)
    assert mapper.dataset_id == "climretrieve"


def test_default_mapper_aligns_ground_truth_climretrieve():
    # Minimal synthetic ground truth with expected columns for ClimRetrieve
    df_raw = pd.DataFrame(
        {
            "document": ["Report A", "Report A"],
            "question": ["What is X?", "What is X?"],
            "context": ["before relevant after", "before relevant2 after2"],
            "relevant": ["relevant", "relevant2"],
            "page_number": [1, 2],
            "Source Relevance Score": [2, 1],
        }
    )

    mapper = DatasetMapperFactory.get_mapper("climretrieve")
    df_aligned = mapper.align_ground_truth(df_raw)

    # Basic shape/columns checks
    assert len(df_aligned) == len(df_raw)
    for col in ["query_id", "chunk_id", "position", "score", "document", "question"]:
        assert col in df_aligned.columns

    # Scores should reflect the source relevance scores
    assert set(df_aligned["score"].tolist()) == {1.0, 2.0}

    # query_id should be consistent for rows with same (document, question)
    assert df_aligned["query_id"].nunique() == 1


def test_default_mapper_aligns_benchmark_climretrieve():
    df_raw = pd.DataFrame(
        {
            "report": ["Report A", "Report A"],
            "question": ["What is X?", "What is X?"],
            "paragraph": ["para1 text", "para2 text"],
            "relevant_text": ["rel1", "rel2"],
            "label": [2, 0],
        }
    )

    mapper = DatasetMapperFactory.get_mapper("climretrieve")
    df_aligned = mapper.align_benchmark(df_raw)

    # Basic shape/columns checks
    assert len(df_aligned) == len(df_raw)
    for col in [
        "query_id",
        "chunk_id",
        "relevant_part_id",
        "position",
        "report",
        "question",
        "paragraph",
        "relevant_text",
        "relevance_label",
    ]:
        assert col in df_aligned.columns

    # query_id should be consistent for rows with same (report, question)
    assert df_aligned["query_id"].nunique() == 1

    # Ensure relevant_part_id is derived from relevant_text (and thus differs from chunk_id)
    assert not (df_aligned["chunk_id"] == df_aligned["relevant_part_id"]).all()
