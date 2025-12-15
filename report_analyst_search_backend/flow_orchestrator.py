"""
Flow Orchestrator

Manages the different document processing and analysis flows.
Provides a clean interface for executing different integration patterns.
"""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import streamlit as st

from .backend_service import BackendService, BackendServiceError, handle_backend_error
from .config import BackendConfig

logger = logging.getLogger(__name__)

# Add parent directory to path for question loader import
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import question loader for dynamic question set loading
try:
    from report_analyst.core.question_loader import get_question_loader

    question_loader = get_question_loader()
    QUESTION_LOADER_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Question loader not available: {e}")
    QUESTION_LOADER_AVAILABLE = False


@dataclass
class ProcessingResult:
    """Result from document processing"""

    success: bool
    chunks: Optional[List[Dict[str, Any]]] = None
    resource_id: Optional[str] = None
    error: Optional[str] = None


@dataclass
class AnalysisResult:
    """Result from analysis"""

    success: bool
    results: Optional[Dict[str, Any]] = None
    analysis_job_id: Optional[str] = None
    stored_in_backend: bool = False
    error: Optional[str] = None


class FlowOrchestrator:
    """Orchestrates different processing and analysis flows"""

    def __init__(self, config: BackendConfig):
        self.config = config
        self.backend_service = BackendService(config) if config.use_backend else None

    def process_document(self, uploaded_file) -> ProcessingResult:
        """
        Process document based on configuration.

        Args:
            uploaded_file: Streamlit uploaded file

        Returns:
            ProcessingResult: Result of processing
        """
        flow_type = self.config.flow_type

        try:
            if flow_type == "local":
                return self._process_local(uploaded_file)
            elif flow_type in [
                "basic_backend",
                "backend_with_features",
                "enhanced_integration",
            ]:
                return self._process_with_backend(uploaded_file)
            elif flow_type == "complete_backend":
                return self._process_complete_backend(uploaded_file)
            else:
                return ProcessingResult(success=False, error=f"Unknown flow type: {flow_type}")
        except Exception as e:
            logger.error(f"Document processing failed: {e}")
            return ProcessingResult(success=False, error=str(e))

    def analyze_document(self, chunks: List[Dict[str, Any]], questions: List[str]) -> AnalysisResult:
        """
        Analyze document based on configuration.

        Args:
            chunks: Document chunks
            questions: Questions to analyze

        Returns:
            AnalysisResult: Result of analysis
        """
        flow_type = self.config.flow_type

        try:
            if flow_type == "local":
                return self._analyze_local(chunks, questions)
            elif flow_type in ["basic_backend", "backend_with_features"]:
                return self._analyze_local_with_features(chunks, questions)
            elif flow_type == "enhanced_integration":
                return self._analyze_enhanced(chunks, questions)
            else:
                return AnalysisResult(success=False, error=f"Analysis not supported for flow: {flow_type}")
        except Exception as e:
            logger.error(f"Document analysis failed: {e}")
            return AnalysisResult(success=False, error=str(e))

    def complete_backend_analysis(self, uploaded_file, question_set: str) -> AnalysisResult:
        """
        Complete backend analysis flow (Flow 4).

        Args:
            uploaded_file: Streamlit uploaded file
            question_set: Question set to use

        Returns:
            AnalysisResult: Complete analysis result
        """
        try:
            st.info("Using complete backend analysis - backend does all the work!")

            # Step 1: Upload
            with st.spinner("Uploading document to backend..."):
                file_bytes = uploaded_file.read()
                import asyncio

                resource_id = asyncio.run(self.backend_service.upload_pdf(file_bytes, uploaded_file.name))
                st.success(f"✅ Document uploaded! Resource ID: {resource_id}")

            # Step 2: Wait for processing
            with st.spinner("Waiting for PDF processing..."):
                processing_success = self.backend_service.wait_for_processing(resource_id)
                if not processing_success:
                    return AnalysisResult(success=False, error="PDF processing failed")

            # Step 3: Configure question set
            question_set = self._configure_question_set(question_set)

            # Step 4: Submit analysis job
            with st.spinner("Submitting analysis job to backend..."):
                analysis_job_id = self.backend_service.submit_analysis_job(resource_id, question_set)
                st.success(f"Analysis job submitted! Job ID: {analysis_job_id}")

            # Step 5: Wait for analysis
            with st.spinner("Backend is running analysis..."):
                analysis_results = self.backend_service.wait_for_analysis(analysis_job_id)

            st.success("Analysis completed and stored in backend database!")
            st.info("These results are now available to all authorized users")

            return AnalysisResult(
                success=True,
                results=analysis_results,
                analysis_job_id=analysis_job_id,
                stored_in_backend=True,
            )

        except BackendServiceError as e:
            handle_backend_error(e, "Complete backend analysis")
            return AnalysisResult(success=False, error=str(e))

    def _process_local(self, uploaded_file) -> ProcessingResult:
        """Process document locally"""
        st.info("Using local processing")

        with st.spinner("Processing document locally..."):
            # Simulate local processing
            chunks = [
                {
                    "chunk_text": f"Local processing chunk 1 from {uploaded_file.name}",
                    "chunk_id": "local_1",
                    "chunk_metadata": {"source": "local"},
                },
                {
                    "chunk_text": f"Local processing chunk 2 from {uploaded_file.name}",
                    "chunk_id": "local_2",
                    "chunk_metadata": {"source": "local"},
                },
            ]

        return ProcessingResult(success=True, chunks=chunks)

    def _process_with_backend(self, uploaded_file) -> ProcessingResult:
        """Process document with search backend"""
        try:
            # Upload
            with st.spinner("Uploading document to backend..."):
                file_bytes = uploaded_file.read()
                import asyncio

                resource_id = asyncio.run(self.backend_service.upload_pdf(file_bytes, uploaded_file.name))
                st.success(f"✅ Document uploaded! Resource ID: {resource_id}")

            # Wait for processing
            with st.spinner("Waiting for backend processing..."):
                success = self.backend_service.wait_for_processing(resource_id)
                if not success:
                    return ProcessingResult(success=False, error="Backend processing failed")

            # Get chunks
            with st.spinner("Retrieving chunks..."):
                chunks = self.backend_service.get_chunks(resource_id)
                if not chunks:
                    return ProcessingResult(success=False, error="No chunks retrieved")

            return ProcessingResult(success=True, chunks=chunks, resource_id=resource_id)

        except BackendServiceError as e:
            handle_backend_error(e, "Backend processing")
            return ProcessingResult(success=False, error=str(e))

    def _process_complete_backend(self, uploaded_file) -> ProcessingResult:
        """This shouldn't be called - complete backend does analysis too"""
        return ProcessingResult(
            success=False,
            error="Complete backend analysis should use complete_backend_analysis() method",
        )

    def _analyze_local(self, chunks: List[Dict[str, Any]], questions: List[str]) -> AnalysisResult:
        """Analyze locally"""
        st.info("Using local analysis")

        results = []
        for question in questions:
            # Simulate local analysis
            chunk_texts = [chunk.get("chunk_text", "") for chunk in chunks[:3]]
            context = " ".join(chunk_texts)

            answer = f"Local analysis for: {question}\n\nBased on the document content: {context[:100]}..."
            results.append({"question": question, "answer": answer})

        return AnalysisResult(
            success=True,
            results={
                "questions": questions,
                "answers": [r["answer"] for r in results],
                "method": "local",
            },
        )

    def _analyze_local_with_features(self, chunks: List[Dict[str, Any]], questions: List[str]) -> AnalysisResult:
        """Analyze locally with optional features"""
        # For now, same as local analysis
        # Could be enhanced with centralized LLM or data lake storage
        return self._analyze_local(chunks, questions)

    def _analyze_enhanced(self, chunks: List[Dict[str, Any]], questions: List[str]) -> AnalysisResult:
        """Enhanced analysis with centralized LLM and data lake"""
        # This would use NATS LLM and store in data lake
        # For now, fallback to local analysis
        st.info("Enhanced analysis not fully implemented - using local analysis")
        return self._analyze_local(chunks, questions)

    def _configure_question_set(self, default_question_set: str) -> str:
        """Configure question set for backend analysis"""
        st.subheader("🔍 Analysis Configuration")

        # Get dynamic question set options
        if QUESTION_LOADER_AVAILABLE:
            question_set_options = question_loader.get_question_set_options() + ["custom"]
            # Calculate index for default question set
            try:
                index = question_set_options.index(default_question_set) if default_question_set in question_set_options else 0
            except ValueError:
                index = 0
        else:
            # Fallback: use a generic approach without hardcoded names
            question_set_options = ["custom"]  # Only custom when question loader unavailable
            index = 0

        question_set = st.selectbox(
            "Select Question Set for Backend Analysis",
            options=question_set_options,
            index=index,
            help="Choose question set for backend to analyze",
        )

        if question_set == "custom":
            custom_questions = st.text_area(
                "Enter custom questions (one per line):",
                placeholder="What are the main climate risks?\nHow does the company address sustainability?",
            )
            if custom_questions:
                # For backend analysis, we'd pass the custom questions
                # This is a simplified implementation
                st.info("Custom questions will be sent to backend")

        return question_set

    async def external_service_analysis(
        self,
        service_id: str,
        external_request_id: str,
        content: Union[str, List[Dict[str, Any]]],  # S3 URL or chunks
        question_set: str,
        analysis_config: Dict[str, Any],
        response_method: str = "nats",  # "nats" or "poll"
    ) -> AnalysisResult:
        """
        Analyze content from external service.

        Args:
            service_id: External service identifier
            external_request_id: Original request ID from external service
            content: S3 URL (str) or pre-processed chunks (List[Dict])
            question_set: Question set identifier (e.g., "tcfd")
            analysis_config: Analysis configuration
            response_method: How to deliver results ("nats" or "poll")

        Returns:
            AnalysisResult with answers and top chunks
        """
        try:
            from report_analyst.core.analyzer import DocumentAnalyzer

            from .external_service_delivery import ExternalServiceDelivery
            from .external_service_handler import ExternalServiceHandler

            handler = ExternalServiceHandler()
            delivery = ExternalServiceDelivery()

            # Process content
            if isinstance(content, str):
                # S3 URL - download and process
                from .external_service_handler import ExternalServiceReadyEvent

                notification = ExternalServiceReadyEvent(
                    service_id=service_id,
                    request_id=external_request_id,
                    content_type="s3_url",
                    s3_url=content,
                )
                processing_result = await handler.handle_external_notification(service_id, notification)
            else:
                # Pre-processed chunks
                from .external_service_handler import ExternalServiceReadyEvent

                notification = ExternalServiceReadyEvent(
                    service_id=service_id,
                    request_id=external_request_id,
                    content_type="chunks",
                    chunks=content,
                )
                processing_result = await handler.handle_external_notification(service_id, notification)

            if not processing_result.success:
                return AnalysisResult(success=False, error=processing_result.error)

            chunks = processing_result.chunks
            if not chunks:
                return AnalysisResult(success=False, error="No chunks available for analysis")

            # Convert chunks to analyzer format
            analyzer_chunks = [
                {
                    "text": chunk.get("chunk_text", chunk.get("text", "")),
                    "metadata": chunk.get("chunk_metadata", chunk.get("metadata", {})),
                }
                for chunk in chunks
            ]

            # Get analyzer
            analyzer = DocumentAnalyzer()
            analyzer.question_set = question_set
            analyzer.questions = analyzer._load_questions()

            # Update analyzer config from analysis_config
            if "chunk_size" in analysis_config:
                analyzer.chunk_params["chunk_size"] = analysis_config["chunk_size"]
            if "chunk_overlap" in analysis_config:
                analyzer.chunk_params["chunk_overlap"] = analysis_config["chunk_overlap"]
            if "top_k" in analysis_config:
                analyzer.chunk_params["top_k"] = analysis_config["top_k"]

            # Run analysis on all questions
            all_question_ids = list(analyzer.questions.keys())
            selected_questions = list(range(1, len(all_question_ids) + 1))

            # Use a temporary file path for cache key
            temp_file_path = f"external_service_{service_id}_{external_request_id}"

            answers = []
            top_chunks_by_question = {}

            async for result in analyzer.process_document(
                file_path=temp_file_path,
                selected_questions=selected_questions,
                use_llm_scoring=analysis_config.get("use_llm_scoring", False),
                single_call=analysis_config.get("single_call", True),
                pre_retrieved_chunks=analyzer_chunks,
            ):
                if "error" in result:
                    logger.error(f"Analysis error: {result['error']}")
                    continue

                if "question_id" in result and "answer" in result:
                    question_id = result["question_id"]
                    answers.append(
                        {
                            "question_id": question_id,
                            "question_text": result.get("question_text", ""),
                            "answer": result["answer"],
                            "confidence_score": result.get("confidence_score"),
                        }
                    )

                    # Collect top chunks for this question
                    evidence_chunks = result.get("evidence_chunks", [])
                    top_chunks_by_question[question_id] = evidence_chunks

            # Flatten top chunks (one list with all top chunks across questions)
            top_chunks = []
            for question_id, chunks_list in top_chunks_by_question.items():
                for chunk in chunks_list:
                    top_chunks.append(
                        {
                            "chunk_id": chunk.get("id", ""),
                            "chunk_text": chunk.get("text", ""),
                            "relevance_score": chunk.get("similarity_score", 0.0),
                            "question_id": question_id,
                            "metadata": chunk.get("metadata", {}),
                        }
                    )

            # Generate request ID for delivery
            import uuid

            request_id = str(uuid.uuid4())

            # Deliver results
            results_data = {
                "answers": answers,
                "top_chunks": top_chunks,
            }

            delivery_success = await delivery.deliver_results(
                service_id=service_id,
                request_id=request_id,
                external_request_id=external_request_id,
                results=results_data,
                response_method=response_method,
                status="completed",
            )

            if not delivery_success:
                logger.warning("Failed to deliver results, but analysis completed")

            return AnalysisResult(
                success=True,
                results={
                    "request_id": request_id,
                    "answers": answers,
                    "top_chunks": top_chunks,
                },
                analysis_job_id=request_id,
            )

        except Exception as e:
            logger.error(f"External service analysis failed: {e}")
            return AnalysisResult(success=False, error=str(e))


# Factory function for creating orchestrator
def create_flow_orchestrator(config: BackendConfig) -> FlowOrchestrator:
    """Create flow orchestrator from config"""
    return FlowOrchestrator(config)


# Convenience function for determining if analysis is needed
def needs_local_analysis(config: BackendConfig) -> bool:
    """Check if local analysis is needed based on flow"""
    return config.flow_type != "complete_backend"
