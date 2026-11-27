"""Catch Coolify/CI gaps: image layout and dependency install must match the repo."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCKERFILE = REPO_ROOT / "Dockerfile"
SCHEMA = REPO_ROOT / "docs" / "contracts" / "questionset-document.v1.schema.json"

# Paths the unified Dockerfile must COPY for enterprise admin API + runtime.
_REQUIRED_COPY_PREFIXES = (
    "report_analyst/",
    "report_analyst_enterprise/",
    "report_analyst_api/",
    "docs/contracts/",
)


def _dockerfile_copy_sources(text: str) -> list[str]:
    sources: list[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("COPY "):
            continue
        parts = line.split()
        if len(parts) < 3:
            continue
        sources.append(parts[1].rstrip("/"))
    return sources


def test_questionset_schema_present_in_repo():
    assert SCHEMA.is_file(), "docs/contracts/questionset-document.v1.schema.json missing"


def test_dockerfile_copies_contracts_for_admin_api():
    assert DOCKERFILE.is_file()
    text = DOCKERFILE.read_text(encoding="utf-8")
    copies = _dockerfile_copy_sources(text)
    assert any(
        c.startswith("docs/contracts") for c in copies
    ), "Dockerfile must COPY docs/contracts/ — load_v1_schema() breaks in production image"


def test_dockerfile_copies_enterprise_runtime():
    text = DOCKERFILE.read_text(encoding="utf-8")
    copies = _dockerfile_copy_sources(text)
    for prefix in _REQUIRED_COPY_PREFIXES:
        assert any(c.startswith(prefix.rstrip("/")) for c in copies), f"Dockerfile missing COPY {prefix}"


def test_pip_requirements_files_exist():
    for rel in (
        "requirements.txt",
        "report_analyst_enterprise/requirements.txt",
        "report_analyst_api/requirements.txt",
        "report_analyst_search_backend/requirements.txt",
    ):
        assert (REPO_ROOT / rel).is_file(), rel


def test_questionset_schema_loads():
    from report_analyst.core.questionset_validation import load_v1_schema

    schema = load_v1_schema()
    assert schema.get("$schema") or schema.get("type") or schema.get("properties")
