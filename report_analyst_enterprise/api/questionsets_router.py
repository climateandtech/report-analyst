"""Admin routes to install question sets on enterprise instances."""

from __future__ import annotations

import json
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Request

from report_analyst.core.installed_questionsets import list_bundled_set_ids, upsert_installed_question_set
from report_analyst.core.question_loader import get_question_loader
from report_analyst.core.questionset_validation import (
    load_v1_schema,
    parse_body,
    validate_document,
    validate_set_id,
)
from report_analyst_enterprise.api.jwt_auth import (
    allow_builtin_override,
    questionset_admin_configured,
    require_questionset_admin,
)

router = APIRouter(prefix="/admin/question-sets", tags=["admin-question-sets"])


@router.get("/schema")
async def get_questionset_schema(
    _: Dict[str, Any] = Depends(require_questionset_admin),
) -> Dict[str, Any]:
    return load_v1_schema()


@router.post("")
async def install_question_set(
    request: Request,
    set_id: str,
    claims: Dict[str, Any] = Depends(require_questionset_admin),
) -> Dict[str, Any]:
    if not questionset_admin_configured():
        raise HTTPException(status_code=503, detail="questionset admin not configured")
    validate_set_id(set_id)
    bundled = list_bundled_set_ids()
    if set_id in bundled and not allow_builtin_override(claims):
        raise HTTPException(status_code=409, detail="reserved_builtin_id")

    raw = await request.body()
    document, errors = validate_document(parse_body(raw, request.headers.get("content-type")))
    if errors:
        raise HTTPException(status_code=400, detail={"schema_errors": errors})

    upsert_installed_question_set(set_id, document)
    get_question_loader().reload()
    return {
        "set_id": set_id,
        "name": document.get("name"),
        "question_count": len(document.get("questions") or []),
    }


def enterprise_admin_enabled() -> bool:
    import os

    return os.environ.get("REPORT_ANALYST_RUNTIME", "core") == "enterprise"


def mount_if_enterprise(app) -> None:
    if not enterprise_admin_enabled():
        return
    app.include_router(router)