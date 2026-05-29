# Docker deployment

Build images from the **repository root** (`docker build -f <module>/Dockerfile .`).

## Core (RPL) — standalone Streamlit

| Image | Dockerfile | Port |
|-------|------------|------|
| Streamlit app | [`Dockerfile`](../Dockerfile) | 8080 |

```bash
docker build -t report-analyst:core .
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=your_key \
  -e OPENAI_API_MODEL=gpt-4o-mini \
  -e OPENBLAS_NUM_THREADS=1 \
  report-analyst:core
```

Health: `GET /_stcore/health`

## Licensed modules (Climate+Tech Open License for Good)

| Module | Dockerfile | Docs |
|--------|------------|------|
| Enterprise Streamlit + Postgres | [`report_analyst_enterprise/Dockerfile`](../report_analyst_enterprise/Dockerfile) | [`report_analyst_enterprise/README.md`](../report_analyst_enterprise/README.md) |
| REST API | [`report_analyst_api/Dockerfile`](../report_analyst_api/Dockerfile) | [`INSTALL.md`](../INSTALL.md) § API |
| NATS jobs worker | [`report_analyst_jobs/Dockerfile`](../report_analyst_jobs/Dockerfile) | [`report_analyst_jobs/README.md`](../report_analyst_jobs/README.md) |

Search-backend integration (S3, NATS upload, data lake) is implemented in **`report_analyst_search_backend/`** (library module; no separate container image).

See [`INSTALL.md`](../INSTALL.md) for local install without Docker.
