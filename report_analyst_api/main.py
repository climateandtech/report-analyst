"""
Report Analyst API

FastAPI application for document analysis.
"""

import logging
import os
import shutil

# Add the parent directory to the path to import from report_analyst
import sys
import tempfile
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from report_analyst.core.analyzer import DocumentAnalyzer
from report_analyst.core.question_loader import get_question_loader
from report_analyst_api.schemas import (
    AnalysisRequest,
    AnalysisResponse,
    HealthResponse,
    QuestionSet,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Report Analyst API",
    description="Document analysis API with multiple question frameworks",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global analyzer instance
analyzer = None


def get_analyzer():
    """Get or create the document analyzer instance"""
    global analyzer
    if analyzer is None:
        analyzer = DocumentAnalyzer()
    return analyzer


@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    logger.info("Starting Report Analyst API")
    # Initialize analyzer
    get_analyzer()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version="0.1.0")


@app.get("/question-sets", response_model=List[QuestionSet])
async def get_question_sets():
    """Get available question sets"""
    try:
        # Get question sets dynamically from question loader
        question_loader_instance = get_question_loader()
        question_sets_data = question_loader_instance.get_question_sets()

        # Convert to API response format
        question_sets = []
        for qset in question_sets_data.values():
            question_sets.append(
                QuestionSet(id=qset.id, name=qset.name, description=qset.description)
            )

        return question_sets
    except Exception as e:
        logger.error(f"Error getting question sets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questions/{question_set_id}")
async def get_questions(question_set_id: str):
    """Get questions for a specific question set"""
    try:
        question_loader = get_question_loader()
        questions = question_loader.get_questions(question_set_id)
        return {"question_set": question_set_id, "questions": questions}
    except Exception as e:
        logger.error(f"Error loading questions for {question_set_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_document(
    file: UploadFile = File(...),
    question_set: str = "tcfd",
    chunk_size: int = 500,
    chunk_overlap: int = 20,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
):
    """Analyze a document with the specified question set"""
    try:
        # Validate file type
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name

        try:
            # Initialize analyzer
            analyzer = get_analyzer()

            # Load questions
            question_loader = get_question_loader()
            questions = question_loader.get_questions(question_set)

            # Analyze document
            results = analyzer.analyze_document(
                file_path=tmp_path,
                questions=questions,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                top_k=top_k,
                model=model,
            )

            # Format response
            response = AnalysisResponse(
                filename=file.filename,
                question_set=question_set,
                results=results,
                configuration={
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "top_k": top_k,
                    "model": model,
                },
            )

            return response

        finally:
            # Clean up temporary file
            os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error analyzing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/analyze-async")
async def analyze_document_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    question_set: str = "tcfd",
    chunk_size: int = 500,
    chunk_overlap: int = 20,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
):
    """Start asynchronous document analysis"""
    try:
        # Generate task ID
        import uuid

        task_id = str(uuid.uuid4())

        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            tmp_path = tmp_file.name

        # Add background task
        background_tasks.add_task(
            process_document_async,
            task_id,
            tmp_path,
            file.filename,
            question_set,
            chunk_size,
            chunk_overlap,
            top_k,
            model,
        )

        return {"task_id": task_id, "status": "processing"}

    except Exception as e:
        logger.error(f"Error starting async analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


async def process_document_async(
    task_id: str,
    file_path: str,
    filename: str,
    question_set: str,
    chunk_size: int,
    chunk_overlap: int,
    top_k: int,
    model: str,
):
    """Process document in background"""
    try:
        logger.info(f"Starting async processing for task {task_id}")

        # Initialize analyzer
        analyzer = get_analyzer()

        # Load questions
        question_loader = get_question_loader()
        questions = question_loader.get_questions(question_set)

        # Analyze document
        results = analyzer.analyze_document(
            file_path=file_path,
            questions=questions,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            model=model,
        )

        logger.info(f"Completed async processing for task {task_id}")

        # In a real implementation, you would store results in a database
        # or cache for later retrieval

    except Exception as e:
        logger.error(f"Error in async processing for task {task_id}: {e}")
    finally:
        # Clean up temporary file
        if os.path.exists(file_path):
            os.unlink(file_path)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
