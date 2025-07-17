import pytest
from pathlib import Path
import streamlit as st
from unittest.mock import Mock, patch, AsyncMock
import tempfile
import shutil
import os
import yaml
import json
import sqlite3
import pandas as pd
from datetime import datetime
import asyncio

# Use relative imports
from app.streamlit_app import ReportAnalyzer, save_uploaded_file, display_dataframes
from app.core.analyzer import DocumentAnalyzer
from app.core.cache_manager import CacheManager

@pytest.fixture
def mock_streamlit():
    """Mock main Streamlit functions"""
    with patch('streamlit.set_page_config') as mock_config, \
         patch('streamlit.title') as mock_title, \
         patch('streamlit.session_state', {}) as mock_state, \
         patch('streamlit.selectbox') as mock_select, \
         patch('streamlit.expander') as mock_expander, \
         patch('streamlit.columns') as mock_columns:
        
        # Setup mock columns
        mock_col = Mock()
        mock_columns.return_value = [mock_col, mock_col, mock_col]
        
        yield {
            'config': mock_config,
            'title': mock_title,
            'state': mock_state,
            'select': mock_select,
            'expander': mock_expander,
            'columns': mock_columns
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
    conn.execute("""
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
    """)
    conn.close()
    
    # Create test question set
    questions_dir = Path(temp_dir) / "questionsets"
    questions_dir.mkdir(parents=True)
    with open(questions_dir / "tcfd_questions.yaml", 'w') as f:
        yaml.dump({
            'name': 'TCFD Questions',
            'description': 'Test TCFD questions',
            'questions': [
                {'id': 'tcfd_1', 'text': 'Test question 1', 'guidelines': 'Test guidelines 1'},
                {'id': 'tcfd_2', 'text': 'Test question 2', 'guidelines': 'Test guidelines 2'}
            ]
        }, f)
    
    # Create test PDF
    test_pdf = storage_path / "test_report.pdf"
    test_pdf.write_bytes(b"%PDF-1.4\n%Test PDF")
    
    # Set environment variables
    os.environ['STORAGE_PATH'] = str(storage_path)
    os.environ['QUESTIONSETS_PATH'] = str(questions_dir)
    os.environ['OPENAI_API_KEY'] = 'test-key'
    
    yield {
        'temp_dir': temp_dir,
        'storage_path': storage_path,
        'questions_dir': questions_dir,
        'db_path': db_path,
        'test_pdf': test_pdf
    }
    
    shutil.rmtree(temp_dir)

@pytest.fixture
def report_analyzer(test_env):
    """Create a ReportAnalyzer instance with test environment"""
    analyzer = ReportAnalyzer()
    analyzer.analyzer.cache_manager = CacheManager(db_path=test_env['db_path'])
    return analyzer

def test_report_analyzer_initialization(report_analyzer):
    """Test ReportAnalyzer initialization"""
    assert isinstance(report_analyzer.analyzer, DocumentAnalyzer)
    assert report_analyzer.temp_dir.exists()

def test_load_question_set(report_analyzer, test_env):
    """Test loading question sets"""
    # Mock the questions file loading
    test_questions = {
        'name': 'TCFD Questions',
        'description': 'Test TCFD questions',
        'questions': [
            {'id': 'tcfd_1', 'text': 'Test question 1', 'guidelines': 'Test guidelines 1'},
            {'id': 'tcfd_2', 'text': 'Test question 2', 'guidelines': 'Test guidelines 2'}
        ]
    }
    
    with patch('yaml.safe_load', return_value=test_questions):
        question_set = report_analyzer.load_question_set('tcfd')
        assert 'questions' in question_set
        assert len(question_set['questions']) == 2
        assert 'tcfd_1' in question_set['questions']
        assert 'tcfd_2' in question_set['questions']

@pytest.mark.asyncio
async def test_analyze_document(report_analyzer, test_env):
    """Test document analysis flow"""
    # Setup test data
    file_path = test_env['test_pdf']
    questions = {
        'tcfd_1': {'number': 1, 'text': 'Test question 1'},
        'tcfd_2': {'number': 2, 'text': 'Test question 2'}
    }
    selected_questions = ['tcfd_1', 'tcfd_2']
    
    # Mock the analyzer's process_document method
    mock_results = [
        {'status': 'processing', 'message': 'Analyzing...'},
        {'status': 'complete', 'question_id': 'tcfd_1', 'result': {'ANSWER': 'Test answer 1'}},
        {'status': 'complete', 'question_id': 'tcfd_2', 'result': {'ANSWER': 'Test answer 2'}}
    ]
    
    async def mock_process_document(*args, **kwargs):
        for result in mock_results:
            yield result
    
    with patch.object(report_analyzer.analyzer, 'process_document', 
                     new=mock_process_document):
        results = []
        async for result in report_analyzer.analyze_document(
            str(file_path),
            questions,
            selected_questions
        ):
            results.append(result)
        
        assert len(results) == 3
        assert results[0]['status'] == 'processing'
        assert results[1]['status'] == 'complete'
        assert results[2]['status'] == 'complete'

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
    analysis_df = pd.DataFrame({
        'Question': ['Test Q1', 'Test Q2'],
        'Analysis': ['Answer 1', 'Answer 2'],
        'Score': [0.8, 0.9]
    })
    
    chunks_df = pd.DataFrame({
        'Chunk Text': ['Chunk 1', 'Chunk 2'],
        'Vector Similarity': [0.7, 0.8],
        'LLM Score': [0.6, 0.7]
    })
    
    # Mock streamlit's dataframe display
    with patch('streamlit.dataframe') as mock_df:
        display_dataframes(analysis_df, chunks_df)
        assert mock_df.call_count == 2 

@pytest.mark.asyncio
async def test_consolidated_tab_after_each_step(report_analyzer, test_env):
    """Test consolidated tab display after each processing step"""
    file_path = test_env['test_pdf']
    
    # Mock configuration
    config = {
        'chunk_size': 1000,
        'chunk_overlap': 200,
        'top_k': 5,
        'model': 'gpt-3.5-turbo',
        'question_set': 'tcfd'
    }
    
    # Mock questions
    questions = {
        'tcfd_1': {'number': 1, 'text': 'Test question 1'},
        'tcfd_2': {'number': 2, 'text': 'Test question 2'}
    }
    
    # Test Step 1: After chunks generated (no embeddings)
    with patch.object(report_analyzer.analyzer, 'check_step_completion') as mock_step_status, \
         patch.object(report_analyzer.analyzer.cache_manager, 'get_document_chunks') as mock_get_chunks, \
         patch.object(report_analyzer.analyzer.cache_manager, 'check_cache_status') as mock_cache_status:
        
        # Mock cache configurations
        mock_cache_status.return_value = [
            (str(file_path), 1000, 200, 5, 'gpt-3.5-turbo', 'tcfd')
        ]
        
        # Mock step completion status after step 1
        mock_step_status.return_value = {
            'chunks': True,
            'embeddings': False,
            'scoring': False,
            'analysis': False
        }
        
        # Mock raw chunks without embeddings
        mock_chunks = [
            {'text': 'Chunk 1 text', 'chunk_text': 'Chunk 1 text', 'embedding': None, 'chunk_size': 1000, 'chunk_overlap': 200},
            {'text': 'Chunk 2 text', 'chunk_text': 'Chunk 2 text', 'embedding': None, 'chunk_size': 1000, 'chunk_overlap': 200}
        ]
        mock_get_chunks.return_value = mock_chunks
        
        # Test "All Document Chunks" view
        from app.streamlit_app import display_consolidated_results
        
        with patch('streamlit.radio', return_value="All Document Chunks"), \
             patch('streamlit.dataframe') as mock_dataframe, \
             patch('streamlit.info') as mock_info, \
             patch('streamlit.selectbox', side_effect=[str(file_path), {'label': 'Chunk: 1000, Overlap: 200, Top-K: 5, Model: gpt-3.5-turbo', 'config': config}]):
            
            display_consolidated_results(report_analyzer, 'tcfd')
            
            # Should show all chunks without embeddings
            mock_dataframe.assert_called_once()
            call_args = mock_dataframe.call_args
            chunks_df = call_args[1]['data']
            
            assert len(chunks_df) == 2
            assert 'Chunk #' in chunks_df.columns
            assert 'Text' in chunks_df.columns
            assert 'Has Embedding' in chunks_df.columns
            assert chunks_df['Has Embedding'].all() == False  # No embeddings yet
            
            # The function shows both the chunk count and the step status
            mock_info.assert_any_call("✓ Found 2 total document chunks in this configuration.")
            mock_info.assert_any_call("Chunks created but no embeddings yet. Run Steps 2, 3, and 4 to continue.")
    
    # Test Step 2: After embeddings generated
    with patch.object(report_analyzer.analyzer, 'check_step_completion') as mock_step_status, \
         patch.object(report_analyzer.analyzer.cache_manager, 'get_document_chunks') as mock_get_chunks, \
         patch.object(report_analyzer.analyzer.cache_manager, 'check_cache_status') as mock_cache_status:
        
        # Mock cache configurations
        mock_cache_status.return_value = [
            (str(file_path), 1000, 200, 5, 'gpt-3.5-turbo', 'tcfd')
        ]
        
        # Mock step completion status after step 2
        mock_step_status.return_value = {
            'chunks': True,
            'embeddings': True,
            'scoring': False,
            'analysis': False
        }
        
        # Mock chunks with embeddings
        mock_chunks = [
            {'text': 'Chunk 1 text', 'chunk_text': 'Chunk 1 text', 'embedding': [0.1, 0.2], 'chunk_size': 1000, 'chunk_overlap': 200},
            {'text': 'Chunk 2 text', 'chunk_text': 'Chunk 2 text', 'embedding': [0.3, 0.4], 'chunk_size': 1000, 'chunk_overlap': 200}
        ]
        mock_get_chunks.return_value = mock_chunks
        
        # Test "All Document Chunks" view
        with patch('streamlit.radio', return_value="All Document Chunks"), \
             patch('streamlit.dataframe') as mock_dataframe, \
             patch('streamlit.info') as mock_info, \
             patch('streamlit.selectbox', side_effect=[str(file_path), {'label': 'Chunk: 1000, Overlap: 200, Top-K: 5, Model: gpt-3.5-turbo', 'config': config}]):
            
            display_consolidated_results(report_analyzer, 'tcfd')
            
            # Should show all chunks with embeddings
            mock_dataframe.assert_called_once()
            call_args = mock_dataframe.call_args
            chunks_df = call_args[1]['data']
            
            assert len(chunks_df) == 2
            assert chunks_df['Has Embedding'].all() == True  # Now has embeddings
            
            # The function shows both the chunk count and the step status
            mock_info.assert_any_call("✓ Found 2 total document chunks in this configuration.")
            mock_info.assert_any_call("Embeddings generated but no scoring or analysis yet. Run Steps 3 and 4 to continue.")
    
    # Test Step 3: After scoring completed
    with patch.object(report_analyzer.analyzer, 'check_step_completion') as mock_step_status, \
         patch.object(report_analyzer.analyzer.cache_manager, 'get_chunk_scoring_only') as mock_get_scoring, \
         patch.object(report_analyzer.analyzer.cache_manager, 'check_cache_status') as mock_cache_status, \
         patch.object(report_analyzer.analyzer, 'questions', questions):
        
        # Mock cache configurations
        mock_cache_status.return_value = [
            (str(file_path), 1000, 200, 5, 'gpt-3.5-turbo', 'tcfd')
        ]
        
        # Mock step completion status after step 3
        mock_step_status.return_value = {
            'chunks': True,
            'embeddings': True,
            'scoring': True,
            'analysis': False
        }
        
        # Mock scored chunks
        mock_scored_chunks = [
            {'text': 'Chunk 1 text', 'similarity_score': 0.8, 'llm_score': 0.7, 'is_evidence': True, 'chunk_order': 1},
            {'text': 'Chunk 2 text', 'similarity_score': 0.6, 'llm_score': 0.5, 'is_evidence': False, 'chunk_order': 2}
        ]
        mock_get_scoring.return_value = mock_scored_chunks
        
        # Test "Chunks by Question" view
        with patch('streamlit.radio', return_value="Chunks by Question"), \
             patch('streamlit.dataframe') as mock_dataframe, \
             patch('streamlit.success') as mock_success, \
             patch('streamlit.selectbox', side_effect=[str(file_path), {'label': 'Chunk: 1000, Overlap: 200, Top-K: 5, Model: gpt-3.5-turbo', 'config': config}]):
            
            display_consolidated_results(report_analyzer, 'tcfd')
            
            # Should show chunks with scoring for each question
            mock_dataframe.assert_called_once()
            call_args = mock_dataframe.call_args
            chunks_df = call_args[1]['data']
            
            assert len(chunks_df) == 4  # 2 questions × 2 chunks each
            assert 'Question ID' in chunks_df.columns
            assert 'Vector Similarity' in chunks_df.columns
            assert 'LLM Score' in chunks_df.columns
            assert 'Is Evidence' in chunks_df.columns
            
            mock_success.assert_called_with("✓ Found 4 chunks across 2 questions with scoring only.")
    
    # Test Step 4: After analysis completed
    with patch.object(report_analyzer.analyzer, 'check_step_completion') as mock_step_status, \
         patch.object(report_analyzer.analyzer.cache_manager, 'get_analysis') as mock_get_analysis, \
         patch.object(report_analyzer.analyzer.cache_manager, 'check_cache_status') as mock_cache_status, \
         patch.object(report_analyzer.analyzer, 'questions', questions):
        
        # Mock cache configurations
        mock_cache_status.return_value = [
            (str(file_path), 1000, 200, 5, 'gpt-3.5-turbo', 'tcfd')
        ]
        
        # Mock step completion status after step 4
        mock_step_status.return_value = {
            'chunks': True,
            'embeddings': True,
            'scoring': True,
            'analysis': True
        }
        
        # Mock analysis results with chunks
        mock_analysis_results = {
            'tcfd_1': {
                'result': {
                    'ANSWER': 'Answer 1',
                    'SCORE': 8.5,
                    'EVIDENCE': [{'text': 'Evidence 1'}],
                    'GAPS': ['Gap 1'],
                    'SOURCES': [1, 2]
                },
                'chunks': [
                    {'text': 'Chunk 1 text', 'similarity_score': 0.8, 'llm_score': 0.7, 'is_evidence': True, 'chunk_order': 1}
                ]
            },
            'tcfd_2': {
                'result': {
                    'ANSWER': 'Answer 2',
                    'SCORE': 7.0,
                    'EVIDENCE': [{'text': 'Evidence 2'}],
                    'GAPS': ['Gap 2'],
                    'SOURCES': [3, 4]
                },
                'chunks': [
                    {'text': 'Chunk 2 text', 'similarity_score': 0.6, 'llm_score': 0.5, 'is_evidence': False, 'chunk_order': 2}
                ]
            }
        }
        mock_get_analysis.return_value = mock_analysis_results
        
        # Test "Chunks by Question" view with analysis
        with patch('streamlit.radio', return_value="Chunks by Question"), \
             patch('streamlit.dataframe') as mock_dataframe, \
             patch('streamlit.success') as mock_success, \
             patch('streamlit.selectbox', side_effect=[str(file_path), {'label': 'Chunk: 1000, Overlap: 200, Top-K: 5, Model: gpt-3.5-turbo', 'config': config}]):
            
            display_consolidated_results(report_analyzer, 'tcfd')
            
            # Should show chunks from analysis results
            assert mock_dataframe.call_count == 2  # Chunks table + Analysis table
            
            # Check chunks dataframe (first call)
            chunks_call = mock_dataframe.call_args_list[0]
            chunks_df = chunks_call[1]['data']
            
            assert len(chunks_df) == 2  # 2 chunks from analysis
            assert 'Question ID' in chunks_df.columns
            assert 'Vector Similarity' in chunks_df.columns
            assert 'LLM Score' in chunks_df.columns
            assert 'Is Evidence' in chunks_df.columns
            
            # Check analysis dataframe (second call)
            analysis_call = mock_dataframe.call_args_list[1]
            analysis_df = analysis_call[1]['data']
            
            assert len(analysis_df) == 2  # 2 questions
            assert 'Question ID' in analysis_df.columns
            assert 'Analysis' in analysis_df.columns
            assert 'Score' in analysis_df.columns
            
            # The new logic shows more detailed status messages
            mock_success.assert_called_with("✓ Found 2 chunks across 2 questions (2 questions with analysis).")

def test_consolidated_tab_no_chunks(report_analyzer, test_env):
    """Test consolidated tab when no chunks are available"""
    file_path = test_env['test_pdf']
    
    with patch.object(report_analyzer.analyzer, 'check_step_completion') as mock_step_status, \
         patch.object(report_analyzer.analyzer.cache_manager, 'get_document_chunks') as mock_get_chunks, \
         patch.object(report_analyzer.analyzer.cache_manager, 'check_cache_status') as mock_cache_status:
        
        # Mock cache configurations
        mock_cache_status.return_value = [
            (str(file_path), 1000, 200, 5, 'gpt-3.5-turbo', 'tcfd')
        ]
        
        # Mock no chunks available
        mock_step_status.return_value = {
            'chunks': False,
            'embeddings': False,
            'scoring': False,
            'analysis': False
        }
        mock_get_chunks.return_value = []
        
        # Test "All Document Chunks" view with no chunks
        with patch('streamlit.radio', return_value="All Document Chunks"), \
             patch('streamlit.warning') as mock_warning, \
             patch('streamlit.selectbox', side_effect=[str(file_path), {'label': 'Chunk: 1000, Overlap: 200, Top-K: 5, Model: gpt-3.5-turbo', 'config': {'chunk_size': 1000, 'chunk_overlap': 200, 'top_k': 5, 'model': 'gpt-3.5-turbo'}}]):
            
            from app.streamlit_app import display_consolidated_results
            display_consolidated_results(report_analyzer, 'tcfd')
            
            mock_warning.assert_called_with("No processing steps completed for this configuration")

def test_consolidated_tab_chunks_by_question_no_embeddings(report_analyzer, test_env):
    """Test consolidated tab Chunks by Question view when no embeddings/scoring available"""
    file_path = test_env['test_pdf']
    
    with patch.object(report_analyzer.analyzer, 'check_step_completion') as mock_step_status, \
         patch.object(report_analyzer.analyzer.cache_manager, 'check_cache_status') as mock_cache_status, \
         patch.object(report_analyzer.analyzer, 'questions', {}):
        
        # Mock cache configurations
        mock_cache_status.return_value = [
            (str(file_path), 1000, 200, 5, 'gpt-3.5-turbo', 'tcfd')
        ]
        
        # Mock chunks exist but no embeddings/scoring
        mock_step_status.return_value = {
            'chunks': True,
            'embeddings': False,
            'scoring': False,
            'analysis': False
        }
        
        # Test "Chunks by Question" view with no embeddings
        with patch('streamlit.radio', return_value="Chunks by Question"), \
             patch('streamlit.info') as mock_info, \
             patch('streamlit.selectbox', side_effect=[str(file_path), {'label': 'Chunk: 1000, Overlap: 200, Top-K: 5, Model: gpt-3.5-turbo', 'config': {'chunk_size': 1000, 'chunk_overlap': 200, 'top_k': 5, 'model': 'gpt-3.5-turbo'}}]):
            
            from app.streamlit_app import display_consolidated_results
            display_consolidated_results(report_analyzer, 'tcfd')
            
            # The function shows both the chunk-by-question message and the step status
            mock_info.assert_any_call("No chunks with embeddings/scoring found. Run steps 2-4 to see question-specific chunks.")
            mock_info.assert_any_call("Chunks created but no embeddings yet. Run Steps 2, 3, and 4 to continue.") 

def test_consolidated_tab_mixed_analysis_and_scoring(report_analyzer, test_env):
    """Test consolidated tab when some questions have analysis and others only have scoring"""
    file_path = test_env['test_pdf']
    
    # Mock questions
    questions = {
        'tcfd_1': {'number': 1, 'text': 'Test question 1'},
        'tcfd_2': {'number': 2, 'text': 'Test question 2'},
        'tcfd_3': {'number': 3, 'text': 'Test question 3'},
        'tcfd_4': {'number': 4, 'text': 'Test question 4'}
    }
    
    with patch.object(report_analyzer.analyzer, 'check_step_completion') as mock_step_status, \
         patch.object(report_analyzer.analyzer.cache_manager, 'get_analysis') as mock_get_analysis, \
         patch.object(report_analyzer.analyzer.cache_manager, 'get_chunk_scoring_only') as mock_get_scoring, \
         patch.object(report_analyzer.analyzer.cache_manager, 'check_cache_status') as mock_cache_status, \
         patch.object(report_analyzer.analyzer, 'questions', questions):
        
        # Mock cache configurations
        mock_cache_status.return_value = [
            (str(file_path), 1000, 200, 5, 'gpt-3.5-turbo', 'tcfd')
        ]
        
        # Mock step completion status - both scoring and analysis completed
        mock_step_status.return_value = {
            'chunks': True,
            'embeddings': True,
            'scoring': True,
            'analysis': True
        }
        
        # Mock analysis results - only question 1 has analysis
        mock_analysis_results = {
            'tcfd_1': {
                'result': {
                    'ANSWER': 'Answer 1',
                    'SCORE': 8.5,
                    'EVIDENCE': [{'text': 'Evidence 1'}],
                    'GAPS': ['Gap 1'],
                    'SOURCES': [1, 2]
                },
                'chunks': [
                    {'text': 'Analysis chunk 1', 'similarity_score': 0.9, 'llm_score': 0.8, 'is_evidence': True, 'chunk_order': 1}
                ]
            }
        }
        mock_get_analysis.return_value = mock_analysis_results
        
        # Mock scoring results for questions 2, 3, 4
        mock_scored_chunks = [
            {'text': 'Scoring chunk 1', 'similarity_score': 0.7, 'llm_score': 0.6, 'is_evidence': False, 'chunk_order': 1},
            {'text': 'Scoring chunk 2', 'similarity_score': 0.6, 'llm_score': 0.5, 'is_evidence': False, 'chunk_order': 2}
        ]
        mock_get_scoring.return_value = mock_scored_chunks
        
        # Test "Chunks by Question" view
        with patch('streamlit.radio', return_value="Chunks by Question"), \
             patch('streamlit.dataframe') as mock_dataframe, \
             patch('streamlit.success') as mock_success, \
             patch('streamlit.selectbox', side_effect=[str(file_path), {'label': 'Chunk: 1000, Overlap: 200, Top-K: 5, Model: gpt-3.5-turbo', 'config': {'chunk_size': 1000, 'chunk_overlap': 200, 'top_k': 5, 'model': 'gpt-3.5-turbo'}}]):
            
            from app.streamlit_app import display_consolidated_results
            display_consolidated_results(report_analyzer, 'tcfd')
            
            # Should show chunks from both analysis and scoring
            assert mock_dataframe.call_count == 2  # Chunks table + Analysis table
            
            # Check chunks dataframe (first call)
            chunks_call = mock_dataframe.call_args_list[0]
            chunks_df = chunks_call[1]['data']
            
            # Should have 1 chunk from analysis (tcfd_1) + 6 chunks from scoring (tcfd_2, tcfd_3, tcfd_4 × 2 chunks each)
            assert len(chunks_df) == 7
            assert 'Question ID' in chunks_df.columns
            assert 'Vector Similarity' in chunks_df.columns
            assert 'LLM Score' in chunks_df.columns
            assert 'Is Evidence' in chunks_df.columns
            
            # Check that we have chunks from all 4 questions
            question_ids = set(chunks_df['Question ID'])
            assert question_ids == {'tcfd_1', 'tcfd_2', 'tcfd_3', 'tcfd_4'}
            
            # Check analysis dataframe (second call)
            analysis_call = mock_dataframe.call_args_list[1]
            analysis_df = analysis_call[1]['data']
            
            assert len(analysis_df) == 1  # Only tcfd_1 has analysis
            assert 'Question ID' in analysis_df.columns
            assert 'Analysis' in analysis_df.columns
            assert 'Score' in analysis_df.columns
            
            # Check status message shows mixed results
            mock_success.assert_called_with("✓ Found 7 chunks across 4 questions (1 questions with analysis, 3 questions with scoring only).")
            
            # Verify that get_chunk_scoring_only was called for questions without analysis
            assert mock_get_scoring.call_count == 3  # Should be called for tcfd_2, tcfd_3, tcfd_4 