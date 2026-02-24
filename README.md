## Open Sustainability Analyst

**Version 0.8.0-rc (Release Candidate)**

Open Sustainability Analyst is the analyst-facing application of the **Open Sustainability Analysis** project by **Climate+Tech**.  
It helps sustainability and ESG professionals analyze complex sustainability reports with modern AI, while keeping methods transparent and research-based.

This project is part of the **OpenSustainability Analysis Framework** by Climate+Tech  
([OpenSustainability Analysis Framework](https://climateandtech.com/en/climate-ai-solutions/opensustainability-analysis-framework)).

> **Tagline:** *Democratizing sustainability report analysis with modern technology.*

---

## What You Can Do With It

- **Upload sustainability reports (PDF)** and analyze them locally.
- **Use preset analysis frameworks** (e.g. TCFD, Lucia, Everest/Denali) instead of writing your own prompts.
- **Get structured, explainable answers** with evidence, gaps, and sources.
- **Compare configurations** (models, chunk sizes, question sets) to find better analysis setups.
- **Export results** for further analysis (e.g. CSV for spreadsheets).

You stay in control of:
- Which reports are analyzed.
- Which questions/frameworks are used.
- Which models and parameters are applied.

---

## Quick Start (for Analysts)

You need basic command line access, but no deep Python knowledge.

1. **Create and activate a virtual environment**

```bash
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install core dependencies**

```bash
pip install -r requirements.txt
```

3. **Set your API keys (for LLMs)**

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Then edit `.env` and add your API keys:

```text
OPENAI_API_KEY=your_openai_key_here
OPENAI_API_MODEL=gpt-4o-mini

# Optional: Google Gemini support
GOOGLE_API_KEY=your_google_api_key_here
```

4. **Run the Streamlit app**

```bash
python3 -m streamlit run report_analyst/streamlit_app.py
```

5. **Upload a report and choose a framework**

In the web UI you can:
- Upload a PDF sustainability report.
- Select a question set (e.g. TCFD, Lucia, Everest).
- Run the analysis and view:
  - Answers
  - Evidence and sources
  - Gaps and uncertainties

For more detailed setup options (API, search backend, jobs), see `INSTALL.md`.

---

## Use Cases

Open Sustainability Analyst is used by various organizations and research institutions:

- **score4more** – Tech & AI/ML innovation for sustainability, using the tool for systematic analysis of corporate sustainability reports

---

## Features

### Document Processing

| Feature | Description |
|---------|-------------|
| PDF Upload | Upload sustainability reports directly through the web interface |
| Intelligent Chunking | Automatic document segmentation with configurable chunk size and overlap |
| Vector Embeddings | Semantic search across document chunks for relevant evidence retrieval |
| Multi-file Support | Analyze multiple reports and compare results side-by-side |

### Analysis Frameworks

| Feature | Description |
|---------|-------------|
| Preset Question Sets | Use research-validated frameworks (TCFD, Lucia, Everest, Denali, Kilimanjaro) |
| Custom Question Selection | Choose specific questions from any framework |
| Framework Comparison | Analyze the same document with different frameworks side-by-side |
| Framework Extensibility | Add your own question sets via YAML files |

### AI & Model Configuration

| Feature | Description |
|---------|-------------|
| Multiple LLM Support | OpenAI GPT models (GPT-4, GPT-4o-mini, etc.) and Google Gemini |
| Configurable Parameters | Adjust chunk size, overlap, and top-k retrieval settings |
| Batch Processing | Process all questions at once or individually |
| LLM-based Scoring | Optional confidence scoring using the LLM itself |
| Model Comparison | Test different models on the same document to compare results |

### Results & Evidence

| Feature | Description |
|---------|-------------|
| Structured Answers | Clear, formatted answers to each question |
| Evidence Chunks | Exact document passages that support each answer |
| Source Citations | Track which parts of the document were used |
| Gap Identification | Identify where information is missing or unclear |
| Consolidated View | View all results across multiple files and question sets in one table |

### Caching & Performance

| Feature | Description |
|---------|-------------|
| Intelligent Caching | Results cached by configuration to avoid redundant analysis |
| Cache Management | Clear cache for specific files or configurations |
| Incremental Analysis | Only analyze new or changed questions |
| Performance Optimization | Skip already-analyzed questions automatically |

### Export & Integration

| Feature | Description |
|---------|-------------|
| CSV Export | Download analysis results as CSV for spreadsheet analysis |
| DataFrame Views | Interactive tables for results and document chunks |
| REST API | Optional FastAPI integration for other systems |
| Backend Integration | Optional enterprise S3+NATS upload and processing |

### Advanced Features

| Feature | Description |
|---------|-------------|
| Search Backend | Connect to external search/upload backends for larger deployments |
| Job Processing | Async job processing for batch analysis (NATS, Celery, Lambda) |
| Modular Architecture | Use only the components you need |

---

## Analysis Frameworks (Question Sets)

Open Sustainability Analyst uses **preset question sets** ("frameworks") that encode analysis logic for different use cases.

Current core question sets (in `report_analyst/questionsets/`):

- **Everest** – `everest_questions.yaml`  
  Comprehensive sustainability labeling and gap analysis framework (35+ questions).
- **TCFD** – `tcfd_questions.yaml`  
  Climate-related financial disclosure questions aligned with TCFD.
- **Denali** – `denali_questions.yaml`  
  Deeper sustainability analysis for specific focus areas.
- **Kilimanjaro** – `kilimanjaro_questions.yaml`  
  Additional thematic coverage.
- **Lucia** – `lucia_questions.yaml`  
  Framework focused on courageous sustainability initiatives, climate-neutral transformation, and climate metrics (Scopes 1–3, targets, certifications, etc.).

In the UI you simply:
- Select a **question set** (framework).
- Optionally select **individual questions**.
- Run the analysis and inspect the structured results.

---

## Optimization and Experimentation

Open Sustainability Analyst is designed to support systematic experimentation and optimization of analysis configurations before deployment.

### Configuration Comparison

You can test and compare different configurations without committing to a single setup:

| Aspect | Capability |
|--------|------------|
| Chunking Parameters | Compare different chunk sizes and overlap settings to find optimal document segmentation |
| Model Selection | Test multiple LLM models (GPT-4, GPT-4o-mini, Gemini, etc.) on the same document |
| Retrieval Settings | Experiment with top-k values to balance relevance and context |
| Question Set Selection | Compare results across different frameworks (TCFD, Lucia, Everest, etc.) |
| Batch vs. Individual | Test batch processing against individual question analysis |

All configurations are cached independently, allowing you to:
- Run multiple experiments on the same document without redundant processing
- Compare results side-by-side in the consolidated view
- Identify the best configuration for your specific use case
- Deploy the optimal setup once you've validated performance

### LLM-based Chunk Selection

For advanced use cases, you can integrate LLM annotators for intelligent chunk selection:

| Feature | Description |
|---------|-------------|
| Relevance Filtering | Use LLMs to score and filter chunks by relevance to specific questions |
| Context Optimization | Select the most informative chunks before analysis to improve accuracy |
| Custom Annotators | Integrate custom LLM-based chunk selection logic for specialized workflows |

This allows you to move beyond simple vector similarity search and use semantic understanding to identify the most relevant document passages for each question.

---

## Module Structure

This repository is intentionally modular. The separation also reflects **different licenses** (see Licensing section below).

```text
report-analyst/
├── report_analyst/                  # Core open-source analysis engine (RPL)
│   ├── core/                        # Chunking, analysis, caching, workflows
│   ├── questionsets/                # Question set YAML files (frameworks)
│   ├── streamlit_app.py             # Main Streamlit application
│   └── streamlit_app_backend.py     # Legacy / backend-focused UI
├── report_analyst_api/              # FastAPI REST API (Climate+Tech Open License for Good)
├── report_analyst_jobs/             # Job / worker integration module (NATS, queues, etc.)
├── report_analyst_search_backend/   # Search + upload backend integration
├── prompts/                         # Prompt templates for analysis and QA
│   ├── analysis/                    # Document analysis prompts
│   └── qa/                          # Question-answering prompts
├── tests/                           # Comprehensive test suite
├── .github/workflows/               # GitHub Actions CI/CD
└── data/                            # Default data directories
    ├── input/                       # Input documents
    └── output/                      # Generated outputs
```

At a high level:
- **`report_analyst/`** – open-core engine and analyst UI (what most users need).
- **`report_analyst_api/`** – REST API if you want to integrate into other systems.
- **`report_analyst_search_backend/`** – backend service for file upload, chunking, and orchestration.
- **`report_analyst_jobs/`** – async jobs, NATS integration, and larger system deployments.

---

## How This Fits Into the Climate+Tech Ecosystem

Open Sustainability Analyst is the open-core analysis app in a broader research and tooling ecosystem:

- **Open Sustainability Analysis Framework** – open-core AI toolkit for sustainability report analysis  
  ([framework overview](https://climateandtech.com/en/climate-ai-solutions/opensustainability-analysis-framework))
- **AI Benchmark for Sustainability Report Analysis** – research benchmark and dataset for evaluating AI pipelines and greenwashing detection  
  ([benchmark project](https://climateandtech.com/en/research-projects/sustainability-ai-benchmark-and-dataset))
- **ChatReport research and related projects** – academic work on evidence-based, explainable sustainability report analysis

The framework is developed together with research partners such as:
- **University of Zurich (UZH)**
- **LMU München**
- **Leuphana Universität Lüneburg**

These collaborations ensure that the analysis methods in this repository are **research-validated** and aligned with current work on benchmarking, greenwashing detection, and robust ESG analysis.

---

## State of the Art

Open Sustainability Analyst builds on recent research advances in AI-powered document analysis and sustainability reporting:

### ChatReport

[ChatReport](https://arxiv.org/abs/2307.15770) showed that it is possible to democratize sustainability disclosure analysis through LLM-based tools by making answers traceable to source passages to reduce hallucination and by actively involving domain experts in the development loop. The system successfully analyzed 1,015 corporate sustainability reports, demonstrating that scalable, evidence-based analysis is feasible when outputs are grounded in the original documents.

### ClimateFinance Bench

[ClimateFinance Bench](https://arxiv.org/abs/2505.22752) showed that it is possible to create systematic benchmarks for evaluating RAG (retrieval-augmented generation) approaches on climate finance document analysis. The benchmark, comprising 330 expert-validated question-answer pairs from 33 sustainability reports across all 11 GICS sectors, demonstrated that the retriever's ability to locate passages containing the answer is the chief performance bottleneck, highlighting the critical importance of effective retrieval strategies.

### DIRAS

[DIRAS](https://arxiv.org/abs/2406.14162) showed that it is possible to efficiently annotate document relevance in RAG systems using fine-tuned open-source LLMs, achieving GPT-4-level performance with smaller (8B) models. The approach addresses the challenge of domain-specific relevance definitions beyond shallow semantic similarity, enabling scalable annotation of (query, document) pairs with calibrated relevance scores for improved retrieval evaluation.

### ClimRetrieve

[ClimRetrieve](https://arxiv.org/abs/2406.09818) showed that it is possible to create comprehensive benchmarking datasets for information retrieval from corporate climate disclosures. The dataset, comprising over 8.5K unique question-source-answer pairs from 30 sustainability reports with 16 detailed climate-related questions, demonstrated both the potential and limitations of embedding-based retrieval in knowledge-intensive domains like climate change communication.

### Ongoing Benchmarking Collaboration

Open Sustainability Analyst is actively developed in collaboration with research partners including the University of Zurich (UZH), LMU München, and Leuphana Universität Lüneburg, as part of the [AI Benchmark for Sustainability Report Analysis](https://climateandtech.com/en/research-projects/sustainability-ai-benchmark-and-dataset) project. This ongoing collaboration aims to improve the accuracy and transparency of AI pipelines for sustainability report analysis through systematic benchmarking, evaluation of retrieval strategies, and validation of analysis methods against expert-annotated datasets.

These research foundations inform the design choices in Open Sustainability Analyst, including the emphasis on evidence-based answers, configurable chunking strategies, systematic experimentation capabilities, and the integration of LLM-based chunk selection for improved retrieval performance.

---

## Integrating Into Production Systems & SaaS Solutions

Open Sustainability Analyst is designed for integration into production environments and scalable SaaS platforms. The modular architecture supports various deployment patterns.

### Production Deployment Options

| Deployment Pattern | Use Case | Modules Required |
|-------------------|----------|------------------|
| **Standalone Analyst Tool** | Internal team usage, local analysis | `report_analyst/` only |
| **REST API Service** | Integrate into existing platforms, microservices architecture | `report_analyst/` + `report_analyst_api/` |
| **Async Job Processing** | High-volume batch analysis, background processing | `report_analyst/` + `report_analyst_jobs/` |
| **Full Backend Integration** | Enterprise SaaS with upload, search, and distributed processing | All modules + external dependencies (NATS, S3, etc.) |

### Scalable Architecture Components

| Component | Purpose | Integration Points |
|-----------|---------|-------------------|
| **Core Analysis Engine** | Document processing, chunking, LLM analysis | Import as Python package in your application |
| **REST API** | Stateless HTTP endpoints for analysis requests | Load-balanced API servers, API gateway integration |
| **Job Queue (NATS/Celery)** | Async processing, job coordination, horizontal scaling | Message broker integration, worker pools |
| **Search Backend** | Document upload, S3 storage, distributed processing | CDN integration, object storage, caching layers |

### Production Integration Patterns

**Microservices Integration:**
```bash
# Deploy core API as a microservice
cd report_analyst_api
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

**Async Job Processing (NATS):**
```bash
# Start NATS workers for distributed analysis
python -m report_analyst_jobs.nats_integration
```

**AWS Lambda/Serverless:**
```python
# Use standalone analysis functions
from report_analyst_jobs import analyze_document_standalone
# See report_analyst_jobs/integration_examples.py for Lambda patterns
```

**SaaS Platform Integration:**
- **User Upload** → S3/Object Storage → NATS message → Worker pool analysis
- **API Endpoints** → Load balancer → Multiple API instances → Shared cache
- **Multi-tenancy** → Separate databases per tenant, isolated job queues
- **Rate Limiting** → API gateway, token-based authentication, usage tracking

### Testing & CI/CD

```bash
# Run comprehensive test suite
pip install pytest pytest-cov pytest-asyncio
export QUESTIONSETS_PATH=report_analyst/questionsets
pytest tests/ -v --cov=report_analyst --cov-report=term-missing
```

**macOS ARM (Apple Silicon):** If you see a crash in `libopenblas` / `gemm_thread_n` (SIGSEGV), set `OPENBLAS_NUM_THREADS=1` before running. The API and test conftest set this by default; for other entry points use `export OPENBLAS_NUM_THREADS=1` in your shell or add it to `.env`.

For detailed deployment patterns (Docker, Kubernetes, NATS workers, etc.), see:
- `INSTALL.md` – Installation and configuration options
- `report_analyst_jobs/README.md` – Job processing and worker patterns
- `docs/CI.md` – Continuous integration and testing

---

## Licensing and Open-Core Model

The repository uses a **module-based licensing model**:

| Module / Path                        | Purpose                                      | License                                        |
|-------------------------------------|----------------------------------------------|------------------------------------------------|
| `report_analyst/`                   | Core analysis engine and Streamlit app       | **RPL – Reciprocal Public License** (open)     |
| `report_analyst_api/`              | FastAPI API module                           | **Climate+Tech Open License for Good**         |
| `report_analyst_jobs/`             | Jobs, NATS, integration toolkit              | **Climate+Tech Open License for Good**         |
| `report_analyst_search_backend/`   | Search/upload backend integration            | **Climate+Tech Open License for Good**         |

The core analysis module `report_analyst/` is open source under the RPL (Reciprocal Public License). All other modules (API, jobs, search backend, etc.) are provided under the Climate+Tech Open License for Good, and can be dual-licensed for commercial or special use cases upon request.

This separation exists so that:
- Researchers and open-source users can rely on a clearly licensed open core.
- Organizations can use additional modules under clear, purpose-driven terms and request commercial/dual licensing where needed.

For full license texts and commercial/dual-licensing inquiries, please contact Climate+Tech via the website:
- [OpenSustainability Analysis Framework](https://climateandtech.com/en/climate-ai-solutions/opensustainability-analysis-framework)
- [AI Benchmark for Sustainability Reports](https://climateandtech.com/en/research-projects/sustainability-ai-benchmark-and-dataset)

---

## Support, Collaboration, and Research

Open Sustainability Analyst is developed as part of Climate+Tech's research and open-source efforts on:
- **AI Benchmark for Sustainability Reports** – benchmarking pipelines, models, and greenwashing detection.
- **ChatReport and related research** – evidence-based question answering over sustainability reports.

If you are a researcher working on sustainability, ESG, or AI benchmarks; a sustainability analyst wanting to use or test the tool; or an organization needing integrations, support, or licensing, you can reach out via the Climate+Tech website:
- [Open Sustainability Analysis Framework – Climate+Tech](https://climateandtech.com/en/climate-ai-solutions/opensustainability-analysis-framework)
- [AI Benchmark for Sustainability Report Analysis](https://climateandtech.com/en/research-projects/sustainability-ai-benchmark-and-dataset)

---

## Summary

Open Sustainability Analyst gives you:
- A **research-backed**, open-core engine for sustainability report analysis.
- A **user-friendly Streamlit app** for analysts.
- A **modular architecture** that can grow with APIs, jobs, and backend integrations.

You keep control over your data, your analysis frameworks, and how the system is deployed.
