# Report Analyst Enterprise Module

Enterprise edition features for Open Sustainability Analyst, licensed under the **Climate+Tech Open License for Good** (see [LICENSE](LICENSE)).

This module adds:

- **PostgreSQL + pgvector** support (`database/`)
- **Enterprise Streamlit image** ([Dockerfile](Dockerfile)) — core app plus this module
- Optional **search-backend integration** UI hooks (via core Streamlit + `report_analyst_search_backend/`)

## Docker

Deploy from the **repository root** using the unified image. Set `REPORT_ANALYST_RUNTIME`:

- `core` — Streamlit only (customer / standalone)
- `enterprise` — Streamlit + API + NATS worker (Climate+Tech internal)

See [`docs/DOCKER-DEPLOY.md`](../docs/DOCKER-DEPLOY.md).

```bash
docker build -t report-analyst .
docker run -p 8080:8080 -p 8001:8001 \
  -e REPORT_ANALYST_RUNTIME=enterprise \
  -e OPENAI_API_KEY=your_key \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e USE_ALEMBIC_MIGRATIONS=true \
  report-analyst
```

## Platform integration (search backend + NATS)

For production (upload, chunking, async analysis), use `REPORT_ANALYST_RUNTIME=enterprise` with:

```bash
BACKEND_URL=https://your-search-backend.example.com
USE_BACKEND=true
USE_CENTRALIZED_LLM=true
USE_DATA_LAKE=true

NATS_URL=nats://your-nats-host:4222
NATS_TOKEN=your_token
```

See [`report_analyst_jobs/README.md`](../report_analyst_jobs/README.md) and [`report_analyst_search_backend/`](../report_analyst_search_backend/) for NATS and upload details.

## License

**Climate+Tech Open License for Good** — research, educational, and non-commercial use. Commercial and dual licensing: contact [Climate+Tech](https://climateandtech.com/en/climate-ai-solutions/opensustainability-analysis-framework).

The core analysis engine in `report_analyst/` remains under the **RPL**.
