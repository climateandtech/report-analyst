# NATS jobs worker (report_analyst_jobs module)
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libpoppler-cpp-dev \
    libsqlite3-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

ENV OPENBLAS_NUM_THREADS=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY report_analyst_search_backend/requirements.txt report_analyst_search_backend/requirements.txt
RUN pip install --no-cache-dir -r report_analyst_search_backend/requirements.txt

RUN pip install --no-cache-dir "nats-py>=2.7.0" "aiohttp>=3.9.0" "pydantic>=2.5.0" "pandas>=2.0.0" "numpy>=1.24.0"

COPY report_analyst/ report_analyst/
COPY report_analyst_jobs/ report_analyst_jobs/
COPY report_analyst_search_backend/ report_analyst_search_backend/
COPY prompts/ prompts/

CMD ["python", "report_analyst_jobs/nats_integration.py", "worker"]
