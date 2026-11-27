# PR: Enterprise question set admin API (#203)

Use this as the GitHub PR description (branch `feature/enterprise-questionset-admin` → `main`).

## Summary

- **POST/GET `/admin/question-sets`** on enterprise runtime (`:8001`), JWT one-time tokens, SQLite persistence merged with bundled frameworks.
- **Actwyser:** Coolify customer compose uses dual Traefik domains (auth `:8080`, API `:8001`); NH-Analyse set pushed via API (not in public git).
- **Deploy fixes:** `COPY docs/contracts/` in Dockerfile; relax `pillow` pin for slim-image pip resolve.
- **CI parity:** Local pre-push checks that mirror CI/Coolify (`ci-parity.sh`, packaging tests, slim `pip install` in CI).

Closes #203.

## API

- Docs: `docs/QUESTIONSET-ADMIN-API.md`
- Mint: `scripts/mint_questionset_upload_jwt.py`
- Schema: `docs/contracts/questionset-document.v1.schema.json`

## Local CI parity (before push / Coolify)

```bash
./scripts/ci-parity.sh before-push   # tests/test_dockerfile_packaging.py + pip in python:3.12-slim
./scripts/ci-parity.sh pytest        # full pytest (CI test job)
./scripts/ci-parity.sh docker-build  # optional full image smoke
QG_CI_PARITY=1 ./scripts/quality-gate.sh full
```

**QG vs CI:** Session QG scopes to your diff (ruff + affected pytest) so multi-agent sessions do not churn unrelated files. CI `lint` / `test` are repo-wide (black, full pytest). PR failures on new files do not mean `main` broke. Coolify gaps: slim `pip install` and Dockerfile `COPY` (see `ci-parity.sh`).

## Test plan

- [ ] `BASE_REF=origin/main QG_STRICT=1 ./scripts/quality-gate.sh full`
- [ ] `./scripts/ci-parity.sh before-push`
- [ ] `pytest tests/test_questionset_admin_api.py tests/test_dockerfile_packaging.py`
- [ ] On enterprise/Coolify: API `GET /health`, JWT `POST` install, framework visible in Streamlit

## Ops (Actwyser)

- Branch merge: `feature/docker-coolify-customer-deploy` (customer compose + enterprise env)
- Coolify compose domains: `report-analyst-auth` → ui sslip `:8080`; `report-analyst` → `{uuid}-api` sslip `:8001`
- JWT env vars must be **runtime**, not build-only