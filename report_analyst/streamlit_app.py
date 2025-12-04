import asyncio
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
        self.cache_manager = (
            self.analyzer.cache_manager
        )  # Access the cache manager from the analyzer

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
    ) -> AsyncGenerator[Dict, None]:
        """Analyze a document using the provided questions"""
        try:
            log_analysis_step(f"Starting analysis of document: {file_path}")
            log_analysis_step(f"Selected questions: {selected_questions}")
            log_analysis_step(f"LLM scoring enabled: {use_llm_scoring}")

            # Update analyzer with the current questions
            self.analyzer.questions = questions

            # Convert selected question IDs to numbers for the analyzer
            selected_numbers = [
                questions[q_id]["number"] for q_id in selected_questions
            ]

            # Get the question set prefix from the first selected question
            question_set = (
                selected_questions[0].split("_")[0] if selected_questions else "tcfd"
            )
            self.analyzer.question_set = question_set

            # Pass use_llm_scoring to process_document
            async for result in self.analyzer.process_document(
                file_path,
                selected_numbers,
                use_llm_scoring,
                single_call,
                force_recompute,
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
        return self.analyzer.process_document(
            file_path, selected_questions, use_llm_scoring, single_call, force_recompute
        )


def save_uploaded_file(uploaded_file) -> Optional[str]:
    """Save uploaded file to temp directory"""
    try:
        if uploaded_file is None:
            logger.warning("No file was uploaded")
            return None

        # If it's already a path, just return it
        if isinstance(uploaded_file, (str, Path)):
            return str(uploaded_file)

        # Check if file was already saved in this session
        file_key = f"saved_file_{uploaded_file.name}"
        if file_key in st.session_state:
            return st.session_state[file_key]

        # Otherwise, handle it as an UploadedFile
        file_path = Path("temp") / uploaded_file.name
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
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
            "Vector Similarity": st.column_config.NumberColumn(
                "Vector Similarity", format="%.3f"
            ),
            "LLM Score": st.column_config.NumberColumn("LLM Score", format="%.3f"),
            "Chunk Text": st.column_config.TextColumn("Chunk Text", width="large"),
        },
    )


def convert_df(df: pd.DataFrame) -> bytes:
    """Convert a DataFrame to CSV bytes"""
    return df.to_csv(index=False).encode("utf-8")


def display_download_buttons(
    analysis_df: pd.DataFrame, chunks_df: pd.DataFrame, file_key: str
):
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
        question_set = (
            selected_questions_list[0].split("_")[0]
            if selected_questions_list
            else "tcfd"
        )

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
            log_analysis_step(
                f"Found {len(cached_answers)} cached answers for {file_key}"
            )
            # Show cache info
            st.info(f"📁 Loading results from cache: {file_key}")

            # Update results with cached answers
            for q_id, answer in cached_answers.items():
                st.session_state.results["answers"][q_id] = answer

            # Update display with cached results
            logger.info(
                f"Creating dataframes with cached results for file_key: {file_key}"
            )
            logger.info(
                f"Current session state settings: chunk_size={st.session_state.get('new_chunk_size')}, overlap={st.session_state.get('new_overlap')}, top_k={st.session_state.get('new_top_k')}, llm_model={st.session_state.get('new_llm_model')}, use_llm_scoring={st.session_state.get('new_llm_scoring')}"
            )
            analysis_df, chunks_df = create_analysis_dataframes(
                st.session_state.results["answers"], file_key
            )
            st.session_state.analysis_df = analysis_df
            st.session_state.chunks_df = chunks_df

        # Determine which questions need processing
        questions_to_process = [
            q_id
            for q_id in selected_questions_list
            if force_recompute or q_id not in cached_answers
        ]

        if questions_to_process:
            log_analysis_step(
                f"Processing {len(questions_to_process)} uncached questions..."
            )

            # Update analyzer with question set
            report_analyzer.analyzer.question_set = question_set

            # Process only uncached questions
            async for result in report_analyzer.analyze_document(
                file_path,
                questions,
                questions_to_process,
                use_llm_scoring,
                single_call,
                force_recompute,
            ):
                # Add debug logging to see what results we're getting
                log_analysis_step(f"Received result: {str(result)[:200]}...")

                if "error" in result:
                    log_analysis_step(
                        f"Error received from analyzer: {result['error']}", "error"
                    )
                    st.error(f"Analysis error: {result['error']}")
                    continue

                if "status" in result:
                    status_placeholder.write(result["status"])
                    continue

                question_id = result.get("question_id")
                if question_id is None:
                    log_analysis_step(
                        f"No question_id in result: {str(result)[:200]}...", "warning"
                    )
                    continue

                # Store results
                st.session_state.results["answers"][question_id] = result

                # Update display
                logger.info(
                    f"Creating dataframes with updated results for file_key: {file_key}"
                )
                logger.info(
                    f"Current session state settings: chunk_size={st.session_state.get('new_chunk_size')}, overlap={st.session_state.get('new_overlap')}, top_k={st.session_state.get('new_top_k')}, llm_model={st.session_state.get('new_llm_model')}, use_llm_scoring={st.session_state.get('new_llm_scoring')}"
                )
                analysis_df, chunks_df = create_analysis_dataframes(
                    st.session_state.results["answers"], file_key
                )

                st.session_state.analysis_df = analysis_df
                st.session_state.chunks_df = chunks_df

                # Add a success message for each processed question
                st.success(f"✓ Processed question {question_id}")
        else:
            log_analysis_step("All selected questions have cached answers")
            # Show success message for cached results
            st.success(
                f"✓ All {len(selected_questions_list)} selected questions loaded from cache"
            )

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
            "Chunk Text": st.column_config.TextColumn(
                "Chunk Text", help="Text content of the chunk", width="large"
            ),
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


def get_uploaded_files_history() -> List[Dict]:
    """Get list of previously uploaded files from temp directory"""
    temp_dir = Path("temp")
    if not temp_dir.exists():
        return []

    files = []
    for file in temp_dir.glob("*.pdf"):
        # Verify file exists and is not empty
        if file.exists() and file.stat().st_size > 0:
            files.append(
                {
                    "name": file.name,
                    "path": str(file.resolve()),  # Get absolute path
                    "date": file.stat().st_mtime,
                    "size": file.stat().st_size,
                }
            )
            logger.info(f"Found file: {file.name}, size: {file.stat().st_size} bytes")

    # Sort by most recent first
    return sorted(files, key=lambda x: x["date"], reverse=True)


def display_analysis_results(
    analysis_df: pd.DataFrame, chunks_df: pd.DataFrame, file_key: str = None
) -> None:
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


def display_consolidated_results(analyzer, question_set):
    """Display consolidated results for all analyzed documents"""
    try:
        # Get all available cache configurations
        cache_configs = analyzer.analyzer.cache_manager.check_cache_status()
        logger.info(f"Found cache configs: {cache_configs}")

        if not cache_configs:
            st.warning("No cached analyses found")
            return

        # Group configurations by file
        file_configs = {}
        for config in cache_configs:
            if len(config) == 6:  # Full config row from cache_status
                file_path, chunk_size, chunk_overlap, top_k, model, qs = config
                if qs == question_set:  # Only show configs for selected question set
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
            st.warning(f"No cached results found for question set: {question_set}")
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
                logger.info(
                    f"Getting results for {Path(file_path).name} with config: {selected_config['config']}"
                )

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
                                "Question Text": (
                                    questions[question_id]["text"]
                                    if question_id in questions
                                    else question_id
                                ),
                                "Analysis": result.get("ANSWER", ""),
                                "Score": float(result.get("SCORE", 0)),
                                "Key Evidence": "\n".join(
                                    [
                                        e.get("text", "")
                                        for e in result.get("EVIDENCE", [])
                                    ]
                                ),
                                "Gaps": "\n".join(result.get("GAPS", [])),
                                "Sources": ", ".join(
                                    map(str, result.get("SOURCES", []))
                                ),
                            }
                            analysis_rows.append(analysis_row)
                            logger.debug(
                                f"Added analysis row for {question_id}: {json.dumps(analysis_row, indent=2)}"
                            )

                            # Process chunks if available
                            if "chunks" in data:
                                for chunk in data["chunks"]:
                                    chunk_row = {
                                        "Question ID": question_id,
                                        "Text": chunk.get("text", ""),
                                        "Vector Similarity": chunk.get(
                                            "similarity_score", 0.0
                                        ),
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
                        chunks_df = (
                            pd.DataFrame(chunks_rows) if chunks_rows else pd.DataFrame()
                        )

                        # Display results using the existing display function
                        file_key = f"{Path(file_path).stem}_cs{selected_config['config']['chunk_size']}"
                        display_analysis_results(analysis_df, chunks_df, file_key)
                    else:
                        st.warning("No results found in cache for this configuration")
                else:
                    st.warning("No cached results found for this configuration")

    except Exception as e:
        logger.error(f"Error displaying consolidated results: {str(e)}", exc_info=True)
        st.error(f"Error displaying consolidated results: {str(e)}")


def display_cache_selector(file_path: str):
    """Display cache management options"""
    st.subheader("Cache Management")

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
            cache_entries = (
                st.session_state.analyzer.analyzer.cache_manager.check_cache_status(
                    file_path
                )
            )
            if cache_entries:
                st.text(f"Found {len(cache_entries)} cached configurations:")
                for entry in cache_entries:
                    st.text(f"• Configuration: {entry}")

                col1, col2 = st.columns([3, 1])
                with col1:
                    st.text(f"Current configuration: {current_config}")

                with col2:
                    if st.button("🔄 Clear Cache for File"):
                        try:
                            st.session_state.analyzer.analyzer.cache_manager.clear_cache(
                                file_path
                            )
                            st.success(f"Cache cleared for file.")
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
                            st.error(f"Error clearing cache: {str(e)}")
            else:
                st.info("No cached analyses available for this file")
        except Exception as e:
            st.error(f"Error checking cache status: {str(e)}")


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
        st.error(
            f"⚠️ Cannot use {llm_model} - No Google API key is set. Defaulting to {OPENAI_MODELS[0]}."
        )
        # Reset to default OpenAI model
        llm_model = OPENAI_MODELS[0]
        st.session_state.new_llm_model = llm_model
    elif llm_model.startswith("gpt-") and not os.getenv("OPENAI_API_KEY"):
        logger.error(f"Attempt to use OpenAI model '{llm_model}' without API key")
        st.error(
            f"⚠️ OPENAI_API_KEY environment variable is not set. OpenAI models will not work correctly."
        )

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
            logger.info(
                f"Updated use_llm_scoring to: {st.session_state.use_llm_scoring}"
            )

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
            progress_text.success("Found cached results!")
            st.session_state.results = cached_results
            logger.info(
                f"[ANALYSIS] Writing results to session state for file: {file_path}"
            )
            logger.info(
                f"[ANALYSIS] Attempting to display results for file: {file_path}"
            )
            return
        else:
            logger.info(f"[CACHE] Cache MISS for config: {config}")
        # If no cached results or force recompute, run analysis
        progress_text.info("Starting analysis...")

        # Log the LLM scoring setting
        llm_scoring_enabled = st.session_state.get("new_llm_scoring", False)
        progress_text.info(
            f"LLM scoring: {'Enabled' if llm_scoring_enabled else 'Disabled'}"
        )
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

        # First update the analyzer's process_document method to use progress_text instead of yielding status
        async for result in analyzer.process_document(
            file_path=file_path,
            selected_questions=question_numbers,  # Pass just the numbers
            use_llm_scoring=st.session_state.get(
                "new_llm_scoring", False
            ),  # Use the checkbox value directly
            force_recompute=st.session_state.get("force_recompute", False),
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
        logger.info(
            f"[ANALYSIS] Writing results to session state for file: {file_path}"
        )
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
            st.session_state.analysis_complete = (
                False  # Initialize analysis complete flag
            )

        st.set_page_config(page_title="Report Analyst", layout="wide")

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

        st.title("Report Analyst")

        # Backend Integration Section
        if BACKEND_INTEGRATION_AVAILABLE:
            with st.expander("🔧 Backend Integration", expanded=False):
                config = configure_backend_integration()
                display_config_status(config)
        else:
            # Show fallback info
            with st.expander("🔧 Backend Integration", expanded=False):
                st.warning("⚠️ Backend integration modules not available")
                st.info(
                    "Install backend integration dependencies to enable advanced features"
                )

        # Settings section - moved below the title
        with st.expander("Analysis Configuration", expanded=True):
            # Question set selection
            col1, col2 = st.columns([1, 2])
            with col1:
                selected_set = st.selectbox(
                    "Select Question Set",
                    options=list(question_sets.keys()),
                    format_func=lambda x: question_sets[x]["name"],
                    key="new_question_set",
                    index=0,  # Ensure a default is selected
                    on_change=update_analyzer_parameters,
                )

            # Show question set description
            with col2:
                if selected_set in question_sets:
                    st.info(question_sets[selected_set]["description"])

            # Update analyzer's question set
            analyzer.analyzer.update_question_set(selected_set)

            # Clear results if question set changed
            if (
                "last_question_set" not in st.session_state
                or st.session_state.last_question_set != selected_set
            ):
                if "results" in st.session_state:
                    del st.session_state.results
                st.session_state.last_question_set = selected_set

            # LLM settings
            col1, col2, col3 = st.columns(3)
            with col1:
                new_llm_scoring = st.checkbox(
                    "Use LLM Scoring",
                    value=False,
                    key="new_llm_scoring",
                    on_change=update_analyzer_parameters,
                )
            with col2:
                new_batch_scoring = st.checkbox(
                    "Batch Scoring",
                    value=True,
                    key="new_batch_scoring",
                    disabled=not st.session_state.get("new_llm_scoring", False),
                    help="Batch scoring only applies when LLM scoring is enabled. When enabled, all chunks are scored in one API call instead of individual calls.",
                )
            with col3:
                # Display available API info
                api_info = []
                if os.getenv("OPENAI_API_KEY"):
                    api_info.append("OpenAI")
                if os.getenv("GOOGLE_API_KEY"):
                    api_info.append("Gemini")

                if len(api_info) > 1:
                    api_status = f"Using {' & '.join(api_info)} models"
                elif len(api_info) == 1:
                    api_status = f"Using {api_info[0]} models only"
                else:
                    api_status = "No API keys configured"

                st.caption(api_status)

                new_llm_model = st.selectbox(
                    "LLM Model",
                    options=LLM_MODELS,
                    index=0,  # Ensure a default is selected
                    key="new_llm_model",
                    on_change=update_analyzer_parameters,
                )

            # Chunking parameters
            col1, col2, col3 = st.columns(3)
            with col1:
                new_chunk_size = st.number_input(
                    "Chunk Size",
                    min_value=100,
                    max_value=2000,
                    value=500,  # Default value
                    key="new_chunk_size",
                    on_change=update_analyzer_parameters,
                )
            with col2:
                new_overlap = st.number_input(
                    "Overlap",
                    min_value=0,
                    max_value=100,
                    value=20,  # Default value
                    key="new_overlap",
                    on_change=update_analyzer_parameters,
                )
            with col3:
                new_top_k = st.number_input(
                    "Top K",
                    min_value=1,
                    max_value=20,
                    value=5,  # Default value
                    key="new_top_k",
                    on_change=update_analyzer_parameters,
                )

        # Create tabs
        file_tab, upload_tab, consolidated_tab = st.tabs(
            ["Previous Reports", "Upload New", "Consolidated Results"]
        )

        # Previous Reports tab
        with file_tab:
            previous_files = get_uploaded_files_history()
            if previous_files:
                selected_file = st.selectbox(
                    "Select a previously analyzed report",
                    options=previous_files,
                    format_func=lambda x: x["name"],
                    key="previous_file",
                )
                if selected_file:
                    file_path = Path(selected_file["path"])
                    if file_path.exists():
                        # Load questions and handle selection
                        question_set_data = analyzer.load_question_set(
                            st.session_state.new_question_set
                        )
                        questions = question_set_data["questions"]

                        if question_set_data["description"]:
                            st.write(question_set_data["description"])

                        # Add cache selector
                        display_cache_selector(str(file_path))

                        # Add question selection UI
                        st.subheader("Select Questions")
                        selected_questions = []
                        for q_id, q_data in questions.items():
                            if st.checkbox(
                                f"{q_id}: {q_data['text']}",
                                key=f"individual_question_{q_id}",
                            ):
                                selected_questions.append(q_id)

                        # Analysis button and results
                        col1, col2 = st.columns([2, 1])
                        with col1:
                            analyze_clicked = st.button(
                                "Analyze Selected Questions", key="analyze_button"
                            )
                        with col2:
                            reanalyze_clicked = st.button(
                                "🔄 Reanalyze", key="reanalyze_button"
                            )

                        if analyze_clicked or reanalyze_clicked:
                            if not selected_questions:
                                st.warning(
                                    "Please select at least one question to analyze."
                                )
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

                                    if reanalyze_clicked:
                                        # For reanalysis, skip cache check and analyze all selected questions
                                        progress_text.info(
                                            f"Reanalyzing {len(selected_questions)} questions..."
                                        )
                                        asyncio.run(
                                            run_analysis(
                                                analyzer,
                                                file_path=str(file_path),
                                                selected_questions=selected_questions,
                                                progress_text=progress_text,
                                            )
                                        )
                                    else:
                                        # For normal analysis, check cache first
                                        cached_results = analyzer.analyzer.cache_manager.get_analysis(
                                            file_path=str(file_path),
                                            config=config,
                                            question_ids=selected_questions,
                                        )

                                        if cached_results:
                                            # Process cached results
                                            for (
                                                question_id,
                                                result,
                                            ) in cached_results.items():
                                                st.session_state.results["answers"][
                                                    question_id
                                                ] = result

                                            # Generate file key for display
                                            file_key = generate_file_key(
                                                str(file_path), st
                                            )

                                            # Update display
                                            analysis_df, chunks_df = (
                                                create_analysis_dataframes(
                                                    st.session_state.results["answers"],
                                                    file_key,
                                                )
                                            )
                                            st.session_state.analysis_df = analysis_df
                                            st.session_state.chunks_df = chunks_df
                                            st.session_state.analysis_complete = True
                                        else:
                                            # Run analysis for uncached questions
                                            progress_text.info(
                                                f"Processing {len(selected_questions)} questions..."
                                            )

                                            try:
                                                # Run analysis for uncached questions
                                                asyncio.run(
                                                    analyze_document_and_display(
                                                        analyzer,
                                                        file_path=str(
                                                            file_path
                                                        ),  # Use the actual file path
                                                        questions=questions,
                                                        selected_questions=selected_questions,
                                                        use_llm_scoring=st.session_state.new_llm_scoring,
                                                        single_call=st.session_state.new_batch_scoring,
                                                    )
                                                )

                                                progress_text.success(
                                                    "Analysis complete!"
                                                )

                                            except Exception as e:
                                                st.error(
                                                    f"Error during analysis: {str(e)}"
                                                )
                                                st.exception(e)

                                        # Get final results
                                        all_results = analyzer.analyzer.cache_manager.get_analysis(
                                            file_path=str(file_path),
                                            config=config,
                                            question_ids=selected_questions,
                                        )

                                        # Process all results into dataframes
                                        if all_results:
                                            analysis_df, chunks_df = (
                                                create_analysis_dataframes(all_results)
                                            )
                                            file_key = Path(file_path).stem
                                            display_analysis_results(
                                                analysis_df, chunks_df, file_key
                                            )
                                            progress_text.success(
                                                f"✓ Analysis complete for {len(selected_questions)} questions"
                                            )
                                        else:
                                            progress_text.error(
                                                "No results found after analysis"
                                            )

                                except Exception as e:
                                    logger.error(
                                        f"Error during analysis: {str(e)}",
                                        exc_info=True,
                                    )
                                    st.error(f"Error during analysis: {str(e)}")
                    else:
                        st.error(f"File not found: {file_path}")
            else:
                st.info("No previously analyzed reports found")

        # Upload New tab
        with upload_tab:
            uploaded_file = st.file_uploader(
                "Choose a PDF file", type="pdf", key="file_uploader"
            )
            if uploaded_file:
                file_path = save_uploaded_file(uploaded_file)
                logger.info(
                    f"[UPLOAD] Saved uploaded file: {uploaded_file.name} at {file_path}"
                )
                if file_path and file_path != st.session_state.get("current_file"):
                    st.session_state.current_file = file_path
                    st.session_state.uploaded_file = uploaded_file
                    st.session_state.analysis_complete = False
                    st.session_state.analysis_triggered = False
                    if "results" in st.session_state:
                        del st.session_state.results
                    logger.info(
                        f"[UPLOAD] Added file to session state: {uploaded_file.name}"
                    )
                    st.success(f"File uploaded successfully: {uploaded_file.name}")
                    logger.info(
                        f"[UPLOAD] Displaying cache selector for file: {file_path}"
                    )
                    display_cache_selector(file_path)
                    if not st.session_state.get("file_processed"):
                        st.session_state.file_processed = True
                        st.rerun()

        # Consolidated Results tab
        with consolidated_tab:
            st.header("View All Results")
            st.write("View and export consolidated results for all analyzed reports")

            # Question set selection for consolidated view
            selected_set = st.selectbox(
                "Select Question Set",
                options=list(question_sets.keys()),
                format_func=lambda x: question_sets[x]["name"],
                key="consolidated_set",
            )

            if selected_set:
                # Show question set description
                if selected_set in question_sets:
                    st.info(question_sets[selected_set]["description"])

                # Only show consolidated results
                display_consolidated_results(analyzer, selected_set)

        # Add Climate+Tech footer at the end
        footer = """
        <style>
        .footer {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100%;
            background-color: #f1f1f1;
            color: black;
            text-align: center;
            padding: 10px;
            font-size: 14px;
        }
        .footer img {
            height: 30px;
            vertical-align: middle;
            margin-right: 10px;
        }
        </style>
        <div class="footer">
            <img src="https://www.climateandtech.com/climateandtech.png" alt="Climate+Tech Logo">
            <p>Climate+Tech Sustainability Report Analysis Tool</p>
            <p>For custom tool development contact us at <a href="https://www.climateandtech.com" target="_blank">www.climateandtech.com</a></p>
        </div>
        """
        st.markdown(footer, unsafe_allow_html=True)

    except Exception as e:
        st.error("Error during analysis:")
        st.exception(e)


if __name__ == "__main__":
    main()
