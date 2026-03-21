"""
Document Analysis Job Handler

Handles document analysis jobs using the existing analyzer logic.
Can be executed by any job executor (NATS, Lambda, etc.).
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from report_analyst.core.analyzer import DocumentAnalyzer
from report_analyst.core.document_sources import DocumentSource
from report_analyst.core.plugins import discover_document_sources
from report_analyst.core.question_loader import get_question_loader

from .interfaces import (
    AnalysisJobDefinition,
    JobDefinition,
    JobHandler,
    JobResult,
    JobStatus,
)

logger = logging.getLogger(__name__)


class DocumentAnalysisHandler(JobHandler):
    """Handler for document analysis jobs"""

    def __init__(self):
        self.analyzer = DocumentAnalyzer()
        self.question_loader = get_question_loader()
        self.document_sources = discover_document_sources()

    async def execute(self, job: JobDefinition) -> JobResult:
        """Execute a document analysis job"""
        try:
            # Validate job type
            if job.job_type != "document_analysis":
                return JobResult(
                    job_id=job.job_id,
                    status=JobStatus.FAILED,
                    error=f"Unsupported job type: {job.job_type}",
                )

            # Parse job parameters
            analysis_job = AnalysisJobDefinition.from_dict(job.to_dict())

            logger.info(f"Starting analysis for document {analysis_job.document_id}")

            # Get document chunks
            chunks = await self._get_document_chunks(analysis_job)

            # Get question set
            question_set = await self._get_question_set(analysis_job)

            # Perform analysis
            results = await self._analyze_document(analysis_job, chunks, question_set)

            return JobResult(
                job_id=job.job_id,
                status=JobStatus.COMPLETED,
                result={
                    "analysis_results": results,
                    "document_id": analysis_job.document_id,
                    "question_set_id": analysis_job.question_set_id,
                    "model_used": analysis_job.model_name,
                    "chunk_count": len(chunks),
                },
                progress=1.0,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )

        except Exception as e:
            logger.error(f"Analysis job {job.job_id} failed: {e}")
            return JobResult(
                job_id=job.job_id,
                status=JobStatus.FAILED,
                error=str(e),
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )

    async def _get_document_chunks(self, job: AnalysisJobDefinition):
        """Get document chunks from appropriate source"""
        # Determine document source
        if job.use_search_backend and "search_backend" in self.document_sources:
            source_class = self.document_sources["search_backend"]
            source = source_class()
        else:
            source_class = self.document_sources["local"]
            source = source_class()

        # Get chunks
        chunks = await source.get_chunks(job.document_id, job.parameters.get("configuration", {}))

        logger.info(f"Retrieved {len(chunks)} chunks for document {job.document_id}")
        return chunks

    async def _get_question_set(self, job: AnalysisJobDefinition):
        """Get question set"""
        question_set = self.question_loader.get_question_set(job.question_set_id)
        if not question_set:
            raise ValueError(f"Question set not found: {job.question_set_id}")

        # Filter to selected questions
        filtered_questions = {}
        for question_id in job.selected_questions:
            if question_id in question_set.questions:
                filtered_questions[question_id] = question_set.questions[question_id]

        logger.info(f"Using {len(filtered_questions)} questions from set {job.question_set_id}")
        return filtered_questions

    async def _analyze_document(self, job: AnalysisJobDefinition, chunks, questions):
        """Perform the actual LLM analysis"""
        results = []

        # Configure analyzer
        self.analyzer.current_model = job.model_name

        for question_id, question_data in questions.items():
            try:
                logger.info(f"Analyzing question {question_id}")

                # Find relevant chunks for this question
                relevant_chunks = await self._find_relevant_chunks(chunks, question_data["text"])

                # Perform LLM analysis
                analysis_result = await self._analyze_question(question_data, relevant_chunks, job)

                results.append(
                    {
                        "question_id": question_id,
                        "question_text": question_data["text"],
                        "answer": analysis_result["answer"],
                        "evidence_chunks": analysis_result["evidence_chunks"],
                        "confidence_score": analysis_result.get("confidence", None),
                        "relevant_chunk_count": len(relevant_chunks),
                    }
                )

            except Exception as e:
                logger.error(f"Failed to analyze question {question_id}: {e}")
                results.append(
                    {
                        "question_id": question_id,
                        "question_text": question_data["text"],
                        "answer": f"Analysis failed: {str(e)}",
                        "evidence_chunks": [],
                        "confidence_score": 0.0,
                        "error": str(e),
                    }
                )

        return results

    async def _find_relevant_chunks(self, chunks, question_text):
        """Find chunks relevant to the question"""
        # For now, return all chunks
        # In the future, this could use vector similarity or LLM-based relevance

        # Convert DocumentChunk objects to dict format expected by analyzer
        chunk_dicts = []
        for chunk in chunks:
            chunk_dicts.append(
                {
                    "text": chunk.chunk_text,
                    "metadata": chunk.chunk_metadata,
                    "id": chunk.chunk_id,
                }
            )

        return chunk_dicts

    async def _analyze_question(self, question_data, chunks, job):
        """Analyze a single question with LLM"""
        try:
            # Use existing analyzer logic
            # This is a simplified version - you might want to adapt the analyzer
            # to work with chunk data directly

            question_text = question_data["text"]
            guidelines = question_data.get("guidelines", "")

            # Combine chunks into context
            context = "\n\n".join(
                [f"Chunk {i+1}: {chunk['text']}" for i, chunk in enumerate(chunks[:10])]  # Limit to avoid token limits
            )

            # Create prompt
            prompt = f"""
Question: {question_text}

Guidelines: {guidelines}

Document Context:
{context}

Please provide a comprehensive answer to the question based on the document context.
Include specific references to relevant information found in the chunks.
"""

            # Call LLM (using existing analyzer logic)
            # This is simplified - you'd use the actual analyzer methods
            answer = await self._call_llm(prompt, job.model_name)

            # Prepare evidence chunks
            evidence_chunks = chunks[:5]  # Take top 5 as evidence

            return {
                "answer": answer,
                "evidence_chunks": evidence_chunks,
                "confidence": 0.8,  # Placeholder
            }

        except Exception as e:
            logger.error(f"LLM analysis failed: {e}")
            raise

    async def _call_llm(self, prompt, model_name):
        """Call LLM with prompt"""
        # This should use the existing LLM provider logic from the analyzer
        # For now, return a placeholder

        # You would use:
        # from report_analyst.core.llm_providers import get_llm_provider
        # provider = get_llm_provider(model_name)
        # return await provider.generate(prompt)

        return f"Analysis result for model {model_name} (placeholder)"

    def get_supported_job_types(self) -> List[str]:
        """Return supported job types"""
        return ["document_analysis"]


class ProgressReportingAnalysisHandler(DocumentAnalysisHandler):
    """Enhanced handler with progress reporting for long-running analyses"""

    def __init__(self, progress_callback=None):
        super().__init__()
        self.progress_callback = progress_callback

    async def execute(self, job: JobDefinition) -> JobResult:
        """Execute with progress reporting"""
        if self.progress_callback:
            await self.progress_callback(job.job_id, 0.0, "Starting analysis")

        try:
            # Parse job
            analysis_job = AnalysisJobDefinition.from_dict(job.to_dict())

            if self.progress_callback:
                await self.progress_callback(job.job_id, 0.1, "Getting document chunks")

            # Get chunks
            chunks = await self._get_document_chunks(analysis_job)

            if self.progress_callback:
                await self.progress_callback(job.job_id, 0.2, "Loading question set")

            # Get questions
            questions = await self._get_question_set(analysis_job)

            # Analyze with progress
            results = await self._analyze_with_progress(analysis_job, chunks, questions)

            if self.progress_callback:
                await self.progress_callback(job.job_id, 1.0, "Analysis completed")

            return JobResult(
                job_id=job.job_id,
                status=JobStatus.COMPLETED,
                result={
                    "analysis_results": results,
                    "document_id": analysis_job.document_id,
                    "question_set_id": analysis_job.question_set_id,
                    "model_used": analysis_job.model_name,
                    "chunk_count": len(chunks),
                },
                progress=1.0,
            )

        except Exception as e:
            if self.progress_callback:
                await self.progress_callback(job.job_id, 0.0, f"Analysis failed: {str(e)}")

            return JobResult(job_id=job.job_id, status=JobStatus.FAILED, error=str(e))

    async def _analyze_with_progress(self, job, chunks, questions):
        """Analyze with progress updates"""
        results = []
        total_questions = len(questions)

        for i, (question_id, question_data) in enumerate(questions.items()):
            if self.progress_callback:
                progress = 0.2 + (0.7 * i / total_questions)
                await self.progress_callback(
                    job.job_id,
                    progress,
                    f"Analyzing question {i+1}/{total_questions}: {question_id}",
                )

            # Analyze question
            relevant_chunks = await self._find_relevant_chunks(chunks, question_data["text"])
            analysis_result = await self._analyze_question(question_data, relevant_chunks, job)

            results.append(
                {
                    "question_id": question_id,
                    "question_text": question_data["text"],
                    "answer": analysis_result["answer"],
                    "evidence_chunks": analysis_result["evidence_chunks"],
                    "confidence_score": analysis_result.get("confidence", None),
                }
            )

        return results
