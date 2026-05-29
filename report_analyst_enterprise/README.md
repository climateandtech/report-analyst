# Report Analyst Enterprise Module

Enterprise edition features for Open Sustainability Analyst, licensed under the **Climate+Tech Open License for Good** (see [LICENSE](LICENSE)).

This module adds:

- **PostgreSQL + pgvector** support (`database/`)
- **Enterprise Streamlit image** ([Dockerfile](Dockerfile)) — core app plus this module
- Optional **search-backend integration** UI hooks (via core Streamlit + `report_analyst_search_backend/`)

## Docker (enterprise Streamlit)

Build from the **repository root** (paths in the Dockerfile expect monorepo layout):

```bash
docker build -f report_analyst_enterprise/Dockerfile -t report-analyst:enterprise .
docker run -p 8080:8080 \
  -e OPENAI_API_KEY=your_key \
  -e DATABASE_URL=postgresql://user:pass@host:5432/db \
  -e USE_ALEMBIC_MIGRATIONS=true \
  -e USE_POSTGRES_FILE_STORAGE=true \
  report-analyst:enterprise
```

## Platform integration (search backend + NATS)

For a full production stack (upload, chunking, async analysis), deploy alongside:

| Module | Role | Docker |
|--------|------|--------|
| `report_analyst_enterprise/` | Analyst UI + Postgres | This Dockerfile |
| `report_analyst_api/` | REST API | `report_analyst_api/Dockerfile` |
| `report_analyst_jobs/` | NATS worker | `report_analyst_jobs/Dockerfile` |
| `report_analyst_search_backend/` | Backend/S3/NATS integration (library) | Used by UI and jobs |

Example integration environment:

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
