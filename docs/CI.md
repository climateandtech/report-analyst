# GitHub Actions CI/CD

This repository uses GitHub Actions for continuous integration and testing of the **Open Sustainability Analyst** (open-core) and related modules.

Part of the **Open Sustainability Analysis** project by **Climate+Tech**.

## Workflows

### 1. Basic Tests (`basic-tests.yml`)
- **Purpose**: Essential functionality tests
- **Triggers**: Push to any branch, PR to main/develop
- **Tests**: 
  - Core module imports
  - Question loader functionality
  - Streamlit app imports
  - Question loader unit tests

### 2. Question Loader Tests (`question-loader.yml`)
- **Purpose**: Comprehensive question loader testing
- **Triggers**: Push to any branch, PR to main/develop
- **Tests**:
  - Question set loading
  - Dynamic question set options
  - All question loader unit tests

### 3. Streamlit App Tests (`test.yml`)
- **Purpose**: Streamlit application testing
- **Triggers**: Push to any branch, PR to main/develop
- **Tests**:
  - Core functionality tests
  - Streamlit app tests (41 tests)
  - App import verification

### 4. API Tests (`api-tests.yml`)
- **Purpose**: API component testing
- **Triggers**: Push to any branch, PR to main/develop
- **Tests**:
  - FastAPI app creation
  - API schema validation
  - API imports

### 5. Full CI (`ci.yml`)
- **Purpose**: Comprehensive testing across Python versions
- **Triggers**: Push to any branch, PR to main/develop
- **Tests**:
  - Multi-Python version testing (3.8-3.12)
  - Full test suite with coverage
  - Linting (black, isort, flake8, mypy)
  - Security scanning (safety, bandit)
  - Package build testing

## Test Coverage

The CI runs comprehensive tests including:

- **Unit Tests**: Core functionality, question loader, cache manager
- **Integration Tests**: Streamlit app, API components
- **App Tests**: 41 Streamlit AppTest-based tests covering:
  - App loading and initialization
  - Dynamic question set loading
  - File upload functionality
  - Tab functionality (Previous Reports, Upload New, Consolidated Results)
  - Configuration widgets and controls
  - Data display and visualization
  - Backend integration features
  - Error handling and fallback behavior

## Environment Setup

All workflows set up:
- Python 3.12 (or matrix of versions for full CI)
- System dependencies (libpoppler-cpp-dev, pkg-config)
- Python dependencies from requirements.txt
- Environment variables for testing
- Required directories (temp, data/cache, storage)

## Status Badges

Add these to your README.md:

```markdown
![Basic Tests](https://github.com/your-username/report-analyst/workflows/Basic%20Tests/badge.svg)
![Question Loader Tests](https://github.com/your-username/report-analyst/workflows/Question%20Loader%20Tests/badge.svg)
![Streamlit Tests](https://github.com/your-username/report-analyst/workflows/Test/badge.svg)
![API Tests](https://github.com/your-username/report-analyst/workflows/API%20Tests/badge.svg)
![Full CI](https://github.com/your-username/report-analyst/workflows/CI/badge.svg)
```

## Local Testing

To run the same tests locally:

```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio

# Set environment variables
export QUESTIONSETS_PATH=report_analyst/questionsets
export OPENAI_API_KEY=test_key
export GOOGLE_API_KEY=test_key

# Create directories
mkdir -p temp data/cache storage/cache storage/llm_cache

# Run tests
pytest tests/ -v --cov=report_analyst --cov-report=term-missing
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed and PYTHONPATH is set correctly
2. **Missing Files**: Check that all required directories exist
3. **Environment Variables**: Verify all required env vars are set
4. **System Dependencies**: Ensure libpoppler-cpp-dev is installed

### Debug Mode

To run tests with more verbose output:

```bash
pytest tests/ -v -s --tb=long
```

### Specific Test Files

```bash
# Test only question loader
pytest tests/test_question_loader.py -v

# Test only streamlit app
pytest tests/test_streamlit_app*.py -v

# Test with coverage
pytest tests/ --cov=report_analyst --cov-report=html
```
