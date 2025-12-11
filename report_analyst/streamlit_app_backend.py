"""
Report Analyst Streamlit Application

Clean, modular Streamlit app supporting multiple backend integration flows.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import streamlit as st

# Add the parent directory to Python path for backend integration imports
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
    st.error(f"Backend integration not available: {e}")
    BACKEND_INTEGRATION_AVAILABLE = False

# Try to import existing core functionality
try:
    from report_analyst.core.question_loader import get_question_loader

    question_loader = get_question_loader()
    CORE_FUNCTIONALITY_AVAILABLE = True

    def get_question_set(question_set_name):
        """Get question set using question loader"""
        question_set_obj = question_loader.get_question_set(question_set_name)
        if question_set_obj:
            return [q_data["text"] for q_data in question_set_obj.questions.values()]
        return []

except ImportError as e:
    st.error(f"Core functionality not available: {e}")
    CORE_FUNCTIONALITY_AVAILABLE = False

    def get_question_set(question_set_name):
        """Fallback question set function"""
        return [f"Sample question for {question_set_name}"]


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Main Streamlit application"""
    st.set_page_config(page_title="Report Analyst", layout="wide")

    st.title("Report Analyst")
    st.markdown("Analyze documents with configurable backend integration")

    # Check if backend integration is available
    if not BACKEND_INTEGRATION_AVAILABLE:
        st.warning(
            "Backend integration modules not available. Running in fallback mode."
        )
        run_fallback_mode()
        return

    # Get configuration
    config = configure_backend_integration()

    # Display current configuration status
    display_config_status(config)

    # Create flow orchestrator
    orchestrator = create_flow_orchestrator(config)

    # Main application flow
    run_application(orchestrator, config)


def run_application(orchestrator, config: BackendConfig):
    """Run the main application logic"""

    # File upload section
    st.header("📄 Document Upload")
    uploaded_file = st.file_uploader("Upload a document", type=["pdf"])

    if not uploaded_file:
        return

    # Process document based on flow
    if config.flow_type == "complete_backend":
        # Complete backend analysis (Flow 4)
        handle_complete_backend_flow(orchestrator, uploaded_file, config)
    else:
        # Other flows that need local analysis
        handle_processing_and_analysis_flow(orchestrator, uploaded_file, config)


def handle_complete_backend_flow(orchestrator, uploaded_file, config: BackendConfig):
    """Handle complete backend analysis flow (Flow 4)"""

    st.header("Complete Backend Analysis")

    # Select question set
    if CORE_FUNCTIONALITY_AVAILABLE:
        question_set_options = question_loader.get_question_set_options()
    else:
        # Fallback: use a generic approach without hardcoded names
        question_set_options = (
            []
        )  # No predefined options when core functionality unavailable
    question_set = st.selectbox(
        "Select Question Set",
        options=question_set_options,
        help="Question set for backend analysis",
    )

    if st.button("Start Complete Backend Analysis"):
        # Run complete backend analysis
        result = orchestrator.complete_backend_analysis(uploaded_file, question_set)

        if result.success:
            st.session_state.backend_analysis_result = result
            st.session_state.analysis_completed = True
        else:
            st.error(f"Complete backend analysis failed: {result.error}")

    # Display results if available
    if st.session_state.get("analysis_completed", False):
        display_backend_analysis_results(st.session_state.backend_analysis_result)


def handle_processing_and_analysis_flow(
    orchestrator, uploaded_file, config: BackendConfig
):
    """Handle flows that require processing then analysis"""

    # Step 1: Process document
    processing_result = orchestrator.process_document(uploaded_file)

    if not processing_result.success:
        st.error(f"Document processing failed: {processing_result.error}")
        return

    # Store processing results
    st.success(f"Document processed! Found {len(processing_result.chunks)} chunks")
    st.session_state.chunks = processing_result.chunks
    st.session_state.resource_id = processing_result.resource_id
    st.session_state.document_uploaded = True
    st.session_state.config = config

    # Step 2: Analysis section
    if st.session_state.get("document_uploaded", False):
        run_analysis_section(orchestrator, config)


def run_analysis_section(orchestrator, config: BackendConfig):
    """Run the analysis section for local/enhanced flows"""

    st.header("🔍 Document Analysis")

    # Question configuration
    questions = configure_questions()

    if not questions:
        return

    if st.button("🚀 Run Analysis"):
        # Run analysis
        chunks = st.session_state.chunks
        result = orchestrator.analyze_document(chunks, questions)

        if result.success:
            display_analysis_results(result, config)
        else:
            st.error(f"Analysis failed: {result.error}")


def configure_questions() -> List[str]:
    """Configure questions for analysis"""

    if CORE_FUNCTIONALITY_AVAILABLE:
        question_set_options = question_loader.get_question_set_options() + ["custom"]
    else:
        # Fallback: use a generic approach without hardcoded names
        question_set_options = [
            "custom"
        ]  # Only custom when core functionality unavailable
    question_set_name = st.selectbox(
        "Select Question Set",
        options=question_set_options,
        help="Choose a predefined question set or create custom questions",
    )

    if question_set_name == "custom":
        custom_question = st.text_area(
            "Enter your custom question:",
            placeholder="What are the main climate risks mentioned in this document?",
        )
        return [custom_question] if custom_question else []
    else:
        return get_question_set(question_set_name)


def display_analysis_results(result: AnalysisResult, config: BackendConfig):
    """Display analysis results from local/enhanced flows"""

    st.subheader("Analysis Results")

    results = result.results
    questions = results.get("questions", [])
    answers = results.get("answers", [])
    method = results.get("method", "unknown")

    # Display Q&A
    for i, (question, answer) in enumerate(zip(questions, answers)):
        st.write(f"**Question {i+1}:** {question}")
        st.write(f"**Answer:** {answer}")
        st.divider()

    # Display summary
    st.subheader("Analysis Summary")
    st.write(f"**Total Questions:** {len(questions)}")
    st.write(f"**Analysis Method:** {method.title()}")
    st.write(f"**Flow Type:** {config.flow_type.replace('_', ' ').title()}")

    # Show flow-specific benefits
    display_flow_benefits(config)


def display_backend_analysis_results(result: AnalysisResult):
    """Display results from complete backend analysis"""

    if not result or not result.success:
        st.error("No analysis results to display")
        return

    st.subheader("Complete Backend Analysis Results")

    # Display metadata
    st.subheader("Analysis Metadata")
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**Analysis Job ID:** {result.analysis_job_id}")
        st.write(
            f"**Stored in Backend:** {'Yes' if result.stored_in_backend else 'No'}"
        )

    with col2:
        st.write(f"**Analysis Method:** Complete Backend")
        st.write(f"**Multi-user Access:** Available to authorized users")

    # Display results
    st.subheader("Results")

    if isinstance(result.results, dict):
        if "questions" in result.results and "answers" in result.results:
            questions = result.results["questions"]
            answers = result.results["answers"]

            for i, (question, answer) in enumerate(zip(questions, answers)):
                st.write(f"**Question {i+1}:** {question}")
                st.write(f"**Answer:** {answer}")
                st.divider()
        else:
            st.json(result.results)
    else:
        st.write(result.results)

    # Display backend analysis benefits
    st.subheader("Backend Analysis Benefits")
    st.info(
        """
    **Persistent Storage**: Results stored in backend database
    **Multi-User Access**: Available to all authorized users  
    **Centralized Processing**: All computation done in backend
    **Scalable**: Backend handles multiple concurrent analyses
    **Consistent**: Same analysis logic across all clients
    """
    )

    if st.button("Refresh Results"):
        st.rerun()


def display_flow_benefits(config: BackendConfig):
    """Display benefits specific to the current flow"""

    flow_benefits = {
        "local": [
            "No dependencies",
            "Works offline",
            "Full local control",
            "Limited processing power",
        ],
        "basic_backend": [
            "Better PDF processing",
            "Vector search capabilities",
            "Async processing",
            "Still local analysis",
        ],
        "backend_with_features": [
            "Backend processing",
            "Enhanced features",
            "Better integration",
            "Partial backend usage",
        ],
        "enhanced_integration": [
            "Centralized LLM",
            "Data lake storage",
            "Full integration",
            "Production ready",
        ],
    }

    benefits = flow_benefits.get(config.flow_type, ["Unknown flow benefits"])

    st.subheader(f"{config.flow_type.replace('_', ' ').title()} Benefits")
    for benefit in benefits:
        st.write(benefit)


def run_fallback_mode():
    """Run in fallback mode when backend integration is not available"""
    st.info("Running in fallback mode - basic functionality only")

    # File upload section
    st.header("Document Upload")
    uploaded_file = st.file_uploader("Upload a document", type=["pdf"])

    if not uploaded_file:
        return

    # Question configuration
    st.header("Document Analysis")

    if CORE_FUNCTIONALITY_AVAILABLE:
        question_set_options = question_loader.get_question_set_options() + ["custom"]
        question_set_name = st.selectbox(
            "Select Question Set",
            options=question_set_options,
            help="Choose a predefined question set or create custom questions",
        )

        if question_set_name == "custom":
            custom_question = st.text_area(
                "Enter your custom question:",
                placeholder="What are the main climate risks mentioned in this document?",
            )
            questions = [custom_question] if custom_question else []
        else:
            questions = get_question_set(question_set_name)

        if st.button("Run Analysis"):
            st.success(
                f"Loaded {len(questions)} questions from {question_set_name.upper()}"
            )

            # Display questions (fallback analysis)
            st.subheader("Questions to Analyze")
            for i, question in enumerate(questions, 1):
                st.write(f"**{i}.** {question}")

            st.info(
                "This is a demo mode. Backend integration modules are not available."
            )
    else:
        st.error("Core functionality not available. Please check your installation.")


if __name__ == "__main__":
    main()
