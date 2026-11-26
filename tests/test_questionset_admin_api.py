"""Enterprise question set admin API and DB install."""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timedelta, timezone

import pytest
import yaml
from joserfc import jwt
from joserfc.jwk import OctKey

pytest.importorskip("llama_index")
from fastapi.testclient import TestClient

os.environ.setdefault("REPORT_ANALYST_RUNTIME", "enterprise")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")

TEST_JWT_SIGNING_KEY = "test-questionset-admin-secret"
ISSUER = "test-issuer"
AUDIENCE = "report-analyst-questionset-admin"


@pytest.fixture(autouse=True)
def admin_env(tmp_path, monkeypatch):
    storage = tmp_path / "storage"
    storage.mkdir()
    (storage / "cache").mkdir()
    monkeypatch.setenv("STORAGE_PATH", str(storage))
    monkeypatch.setenv("REPORT_ANALYST_RUNTIME", "enterprise")
    monkeypatch.setenv("QUESTIONSETS_JWT_HMAC_SECRET", TEST_JWT_SIGNING_KEY)
    monkeypatch.setenv("QUESTIONSETS_JWT_ISSUERS", ISSUER)
    monkeypatch.setenv("QUESTIONSETS_JWT_AUDIENCE", AUDIENCE)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    from report_analyst.core.question_loader import get_question_loader

    get_question_loader().reload()
    yield
    get_question_loader().reload()


def _mint_token(*, jti: str | None = None, scope: str = "questionset:write") -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "iss": ISSUER,
        "sub": "pytest",
        "aud": AUDIENCE,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "jti": jti or str(uuid.uuid4()),
        "scope": scope,
    }
    return jwt.encode({"alg": "HS256"}, claims, OctKey.import_key(TEST_JWT_SIGNING_KEY))


@pytest.fixture
def client():
    from report_analyst_api.main import app
    from report_analyst_enterprise.api.questionsets_router import mount_if_enterprise

    mount_if_enterprise(app)
    return TestClient(app)


MINIMAL_SET = {
    "name": "Installed Test Set",
    "description": "From pytest",
    "questions": [{"id": "q1", "text": "What is the scope?", "guidelines": ""}],
}


def test_install_question_set_upsert_updates_existing(client):
    token1 = _mint_token()
    token2 = _mint_token()
    set_id = "pytest-upsert"
    headers = {"Content-Type": "application/yaml"}
    first = client.post(
        f"/admin/question-sets?set_id={set_id}",
        content=yaml.dump(MINIMAL_SET),
        headers={**headers, "Authorization": f"Bearer {token1}"},
    )
    assert first.status_code == 200
    updated = {**MINIMAL_SET, "name": "Updated name", "documents": ["Annual report"]}
    second = client.post(
        f"/admin/question-sets?set_id={set_id}",
        content=yaml.dump(updated),
        headers={**headers, "Authorization": f"Bearer {token2}"},
    )
    assert second.status_code == 200
    from report_analyst.core.question_loader import get_question_loader

    get_question_loader().reload()
    assert get_question_loader().get_question_set_info()[set_id]["name"] == "Updated name"


def test_install_question_set_appears_in_loader(client):
    token = _mint_token()
    set_id = "pytest-installed"
    body = yaml.dump(MINIMAL_SET)
    response = client.post(
        f"/admin/question-sets?set_id={set_id}",
        content=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/yaml",
        },
    )
    assert response.status_code == 200, response.text
    from report_analyst.core.question_loader import get_question_loader

    get_question_loader().reload()
    info = get_question_loader().get_question_set_info()
    assert set_id in info
    assert info[set_id]["name"] == "Installed Test Set"


def test_reject_builtin_id(client):
    token = _mint_token()
    response = client.post(
        "/admin/question-sets?set_id=tcfd",
        content=yaml.dump(MINIMAL_SET),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/yaml"},
    )
    assert response.status_code == 409


def test_jwt_replay_rejected(client):
    jti = str(uuid.uuid4())
    token = _mint_token(jti=jti)
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/yaml"}
    first = client.post(
        "/admin/question-sets?set_id=pytest-replay",
        content=yaml.dump(MINIMAL_SET),
        headers=headers,
    )
    assert first.status_code == 200
    second = client.post(
        "/admin/question-sets?set_id=pytest-replay-2",
        content=yaml.dump(MINIMAL_SET),
        headers=headers,
    )
    assert second.status_code == 401


def test_answer_type_normalization(client):
    token = _mint_token()
    doc = {
        "name": "Typed",
        "questions": [
            {
                "id": "t1",
                "text": "Is there a plan?",
                "answer_type": {"kind": "classification"},
            }
        ],
    }
    response = client.post(
        "/admin/question-sets?set_id=pytest-typed",
        content=json.dumps(doc),
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
    )
    assert response.status_code == 200
    from report_analyst.core.prompt_manager import has_typed_answer
    from report_analyst.core.question_loader import get_question_loader

    get_question_loader().reload()
    guidelines = get_question_loader().get_questions("pytest-typed")["t1"]["guidelines"]
    assert has_typed_answer(guidelines)

