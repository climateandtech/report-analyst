# Question set admin API (enterprise)

Install custom question sets on a running **enterprise** instance without redeploying app images.

**Issue:** [GitHub #203](https://github.com/climateandtech/report-analyst/issues/203)

## Runtime

- `REPORT_ANALYST_RUNTIME=enterprise` — Streamlit `:8080` and API `:8001`
- `USE_NATS_WORKER` — default **off**; set `true` only for internal NATS integrations

## Storage

Pushed sets are stored in the **same SQLite database** as analysis cache (`{STORAGE_PATH}/cache/analysis.db`). Built-in frameworks in the image remain available; installed sets are **merged** into the Streamlit dropdown.

Requires **persistent** `/app/storage` on production hosts.

## Auth

One-time **Bearer JWT** (mint offline):

```bash
export QUESTIONSETS_JWT_HMAC_SECRET=...   # dev; production: verify via QUESTIONSETS_JWT_PUBLIC_JWK
export QUESTIONSETS_JWT_ISSUERS=climateandtech-ops
export QUESTIONSETS_JWT_AUDIENCE=report-analyst-questionset-admin

TOKEN=$(python scripts/mint_questionset_upload_jwt.py)
```

## Install

```bash
curl -sS -X POST "https://<host>:8001/admin/question-sets?set_id=actwyser-november-2026" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/yaml" \
  --data-binary @actwyser-november-2026_questions.yaml
```

Contract: [`docs/contracts/questionset-document.v1.schema.json`](contracts/questionset-document.v1.schema.json)

`GET /admin/question-sets/schema` — returns the JSON Schema (requires JWT).

## Actwyser

1. Deploy branch with enterprise runtime and expose `8001`.
2. Set JWT verify env on Coolify; keep `STORAGE_PATH=/app/storage` volume.
3. POST NH-Analyse off-repo; refresh Streamlit and select the new framework.