# Report Analyst Service Discovery Schema

This directory contains service discovery schemas that define the contract for compatible backend services. These schemas enable service discovery, validation, and integration.

## Schema Standards

We use industry-standard schema formats:

1. **AsyncAPI 2.6.0** (`asyncapi.yaml`) - For NATS messaging channels
   - Defines all NATS subjects/channels
   - Message formats and payloads
   - JetStream streams

2. **OpenAPI 3.1.0** (`openapi.yaml`) - For HTTP REST endpoints
   - Defines all REST API endpoints
   - Request/response formats
   - Authentication and error handling

3. **JSON Schema** (`service-contract.json`) - For service manifest validation
   - Combined service contract definition
   - Service capabilities and metadata
   - Validation rules

## Why These Standards?

- **AsyncAPI**: Industry standard for async messaging APIs (NATS, Kafka, RabbitMQ, etc.)
  - Similar to OpenAPI but designed for event-driven architectures
  - Widely supported by tooling (code generators, validators, documentation)
  - Enables automatic client/server generation

- **OpenAPI**: Industry standard for REST APIs
  - Used by Swagger, Postman, and many API tools
  - Enables automatic client generation
  - Standard format for API documentation

- **JSON Schema**: Standard for JSON data validation
  - Used by both AsyncAPI and OpenAPI internally
  - Enables runtime validation
  - Tooling support across languages

## Directory Structure

```
schemas/service-discovery/
├── README.md                 # This file
├── asyncapi.yaml             # AsyncAPI schema for NATS channels
├── openapi.yaml              # OpenAPI schema for HTTP REST endpoints
└── service-contract.json     # JSON Schema for service manifest validation
```

## Usage

### 1. Service Manifest

A backend service should provide a service manifest (JSON) that describes its capabilities:

```json
{
  "service_name": "search-backend",
  "version": "1.0.0",
  "contract_version": "1.0.0",
  "protocols": {
    "nats": {
      "enabled": true,
      "url": "nats://localhost:4222",
      "jetstream": true,
      "streams": ["DOCUMENTS", "ANALYSIS_JOBS"]
    },
    "http": {
      "enabled": true,
      "base_url": "http://localhost:8000"
    }
  },
  "nats_channels": {
    "publishes": [
      {
        "channel": "document.ready",
        "message_schema": "#/components/messages/DocumentReadyEvent"
      }
    ],
    "subscribes": [
      {
        "channel": "document.upload",
        "message_schema": "#/components/messages/DocumentUploadEvent"
      }
    ]
  },
  "http_endpoints": {
    "required": [
      {
        "method": "GET",
        "path": "/resources/",
        "operation_id": "listResources"
      }
    ]
  },
  "capabilities": {
    "document_processing": true,
    "semantic_search": true
  }
}
```

### 2. Validation

Use the Python validation module to validate service manifests:

```python
from report_analyst.core.service_discovery import ServiceValidator, validate_service_from_file

# Validate from file
result = validate_service_from_file(Path("service-manifest.json"))
if result.is_valid:
    print("Service is compatible!")
else:
    print(f"Errors: {result.errors}")

# Or validate a dictionary
validator = ServiceValidator()
manifest = {...}  # Your service manifest
result = validator.validate_service(manifest)
```

### 3. Generate Template

Generate a template service manifest:

```python
from report_analyst.core.service_discovery import ServiceValidator

validator = ServiceValidator()
template = validator.generate_service_template()
# Fill in the template with your service details
```

### 4. Get Required Interfaces

Query what interfaces a service must implement:

```python
from report_analyst.core.service_discovery import ServiceValidator

validator = ServiceValidator()

# Get required NATS channels
channels = validator.get_required_channels()
print("Must publish to:", channels["publish"])
print("Must subscribe to:", channels["subscribe"])

# Get required HTTP endpoints
endpoints = validator.get_required_endpoints()
for endpoint in endpoints:
    print(f"{endpoint['method']} {endpoint['path']}")
```

## NATS Channels

### Document Processing

- **`document.ready`** - Published when document processing is complete
  - Publisher: Search Backend
  - Subscriber: Report Analyst Workers
  - Message: `DocumentReadyEvent`

- **`document.upload`** - Published for S3+NATS document uploads
  - Publisher: Report Analyst Client
  - Subscriber: Search Backend
  - Message: `DocumentUploadEvent`

### Analysis Jobs

- **`analysis.job.submit`** - Submit an analysis job
  - Publisher: Report Analyst Client
  - Subscriber: Report Analyst Workers
  - Message: `AnalysisJobRequest`

- **`analysis.job.status`** - Job status updates
  - Publisher: Report Analyst Workers
  - Subscriber: Report Analyst Clients
  - Message: `AnalysisJobStatus`

- **`analysis.job.completed`** - Job completion notification
  - Publisher: Report Analyst Workers
  - Subscriber: Report Analyst Clients
  - Message: `AnalysisJobCompleted`

- **`analysis.job.failed`** - Job failure notification
  - Publisher: Report Analyst Workers
  - Subscriber: Report Analyst Clients
  - Message: `AnalysisJobFailed`

### LLM Service

- **`llm.request`** - Request LLM processing
  - Publisher: Report Analyst Client
  - Subscriber: LLM Worker (Search Backend)
  - Message: `LLMRequest`

- **`llm.response`** - LLM processing results
  - Publisher: LLM Worker (Search Backend)
  - Subscriber: Report Analyst Client
  - Message: `LLMResponse`

## HTTP REST Endpoints

### Resource Management

- `GET /resources/` - List all resources
- `POST /resources/text` - Upload a text resource
- `GET /resources/{resource_id}` - Get resource details

### Search

- `POST /search/` - Semantic search across resources

### Analysis

- `POST /analysis/jobs/` - Submit analysis job
- `GET /analysis/jobs/{job_id}` - Get analysis job status
- `GET /analysis/jobs/{job_id}/results` - Get analysis results
- `GET /analysis/results?resource_id={id}` - Get results by resource

### Health

- `GET /resources/count` - Get resource count (health check)

## Message Formats

All message formats are defined in the AsyncAPI and OpenAPI schemas. Key message types:

### DocumentReadyEvent
```json
{
  "resource_id": "uuid",
  "document_url": "https://...",
  "chunks_count": 42,
  "status": "ready",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### AnalysisJobRequest
```json
{
  "id": "job-uuid",
  "resource_id": "resource-uuid",
  "question_set": "tcfd",
  "analysis_config": {
    "model": "gpt-4o-mini",
    "temperature": 0.1
  },
  "status": "pending"
}
```

### LLMRequest
```json
{
  "id": "llm-uuid",
  "request_type": "analyze_question",
  "prompt": "...",
  "model": "gpt-4o-mini",
  "temperature": 0.1
}
```

## Tooling

### AsyncAPI Tools

- **AsyncAPI Studio**: Visual editor and documentation generator
  ```bash
   npx @asyncapi/studio asyncapi.yaml
   ```

- **AsyncAPI Generator**: Generate clients/servers from schema
  ```bash
   npx @asyncapi/generator asyncapi.yaml ./output -g python
   ```

### OpenAPI Tools

- **Swagger UI**: Interactive API documentation
  ```bash
   npx swagger-ui-watcher openapi.yaml
   ```

- **OpenAPI Generator**: Generate clients/servers
  ```bash
   npx @openapitools/openapi-generator-cli generate \
     -i openapi.yaml -g python -o ./output
   ```

### JSON Schema Tools

- **ajv-cli**: JSON Schema validator
  ```bash
   npm install -g ajv-cli
   ajv validate -s service-contract.json -d service-manifest.json
   ```

## Integration Checklist

For a backend service to be compatible with Report Analyst:

- [ ] Provide a service manifest JSON file
- [ ] Implement all required NATS channels (publish/subscribe)
- [ ] Implement all required HTTP REST endpoints
- [ ] Use message formats matching AsyncAPI schema
- [ ] Use request/response formats matching OpenAPI schema
- [ ] Validate manifest using `ServiceValidator`
- [ ] Document any custom extensions

## Versioning

- **Contract Version**: Version of the service contract schema (e.g., "1.0.0")
- **Service Version**: Version of the service implementation (e.g., "1.2.3")

Services should specify which contract version they implement. Backward compatibility is maintained within major versions.

## Extensions

Services may extend the contract with:
- Additional NATS channels (documented in manifest)
- Additional HTTP endpoints (marked as "optional")
- Custom message fields (must not conflict with required fields)

Extensions should be documented in the service manifest's `metadata` section.

## References

- [AsyncAPI Specification](https://www.asyncapi.com/docs/specifications/2.6.0)
- [OpenAPI Specification](https://swagger.io/specification/)
- [JSON Schema](https://json-schema.org/)
- [NATS Documentation](https://docs.nats.io/)

