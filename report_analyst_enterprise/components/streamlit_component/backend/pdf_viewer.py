"""Streamlit bridge for the PDF viewer with analysis chunks."""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import streamlit.components.v1 as components

_FRONTEND_DIR = Path(__file__).parent.parent / "frontend" / "public"
_COMPONENT = components.declare_component("pdf_viewer", path=str(_FRONTEND_DIR))

_CHUNK_FIELDS = (
    "chunk_order",
    "evidence_order",
    "is_evidence",
    "llm_score",
    "similarity_score",
)


def _pdf_source(pdf_path: str) -> tuple[str | None, str | None]:
    if not pdf_path:
        return None, "No PDF source was provided."

    local_path = Path(pdf_path.removeprefix("file://")).expanduser()
    if not local_path.is_file():
        return None, f"PDF file not found: {local_path}"

    try:
        encoded_pdf = base64.b64encode(local_path.read_bytes()).decode("ascii")
    except OSError as exc:
        return None, f"PDF file could not be read: {exc}"

    return f"data:application/pdf;base64,{encoded_pdf}", None


def _viewer_chunk(chunk: dict[str, Any]) -> dict[str, Any]:
    return {
        "text": chunk.get("text", chunk.get("chunk_text", "")),
        "metadata": chunk.get("metadata", chunk.get("chunk_metadata", {})),
        **{field: chunk[field] for field in _CHUNK_FIELDS if field in chunk},
    }


def pdf_viewer(
    pdf_path: str,
    chunks_data: dict[str, list[dict[str, Any]]],
    questions_data: dict[str, str],
    unmapped_chunks: list[dict[str, Any]] | None = None,
    key: str | None = None,
    height: int = 800,
) -> None:
    pdf_data, source_error = _pdf_source(pdf_path)

    questions = [
        {
            "question_id": question_id,
            "text": question_text,
        }
        for question_id, question_text in questions_data.items()
    ]

    chunks = [
        {**_viewer_chunk(chunk), "question_id": question_id}
        for question_id, question_chunks in chunks_data.items()
        for chunk in question_chunks
    ]
    chunks.extend({**_viewer_chunk(chunk), "question_id": None} for chunk in unmapped_chunks or [])

    _COMPONENT(
        pdfData=pdf_data,
        sourceError=source_error,
        chunks=chunks,
        questions=questions,
        key=key,
        height=height,
    )
