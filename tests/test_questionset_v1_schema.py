"""Validate bundled question sets against v1 JSON Schema."""

from pathlib import Path

import pytest
import yaml

from report_analyst.core import question_loader as ql
from report_analyst.core import questionset_validation as v1
from report_analyst.core.questionset_validation import parse_body, validate_document, validate_set_id


def test_bundled_questionsets_validate_against_schema():
    base = Path(__file__).resolve().parent.parent / "report_analyst" / "questionsets"
    for path in base.glob("*_questions.yaml"):
        with path.open(encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        _, errors = validate_document(doc)
        assert not errors, f"{path.name}: {errors}"


def test_core_init_lazy_cache_manager():
    import report_analyst.core as core

    cls = core.CacheManager
    assert cls.__name__ == "CacheManager"
    with pytest.raises(AttributeError, match="has no attribute"):
        _ = core.NotDefinedInCore


def test_validate_set_id_rejects_invalid_slug():
    with pytest.raises(ValueError, match="set_id"):
        validate_set_id("Bad Id!")


def test_parse_body_rejects_huge_payload():
    with pytest.raises(ValueError, match="exceeds"):
        parse_body(b"x" * (v1._MAX_BODY_BYTES + 1), "application/json")


def test_parse_body_requires_mapping():
    with pytest.raises(ValueError, match="body must"):
        parse_body(b"[]", "application/json")


def test_classification_answer_type_uses_default_spec():
    line = v1._answer_type_line("classification", None)
    assert line is not None
    assert "Yes / No" in line
    assert v1._answer_type_line("unknown", None) is None


def test_validate_document_reports_schema_and_duplicate_ids():
    _, errors = validate_document({"name": "x"})
    assert errors

    doc = {
        "name": "Dup",
        "questions": [
            {"id": "a", "text": "one"},
            {"id": "a", "text": "two"},
        ],
    }
    _, errors = validate_document(doc)
    assert any("duplicate" in e for e in errors)


def test_normalize_answer_types_and_skip_non_dict_questions():
    doc, errors = validate_document(
        {
            "name": "Typed",
            "questions": [
                {"id": "q1", "text": "Qty?", "answer_type": {"kind": "quantity"}},
                {"id": "q2", "text": "Narr?", "answer_type": {"kind": "narrative"}},
            ],
        }
    )
    assert not errors
    assert "ANSWER type: quantity" in doc["questions"][0]["guidelines"]
    assert doc["questions"][1]["guidelines"] == ""

    skipped = v1.normalize_document({"name": "X", "questions": ["bad", {"id": "q", "text": "ok"}]})
    assert len(skipped["questions"]) == 1


def test_question_loader_skips_missing_bundled_dir(monkeypatch):
    monkeypatch.setattr(ql, "bundled_questionsets_dir", lambda: Path("/no-such-questionsets-dir"))
    loader = ql.QuestionSetLoader()
    assert loader._load_bundled_yaml() == {}


def test_list_bundled_set_ids_when_dir_missing(monkeypatch, tmp_path):
    from report_analyst.core import installed_questionsets as iq

    core_dir = tmp_path / "report_analyst" / "core"
    core_dir.mkdir(parents=True)
    fake_module = core_dir / "installed_questionsets.py"
    fake_module.write_text("", encoding="utf-8")
    monkeypatch.setattr(iq, "__file__", str(fake_module))
    assert iq.list_bundled_set_ids() == set()


def test_load_installed_tolerates_bad_documents_json(tmp_path, monkeypatch):
    from sqlalchemy import text

    from report_analyst.core.database_manager import DatabaseManager
    from report_analyst.core.installed_questionsets import (
        load_installed_question_sets,
        upsert_installed_question_set,
    )

    storage = tmp_path / "storage"
    (storage / "cache").mkdir(parents=True)
    monkeypatch.setenv("STORAGE_PATH", str(storage))
    monkeypatch.delenv("DATABASE_URL", raising=False)
    doc = {
        "name": "With docs",
        "questions": [{"id": "q1", "text": "t", "guidelines": ""}],
        "documents": ["Annual report"],
    }
    upsert_installed_question_set("with-docs", doc)
    db = DatabaseManager()
    with db.get_connection() as conn:
        conn.execute(
            text("UPDATE installed_question_sets SET documents_json = :bad WHERE set_id = :id"),
            {"bad": "not-json", "id": "with-docs"},
        )
    loaded = load_installed_question_sets()
    assert loaded["with-docs"].name == "With docs"


def test_question_loader_db_failure_returns_empty(monkeypatch):
    from sqlalchemy.exc import SQLAlchemyError

    def boom():
        raise SQLAlchemyError("db down")

    monkeypatch.setattr(
        "report_analyst.core.installed_questionsets.load_installed_question_sets",
        boom,
    )
    loader = ql.QuestionSetLoader()
    assert loader._load_installed_db() == {}
