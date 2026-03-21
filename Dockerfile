# Core image: report_analyst Streamlit app (RPL only, no enterprise deps)
FROM python:3.12-slim

WORKDIR /app

# System deps: PyMuPDF (poppler), chroma-hnswlib (build), sqlite-vss (build from source on ARM), healthcheck (curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libpoppler-cpp-dev \
    libsqlite3-dev \
    pkg-config \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies (core only)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY report_analyst/ report_analyst/
COPY prompts/ prompts/
COPY .streamlit/ .streamlit/

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

ENTRYPOINT ["streamlit", "run", "report_analyst/streamlit_app.py", "--server.port=8080", "--server.address=0.0.0.0"]
