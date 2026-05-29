# Docker deployment

This repository ships several Docker images for self-hosted or PaaS deployment (any platform that builds from a Git repo and runs containers).

## Images

| Dockerfile | Service | Port |
|------------|---------|------|
| `Dockerfile` | Streamlit app (core, RPL) | 8080 |
| `Dockerfile.enterprise` | Streamlit + Postgres/pgvector enterprise module | 8080 |
| `Dockerfile.api` | FastAPI (`report_analyst_api`) | 8001 |
| `Dockerfile.jobs` | NATS worker (`document.ready` → analysis) | — |

## Standalone Streamlit

Build and run the core image:

```bash
docker build -t report-analyst:core .
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=your_key \
  -e OPENAI_API_MODEL=gpt-4o-mini \
  -e OPENBLAS_NUM_THREADS=1 \
  report-analyst:core
```

Enterprise (persistent storage via Postgres):

```bash
docker build -f Dockerfile.enterprise -t report-analyst:enterprise .
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=your_key \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e USE_ALEMBIC_MIGRATIONS=true \
  -e USE_POSTGRES_FILE_STORAGE=true \
  report-analyst:enterprise
```

On **Apple Silicon**, use `--platform linux/amd64` if the enterprise build fails on native ARM.

## API service

```bash
docker build -f Dockerfile.api -t report-analyst:api .
docker run -p 8001:8001 \
  -e OPENAI_API_KEY=your_key \
  -e OPENBLAS_NUM_THREADS=1 \
  report-analyst:api
```

Health check: `GET /health` on port 8001.

## Platform integration (search backend + NATS)

For production setups that connect to a **search backend** (document upload, chunking, embeddings) and **NATS** (async jobs, centralized LLM via the backend), deploy three services from the same repo:

1. **Streamlit** — `Dockerfile.enterprise` (optional UI for analysts)
2. **API** — `Dockerfile.api`
3. **Jobs worker** — `Dockerfile.jobs` (entrypoint: `python report_analyst_jobs/nats_integration.py worker`)

Example environment (adjust URLs and secrets for your environment):

```bash
BACKEND_URL=https://your-search-backend.example.com
USE_BACKEND=true
USE_CENTRALIZED_LLM=true
USE_DATA_LAKE=true

NATS_URL=nats://your-nats-host:4222
NATS_TOKEN=your_token
NATS_STREAM_NAME=DOCUMENTS
NATS_SUBJECT_PREFIX=docs

# S3-compatible storage (when using enterprise upload path)
USE_S3_STORAGE=true
S3_BUCKET_NAME=documents
S3_ENDPOINT_URL=https://your-object-storage.example.com
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
```

The jobs worker reads `NATS_URL`, `NATS_TOKEN`, and `BACKEND_URL` from the environment.

See also:

- [`INSTALL.md`](../INSTALL.md) — local install and module overview
- [`report_analyst_jobs/README.md`](../report_analyst_jobs/README.md) — NATS job flow
- [`report_analyst_search_backend/`](../report_analyst_search_backend/) — backend integration module

## Health checks

| Service | Endpoint |
|---------|----------|
| Streamlit | `GET /_stcore/health` (port 8080) |
| API | `GET /health` (port 8001) |
