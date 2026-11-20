"""Public library API for embedding Open Sustainability Analyst in your own apps.

The Streamlit UI and REST API both sit on :class:`~report_analyst.core.analyzer.DocumentAnalyzer`.
Use this module when you want grounded answers (answer + evidence + gaps + sources)
inside a custom interface without depending on Streamlit.
"""

from __future__ import annotations

import logging
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

import yaml

logger = logging.getLogger(__name__)

QuestionsInput = Union[str, Path, Dict[str, Dict[str, Any]]]


@dataclass
class GroundedAnswer:
    """One question result with evidence suitable for a custom UI or downstream use."""

    question_id: str
    question_text: str
    answer: str
    score: float = 0.0
    evidence: List[Any] = field(default_factory=list)
    gaps: List[Any] = field(default_factory=list)
    sources: List[Any] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize for JSON APIs and product brief builders."""
        return asdict(self)


def _ensure_openblas_threads() -> None:
    if "OPENBLAS_NUM_THREADS" not in os.environ:
        os.environ["OPENBLAS_NUM_THREADS"] = "1"


def _resolve_pdf_path(pdf_path: Union[str, Path]) -> Path:
    """Validate and normalize a PDF path (sync helper for async callers)."""
    path = Path(pdf_path).expanduser().resolve()
    if not path.is_file() or path.suffix.lower() != ".pdf":
        raise FileNotFoundError(f"Expected an existing PDF file, got: {pdf_path!r}")
    return path


def _question_number(question_id: str, fallback: int) -> int:
    if "_" in question_id:
        suffix = question_id.rsplit("_", 1)[-1]
        if suffix.isdigit():
            return int(suffix)
    return fallback


def _normalize_questions(
    questions: Dict[str, Dict[str, Any]],
) -> Dict[str, Dict[str, Any]]:
    normalized: Dict[str, Dict[str, Any]] = {}
    for index, (question_id, payload) in enumerate(questions.items(), start=1):
        text = str(payload.get("text") or "")
        guidelines = str(payload.get("guidelines") or "")
        number = _question_number(question_id, index)
        normalized[question_id] = {
            "id": question_id,
            "text": text,
            "guidelines": guidelines,
            "number": number,
        }
    return normalized


def load_questions_from_yaml(path: Union[str, Path]) -> Dict[str, Dict[str, Any]]:
    """Load a question-set YAML (same shape as ``report_analyst/questionsets/*``)."""
    yaml_path = Path(path)
    with yaml_path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    questions: Dict[str, Dict[str, Any]] = {}
    for item in config.get("questions") or []:
        question_id = str(item.get("id") or "").strip()
        if not question_id:
            continue
        questions[question_id] = {
            "text": item.get("text", ""),
            "guidelines": item.get("guidelines", ""),
        }
    return _normalize_questions(questions)


def resolve_questions(
    questions: QuestionsInput,
    *,
    question_set_id: Optional[str] = None,
) -> tuple[Dict[str, Dict[str, Any]], str]:
    """Resolve questions from a built-in set id, YAML path, or in-memory dict."""
    if isinstance(questions, dict):
        resolved = _normalize_questions(questions)
        set_id = question_set_id or "custom"
        return resolved, set_id

    path = Path(questions)
    if path.suffix.lower() in {".yaml", ".yml"} and path.exists():
        resolved = load_questions_from_yaml(path)
        stem = path.stem.replace("_questions", "")
        set_id = question_set_id or stem
        return resolved, set_id

    set_id = str(questions)
    from report_analyst.core.question_loader import get_question_loader

    loaded = get_question_loader().get_questions(set_id)
    if not loaded:
        raise ValueError(f"Unknown question set or missing YAML: {questions!r}")
    return _normalize_questions(loaded), question_set_id or set_id


def _extract_grounded(
    *,
    question_id: str,
    question_text: str,
    payload: Dict[str, Any],
) -> GroundedAnswer:
    nested = payload.get("result") if isinstance(payload.get("result"), dict) else payload
    answer = str(nested.get("ANSWER") or nested.get("answer") or nested.get("analysis") or "")
    score_raw = nested.get("SCORE", nested.get("score", nested.get("confidence_score", 0)))
    try:
        score = float(score_raw or 0)
    except (TypeError, ValueError):
        score = 0.0
    evidence = nested.get("EVIDENCE") or nested.get("evidence") or []
    gaps = nested.get("GAPS") or nested.get("gaps") or []
    sources = nested.get("SOURCES") or nested.get("sources") or []
    if not isinstance(evidence, list):
        evidence = [evidence]
    if not isinstance(gaps, list):
        gaps = [gaps]
    if not isinstance(sources, list):
        sources = [sources]
    return GroundedAnswer(
        question_id=question_id,
        question_text=question_text,
        answer=answer,
        score=score,
        evidence=evidence,
        gaps=gaps,
        sources=sources,
        raw=dict(nested),
    )


async def analyze_report(
    pdf_path: Union[str, Path],
    questions: QuestionsInput,
    *,
    question_set_id: Optional[str] = None,
    question_ids: Optional[Sequence[str]] = None,
    chunk_size: int = 500,
    chunk_overlap: int = 20,
    top_k: int = 5,
    model: Optional[str] = None,
    use_llm_scoring: bool = False,
    force_recompute: bool = False,
) -> List[GroundedAnswer]:
    """Analyze a PDF and return grounded answers for a custom product UI.

    Args:
        pdf_path: Path to a local sustainability-report PDF.
        questions: Built-in question-set id (e.g. ``\"tcfd\"``), path to a YAML
            question file, or an in-memory ``{question_id: {text, guidelines}}`` map.
        question_set_id: Optional override for the set id stored on the analyzer.
        question_ids: Subset of question ids; defaults to all resolved questions.
        chunk_size: Chunk size passed to the analyzer.
        chunk_overlap: Chunk overlap passed to the analyzer.
        top_k: Retrieval depth per question.
        model: Optional LLM model name; defaults to analyzer / env default.
        use_llm_scoring: Enable LLM chunk scoring (same flag as Streamlit).
        force_recompute: Bypass cached answers when true.

    Returns:
        Ordered list of :class:`GroundedAnswer` rows (answer + evidence + gaps).
    """
    _ensure_openblas_threads()
    path = _resolve_pdf_path(pdf_path)

    resolved_questions, set_id = resolve_questions(questions, question_set_id=question_set_id)
    selected_ids = list(question_ids) if question_ids else list(resolved_questions.keys())
    missing = [qid for qid in selected_ids if qid not in resolved_questions]
    if missing:
        raise ValueError(f"Unknown question ids for set {set_id!r}: {missing}")
    if not selected_ids:
        raise ValueError("No questions selected for analysis")

    from report_analyst.core.analyzer import DocumentAnalyzer

    analyzer = DocumentAnalyzer()
    analyzer.questions = resolved_questions
    analyzer.question_set = set_id
    analyzer.update_parameters(chunk_size, chunk_overlap, top_k)
    if model:
        analyzer.default_model = model

    selected_numbers = [resolved_questions[qid]["number"] for qid in selected_ids]
    id_by_number = {resolved_questions[qid]["number"]: qid for qid in selected_ids}
    text_by_id = {qid: resolved_questions[qid]["text"] for qid in selected_ids}

    grounded: List[GroundedAnswer] = []
    async for event in analyzer.process_document(
        str(path),
        selected_numbers,
        use_llm_scoring=use_llm_scoring,
        force_recompute=force_recompute,
    ):
        if not isinstance(event, dict):
            continue
        if event.get("error"):
            raise RuntimeError(str(event["error"]))
        if "status" in event and "question_number" not in event and "result" not in event:
            logger.info("[library] %s", event["status"])
            continue
        question_number = event.get("question_number")
        if question_number is None:
            continue
        question_id = str(event.get("question_id") or id_by_number.get(question_number) or f"{set_id}_{question_number}")
        grounded.append(
            _extract_grounded(
                question_id=question_id,
                question_text=text_by_id.get(question_id, ""),
                payload=event,
            )
        )
    return grounded


def analyze_report_sync(*args: Any, **kwargs: Any) -> List[GroundedAnswer]:
    """Synchronous wrapper around :func:`analyze_report` for simple scripts."""
    import asyncio

    return asyncio.run(analyze_report(*args, **kwargs))


def build_topic_brief(answers: Sequence[GroundedAnswer], *, topic: str) -> Dict[str, Any]:
    """Turn grounded answers into a structured brief a host app can render or export.

    This is the “use the grounded data” step after analysis: your UI keeps its own
    look-and-feel, while answers remain tied to evidence and gaps from the report.
    """
    findings = []
    for item in answers:
        findings.append(
            {
                "question_id": item.question_id,
                "question": item.question_text,
                "answer": item.answer,
                "confidence": item.score,
                "evidence": item.evidence,
                "gaps": item.gaps,
                "sources": item.sources,
            }
        )
    covered = sum(1 for item in answers if (item.answer or "").strip())
    with_evidence = sum(1 for item in answers if item.evidence)
    return {
        "topic": topic,
        "question_count": len(answers),
        "answered_count": covered,
        "evidence_backed_count": with_evidence,
        "findings": findings,
    }
