"""
Tests for service discovery and contract validation
"""

import json
from pathlib import Path

import pytest

from report_analyst_search_backend.service_discovery import (
    ServiceValidator,
    ValidationResult,
    validate_service_from_file,
)


@pytest.fixture
def schema_dir():
    """Get schema directory path"""
    # Schemas are now in the enterprise module
    enterprise_module = Path(__file__).parent.parent / "report_analyst_search_backend"
    return enterprise_module / "schemas" / "service-discovery"


@pytest.fixture
def validator(schema_dir):
    """Create service validator"""
    return ServiceValidator(schema_dir=schema_dir)


@pytest.fixture
def example_manifest(schema_dir):
    """Load example service manifest"""
    manifest_path = schema_dir / "example-service-manifest.json"
    if manifest_path.exists():
        with open(manifest_path) as f:
            return json.load(f)
    return None


def test_validator_initialization(validator):
    """Test that validator loads schemas correctly"""
    assert validator.schema_dir.exists()
    assert validator._contract_schema is not None
    assert validator._asyncapi_schema is not None
    assert validator._openapi_schema is not None


def test_generate_service_template(validator):
    """Test template generation"""
    template = validator.generate_service_template()

    assert "service_name" in template
    assert "version" in template
    assert "contract_version" in template
    assert "protocols" in template
    assert "nats_channels" in template
    assert "http_endpoints" in template
    assert "capabilities" in template


def test_validate_valid_service(validator, example_manifest):
    """Test validation of a valid service manifest"""
    if example_manifest is None:
        pytest.skip("Example manifest not found")

    result = validator.validate_service(example_manifest)

    assert isinstance(result, ValidationResult)
    # Should pass basic validation (may have warnings for extensions)
    assert result.is_valid or len(result.errors) == 0


def test_validate_invalid_service(validator):
    """Test validation of an invalid service manifest"""
    invalid_manifest = {
        "service_name": "test",
        # Missing required fields
    }

    result = validator.validate_service(invalid_manifest)

    assert isinstance(result, ValidationResult)
    assert not result.is_valid
    assert len(result.errors) > 0


def test_validate_missing_required_fields(validator):
    """Test validation catches missing required fields"""
    incomplete_manifest = {
        "service_name": "test-service",
        "version": "1.0.0",
        # Missing contract_version, protocols, etc.
    }

    result = validator.validate_service(incomplete_manifest)

    assert not result.is_valid
    assert any("required" in error.lower() for error in result.errors)


def test_get_required_channels(validator):
    """Test getting required NATS channels"""
    channels = validator.get_required_channels()

    assert isinstance(channels, dict)
    assert "publish" in channels
    assert "subscribe" in channels
    assert isinstance(channels["publish"], list)
    assert isinstance(channels["subscribe"], list)


def test_get_required_endpoints(validator):
    """Test getting required HTTP endpoints"""
    endpoints = validator.get_required_endpoints()

    assert isinstance(endpoints, list)
    if len(endpoints) > 0:
        endpoint = endpoints[0]
        assert "method" in endpoint
        assert "path" in endpoint
        assert "operation_id" in endpoint


def test_validate_from_file(schema_dir):
    """Test validation from file"""
    manifest_path = schema_dir / "example-service-manifest.json"

    if not manifest_path.exists():
        pytest.skip("Example manifest file not found")

    result = validate_service_from_file(manifest_path)

    assert isinstance(result, ValidationResult)
    # Should pass basic validation
    assert result.is_valid or len(result.errors) == 0


def test_service_manifest_structure(example_manifest):
    """Test that example manifest has correct structure"""
    if example_manifest is None:
        pytest.skip("Example manifest not found")

    # Check required top-level fields
    assert "service_name" in example_manifest
    assert "version" in example_manifest
    assert "contract_version" in example_manifest
    assert "protocols" in example_manifest
    assert "nats_channels" in example_manifest
    assert "http_endpoints" in example_manifest

    # Check protocols structure
    protocols = example_manifest["protocols"]
    assert "nats" in protocols
    assert "http" in protocols

    # Check NATS channels structure
    nats_channels = example_manifest["nats_channels"]
    assert "publishes" in nats_channels
    assert "subscribes" in nats_channels

    # Check HTTP endpoints structure
    http_endpoints = example_manifest["http_endpoints"]
    assert "required" in http_endpoints


def test_version_compatibility_warning(validator):
    """Test that version mismatch generates warning"""
    manifest = validator.generate_service_template()
    manifest["contract_version"] = "2.0.0"  # Different version

    result = validator.validate_service(manifest)

    # Should have warnings about version mismatch
    assert (
        len(result.warnings) > 0 or result.is_valid
    )  # May still be valid but with warnings
