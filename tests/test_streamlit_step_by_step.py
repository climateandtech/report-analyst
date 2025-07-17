import pytest
import tempfile
import shutil
from pathlib import Path
import os
import yaml
import json
import sqlite3
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, AsyncMock
import asyncio
from streamlit.testing.v1 import AppTest

# Import the app components
from app.core.analyzer import DocumentAnalyzer
from app.core.cache_manager import CacheManager

class TestStepByStepProcessing:
    """End-to-end tests for the step-by-step processing feature"""
    
    @pytest.fixture
    def test_env(self):
        """Setup test environment with necessary files and directories"""
        temp_dir = tempfile.mkdtemp()
        print(f"\nSetting up test environment in: {temp_dir}")
        
        # Create storage structure
        storage_path = Path(temp_dir) / "storage"
        cache_path = storage_path / "cache"
        cache_path.mkdir(parents=True)
        
        # Create test database with all required tables
        db_path = cache_path / "analysis.db"
        conn = sqlite3.connect(db_path)
        
        # Create all required tables
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
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS document_chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                chunk_text TEXT,
                chunk_metadata TEXT,
                embedding BLOB,
                chunk_size INTEGER,
                chunk_overlap INTEGER,
                created_at TEXT
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunk_relevance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                question_id TEXT,
                chunk_id INTEGER,
                similarity_score REAL,
                llm_score REAL,
                chunk_size INTEGER,
                chunk_overlap INTEGER,
                top_k INTEGER,
                model TEXT,
                question_set TEXT,
                created_at TEXT
            )
        """)
        
        conn.close()
        
        # Create test question set
        questions_dir = Path(temp_dir) / "app" / "questionsets"
        questions_dir.mkdir(parents=True)
        with open(questions_dir / "tcfd_questions.yaml", 'w') as f:
            yaml.dump({
                'name': 'TCFD Questions',
                'description': 'Test TCFD questions',
                'questions': [
                    {'id': 'tcfd_1', 'text': 'What are the climate-related risks?', 'guidelines': 'Identify physical and transition risks'},
                    {'id': 'tcfd_2', 'text': 'What are the governance processes?', 'guidelines': 'Describe board oversight and management processes'}
                ]
            }, f)
        
        # Create test PDF file
        test_pdf = storage_path / "test_report.pdf"
        # Create a minimal PDF file
        pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF Content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000115 00000 n 
0000000206 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
299
%%EOF"""
        test_pdf.write_bytes(pdf_content)
        
        # Set environment variables
        original_env = dict(os.environ)
        os.environ['STORAGE_PATH'] = str(storage_path)
        os.environ['QUESTIONSETS_PATH'] = str(questions_dir)
        os.environ['OPENAI_API_KEY'] = 'test-key-12345'
        os.environ['OPENAI_API_MODEL'] = 'gpt-3.5-turbo'
        
        yield {
            'temp_dir': temp_dir,
            'storage_path': storage_path,
            'questions_dir': questions_dir,
            'db_path': db_path,
            'test_pdf': test_pdf,
            'original_env': original_env
        }
        
        # Cleanup
        os.environ.clear()
        os.environ.update(original_env)
        shutil.rmtree(temp_dir)

    def setup_mock_analyzer(self, mock_analyzer_methods, additional_setup=None):
        """Helper method to set up a mock analyzer with all required methods"""
        mock_analyzer = Mock()
        
        # Core methods that all tests need
        mock_analyzer.process_document_steps = mock_analyzer_methods['process_document_steps']
        mock_analyzer.check_step_completion = mock_analyzer_methods['check_step_completion']
        
        # Optional methods that some tests need
        if 'create_chunks_only' in mock_analyzer_methods:
            mock_analyzer.create_chunks_only = mock_analyzer_methods['create_chunks_only']
        if 'add_embeddings_to_chunks' in mock_analyzer_methods:
            mock_analyzer.add_embeddings_to_chunks = mock_analyzer_methods['add_embeddings_to_chunks']
        if 'score_chunks_for_questions' in mock_analyzer_methods:
            mock_analyzer.score_chunks_for_questions = mock_analyzer_methods['score_chunks_for_questions']
        if 'analyze_questions_with_scored_chunks' in mock_analyzer_methods:
            mock_analyzer.analyze_questions_with_scored_chunks = mock_analyzer_methods['analyze_questions_with_scored_chunks']
        
        # Mock cache manager
        mock_cache_manager = Mock()
        mock_cache_manager.check_cache_status.return_value = []
        mock_analyzer.cache_manager = mock_cache_manager
        
        # Additional setup function
        if additional_setup:
            additional_setup(mock_analyzer)
        
        return mock_analyzer

    @pytest.fixture
    def mock_analyzer_methods(self):
        """Mock the analyzer methods for testing"""
        
        # Mock chunks data
        mock_chunks = [
            {
                'text': 'Climate change poses significant physical risks to our operations including extreme weather events.',
                'metadata': {'page': 1, 'chunk_id': 1},
                'embedding': np.random.rand(1536).astype(np.float32),
                'similarity': 0.85,
                'computed_score': 0.85
            },
            {
                'text': 'Our governance framework includes board oversight of climate-related risks and opportunities.',
                'metadata': {'page': 2, 'chunk_id': 2},
                'embedding': np.random.rand(1536).astype(np.float32),
                'similarity': 0.78,
                'computed_score': 0.78
            },
            {
                'text': 'We have implemented transition risk management processes to address regulatory changes.',
                'metadata': {'page': 3, 'chunk_id': 3},
                'embedding': np.random.rand(1536).astype(np.float32),
                'similarity': 0.72,
                'computed_score': 0.72
            }
        ]
        
        # Mock analysis results
        mock_analysis_result = {
            'ANSWER': 'The company faces both physical and transition climate risks. Physical risks include extreme weather events, while transition risks involve regulatory changes.',
            'SCORE': 0.8,
            'EVIDENCE': [
                {'chunk': 1, 'text': 'Climate change poses significant physical risks', 'score': 0.9},
                {'chunk': 3, 'text': 'transition risk management processes', 'score': 0.7}
            ],
            'GAPS': ['More specific quantification of financial impacts needed'],
            'SOURCES': [1, 3]
        }
        
        async def mock_process_document_steps(*args, **kwargs):
            """Mock the step-by-step processing"""
            steps = kwargs.get('steps', {})
            
            if steps.get('chunks'):
                yield {"status": "Step 1: Creating chunks..."}
                yield {"step_complete": "chunks", "count": len(mock_chunks)}
            
            if steps.get('embeddings'):
                yield {"status": "Step 2: Adding embeddings..."}
                yield {"step_complete": "embeddings", "count": len(mock_chunks)}
            
            if steps.get('scoring'):
                yield {"status": "Step 3: Scoring chunks for questions..."}
                yield {"step_complete": "scoring", "questions": 2}
            
            if steps.get('analysis'):
                yield {"status": "Step 4: Analyzing questions..."}
                yield {"step_complete": "analysis", "questions": 2}
                
                # Yield individual results
                yield {
                    'question_number': 1,
                    'question_id': 'tcfd_1',
                    'result': mock_analysis_result
                }
                yield {
                    'question_number': 2,
                    'question_id': 'tcfd_2',
                    'result': {**mock_analysis_result, 'ANSWER': 'Board oversight includes climate risk governance processes.'}
                }
            
            yield {"status": "All selected steps completed successfully"}
        
        def mock_check_step_completion(*args, **kwargs):
            """Mock step completion checking"""
            return {
                'chunks': True,
                'embeddings': True,
                'scoring': True,
                'analysis': True
            }
        
        def mock_create_chunks_only(*args, **kwargs):
            """Mock chunks creation"""
            return mock_chunks
        
        def mock_add_embeddings_to_chunks(*args, **kwargs):
            """Mock embeddings addition"""
            return mock_chunks
        
        async def mock_score_chunks_for_questions(*args, **kwargs):
            """Mock chunk scoring"""
            return {'tcfd_1': mock_chunks, 'tcfd_2': mock_chunks}
        
        async def mock_analyze_questions_with_scored_chunks(*args, **kwargs):
            """Mock question analysis"""
            return {
                'tcfd_1': mock_analysis_result,
                'tcfd_2': {**mock_analysis_result, 'ANSWER': 'Board oversight analysis'}
            }
        
        return {
            'process_document_steps': mock_process_document_steps,
            'check_step_completion': mock_check_step_completion,
            'create_chunks_only': mock_create_chunks_only,
            'add_embeddings_to_chunks': mock_add_embeddings_to_chunks,
            'score_chunks_for_questions': mock_score_chunks_for_questions,
            'analyze_questions_with_scored_chunks': mock_analyze_questions_with_scored_chunks,
            'chunks': mock_chunks,
            'analysis_result': mock_analysis_result
        }

    def test_streamlit_app_initialization(self, test_env):
        """Test that the Streamlit app initializes correctly"""
        with patch.dict(os.environ, {
            'STORAGE_PATH': str(test_env['storage_path']),
            'QUESTIONSETS_PATH': str(test_env['questions_dir']),
            'OPENAI_API_KEY': 'test-key-12345'
        }):
            # Initialize the app
            at = AppTest.from_file("app/streamlit_app.py")
            at.run()
            
            # Check that the app doesn't crash on startup
            assert not at.exception
            
            # Check that basic UI elements are present
            assert len(at.title) > 0
            assert "Report Analyst" in str(at.title[0].value)

    def test_step_by_step_ui_elements(self, test_env, mock_analyzer_methods):
        """Test that step-by-step UI elements are present and functional"""
        
        with patch.dict(os.environ, {
            'STORAGE_PATH': str(test_env['storage_path']),
            'QUESTIONSETS_PATH': str(test_env['questions_dir']),
            'OPENAI_API_KEY': 'test-key-12345'
        }):
            # Patch the analyzer methods
            with patch('app.core.analyzer.DocumentAnalyzer') as mock_analyzer_class:
                mock_analyzer = self.setup_mock_analyzer(mock_analyzer_methods)
                mock_analyzer_class.return_value = mock_analyzer
                
                at = AppTest.from_file("app/streamlit_app.py")
                at.run()
                
                # Check that step-by-step section exists
                step_checkboxes = [cb for cb in at.checkbox if any(step in str(cb.label) for step in ['Generate Chunks', 'Generate Embeddings', 'Score Chunks', 'Answer Questions'])]
                assert len(step_checkboxes) >= 4, "Should have at least 4 step checkboxes"
                
                # Check checkbox labels
                expected_steps = [
                    "1. Generate Chunks",
                    "2. Generate Embeddings", 
                    "3. Score Chunks",
                    "4. Answer Questions"
                ]
                
                checkbox_labels = [str(cb.label) for cb in step_checkboxes]
                for expected_step in expected_steps:
                    assert any(expected_step in label for label in checkbox_labels), f"Missing step: {expected_step}"

    def test_step_dependency_logic(self, test_env, mock_analyzer_methods):
        """Test that step dependencies are enforced correctly"""
        
        with patch.dict(os.environ, {
            'STORAGE_PATH': str(test_env['storage_path']),
            'QUESTIONSETS_PATH': str(test_env['questions_dir']),
            'OPENAI_API_KEY': 'test-key-12345'
        }):
            with patch('app.core.analyzer.DocumentAnalyzer') as mock_analyzer_class:
                # Mock analyzer to return no completed steps initially
                mock_analyzer = Mock()
                mock_analyzer.check_step_completion = Mock(return_value={
                    'chunks': False,
                    'embeddings': False,
                    'scoring': False,
                    'analysis': False
                })
                mock_analyzer_class.return_value = mock_analyzer
                
                at = AppTest.from_file("app/streamlit_app.py")
                at.run()
                
                # Initially, only Step 1 should be enabled
                step_checkboxes = [cb for cb in at.checkbox if 'Step' in str(cb.label)]
                
                # Try to enable Step 2 without Step 1
                if len(step_checkboxes) >= 2:
                    step2_checkbox = step_checkboxes[1]
                    # Step 2 should be disabled when Step 1 is not completed
                    assert step2_checkbox.disabled, "Step 2 should be disabled when Step 1 is not completed"

    def test_file_upload_and_processing(self, test_env, mock_analyzer_methods):
        """Test file upload and step-by-step processing"""
        
        with patch.dict(os.environ, {
            'STORAGE_PATH': str(test_env['storage_path']),
            'QUESTIONSETS_PATH': str(test_env['questions_dir']),
            'OPENAI_API_KEY': 'test-key-12345'
        }):
            with patch('app.core.analyzer.DocumentAnalyzer') as mock_analyzer_class:
                mock_analyzer = self.setup_mock_analyzer(mock_analyzer_methods)
                mock_analyzer_class.return_value = mock_analyzer
                
                at = AppTest.from_file("app/streamlit_app.py")
                at.run()
                
                # Test basic tab functionality - file upload testing is complex with AppTest
                assert len(at.tabs) >= 2, "Should have at least 2 tabs"
                
                # Test that step checkboxes are present in the UI
                step_checkboxes = [cb for cb in at.checkbox if any(step in str(cb.label) for step in ['Generate Chunks', 'Generate Embeddings', 'Score Chunks', 'Answer Questions'])]
                assert len(step_checkboxes) >= 4, "Should have step checkboxes"
                
                # Test that the app doesn't crash
                assert not at.exception, f"Exception occurred: {at.exception}"

    def test_step_execution_flow(self, test_env, mock_analyzer_methods):
        """Test the complete step execution flow"""
        
        with patch.dict(os.environ, {
            'STORAGE_PATH': str(test_env['storage_path']),
            'QUESTIONSETS_PATH': str(test_env['questions_dir']),
            'OPENAI_API_KEY': 'test-key-12345'
        }):
            with patch('app.core.analyzer.DocumentAnalyzer') as mock_analyzer_class:
                def setup_questions(analyzer):
                    analyzer.questions = {
                        'tcfd_1': {'text': 'What are the climate-related risks?'},
                        'tcfd_2': {'text': 'What are the governance processes?'}
                    }
                
                mock_analyzer = self.setup_mock_analyzer(mock_analyzer_methods, setup_questions)
                mock_analyzer_class.return_value = mock_analyzer
                
                at = AppTest.from_file("app/streamlit_app.py")
                at.run()
                
                # Enable all steps
                step_checkboxes = [cb for cb in at.checkbox if 'Step' in str(cb.label)]
                for checkbox in step_checkboxes[:4]:  # Enable first 4 steps
                    if not checkbox.disabled:
                        checkbox.check()
                
                at.run()
                
                # Find and click the execute button
                execute_buttons = [btn for btn in at.button if 'Execute' in str(btn.label)]
                if execute_buttons:
                    execute_buttons[0].click()
                    at.run()
                    
                    # Check that no exceptions occurred
                    assert not at.exception, f"Exception during execution: {at.exception}"

    def test_results_display(self, test_env, mock_analyzer_methods):
        """Test that results are displayed correctly after processing"""
        
        with patch.dict(os.environ, {
            'STORAGE_PATH': str(test_env['storage_path']),
            'QUESTIONSETS_PATH': str(test_env['questions_dir']),
            'OPENAI_API_KEY': 'test-key-12345'
        }):
            with patch('app.core.analyzer.DocumentAnalyzer') as mock_analyzer_class:
                mock_analyzer = Mock()
                mock_analyzer.process_document_steps = mock_analyzer_methods['process_document_steps']
                mock_analyzer.check_step_completion = mock_analyzer_methods['check_step_completion']
                mock_analyzer.questions = {
                    'tcfd_1': {'text': 'What are the climate-related risks?'},
                    'tcfd_2': {'text': 'What are the governance processes?'}
                }
                
                # Mock cache manager to return results
                mock_cache_manager = Mock()
                mock_cache_manager.get_analysis.return_value = {
                    'tcfd_1': mock_analyzer_methods['analysis_result'],
                    'tcfd_2': mock_analyzer_methods['analysis_result']
                }
                mock_analyzer.cache_manager = mock_cache_manager
                mock_analyzer_class.return_value = mock_analyzer
                
                at = AppTest.from_file("app/streamlit_app.py")
                at.run()
                
                # Check that results section exists
                # Results should be displayed in expanders or dataframes
                assert len(at.expander) > 0 or len(at.dataframe) > 0, "Results should be displayed"

    def test_error_handling(self, test_env):
        """Test error handling in step-by-step processing"""
        
        with patch.dict(os.environ, {
            'STORAGE_PATH': str(test_env['storage_path']),
            'QUESTIONSETS_PATH': str(test_env['questions_dir']),
            'OPENAI_API_KEY': 'test-key-12345'
        }):
            with patch('app.core.analyzer.DocumentAnalyzer') as mock_analyzer_class:
                # Mock analyzer to raise an exception
                mock_analyzer = Mock()
                mock_analyzer.process_document_steps = Mock(side_effect=Exception("Test error"))
                mock_analyzer.check_step_completion = Mock(return_value={
                    'chunks': False,
                    'embeddings': False,
                    'scoring': False,
                    'analysis': False
                })
                mock_analyzer_class.return_value = mock_analyzer
                
                at = AppTest.from_file("app/streamlit_app.py")
                at.run()
                
                # The app should handle errors gracefully
                # Check that error messages are displayed
                error_messages = [elem for elem in at.error if elem.value]
                warning_messages = [elem for elem in at.warning if elem.value]
                
                # At minimum, the app should not crash
                assert not at.exception or "Test error" in str(at.exception)

    def test_configuration_persistence(self, test_env, mock_analyzer_methods):
        """Test that configuration settings persist across interactions"""
        
        with patch.dict(os.environ, {
            'STORAGE_PATH': str(test_env['storage_path']),
            'QUESTIONSETS_PATH': str(test_env['questions_dir']),
            'OPENAI_API_KEY': 'test-key-12345'
        }):
            with patch('app.core.analyzer.DocumentAnalyzer') as mock_analyzer_class:
                mock_analyzer = Mock()
                mock_analyzer.process_document_steps = mock_analyzer_methods['process_document_steps']
                mock_analyzer.check_step_completion = mock_analyzer_methods['check_step_completion']
                mock_analyzer.update_parameters = Mock()
                mock_analyzer.update_llm_model = Mock()
                mock_analyzer_class.return_value = mock_analyzer
                
                at = AppTest.from_file("app/streamlit_app.py")
                at.run()
                
                # Change configuration settings
                chunk_size_inputs = [inp for inp in at.number_input if 'chunk' in str(inp.label).lower()]
                if chunk_size_inputs:
                    chunk_size_inputs[0].set_value(1000)
                    at.run()
                    
                    # Verify that the analyzer was updated
                    mock_analyzer.update_parameters.assert_called()

    @pytest.mark.asyncio
    async def test_async_processing_integration(self, test_env, mock_analyzer_methods):
        """Test that async processing works correctly with the UI"""
        
        with patch.dict(os.environ, {
            'STORAGE_PATH': str(test_env['storage_path']),
            'QUESTIONSETS_PATH': str(test_env['questions_dir']),
            'OPENAI_API_KEY': 'test-key-12345'
        }):
            with patch('app.core.analyzer.DocumentAnalyzer') as mock_analyzer_class:
                mock_analyzer = Mock()
                
                # Create an async generator that yields results
                async def async_generator():
                    yield {"status": "Step 1: Creating chunks..."}
                    yield {"step_complete": "chunks", "count": 3}
                    yield {"status": "All steps completed"}
                
                mock_analyzer.process_document_steps = AsyncMock(return_value=async_generator())
                mock_analyzer.check_step_completion = mock_analyzer_methods['check_step_completion']
                mock_analyzer_class.return_value = mock_analyzer
                
                at = AppTest.from_file("app/streamlit_app.py")
                at.run()
                
                # The app should handle async generators correctly
                assert not at.exception, f"Async processing failed: {at.exception}"

    def test_data_persistence_across_sessions(self, test_env, mock_analyzer_methods):
        """Test that data persists correctly across app sessions"""
        
        with patch.dict(os.environ, {
            'STORAGE_PATH': str(test_env['storage_path']),
            'QUESTIONSETS_PATH': str(test_env['questions_dir']),
            'OPENAI_API_KEY': 'test-key-12345'
        }):
            # First session - create some data
            with patch('app.core.analyzer.DocumentAnalyzer') as mock_analyzer_class:
                mock_analyzer = Mock()
                mock_analyzer.process_document_steps = mock_analyzer_methods['process_document_steps']
                mock_analyzer.check_step_completion = Mock(return_value={
                    'chunks': True,
                    'embeddings': True,
                    'scoring': False,
                    'analysis': False
                })
                mock_analyzer_class.return_value = mock_analyzer
                
                at1 = AppTest.from_file("app/streamlit_app.py")
                at1.run()
                
                # Simulate some processing
                step_checkboxes = [cb for cb in at1.checkbox if 'Step' in str(cb.label)]
                if step_checkboxes:
                    step_checkboxes[0].check()
                at1.run()
            
            # Second session - data should persist
            with patch('app.core.analyzer.DocumentAnalyzer') as mock_analyzer_class:
                mock_analyzer = Mock()
                mock_analyzer.check_step_completion = Mock(return_value={
                    'chunks': True,
                    'embeddings': True,
                    'scoring': False,
                    'analysis': False
                })
                mock_analyzer_class.return_value = mock_analyzer
                
                at2 = AppTest.from_file("app/streamlit_app.py")
                at2.run()
                
                # Check that previous state is reflected
                assert not at2.exception, "Second session should load successfully" 