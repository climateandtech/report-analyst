"""Validate and normalize question set documents (v1 JSON Schema)."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple

import jsonschema
import yaml

SCHEMA_VERSION = "v1"
_SCHEMA_PATH = (
    Path(__file__).resolve().parent.parent.parent / "docs" / "contracts" / "questionset-document.v1.schema.json"
)
_SET_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,127}$")

DEFAULT_CLASSIFICATION_SPEC = "exactly one of Yes / No / Unclear / Not disclosed"
DEFAULT_QUANTITY_SPEC = (
    "numeric value with unit (tCO2e, %, EUR/t, etc.) or Unclear / Not disclosed if not reported"
)

_MAX_BODY_BYTES = 10 * 1024 * 1024


def load_v1_schema() -> Dict[str, Any]:
    with _SCHEMA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def validate_set_id(set_id: str) -> None:
    if not _SET_ID_RE.match(set_id):
        raise ValueError(
            "set_id must match ^[a-z0-9][a-z0-9_-]{0,127}$ (lowercase slug for framework id)"
        )


def parse_body(raw: bytes, content_type: str | None) -> Dict[str, Any]:
    if len(raw) > _MAX_BODY_BYTES:
        raise ValueError(f"request body exceeds {_MAX_BODY_BYTES} bytes")
    text = raw.decode("utf-8")
    ctype = (content_type or "").lower()
    if "yaml" in ctype or text.lstrip().startswith(("-", "name:", "questions:")):
        data = yaml.safe_load(text)
    else:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("body must be a JSON object or YAML mapping")
    return data


def _answer_type_line(kind: str, spec: str | None) -> str | None:
    if kind == "narrative":
        return None
    if kind == "classification":
        detail = (spec or "").strip() or DEFAULT_CLASSIFICATION_SPEC
        return f"- ANSWER type: classification — {detail}"
    if kind == "quantity":
        detail = (spec or "").strip() or DEFAULT_QUANTITY_SPEC
        return f"- ANSWER type: quantity — {detail}"
    return None


def normalize_question_item(item: Dict[str, Any]) -> Dict[str, str]:
    qid = str(item["id"]).strip()
    text = str(item["text"])
    guidelines = str(item.get("guidelines") or "")
    answer_type = item.get("answer_type")
    if isinstance(answer_type, dict):
        line = _answer_type_line(str(answer_type.get("kind", "")), answer_type.get("spec"))
        if line:
            if guidelines.strip():
                guidelines = f"{line}\n{guidelines.lstrip()}"
            else:
                guidelines = line
    return {"id": qid, "text": text, "guidelines": guidelines}


def normalize_document(document: Dict[str, Any]) -> Dict[str, Any]:
    """Strip answer_type and return loader-shaped questions list."""
    out = {k: v for k, v in document.items() if k != "questions"}
    questions: List[Dict[str, str]] = []
    for raw in document.get("questions") or []:
        if not isinstance(raw, dict):
            continue
        normalized = normalize_question_item(raw)
        questions.append(
            {
                "id": normalized["id"],
                "text": normalized["text"],
                "guidelines": normalized["guidelines"],
            }
        )
    out["questions"] = questions
    return out


def validate_document(document: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    schema = load_v1_schema()
    validator = jsonschema.Draft7Validator(schema)
    errors = sorted(validator.iter_errors(document), key=lambda e: list(e.path))
    if errors:
        messages = [e.message for e in errors[:20]]
        return document, messages
    seen: set[str] = set()
    for q in document.get("questions") or []:
        if not isinstance(q, dict):
            continue
        qid = str(q.get("id", "")).strip()
        if qid in seen:
            return document, [f"duplicate question id: {qid}"]
        seen.add(qid)
    return normalize_document(document), []


def document_to_question_set(set_id: str, document: Dict[str, Any]):
    from report_analyst.core.question_loader import QuestionSet

    questions = {}
    for idx, q in enumerate(document.get("questions") or []):
        q_id = q.get("id", "")
        if q_id:
            questions[q_id] = {
                "text": q.get("text", ""),
                "guidelines": q.get("guidelines", ""),
            }
    return QuestionSet(
        id=set_id,
        name=document.get("name", set_id),
        description=document.get("description", "") or "",
        shortcut=document.get("shortcut") or set_id,
        questions=questions,
    )