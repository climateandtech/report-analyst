# Deploy on Coolify (Climate+Tech)

Open Sustainability Analyst can run on [Coolify](https://coolify.io/) using the Dockerfiles in this repository.

## Images

| Dockerfile | Service | Port |
|------------|---------|------|
| `Dockerfile` | Streamlit (core, RPL) | 8080 |
| `Dockerfile.enterprise` | Streamlit + Postgres/pgvector enterprise module | 8080 |
| `Dockerfile.api` | FastAPI (`report_analyst_api`) | 8001 |
| `Dockerfile.jobs` | NATS worker (`document.ready` → analysis) | — |

## Customer standalone (Streamlit only)

1. New Coolify application → **Public** Git repository: `https://github.com/climateandtech/report-analyst`
2. Branch: `main`, build pack: **Dockerfile**, file: `Dockerfile` (or `Dockerfile.enterprise` + Postgres)
3. Exposed port: **8080**
4. Runtime env (required):

```bash
OPENAI_API_KEY=...
OPENAI_API_MODEL=gpt-4o-mini
OPENBLAS_NUM_THREADS=1
```

Optional: `GOOGLE_API_KEY`, `DATABASE_URL` (enterprise + Alembic).

## Enterprise + ct-platform

Wire Streamlit enterprise, API, and jobs worker to your existing **platform-backend**, **NATS**, and **S3** stack. Use the provisioning scripts in the Climate+Tech monorepo:

```bash
cd coolify-provisioning
source .env && source .env.platform && source .env.report-analyst
./setup-report-analyst.sh --enterprise --deploy
```

See `coolify-provisioning/REPORT-ANALYST-DEPLOY.md` for full env tables and verification.

## Health checks

- Streamlit: `GET /_stcore/health` on port 8080
- API: `GET /docs` or OpenAPI on port 8001
