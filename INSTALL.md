# Installation Guide – Open Sustainability Analyst

This guide explains how to install and run **Open Sustainability Analyst** and its optional modules.

---

## Modular Architecture

The project is built with a modular architecture so you can install only what you need:

- **`report_analyst/`** – Core open-source package (Streamlit app + analysis engine, **RPL**)
- **`report_analyst_api/`** – FastAPI REST API (**Climate+Tech Open License for Good**)
- **`report_analyst_search_backend/`** – Search backend integration (uploads, chunking)
- **`report_analyst_jobs/`** – Jobs and worker integrations (NATS, queues, etc.)

**Licensing Overview** (details in `README.md`):

- **`report_analyst/`** – **Reciprocal Public License (RPL)** – open-core
- **Other modules** – **Climate+Tech Open License for Good**, with **dual licensing** available on request

---

## 1. Core Package Only (Streamlit App)

**Recommended for most analysts.**

```bash
# 1) Create virtual environment (optional but recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2) Install core dependencies
pip install -r requirements.txt

# 3) Run Streamlit app
python -m streamlit run report_analyst/streamlit_app.py
```

**Environment variables** (create a `.env` file in the project root):

```text
OPENAI_API_KEY=your_openai_key_here
OPENAI_API_MODEL=gpt-4o-mini

# Optional: Google Gemini support
GOOGLE_API_KEY=your_google_api_key_here
```

---

## 2. Core + API Module

Add a REST API if you want to integrate the analysis into other systems.

```bash
# Core dependencies
pip install -r requirements.txt

# API dependencies
pip install -r report_analyst_api/requirements.txt

# Run API server
uvicorn report_analyst_api.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 3. Core + Search Backend Integration

Use this if you run a separate search/upload backend.

```bash
# Core dependencies
pip install -r requirements.txt

# Search backend dependencies
pip install -r report_analyst_search_backend/requirements.txt

# Configure search backend URL in environment
export SEARCH_BACKEND_URL="http://localhost:8001"
export SEARCH_BACKEND_API_KEY="your-api-key"  # optional
```

---

## 4. Full Installation (All Modules)

For advanced setups (API + search backend + jobs/workers).

```bash
# Core
pip install -r requirements.txt

# API
pip install -r report_analyst_api/requirements.txt

# Search backend
pip install -r report_analyst_search_backend/requirements.txt

# Jobs / workers
pip install -r report_analyst_jobs/requirements.txt

# Now you can use all features:
# - Streamlit app: python -m streamlit run report_analyst/streamlit_app.py
# - API server:    uvicorn report_analyst_api.main:app --reload
# - Search backend: see report_analyst_search_backend/
# - Jobs/workers:   see report_analyst_jobs/README.md
```

---

## Usage Summary

### Streamlit App (Core)

```bash
python -m streamlit run report_analyst/streamlit_app.py
```

### API Server

```bash
uvicorn report_analyst_api.main:app --reload --port 8000
```

For more advanced deployment patterns (NATS workers, search backend, etc.), see:

- `report_analyst_jobs/README.md`
- `report_analyst_search_backend/`

---

## For Contributors

After cloning, enable the project's git hooks (strips Co-authored-by from commits):

```bash
git config core.hooksPath .githooks
```

See `.githooks/README.md` for details.

---

## Licensing Notes

- **`report_analyst/`** is open-core under the **Reciprocal Public License (RPL)**
- **Other modules** (`report_analyst_api/`, `report_analyst_jobs/`, `report_analyst_search_backend/`) are under the **Climate+Tech Open License for Good**, and can be **dual-licensed** for commercial or special use cases upon request

For full license texts and commercial/dual-licensing inquiries, see the main `README.md` and:

- [OpenSustainability Analysis Framework](https://climateandtech.com/en/climate-ai-solutions/opensustainability-analysis-framework)
- [AI Benchmark for Sustainability Report Analysis](https://climateandtech.com/en/research-projects/sustainability-ai-benchmark-and-dataset)
