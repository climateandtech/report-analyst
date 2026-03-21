import asyncio
import base64
import json
import logging
import os
import sys
import time
import traceback
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)
from streamlit_card import card

# Add parent directory to path for backend integration
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Try to import backend integration features
try:
    from report_analyst_search_backend.config import (
        BackendConfig,
        configure_backend_integration,
        display_config_status,
    )
    from report_analyst_search_backend.flow_orchestrator import (
        AnalysisResult,
        ProcessingResult,
        create_flow_orchestrator,
        needs_local_analysis,
    )

    BACKEND_INTEGRATION_AVAILABLE = True
except ImportError as e:
    BACKEND_INTEGRATION_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("app.log")],
)
logger = logging.getLogger(__name__)

# Reduce noise from other libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("chromadb").setLevel(logging.WARNING)


def log_analysis_step(message: str, level: str = "info"):
    """Helper function to log analysis steps with consistent formatting"""
    log_func = getattr(logger, level)
    log_func(f"[ANALYSIS] {message}")


# Add the report-analyst directory to the Python path
current_dir = Path(__file__).parent.parent
if str(current_dir) not in sys.path:
    sys.path.append(str(current_dir))
logger.info(f"Added {current_dir} to Python path")

# Keep relative imports
from report_analyst.core.analyzer import DocumentAnalyzer
from report_analyst.core.api_key_manager import APIKeyManager
from report_analyst.core.dataframe_manager import (
    create_analysis_dataframes,
    create_combined_dataframe,
)
from report_analyst.core.prompt_manager import PromptManager
from report_analyst.core.question_loader import get_question_loader

# Load environment variables
load_dotenv()
logger.info("Loaded environment variables")

# Initialize question loader
question_loader = get_question_loader()

# Define model lists based on available API keys
OPENAI_MODELS = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]

GEMINI_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro"]

# Only include models with available API keys
LLM_MODELS = OPENAI_MODELS.copy()

# Check for Google API key and add Gemini models if available
if os.getenv("GOOGLE_API_KEY"):
    logger.info("Google API key found - adding Gemini models to available options")
    LLM_MODELS.extend(GEMINI_MODELS)
else:
    logger.warning("No Google API key found - Gemini models will not be available")


# Load question sets dynamically using the centralized loader
def get_question_sets() -> Dict[str, Dict[str, str]]:
    """Get all available question sets dynamically with Everest at the end"""
    try:
        all_sets = question_loader.get_question_set_info()

        # Reorder to put Everest last
        ordered_sets = {}
        everest_data = None

        # Add all non-Everest sets first
        for key, value in all_sets.items():
            if key == "everest":
                everest_data = value
            else:
                ordered_sets[key] = value

        # Add Everest at the end if it exists
        if everest_data:
            ordered_sets["everest"] = everest_data

        return ordered_sets
    except Exception as e:
        logger.error(f"Error loading question sets: {e}")
        return {}


# Get question sets at startup
question_sets = get_question_sets()


class ReportAnalyzer:
    """Class to handle report analysis"""

    def __init__(self):
        """Initialize the analyzer"""
        self.temp_dir = Path("temp")
        self.temp_dir.mkdir(exist_ok=True)

        # Initialize the real document analyzer
        self.analyzer = DocumentAnalyzer()
        self.prompt_manager = PromptManager()
        self.cache_manager = self.analyzer.cache_manager  # Access the cache manager from the analyzer

    def load_question_set(self, question_set: str) -> Dict:
        """Load questions from the specified question set using centralized loader"""
        try:
            question_set_obj = question_loader.get_question_set(question_set)
            if not question_set_obj:
                logger.error(f"Question set '{question_set}' not found")
                return {"questions": {}, "name": "", "description": ""}

            # Convert to the format expected by the UI
            questions = {}
            for i, (q_id, q_data) in enumerate(question_set_obj.questions.items(), 1):
                questions[q_id] = {
                    "text": q_data["text"],
                    "guidelines": q_data.get("guidelines", ""),
                    "id": q_id,
                    "number": i,  # Add numeric ID for easier mapping
                }

            return {
                "questions": questions,
                "name": question_set_obj.name,
                "description": question_set_obj.description,
            }

        except Exception as e:
            logger.error(f"Failed to load questions for {question_set}: {str(e)}")
            return {"questions": {}, "name": "", "description": ""}

    async def analyze_document(
        self,
        file_path: str,
        questions: Dict,
        selected_questions: List[str],
        use_llm_scoring: bool = False,
        single_call: bool = True,
        force_recompute: bool = False,
        pre_retrieved_chunks: Optional[List[Dict[str, Any]]] = None,
    ) -> AsyncGenerator[Dict, None]:
        """Analyze a document using the provided questions

        Args:
            file_path: Path to document file or URN for backend resources
            questions: Dictionary of questions
            selected_questions: List of selected question IDs
            use_llm_scoring: Whether to use LLM for chunk scoring
            single_call: Whether to use single LLM call per question
            force_recompute: Whether to force recomputation
            pre_retrieved_chunks: Optional pre-retrieved chunks (e.g., from backend)
        """
        try:
            log_analysis_step(f"Starting analysis of document: {file_path}")
            log_analysis_step(f"Selected questions: {selected_questions}")
            log_analysis_step(f"LLM scoring enabled: {use_llm_scoring}")

            # Update analyzer with the current questions
            self.analyzer.questions = questions

            # Convert selected question IDs to numbers for the analyzer
            selected_numbers = [questions[q_id]["number"] for q_id in selected_questions]

            # Get the question set prefix from the first selected question
            question_set = selected_questions[0].split("_")[0] if selected_questions else "tcfd"
            self.analyzer.question_set = question_set

            # Pass use_llm_scoring to process_document
            async for result in self.analyzer.process_document(
                file_path,
                selected_numbers,
                use_llm_scoring,
                single_call,
                force_recompute,
                pre_retrieved_chunks=pre_retrieved_chunks,
            ):
                # Pass through status and error messages
                if "status" in result or "error" in result:
                    yield result
                    continue

                # Handle results with question_number
                if "question_number" in result:
                    question_number = result["question_number"]
                    question_id = f"{question_set}_{question_number}"

                    # Create a new result with the question_id
                    new_result = {
                        "question_id": question_id,
                        "question_number": question_number,
                    }

                    # Copy over the result data
                    if "result" in result:
                        # If result is nested, extract it
                        new_result.update(result["result"])
                    else:
                        # Otherwise copy all other fields
                        for key, value in result.items():
                            if key not in ["question_number"]:
                                new_result[key] = value

                    yield new_result
                else:
                    # If no question_number, just pass through the result
                    yield result

        except Exception as e:
            log_analysis_step(f"Critical error during analysis: {str(e)}", "error")
            yield {"error": f"Error analyzing document: {str(e)}"}

    def process_document(
        self,
        file_path: str,
        selected_questions: List[int] = None,
        use_llm_scoring: bool = False,
        single_call: bool = True,
        force_recompute: bool = False,
    ):
        """Delegate to the analyzer's process_document method"""
        return self.analyzer.process_document(file_path, selected_questions, use_llm_scoring, single_call, force_recompute)


def save_uploaded_file(uploaded_file) -> Optional[str]:
    """Save uploaded file to temp directory or PostgreSQL"""
    try:
        if uploaded_file is None:
            logger.warning("No file was uploaded")
            return None

        # If it's already a path, just return it
        if isinstance(uploaded_file, (str, Path)):
            return str(uploaded_file)

        # Check if PostgreSQL file storage is enabled (check both keys for persistence)
        use_postgres_storage = st.session_state.get("postgres_file_storage_enabled", False) or st.session_state.get(
            "use_postgres_file_storage", False
        )

        # Check if file was already saved in this session with the SAME storage mode
        file_key = f"saved_file_{uploaded_file.name}"
        storage_mode_key = f"saved_file_mode_{uploaded_file.name}"
        cached_mode = st.session_state.get(storage_mode_key)

        # Only use cache if storage mode matches
        if file_key in st.session_state and cached_mode == ("postgres" if use_postgres_storage else "local"):
            return st.session_state[file_key]

        # Get file bytes
        file_bytes = uploaded_file.getbuffer()

        if use_postgres_storage:
            try:
                from report_analyst.core.file_storage import get_file_storage

                # Get database URL from session state or environment
                database_url = st.session_state.get("database_url")
                file_storage = get_file_storage(database_url)

                if file_storage:
                    # Check if file already exists in PostgreSQL
                    existing_file_id = file_storage.find_by_filename(uploaded_file.name)
                    if existing_file_id:
                        # Retrieve from PostgreSQL instead of re-uploading
                        temp_path = file_storage.save_to_temp(existing_file_id)
                        if temp_path:
                            st.session_state[file_key] = temp_path
                            st.session_state[f"{file_key}_id"] = existing_file_id
                            st.session_state[storage_mode_key] = "postgres"
                            logger.info(
                                f"Retrieved existing file {uploaded_file.name} from PostgreSQL (ID: {existing_file_id})"
                            )
                            st.session_state.file_processed = False
                            return temp_path

                    # Store new file in PostgreSQL
                    file_id = file_storage.store_file(file_bytes, uploaded_file.name, uploaded_file.type)

                    # Save to temp for processing (retrieve from DB)
                    temp_path = file_storage.save_to_temp(file_id)

                    if temp_path:
                        # Store both file_id and path in session state
                        st.session_state[file_key] = temp_path
                        st.session_state[f"{file_key}_id"] = file_id
                        st.session_state[storage_mode_key] = "postgres"
                        logger.info(f"Stored file {uploaded_file.name} in PostgreSQL (ID: {file_id})")
                        st.session_state.file_processed = False
                        return temp_path
                    else:
                        logger.warning("Failed to save file from PostgreSQL to temp, falling back to local")
                else:
                    logger.warning("PostgreSQL file storage not available, falling back to local")
            except Exception as e:
                logger.warning(f"PostgreSQL file storage failed: {str(e)}, falling back to local")

        # Fallback to local file storage
        file_path = Path("temp") / uploaded_file.name
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        logger.info(f"Successfully saved file: {file_path}")

        # Store the path in session state
        st.session_state[file_key] = str(file_path)
        # Reset file processing flag when a new file is saved
        st.session_state.file_processed = False
        return str(file_path)
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        st.error(f"Error saving file: {str(e)}")
        return None


def display_dataframes(analysis_df: pd.DataFrame, chunks_df: pd.DataFrame):
    """Display only the dataframes without download buttons"""
    # Main Analysis Table (only once)
    st.subheader("Analysis Results")
    st.dataframe(
        analysis_df,
        use_container_width=True,
        column_config={
            "Score": st.column_config.NumberColumn(
                "Score",
                help="Analysis score out of 10",
                min_value=0,
                max_value=10,
                format="%.1f",
            ),
            "Analysis": st.column_config.TextColumn("Analysis", width="large"),
            "Key Evidence": st.column_config.TextColumn("Key Evidence", width="medium"),
        },
    )

    # Document Chunks Table (only once)
    st.subheader("Document Chunks")
    st.dataframe(
        chunks_df,
        use_container_width=True,
        column_config={
            "Vector Similarity": st.column_config.NumberColumn("Vector Similarity", format="%.3f"),
            "LLM Score": st.column_config.NumberColumn("LLM Score", format="%.3f"),
            "Chunk Text": st.column_config.TextColumn("Chunk Text", width="large"),
        },
    )


def convert_df(df: pd.DataFrame) -> bytes:
    """Convert a DataFrame to CSV bytes"""
    return df.to_csv(index=False).encode("utf-8")


def display_download_buttons(analysis_df: pd.DataFrame, chunks_df: pd.DataFrame, file_key: str):
    """Display download buttons for analysis results"""
    # Generate unique timestamp for this render
    timestamp = int(time.time() * 1000)

    col1, col2 = st.columns(2)

    with col1:
        csv = convert_df(analysis_df)
        st.download_button(
            label="Download Analysis Results",
            data=csv,
            file_name=f"analysis_{file_key}.csv",
            mime="text/csv",
            key=f"download_analysis_{file_key}_{timestamp}",
        )

    with col2:
        csv = convert_df(chunks_df)
        st.download_button(
            label="Download Chunks Data",
            data=csv,
            file_name=f"chunks_{file_key}.csv",
            mime="text/csv",
            key=f"download_chunks_{file_key}_{timestamp}",
        )


def generate_file_key(file_path: str, st) -> str:
    """Generate a cache file key from file path and settings"""
    return (
        f"{Path(file_path).name}_"
        f"cs{st.session_state.new_chunk_size}_"
        f"ov{st.session_state.new_overlap}_"
        f"tk{st.session_state.new_top_k}_"
        f"m{st.session_state.new_llm_model}"
    )


async def analyze_document_and_display(
    report_analyzer,
    file_path: str,
    questions: Dict,
    selected_questions: List[str],
    use_llm_scoring: bool = False,
    single_call: bool = True,
    force_recompute: bool = False,
):
    """Analyze document and display results as they come in"""
    try:
        selected_questions_list = list(selected_questions) if selected_questions else []
        question_set = selected_questions_list[0].split("_")[0] if selected_questions_list else "tcfd"

        # Use the helper function to generate file key
        file_key = generate_file_key(file_path, st)

        # Initialize or clear results if question set changed
        if (
            "results" not in st.session_state
            or "current_question_set" not in st.session_state
            or st.session_state.current_question_set != question_set
        ):
            st.session_state.results = {"answers": {}}
            st.session_state.current_question_set = question_set
            st.session_state.analyzed_files = set()

        # Create status placeholder
        status_placeholder = st.empty()

        log_analysis_step(f"Starting analysis with question set: {question_set}")

        # Get current configuration
        config = {
            "chunk_size": st.session_state.chunk_size,
            "chunk_overlap": st.session_state.chunk_overlap,
            "top_k": st.session_state.top_k,
            "model": st.session_state.llm_model,
            "question_set": question_set,
        }

        # Load cached answers using the cache manager
        cached_answers = (
            {}
            if force_recompute
            else report_analyzer.cache_manager.get_analysis(
                file_path=file_path, config=config, question_ids=selected_questions_list
            )
        )

        if cached_answers:
            log_analysis_step(f"Found {len(cached_answers)} cached answers for {file_key}")
            # Show cache info
            st.info(f"📁 Loading results from stored: {file_key}")

            # Update results with cached answers
            for q_id, answer in cached_answers.items():
                st.session_state.results["answers"][q_id] = answer

            # Update display with cached results
            logger.info(f"Creating dataframes with cached results for file_key: {file_key}")
            logger.info(
                f"Current session state settings: chunk_size={st.session_state.get('new_chunk_size')}, overlap={st.session_state.get('new_overlap')}, top_k={st.session_state.get('new_top_k')}, llm_model={st.session_state.get('new_llm_model')}, use_llm_scoring={st.session_state.get('new_llm_scoring')}"
            )
            analysis_df, chunks_df = create_analysis_dataframes(st.session_state.results["answers"], file_key)
            st.session_state.analysis_df = analysis_df
            st.session_state.chunks_df = chunks_df

        # Determine which questions need processing
        questions_to_process = [q_id for q_id in selected_questions_list if force_recompute or q_id not in cached_answers]

        if questions_to_process:
            log_analysis_step(f"Processing {len(questions_to_process)} uncached questions...")

            # Update analyzer with question set
            report_analyzer.analyzer.question_set = question_set

            # Process only uncached questions
            # Check if we have pre-retrieved chunks (for backend resources)
            pre_retrieved_chunks = st.session_state.get("backend_chunks")

            async for result in report_analyzer.analyze_document(
                file_path,
                questions,
                questions_to_process,
                use_llm_scoring,
                single_call,
                force_recompute,
                pre_retrieved_chunks=pre_retrieved_chunks,
            ):
                # Add debug logging to see what results we're getting
                log_analysis_step(f"Received result: {str(result)[:200]}...")

                if "error" in result:
                    log_analysis_step(f"Error received from analyzer: {result['error']}", "error")
                    st.error(f"Analysis error: {result['error']}")
                    continue

                if "status" in result:
                    status_placeholder.write(result["status"])
                    continue

                question_id = result.get("question_id")
                if question_id is None:
                    log_analysis_step(f"No question_id in result: {str(result)[:200]}...", "warning")
                    continue

                # Store results
                st.session_state.results["answers"][question_id] = result

                # Update display
                logger.info(f"Creating dataframes with updated results for file_key: {file_key}")
                logger.info(
                    f"Current session state settings: chunk_size={st.session_state.get('new_chunk_size')}, overlap={st.session_state.get('new_overlap')}, top_k={st.session_state.get('new_top_k')}, llm_model={st.session_state.get('new_llm_model')}, use_llm_scoring={st.session_state.get('new_llm_scoring')}"
                )
                analysis_df, chunks_df = create_analysis_dataframes(st.session_state.results["answers"], file_key)

                st.session_state.analysis_df = analysis_df
                st.session_state.chunks_df = chunks_df

                # Add a success message for each processed question
                st.success(f"✓ Processed question {question_id}")
        else:
            log_analysis_step("All selected questions have cached answers")
            # Show success message for cached results
            st.success(f"✓ All {len(selected_questions_list)} selected questions loaded from stored")

        # Mark this file as analyzed with current configuration
        if "analyzed_files" not in st.session_state:
            st.session_state.analyzed_files = set()
        st.session_state.analyzed_files.add(file_key)

        # Clear status and mark as complete
        status_placeholder.empty()
        st.session_state.analysis_complete = True

    except Exception as e:
        log_analysis_step(f"Critical error during analysis: {str(e)}", "error")
        log_analysis_step(traceback.format_exc(), "error")
        st.error(f"Error during analysis: {str(e)}")


def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe
    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            left.write("↳")

            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df


def display_final_results(analysis_df: pd.DataFrame, chunks_df: pd.DataFrame):
    """Display the final results including both tables"""
    # Analysis Results
    st.subheader("Analysis Results")
    st.dataframe(
        analysis_df,
        column_config={
            "Score": st.column_config.NumberColumn(
                "Score",
                help="Analysis score out of 10",
                min_value=0,
                max_value=10,
                format="%.1f",
            ),
            "Analysis": st.column_config.TextColumn("Analysis", width="large"),
            "Key Evidence": st.column_config.TextColumn("Key Evidence", width="medium"),
        },
        use_container_width=True,
        hide_index=True,
    )

    # Document Chunks
    st.subheader("Document Chunks")
    st.dataframe(
        filter_dataframe(chunks_df),  # Apply the filter function
        column_config={
            "Question ID": st.column_config.SelectboxColumn(
                "Question ID",
                help="The question this chunk belongs to",
                width="medium",
                options=chunks_df["Question ID"].unique().tolist(),
            ),
            "Vector Similarity": st.column_config.NumberColumn(
                "Vector Similarity",
                help="Similarity score between chunk and question",
                min_value=0,
                max_value=1,
                format="%.3f",
            ),
            "LLM Score": st.column_config.NumberColumn(
                "LLM Score",
                help="LLM-computed relevance score",
                min_value=0,
                max_value=1,
                format="%.3f",
            ),
            "Chunk Text": st.column_config.TextColumn("Chunk Text", help="Text content of the chunk", width="large"),
            "Evidence Reference": st.column_config.CheckboxColumn(
                "Used as Evidence",
                help="Whether this chunk was referenced in the analysis",
            ),
            "Position in Question": st.column_config.NumberColumn(
                "Position",
                help="Position of chunk within question results",
                min_value=0,
            ),
        },
        use_container_width=True,
        hide_index=False,
    )


def load_question_sets() -> Dict[str, str]:
    """Load all available question sets and their descriptions using centralized loader"""
    try:
        return question_loader.get_question_set_info()
    except Exception as e:
        logger.error(f"Error loading question sets: {e}")
        return {}


def get_uploaded_files_history(backend_config=None) -> List[Dict]:
    """Get list of files for Streamlit dropdown (UI adapter)"""
    from report_analyst.core.report_data_client import ReportDataClient

    client = ReportDataClient()

    # Collect backend configs (could be multiple backends in future)
    backend_configs = (
        [backend_config] if backend_config and hasattr(backend_config, "use_backend") and backend_config.use_backend else []
    )

    resources = client.list_reports(backend_configs=backend_configs)

    # Convert to dict format for Streamlit selectbox
    result = []
    for r in resources:
        # Extract actual file path from file:// URI for backward compatibility
        if r.is_local_resource and r.uri.startswith("file://"):
            # Extract path from file:// URI (remove file:// prefix)
            actual_path = r.uri.replace("file://", "")
        elif r.is_local_resource:
            # Already a direct path
            actual_path = r.uri
        else:
            # Backend resource - keep URI as path for compatibility
            actual_path = r.uri

        result.append(
            {
                "name": r.name,
                "uri": r.uri,  # Primary identifier (URN or file://)
                "path": actual_path,  # Actual file path for local files, URI for backend
                "date": r.date,
                "size": r.size,
            }
        )
    return result


def display_analysis_results(analysis_df: pd.DataFrame, chunks_df: pd.DataFrame, file_key: str = None) -> None:
    """Display analysis results in a consistent format for both individual and consolidated views"""
    try:
        if analysis_df.empty:
            st.warning("No analysis results to display")
            return

        # Analysis Results Table
        st.subheader("Analysis Results")
        st.dataframe(
            data=analysis_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Question ID": st.column_config.TextColumn(
                    "Question ID",
                    width="small",
                ),
                "Analysis": st.column_config.TextColumn(
                    "Analysis",
                    width="large",
                ),
                "Score": st.column_config.NumberColumn(
                    "Score",
                    format="%.1f",
                ),
                "Key Evidence": st.column_config.TextColumn(
                    "Key Evidence",
                    width="medium",
                ),
                "Gaps": st.column_config.TextColumn(
                    "Gaps",
                    width="medium",
                ),
                "Sources": st.column_config.TextColumn(
                    "Sources",
                    width="small",
                ),
            },
        )

        # Document Chunks Table
        if not chunks_df.empty:
            st.subheader("Document Chunks")
            st.dataframe(
                data=chunks_df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Question ID": st.column_config.TextColumn(
                        "Question ID",
                        width="small",
                    ),
                    "Chunk Text": st.column_config.TextColumn(
                        "Text",
                        width="large",
                    ),
                    "Vector Similarity": st.column_config.NumberColumn(
                        "Vector Similarity",
                        format="%.4f",  # Show raw value with 4 decimal places
                    ),
                    "LLM Score": st.column_config.NumberColumn(
                        "LLM Score",
                        format="%.4f",  # Show raw value with 4 decimal places
                    ),
                    "Is Evidence": st.column_config.CheckboxColumn(
                        "Is Evidence",
                    ),
                    "Position": st.column_config.NumberColumn(
                        "Position",
                        width="small",
                    ),
                },
            )

        # Add download buttons if file_key is provided
        if file_key:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    "Download Analysis Results",
                    convert_df(analysis_df),
                    f"analysis_results_{file_key}.csv",
                    "text/csv",
                    key=f"download_analysis_{file_key}",
                )

            with col2:
                st.download_button(
                    "Download Chunks",
                    convert_df(chunks_df),
                    f"chunks_{file_key}.csv",
                    "text/csv",
                    key=f"download_chunks_{file_key}",
                )

    except Exception as e:
        logger.error(f"Error displaying analysis results: {str(e)}", exc_info=True)
        st.error(f"Error displaying results: {str(e)}")


def display_consolidated_results(analyzer, question_set, file_path=None, selected_config=None):
    """Display consolidated results for all analyzed documents

    Args:
        analyzer: ReportAnalyzer instance
        question_set: Selected question set identifier
        file_path: Optional file path. If provided, skip file selection and use this file.
                   If None, will attempt to get file from cache (backward compatibility).
        selected_config: Optional configuration dict. If provided, skip config selection and use this config.
                        If None, will attempt to get config from cache (backward compatibility).
    """
    try:
        # Create mapping from question set names to database identifiers
        question_set_mapping = {
            "tcfd": "tcfd",
            "s4m": "s4m",
            "lucia": "lucia",
            "everest": "ev",  # Everest questions use 'ev_' prefix, so database stores as 'ev'
        }

        # Get the database identifier for the selected question set
        db_question_set = question_set_mapping.get(question_set, question_set)
        logger.info(f"Mapping question set '{question_set}' to database identifier '{db_question_set}'")

        # Get all available cache configurations
        cache_configs = analyzer.analyzer.cache_manager.check_cache_status()
        logger.info(f"Found cache configs: {cache_configs}")

        if not cache_configs:
            st.warning("No stored analyses found")
            return

        # Group configurations by file
        file_configs = {}
        for config in cache_configs:
            if len(config) == 6:  # Full config row from cache_status
                file_path, chunk_size, chunk_overlap, top_k, model, qs = config
                if qs == db_question_set:  # Only show configs for selected question set using database identifier
                    if file_path not in file_configs:
                        file_configs[file_path] = []
                    file_configs[file_path].append(
                        {
                            "chunk_size": chunk_size,
                            "chunk_overlap": chunk_overlap,
                            "top_k": top_k,
                            "model": model,
                            "question_set": qs,
                        }
                    )

        if not file_configs:
            st.warning(f"No stored results found for question set: {question_set}")
            return

        # File selection
        st.subheader("Select Report and Configuration")
        file_path = st.selectbox(
            "Select Report",
            options=list(file_configs.keys()),
            format_func=lambda x: Path(x).name,
        )

        if file_path:
            # Show configurations for selected file
            configs = file_configs[file_path]
            config_options = []
            for config in configs:
                label = f"Chunk: {config['chunk_size']}, Overlap: {config['chunk_overlap']}, Top-K: {config['top_k']}, Model: {config['model']}"
                config_options.append({"label": label, "config": config})

            selected_config = st.selectbox(
                "Select Configuration",
                options=config_options,
                format_func=lambda x: x["label"],
            )

            if selected_config:
                logger.info(f"Getting results for {Path(file_path).name} with config: {selected_config['config']}")

                # Add similarity search section for document chunks
                try:
                    raw_chunks = analyzer.analyzer.cache_manager.get_document_chunks(
                        file_path=file_path,
                        chunk_size=selected_config["config"]["chunk_size"],
                        chunk_overlap=selected_config["config"]["chunk_overlap"],
                    )

                    if raw_chunks:
                        # Add similarity search controls
                        st.subheader("Similarity Search")

                        # Get questions for the current question set
                        # Make sure analyzer is using the correct question set
                        if analyzer.analyzer.question_set != question_set:
                            analyzer.analyzer.update_question_set(question_set)
                        questions = analyzer.analyzer.questions

                        col1, col2 = st.columns([1, 1])
                        with col1:
                            # Question dropdown with shorter, cleaner options
                            question_options = ["None"] + [f"{q_id}" for q_id in questions.keys()]
                            selected_question_id = st.selectbox(
                                "Select a question to sort by similarity:",
                                options=question_options,
                                key="chunk_similarity_question",
                                help="Choose a question from the current question set",
                            )

                            # Show selected question text below dropdown
                            if selected_question_id != "None" and selected_question_id in questions:
                                st.caption(f"**{selected_question_id}:** {questions[selected_question_id]['text'][:100]}...")
                            selected_question = selected_question_id

                        with col2:
                            # Free text input
                            custom_question = st.text_input(
                                "Or enter custom question:",
                                placeholder="Enter your own question to compare chunks against...",
                                key="chunk_similarity_custom",
                            )

                        # Determine which question to use
                        query_text = None
                        if custom_question.strip():
                            query_text = custom_question.strip()
                            st.info(f"Using custom question: {query_text[:100]}...")
                        elif selected_question != "None":
                            if selected_question in questions:
                                query_text = questions[selected_question]["text"]
                                st.info(f"Using question {selected_question}: {query_text[:100]}...")

                        # Process chunks
                        chunks_rows = []
                        chunks_with_embeddings = [c for c in raw_chunks if c.get("embedding") is not None]

                        if query_text and chunks_with_embeddings:
                            # Compute similarity scores
                            try:
                                # Check if embeddings are available
                                if not analyzer.analyzer.embeddings or analyzer.analyzer.use_backend_llm:
                                    st.warning(
                                        "Embeddings not available for similarity search. Using backend mode or embeddings not initialized."
                                    )
                                    query_text = None
                                else:
                                    # Get query embedding
                                    query_embedding = analyzer.analyzer.embeddings.get_text_embedding(query_text)
                                    query_embedding = np.array(query_embedding, dtype=np.float32)

                                    # Compute similarity for each chunk
                                    similarities = []
                                    for chunk in raw_chunks:
                                        if chunk.get("embedding") is not None:
                                            chunk_embedding = np.frombuffer(chunk["embedding"], dtype=np.float32)
                                            # Compute cosine similarity
                                            similarity = np.dot(query_embedding, chunk_embedding) / (
                                                np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                                            )
                                            similarities.append(similarity)
                                        else:
                                            similarities.append(0.0)

                                    # Sort chunks by similarity
                                    chunk_similarity_pairs = list(zip(raw_chunks, similarities))
                                    chunk_similarity_pairs.sort(key=lambda x: x[1], reverse=True)

                                    # Create rows with similarity scores
                                    for i, (chunk, similarity) in enumerate(chunk_similarity_pairs):
                                        chunk_row = {
                                            "Rank": i + 1,
                                            "Similarity": similarity,
                                            "Text": chunk.get("text", chunk.get("chunk_text", "")),
                                            "Has Embedding": chunk.get("embedding") is not None,
                                            "Chunk Size": chunk.get("chunk_size", "N/A"),
                                            "Chunk Overlap": chunk.get("chunk_overlap", "N/A"),
                                        }
                                        chunks_rows.append(chunk_row)

                                    st.success(f"✓ Sorted {len(chunks_rows)} chunks by similarity to query")

                            except Exception as e:
                                st.error(f"Error computing similarity: {str(e)}")
                                logger.error(
                                    f"Error computing similarity: {str(e)}",
                                    exc_info=True,
                                )
                                # Fall back to original display
                                for i, chunk in enumerate(raw_chunks):
                                    chunk_row = {
                                        "Chunk #": i + 1,
                                        "Text": chunk.get("text", chunk.get("chunk_text", "")),
                                        "Has Embedding": chunk.get("embedding") is not None,
                                        "Chunk Size": chunk.get("chunk_size", "N/A"),
                                        "Chunk Overlap": chunk.get("chunk_overlap", "N/A"),
                                    }
                                    chunks_rows.append(chunk_row)

                        else:
                            # No query or no embeddings - show original order
                            for i, chunk in enumerate(raw_chunks):
                                chunk_row = {
                                    "Chunk #": i + 1,
                                    "Text": chunk.get("text", chunk.get("chunk_text", "")),
                                    "Has Embedding": chunk.get("embedding") is not None,
                                    "Chunk Size": chunk.get("chunk_size", "N/A"),
                                    "Chunk Overlap": chunk.get("chunk_overlap", "N/A"),
                                }
                                chunks_rows.append(chunk_row)

                            if query_text and not chunks_with_embeddings:
                                st.warning(
                                    "No chunks with embeddings found. Run Step 2 to generate embeddings for similarity search."
                                )

                        # Display chunks
                        if chunks_rows:
                            chunks_df = pd.DataFrame(chunks_rows)

                            # Configure columns based on whether we have similarity scores
                            if query_text and chunks_with_embeddings:
                                column_config = {
                                    "Rank": st.column_config.NumberColumn(
                                        "Rank",
                                        width="small",
                                    ),
                                    "Similarity": st.column_config.NumberColumn(
                                        "Similarity",
                                        format="%.4f",
                                        width="small",
                                    ),
                                    "Text": st.column_config.TextColumn(
                                        "Text",
                                        width="large",
                                    ),
                                    "Has Embedding": st.column_config.CheckboxColumn(
                                        "Has Embedding",
                                    ),
                                    "Chunk Size": st.column_config.NumberColumn(
                                        "Chunk Size",
                                        width="small",
                                    ),
                                    "Chunk Overlap": st.column_config.NumberColumn(
                                        "Chunk Overlap",
                                        width="small",
                                    ),
                                }
                            else:
                                column_config = {
                                    "Chunk #": st.column_config.NumberColumn(
                                        "Chunk #",
                                        width="small",
                                    ),
                                    "Text": st.column_config.TextColumn(
                                        "Text",
                                        width="large",
                                    ),
                                    "Has Embedding": st.column_config.CheckboxColumn(
                                        "Has Embedding",
                                    ),
                                    "Chunk Size": st.column_config.NumberColumn(
                                        "Chunk Size",
                                        width="small",
                                    ),
                                    "Chunk Overlap": st.column_config.NumberColumn(
                                        "Chunk Overlap",
                                        width="small",
                                    ),
                                }

                            st.dataframe(
                                data=chunks_df,
                                use_container_width=True,
                                hide_index=True,
                                column_config=column_config,
                            )

                            st.info(f"✓ Found {len(chunks_rows)} total document chunks in this configuration.")
                        else:
                            st.warning("No chunks found. Run Step 1 to generate document chunks first.")

                except Exception as e:
                    logger.warning(f"Error displaying document chunks with similarity search: {str(e)}")
                    # Continue to show analysis results even if chunk display fails

                # Get cached results
                cached_results = analyzer.analyzer.cache_manager.get_analysis(
                    file_path=file_path, config=selected_config["config"]
                )

                if cached_results:
                    # Get questions data
                    questions = analyzer.analyzer.questions

                    # Process results into analysis rows
                    analysis_rows = []
                    chunks_rows = []

                    for question_id, data in cached_results.items():
                        try:
                            # Create analysis row
                            result = data.get("result", {})
                            analysis_row = {
                                "Question ID": question_id,
                                "Question Text": (questions[question_id]["text"] if question_id in questions else question_id),
                                "Analysis": result.get("ANSWER", ""),
                                "Score": float(result.get("SCORE", 0)),
                                "Key Evidence": "\n".join([e.get("text", "") for e in result.get("EVIDENCE", [])]),
                                "Gaps": "\n".join(result.get("GAPS", [])),
                                "Sources": ", ".join(map(str, result.get("SOURCES", []))),
                            }
                            analysis_rows.append(analysis_row)
                            logger.debug(f"Added analysis row for {question_id}: {json.dumps(analysis_row, indent=2)}")

                            # Process chunks if available
                            if "chunks" in data:
                                for chunk in data["chunks"]:
                                    chunk_row = {
                                        "Question ID": question_id,
                                        "Text": chunk.get("text", ""),
                                        "Vector Similarity": chunk.get("similarity_score", 0.0),
                                        "LLM Score": chunk.get("llm_score", 0.0),
                                        "Is Evidence": chunk.get("is_evidence", False),
                                        "Position": chunk.get("chunk_order", 0),
                                    }
                                    chunks_rows.append(chunk_row)

                        except Exception as e:
                            logger.error(
                                f"Error processing result for question {question_id}: {str(e)}",
                                exc_info=True,
                            )
                            continue

                    # Create DataFrames
                    if analysis_rows:
                        analysis_df = pd.DataFrame(analysis_rows)
                        chunks_df = pd.DataFrame(chunks_rows) if chunks_rows else pd.DataFrame()

                        # Display results using the existing display function
                        file_key = f"{Path(file_path).stem}_cs{selected_config['config']['chunk_size']}"
                        display_analysis_results(analysis_df, chunks_df, file_key)
                    else:
                        st.warning("No results found in stored for this configuration")
                else:
                    st.warning("No stored results found for this configuration")

    except Exception as e:
        logger.error(f"Error displaying consolidated results: {str(e)}", exc_info=True)
        st.error(f"Error displaying consolidated results: {str(e)}")


def display_cache_selector(file_path: str):
    """Display cache management options"""
    st.subheader("Stored Data Management")

    # Get current configuration
    current_config = {
        "chunk_size": st.session_state.new_chunk_size,
        "chunk_overlap": st.session_state.new_overlap,
        "top_k": st.session_state.new_top_k,
        "model": st.session_state.new_llm_model,
        "question_set": st.session_state.new_question_set,
    }

    if "analyzer" in st.session_state:
        # Show cache status using cache manager
        try:
            cache_entries = st.session_state.analyzer.analyzer.cache_manager.check_cache_status(file_path)
            if cache_entries:
                st.text(f"Found {len(cache_entries)} cached configurations:")
                for entry in cache_entries:
                    st.text(f"• Configuration: {entry}")

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"Current configuration: {current_config}")

                with col2:
                    if st.button("Clear Stored Data for File"):
                        try:
                            st.session_state.analyzer.analyzer.cache_manager.clear_cache(file_path)
                            st.success(f"Stored data cleared for file.")
                            # Clear results from session state
                            if "results" in st.session_state:
                                del st.session_state.results
                            if "analysis_df" in st.session_state:
                                del st.session_state.analysis_df
                            if "chunks_df" in st.session_state:
                                del st.session_state.chunks_df
                            st.session_state.analysis_complete = False
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error clearing stored data: {str(e)}")
            else:
                st.info("No stored analyses available for this file")
        except Exception as e:
            st.error(f"Error checking stored data status: {str(e)}")


def get_current_settings(st) -> dict:
    """Get all current settings from the UI widgets"""
    # Get first question set as default
    default_set = list(question_sets.keys())[0]

    # Ensure LLM scoring setting is synced
    if "new_llm_scoring" in st.session_state:
        st.session_state.use_llm_scoring = st.session_state.new_llm_scoring

    return {
        "chunk_size": st.session_state.get("new_chunk_size", 500),
        "overlap": st.session_state.get("new_overlap", 20),
        "top_k": st.session_state.get("new_top_k", 5),
        "llm_model": st.session_state.get("new_llm_model", LLM_MODELS[0]),
        "use_llm_scoring": st.session_state.get("new_llm_scoring", False),
        "batch_scoring": st.session_state.get("new_batch_scoring", True),
        "selected_set": st.session_state.get("new_question_set", default_set),
    }


def update_analyzer_parameters():
    """Update analyzer parameters based on session state."""
    if "analyzer" not in st.session_state:
        return

    analyzer = st.session_state.analyzer

    # Get the current parameters from session state
    chunk_size = st.session_state.new_chunk_size
    chunk_overlap = st.session_state.new_overlap
    top_k = st.session_state.new_top_k
    llm_model = st.session_state.new_llm_model

    # Validate selected model availability
    if llm_model.startswith("gemini-") and not os.getenv("GOOGLE_API_KEY"):
        # If somehow a Gemini model was selected but no API key exists
        logger.error(f"Attempt to use Gemini model '{llm_model}' without API key")
        st.error(f"Cannot use {llm_model} - No Google API key is set. Defaulting to {OPENAI_MODELS[0]}.")
        # Reset to default OpenAI model
        llm_model = OPENAI_MODELS[0]
        st.session_state.new_llm_model = llm_model
    elif llm_model.startswith("gpt-") and not os.getenv("OPENAI_API_KEY"):
        logger.error(f"Attempt to use OpenAI model '{llm_model}' without API key")
        st.error(f"OPENAI_API_KEY environment variable is not set. OpenAI models will not work correctly.")

    # Update the analyzer with the new parameters
    try:
        # Update the chunk size and chunk overlap first
        analyzer.analyzer.update_parameters(chunk_size, chunk_overlap, top_k)

        # Update the LLM model name
        analyzer.analyzer.update_llm_model(llm_model)

        # Store parameters in session state
        st.session_state.chunk_size = chunk_size
        st.session_state.chunk_overlap = chunk_overlap
        st.session_state.top_k = top_k
        st.session_state.llm_model = llm_model

        # Sync LLM scoring checkbox with session state
        if "new_llm_scoring" in st.session_state:
            st.session_state.use_llm_scoring = st.session_state.new_llm_scoring
            logger.info(f"Updated use_llm_scoring to: {st.session_state.use_llm_scoring}")

    except Exception as e:
        st.error(f"Error updating parameters: {str(e)}")


async def run_analysis(analyzer, file_path, selected_questions, progress_text):
    """Run analysis and update the UI with progress"""
    try:
        # Get current configuration
        config = {
            "chunk_size": st.session_state.chunk_size,
            "chunk_overlap": st.session_state.chunk_overlap,
            "top_k": st.session_state.top_k,
            "model": st.session_state.llm_model,
            "question_set": st.session_state.question_set,
        }
        logger.info(f"[ANALYSIS] User triggered analysis for file: {file_path}")
        logger.info(f"[ANALYSIS] Selected questions: {selected_questions}")
        if "questions" in st.session_state:
            logger.info(
                f"[ANALYSIS] Selected question texts: {[st.session_state.questions[q]['text'] for q in selected_questions if q in st.session_state.questions]}"
            )
        logger.info(
            f"[CACHE] Looking up cache for file: {file_path} with config: {config} and questions: {selected_questions}"
        )
        # Check if we have cached results first
        cached_results = analyzer.cache_manager.get_analysis(
            file_path=file_path,
            config=config,
            question_ids=[f"{config['question_set']}_{q}" for q in selected_questions],
        )
        if cached_results and not st.session_state.get("force_recompute", False):
            logger.info(f"[CACHE] Cache HIT for config: {config}")
            progress_text.success("Found stored results!")
            st.session_state.results = cached_results
            logger.info(f"[ANALYSIS] Writing results to session state for file: {file_path}")
            logger.info(f"[ANALYSIS] Attempting to display results for file: {file_path}")
            return
        else:
            logger.info(f"[CACHE] Cache MISS for config: {config}")
        # If no cached results or force recompute, run analysis
        progress_text.info("Starting analysis...")

        # Log the LLM scoring setting
        llm_scoring_enabled = st.session_state.get("new_llm_scoring", False)
        progress_text.info(f"LLM scoring: {'Enabled' if llm_scoring_enabled else 'Disabled'}")
        logger.info(f"Starting analysis with LLM scoring: {llm_scoring_enabled}")

        # Track results
        all_results = {}

        # Convert selected_questions from full IDs (e.g., "tcfd_1") to just numbers (e.g., 1)
        question_numbers = []
        for q_id in selected_questions:
            # Extract the number part from the question ID
            parts = q_id.split("_")
            if len(parts) > 1:
                try:
                    question_numbers.append(int(parts[1]))
                except ValueError:
                    progress_text.warning(f"Invalid question ID format: {q_id}")
            else:
                progress_text.warning(f"Invalid question ID format: {q_id}")

        # Check if we have pre-retrieved chunks (for backend resources)
        pre_retrieved_chunks = st.session_state.get("backend_chunks")

        # First update the analyzer's process_document method to use progress_text instead of yielding status
        async for result in analyzer.process_document(
            file_path=file_path,
            selected_questions=question_numbers,  # Pass just the numbers
            use_llm_scoring=st.session_state.get("new_llm_scoring", False),  # Use the checkbox value directly
            force_recompute=st.session_state.get("force_recompute", False),
            pre_retrieved_chunks=pre_retrieved_chunks,  # Pass backend chunks if available
        ):
            # Handle errors by displaying them but not storing them
            if "error" in result:
                progress_text.error(f"Error: {result['error']}")
                continue

            # Handle status updates by displaying them but not storing them
            if "status" in result:
                progress_text.info(result["status"])
                continue

            # Process actual analysis results
            question_id = result.get("question_id")
            if not question_id:
                # Try to construct question_id from question_number
                question_number = result.get("question_number")
                if question_number:
                    question_id = f"{st.session_state.question_set}_{question_number}"
                else:
                    # Skip results without question_id or question_number
                    continue

            progress_text.info(f"Completed analysis for question {question_id}")

            # Store only the actual result data
            result_data = result.get("result", result)
            all_results[question_id] = result_data

        # After all questions are processed, get the complete results with chunks
        final_results = analyzer.cache_manager.get_analysis(
            file_path=file_path, config=config, question_ids=list(all_results.keys())
        )

        if not final_results:
            # If no results from cache, use the ones we just processed
            final_results = all_results

        # When writing results to session state
        logger.info(f"[ANALYSIS] Writing results to session state for file: {file_path}")
        st.session_state.results = final_results
        logger.info(f"[ANALYSIS] Attempting to display results for file: {file_path}")
        progress_text.success("Analysis complete!")

    except Exception as e:
        progress_text.error(f"Error during analysis: {str(e)}")
        logger.error(f"Error during analysis: {str(e)}", exc_info=True)


def main():
    """Main function for the Streamlit app"""
    try:
        # Initialize session state variables if they don't exist
        if "chunk_size" not in st.session_state:
            st.session_state.chunk_size = 500  # Default chunk size

        if "chunk_overlap" not in st.session_state:
            st.session_state.chunk_overlap = 0  # Default chunk overlap

        if "top_k" not in st.session_state:
            st.session_state.top_k = 10  # Default number of chunks to retrieve

        if "llm_model" not in st.session_state:
            st.session_state.llm_model = "gpt-4o-mini"  # Default model

        if "question_set" not in st.session_state:
            st.session_state.question_set = "tcfd"  # Default question set

        if "use_llm_scoring" not in st.session_state:
            st.session_state.use_llm_scoring = False  # Default LLM scoring setting

        if "force_recompute" not in st.session_state:
            st.session_state.force_recompute = False  # Default recompute setting

        if "results" not in st.session_state:
            st.session_state.results = {}  # Initialize empty results

        if "current_file" not in st.session_state:
            st.session_state.current_file = None  # Initialize current file

        if "file_processed" not in st.session_state:
            st.session_state.file_processed = False  # Initialize file processed flag

        if "analysis_complete" not in st.session_state:
            st.session_state.analysis_complete = False  # Initialize analysis complete flag

        # Initialize use_s3_upload in session state if not already set
        # Respect override_s3_upload if user has temporarily disabled it
        if "use_s3_upload" not in st.session_state:
            env_s3_upload = os.getenv("USE_S3_UPLOAD", "false").lower() == "true"
            override = st.session_state.get("override_s3_upload", False)
            st.session_state.use_s3_upload = env_s3_upload and not override

        # Sync API keys from session state to environment at startup
        APIKeyManager.sync_api_keys_to_env(st.session_state)

        st.set_page_config(page_title="Report Analyst", layout="wide")

        # Inject Material Icons link tag at the top
        st.markdown(
            '<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">',
            unsafe_allow_html=True,
        )

        # Inject MINIMAL custom CSS for specific customizations only
        # Let Streamlit handle most theming automatically
        try:
            # Minimal custom CSS - only for active sidebar item styling
            custom_css = """
            <style>
            /* Import fonts from Google Fonts */
            @import url('https://fonts.googleapis.com/css2?family=Afacad:wght@400;500;600;700&display=swap');
            @import url('https://fonts.googleapis.com/css2?family=Cousine:wght@400;700&display=swap');
            @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
            
            /* Material Icons base styles */
            .material-icons,
            i.material-icons {
                font-family: 'Material Icons';
                font-weight: normal;
                font-style: normal;
                font-size: 24px;
                line-height: 1;
                letter-spacing: normal;
                text-transform: none;
                display: inline-block;
                white-space: nowrap;
                word-wrap: normal;
                direction: ltr;
                -webkit-font-feature-settings: 'liga';
                -webkit-font-smoothing: antialiased;
                vertical-align: middle;
                margin-right: 8px;
            }
            
            /* Fix Material Icons rendering issues for Streamlit's stIconMaterial component */
            [data-testid="stIconMaterial"] {
                font-family: 'Material Icons' !important;
                font-feature-settings: 'liga' !important;
                -webkit-font-feature-settings: 'liga' !important;
                font-weight: normal !important;
                font-style: normal !important;
                text-transform: none !important;
                letter-spacing: normal !important;
            }
            
            /* @font-face fallback for Material Icons */
            @font-face {
                font-family: 'Material Icons';
                font-style: normal;
                font-weight: 400;
                src: url(https://fonts.gstatic.com/s/materialicons/v142/flUhRq6tzZclQEJ-Vdg-IuiaDsNc.woff2) format('woff2');
            }
            
            /* Add Material Icon to stAlert elements - only ONE icon per alert */
            /* Add icon only to the markdown container, NOT to paragraphs to avoid duplicates */
            [data-testid="stAlert"] [data-testid="stMarkdownContainer"]::before {
                content: 'info';
                font-family: 'Material Icons';
                font-size: 20px;
                vertical-align: middle;
                margin-right: 8px;
                display: inline-block;
            }
            
            /* Remove icons from paragraphs inside stAlert to prevent double icons */
            [data-testid="stAlert"] p::before {
                content: none !important;
                display: none !important;
            }
            
            /* Add icons to custom notifications */
            [data-testid="stNotification"] [data-testid="stMarkdownContainer"]::before {
                content: 'info';
                font-family: 'Material Icons';
                font-size: 20px;
                vertical-align: middle;
                margin-right: 8px;
                display: inline-block;
            }
            
            /* Remove icons from paragraphs in custom notifications too */
            [data-testid="stNotification"] p::before {
                content: none !important;
                display: none !important;
            }
            
            /* Settings expander icon in sidebar */
            [data-testid="stSidebar"] [data-testid="stExpander"] summary::before {
                content: 'settings';
                font-family: 'Material Icons';
                font-size: 20px;
                vertical-align: middle;
                margin-right: 8px;
                display: inline-block;
            }
            
            /* Active navigation item - light purple background with dark purple text */
            [data-testid="stSidebar"] .nav-link-selected {
                background-color: rgba(67, 19, 200, 0.15) !important;
                color: #4313C8 !important;
                font-weight: 700 !important;
            }
            
            /* Active navigation item icon - dark purple */
            [data-testid="stSidebar"] .nav-link-selected i {
                color: #4313C8 !important;
            }
            
            /* Inactive navigation items - gray text and icons */
            [data-testid="stSidebar"] .nav-link:not(.nav-link-selected) {
                color: #7872A7 !important;
            }
            
            [data-testid="stSidebar"] .nav-link:not(.nav-link-selected) i {
                color: #7872A7 !important;
            }
            
            /* Designer Colors - Exact specifications from Daniela */
            
            /* ========== LIGHT MODE ========== */
            
            /* Main app background - #F5F7FF */
            .stApp {
                background-color: #F5F7FF !important;
                font-family: 'Afacad', sans-serif !important;
            }
            
            /* Primary font - Afacad for titles and body text */
            body, .main, p, span, div, label {
                font-family: 'Afacad', sans-serif !important;
            }
            
            /* Titles use Afacad */
            h1, h2, h3, h4, h5, h6 {
                font-family: 'Afacad', sans-serif !important;
            }
            
            /* Secondary font - Cousine for UI elements */
            button, .stButton > button,
            input, textarea, select,
            .stTextInput input, .stTextArea textarea, .stSelectbox select,
            [data-baseweb="select"],
            [data-baseweb="input"],
            ::placeholder,
            .stCaption, small,
            [data-testid="stCaptionContainer"],
            code, pre {
                font-family: 'Cousine', monospace !important;
            }
            
            /* Main container - #FFFFFF */
            .main .block-container {
                background-color: #FFFFFF !important;
            }
            
            /* Secondary containers - C0C4FA 10% opacity */
            [data-testid="stExpander"],
            .stAlert,
            [data-testid="stNotification"],
            .stInfo {
                background-color: rgba(192, 196, 250, 0.1) !important;
            }
            
            /* Fix text layout - prevent vertical stacking */
            .stInfo {
                word-break: normal !important;
                white-space: normal !important;
            }
            
            .stInfo p,
            .stInfo span {
                writing-mode: horizontal-tb !important;
                text-orientation: mixed !important;
            }
            
            /* Ensure columns don't cause vertical text */
            [data-testid="column"] {
                min-width: 0 !important;
            }
            
            [data-testid="column"] * {
                word-break: normal !important;
                white-space: normal !important;
            }
            
            /* Titles - #4313C8 */
            h1, h2, [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2 {
                color: #4313C8 !important;
            }
            
            /* Subtitles - #979DF6 */
            h3, h4, [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4 {
                color: #979DF6 !important;
            }
            
            /* Body text - #170843 */
            p, span, label {
                color: #170843 !important;
            }
            
            /* Don't force color on all divs - let them inherit to prevent layout issues */
            div:not([data-testid="stSidebar"] div):not(.stCheckbox):not([data-testid="stMarkdownContainer"]) {
                color: #170843 !important;
            }
            
            /* Caption text - #718096 */
            .stCaption, small, [data-testid="stCaptionContainer"] {
                color: #718096 !important;
            }
            
            /* Sidebar - white background */
            [data-testid="stSidebar"] {
                background-color: #FFFFFF !important;
            }
            
            /* Sidebar text - #7872A7 (exclude option-menu navigation) */
            [data-testid="stSidebar"] *:not([data-testid="stSidebarNav"] [aria-current="page"] *):not(.nav-link):not(.nav-link-selected):not(.nav-link *):not([class*="nav-link"]) {
                color: #7872A7 !important;
            }
            
            /* Ensure option-menu navigation styles are not overridden */
            [data-testid="stSidebar"] .nav-link,
            [data-testid="stSidebar"] .nav-link-selected {
                color: inherit !important;
            }
            
            /* File Display Panel - Unique class for green panel styling */
            /* The key="file-display-panel" creates the class st-key-file-display-panel */
            /* Target the container element which has the st-key- class */
            [data-testid="stVerticalBlock"].st-key-file-display-panel,
            .st-key-file-display-panel[data-testid="stVerticalBlock"] {
                background-color: #E8F5E9 !important;
                border-radius: 12px !important;
                padding: 1rem 1.5rem !important;
                margin: 1rem 0 1.5rem 0 !important;
            }
            
            /* Target the horizontal block inside the container (for columns) */
            .st-key-file-display-panel [data-testid="stHorizontalBlock"] {
                background-color: transparent !important;
            }

            /* Ensure columns inside the file display panel have transparent background */
            .st-key-file-display-panel [data-testid="column"] {
                background-color: transparent !important;
            }
            
            /* Keep upload date gray */
            .st-key-file-display-panel .pdf-upload-date {
                color: #718096 !important;
            }
            
            .pdf-icon-box {
                background-color: #C8E6C9;
                border-radius: 12px;
                width: 56px;
                height: 56px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }
            
            .pdf-icon-box .material-icons,
            .pdf-icon-box i.material-icons {
                font-size: 28px !important;
                color: #2E7D32 !important;
                display: inline-block !important;
            }
            
            .pdf-info-section {
                flex-grow: 1;
            }
            
            .pdf-upload-date {
                font-size: 13px;
                color: #718096;
                display: block;
                margin-top: 4px;
            }
            
            /* Style ONLY the PDF selectbox - target it specifically within the file display panel */
            /* Make the selectbox container bigger */
            .st-key-file-display-panel [data-baseweb="select"] {
                min-width: 300px !important;
                max-width: 500px !important;
            }
            
            /* Target the main selectbox wrapper */
            .st-key-file-display-panel [data-baseweb="select"] > div {
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }
            
            /* Target the div with value attribute (the displayed text) - make it bigger, bolder, and green */
            .st-key-file-display-panel [data-baseweb="select"] div[value] {
                font-size: 22px !important;
                font-weight: 800 !important;
                color: #1B9E6B !important;
            }
            
            /* Also target by the specific class pattern for the value div */
            .st-key-file-display-panel [data-baseweb="select"] [class*="st-dn"] {
                font-size: 22px !important;
                font-weight: 800 !important;
                color: #1B9E6B !important;
            }
            
            /* Target nested divs that contain the text */
            .st-key-file-display-panel [data-baseweb="select"] > div > div > div[value],
            .st-key-file-display-panel [data-baseweb="select"] > div > div > div[class*="st-dn"] {
                font-size: 22px !important;
                font-weight: 800 !important;
                color: #1B9E6B !important;
            }
            
            /* Make the dropdown arrow bigger, bold, and green */
            .st-key-file-display-panel [data-baseweb="select"] svg {
                color: #1B9E6B !important;
                width: 28px !important;
                height: 28px !important;
            }
            
            .st-key-file-display-panel [data-baseweb="select"] svg path,
            .st-key-file-display-panel [data-baseweb="select"] svg polygon {
                stroke-width: 4 !important;
                stroke: #1B9E6B !important;
                fill: #1B9E6B !important;
            }
            
            /* Question Set Display Panel - same styling as file display panel */
            [data-testid="stVerticalBlock"].st-key-question-set-display-panel,
            .st-key-question-set-display-panel[data-testid="stVerticalBlock"] {
                background-color: #E8F5E9 !important;
                border-radius: 12px !important;
                padding: 1rem 1.5rem !important;
                margin: 1rem 0 0.5rem 0 !important;
            }
            
            .st-key-question-set-display-panel [data-testid="stHorizontalBlock"] {
                background-color: transparent !important;
            }
            
            .st-key-question-set-display-panel [data-testid="column"] {
                background-color: transparent !important;
            }
            
            .st-key-question-set-display-panel [data-baseweb="select"] {
                min-width: 300px !important;
                max-width: 500px !important;
            }
            
            .st-key-question-set-display-panel [data-baseweb="select"] > div {
                background-color: transparent !important;
                border: none !important;
                box-shadow: none !important;
            }
            
            .st-key-question-set-display-panel [data-baseweb="select"] div[value],
            .st-key-question-set-display-panel [data-baseweb="select"] [class*="st-dn"],
            .st-key-question-set-display-panel [data-baseweb="select"] > div > div > div[value],
            .st-key-question-set-display-panel [data-baseweb="select"] > div > div > div[class*="st-dn"] {
                font-size: 22px !important;
                font-weight: 800 !important;
                color: #1B9E6B !important;
            }
            
            .st-key-question-set-display-panel [data-baseweb="select"] svg {
                color: #1B9E6B !important;
                width: 28px !important;
                height: 28px !important;
            }
            
            .st-key-question-set-display-panel [data-baseweb="select"] svg path,
            .st-key-question-set-display-panel [data-baseweb="select"] svg polygon {
                stroke-width: 4 !important;
                stroke: #1B9E6B !important;
                fill: #1B9E6B !important;
            }
            
            /* Styled Selectboxes - White background, thin border */
            /* Only target selectboxes that are NOT in the PDF container */
            /* Target selectboxes inside expanders or other sections, but NOT in PDF container */
            [data-testid="stExpander"] [data-baseweb="select"] > div,
            [data-testid="stExpander"] [data-baseweb="select"] > div > div {
                background-color: #FFFFFF !important;
                border: 1px solid #E2E8F0 !important;
                border-radius: 4px !important;
            }
            
            /* Ensure selectboxes in expanders have normal text color (NOT green) */
            [data-testid="stExpander"] [data-baseweb="select"] > div > div > div {
                color: #170843 !important;
            }
            
            /* Ensure selectbox arrows in expanders are NOT green */
            [data-testid="stExpander"] [data-baseweb="select"] svg path,
            [data-testid="stExpander"] [data-baseweb="select"] svg polygon {
                stroke: #170843 !important;
                fill: #170843 !important;
                stroke-width: 1 !important;
            }
            
            [data-testid="stExpander"] [data-baseweb="select"]:hover > div,
            [data-testid="stExpander"] [data-baseweb="select"]:hover > div > div {
                border-color: #4313C8 !important;
            }
            
            /* Styled Questions Table */
            .questions-table-container {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 8px;
                padding: 1rem;
                margin: 1rem 0;
            }
            
            /* Sidebar accent (active item) - #4313C8 with white text */
            [data-testid="stSidebarNav"] li[aria-selected="true"],
            [data-testid="stSidebarNav"] a[aria-selected="true"],
            [data-testid="stSidebarNav"] li[aria-current="page"],
            [data-testid="stSidebarNav"] a[aria-current="page"] {
                background-color: #4313C8 !important;
                border-radius: 4px !important;
            }
            
            /* Active sidebar item text and icons - white */
            [data-testid="stSidebarNav"] li[aria-current="page"] *,
            [data-testid="stSidebarNav"] a[aria-current="page"] * {
                color: #ffffff !important;
                fill: #ffffff !important;
            }
            
            /* Sidebar navigation radio buttons - styled like screen design */
            [data-testid="stSidebar"] [data-baseweb="radio"] {
                display: flex !important;
                flex-direction: column !important;
                gap: 4px !important;
            }
            
            /* Hide radio button input circles completely */
            [data-testid="stSidebar"] [data-baseweb="radio"] input[type="radio"] {
                display: none !important;
                visibility: hidden !important;
                opacity: 0 !important;
                position: absolute !important;
                width: 0 !important;
                height: 0 !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            
            /* Hide the radio button circle indicators */
            [data-testid="stSidebar"] [data-baseweb="radio"] > div > div:first-child,
            [data-testid="stSidebar"] [data-baseweb="radio"] label::before,
            [data-testid="stSidebar"] [data-baseweb="radio"] label > div:first-child:not(span) {
                display: none !important;
            }
            
            [data-testid="stSidebar"] [data-baseweb="radio"] > label {
                padding: 10px 15px !important;
                border-radius: 6px !important;
                margin: 2px 0 !important;
                transition: all 0.2s ease !important;
                cursor: pointer !important;
                background-color: transparent !important;
                border: none !important;
                display: flex !important;
                align-items: center !important;
                gap: 8px !important;
            }
            
            [data-testid="stSidebar"] [data-baseweb="radio"] > label:hover {
                background-color: rgba(67, 19, 200, 0.1) !important;
            }
            
            /* Inactive sidebar items - purple text */
            [data-testid="stSidebar"] [data-baseweb="radio"] label {
                color: #4313C8 !important;
            }
            
            [data-testid="stSidebar"] [data-baseweb="radio"] label span {
                color: #4313C8 !important;
                font-family: 'Cousine', monospace !important;
                font-weight: 400 !important;
            }
            
            /* Active/selected sidebar item - purple background with white text */
            /* Streamlit uses a div wrapper with data-checked attribute */
            [data-testid="stSidebar"] [data-baseweb="radio"] > div[data-checked="true"] > label,
            [data-testid="stSidebar"] [data-baseweb="radio"] > div[data-checked="true"] label,
            [data-testid="stSidebar"] [data-baseweb="radio"] label[data-checked="true"],
            [data-testid="stSidebar"] [data-baseweb="radio"] input[type="radio"]:checked ~ label,
            [data-testid="stSidebar"] [data-baseweb="radio"] input[type="radio"]:checked + label {
                background-color: #4313C8 !important;
                color: #ffffff !important;
                border-radius: 6px !important;
                font-weight: 700 !important;
            }
            
            /* Also target the parent div when checked */
            [data-testid="stSidebar"] [data-baseweb="radio"] > div[data-checked="true"] {
                background-color: #4313C8 !important;
                border-radius: 6px !important;
            }
            
            /* Active sidebar item text - white and bold */
            [data-testid="stSidebar"] [data-baseweb="radio"] input[type="radio"]:checked ~ label span,
            [data-testid="stSidebar"] [data-baseweb="radio"] input[type="radio"]:checked + label span,
            [data-testid="stSidebar"] [data-baseweb="radio"] label[data-checked="true"] span,
            [data-testid="stSidebar"] [data-baseweb="radio"] label[aria-checked="true"] span,
            [data-testid="stSidebar"] [data-baseweb="radio"] > div > label[data-checked="true"] span,
            [data-testid="stSidebar"] [data-baseweb="radio"] > label[data-checked="true"] span,
            [data-testid="stSidebar"] [data-baseweb="radio"] [data-checked="true"] span {
                color: #ffffff !important;
                font-weight: 700 !important;
            }
            
            /* Active sidebar item - also target the parent container */
            [data-testid="stSidebar"] [data-baseweb="radio"] > div[data-checked="true"] > label,
            [data-testid="stSidebar"] [data-baseweb="radio"] > div[data-checked="true"] label {
                background-color: #4313C8 !important;
                color: #ffffff !important;
                font-weight: 700 !important;
            }
            
            [data-testid="stSidebar"] [data-baseweb="radio"] > div[data-checked="true"] > label span,
            [data-testid="stSidebar"] [data-baseweb="radio"] > div[data-checked="true"] label span {
                color: #ffffff !important;
                font-weight: 700 !important;
            }
            
            /* Sidebar Material Icons - match text color */
            [data-testid="stSidebar"] [data-baseweb="radio"] label .nav-material-icon,
            [data-testid="stSidebar"] [data-baseweb="radio"] label .material-icons {
                color: #4313C8 !important;
                font-size: 20px !important;
                margin-right: 8px !important;
                vertical-align: middle !important;
            }
            
            /* Active sidebar item Material Icons - white */
            [data-testid="stSidebar"] [data-baseweb="radio"] > div[data-checked="true"] > label .nav-material-icon,
            [data-testid="stSidebar"] [data-baseweb="radio"] > div[data-checked="true"] label .nav-material-icon,
            [data-testid="stSidebar"] [data-baseweb="radio"] label[data-checked="true"] .nav-material-icon,
            [data-testid="stSidebar"] [data-baseweb="radio"] input[type="radio"]:checked ~ label .nav-material-icon,
            [data-testid="stSidebar"] [data-baseweb="radio"] input[type="radio"]:checked + label .nav-material-icon {
                color: #ffffff !important;
            }
            
            /* Keep tooltip icons (help icons) visible and styled */
            [data-testid="stSidebar"] [data-baseweb="radio"] label [data-testid="stTooltipIcon"] svg,
            [data-testid="stSidebar"] [data-baseweb="radio"] label [data-testid="stTooltipHoverTarget"] svg {
                display: inline-block !important;
                color: #4313C8 !important;
                stroke: #4313C8 !important;
            }
            
            [data-testid="stSidebar"] [data-baseweb="radio"] > div[data-checked="true"] > label [data-testid="stTooltipIcon"] svg,
            [data-testid="stSidebar"] [data-baseweb="radio"] > div[data-checked="true"] label [data-testid="stTooltipIcon"] svg {
                color: #ffffff !important;
                stroke: #ffffff !important;
            }
            
            /* Green accent - #2E9D6F */
            .stSuccess {
                background-color: rgba(46, 157, 111, 0.3) !important;
                border-color: #2E9D6F !important;
                color: #2E9D6F !important;
            }
            
            /* Green cards - 30% and 10% opacity */
            [data-testid="stNotification"][data-status="success"] {
                background-color: rgba(46, 157, 111, 0.1) !important;
            }
            
            /* ========== UNIFIED BUTTON STYLES ========== */
            
            /* Help icon button - styled as icon only, no background */
            div[data-testid="stButton"] button:has-text("ℹ️") {
                background-color: transparent !important;
                color: #4313C8 !important;
                border: none !important;
                padding: 0 4px !important;
                min-width: auto !important;
                width: auto !important;
                height: auto !important;
                font-size: 18px !important;
                cursor: help !important;
                box-shadow: none !important;
                line-height: 1 !important;
            }
            
            div[data-testid="stButton"] button:has-text("ℹ️"):hover {
                background-color: transparent !important;
                color: #4313C8 !important;
                opacity: 0.7 !important;
                transform: none !important;
            }
            
            /* Select All button - small light purple button like processing steps */
            /* Target primary buttons that appear after "Select Questions" heading */
            h3:has-text("Select Questions") + div[data-testid="stButton"] button[kind="primary"],
            /* Fallback: target primary buttons with smaller text */
            div[data-testid="stButton"] button[kind="primary"] {
                background-color: rgba(192, 196, 250, 0.1) !important;
                color: #4313C8 !important;
                border: 1px solid #4313C8 !important;
                border-radius: 4px !important;
                padding: 4px 12px !important;
                font-size: 12px !important;
                font-family: 'Cousine', monospace !important;
                height: auto !important;
                min-height: 28px !important;
                width: auto !important;
                max-width: fit-content !important;
            }
            
            /* Hover state for Select All button */
            h3:has-text("Select Questions") + div[data-testid="stButton"] button[kind="primary"]:hover,
            div[data-testid="stButton"] button[kind="primary"]:hover {
                background-color: rgba(192, 196, 250, 0.2) !important;
                border-color: #4313C8 !important;
            }
            
            /* Override for larger primary buttons (like Analyze Selected Questions, Reanalyze) */
            /* These buttons have more text, so we can target them by their longer text content */
            div[data-testid="stButton"]:has(button:contains("Analyze")) button,
            div[data-testid="stButton"]:has(button:contains("Reanalyze")) button {
                background-color: #4313C8 !important;
                color: #FFFFFF !important;
                padding: 10px 24px !important;
                font-size: 14px !important;
                width: 100% !important;
                max-width: 100% !important;
            }
            
            /* Default: All buttons in main content - white background with purple text (like Browse File) */
            /* Style all buttons first, then override for sidebar and special buttons */
            .stButton > button,
            .stDownloadButton > button,
            [data-testid="stDownloadButton"] button,
            button[data-baseweb="button"],
            [data-baseweb="button"] {
                background-color: #FFFFFF !important;
                color: #4313C8 !important;
                border: 1px solid #4313C8 !important;
                border-radius: 6px !important;
                box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08), 0 1px 1px rgba(0, 0, 0, 0.04) !important;
                transition: all 0.2s ease !important;
                font-family: 'Cousine', monospace !important;
                font-weight: 400 !important;
                font-size: 14px !important;
                padding: 0.5rem 1rem !important;
                text-align: center !important;
                width: auto !important;
                min-width: auto !important;
            }
            
            .stButton > button:hover,
            .stDownloadButton > button:hover,
            [data-testid="stDownloadButton"] button:hover,
            button[data-baseweb="button"]:hover,
            [data-baseweb="button"]:hover {
                background-color: #4313C8 !important;
                color: #FFFFFF !important;
                border: 1px solid #4313C8 !important;
                box-shadow: 0 2px 6px rgba(67, 19, 200, 0.25), 0 1px 3px rgba(67, 19, 200, 0.15) !important;
            }
            
            .stButton > button:active,
            .stButton > button:focus,
            .stDownloadButton > button:active,
            .stDownloadButton > button:focus,
            [data-testid="stDownloadButton"] button:active,
            [data-testid="stDownloadButton"] button:focus,
            button[data-baseweb="button"]:active,
            button[data-baseweb="button"]:focus,
            [data-baseweb="button"]:active,
            [data-baseweb="button"]:focus {
                background-color: #4313C8 !important;
                color: #FFFFFF !important;
                border: 1px solid #4313C8 !important;
                outline: none !important;
                box-shadow: 0 1px 3px rgba(67, 19, 200, 0.3) !important;
            }
            
            /* Sidebar buttons - override with purple background (higher specificity) */
            [data-testid="stSidebar"] .stButton > button {
                background-color: #4313C8 !important;
                color: #ffffff !important;
                border: 2px solid #4313C8 !important;
                border-radius: 6px !important;
                box-shadow: none !important;
                transition: all 0.2s ease !important;
                font-family: 'Cousine', monospace !important;
                font-weight: 400 !important;
                padding: 0.5rem 1rem !important;
            }
            
            [data-testid="stSidebar"] .stButton > button:hover {
                background-color: #979DF6 !important;
                color: #ffffff !important;
                border: 2px solid #979DF6 !important;
                box-shadow: none !important;
            }
            
            [data-testid="stSidebar"] .stButton > button:active,
            [data-testid="stSidebar"] .stButton > button:focus {
                background-color: #4313C8 !important;
                color: #ffffff !important;
                border: 2px solid #4313C8 !important;
                outline: none !important;
                box-shadow: none !important;
            }
            
            /* Remove all orange/red borders and states from buttons */
            /* Note: Main button styles are defined above, this just ensures border color */
            /* Exclude sidebar and file uploader buttons, but include download buttons */
            button:not([data-testid="stSidebar"] button):not([data-testid*="FileUploader"] button),
            .stButton > button:not([data-testid="stSidebar"] .stButton > button):not([data-testid*="FileUploader"] button),
            [data-baseweb="button"]:not([data-testid="stSidebar"] [data-baseweb="button"]):not([data-testid*="FileUploader"] [data-baseweb="button"]) {
                border-color: #4313C8 !important;
                outline: none !important;
            }
            
            /* File uploader buttons - purple with white text (keep special styling) */
            [data-testid="stFileUploader"] button,
            [data-testid="stFileUploader"] [data-baseweb="button"],
            .stFileUploader button {
                background-color: #4313C8 !important;
                color: #ffffff !important;
                border: 2px solid #4313C8 !important;
                border-radius: 6px !important;
                transition: all 0.2s ease !important;
                font-family: 'Cousine', monospace !important;
                font-weight: 400 !important;
                padding: 0.5rem 1rem !important;
            }
            
            [data-testid="stFileUploader"] button:hover,
            [data-testid="stFileUploader"] [data-baseweb="button"]:hover,
            .stFileUploader button:hover {
                background-color: #979DF6 !important;
                color: #ffffff !important;
                border: 2px solid #979DF6 !important;
            }
            
            [data-testid="stFileUploader"] button:active,
            [data-testid="stFileUploader"] button:focus,
            [data-testid="stFileUploader"] [data-baseweb="button"]:active,
            .stFileUploader button:active,
            .stFileUploader button:focus {
                background-color: #4313C8 !important;
                color: #ffffff !important;
                border: 2px solid #4313C8 !important;
                outline: none !important;
            }
            
            /* Download buttons - use main content button style (white background, purple text) */
            /* They inherit from .stButton > button above, no special override needed */
            
            /* Secondary buttons - transparent with purple border */
            button[data-baseweb="button"][kind="secondary"],
            [data-baseweb="button"][kind="secondary"],
            button.kind-secondary {
                background-color: transparent !important;
                color: #4313C8 !important;
                border: 2px solid #4313C8 !important;
                border-radius: 6px !important;
                font-family: 'Cousine', monospace !important;
            }
            
            button[data-baseweb="button"][kind="secondary"]:hover,
            [data-baseweb="button"][kind="secondary"]:hover,
            button.kind-secondary:hover {
                background-color: #4313C8 !important;
                color: #ffffff !important;
            }
            
            /* Checkboxes - purple accent, remove ALL orange, make checkmark visible */
            .stCheckbox > label > span[data-baseweb="checkbox"],
            span[data-baseweb="checkbox"],
            [data-baseweb="checkbox"],
            .stCheckbox input[type="checkbox"] {
                background-color: transparent !important;
                border: 2px solid #4313C8 !important;
                border-radius: 4px !important;
                width: 18px !important;
                height: 18px !important;
            }
            
            .stCheckbox > label > span[data-baseweb="checkbox"][aria-checked="true"],
            span[data-baseweb="checkbox"][aria-checked="true"],
            [data-baseweb="checkbox"][aria-checked="true"],
            .stCheckbox input[type="checkbox"]:checked {
                background-color: #4313C8 !important;
                border-color: #4313C8 !important;
            }
            
            /* Make checkmark visible - white checkmark on purple background */
            .stCheckbox > label > span[data-baseweb="checkbox"][aria-checked="true"] svg,
            span[data-baseweb="checkbox"][aria-checked="true"] svg,
            [data-baseweb="checkbox"][aria-checked="true"] svg {
                color: #ffffff !important;
                fill: #ffffff !important;
                stroke: #ffffff !important;
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
            }
            
            /* Alternative checkmark using CSS if SVG doesn't work */
            .stCheckbox > label > span[data-baseweb="checkbox"][aria-checked="true"]::after,
            span[data-baseweb="checkbox"][aria-checked="true"]::after {
                content: "✓" !important;
                color: #ffffff !important;
                font-size: 16px !important;
                font-weight: bold !important;
                display: block !important;
                position: absolute !important;
                top: 50% !important;
                left: 50% !important;
                transform: translate(-50%, -50%) !important;
                line-height: 1 !important;
            }
            
            /* Make checkmark visible in Streamlit's internal checkboxes */
            span.st-bi[aria-checked="true"] svg,
            span[class*="st-bi"][aria-checked="true"] svg {
                color: #ffffff !important;
                fill: #ffffff !important;
                stroke: #ffffff !important;
                visibility: visible !important;
                opacity: 1 !important;
            }
            
            /* Question checkboxes - make them visible like in screen design */
            .stCheckbox {
                margin-bottom: 12px !important;
                width: 100% !important;
                max-width: 100% !important;
            }
            
            .stCheckbox > div {
                width: 100% !important;
                max-width: 100% !important;
            }
            
            .stCheckbox label {
                display: flex !important;
                flex-direction: row !important;
                align-items: flex-start !important;
                gap: 8px !important;
                width: 100% !important;
                max-width: 100% !important;
                font-family: 'Cousine', monospace !important;
                box-sizing: border-box !important;
            }
            
            .stCheckbox label > span[data-baseweb="checkbox"] {
                min-width: 18px !important;
                width: 18px !important;
                min-height: 18px !important;
                height: 18px !important;
                flex-shrink: 0 !important;
                flex-grow: 0 !important;
                display: block !important;
                visibility: visible !important;
                opacity: 1 !important;
                margin-top: 2px !important;
            }
            
            /* Fix markdown container - ensure horizontal text and proper responsive layout */
            .stCheckbox label [data-testid="stMarkdownContainer"] {
                writing-mode: horizontal-tb !important;
                text-orientation: mixed !important;
                flex: 1 1 auto !important;
                min-width: 0 !important;
                width: calc(100% - 26px) !important;
                max-width: calc(100% - 26px) !important;
                background-color: transparent !important;
                border: none !important;
                padding: 0 !important;
                overflow: visible !important;
                box-sizing: border-box !important;
            }
            
            .stCheckbox label [data-testid="stMarkdownContainer"] p {
                writing-mode: horizontal-tb !important;
                text-orientation: mixed !important;
                word-break: normal !important;
                white-space: normal !important;
                margin: 0 !important;
                padding: 0 !important;
                display: block !important;
                line-height: 1.5 !important;
                text-align: left !important;
                background-color: transparent !important;
                border: none !important;
                font-family: 'Cousine', monospace !important;
                width: 100% !important;
                max-width: 100% !important;
                overflow-wrap: break-word !important;
                word-wrap: break-word !important;
                box-sizing: border-box !important;
            }
            
            /* Remove any background or border from checkbox label elements */
            .stCheckbox label,
            .stCheckbox label *,
            .stCheckbox label div,
            .stCheckbox label span,
            .stCheckbox label p,
            .stCheckbox label [data-testid="stWidgetLabel"],
            .stCheckbox label [data-testid="stWidgetLabel"] * {
                background-color: transparent !important;
                border: none !important;
                outline: none !important;
                box-shadow: none !important;
            }
            
            /* Remove borders from markdown container specifically */
            .stCheckbox label [data-testid="stMarkdownContainer"],
            .stCheckbox label [data-testid="stMarkdownContainer"] *,
            .stCheckbox label [data-testid="stMarkdownContainer"] p,
            .stCheckbox label [data-testid="stMarkdownContainer"] div {
                border: none !important;
                outline: none !important;
                box-shadow: none !important;
                background-color: transparent !important;
            }
            
            /* Prevent text fragmentation in checkbox labels */
            .stCheckbox label [data-testid="stMarkdownContainer"] * {
                word-break: normal !important;
                word-wrap: break-word !important;
                overflow-wrap: break-word !important;
                background-color: transparent !important;
                border: none !important;
            }
            
            /* Ensure checkbox container doesn't break text */
            .stCheckbox > div,
            .stCheckbox > div > div {
                width: 100% !important;
                overflow: visible !important;
                background-color: transparent !important;
                border: none !important;
            }
            
            /* Remove borders from all checkbox-related elements */
            .stCheckbox * {
                border: none !important;
            }
            
            /* But keep the checkbox itself visible */
            .stCheckbox label > span[data-baseweb="checkbox"] {
                border: 2px solid #4313C8 !important;
            }
            
            /* Ensure all checkboxes are visible */
            input[type="checkbox"] {
                width: 18px !important;
                height: 18px !important;
                visibility: visible !important;
                opacity: 1 !important;
                display: block !important;
            }
            
            /* Remove orange from Streamlit's internal checkbox elements */
            span.st-bi,
            span[class*="st-bi"],
            span[class*="st-bj"],
            span[class*="st-bk"],
            span[class*="st-bl"],
            span[class*="st-bm"],
            span[class*="st-bn"],
            span[class*="st-bo"],
            span[class*="st-bp"],
            span[class*="st-bq"],
            span[class*="st-br"],
            span[class*="st-bs"],
            span[class*="st-bt"] {
                background-color: transparent !important;
                border: 2px solid #4313C8 !important;
            }
            
            span.st-bi[aria-checked="true"],
            span[class*="st-bi"][aria-checked="true"] {
                background-color: #4313C8 !important;
                border-color: #4313C8 !important;
            }
            
            /* Make checkmark visible in Streamlit's internal checkboxes */
            span.st-bi[aria-checked="true"]::after,
            span[class*="st-bi"][aria-checked="true"]::after {
                content: "✓" !important;
                color: #ffffff !important;
                font-size: 14px !important;
                font-weight: bold !important;
                display: block !important;
            }
            
            /* Force remove #FF4B4B (Streamlit's default orange) from ALL elements */
            * {
                --primary-color: #4313C8 !important;
            }
            
            /* Remove orange from ALL elements with #FF4B4B */
            div[style*="#FF4B4B"],
            span[style*="#FF4B4B"],
            div[style*="#ff4b4b"],
            span[style*="#ff4b4b"],
            div[style*="rgb(255, 75, 75)"],
            span[style*="rgb(255, 75, 75)"],
            *[style*="#FF4B4B"],
            *[style*="#ff4b4b"] {
                background-color: #4313C8 !important;
                border-color: #4313C8 !important;
                color: #4313C8 !important;
            }
            
            /* Remove orange from Streamlit's internal div classes */
            div[class*="st-cu"],
            div[class*="st-cl"],
            div[class*="st-f6"],
            div[class*="st-f7"],
            div[class*="st-f8"],
            div[class*="st-f9"],
            div[class*="st-fo"],
            div[class*="st-fp"],
            div[class*="st-b0"],
            div[class*="st-fq"],
            div[class*="st-fr"] {
                background-color: transparent !important;
                border-color: transparent !important;
            }
            
            /* Specifically hide the orange line element */
            div.st-cu.st-cl.st-f6.st-f7.st-f8.st-f9.st-fo.st-fp.st-b0.st-fq.st-fr {
                display: none !important;
                background-color: transparent !important;
                border-color: transparent !important;
            }
            
            /* Radio buttons - purple accent */
            .stRadio > label > div[data-baseweb="radio"] > div {
                background-color: transparent !important;
                border-color: #4313C8 !important;
            }
            
            .stRadio > label > div[data-baseweb="radio"][aria-checked="true"] > div:first-child {
                background-color: #4313C8 !important;
            }
            
            /* Number input buttons */
            .stNumberInput button {
                color: #4313C8 !important;
                background-color: transparent !important;
            }
            
            .stNumberInput button:hover {
                background-color: rgba(67, 19, 200, 0.1) !important;
            }
            
            /* Tabs - remove orange/red underline completely */
            .stTabs [data-baseweb="tab"] {
                color: #170843 !important;
            }
            
            .stTabs [aria-selected="true"],
            .stTabs [aria-selected="true"] [data-baseweb="tab"] {
                color: #4313C8 !important;
                border-bottom-color: #4313C8 !important;
            }
            
            /* Remove all orange/red Streamlit defaults from tabs */
            [data-baseweb="tab"][aria-selected="true"],
            [data-baseweb="tab-list"] [aria-selected="true"] {
                border-bottom: 2px solid #4313C8 !important;
            }
            
            /* Remove orange from tab indicators and underlines */
            .stTabs [aria-selected="true"]::after,
            .stTabs [aria-selected="true"]::before,
            [data-baseweb="tab"][aria-selected="true"]::after,
            [data-baseweb="tab"][aria-selected="true"]::before {
                background-color: #4313C8 !important;
                border-color: #4313C8 !important;
            }
            
            /* Target Streamlit's internal tab styling */
            div[class*="stTabs"] [aria-selected="true"],
            div[class*="stTabs"] [aria-selected="true"] > div {
                border-bottom-color: #4313C8 !important;
            }
            
            /* Remove any orange borders/lines from tabs */
            .stTabs * {
                border-color: transparent !important;
            }
            
            .stTabs [aria-selected="true"] * {
                border-bottom-color: #4313C8 !important;
            }
            
            /* Progress bars */
            .stProgress > div > div > div {
                background-color: #4313C8 !important;
            }
            
            /* Sliders */
            [data-baseweb="slider"] [data-baseweb="slider-track"] {
                background-color: #4313C8 !important;
            }
            
            [data-baseweb="slider"] [data-baseweb="slider-handle"] {
                background-color: #4313C8 !important;
                border-color: #4313C8 !important;
            }
            
            /* File uploader */
            [data-testid="stFileUploader"] button {
                background-color: #4313C8 !important;
                color: #ffffff !important;
            }
            
            /* Remove any orange from links */
            a:link, a:visited {
                color: #4313C8 !important;
            }
            
            a:hover {
                color: #979DF6 !important;
            }
            
            /* Expander icons */
            .streamlit-expanderHeader {
                color: #4313C8 !important;
            }
            
            /* Header - remove orange/red bar at top */
            [data-testid="stHeader"],
            [data-testid="stHeader"] > div,
            [data-testid="stHeader"] > div > div {
                background-color: transparent !important;
                border-bottom: none !important;
            }
            
            /* Remove orange from progress bars */
            [data-baseweb="progressbar"],
            [data-baseweb="progressbar"] > div,
            [data-baseweb="progressbar"] > div > div {
                background-color: #4313C8 !important;
            }
            
            /* Remove orange from any remaining Streamlit elements */
            [style*="rgb(255, 75, 75)"],
            [style*="rgb(255, 107, 107)"],
            [style*="#ff4b4b"],
            [style*="#ff6b6b"],
            [style*="rgb(255, 99, 71)"],
            [style*="#ff6347"],
            [style*="rgb(255, 140, 0)"],
            [style*="#ff8c00"] {
                color: #4313C8 !important;
                background-color: #4313C8 !important;
                border-color: #4313C8 !important;
            }
            
            /* Force remove orange backgrounds */
            div[style*="background"][style*="255, 75"],
            div[style*="background"][style*="255, 107"],
            div[style*="background"][style*="#ff4b"],
            div[style*="background"][style*="#ff6b"] {
                background-color: transparent !important;
            }
            
            /* Links */
            a {
                color: #4313C8 !important;
            }
            
            /* Footer styling - in sidebar at bottom */
            [data-testid="stSidebar"] .footer {
                text-align: center;
                padding: 15px 10px;
                font-size: 11px;
                border-top: 1px solid rgba(67, 19, 200, 0.1);
                margin-top: 20px;
            }
            
            [data-testid="stSidebar"] .footer a {
                color: #4313C8 !important;
            }
            
            [data-testid="stSidebar"] .footer img {
                height: 25px;
                max-width: 100%;
                width: auto;
                vertical-align: middle;
                margin-right: 8px;
                object-fit: contain;
            }
            
            [data-testid="stSidebar"] .footer {
                overflow: visible;
                word-wrap: break-word;
            }
            
            [data-testid="stSidebar"] .footer p {
                margin: 4px 0;
                color: #7872A7;
                font-size: 11px;
            }
            
            </style>
            """

            st.markdown(custom_css, unsafe_allow_html=True)
        except Exception as e:
            # Fallback if theme detection fails
            logger.warning(f"Could not apply custom theme: {str(e)}")

        # Initialize analyzer with default question set
        try:
            # Initialize analyzer and store in session state if not already there
            if "analyzer" not in st.session_state:
                st.session_state.analyzer = ReportAnalyzer()
            analyzer = st.session_state.analyzer  # Use the stored analyzer

        except Exception as e:
            st.error(f"Error initializing analyzer: {str(e)}")
            st.exception(e)
            return

        # Add logo to sidebar
        try:
            logo_path = Path(__file__).parent / "assets" / "open-sustainability-analyst.svg"
            if logo_path.exists():
                with open(logo_path, "rb") as f:
                    logo_data = base64.b64encode(f.read()).decode()
                    st.sidebar.markdown(
                        f"""
                        <div style="text-align: center; padding: 10px 20px 30px 20px; margin-bottom: 20px;">
                            <img src="data:image/svg+xml;base64,{logo_data}" 
                                 alt="Open Sustainability Analyst" 
                                 style="width: 90%; max-width: 200px; height: auto;" />
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        except Exception as e:
            logger.warning(f"Could not load sidebar logo: {str(e)}")

        # Create sidebar navigation using streamlit-option-menu
        st.sidebar.markdown("---")

        try:
            from streamlit_option_menu import option_menu

            # Ensure it's in sidebar context
            with st.sidebar:
                nav_page = option_menu(
                    menu_title=None,
                    options=[
                        "Upload Report",
                        "Report Analyst",
                        "All Results",
                        "Settings",
                    ],
                    icons=["house", "file-text", "bar-chart", "gear"],
                    menu_icon=None,
                    default_index=0,
                    orientation="vertical",
                    key="nav_page",
                    styles={
                        "container": {
                            "padding": "0",
                            "background-color": "transparent",
                        },
                        "icon": {"color": "#7872A7", "font-size": "20px"},
                        "nav-link": {
                            "font-family": "'Afacad', sans-serif",
                            "font-size": "16px",
                            "text-align": "left",
                            "margin": "2px 0",
                            "padding": "10px 15px",
                            "border-radius": "6px",
                            "color": "#7872A7",
                            "background-color": "transparent",
                        },
                        "nav-link-selected": {
                            "background-color": "rgba(67, 19, 200, 0.15)",
                            "color": "#4313C8",
                            "font-weight": "700",
                        },
                    },
                )
        except ImportError:
            # Fallback to regular radio if package not installed
            nav_options = ["Upload Report", "Report Analyst", "All Results", "Settings"]
            nav_page = st.sidebar.radio("", nav_options, key="nav_page", label_visibility="collapsed")

        # Show page-specific content based on navigation
        if nav_page == "Settings":
            st.title("Settings")
            st.caption("Configure application settings and integrations")

            # Open Source Modules Section
            st.header("Open Source Modules")
            st.caption("Core features available in the open source edition")

            # API Keys Configuration
            st.subheader("API Keys")
            st.caption("Enter your API keys to enable LLM features. Keys are stored in session state only and not persisted.")

            # Check if keys exist in environment but not in session state
            env_openai_key = os.getenv("OPENAI_API_KEY")
            env_google_key = os.getenv("GOOGLE_API_KEY")
            session_openai_key = st.session_state.get("api_key_openai_api_key")
            session_google_key = st.session_state.get("api_key_google_api_key")

            has_env_openai = env_openai_key and not session_openai_key
            has_env_google = env_google_key and not session_google_key

            # Get current values (from session state or environment)
            current_openai_key = APIKeyManager.get_api_key("OPENAI_API_KEY", st.session_state)
            current_google_key = APIKeyManager.get_api_key("GOOGLE_API_KEY", st.session_state)

            # OpenAI API Key section
            with st.expander(
                "OpenAI API Key",
                expanded=not has_env_openai or st.session_state.get("override_openai_key", False),
            ):
                # Show status for OpenAI key
                if has_env_openai and not st.session_state.get("override_openai_key", False):
                    st.info("API key is set from environment variable")
                    if st.button("Override with new key", key="btn_override_openai"):
                        st.session_state.override_openai_key = True
                        st.rerun()
                elif current_openai_key:
                    masked_openai = (
                        f"{current_openai_key[:8]}...{current_openai_key[-4:]}" if len(current_openai_key) > 12 else "***"
                    )
                    # Show source of key
                    if session_openai_key:
                        st.success(f"✓ API key set in session: `{masked_openai}`")
                    elif env_openai_key:
                        st.info(f"API key from environment: `{masked_openai}`")
                    else:
                        st.caption(f"Current key: `{masked_openai}`")

                # Track override state
                override_openai = st.session_state.get("override_openai_key", False)

                if not has_env_openai or override_openai:
                    # Track previous values to detect changes
                    prev_openai_key = st.session_state.get("prev_openai_key", current_openai_key)

                    # OpenAI API Key input
                    openai_key_input = st.text_input(
                        "OpenAI API Key",
                        value="",  # Never show the actual key in the input
                        type="password",
                        key="openai_api_key_input",
                        help="Enter your OpenAI API key to use GPT models. Leave empty to use existing key from environment.",
                        placeholder=("sk-..." if not current_openai_key else "Enter new key to update"),
                    )

                    # Update API key if user entered a new value (different from current)
                    if openai_key_input and openai_key_input != current_openai_key:
                        APIKeyManager.set_api_key("OPENAI_API_KEY", openai_key_input, st.session_state)
                        st.session_state.prev_openai_key = openai_key_input
                        st.session_state.override_openai_key = False  # Reset override state
                        st.success("OpenAI API key updated")
                    elif openai_key_input == "" and current_openai_key and not has_env_openai:
                        # User cleared the input - keep existing key (only if not from env)
                        st.session_state.prev_openai_key = current_openai_key
                    else:
                        st.session_state.prev_openai_key = current_openai_key

                    # Cancel override button
                    if override_openai:
                        if st.button("Cancel Override", key="cancel_override_openai"):
                            st.session_state.override_openai_key = False
                            st.rerun()

            # Google/Gemini API Key section
            with st.expander(
                "Google/Gemini API Key",
                expanded=not has_env_google or st.session_state.get("override_google_key", False),
            ):
                # Show status for Google key
                if has_env_google and not st.session_state.get("override_google_key", False):
                    st.info("API key is set from environment variable")
                    if st.button("Override with new key", key="btn_override_google"):
                        st.session_state.override_google_key = True
                        st.rerun()
                elif current_google_key:
                    masked_google = (
                        f"{current_google_key[:8]}...{current_google_key[-4:]}" if len(current_google_key) > 12 else "***"
                    )
                    st.caption(f"Current key: `{masked_google}`")

                # Track override state
                override_google = st.session_state.get("override_google_key", False)

                if not has_env_google or override_google:
                    # Track previous values to detect changes
                    prev_google_key = st.session_state.get("prev_google_key", current_google_key)

                    # Google/Gemini API Key input
                    google_key_input = st.text_input(
                        "Google/Gemini API Key",
                        value="",  # Never show the actual key in the input
                        type="password",
                        key="google_api_key_input",
                        help="Enter your Google API key to use Gemini models. Leave empty to use existing key from environment.",
                        placeholder=("Enter your Google API key" if not current_google_key else "Enter new key to update"),
                    )

                    # Update API key if user entered a new value (different from current)
                    if google_key_input and google_key_input != current_google_key:
                        APIKeyManager.set_api_key("GOOGLE_API_KEY", google_key_input, st.session_state)
                        st.session_state.prev_google_key = google_key_input
                        st.session_state.override_google_key = False  # Reset override state
                        st.success("Google API key updated")
                    elif google_key_input == "" and current_google_key and not has_env_google:
                        # User cleared the input - keep existing key (only if not from env)
                        st.session_state.prev_google_key = current_google_key
                    else:
                        st.session_state.prev_google_key = current_google_key

                    # Cancel override button
                    if override_google:
                        if st.button("Cancel Override", key="cancel_override_google"):
                            st.session_state.override_google_key = False
                            st.rerun()

                # Show clear button if key exists (only for session state keys, not env)
                if current_google_key and not has_env_google:
                    if st.button("Clear Google Key", key="clear_google_key"):
                        APIKeyManager.set_api_key("GOOGLE_API_KEY", None, st.session_state)
                        st.rerun()

            # Show clear button for OpenAI if key exists (only for session state keys, not env)
            if current_openai_key and not has_env_openai:
                if st.button("Clear OpenAI Key", key="clear_openai_key"):
                    APIKeyManager.set_api_key("OPENAI_API_KEY", None, st.session_state)
                    st.rerun()

            st.divider()

            # Database Configuration (read-only, from environment variables)
            st.subheader("Database Configuration")

            # Get database URL from environment or default
            database_url = os.getenv("DATABASE_URL")
            if database_url is None:
                # Default to SQLite
                storage_path = os.getenv("STORAGE_PATH", "./storage")
                db_path = str(Path(storage_path) / "cache" / "analysis.db")
                database_url = f"sqlite:///{db_path}"
                database_type = "SQLite"
                st.info(
                    f"**Type:** {database_type}\n\n**Path:** `{db_path}`\n\n*Configure via `STORAGE_PATH` environment variable*"
                )
            else:
                # Parse PostgreSQL URL to show connection details (masked)
                database_type = "PostgreSQL"
                try:
                    # Mask password in display
                    if "@" in database_url:
                        parts = database_url.split("@")
                        if len(parts) == 2:
                            user_pass = parts[0].split("://")[-1]
                            if ":" in user_pass:
                                user = user_pass.split(":")[0]
                                masked_url = database_url.replace(user_pass, f"{user}:***")
                            else:
                                masked_url = database_url
                        else:
                            masked_url = database_url
                    else:
                        masked_url = database_url

                    # Extract connection details for display
                    if "postgresql://" in database_url or "postgres://" in database_url:
                        url_part = database_url.split("://")[-1]
                        if "@" in url_part:
                            auth, host_db = url_part.split("@")
                            user = auth.split(":")[0] if ":" in auth else auth
                            if ":" in host_db:
                                host, port_db = host_db.split(":")
                                if "/" in port_db:
                                    port, db = port_db.split("/", 1)
                                else:
                                    port = port_db
                                    db = "?"
                            else:
                                if "/" in host_db:
                                    host, db = host_db.split("/", 1)
                                    port = "5432"
                                else:
                                    host = host_db
                                    port = "5432"
                                    db = "?"

                            st.info(
                                f"**Type:** {database_type}\n\n**Host:** `{host}`\n**Port:** `{port}`\n**Database:** `{db}`\n**User:** `{user}`\n\n*Configure via `DATABASE_URL` environment variable*"
                            )
                        else:
                            st.info(
                                f"**Type:** {database_type}\n\n**Connection:** `{masked_url}`\n\n*Configure via `DATABASE_URL` environment variable*"
                            )
                    else:
                        st.info(
                            f"**Type:** {database_type}\n\n**Connection:** `{masked_url}`\n\n*Configure via `DATABASE_URL` environment variable*"
                        )
                except Exception:
                    st.info(
                        f"**Type:** {database_type}\n\n**Connection:** `{masked_url}`\n\n*Configure via `DATABASE_URL` environment variable*"
                    )

            # Store in session state for use by DocumentAnalyzer
            st.session_state.database_url = database_url

            st.divider()
            st.divider()

            # Enterprise Modules Section
            st.header("Enterprise Modules")
            st.caption("Features available in the enterprise edition")

            # Enterprise Integration (S3+NATS)
            st.subheader("Enterprise Integration")

            # Check if USE_S3_UPLOAD is set from environment
            env_s3_upload = os.getenv("USE_S3_UPLOAD", "").lower() == "true"

            # Show env var status like API keys
            if env_s3_upload and not st.session_state.get("override_s3_upload", False):
                st.info("S3+NATS upload is enabled via `USE_S3_UPLOAD` environment variable")
                col1, col2 = st.columns([1, 3])
                with col1:
                    if st.button("Disable temporarily", key="btn_override_s3"):
                        st.session_state.override_s3_upload = True
                        st.session_state.use_s3_upload = False
                        st.rerun()
                use_s3_upload = True
            else:
                st.markdown(
                    """
                <style>
                div[data-testid="stCheckbox"] label {
                    font-family: 'Afacad', sans-serif !important;
                    white-space: nowrap !important;
                    min-width: 250px !important;
                }
                </style>
                """,
                    unsafe_allow_html=True,
                )
                use_s3_upload = st.checkbox(
                    "Enable S3+NATS Upload",
                    key="use_s3_upload",
                    help="Upload documents via S3 and process via NATS for enterprise integration",
                )
                if not env_s3_upload:
                    st.caption("*Or set `USE_S3_UPLOAD=true` in environment*")

            # Show Enterprise Mode status only if enabled AND backend is available
            if use_s3_upload and BACKEND_INTEGRATION_AVAILABLE:
                st.info("Enterprise mode enabled")

            st.divider()

            # Backend Integration (Enterprise feature)
            if BACKEND_INTEGRATION_AVAILABLE:
                config = configure_backend_integration()
                # Store config in session state for access across pages
                st.session_state.backend_config = config
            else:
                st.subheader("Backend Integration")
                st.warning("Backend integration modules not available")
                config = None
                st.session_state.backend_config = None

            st.divider()

            # File Storage Configuration (Enterprise feature)
            st.subheader("File Storage")
            st.caption("Configure where uploaded files are stored (Enterprise feature)")

            # Get database URL from session state (set above in Database Configuration)
            database_url_enterprise = st.session_state.get("database_url")
            is_postgres_enterprise = database_url_enterprise and database_url_enterprise.startswith(
                ("postgresql://", "postgres://")
            )

            # Initialize postgres_file_storage_enabled from session state or env
            if "postgres_file_storage_enabled" not in st.session_state:
                st.session_state.postgres_file_storage_enabled = (
                    os.getenv("USE_POSTGRES_FILE_STORAGE", "false").lower() == "true"
                )

            if is_postgres_enterprise:
                use_postgres_storage = st.checkbox(
                    "Store files in PostgreSQL",
                    value=st.session_state.get("postgres_file_storage_enabled", False),
                    key="use_postgres_file_storage",
                    help="Store uploaded files in PostgreSQL database (useful for Heroku deployments). Files are stored as BYTEA/BLOB. This is an enterprise feature.",
                )
                # Store in a separate key that persists across page navigation
                st.session_state.postgres_file_storage_enabled = use_postgres_storage

                if use_postgres_storage:
                    st.info("📦 Files will be stored in PostgreSQL database")
                else:
                    st.caption("Files will be stored in local temp directory")
            else:
                st.info("PostgreSQL file storage requires a PostgreSQL database. Currently using SQLite.")
                st.caption("Files are stored in local temp directory")

        # Show page-specific content based on navigation
        if nav_page == "Report Analyst":
            st.title("Report Analyst")
            st.caption("Analysis parameters tailored to your configurations")

            # Get file list for dropdown (including backend resources if enabled)
            backend_config = st.session_state.get("backend_config")
            previous_files = get_uploaded_files_history(backend_config=backend_config)

            # Determine selected file for display - check session state first
            selected_file_for_display = None
            if previous_files:
                if "previous_file" in st.session_state:
                    prev_file = st.session_state.previous_file
                    # Handle both dict (from dropdown) and string (from initial state) formats
                    if isinstance(prev_file, dict):
                        selected_file_for_display = prev_file
                    else:
                        # If it's a string, find the matching file in the list
                        for f in previous_files:
                            if f["name"] == prev_file or f.get("path") == prev_file:
                                selected_file_for_display = f
                                break

                # If no file selected yet, use first one
                if not selected_file_for_display and previous_files:
                    selected_file_for_display = previous_files[0]

            # Green PDF Display Container with integrated file selector
            if previous_files:
                # Use container with unique key for green panel styling
                # The key will be used as CSS class name prefixed with st-key-
                with st.container(key="file-display-panel"):
                    # Use columns for layout
                    icon_col, content_col = st.columns([0.1, 0.9])

                    with icon_col:
                        st.markdown(
                            """
                        <div class="pdf-icon-box">
                            <i class="material-icons">description</i>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                    with content_col:
                        # File selector inside the green container
                        selected_file_dropdown = st.selectbox(
                            "Select Report",
                            options=previous_files,
                            format_func=lambda x: x["name"],
                            key="previous_file",
                            label_visibility="collapsed",
                        )

                        # Upload date below selector
                        if selected_file_dropdown:
                            selected_uri = selected_file_dropdown.get("uri", selected_file_dropdown.get("path", ""))
                            is_backend = selected_uri.startswith("urn:report-analyst:backend:")

                            if is_backend:
                                # For backend resources, show backend info
                                from report_analyst.core.report_data_client import (
                                    ReportResource,
                                )

                                resource = ReportResource(
                                    name=selected_file_dropdown["name"],
                                    uri=selected_uri,
                                )
                                parsed = resource.parse_backend_urn()
                                if parsed:
                                    st.markdown(
                                        f'<span class="pdf-upload-date">Backend: {parsed["host"]}</span>',
                                        unsafe_allow_html=True,
                                    )
                            else:
                                # For local files, show upload date
                                file_path_str = selected_file_dropdown.get("path", "")
                                # Handle file:// URI format
                                if file_path_str.startswith("file://"):
                                    file_path_str = file_path_str.replace("file://", "")

                                file_path_display = Path(file_path_str)
                                if file_path_display.exists():
                                    import datetime

                                    mod_time = file_path_display.stat().st_mtime
                                    upload_date = datetime.datetime.fromtimestamp(mod_time).strftime("%d.%m.%Y")
                                    st.markdown(
                                        f'<span class="pdf-upload-date">Uploaded, {upload_date}</span>',
                                        unsafe_allow_html=True,
                                    )

            # Analysis Configuration section - 3 column layout
            with st.expander("Analysis Configuration", expanded=True):
                col1, col2, col3 = st.columns([1, 1, 1])

                # Left column: Question Set
                with col1:
                    selected_set = st.selectbox(
                        "Select Question Set",
                        options=list(question_sets.keys()),
                        format_func=lambda x: question_sets[x]["name"],
                        key="new_question_set",
                        index=0,  # Ensure a default is selected
                        on_change=update_analyzer_parameters,
                    )

                    # Show question set description below
                    if selected_set in question_sets:
                        st.caption(question_sets[selected_set]["description"])

                # Middle column: Processing Steps
                with col2:
                    # Processing Steps heading with help icon and tooltip
                    st.markdown(
                        """
                    <style>
                    .help-container {
                        position: relative;
                        display: inline-block;
                    }
                    .help-icon {
                        display: inline-block !important;
                        margin-left: 6px;
                        color: #4313C8 !important;
                        cursor: help;
                        font-size: 18px !important;
                        vertical-align: middle;
                        opacity: 0.7;
                        transition: opacity 0.2s;
                        font-family: 'Material Icons' !important;
                        font-weight: normal !important;
                        font-style: normal !important;
                        line-height: 1 !important;
                        letter-spacing: normal !important;
                        text-transform: none !important;
                        white-space: nowrap !important;
                        word-wrap: normal !important;
                        direction: ltr !important;
                    }
                    .help-icon:hover {
                        opacity: 1;
                    }
                    .help-tooltip {
                        visibility: hidden;
                        opacity: 0;
                        position: absolute;
                        bottom: 125%;
                        left: 50%;
                        transform: translateX(-50%);
                        background-color: #ffffff;
                        color: #170843;
                        text-align: left;
                        border-radius: 6px;
                        padding: 12px 16px;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
                        z-index: 1000;
                        width: 320px;
                        font-size: 13px;
                        line-height: 1.5;
                        font-family: 'Afacad', sans-serif;
                        border: 1px solid rgba(67, 19, 200, 0.2);
                        transition: opacity 0.2s, visibility 0.2s;
                        pointer-events: none;
                    }
                    .help-tooltip::after {
                        content: "";
                        position: absolute;
                        top: 100%;
                        left: 50%;
                        transform: translateX(-50%);
                        border: 6px solid transparent;
                        border-top-color: #ffffff;
                    }
                    .help-container:hover .help-tooltip {
                        visibility: visible;
                        opacity: 1;
                    }
                    </style>
                    <div class="help-container">
                        <strong>Processing Steps</strong>
                        <i class="material-icons help-icon">help_outline</i>
                        <div class="help-tooltip">
                            You can choose if you want to first only cut the report in pieces (Chunking), make it searchable (Embedding), map text to questions (Question Mapping), or answer the questions (Question Answering). Note: Answering questions incurs LLM API costs.
                        </div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Get step status if file is selected (check if we have a file path)
                    step_status = {
                        "chunks": False,
                        "embeddings": False,
                        "scoring": False,
                        "analysis": False,
                    }

                    # Try to get step status if a file is selected
                    if previous_files and "previous_file" in st.session_state:
                        try:
                            selected_file_obj = None
                            for f in previous_files:
                                if (
                                    f["name"] == st.session_state.previous_file
                                    or f.get("path") == st.session_state.previous_file
                                ):
                                    selected_file_obj = f
                                    break

                            if selected_file_obj:
                                selected_uri = selected_file_obj.get("uri", selected_file_obj.get("path", ""))
                                is_backend = selected_uri.startswith("urn:report-analyst:backend:")

                                if is_backend:
                                    # For backend resources, use URN for step status check
                                    try:
                                        step_status = analyzer.analyzer.check_step_completion(selected_uri)
                                    except Exception as e:
                                        logger.warning(f"Error checking step completion: {str(e)}")
                                else:
                                    file_path_for_status = Path(selected_file_obj["path"])
                                    if file_path_for_status.exists():
                                        try:
                                            step_status = analyzer.analyzer.check_step_completion(str(file_path_for_status))
                                        except Exception as e:
                                            logger.warning(f"Error checking step completion: {str(e)}")
                        except Exception as e:
                            logger.warning(f"Error getting step status: {str(e)}")

                    # Define processing steps with shorter labels
                    step_options = ["Chunk", "Embed", "Map", "Answer"]

                    # Full step names for display
                    step_full_names = {
                        "Chunk": "Chunking",
                        "Embed": "Embedding",
                        "Map": "Question Mapping",
                        "Answer": "Question Answering",
                    }

                    # Initialize selected step in session state if not exists
                    if "processing_steps_slider" not in st.session_state:
                        st.session_state.processing_steps_slider = "Answer"

                    # Add CSS to make slider labels more visible
                    st.markdown(
                        """
                    <style>
                    /* Style select slider labels to be more visible */
                    div[data-testid="stSlider"] label,
                    div[data-testid="stSlider"] p {
                        color: #170843 !important;
                        font-weight: 500 !important;
                        font-size: 14px !important;
                        font-family: 'Afacad', sans-serif !important;
                    }
                    
                    /* Make all slider tick labels visible */
                    [data-baseweb="slider"] [role="slider"] ~ div,
                    [data-baseweb="slider"] div[role="slider"] ~ div,
                    [data-baseweb="slider"] div[role="slider"] + div,
                    [data-baseweb="slider"] > div > div > div {
                        color: #170843 !important;
                        font-size: 12px !important;
                        font-family: 'Afacad', sans-serif !important;
                        font-weight: 500 !important;
                        opacity: 1 !important;
                        visibility: visible !important;
                    }
                    </style>
                    """,
                        unsafe_allow_html=True,
                    )

                    # Create select slider for step selection
                    selected_step = st.select_slider(
                        "Select processing steps",
                        options=step_options,
                        value=st.session_state.processing_steps_slider,
                        key="processing_steps_slider",
                        help="Select how many processing steps to execute",
                        label_visibility="collapsed",
                    )

                    # Display all step labels below the slider
                    step_cols = st.columns(4)
                    selected_index = (
                        step_options.index(selected_step) if selected_step in step_options else len(step_options) - 1
                    )

                    # Map step names to status keys
                    step_status_map = {
                        "Chunk": step_status.get("chunks", False),
                        "Embed": step_status.get("embeddings", False),
                        "Map": step_status.get("scoring", False),
                        "Answer": step_status.get("analysis", False),
                    }

                    # Check if there's any stored data for this file
                    # Reuse the file_path_for_status from the step_status check above
                    has_stored_data = False
                    if "analyzer" in st.session_state:
                        try:
                            # Use file_path_for_status if it was set in the step_status check above
                            file_to_check = None
                            if previous_files and "previous_file" in st.session_state:
                                # Try to find the selected file
                                selected_file_obj = None
                                prev_file = st.session_state.previous_file

                                # Handle both dict and string formats
                                if isinstance(prev_file, dict):
                                    for f in previous_files:
                                        if f["name"] == prev_file.get("name") or f.get("path") == prev_file.get("path"):
                                            selected_file_obj = f
                                            break
                                else:
                                    for f in previous_files:
                                        if f["name"] == prev_file or f.get("path") == prev_file:
                                            selected_file_obj = f
                                            break

                                if selected_file_obj:
                                    selected_uri = selected_file_obj.get("uri", selected_file_obj.get("path", ""))
                                    is_backend = selected_uri.startswith("urn:report-analyst:backend:")
                                    if is_backend:
                                        file_to_check = None  # Backend resources don't have local file paths
                                    else:
                                        file_to_check = Path(selected_file_obj["path"])

                            # If we have a file path, check for stored data
                            if file_to_check and file_to_check.exists():
                                cache_entries = st.session_state.analyzer.analyzer.cache_manager.check_cache_status(
                                    str(file_to_check)
                                )
                                # check_cache_status returns a list of tuples, so check if it has any entries
                                has_stored_data = bool(cache_entries) and len(cache_entries) > 0
                        except Exception as e:
                            logger.debug(f"Error checking stored data: {str(e)}")
                            has_stored_data = False

                    for idx, step_short in enumerate(step_options):
                        with step_cols[idx]:
                            step_full = step_full_names[step_short]
                            is_selected = idx <= selected_index
                            is_complete = step_status_map.get(step_short, False)

                            # Show checkmark if complete, circle if incomplete
                            indicator = "✓" if is_complete else "○"

                            # Visual styling for selected steps
                            if is_selected:
                                highlight_style = (
                                    "background-color: rgba(192, 196, 250, 0.1); border: 1px solid #4313C8; color: #4313C8;"
                                )
                            else:
                                highlight_style = "background-color: rgba(192, 196, 250, 0.05); border: 1px solid rgba(67, 19, 200, 0.3); color: #718096;"

                            # Add status badge next to Chunking step - always show
                            status_badge = ""
                            if step_short == "Chunk":
                                badge_text = "Stored" if has_stored_data else "New"
                                badge_bg = "rgba(192, 196, 250, 0.3)" if has_stored_data else "rgba(192, 196, 250, 0.15)"
                                status_badge = f"<span style=\"background-color: {badge_bg}; color: #4313C8; border: 1px solid #4313C8; border-radius: 12px; padding: 2px 8px; font-size: 9px; margin-left: 6px; font-family: 'Cousine', monospace; display: inline-block;\">{badge_text}</span>"

                            st.markdown(
                                f"""
                            <div style="{highlight_style} border-radius: 8px; padding: 0.5rem; text-align: center; font-size: 11px; font-family: 'Afacad', sans-serif;">
                                <span>{indicator} {step_full}</span>{status_badge}
                            </div>
                            """,
                                unsafe_allow_html=True,
                            )

                # Right column: Advanced Parameters
                with col3:
                    st.markdown("**Advanced Parameters**")

                    # Use 2 columns for Advanced Parameters to make it more compact
                    adv_col1, adv_col2 = st.columns(2)

                    with adv_col1:
                        new_top_k = st.number_input(
                            "Top K",
                            min_value=1,
                            max_value=20,
                            value=5,  # Default value
                            key="new_top_k",
                            on_change=update_analyzer_parameters,
                        )

                        new_chunk_size = st.number_input(
                            "Chunk Size",
                            min_value=100,
                            max_value=2000,
                            value=500,  # Default value
                            key="new_chunk_size",
                            on_change=update_analyzer_parameters,
                        )

                        new_overlap = st.number_input(
                            "Overlap",
                            min_value=0,
                            max_value=100,
                            value=20,  # Default value
                            key="new_overlap",
                            on_change=update_analyzer_parameters,
                        )

                    with adv_col2:
                        new_llm_model = st.selectbox(
                            "LLM Model",
                            options=LLM_MODELS,
                            index=0,  # Ensure a default is selected
                            key="new_llm_model",
                            on_change=update_analyzer_parameters,
                        )

                        new_llm_scoring = st.checkbox(
                            "LLM Scoring",
                            value=False,
                            key="new_llm_scoring",
                            on_change=update_analyzer_parameters,
                        )

                        new_batch_scoring = st.checkbox(
                            "Batch Scoring",
                            value=True,
                            key="new_batch_scoring",
                            disabled=not st.session_state.get("new_llm_scoring", False),
                            help="Batch scoring only applies when LLM scoring is enabled.",
                        )

                # Update analyzer's question set
                analyzer.analyzer.update_question_set(selected_set)

                # Clear results if question set changed
                if "last_question_set" not in st.session_state or st.session_state.last_question_set != selected_set:
                    if "results" in st.session_state:
                        del st.session_state.results
                    st.session_state.last_question_set = selected_set

            # Report Analyst page content - questions and analysis
            if previous_files and selected_file_dropdown:
                # Check if this is a backend resource (URN) or local file
                selected_uri = selected_file_dropdown.get("uri", selected_file_dropdown.get("path", ""))
                is_backend_resource = selected_uri.startswith("urn:report-analyst:backend:")

                if is_backend_resource:
                    # Handle backend resource
                    from report_analyst.core.report_data_client import (
                        get_chunks_for_backend_resource,
                    )

                    backend_config = st.session_state.get("backend_config")
                    backend_configs = (
                        [backend_config]
                        if backend_config and hasattr(backend_config, "use_backend") and backend_config.use_backend
                        else []
                    )

                    # Get chunks from backend
                    chunks = get_chunks_for_backend_resource(selected_uri, backend_configs)
                    if chunks:
                        # Store chunks in session state for analysis
                        st.session_state.backend_chunks = chunks
                        st.session_state.backend_resource_uri = selected_uri
                        # Use URN as file_path for cache (maintains compatibility with cache_manager)
                        file_path = selected_uri  # Store as string, not Path
                    else:
                        st.error("Failed to retrieve chunks from backend resource")
                        chunks = None
                        file_path = None
                else:
                    # Handle local file - maintain backwards compatibility
                    # Use absolute path string as before (existing behavior for SQLite cache)
                    file_path_str = selected_file_dropdown.get("path", "")

                    # Handle file:// URI format - extract actual path
                    if file_path_str.startswith("file://"):
                        file_path_str = file_path_str.replace("file://", "")

                    if file_path_str:
                        file_path_obj = Path(file_path_str)
                        if file_path_obj.exists():
                            # Use absolute path string (maintains backwards compatibility with cache)
                            file_path = str(file_path_obj.resolve())
                            st.session_state.backend_chunks = None
                            st.session_state.backend_resource_uri = None
                        else:
                            # File path doesn't exist - log warning but don't set file_path to None yet
                            # This allows the error message to show the actual path
                            file_path = file_path_str
                            logger.warning(f"File path does not exist: {file_path_str}")
                    else:
                        # No path found in selected file
                        file_path = None
                        logger.warning(f"No path found in selected file: {selected_file_dropdown}")

                # Continue with analysis if we have a valid file path or chunks
                if (not is_backend_resource and file_path and Path(file_path).exists()) or (is_backend_resource and chunks):
                    # Load questions and handle selection
                    question_set_data = analyzer.load_question_set(st.session_state.new_question_set)
                    questions = question_set_data["questions"]

                    st.markdown("<br>", unsafe_allow_html=True)

                    # Add question selection UI - styled table format
                    st.subheader("Select Questions")

                    table_key = f"questions_table_{st.session_state.new_question_set}"
                    select_all_key = f"select_all_{st.session_state.new_question_set}"

                    # Select All button - styled purple, smaller, below heading
                    select_all_clicked = st.button("Select All", key=select_all_key, type="primary")

                    # Handle select all button click - toggle state
                    if select_all_clicked:
                        # Toggle the select all state
                        toggle_key = f"select_all_state_{st.session_state.new_question_set}"
                        if toggle_key not in st.session_state:
                            st.session_state[toggle_key] = False
                        st.session_state[toggle_key] = not st.session_state[toggle_key]

                    # Get current select all state
                    toggle_key = f"select_all_state_{st.session_state.new_question_set}"
                    select_all = st.session_state.get(toggle_key, False)

                    # If select all is active, update all checkboxes
                    if select_all:
                        # Set all questions to selected
                        questions_data = []
                        for q_id, q_data in questions.items():
                            questions_data.append(
                                {
                                    "Select": True,
                                    "QID": q_id,
                                    "QUESTION": q_data["text"],
                                }
                            )
                        questions_df = pd.DataFrame(questions_data)
                    else:
                        # Build dataframe - let widget manage its own state, don't sync until analyze is clicked
                        # Check if widget state exists and has the correct structure
                        if table_key in st.session_state:
                            widget_df = st.session_state[table_key]
                            # Check if widget_df is a DataFrame with the expected columns
                            if (
                                isinstance(widget_df, pd.DataFrame)
                                and "QID" in widget_df.columns
                                and "Select" in widget_df.columns
                            ):
                                # Widget has valid state - use it directly
                                questions_data = []
                                for q_id, q_data in questions.items():
                                    if q_id in widget_df["QID"].values:
                                        is_selected = bool(widget_df[widget_df["QID"] == q_id]["Select"].iloc[0])
                                    else:
                                        # Question not in widget state yet, default to False
                                        is_selected = False

                                    questions_data.append(
                                        {
                                            "Select": is_selected,
                                            "QID": q_id,
                                            "QUESTION": q_data["text"],
                                        }
                                    )
                                questions_df = pd.DataFrame(questions_data)
                            else:
                                # Widget state exists but has wrong structure - rebuild from scratch
                                questions_data = []
                                for q_id, q_data in questions.items():
                                    questions_data.append(
                                        {
                                            "Select": False,
                                            "QID": q_id,
                                            "QUESTION": q_data["text"],
                                        }
                                    )
                                questions_df = pd.DataFrame(questions_data)
                        else:
                            # First time - build from scratch (don't use session state to avoid sync issues)
                            questions_data = []
                            for q_id, q_data in questions.items():
                                questions_data.append(
                                    {
                                        "Select": False,
                                        "QID": q_id,
                                        "QUESTION": q_data["text"],
                                    }
                                )
                            questions_df = pd.DataFrame(questions_data)

                    # Display as editable table - widget manages its own state
                    edited_df = st.data_editor(
                        questions_df,
                        column_config={
                            "Select": st.column_config.CheckboxColumn("Select", width=70),
                            "QID": st.column_config.TextColumn("QID", disabled=True, width=120),
                            "QUESTION": st.column_config.TextColumn("Question", disabled=True),
                        },
                        hide_index=True,
                        use_container_width=True,
                        key=table_key,
                        num_rows="fixed",
                        column_order=["Select", "QID", "QUESTION"],
                    )

                    # Don't sync to session state here - only sync when analyze button is clicked

                    # Analysis button and results
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        analyze_clicked = st.button("Analyze Selected Questions", key="analyze_button")
                    with col2:
                        reanalyze_clicked = st.button("Reanalyze", key="reanalyze_button")

                    if analyze_clicked or reanalyze_clicked:
                        # NOW sync the selection state from the widget
                        # Get selected questions from the edited dataframe
                        selected_questions = edited_df[edited_df["Select"] == True]["QID"].tolist()

                        # Update session state for individual question checkboxes (for backward compatibility)
                        for q_id in questions.keys():
                            is_selected = q_id in selected_questions
                            st.session_state[f"individual_question_{q_id}"] = is_selected

                        if not selected_questions:
                            st.warning("Please select at least one question to analyze.")
                        else:
                            try:
                                # Set force_recompute based on which button was clicked
                                st.session_state.force_recompute = reanalyze_clicked

                                # Get current configuration
                                config = {
                                    "chunk_size": st.session_state.new_chunk_size,
                                    "chunk_overlap": st.session_state.new_overlap,
                                    "top_k": st.session_state.new_top_k,
                                    "model": st.session_state.new_llm_model,
                                    "question_set": st.session_state.new_question_set,
                                }

                                # Initialize progress display
                                progress_text = st.empty()

                                # Check if this is a backend resource
                                is_backend = st.session_state.get("backend_chunks") is not None
                                backend_uri = st.session_state.get("backend_resource_uri")

                                # Use URN as file_path for backend resources, absolute path string for local files
                                # This maintains backwards compatibility with SQLite cache
                                if is_backend and backend_uri:
                                    analysis_file_path = backend_uri  # URN string
                                else:
                                    # Local file - ensure it's absolute path string (backwards compatible)
                                    analysis_file_path = str(Path(file_path).resolve()) if file_path else file_path

                                if reanalyze_clicked:
                                    # For reanalysis, skip cache check and analyze all selected questions
                                    progress_text.info(f"Reanalyzing {len(selected_questions)} questions...")
                                    asyncio.run(
                                        run_analysis(
                                            analyzer,
                                            file_path=analysis_file_path,
                                            selected_questions=selected_questions,
                                            progress_text=progress_text,
                                        )
                                    )
                                else:
                                    # For normal analysis, check cache first
                                    cached_results = analyzer.analyzer.cache_manager.get_analysis(
                                        file_path=analysis_file_path,
                                        config=config,
                                        question_ids=selected_questions,
                                    )

                                    if cached_results:
                                        # Process cached results
                                        for (
                                            question_id,
                                            result,
                                        ) in cached_results.items():
                                            st.session_state.results["answers"][question_id] = result

                                        # Generate file key for display
                                        file_key = generate_file_key(analysis_file_path, st)

                                        # Update display
                                        analysis_df, chunks_df = create_analysis_dataframes(
                                            st.session_state.results["answers"],
                                            file_key,
                                        )
                                        st.session_state.analysis_df = analysis_df
                                        st.session_state.chunks_df = chunks_df
                                        st.session_state.analysis_complete = True
                                    else:
                                        # Run analysis for uncached questions
                                        progress_text.info(f"Processing {len(selected_questions)} questions...")

                                        try:
                                            # Run analysis for uncached questions
                                            asyncio.run(
                                                analyze_document_and_display(
                                                    analyzer,
                                                    file_path=analysis_file_path,  # Use URN for backend, file path for local
                                                    questions=questions,
                                                    selected_questions=selected_questions,
                                                    use_llm_scoring=st.session_state.new_llm_scoring,
                                                    single_call=st.session_state.new_batch_scoring,
                                                )
                                            )

                                            progress_text.success("Analysis complete!")

                                        except Exception as e:
                                            st.error(f"Error during analysis: {str(e)}")
                                            st.exception(e)

                                    # Get final results
                                    all_results = analyzer.analyzer.cache_manager.get_analysis(
                                        file_path=str(file_path),
                                        config=config,
                                        question_ids=selected_questions,
                                    )

                                    # Process all results into dataframes
                                    if all_results:
                                        analysis_df, chunks_df = create_analysis_dataframes(all_results)
                                        file_key = Path(file_path).stem
                                        display_analysis_results(analysis_df, chunks_df, file_key)
                                        progress_text.success(f"✓ Analysis complete for {len(selected_questions)} questions")
                                    else:
                                        progress_text.error("No results found after analysis")

                            except Exception as e:
                                logger.error(
                                    f"Error during analysis: {str(e)}",
                                    exc_info=True,
                                )
                                st.error(f"Error during analysis: {str(e)}")
                else:
                    # Show helpful error message
                    if file_path is None:
                        st.error("File not found: No file path available. Please select a valid file.")
                    else:
                        st.error(f"File not found: {file_path}. Please ensure the file exists.")
            else:
                st.info("No previously analyzed reports found")

        # Upload Report page
        elif nav_page == "Upload Report":
            # Check if S3+NATS enterprise integration is enabled
            # Respect override_s3_upload if user has temporarily disabled it
            if st.session_state.get("override_s3_upload", False):
                use_s3_upload = False
            else:
                use_s3_upload = (
                    st.session_state.get("use_s3_upload", False) or os.getenv("USE_S3_UPLOAD", "false").lower() == "true"
                )

            # Initialize backend integration with S3+NATS enabled if needed
            if use_s3_upload and BACKEND_INTEGRATION_AVAILABLE:
                if "backend_config" not in st.session_state or not getattr(
                    st.session_state.get("backend_config"), "use_backend", False
                ):
                    # Create a custom config for S3+NATS enterprise mode
                    from report_analyst_search_backend.config import BackendConfig

                    st.session_state.backend_config = BackendConfig(
                        use_backend=True,  # Enable backend integration
                        backend_url=os.getenv("BACKEND_URL", "http://localhost:8000"),
                        use_centralized_llm=True,  # Enable for enterprise mode
                        use_data_lake=False,
                        use_full_backend_analysis=False,
                        nats_url=os.getenv("NATS_URL", "nats://localhost:4222"),
                        owner="report-analyst",
                        deployment_type="enterprise",
                        experiment_name="S3+NATS Upload",
                    )
                    st.session_state.flow_orchestrator = create_flow_orchestrator(st.session_state.backend_config)

            # Unified upload page styling (shows for both enterprise and regular mode)
            st.markdown(
                """
            <style>
            .upload-icon-box {
                background-color: rgba(192, 196, 250, 0.1);
                border-radius: 12px;
                padding: 50px 40px;
                margin: 0 auto 40px auto;
                max-width: 300px;
                display: inline-block;
            }
            .upload-icon-box i.material-icons {
                font-family: 'Material Icons' !important;
                font-weight: normal !important;
                font-style: normal !important;
                font-size: 80px !important;
                line-height: 1 !important;
                letter-spacing: normal !important;
                text-transform: none !important;
                display: block !important;
                white-space: nowrap !important;
                word-wrap: normal !important;
                direction: ltr !important;
                -webkit-font-feature-settings: 'liga' !important;
                -webkit-font-smoothing: antialiased !important;
                color: #4313C8 !important;
            }
            </style>
            <div style="text-align: center; padding: 60px 20px 40px 20px;">
                <div class="upload-icon-box">
                    <i class="material-icons">cloud_upload</i>
                </div>
                <h1 style="color: #4313C8; font-family: 'Afacad', sans-serif; font-weight: 700; margin: 0 0 20px 0; font-size: 32px;">Upload your Sustainability Report</h1>
                <p style="color: #718096; font-family: 'Cousine', monospace; font-size: 14px; margin: 0 0 40px 0; line-height: 1.5;">Drag and drop your file here, or click to browse.<br>PDF only, limited to 200MB</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Style the file uploader (works for both modes)
            st.markdown(
                """
            <style>
            [data-testid="stFileUploader"] {
                text-align: center;
                margin: 0 auto;
                max-width: 600px;
            }
            [data-testid="stFileUploader"] > div:first-child {
                border: 2px dashed #4313C8 !important;
                border-radius: 8px !important;
                background-color: #FFFFFF !important;
                padding: 40px !important;
            }
            [data-testid="stFileUploader"] [data-baseweb="file-uploader"] {
                border: none !important;
                background-color: transparent !important;
            }
            [data-testid="stFileUploader"] button {
                background-color: #4313C8 !important;
                color: #FFFFFF !important;
                border: none !important;
                border-radius: 6px !important;
                font-family: 'Cousine', monospace !important;
                padding: 10px 24px !important;
                font-weight: 400 !important;
                font-size: 14px !important;
                margin: 0 auto !important;
                display: block !important;
                cursor: pointer !important;
                transition: all 0.2s ease !important;
            }
            [data-testid="stFileUploader"] button:hover {
                background-color: #979DF6 !important;
            }
            [data-testid="stFileUploader"] label {
                font-family: 'Afacad', sans-serif !important;
                color: #4313C8 !important;
                font-weight: 600 !important;
                margin-bottom: 10px !important;
            }
            </style>
            """,
                unsafe_allow_html=True,
            )

            # Try to import JSON Schema form component (enterprise feature)
            try:
                # Use the proper Streamlit custom component
                import json

                from report_analyst_enterprise.components.streamlit_component.backend import (
                    json_schema_form,
                )

                # Path is already imported at the top of the file

                JSON_SCHEMA_FORM_AVAILABLE = True

                # Load PDF upload schema
                schema_path = (
                    Path(__file__).parent.parent
                    / "report_analyst_enterprise"
                    / "components"
                    / "schemas"
                    / "pdf_upload_schema.json"
                )
                ui_schema_path = (
                    Path(__file__).parent.parent
                    / "report_analyst_enterprise"
                    / "components"
                    / "schemas"
                    / "pdf_upload_ui_schema.json"
                )

                if schema_path.exists() and ui_schema_path.exists():
                    with open(schema_path) as f:
                        pdf_upload_schema = json.load(f)
                    with open(ui_schema_path) as f:
                        pdf_upload_ui_schema = json.load(f)
                else:
                    JSON_SCHEMA_FORM_AVAILABLE = False
                    pdf_upload_schema = None
                    pdf_upload_ui_schema = None
            except ImportError:
                JSON_SCHEMA_FORM_AVAILABLE = False
                pdf_upload_schema = None
                pdf_upload_ui_schema = None

            # File upload with optional metadata form
            uploaded_file = st.file_uploader(
                "Choose a PDF file",
                type="pdf",
                key="file_uploader",
                help="Limit 200MB per file • PDF",
            )

            # Show metadata form if JSON Schema form is available
            pdf_metadata = None
            company_metadata = None

            if JSON_SCHEMA_FORM_AVAILABLE:
                # ESRS Company Information Form
                esrs_schema_path = (
                    Path(__file__).parent.parent
                    / "report_analyst_enterprise"
                    / "components"
                    / "schemas"
                    / "esrs_company_schema.json"
                )
                esrs_ui_schema_path = (
                    Path(__file__).parent.parent
                    / "report_analyst_enterprise"
                    / "components"
                    / "schemas"
                    / "esrs_company_ui_schema.json"
                )

                if esrs_schema_path.exists() and esrs_ui_schema_path.exists():
                    with open(esrs_schema_path) as f:
                        esrs_company_schema = json.load(f)
                    with open(esrs_ui_schema_path) as f:
                        esrs_company_ui_schema = json.load(f)

                    with st.expander("ESRS Company Information", expanded=True):
                        st.caption("Enter company data aligned with ESRS XBRL taxonomy requirements")
                        company_metadata = json_schema_form(
                            schema=esrs_company_schema,
                            ui_schema=esrs_company_ui_schema,
                            key="esrs_company_form",
                            height=700,
                        )
                        if company_metadata and company_metadata.get("type") == "submit":
                            st.success("Company information saved!")
                            st.session_state.esrs_company_metadata = company_metadata.get("formData", company_metadata)

                # Basic PDF metadata form
                if pdf_upload_schema:
                    with st.expander("Add Document Metadata (Optional)", expanded=False):
                        st.caption("Add metadata like category, tags, and description to help organize your documents.")
                        pdf_metadata = json_schema_form(
                            schema=pdf_upload_schema,
                            ui_schema=pdf_upload_ui_schema,
                            key="pdf_metadata_form",
                            height=500,
                        )
                        if pdf_metadata:
                            st.success("Metadata saved!")
                            # Store in session state for use after upload
                            st.session_state.pdf_metadata = pdf_metadata

            if uploaded_file:
                # Handle upload based on mode
                if use_s3_upload and BACKEND_INTEGRATION_AVAILABLE:
                    # Use S3+NATS enterprise flow
                    with st.spinner("Uploading to S3 and triggering backend processing..."):
                        try:
                            # Debug: Check if backend_service exists
                            orchestrator = st.session_state.get("flow_orchestrator")
                            backend_service = getattr(orchestrator, "backend_service", None) if orchestrator else None

                            logger.info(f"[ENTERPRISE] Debug - orchestrator: {orchestrator is not None}")
                            logger.info(f"[ENTERPRISE] Debug - backend_service: {backend_service is not None}")

                            if not backend_service:
                                raise Exception("Backend service not initialized properly")

                            # Get file bytes
                            file_bytes = uploaded_file.getbuffer()

                            # Process via S3+NATS flow
                            result = asyncio.run(backend_service.upload_pdf(file_bytes, uploaded_file.name))

                            if result:
                                st.success(f"File uploaded via S3+NATS: {uploaded_file.name}")
                                st.info(f"Document ID: {result}")
                                st.session_state.current_file = result
                                st.session_state.uploaded_file = uploaded_file
                                st.session_state.analysis_complete = False
                                st.session_state.analysis_triggered = False
                                if "results" in st.session_state:
                                    del st.session_state.results
                                st.rerun()
                            else:
                                st.error("Failed to upload file via S3+NATS")
                        except Exception as e:
                            logger.error(
                                f"[ENTERPRISE] Error in S3+NATS upload: {e}",
                                exc_info=True,
                            )
                            st.error(f"Error uploading via S3+NATS: {str(e)}")
                            st.info("Falling back to local processing...")
                            # Fall through to local processing
                            use_s3_upload = False

                # Local processing (when enterprise mode is off or failed)
                if not use_s3_upload or not BACKEND_INTEGRATION_AVAILABLE:
                    file_path = save_uploaded_file(uploaded_file)
                    logger.info(f"[UPLOAD] Saved uploaded file: {uploaded_file.name} at {file_path}")
                    if file_path and file_path != st.session_state.get("current_file"):
                        st.session_state.current_file = file_path
                        st.session_state.uploaded_file = uploaded_file
                        st.session_state.analysis_complete = False
                        st.session_state.analysis_triggered = False
                        if "results" in st.session_state:
                            del st.session_state.results
                        logger.info(f"[UPLOAD] Added file to session state: {uploaded_file.name}")
                        st.success(f"File uploaded successfully: {uploaded_file.name}")
                        logger.info(f"[UPLOAD] Displaying cache selector for file: {file_path}")
                        # Removed display_cache_selector - stored data status now shown as pill next to Chunking step
                        if not st.session_state.get("file_processed"):
                            st.session_state.file_processed = True
                            st.rerun()

        # All Results page
        elif nav_page == "All Results":
            st.header("View All Results")
            st.write("View and export consolidated results for all analyzed reports")

            # Initialize selected_set from session state if available
            if "consolidated_set" not in st.session_state:
                st.session_state.consolidated_set = list(question_sets.keys())[0] if question_sets else None

            # 1. Question set and report selectors side by side (green containers)
            col1, col2 = st.columns([1, 1])

            with col1:
                # Question set selector in green container
                with st.container(key="question-set-display-panel"):
                    icon_col, content_col = st.columns([0.1, 0.9])

                    with icon_col:
                        st.markdown(
                            """
                        <div class="pdf-icon-box">
                            <i class="material-icons">help_outline</i>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                    with content_col:
                        # Question set selector
                        selected_set = st.selectbox(
                            "Select Question Set",
                            options=list(question_sets.keys()),
                            format_func=lambda x: question_sets[x]["name"],
                            key="consolidated_set",
                            label_visibility="collapsed",
                        )

                        # Show question set description
                        if selected_set and selected_set in question_sets:
                            st.caption(question_sets[selected_set]["description"])

            # Get file configs if question set is selected
            file_configs = {}
            if selected_set:
                # Create mapping from question set names to database identifiers
                question_set_mapping = {
                    "tcfd": "tcfd",
                    "s4m": "s4m",
                    "lucia": "lucia",
                    "everest": "ev",
                }

                # Get the database identifier for the selected question set
                db_question_set = question_set_mapping.get(selected_set, selected_set)

                # Get all available cache configurations
                cache_configs = analyzer.analyzer.cache_manager.check_cache_status()

                # Group configurations by file for the selected question set
                if cache_configs:
                    for config in cache_configs:
                        if len(config) == 6:
                            file_path, chunk_size, chunk_overlap, top_k, model, qs = config
                            if qs == db_question_set:
                                if file_path not in file_configs:
                                    file_configs[file_path] = []
                                file_configs[file_path].append(
                                    {
                                        "chunk_size": chunk_size,
                                        "chunk_overlap": chunk_overlap,
                                        "top_k": top_k,
                                        "model": model,
                                        "question_set": qs,
                                    }
                                )

                with col2:
                    # Report selector in green container
                    if file_configs:
                        with st.container(key="file-display-panel"):
                            icon_col, content_col = st.columns([0.1, 0.9])

                            with icon_col:
                                st.markdown(
                                    """
                                <div class="pdf-icon-box">
                                    <i class="material-icons">description</i>
                                </div>
                                """,
                                    unsafe_allow_html=True,
                                )

                            with content_col:
                                selected_file_path = st.selectbox(
                                    "Select Report",
                                    options=list(file_configs.keys()),
                                    format_func=lambda x: Path(x).name,
                                    key="consolidated_file",
                                    label_visibility="collapsed",
                                )

                                # Show file info
                                if selected_file_path:
                                    file_path_str = str(selected_file_path)
                                    if not file_path_str.startswith("file://"):
                                        file_path_display = Path(file_path_str)
                                        if file_path_display.exists():
                                            import datetime

                                            mod_time = file_path_display.stat().st_mtime
                                            upload_date = datetime.datetime.fromtimestamp(mod_time).strftime("%d.%m.%Y")
                                            st.markdown(
                                                f'<span class="pdf-upload-date">Uploaded, {upload_date}</span>',
                                                unsafe_allow_html=True,
                                            )
                    else:
                        st.warning("No stored results found for the selected question set")
                        selected_file_path = None

                # 2. Configuration selector - horizontal styled cards
                if selected_file_path and file_configs:
                    configs = file_configs[selected_file_path]

                    st.markdown("##### Configuration")

                    # Create config cards using columns
                    num_configs = len(configs)
                    if num_configs > 0:
                        # Initialize selected config from session state
                        if "selected_config_idx" not in st.session_state:
                            st.session_state.selected_config_idx = 0

                        # Ensure index is valid
                        if st.session_state.selected_config_idx >= num_configs:
                            st.session_state.selected_config_idx = 0

                        # Create fixed-width columns
                        col_spec = [1] * num_configs
                        remaining_space = max(0, 4 - num_configs)
                        if remaining_space > 0:
                            col_spec.append(remaining_space)

                        all_cols = st.columns(col_spec)
                        config_cols = all_cols[:num_configs]

                        for idx, config in enumerate(configs):
                            with config_cols[idx]:
                                # Format model name nicely
                                model_name = config["model"]
                                if "gpt-4o-mini" in model_name:
                                    model_display = "GPT-4o Mini"
                                elif "gpt-4o" in model_name:
                                    model_display = "GPT-4o"
                                elif "gpt-4" in model_name:
                                    model_display = "GPT-4"
                                elif "gemini" in model_name.lower():
                                    model_display = "Gemini"
                                else:
                                    model_display = model_name

                                # Check if this config is selected
                                is_selected = idx == st.session_state.selected_config_idx

                                # Create clickable card
                                clicked = card(
                                    title=model_display,
                                    text=f"Chunk: {config['chunk_size']} · Overlap: {config['chunk_overlap']} · Top-K: {config['top_k']}",
                                    key=f"config_card_{idx}",
                                    styles={
                                        "card": {
                                            "width": "100%",
                                            "height": "85px",
                                            "border-radius": "10px",
                                            "box-shadow": (
                                                "0 2px 8px rgba(0,0,0,0.08)"
                                                if not is_selected
                                                else "0 4px 16px rgba(67,19,200,0.25)"
                                            ),
                                            "background-color": "#4313C8" if is_selected else "#FFFFFF",
                                            "border": "2px solid #4313C8" if is_selected else "1px solid #E5E7EB",
                                            "padding": "10px",
                                            "margin": "0",
                                        },
                                        "title": {
                                            "font-size": "15px",
                                            "font-weight": "600",
                                            "color": "white" if is_selected else "#1F2937",
                                            "font-family": "'Afacad', sans-serif",
                                            "margin-bottom": "2px",
                                        },
                                        "text": {
                                            "font-size": "11px",
                                            "color": "rgba(255,255,255,0.85)" if is_selected else "#6B7280",
                                            "font-family": "'Afacad', sans-serif",
                                        },
                                    },
                                )

                                if clicked:
                                    st.session_state.selected_config_idx = idx
                                    st.rerun()

                        # Get the selected config
                        selected_config = {
                            "label": "",
                            "config": configs[st.session_state.selected_config_idx],
                        }
                    else:
                        selected_config = None
                else:
                    selected_config = None

                # 3. Display consolidated results
                if selected_file_path and selected_config:
                    display_consolidated_results(
                        analyzer,
                        selected_set,
                        selected_file_path,
                        selected_config["config"],
                    )

        # Add Climate+Tech footer at the bottom of sidebar
        # Get current theme for logo selection and encode image as base64
        try:
            theme = st.context.theme if hasattr(st.context, "theme") else {}
            is_dark = theme.get("base", "light") == "dark" if theme else False
            logo_filename = (
                "assets/climate-and-tech-logo-dark-mode.png" if is_dark else "assets/climateandtech-logo-new-light-mode.png"
            )
            logo_path = Path(__file__).parent / logo_filename

            # Read and encode image as base64
            if logo_path.exists():
                with open(logo_path, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode()
                    logo_src = f"data:image/png;base64,{img_data}"
            else:
                # Fallback if logo file doesn't exist
                logo_src = ""
        except Exception as e:
            logger.warning(f"Could not load logo: {str(e)}")
            logo_src = ""

        # Add footer to sidebar
        st.sidebar.markdown("---")
        footer = f"""
        <div class="footer">
            {f'<img src="{logo_src}" alt="Climate+Tech Logo" style="height: 25px; max-width: 100%; width: auto; vertical-align: middle; margin-right: 8px; object-fit: contain;">' if logo_src else ''}
            <p>Climate+Tech Sustainability Report Analysis Tool</p>
            <p>For custom tool development contact us at <a href="https://www.climateandtech.com" target="_blank">www.climateandtech.com</a></p>
        </div>
        """
        st.sidebar.markdown(footer, unsafe_allow_html=True)

    except Exception as e:
        st.error("Error during analysis:")
        st.exception(e)


if __name__ == "__main__":
    main()
