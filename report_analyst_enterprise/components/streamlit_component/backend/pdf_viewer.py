"""
Streamlit custom component backend for PDF viewer with chunks.

This creates a proper Streamlit custom component using the framework-agnostic
web component, which internally uses PDF.js.
"""

import base64
import json
import logging
import socket
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit.components.v1 as components

logger = logging.getLogger(__name__)

# Get the path to the frontend
_COMPONENT_DIR = Path(__file__).parent.parent / "frontend"
_RELEASE_DIR = _COMPONENT_DIR / "build"


def pdf_viewer(
    pdf_path: str,
    chunks_data: Dict[str, List[Dict[str, Any]]],
    questions_data: Dict[str, str],
    selected_question_id: Optional[str] = None,
    show_evidence_only: bool = False,
    highlight_chunk_id: Optional[str] = None,
    key: Optional[str] = None,
    height: int = 800,
) -> Optional[Dict[str, Any]]:
    """
    Render a PDF viewer with chunk annotations in Streamlit using a custom component.
    
    Args:
        pdf_path: Path to PDF file (local file path or URI)
        chunks_data: Dictionary mapping question_id to list of chunk dictionaries.
                    Each chunk should have:
                    - text: str
                    - metadata: dict (with page_number)
                    - is_evidence: bool
                    - similarity_score: float
                    - llm_score: float (optional)
                    - chunk_order: int
        questions_data: Dictionary mapping question_id to question text
        selected_question_id: Optional question ID to highlight initially
        show_evidence_only: Whether to filter to show only evidence chunks
        highlight_chunk_id: Optional chunk ID to highlight (format: "question_id_chunk_order")
        key: Optional key for Streamlit component (for state management)
        height: Height of the component in pixels
        
    Returns:
        Dictionary with event data if chunk was selected, None otherwise
    """
    # Check for dev server availability (prefer dev server for hot reload)
    dev_server_port = None
    dev_server_available = False
    
    # Check common dev server ports (use 3002 for PDF viewer, different from JSON form)
    for port in [3002, 3003, 3004]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result == 0:
                dev_server_port = port
                dev_server_available = True
                break
        except:
            pass
    
    if dev_server_available:
        # Use dev server (hot reload) - need to specify the HTML file
        logger.info(f"Using PDF viewer component from dev server (http://localhost:{dev_server_port})")
        component = components.declare_component(
            "pdf_viewer",
            url=f"http://localhost:{dev_server_port}",
        )
    elif _RELEASE_DIR.exists() and any(_RELEASE_DIR.iterdir()):
        # Use built component - check for PDF viewer subdirectory
        pdf_viewer_dir = _RELEASE_DIR / "pdf-viewer"
        if pdf_viewer_dir.exists() and (pdf_viewer_dir / "index.html").exists():
            # Use PDF viewer specific subdirectory
            logger.info(f"Using PDF viewer component from build: {pdf_viewer_dir}")
            component = components.declare_component(
                "pdf_viewer",
                path=str(pdf_viewer_dir),
            )
        else:
            # Fallback: check for index-pdf-viewer.html and create subdirectory structure
            pdf_viewer_html = _RELEASE_DIR / "index-pdf-viewer.html"
            if pdf_viewer_html.exists():
                logger.warning("PDF viewer build found but not in expected structure. Please rebuild with: npm run build:pdf-viewer")
            # Still try to use the build directory
            logger.info(f"Using PDF viewer component from build (fallback): {_RELEASE_DIR}")
            component = components.declare_component(
                "pdf_viewer",
                path=str(_RELEASE_DIR),
            )
    else:
        # No build and no dev server - show helpful error
        logger.warning(
            f"PDF viewer component not built and dev server not running.\n"
            f"To build the component, run:\n"
            f"  cd {_COMPONENT_DIR}\n"
            f"  npm install\n"
            f"  npm run build:pdf-viewer\n"
            f"Or for development, start the dev server:\n"
            f"  cd {_COMPONENT_DIR}\n"
            f"  npm run dev:pdf-viewer (in a separate terminal)"
        )
        # Still try to declare component - Streamlit will show its own error
        component = components.declare_component(
            "pdf_viewer",
            url="http://localhost:3002",
        )
    
    # Prepare PDF data
    pdf_url = None
    pdf_data = None
    
    # Check if it's a local file or URI
    if pdf_path.startswith("file://") or pdf_path.startswith("http://") or pdf_path.startswith("https://") or pdf_path.startswith("urn:"):
        # It's a URI, pass it directly
        pdf_url = pdf_path
    else:
        # It's a local file path, convert to base64
        try:
            pdf_file = Path(pdf_path)
            if pdf_file.exists():
                with open(pdf_file, 'rb') as f:
                    pdf_bytes = f.read()
                    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                    pdf_data = f"data:application/pdf;base64,{pdf_base64}"
            else:
                logger.warning(f"PDF file not found: {pdf_path}")
                pdf_url = pdf_path  # Fallback: pass as URL
        except Exception as e:
            logger.error(f"Error reading PDF file: {e}")
            pdf_url = pdf_path  # Fallback: pass as URL
    
    # Prepare questions in the format expected by the component
    questions_list = []
    for question_id, question_text in questions_data.items():
        # Get chunks for this question
        question_chunks = chunks_data.get(question_id, [])
        questions_list.append({
            "question_id": question_id,
            "text": question_text,
            "chunks": question_chunks
        })
    
    # Flatten all chunks for the component (it will filter by question)
    all_chunks = []
    for question_id, chunks in chunks_data.items():
        for chunk in chunks:
            # Add question_id to chunk for filtering
            chunk_with_qid = chunk.copy()
            chunk_with_qid["question_id"] = question_id
            all_chunks.append(chunk_with_qid)
    
    # Log chunk data for debugging
    logger.info(f"PDF viewer: Preparing {len(all_chunks)} total chunks for {len(questions_list)} questions")
    if all_chunks:
        logger.debug(f"Sample chunk structure: {all_chunks[0]}")
    else:
        logger.warning(f"No chunks found in chunks_data. Keys: {list(chunks_data.keys())}, Total chunks per question: {[len(chunks) for chunks in chunks_data.values()]}")
    
    # Render component and get result
    result = component(
        pdfUrl=pdf_url,
        pdfData=pdf_data,
        chunks=json.dumps(all_chunks),
        questions=json.dumps(questions_list),
        selectedQuestionId=selected_question_id,
        showEvidenceOnly=show_evidence_only,
        key=key,
        height=height,
    )
    
    # Parse result if it's a string
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except (json.JSONDecodeError, TypeError):
            pass
    
    return result

