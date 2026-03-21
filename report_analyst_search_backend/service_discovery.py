"""
Service Discovery and Contract Validation

This module provides utilities for validating backend services against
the Report Analyst service contract schemas (AsyncAPI for NATS, OpenAPI for HTTP).

Usage:
    from report_analyst.core.service_discovery import ServiceValidator

    validator = ServiceValidator()
    result = validator.validate_service(service_manifest)
    if result.is_valid:
        print("Service is compatible!")
    else:
        print(f"Validation errors: {result.errors}")
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import jsonschema
import yaml

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of service contract validation"""

    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []

    def __bool__(self):
        return self.is_valid

    def __str__(self):
        if self.is_valid:
            return "Validation passed"
        return f"Validation failed: {', '.join(self.errors)}"


class ServiceValidator:
    """Validates service manifests against the Report Analyst service contract"""

    def __init__(self, schema_dir: Optional[Path] = None):
        """
        Initialize validator with schema directory.

        Args:
            schema_dir: Directory containing service contract schemas.
                       Defaults to schemas/service-discovery/ in project root.
        """
        if schema_dir is None:
            # Find schema directory relative to this module (in enterprise module)
            schema_dir = Path(__file__).parent / "schemas" / "service-discovery"

        self.schema_dir = Path(schema_dir)
        self._contract_schema = None
        self._asyncapi_schema = None
        self._openapi_schema = None
        self._load_schemas()

    def _load_schemas(self):
        """Load all service contract schemas"""
        try:
            # Load JSON Schema for service contract
            contract_path = self.schema_dir / "service-contract.json"
            if contract_path.exists():
                with open(contract_path) as f:
                    self._contract_schema = json.load(f)

            # Load AsyncAPI schema (YAML)
            asyncapi_path = self.schema_dir / "asyncapi.yaml"
            if asyncapi_path.exists():
                with open(asyncapi_path) as f:
                    self._asyncapi_schema = yaml.safe_load(f)

            # Load OpenAPI schema (YAML)
            openapi_path = self.schema_dir / "openapi.yaml"
            if openapi_path.exists():
                with open(openapi_path) as f:
                    self._openapi_schema = yaml.safe_load(f)

            logger.info(f"Loaded service contract schemas from {self.schema_dir}")
        except Exception as e:
            logger.error(f"Failed to load schemas: {e}")
            raise

    def validate_service(self, service_manifest: Dict[str, Any]) -> ValidationResult:
        """
        Validate a service manifest against the service contract schema.

        Args:
            service_manifest: Service manifest dictionary (must match service-contract.json schema)

        Returns:
            ValidationResult with validation status and any errors/warnings
        """
        errors = []
        warnings = []

        if not self._contract_schema:
            return ValidationResult(
                False,
                errors=["Service contract schema not loaded"],
            )

        # Validate against JSON Schema
        try:
            jsonschema.validate(instance=service_manifest, schema=self._contract_schema)
        except jsonschema.ValidationError as e:
            errors.append(f"Schema validation error: {e.message} (path: {'.'.join(str(p) for p in e.path)})")
        except jsonschema.SchemaError as e:
            errors.append(f"Schema error: {e.message}")

        # Additional semantic validations
        if not errors:
            semantic_result = self._validate_semantics(service_manifest)
            errors.extend(semantic_result.errors)
            warnings.extend(semantic_result.warnings)

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
        )

    def _validate_semantics(self, manifest: Dict[str, Any]) -> ValidationResult:
        """Perform semantic validation beyond JSON Schema"""
        errors = []
        warnings = []

        # Check version compatibility
        contract_version = manifest.get("contract_version", "1.0.0")
        if contract_version != "1.0.0":
            warnings.append(
                f"Service uses contract version {contract_version}, " f"validator expects 1.0.0. Compatibility not guaranteed."
            )

        # Validate NATS channels exist in AsyncAPI schema
        if self._asyncapi_schema and manifest.get("protocols", {}).get("nats", {}).get("enabled"):
            nats_channels = manifest.get("nats_channels", {})
            published = [ch["channel"] for ch in nats_channels.get("publishes", [])]
            subscribed = [ch["channel"] for ch in nats_channels.get("subscribes", [])]

            all_channels = published + subscribed
            asyncapi_channels = self._asyncapi_schema.get("channels", {})

            for channel in all_channels:
                if channel not in asyncapi_channels:
                    warnings.append(f"NATS channel '{channel}' not defined in AsyncAPI schema. " f"May be a custom extension.")

        # Validate HTTP endpoints exist in OpenAPI schema
        if self._openapi_schema and manifest.get("protocols", {}).get("http", {}).get("enabled"):
            http_endpoints = manifest.get("http_endpoints", {})
            required_endpoints = http_endpoints.get("required", [])

            openapi_paths = self._openapi_schema.get("paths", {})

            for endpoint in required_endpoints:
                path = endpoint.get("path")
                method = endpoint.get("method", "GET").lower()
                operation_id = endpoint.get("operation_id")

                # Check if path exists in OpenAPI
                if path not in openapi_paths:
                    errors.append(f"Required endpoint {method.upper()} {path} not defined in OpenAPI schema")
                else:
                    # Check if method exists for this path
                    path_item = openapi_paths[path]
                    if method not in path_item:
                        errors.append(f"Method {method.upper()} not defined for endpoint {path} in OpenAPI schema")
                    else:
                        # Check if operation_id matches
                        operation = path_item[method]
                        if operation.get("operationId") != operation_id:
                            warnings.append(
                                f"Operation ID mismatch for {method.upper()} {path}: "
                                f"manifest has '{operation_id}', OpenAPI has '{operation.get('operationId')}'"
                            )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def get_required_channels(self) -> Dict[str, List[str]]:
        """
        Get list of required NATS channels from AsyncAPI schema.

        Returns:
            Dictionary with 'publish' and 'subscribe' channel lists
        """
        if not self._asyncapi_schema:
            return {"publish": [], "subscribe": []}

        channels = self._asyncapi_schema.get("channels", {})
        return {
            "publish": list(channels.keys()),
            "subscribe": list(channels.keys()),
        }

    def get_required_endpoints(self) -> List[Dict[str, str]]:
        """
        Get list of required HTTP endpoints from OpenAPI schema.

        Returns:
            List of endpoint dictionaries with 'method' and 'path'
        """
        if not self._openapi_schema:
            return []

        endpoints = []
        paths = self._openapi_schema.get("paths", {})

        for path, path_item in paths.items():
            for method in ["get", "post", "put", "delete", "patch"]:
                if method in path_item:
                    operation = path_item[method]
                    endpoints.append(
                        {
                            "method": method.upper(),
                            "path": path,
                            "operation_id": operation.get("operationId", ""),
                            "summary": operation.get("summary", ""),
                        }
                    )

        return endpoints

    def generate_service_template(self) -> Dict[str, Any]:
        """
        Generate a template service manifest based on the contract schema.

        Returns:
            Template dictionary that can be filled in by service implementers
        """
        return {
            "service_name": "your-service-name",
            "version": "1.0.0",
            "contract_version": "1.0.0",
            "protocols": {
                "nats": {
                    "enabled": True,
                    "url": "nats://localhost:4222",
                    "jetstream": True,
                    "streams": [],
                },
                "http": {
                    "enabled": True,
                    "base_url": "http://localhost:8000",
                    "api_version": "v1",
                },
            },
            "nats_channels": {
                "publishes": [],
                "subscribes": [],
            },
            "http_endpoints": {
                "required": [],
                "optional": [],
            },
            "capabilities": {
                "document_processing": False,
                "semantic_search": False,
                "llm_processing": False,
                "analysis_jobs": False,
                "s3_upload": False,
                "data_lake": False,
            },
            "metadata": {
                "description": "",
                "contact": {
                    "name": "",
                    "url": "",
                },
                "deployment": {
                    "environment": "development",
                },
            },
        }


def validate_service_from_file(manifest_path: Path) -> ValidationResult:
    """
    Convenience function to validate a service manifest from a file.

    Args:
        manifest_path: Path to service manifest JSON file

    Returns:
        ValidationResult
    """
    validator = ServiceValidator()

    with open(manifest_path) as f:
        manifest = json.load(f)

    return validator.validate_service(manifest)


# Example usage
if __name__ == "__main__":
    # Generate template
    validator = ServiceValidator()
    template = validator.generate_service_template()

    print("Service Contract Template:")
    print(json.dumps(template, indent=2))

    print("\nRequired NATS Channels:")
    channels = validator.get_required_channels()
    print(json.dumps(channels, indent=2))

    print("\nRequired HTTP Endpoints:")
    endpoints = validator.get_required_endpoints()
    print(json.dumps(endpoints, indent=2))
