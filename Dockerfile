# Unified Report Analyst image — same codebase, runtime selected via REPORT_ANALYST_RUNTIME:
#   core       — Streamlit only (customer / standalone)
#   enterprise — Streamlit + FastAPI + NATS worker (Climate+Tech internal)
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libpoppler-cpp-dev \
    libsqlite3-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV OPENBLAS_NUM_THREADS=1
ENV REPORT_ANALYST_RUNTIME=core
ENV STORAGE_PATH=/app/storage

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY report_analyst_enterprise/requirements.txt report_analyst_enterprise/requirements.txt
RUN pip install --no-cache-dir -r report_analyst_enterprise/requirements.txt

COPY report_analyst_api/requirements.txt report_analyst_api/requirements.txt
RUN pip install --no-cache-dir -r report_analyst_api/requirements.txt

COPY report_analyst_search_backend/requirements.txt report_analyst_search_backend/requirements.txt
RUN pip install --no-cache-dir -r report_analyst_search_backend/requirements.txt

RUN pip install --no-cache-dir "nats-py>=2.7.0" "aiohttp>=3.9.0" "pandas>=2.0.0" "numpy>=1.24.0"

COPY report_analyst/ report_analyst/
COPY report_analyst_enterprise/ report_analyst_enterprise/
COPY report_analyst_api/ report_analyst_api/
COPY report_analyst_jobs/ report_analyst_jobs/
COPY report_analyst_search_backend/ report_analyst_search_backend/
COPY prompts/ prompts/
COPY .streamlit/ .streamlit/
COPY alembic.ini .
COPY alembic/ alembic/

COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 8080 8001

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

ENTRYPOINT ["/docker-entrypoint.sh"]
