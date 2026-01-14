# Open Sustainability Analyst – Jobs & Integrations

Universal analysis functions that use the same core logic as the Streamlit app.

Part of the **Open Sustainability Analysis** project by **Climate+Tech**.

## 🚀 Quick Start

```python
# AWS Lambda
from report_analyst_jobs import analyze_document_standalone
import asyncio

def lambda_handler(event, context):
    result = asyncio.run(analyze_document_standalone(
        document_id=event['document_id'],
        question_set_id=event['question_set_id'],
        selected_questions=event['selected_questions']
    ))
    return {'statusCode': 200, 'body': result}
```

```python
# Celery Worker
from report_analyst_jobs import analyze_document_sync

@app.task
def analyze_task(document_id, question_set_id, questions):
    return analyze_document_sync(document_id, question_set_id, questions)
```

## 📦 Installation

```bash
# Core dependency
pip install report-analyst

# This module
pip install report-analyst-jobs

# Optional: for specific integrations
pip install boto3          # For AWS Lambda
pip install celery redis   # For Celery
pip install nats-py        # For NATS
```

## 🔧 Functions

- `analyze_document_standalone()` - Async version
- `analyze_document_sync()` - Sync version  
- `analyze_document_with_progress()` - With progress callbacks
- `AnalysisToolkit` - Full toolkit class

## 📚 Examples

See `integration_examples.py` for complete examples of:
- AWS Lambda functions
- Celery tasks
- NATS workers
- FastAPI background tasks
- Search backend integration

## ⚖️ License

This module is part of the **Open Sustainability Analysis** project by **Climate+Tech**.

- **Core engine** (`report_analyst/`) is licensed under the **Reciprocal Public License (RPL)**
- **`report_analyst_jobs/`** is provided under the **Climate+Tech Open License for Good**, and can be **dual-licensed** for commercial or custom deployments upon request

See the main `README.md` for an overview and links, or contact Climate+Tech via:

- [OpenSustainability Analysis Framework](https://climateandtech.com/en/climate-ai-solutions/opensustainability-analysis-framework)
- [AI Benchmark for Sustainability Report Analysis](https://climateandtech.com/en/research-projects/sustainability-ai-benchmark-and-dataset)

## 🔗 Dependencies

This module requires the core `report_analyst` package and uses its analysis logic directly, ensuring consistency across all deployment environments. 

# NATS Integration MVP

This module provides async job coordination between the search backend and report-analyst using NATS messaging.

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Client      │    │  Search Backend │    │  NATS Worker    │
│                 │    │                 │    │                 │
│ 1. Upload PDF   │───▶│ 2. Process PDF  │    │                 │
│                 │    │   - Download    │    │                 │
│                 │    │   - Chunk       │    │                 │
│                 │    │   - Embed       │    │                 │
│                 │    │                 │    │                 │
│                 │    │ 3. Publish to   │───▶│ 4. Run Analysis │
│                 │    │    NATS         │    │   - Get chunks  │
│                 │    │                 │    │   - Use toolkit │
│                 │    │                 │    │   - Process Q&A │
│                 │    │                 │    │                 │
│ 6. Get Results  │◀───│ 5. Store Results│◀───│ 5. Publish      │
│                 │    │                 │    │    Results      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Flow

1. **Client** uploads PDF to search backend via REST API
2. **Search Backend** processes PDF via Celery (chunking, embedding)
3. When complete, **Search Backend** publishes "document.ready" event to NATS
4. **NATS Worker** receives event and runs analysis using existing chunks
5. **Analysis results** are published back via NATS
6. **Client** can poll search backend for results

## Key Benefits

- **Separation of Concerns**: Search backend handles PDF processing, NATS handles job coordination
- **Scalability**: Multiple NATS workers can process analysis jobs
- **Reliability**: JetStream persistence ensures jobs aren't lost
- **Flexibility**: Can be deployed in various configurations (local, cloud, hybrid)

## Quick Start

### 1. Start NATS Server

```bash
# Using Docker
docker run -p 4222:4222 nats:latest

# Or install locally: https://docs.nats.io/running-a-nats-service/introduction/installation
```

### 2. Install Dependencies

```bash
cd report_analyst_jobs
pip install -r requirements.txt
```

### 3. Run the Example

```bash
# Test NATS connection
python mvp_example.py test

# Run full simulation
python mvp_example.py simulate

# Or run components separately:
# Terminal 1: Start worker
python mvp_example.py worker

# Terminal 2: Submit job
python mvp_example.py submit
```

## Integration

### For Search Backend

Add to your Celery task that processes PDFs:

```python
from report_analyst_jobs.search_backend_integration import notify_document_ready_sync

def embed_chunks_service(db: Session, resource_id: uuid.UUID):
    # ... existing PDF processing logic ...
    
    # After successful processing, notify NATS
    try:
        resource = crud.get_resource(db, resource_id)
        if resource and resource.status == ResourceStatus.COMPLETED:
            notify_document_ready_sync(
                resource_id=str(resource_id),
                document_url=resource.url,
                chunks_count=len(resource.chunks)
            )
    except Exception as e:
        logging.error(f"Failed to notify NATS: {e}")
        # Continue - not critical for main processing
```

### For Analysis Workers

Deploy workers that process analysis jobs:

```python
from report_analyst_jobs.nats_integration import NATSAnalysisWorker

async def main():
    worker = NATSAnalysisWorker()
    await worker.start()

if __name__ == "__main__":
    asyncio.run(main())
```

### For Clients

Submit analysis jobs:

```python
from report_analyst_jobs.nats_integration import NATSAnalysisClient

async def analyze_document(resource_id: str):
    async with NATSAnalysisClient() as client:
        job_id = await client.analyze_resource(
            resource_id=resource_id,
            question_set="tcfd",
            analysis_config={"model": "gpt-4o-mini"}
        )
        
        result = await client.wait_for_completion(job_id)
        return result
```

## Configuration

### Environment Variables

```bash
# NATS Configuration
NATS_URL=nats://localhost:4222

# Search Backend Configuration  
SEARCH_BACKEND_URL=http://localhost:8000

# Analysis Configuration
DEFAULT_MODEL=gpt-4o-mini
DEFAULT_QUESTION_SET=tcfd
```

### NATS Streams

The system creates these JetStream streams:

- **DOCUMENTS**: For document ready events (`document.*`)
- **ANALYSIS_JOBS**: For analysis job coordination (`analysis.*`)

## Deployment Patterns

### 1. Development (All Local)

```bash
# Terminal 1: NATS
docker run -p 4222:4222 nats:latest

# Terminal 2: Search Backend  
cd ../thinktank2/search/backend
python -m uvicorn app.main:app --reload

# Terminal 3: Analysis Worker
cd report_analyst_jobs
python mvp_example.py worker

# Terminal 4: Test Client
python mvp_example.py simulate
```

### 2. Production (Distributed)

```yaml
# docker-compose.yml
version: '3.8'
services:
  nats:
    image: nats:latest
    ports:
      - "4222:4222"
      
  search-backend:
    build: ./search/backend
    environment:
      - NATS_URL=nats://nats:4222
    depends_on:
      - nats
      
  analysis-worker:
    build: ./report-analyst
    environment:
      - NATS_URL=nats://nats:4222
      - SEARCH_BACKEND_URL=http://search-backend:8000
    depends_on:
      - nats
      - search-backend
    deploy:
      replicas: 3  # Scale analysis workers
```

### 3. Cloud (AWS Lambda + NATS Cloud)

```python
# Lambda function for analysis
import json
from report_analyst_jobs.analysis_toolkit import analyze_document_with_chunks

def lambda_handler(event, context):
    # Parse NATS message from event bridge
    job_data = json.loads(event['Records'][0]['body'])
    
    # Run analysis
    result = analyze_document_with_chunks(
        chunks=job_data['chunks'],
        question_set=job_data['question_set'],
        config=job_data['config']
    )
    
    # Publish result back to NATS
    # ... 
```

## Monitoring

### NATS Metrics

```bash
# Check stream status
nats stream info ANALYSIS_JOBS

# Monitor message rates
nats stream report ANALYSIS_JOBS
```

### Application Logs

All components log important events:

- 🔄 PDF processing start/complete
- 📢 NATS event publishing  
- 🎯 Analysis job submission
- ✅ Analysis completion
- ❌ Error handling

## Files Overview

- **`nats_integration.py`** - Core NATS coordination classes
- **`search_backend_integration.py`** - Helper for search backend integration
- **`analysis_toolkit.py`** - Universal analysis functions
- **`mvp_example.py`** - Complete working example
- **`requirements.txt`** - NATS dependencies

## Next Steps

1. **Test with Real PDFs**: Use actual search backend with real documents
2. **Add Error Handling**: Implement retry logic and dead letter queues
3. **Scale Workers**: Deploy multiple analysis workers
4. **Add Monitoring**: Integrate with monitoring tools (Prometheus, DataDog)
5. **Cloud Deployment**: Deploy to AWS/GCP with managed NATS 