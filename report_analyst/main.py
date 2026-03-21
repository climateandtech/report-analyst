import logging
import pdb
from pathlib import Path

import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .core.analyzer import DocumentAnalyzer
from .core.document_processor import DocumentProcessor
from .models.requests import AnalysisRequest, QuestionRequest
from .models.responses import AnalysisResponse, QuestionResponse

app = FastAPI(
    title="Report Analyst",
    description="A modern document analysis API for corporate reports",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize core components
document_processor = DocumentProcessor()
document_analyzer = DocumentAnalyzer()

logger = logging.getLogger(__name__)


@app.post("/upload", response_model=dict)
async def upload_document(file: UploadFile = File(...)):
    """Upload a document for analysis"""
    try:
        # Read the content before processing
        content = await file.read()
        # Reset the file pointer for subsequent reads
        await file.seek(0)

        # Debug log to see what we're getting
        logger.debug(f"File size: {len(content)} bytes")
        logger.debug(f"Content starts with: {content[:50]}")

        result = await document_processor.process_upload(file)
        return {
            "message": "Document uploaded successfully",
            "document_id": result["document_id"],
        }
    except Exception as e:
        logger.error(f"Error uploading document: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_document(request: AnalysisRequest):
    """Analyze a document with specified parameters"""
    try:
        result = await document_analyzer.analyze(request.document_id, request.analysis_type)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """Ask a question about a document"""
    try:
        result = await document_analyzer.ask_question(request.document_id, request.question, request.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
