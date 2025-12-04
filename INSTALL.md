# Installation Guide

## Modular Architecture

The report-analyst is built with a modular architecture that allows you to install only the components you need:

- **`report_analyst/`** - Core package (required)
- **`report_analyst_api/`** - FastAPI REST API (optional)
- **`report_analyst_search_backend/`** - Search backend integration (optional)

## Installation Options

### 1. Core Package Only (Streamlit App)

```bash
# Install core dependencies
pip install -r requirements.txt

# Run Streamlit app
python -m streamlit run report_analyst/streamlit_app.py
```

### 2. Core + API Module

```bash
# Install core dependencies
pip install -r requirements.txt

# Install API dependencies
pip install -r report_analyst_api/requirements.txt

# Run API server
uvicorn report_analyst_api.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Core + Search Backend Integration

```bash
# Install core dependencies
pip install -r requirements.txt

# Install search backend dependencies
pip install -r report_analyst_search_backend/requirements.txt

# Configure search backend URL in environment
export SEARCH_BACKEND_URL="http://localhost:8001"
export SEARCH_BACKEND_API_KEY="your-api-key"  # optional
```

### 4. Full Installation (All Modules)

```bash
# Install all dependencies
pip install -r requirements.txt
pip install -r report_analyst_api/requirements.txt
pip install -r report_analyst_search_backend/requirements.txt

# Now you can use all features:
# - Streamlit app: python -m streamlit run report_analyst/streamlit_app.py  
# - API server: uvicorn report_analyst_api.main:app --reload
# - Search backend integration: automatic discovery
```

## Usage

### Streamlit App (Core)
```bash
python -m streamlit run report_analyst/streamlit_app.py
```

### API Server
```bash
uvicorn report_analyst_api.main:app --reload --port 8000
```
