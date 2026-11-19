# Core and enterprise

Every API page is labeled. The label matches the module and the license, not the screen you happen to be on.

| | Core | Enterprise |
| --- | --- | --- |
| Package | `report_analyst/` | `report_analyst_enterprise/`, plus `report_analyst_api/`, `report_analyst_jobs/`, and `report_analyst_search_backend/` |
| License | Reciprocal Public License | Climate+Tech Open License for Good |
| Docker image | `report-analyst:core` — Streamlit analyst | `report-analyst:enterprise` — core plus Postgres/pgvector. API, jobs, and search are installed separately |
| What it covers | Chunking, question sets, analysis workflow, benchmarking | PDF viewer, pgvector, REST models, S3/NATS upload, async jobs |

The Streamlit app can call enterprise pieces, such as the PDF viewer, when that package is installed. Those calls are still enterprise. The open core does not require them.

## Core

- [Question sets](question-sets.md)
- [Documents and chunks](documents.md)
- [Analysis workflow](workflow.md)
- [Benchmark models](benchmark-models.md)
- [Evaluation engine](evaluation-engine.md)
- [Loading results](retrieval-results.md)

## Enterprise

- [PDF viewer](pdf-viewer.md)
- [pgvector](pgvector.md)
- [REST API models](api-schemas.md)
