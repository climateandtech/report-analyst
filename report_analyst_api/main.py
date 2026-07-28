"""
Report Analyst API

FastAPI application for document analysis.
"""

# Load .env first so OPENBLAS_NUM_THREADS=1 (and other vars) are set before any NumPy/OpenBLAS import
import os

from dotenv import load_dotenv

load_dotenv()
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

import logging
import os
import shutil

# Add the parent directory to the path to import from report_analyst
import sys
import tempfile
from typing import Any, Dict, List, Optional

from fastapi import BackgroundTasks, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# API wraps the same services the Streamlit app uses (question_loader, DocumentAnalyzer)
from report_analyst.core.service import (
    get_analysis_keys_for_api,
    get_consolidated_results_for_api,
    get_document_analyzer,
    get_question_sets_for_api,
    get_questions_for_api,
    get_reports_for_api,
)
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


@app.on_event("startup")
async def startup_event():
    """Initialize the application. Analyzer is created on first /analyze or /analyze-async request."""
    logger.info("Starting Report Analyst API")


@app.get("/health", response_model=HealthResponse, operation_id="health_check")
async def health_check():
    """Health check endpoint"""
    return HealthResponse(status="healthy", version="0.1.0")


@app.get(
    "/question-sets",
    response_model=List[QuestionSet],
    operation_id="get_question_sets",
    responses={
        200: {
            "links": {
                "analysisKeysFromQuestionSets": {
                    "operationId": "get_analysis_keys",
                    "description": "Question sets can be combined with reports to build analysis key pairs.",
                }
            }
        }
    },
)
async def get_question_sets():
    """Get all available question sets (full list, no limit; same source as Streamlit app)."""
    try:
        items = get_question_sets_for_api()
        return [QuestionSet(id=x["id"], name=x["name"], description=x["description"]) for x in items]
    except Exception as e:
        logger.error(f"Error getting question sets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/questions/{question_set_id}", operation_id="get_questions")
async def get_questions(question_set_id: str):
    """Get questions for a specific question set (same service as Streamlit app)."""
    try:
        questions = get_questions_for_api(question_set_id)
        return {"question_set": question_set_id, "questions": questions}
    except Exception as e:
        logger.error(f"Error loading questions for {question_set_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/reports",
    operation_id="get_reports",
    responses={
        200: {
            "links": {
                "analysisKeysFromReports": {
                    "operationId": "get_analysis_keys",
                    "description": "Reports can be combined with question sets to build analysis key pairs.",
                }
            }
        }
    },
)
async def get_reports(question_set_id: Optional[str] = None):
    """List reports. When question_set_id is provided, returns only reports with cached rows for that set."""
    try:
        return get_reports_for_api(question_set_id=question_set_id)
    except Exception as e:
        logger.error(f"Error listing reports: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get(
    "/analysis-keys",
    operation_id="get_analysis_keys",
    responses={
        200: {
            "links": {
                "consolidatedResults": {
                    "operationId": "get_consolidated_results",
                    "description": "Analysis keys drive selector choices for consolidated results.",
                }
            }
        }
    },
)
async def get_analysis_keys():
    """List all (report_id, report_name, question_set_id) pairs (report × question set)."""
    try:
        return get_analysis_keys_for_api()
    except Exception as e:
        logger.error(f"Error listing analysis keys: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/consolidated-results", operation_id="get_consolidated_results")
async def get_consolidated_results(
    question_set_id: Optional[str] = None,
    report_id: Optional[str] = None,
):
    """List cached consolidated analysis rows, optionally filtered by selectors."""
    try:
        return get_consolidated_results_for_api(
            question_set_id=question_set_id,
            report_id=report_id,
        )
    except Exception as e:
        logger.error(f"Error listing consolidated results: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/models", operation_id="get_models")
async def get_models():
    """List available LLM models for analysis."""
    return [
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini"},
        {"id": "gpt-4o", "name": "GPT-4o"},
        {"id": "gpt-4", "name": "GPT-4"},
        {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
    ]


def _get_temp_dir() -> str:
    """Report temp dir for uploads and report_path (same as service.get_report_temp_dir)."""
    from report_analyst.core.service import get_report_temp_dir

    return str(get_report_temp_dir())


def _resolve_analyze_path(file: UploadFile | None, report_path: str | None) -> tuple[str, str]:
    """Resolve path and filename for analyze: either from uploaded file or report_path (allowed dirs)."""
    if file and file.filename:
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            shutil.copyfileobj(file.file, tmp_file)
            return tmp_file.name, file.filename
    if report_path:
        # Allow file:// URL or bare path; restrict to temp dir
        path = report_path.replace("file://", "").strip()
        if not path:
            raise HTTPException(status_code=400, detail="report_path is empty")
        temp_dir = _get_temp_dir()
        if not os.path.isdir(temp_dir):
            raise HTTPException(status_code=400, detail=f"Temp dir not found: {temp_dir}")
        resolved = os.path.realpath(path)
        if not resolved.startswith(os.path.realpath(temp_dir)):
            raise HTTPException(status_code=400, detail="report_path must be under temp directory")
        if not os.path.isfile(resolved) or not resolved.endswith(".pdf"):
            raise HTTPException(status_code=400, detail="report_path must be an existing PDF file")
        return resolved, os.path.basename(resolved)
    raise HTTPException(status_code=400, detail="Either file or report_path is required")


@app.post("/analyze", response_model=AnalysisResponse, operation_id="analyze_document")
async def analyze_document(
    file: UploadFile | None = File(None),
    report_path: str | None = Form(None),
    question_set: str = "tcfd",
    chunk_size: int = 500,
    chunk_overlap: int = 20,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
):
    """Analyze a document with the specified question set (upload file or report_path)."""
    try:
        tmp_path, filename = _resolve_analyze_path(file, report_path)
        delete_after = not (report_path and os.path.isfile(tmp_path))

        try:
            # Initialize analyzer
            analyzer = get_document_analyzer()

            questions = get_questions_for_api(question_set)
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
                filename=filename,
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
            if delete_after and os.path.exists(tmp_path):
                os.unlink(tmp_path)

    except Exception as e:
        logger.error(f"Error analyzing document: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def _sanitize_filename(name: str) -> str:
    """Keep safe filename characters for saving async uploads."""
    if not name or not name.endswith(".pdf"):
        return "document.pdf"
    base = os.path.basename(name)
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in base)
    return safe or "document.pdf"


@app.post("/analyze-async", operation_id="start_async_analysis")
async def analyze_document_async(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    question_set: str = "tcfd",
    chunk_size: int = 500,
    chunk_overlap: int = 20,
    top_k: int = 5,
    model: str = "gpt-4o-mini",
):
    """Start asynchronous document analysis. File is saved to report temp dir and results are persisted to cache."""
    try:
        import uuid

        task_id = str(uuid.uuid4())
        temp_dir = _get_temp_dir()
        os.makedirs(temp_dir, exist_ok=True)
        safe_name = _sanitize_filename(file.filename or "document.pdf")
        # Unique path so concurrent uploads do not clash; file stays for /reports and consolidated-results
        stem = os.path.splitext(safe_name)[0]
        dest_name = f"{stem}_{task_id[:8]}.pdf"
        tmp_path = os.path.join(temp_dir, dest_name)
        with open(tmp_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        background_tasks.add_task(
            process_document_async,
            task_id,
            tmp_path,
            file.filename or dest_name,
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
    """Process document in background. Analyzer persists to cache; file is left in temp for /reports."""
    try:
        logger.info(f"Starting async processing for task {task_id}")

        analyzer = get_document_analyzer()
        questions = get_questions_for_api(question_set)
        analyzer.analyze_document(
            file_path=file_path,
            questions=questions,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            top_k=top_k,
            model=model,
        )

        logger.info(f"Completed async processing for task {task_id}; results in cache, file at {file_path}")
    except Exception as e:
        logger.error(f"Error in async processing for task {task_id}: {e}")
        if os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except OSError:
                pass


if __name__ == "__main__":
    import uvicorn

    # Avoid OpenBLAS stack overflow (SIGSEGV in gemm_thread_n) on macOS/ARM
    if "OPENBLAS_NUM_THREADS" not in os.environ:
        os.environ["OPENBLAS_NUM_THREADS"] = "1"

    # Default 8001 so it doesn't conflict with search backend on 8000; frontend proxies /report-analyst-api here
    port = int(os.environ.get("PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)
