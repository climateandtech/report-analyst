"""
Micro Workflow Engine for Document Analysis

This engine orchestrates the analysis process in clean, separate steps:
1. Chunk Retrieval: Get chunks with vector similarity (no evidence flags)
2. LLM Scoring: Optional reranking with LLM scores
3. Question Analysis: Analyze question and extract evidence
4. Evidence Assignment: Update chunks with evidence flags
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class WorkflowStep(Enum):
    CHUNK_RETRIEVAL = "chunk_retrieval"
    LLM_SCORING = "llm_scoring"
    QUESTION_ANALYSIS = "question_analysis"
    EVIDENCE_ASSIGNMENT = "evidence_assignment"


@dataclass
class WorkflowContext:
    """Context passed between workflow steps"""

    file_path: str
    question_id: str
    question_text: str
    config: Dict[str, Any]
    chunks: List[Dict[str, Any]] = None
    llm_scores: Dict[str, float] = None
    analysis_result: Dict[str, Any] = None
    evidence_chunks: List[str] = None


class WorkflowStep:
    """Base class for workflow steps"""

    def __init__(self, name: str):
        self.name = name

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Execute this workflow step"""
        logger.info(f"[WORKFLOW] Executing step: {self.name}")
        return context

    def validate_input(self, context: WorkflowContext) -> bool:
        """Validate input context for this step"""
        return True

    def validate_output(self, context: WorkflowContext) -> bool:
        """Validate output context for this step"""
        return True


class ChunkRetrievalStep(WorkflowStep):
    """Step 1: Retrieve chunks with vector similarity (no evidence flags)"""

    def __init__(self, cache_manager, vector_manager):
        super().__init__("chunk_retrieval")
        self.cache_manager = cache_manager
        self.vector_manager = vector_manager

    def validate_input(self, context: WorkflowContext) -> bool:
        return context.file_path and context.question_text

    def validate_output(self, context: WorkflowContext) -> bool:
        return context.chunks is not None and len(context.chunks) > 0

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Retrieve chunks with vector similarity only"""
        try:
            # Get chunks from cache or vector store
            chunks = await self.vector_manager.get_similar_chunks(
                query_text=context.question_text,
                file_path=context.file_path,
                top_k=context.config.get("top_k", 5),
                chunk_size=context.config.get("chunk_size"),
                chunk_overlap=context.config.get("chunk_overlap"),
            )

            # Clean chunks - only vector similarity, no evidence flags
            clean_chunks = []
            for i, chunk in enumerate(chunks):
                clean_chunk = {
                    "id": chunk.get("id"),
                    "text": chunk["text"],
                    "chunk_order": i,
                    "similarity_score": chunk.get("similarity_score", chunk.get("score", 0.0)),
                    "llm_score": None,  # Will be set in LLM scoring step if enabled
                    "is_evidence": False,  # Will be set in evidence assignment step
                    "evidence_order": None,
                    "metadata": chunk.get("metadata", {}),
                    "relevance_metadata": {},
                }
                clean_chunks.append(clean_chunk)

            context.chunks = clean_chunks
            logger.info(f"[WORKFLOW] Retrieved {len(clean_chunks)} chunks with vector similarity")

            return context

        except Exception as e:
            logger.error(f"[WORKFLOW] Error in chunk retrieval: {str(e)}")
            raise


class LLMScoringStep(WorkflowStep):
    """Step 2: Optional LLM reranking and scoring"""

    def __init__(self, llm_manager):
        super().__init__("llm_scoring")
        self.llm_manager = llm_manager

    def validate_input(self, context: WorkflowContext) -> bool:
        return context.chunks is not None and len(context.chunks) > 0

    def validate_output(self, context: WorkflowContext) -> bool:
        return context.llm_scores is not None

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Apply LLM scoring if enabled"""
        use_llm_scoring = context.config.get("use_llm_scoring", False)

        if not use_llm_scoring:
            logger.info("[WORKFLOW] LLM scoring disabled, skipping")
            context.llm_scores = {}
            return context

        try:
            # Score chunks with LLM
            llm_scores = await self.llm_manager.score_chunks(question=context.question_text, chunks=context.chunks)

            # Update chunks with LLM scores
            for chunk in context.chunks:
                chunk_id = chunk.get("id")
                if chunk_id in llm_scores:
                    chunk["llm_score"] = llm_scores[chunk_id]
                else:
                    chunk["llm_score"] = 0.0

            context.llm_scores = llm_scores
            logger.info(f"[WORKFLOW] Applied LLM scoring to {len(llm_scores)} chunks")

            return context

        except Exception as e:
            logger.error(f"[WORKFLOW] Error in LLM scoring: {str(e)}")
            raise


class QuestionAnalysisStep(WorkflowStep):
    """Step 3: Analyze question and extract evidence"""

    def __init__(self, llm_manager):
        super().__init__("question_analysis")
        self.llm_manager = llm_manager

    def validate_input(self, context: WorkflowContext) -> bool:
        return context.chunks is not None and len(context.chunks) > 0

    def validate_output(self, context: WorkflowContext) -> bool:
        return context.analysis_result is not None and context.evidence_chunks is not None

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Analyze question and extract evidence"""
        try:
            # Sort chunks by appropriate score
            use_llm_scoring = context.config.get("use_llm_scoring", False)
            if use_llm_scoring and context.llm_scores:
                # Sort by LLM score if available
                sorted_chunks = sorted(context.chunks, key=lambda x: x.get("llm_score", 0.0), reverse=True)
            else:
                # Sort by vector similarity
                sorted_chunks = sorted(
                    context.chunks,
                    key=lambda x: x.get("similarity_score", 0.0),
                    reverse=True,
                )

            # Analyze question with LLM
            analysis_result = await self.llm_manager.analyze_question(question=context.question_text, chunks=sorted_chunks)

            # Extract evidence chunk IDs
            evidence_chunks = analysis_result.get("evidence_chunks", [])

            context.analysis_result = analysis_result
            context.evidence_chunks = evidence_chunks
            logger.info(f"[WORKFLOW] Question analysis complete, found {len(evidence_chunks)} evidence chunks")

            return context

        except Exception as e:
            logger.error(f"[WORKFLOW] Error in question analysis: {str(e)}")
            raise


class EvidenceAssignmentStep(WorkflowStep):
    """Step 4: Assign evidence flags to chunks"""

    def __init__(self):
        super().__init__("evidence_assignment")

    def validate_input(self, context: WorkflowContext) -> bool:
        return context.chunks is not None and context.evidence_chunks is not None and context.analysis_result is not None

    def validate_output(self, context: WorkflowContext) -> bool:
        return context.chunks is not None

    async def execute(self, context: WorkflowContext) -> WorkflowContext:
        """Assign evidence flags to chunks"""
        try:
            # Create mapping of chunk IDs to evidence order
            evidence_mapping = {}
            for i, chunk_id in enumerate(context.evidence_chunks):
                evidence_mapping[chunk_id] = i + 1

            # Update chunks with evidence flags
            for chunk in context.chunks:
                chunk_id = chunk.get("id")
                if chunk_id in evidence_mapping:
                    chunk["is_evidence"] = True
                    chunk["evidence_order"] = evidence_mapping[chunk_id]
                else:
                    chunk["is_evidence"] = False
                    chunk["evidence_order"] = None

            logger.info(f"[WORKFLOW] Assigned evidence flags to {len(evidence_mapping)} chunks")

            return context

        except Exception as e:
            logger.error(f"[WORKFLOW] Error in evidence assignment: {str(e)}")
            raise


class WorkflowEngine:
    """Workflow engine for orchestrating document analysis steps"""

    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        # TODO: Add vector_manager and llm_manager when available
        self.vector_manager = None
        self.llm_manager = None

        # Initialize workflow steps (placeholder for now)
        self.steps = []

        logger.info("[WORKFLOW] Initialized workflow engine (cache-only mode)")

    async def execute_workflow(
        self,
        file_path: str,
        question_id: str,
        question_text: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute the full workflow for a question"""
        logger.info(f"[WORKFLOW] Starting workflow for question: {question_id}")

        # For now, just return cached results if available
        cached_result = self.cache_manager.get_analysis(file_path=file_path, config=config, question_ids=[question_id])

        if cached_result and question_id in cached_result:
            logger.info(f"[WORKFLOW] Found cached result for {question_id}")
            return cached_result[question_id]
        else:
            logger.warning(f"[WORKFLOW] No cached result for {question_id}, full workflow not implemented")
            return {
                "error": "Full workflow not implemented - only cached results available",
                "question_id": question_id,
                "chunks": [],
            }

    def get_workflow_status(self) -> Dict[str, Any]:
        """Get current workflow status"""
        return {
            "engine_status": "cache_only",
            "vector_manager": "not_available",
            "llm_manager": "not_available",
            "steps_configured": len(self.steps),
        }
