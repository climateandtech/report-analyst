"""Persistence for API-installed question sets."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from sqlalchemy import delete, insert, select, text, update

from report_analyst.core.database_manager import DatabaseManager
from report_analyst.core.database_schema import (
    installed_question_set_items,
    installed_question_sets,
    metadata,
    questionset_admin_jti,
)
from report_analyst.core.question_loader import QuestionSet
from report_analyst.core.questionset_validation import SCHEMA_VERSION, document_to_question_set

logger = logging.getLogger(__name__)


def _database_manager() -> DatabaseManager:
    return DatabaseManager()


def ensure_tables() -> None:
    engine = _database_manager().get_engine()
    metadata.create_all(
        engine,
        tables=[
            installed_question_sets,
            installed_question_set_items,
            questionset_admin_jti,
        ],
    )


def list_bundled_set_ids() -> set[str]:
    from pathlib import Path

    base = Path(__file__).resolve().parent.parent / "questionsets"
    if not base.is_dir():
        return set()
    ids = set()
    for path in base.glob("*_questions.yaml"):
        ids.add(path.stem.replace("_questions", ""))
    return ids


def load_installed_question_sets() -> Dict[str, QuestionSet]:
    ensure_tables()
    db = _database_manager()
    result: Dict[str, QuestionSet] = {}
    with db.get_connection() as conn:
        sets = conn.execute(select(installed_question_sets)).fetchall()
        for row in sets:
            set_id = row.set_id
            items = conn.execute(
                select(installed_question_set_items)
                .where(installed_question_set_items.c.set_id == set_id)
                .order_by(installed_question_set_items.c.sort_order)
            ).fetchall()
            document = {
                "name": row.name,
                "description": row.description or "",
                "shortcut": row.shortcut or set_id,
                "analysis_guidelines": row.analysis_guidelines or "",
                "questions": [{"id": i.question_id, "text": i.text, "guidelines": i.guidelines or ""} for i in items],
            }
            if row.documents_json:
                try:
                    document["documents"] = json.loads(row.documents_json)
                except json.JSONDecodeError:
                    pass
            result[set_id] = document_to_question_set(set_id, document)
    return result


def upsert_installed_question_set(set_id: str, document: Dict[str, Any]) -> None:
    ensure_tables()
    db = _database_manager()
    now = datetime.now()
    docs_json = None
    if document.get("documents"):
        docs_json = json.dumps(document["documents"])
    with db.get_connection() as conn:
        conn.execute(delete(installed_question_set_items).where(installed_question_set_items.c.set_id == set_id))
        existing = conn.execute(select(installed_question_sets).where(installed_question_sets.c.set_id == set_id)).fetchone()
        if existing:
            conn.execute(
                update(installed_question_sets)
                .where(installed_question_sets.c.set_id == set_id)
                .values(
                    name=document["name"],
                    description=document.get("description") or "",
                    shortcut=document.get("shortcut") or set_id,
                    documents_json=docs_json,
                    analysis_guidelines=document.get("analysis_guidelines"),
                    schema_version=SCHEMA_VERSION,
                    updated_at=now,
                )
            )
        else:
            conn.execute(
                insert(installed_question_sets).values(
                    set_id=set_id,
                    name=document["name"],
                    description=document.get("description") or "",
                    shortcut=document.get("shortcut") or set_id,
                    documents_json=docs_json,
                    analysis_guidelines=document.get("analysis_guidelines"),
                    schema_version=SCHEMA_VERSION,
                    installed_at=now,
                    updated_at=now,
                )
            )
        for order, q in enumerate(document.get("questions") or []):
            conn.execute(
                insert(installed_question_set_items).values(
                    set_id=set_id,
                    question_id=q["id"],
                    text=q["text"],
                    guidelines=q.get("guidelines") or "",
                    sort_order=order,
                )
            )


def record_jti(jti: str, expires_at: datetime) -> bool:
    """Return False if jti already used."""
    ensure_tables()
    db = _database_manager()
    with db.get_connection() as conn:
        _prune_expired_jtis(conn)
        existing = conn.execute(select(questionset_admin_jti).where(questionset_admin_jti.c.jti == jti)).fetchone()
        if existing:
            return False
        conn.execute(insert(questionset_admin_jti).values(jti=jti, expires_at=expires_at))
        return True


def _utc_naive_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _prune_expired_jtis(conn) -> None:
    conn.execute(
        text("DELETE FROM questionset_admin_jti WHERE expires_at < :now"),
        {"now": _utc_naive_now()},
    )
