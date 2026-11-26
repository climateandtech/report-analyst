"""Validate bundled question sets against v1 JSON Schema."""

from pathlib import Path

import yaml

from report_analyst.core.questionset_validation import validate_document


def test_bundled_questionsets_validate_against_schema():
    base = Path(__file__).resolve().parent.parent / "report_analyst" / "questionsets"
    for path in base.glob("*_questions.yaml"):
        with path.open(encoding="utf-8") as handle:
            doc = yaml.safe_load(handle)
        _, errors = validate_document(doc)
        assert not errors, f"{path.name}: {errors}"