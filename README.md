## Open Sustainability Analyst

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

## How This Fits Into the Climate+Tech Ecosystem

Open Sustainability Analyst is the open-core analysis app in a broader research and tooling ecosystem:

- **Open Sustainability Analysis Framework** – open-core AI toolkit for sustainability report analysis  
  ([framework overview](https://climateandtech.com/en/climate-ai-solutions/opensustainability-analysis-framework))
- **AI Benchmark for Sustainability Report Analysis** – research benchmark and dataset for evaluating AI pipelines and greenwashing detection  
  ([benchmark project](https://climateandtech.com/en/research-projects/sustainability-ai-benchmark-and-dataset))
- **ChatReport research and related projects** – academic work on evidence-based, explainable sustainability report analysis

The framework is developed together with partners such as:
- **University of Zurich (UZH)**
- **LMU München**
- **Leuphana Universität Lüneburg**
- **score4more** (tech & AI/ML innovation for sustainability)

These collaborations ensure that the analysis methods in this repository are **research-validated** and aligned with current work on benchmarking, greenwashing detection, and robust ESG analysis.

---

## Quick Start (for Analysts)

You need basic command line access, but no deep Python knowledge.

1. **Create and activate a virtual environment**

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install core dependencies**

```bash
pip install -r requirements.txt
```

3. **Set your API keys (for LLMs)**

Create a `.env` file in the project root:

```text
OPENAI_API_KEY=your_openai_key_here
OPENAI_API_MODEL=gpt-4o-mini

# Optional: Google Gemini support
GOOGLE_API_KEY=your_google_api_key_here
```

4. **Run the Streamlit app**

```bash
python -m streamlit run report_analyst/streamlit_app.py
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

## Analysis Frameworks (Question Sets)

Open Sustainability Analyst uses **preset question sets** (“frameworks”) that encode analysis logic for different use cases.

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

## For Technical Users

If you want to extend or integrate the tool:

- **Streamlit app**

```bash
python -m streamlit run report_analyst/streamlit_app.py
```

- **FastAPI backend**

```bash
cd report_analyst_api
uvicorn main:app --reload
```

- **Tests**

```bash
pip install pytest pytest-cov pytest-asyncio
export QUESTIONSETS_PATH=report_analyst/questionsets
pytest tests/ -v --cov=report_analyst --cov-report=term-missing
```

For deployment patterns (jobs, search backend, NATS workers, etc.), see:
- `INSTALL.md`
- `report_analyst_jobs/README.md`

---

## Licensing and Open-Core Model

The repository uses a **module-based licensing model**:

| Module / Path                        | Purpose                                      | License                                        |
|-------------------------------------|----------------------------------------------|------------------------------------------------|
| `report_analyst/`                   | Core analysis engine and Streamlit app       | **RPL – Reciprocal Public License** (open)     |
| `report_analyst_api/`              | FastAPI API module                           | **Climate+Tech Open License for Good**         |
| `report_analyst_jobs/`             | Jobs, NATS, integration toolkit              | **Climate+Tech Open License for Good**         |
| `report_analyst_search_backend/`   | Search/upload backend integration            | **Climate+Tech Open License for Good**         |

- The **core analysis module** `report_analyst/` is open source under the **RPL (Reciprocal Public License)**.
- All other modules (API, jobs, search backend, etc.) are provided under the  
  **Climate+Tech Open License for Good**, and can be **dual-licensed** for commercial or special use cases upon request.

This separation exists so that:
- Researchers and open-source users can rely on a clearly licensed **open core**.
- Organizations can use additional modules under **clear, purpose-driven terms** and request commercial/dual licensing where needed.

For full license texts and commercial/dual-licensing inquiries, please contact Climate+Tech via the website:
- [OpenSustainability Analysis Framework](https://climateandtech.com/en/climate-ai-solutions/opensustainability-analysis-framework)
- [AI Benchmark for Sustainability Reports](https://climateandtech.com/en/research-projects/sustainability-ai-benchmark-and-dataset)

---

## Support, Collaboration, and Research

Open Sustainability Analyst is developed as part of Climate+Tech’s research and open-source efforts on:
- **AI Benchmark for Sustainability Reports** – benchmarking pipelines, models, and greenwashing detection.
- **ChatReport and related research** – evidence-based question answering over sustainability reports.

If you are:
- A **researcher** working on sustainability, ESG, or AI benchmarks.
- A **sustainability analyst** wanting to use or test the tool.
- An **organization** needing integrations, support, or licensing.

You can reach out via the Climate+Tech website:
- [Open Sustainability Analysis Framework – Climate+Tech](https://climateandtech.com/en/climate-ai-solutions/opensustainability-analysis-framework)
- [AI Benchmark for Sustainability Report Analysis](https://climateandtech.com/en/research-projects/sustainability-ai-benchmark-and-dataset)

---

## Summary

Open Sustainability Analyst gives you:
- A **research-backed**, open-core engine for sustainability report analysis.
- A **user-friendly Streamlit app** for analysts.
- A **modular architecture** that can grow with APIs, jobs, and backend integrations.

You keep control over your data, your analysis frameworks, and how the system is deployed.
