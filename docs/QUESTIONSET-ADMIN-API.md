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

## Actwyser (Coolify compose)

In Coolify **Domains**, two services (internal port = container port):

| Service | Domain | Internal port |
|---------|--------|----------------|
| `report-analyst-auth` | `https://<uuid>.<ip>.sslip.io` | **8080** |
| `report-analyst` | `https://<uuid>-api.<ip>.sslip.io` | **8001** |

Ops mirror in `coolify-provisioning` (`.env` + `.env.report-analyst` + `.env.customer.actwyser`):

- `REPORT_ANALYST_CUSTOMER_ACTWYSER_API_DOMAIN` — browser base for POST (no basic auth)
- `./scripts/set_compose_customer_enterprise_domains.py --customer actwyser --deploy`

1. `REPORT_ANALYST_RUNTIME=enterprise`, JWT envs, persistent `STORAGE_PATH`.
2. Redeploy after domain + git changes (`feature/docker-coolify-customer-deploy`).
3. `curl -fsS "${REPORT_ANALYST_CUSTOMER_ACTWYSER_API_DOMAIN}/health"` → `ok`
4. POST NH-Analyse; refresh Streamlit and select the new framework.