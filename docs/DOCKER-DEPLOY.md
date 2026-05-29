# Docker deployment

One image from the **repository root**. Runtime mode is selected with `REPORT_ANALYST_RUNTIME`:

| Mode | Env | Processes |
|------|-----|-----------|
| **core** (default) | `REPORT_ANALYST_RUNTIME=core` | Streamlit on `:8080` |
| **enterprise** | `REPORT_ANALYST_RUNTIME=enterprise` | Streamlit `:8080`, FastAPI `:8001`, NATS worker |

```bash
docker build -t report-analyst .
```

## Customer (Streamlit only)

```bash
docker run -p 8080:8080 \
  -v report-analyst-storage:/app/storage \
  -e REPORT_ANALYST_RUNTIME=core \
  -e STORAGE_PATH=/app/storage \
  -e OPENAI_API_KEY=your_key \
  -e OPENAI_API_MODEL=gpt-4o-mini \
  report-analyst
```

On **Coolify**, use `docker-compose.coolify-customer.yml` (declares `storage-data:/app/storage`) or add a **Persistent Storage** volume mount at `/app/storage` (directory, not the `.sqlite` file alone). Coolify prefixes volume names with the app UUID.

Health: `GET /_stcore/health`

Optional Postgres (enterprise module features in UI):

```bash
docker run -p 8080:8080 \
  -e REPORT_ANALYST_RUNTIME=core \
  -e DATABASE_URL=postgresql://... \
  -e USE_ALEMBIC_MIGRATIONS=true \
  report-analyst
```

## Internal enterprise (Climate+Tech)

```bash
docker run -p 8080:8080 -p 8001:8001 \
  -e REPORT_ANALYST_RUNTIME=enterprise \
  -e DATABASE_URL=postgresql://... \
  -e USE_BACKEND=true \
  -e USE_CENTRALIZED_LLM=true \
  -e NATS_URL=nats://nats:4222 \
  report-analyst
```

- Streamlit health: `GET /_stcore/health`
- API health: `GET /health` on port 8001

Licensed modules (`report_analyst_enterprise/`, `report_analyst_api/`, `report_analyst_jobs/`, `report_analyst_search_backend/`) ship in the same image; no separate container builds.

See [`INSTALL.md`](../INSTALL.md) for local install without Docker.
