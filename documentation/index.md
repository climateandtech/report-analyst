# Open Sustainability Analyst

Guides for the analyst, plus an API reference generated from the Python docstrings.

Product site: [opensustainabilityanalyst.com](https://opensustainabilityanalyst.com/en)

## Guides

- [Report analysis](guides/report-analysis.md) — upload a PDF, pick a question set, and run Chunk through Answer.
- [Parameters](guides/parameters.md) — chunk size, overlap, top K, model, and LLM scoring.
- [Question sets](guides/question-sets.md) — the built-in frameworks and where their YAML lives.
- [Chunk highlighting](guides/chunk-highlighting.md) — open an evidence chunk on its PDF page (enterprise viewer).
- [Benchmarking](guides/benchmarking.md) — score retrieval against an expert reference, including ClimRetrieve.

## API reference

The [overview](reference/index.md) is the map. Each reference page is labeled **Core** (`report_analyst/`, Reciprocal Public License) or **Enterprise** (Climate+Tech Open License for Good). The class and function sections are generated with [mkdocstrings](https://mkdocstrings.github.io/). Adding a public symbol to one of those pages publishes its docstring on the next docs build.

## Setup

Install and deploy guides live on the product site:

- [Deploy on Render](https://opensustainabilityanalyst.com/en/sustainability-report-analysis-with-ai-render-setup)
- [Deploy on Streamlit](https://opensustainabilityanalyst.com/en/sustainability-report-analysis-with-ai-streamlit-setup)
- [Customize frameworks](https://opensustainabilityanalyst.com/en/esrs-analysis-customize-frameworks)
