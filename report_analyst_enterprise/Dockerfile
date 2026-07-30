# Deprecated for deploy — use repository root Dockerfile + REPORT_ANALYST_RUNTIME.
# Enterprise Streamlit image (report_analyst_enterprise module + core RPL app)
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

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY report_analyst_enterprise/requirements.txt report_analyst_enterprise/requirements.txt
RUN pip install --no-cache-dir -r report_analyst_enterprise/requirements.txt

COPY report_analyst/ report_analyst/
COPY report_analyst_enterprise/ report_analyst_enterprise/
COPY report_analyst_search_backend/ report_analyst_search_backend/
COPY prompts/ prompts/
COPY .streamlit/ .streamlit/

COPY alembic.ini .
COPY alembic/ alembic/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "report_analyst/streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0"]
