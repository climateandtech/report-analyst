import asyncio
import json
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

import pandas as pd
import pytest
import streamlit as st
import yaml

from report_analyst.core.analyzer import DocumentAnalyzer
from report_analyst.core.cache_manager import CacheManager

# Use relative imports
from report_analyst.streamlit_app import (
    ReportAnalyzer,
    display_dataframes,
    save_uploaded_file,
)


@pytest.fixture
def mock_streamlit():
    """Mock main Streamlit functions"""
    with patch("streamlit.set_page_config") as mock_config, patch(
        "streamlit.title"
    ) as mock_title, patch("streamlit.session_state", {}) as mock_state, patch(
        "streamlit.selectbox"
    ) as mock_select, patch(
        "streamlit.expander"
    ) as mock_expander, patch(
        "streamlit.columns"
    ) as mock_columns:

        # Setup mock columns
        mock_col = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col]

        yield {
            "config": mock_config,
            "title": mock_title,
            "state": mock_state,
            "select": mock_select,
            "expander": mock_expander,
            "columns": mock_columns,
        }


@pytest.fixture
def test_env():
    """Setup test environment with necessary files and directories"""
    temp_dir = tempfile.mkdtemp()
    print(f"\nSetting up test environment in: {temp_dir}")

    # Create storage structure
    storage_path = Path(temp_dir) / "storage"
    cache_path = storage_path / "cache"
    cache_path.mkdir(parents=True)

    # Create test database
    db_path = cache_path / "analysis.db"
    conn = sqlite3.connect(db_path)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS analysis_cache (
            file_path TEXT,
            question_id TEXT,
            chunk_size INTEGER,
            chunk_overlap INTEGER,
            top_k INTEGER,
            model TEXT,
            question_set TEXT,
            result TEXT,
            created_at TEXT,
            PRIMARY KEY (file_path, question_id, chunk_size, chunk_overlap, top_k, model, question_set)
        )
    """
    )
    conn.close()

    # Create test question set
    questions_dir = Path(temp_dir) / "questionsets"
    questions_dir.mkdir(parents=True)
    with open(questions_dir / "tcfd_questions.yaml", "w") as f:
        yaml.dump(
            {
                "name": "TCFD Questions",
                "description": "Test TCFD questions",
                "questions": [
                    {
                        "id": "tcfd_1",
                        "text": "Test question 1",
                        "guidelines": "Test guidelines 1",
                    },
                    {
                        "id": "tcfd_2",
                        "text": "Test question 2",
                        "guidelines": "Test guidelines 2",
                    },
                ],
            },
            f,
        )

    # Create test PDF
    test_pdf = storage_path / "test_report.pdf"
    test_pdf.write_bytes(b"%PDF-1.4\n%Test PDF")

    # Set environment variables
    os.environ["STORAGE_PATH"] = str(storage_path)
    os.environ["QUESTIONSETS_PATH"] = str(questions_dir)
    os.environ["OPENAI_API_KEY"] = "test-key"

    yield {
        "temp_dir": temp_dir,
        "storage_path": storage_path,
        "questions_dir": questions_dir,
        "db_path": db_path,
        "test_pdf": test_pdf,
    }

    shutil.rmtree(temp_dir)


@pytest.fixture
def report_analyzer(test_env):
    """Create a ReportAnalyzer instance with test environment"""
    analyzer = ReportAnalyzer()
    analyzer.analyzer.cache_manager = CacheManager(db_path=test_env["db_path"])
    return analyzer


def test_report_analyzer_initialization(report_analyzer):
    """Test ReportAnalyzer initialization"""
    assert isinstance(report_analyzer.analyzer, DocumentAnalyzer)
    assert report_analyzer.temp_dir.exists()


def test_load_question_set(report_analyzer, test_env):
    """Test loading question sets"""
    # Mock the questions file loading
    test_questions = {
        "name": "TCFD Questions",
        "description": "Test TCFD questions",
        "questions": [
            {
                "id": "tcfd_1",
                "text": "Test question 1",
                "guidelines": "Test guidelines 1",
            },
            {
                "id": "tcfd_2",
                "text": "Test question 2",
                "guidelines": "Test guidelines 2",
            },
        ],
    }

    # Test with actual TCFD questions (not mocked)
    question_set = report_analyzer.load_question_set("tcfd")
    assert "questions" in question_set
    assert len(question_set["questions"]) == 11  # TCFD has 11 questions
    assert "tcfd_1" in question_set["questions"]
    assert "tcfd_11" in question_set["questions"]

@pytest.mark.asyncio
async def test_analyze_document(report_analyzer, test_env):
    """Test document analysis flow"""
    # Setup test data
    file_path = test_env["test_pdf"]
    questions = {
        "tcfd_1": {"number": 1, "text": "Test question 1"},
        "tcfd_2": {"number": 2, "text": "Test question 2"},
    }
    selected_questions = ["tcfd_1", "tcfd_2"]

    # Mock the analyzer's process_document method
    mock_results = [
        {"status": "processing", "message": "Analyzing..."},
        {
            "status": "complete",
            "question_id": "tcfd_1",
            "result": {"ANSWER": "Test answer 1"},
        },
        {
            "status": "complete",
            "question_id": "tcfd_2",
            "result": {"ANSWER": "Test answer 2"},
        },
    ]

    async def mock_process_document(*args, **kwargs):
        for result in mock_results:
            yield result

    with patch.object(
        report_analyzer.analyzer, "process_document", new=mock_process_document
    ):
        results = []
        async for result in report_analyzer.analyze_document(
            str(file_path), questions, selected_questions
        ):
            results.append(result)

        assert len(results) == 3
        assert results[0]["status"] == "processing"
        assert results[1]["status"] == "complete"
        assert results[2]["status"] == "complete"


def test_save_uploaded_file(test_env):
    """Test file upload handling"""
    # Mock an uploaded file
    mock_file = Mock()
    mock_file.name = "test.pdf"
    mock_file.getbuffer = Mock(return_value=b"%PDF-1.4\n%Test PDF")

    # Test saving the file
    file_path = save_uploaded_file(mock_file)
    assert file_path is not None
    assert Path(file_path).exists()
    assert Path(file_path).read_bytes() == b"%PDF-1.4\n%Test PDF"


def test_display_dataframes():
    """Test dataframe display functionality"""
    # Create test dataframes
    analysis_df = pd.DataFrame(
        {
            "Question": ["Test Q1", "Test Q2"],
            "Analysis": ["Answer 1", "Answer 2"],
            "Score": [0.8, 0.9],
        }
    )

    chunks_df = pd.DataFrame(
        {
            "Chunk Text": ["Chunk 1", "Chunk 2"],
            "Vector Similarity": [0.7, 0.8],
            "LLM Score": [0.6, 0.7],
        }
    )

    # Mock streamlit's dataframe display
    with patch("streamlit.dataframe") as mock_df:
        display_dataframes(analysis_df, chunks_df)
        assert mock_df.call_count == 2
