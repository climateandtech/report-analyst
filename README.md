# Report Analyst

A modern document analysis tool built with LangChain for analyzing corporate reports and documents.

## Features

- 📄 PDF and document processing
- 🤖 Advanced document analysis using LLMs
- 🔍 Customizable question & answer system
- 📊 Structured report generation
- 🎯 Modular prompt system
- 🚀 FastAPI backend
- ⚡ High performance document processing
- 🧪 Comprehensive test suite with CI/CD
- 🎨 Modern Streamlit UI with dynamic question loading

## Project Structure

```
report-analyst/
├── report_analyst/         # Main application code
│   ├── core/              # Core business logic
│   ├── questionsets/      # Question set YAML files
│   ├── streamlit_app.py   # Main Streamlit application
│   └── streamlit_app_backend.py  # Backend integration
├── report_analyst_api/     # FastAPI backend
├── report_analyst_jobs/    # Background job processing
├── report_analyst_search_backend/  # Search backend
├── prompts/               # Modular prompt templates
│   ├── analysis/         # Document analysis prompts
│   └── qa/               # Q&A prompts
├── tests/                # Comprehensive test suite
│   ├── test_streamlit_app*.py  # Streamlit AppTest tests
│   ├── test_question_loader.py # Question loader tests
│   └── integration/      # Integration tests
├── .github/workflows/     # GitHub Actions CI/CD
└── data/                  # Data directory
    ├── input/            # Input documents
    └── output/           # Generated outputs
```

## Question Set Naming Convention

This project uses a **mountain peak naming convention** for question sets to enable scalable versioning:

### Current Question Sets:
- **`everest_questions.yaml`** - Comprehensive sustainability labeling framework (35 questions, prefix: `ev_`)
- **`tcfd_questions.yaml`** - TCFD climate disclosure questions (prefix: `tcfd_`)
- **`kilimanjaro_questions.yaml`** - Kilimanjaro sustainability questions (prefix: `kilimanjaro_`)
- **`denali_questions.yaml`** - Denali sustainability analysis questions (prefix: `denali_`)

### Future Naming Pattern:
| Version | Mountain | File | Prefix |
|---------|----------|------|--------|
| 1 | **Everest** | `everest_questions.yaml` | `ev_` |
| 2 | **Kilimanjaro** | `kilimanjaro_questions.yaml` | `ki_` |
| 3 | **Denali** | `denali_questions.yaml` | `de_` |
| 4 | **Matterhorn** | `matterhorn_questions.yaml` | `ma_` |
| 5 | **Fuji** | `fuji_questions.yaml` | `fu_` |

This system provides hundreds of unique names for future question set iterations while maintaining memorable, professional naming.

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file:
```
OPENAI_API_KEY=your_api_key_here
OPENAI_ORGANIZATION=your_organization_id  # Optional
OPENAI_API_MODEL=gpt-4o-mini             # Default model

# For Gemini models
GOOGLE_API_KEY=your_google_api_key_here  # Required for Gemini models
```

4. Run the application:
```bash
uvicorn app.main:app --reload
# Or use the Streamlit interface
streamlit run app/streamlit_app.py
```

## Available LLM Models

The application supports multiple LLM providers:

### OpenAI Models (requires OPENAI_API_KEY)
- gpt-4o-mini
- gpt-4o
- gpt-3.5-turbo

### Google Gemini Models (requires GOOGLE_API_KEY)
- gemini-flash-2.0
- gemini-pro

Models will only be available in the UI if you have the corresponding API key configured.

## CI/CD and Testing

This project includes comprehensive CI/CD with GitHub Actions:

### Test Coverage
- **41 Streamlit AppTest tests** covering all UI functionality
- **Question loader tests** with 100% coverage
- **Integration tests** for API and backend components
- **Multi-Python version testing** (3.8-3.12)

### GitHub Actions Workflows
- **Basic Tests**: Essential functionality and imports
- **Question Loader Tests**: Dynamic question set loading
- **Streamlit Tests**: Complete UI testing with AppTest
- **API Tests**: FastAPI backend testing
- **Full CI**: Comprehensive testing with linting and security scanning

### Running Tests Locally
```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio

# Set environment variables
export QUESTIONSETS_PATH=report_analyst/questionsets
export OPENAI_API_KEY=your_key
export GOOGLE_API_KEY=your_key

# Run all tests
pytest tests/ -v --cov=report_analyst --cov-report=term-missing

# Run specific test suites
pytest tests/test_streamlit_app*.py -v  # Streamlit tests
pytest tests/test_question_loader.py -v  # Question loader tests
```

## Usage

### Streamlit App
```bash
# Run the main Streamlit application
streamlit run report_analyst/streamlit_app.py
```

### API Backend
```bash
# Run the FastAPI backend
cd report_analyst_api
uvicorn main:app --reload
```

### Document Analysis
1. Place your documents in the `data/input` directory
2. Use the Streamlit UI or API endpoints to:
   - Analyze documents with dynamic question sets
   - Ask questions about documents
   - Generate structured reports

## Customizing Prompts

The `prompts` directory contains modular prompt templates that can be customized for different use cases. Each prompt is a separate file that can be modified without affecting the core functionality.

## License

MIT License 