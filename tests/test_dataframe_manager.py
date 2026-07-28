import pandas as pd
import pytest

from report_analyst.core.dataframe_manager import (
    create_analysis_dataframes,
    format_list_field,
)


def test_format_list_field_with_evidence():
    """Test that format_list_field properly formats evidence dictionaries"""
    # Test with evidence dictionary format
    evidence_list = [
        {
            "chunk": 3,
            "text": "CO2 emissions in Scope 1, 2 for the Kyocera Document Solutions Group in FY 2024: Total for the group 40,613 [t-CO2]",
            "chunk_text": "- 14 - \n \n \nCO2 emissions in Scope 1, 2 for the Kyocera Document Solutions Group in FY 2024...",
            "score": 1.0,
            "order": 1,
            "metadata": {"total_pages": 44, "source": "15"},
        },
        {
            "chunk": 1,
            "text": "Additional evidence from first chunk",
            "chunk_text": "Full chunk text...",
            "score": 0.8,
            "order": 2,
            "metadata": {"source": "1"},
        },
    ]

    formatted = format_list_field(evidence_list)

    # Should format as bullet points with chunk references
    expected_lines = [
        "• CO2 emissions in Scope 1, 2 for the Kyocera Document Solutions Group in FY 2024: Total for the group 40,613 [t-CO2] [Chunk 3]",
        "• Additional evidence from first chunk [Chunk 1]",
    ]

    assert formatted == "\n".join(expected_lines)
    assert "[Chunk 3]" in formatted
    assert "[Chunk 1]" in formatted
    assert "•" in formatted


def test_format_list_field_with_simple_list():
    """Test format_list_field with simple string list"""
    simple_list = ["First item", "Second item", "Third item"]

    formatted = format_list_field(simple_list)
    expected = "• First item\n• Second item\n• Third item"

    assert formatted == expected


def test_format_list_field_with_empty_list():
    """Test format_list_field with empty list"""
    formatted = format_list_field([])
    assert formatted == ""


def test_format_list_field_with_string():
    """Test format_list_field with string input"""
    formatted = format_list_field("Already a string")
    assert formatted == "Already a string"


def test_create_analysis_dataframes_with_evidence():
    """Test that create_analysis_dataframes properly formats evidence in the Key Evidence column"""
    cached_results = {
        "ev_24": {
            "result": {
                "ANSWER": "No data reported for Scope 1 CO₂ emissions for the year 2022.",
                "SCORE": 2,
                "EVIDENCE": [
                    {
                        "chunk": 3,
                        "text": "CO2 emissions data for FY 2024",
                        "chunk_text": "Full chunk text...",
                        "score": 1.0,
                        "order": 1,
                        "metadata": {"source": "15"},
                    }
                ],
                "GAPS": ["Specific Scope 1 CO₂ emissions for 2022"],
                "SOURCES": [3],
            },
            "chunks": [],
        }
    }

    analysis_df, chunks_df = create_analysis_dataframes(cached_results)

    # Check that analysis dataframe was created correctly
    assert len(analysis_df) == 1
    assert analysis_df.iloc[0]["Question ID"] == "ev_24"
    assert analysis_df.iloc[0]["Analysis"] == "No data reported for Scope 1 CO₂ emissions for the year 2022."
    assert analysis_df.iloc[0]["Score"] == 2

    # Most importantly, check that Key Evidence is properly formatted
    key_evidence = analysis_df.iloc[0]["Key Evidence"]
    assert "• CO2 emissions data for FY 2024 [Chunk 3]" in key_evidence
    assert not key_evidence.startswith("{")  # Should not be raw dictionary
    assert "[Chunk 3]" in key_evidence


def test_create_analysis_dataframes_with_gaps_and_sources():
    """Test that gaps and sources are also properly formatted"""
    cached_results = {
        "tcfd_1": {
            "result": {
                "ANSWER": "Test answer",
                "SCORE": 8,
                "EVIDENCE": [],
                "GAPS": ["Missing data point 1", "Missing data point 2"],
                "SOURCES": [1, 2, 3],
            },
            "chunks": [],
        }
    }

    analysis_df, chunks_df = create_analysis_dataframes(cached_results)

    # Check that gaps and sources are formatted as bullet points
    gaps = analysis_df.iloc[0]["Gaps"]
    sources = analysis_df.iloc[0]["Sources"]

    assert "• Missing data point 1" in gaps
    assert "• Missing data point 2" in gaps
    assert "• 1" in sources
    assert "• 2" in sources
    assert "• 3" in sources


def test_create_analysis_dataframes_with_chunks():
    """Test that chunks dataframe is created correctly with similarity scores"""
    cached_results = {
        "ev_24": {
            "result": {
                "ANSWER": "Test",
                "SCORE": 5,
                "EVIDENCE": [],
                "GAPS": [],
                "SOURCES": [],
            },
            "chunks": [
                {
                    "text": "High similarity chunk",
                    "similarity_score": 0.95,
                    "llm_score": None,
                    "is_evidence": True,
                    "chunk_order": 0,
                },
                {
                    "text": "Lower similarity chunk",
                    "similarity_score": 0.75,
                    "llm_score": 0.8,
                    "is_evidence": False,
                    "chunk_order": 1,
                },
            ],
        }
    }

    analysis_df, chunks_df = create_analysis_dataframes(cached_results)

    # Check chunks dataframe
    assert len(chunks_df) == 2
    assert chunks_df.iloc[0]["Vector Similarity"] == 0.95
    assert chunks_df.iloc[1]["Vector Similarity"] == 0.75
    assert chunks_df.iloc[0]["Is Evidence"] == True  # Use == instead of is for pandas bool
    assert chunks_df.iloc[1]["Is Evidence"] == False  # Use == instead of is for pandas bool
    assert pd.isna(chunks_df.iloc[0]["LLM Score"])  # None should become NaN
    assert chunks_df.iloc[1]["LLM Score"] == 0.8
