import json
import pytest
import gzip
from pathlib import Path
from jsonschema import Draft202012Validator

from tests.schema_test_helpers import (
    extract_descriptions,
    extract_patterns,
)


# ============================================================================
# Test Configuration
# ============================================================================

# Define schema configurations
SCHEMA_CONFIGS = {
    "mseg": {
        "schema_file": "mseg_res_com_cz_schema.json",
        "data_file": "mseg_res_com_cz.json",
        "compressed": False,
        "filter_errors": [],
        "description": "Microsegment Stock and Energy Data",
    },
    "cpl": {
        "schema_file": "cpl_res_com_cz_schema.json",
        "data_file": "cpl_res_com_cz.gz",
        "compressed": True,
        "filter_errors": ["consumer choice"],
        # Filter consumer choice regex errors
        "description": "Cost, Performance, and Lifetime Data",
    },
}


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(params=["mseg", "cpl"], ids=lambda x: x)
def schema_config(request):
    """Return configuration for the current schema being tested."""
    return request.param, SCHEMA_CONFIGS[request.param]


@pytest.fixture
def schema_path(schema_config):
    """Return the path to the schema file."""
    schema_name, config = schema_config
    return (
        Path(__file__).parent.parent
        / "scout"
        / "supporting_data"
        / "stock_energy_tech_data"
        / config["schema_file"]
    )


@pytest.fixture
def data_path(schema_config):
    """Return the path to the data file."""
    schema_name, config = schema_config
    return (
        Path(__file__).parent.parent
        / "scout"
        / "supporting_data"
        / "stock_energy_tech_data"
        / config["data_file"]
    )


@pytest.fixture
def schema(schema_path):
    """Load and return the JSON schema."""
    schema_text = schema_path.read_text()
    return json.loads(schema_text)


@pytest.fixture
def data(data_path, schema_config):
    """Load and return JSON data (compressed and uncompressed)."""
    schema_name, config = schema_config

    if config["compressed"]:
        with gzip.open(data_path, "rt", encoding="utf-8") as f:
            return json.load(f)
    else:
        data_text = data_path.read_text()
        return json.loads(data_text)


# ============================================================================
# Tests
# ============================================================================

def test_schema_file_exists(schema_path):
    """Test that schema files exist at expected locations."""
    assert schema_path.exists(), f"Schema file not found at {schema_path}"


def test_schema_is_valid_json(schema_path):
    """Test that schema files are valid JSON.

    Verifies schema files can be parsed as JSON without errors.
    """
    try:
        json.loads(schema_path.read_text())
    except json.JSONDecodeError as e:
        pytest.fail(f"Schema file is not valid JSON: {e}")


def test_schema_is_valid_json_schema(schema):
    """Test that schemas are valid JSON Schemas (Draft-07).

    Verifies that schemas conform to JSON Schema specification.
    This ensures the schemas can be used for validation.
    """
    try:
        Draft202012Validator(schema)
        Draft202012Validator.check_schema(schema)
    except Exception as e:
        pytest.fail(f"Schema file is not a valid JSON Schema: {e}")


def test_schema_has_metadata(schema, schema_config):
    """Test that schemas have proper metadata.

    Verifies each schema includes:
    - $schema: JSON Schema version
    - $id: Unique schema identifier
    - version: Schema version number (semantic versioning)
    - title: Human-readable title
    - description: Comprehensive description

    These metadata fields are important for:
    - Schema identification and versioning
    - Documentation and tooling support
    - Professional schema quality standards

    Tested schemas:
    - mseg: Microsegment Stock and Energy Data schema
    - cpl: Cost, Performance and Lifetime Data schema
    """
    schema_name, _ = schema_config

    # Check required metadata fields exist
    assert "$schema" in schema, f"{schema_name}: Schema missing $schema"
    assert "$id" in schema, f"{schema_name}: Schema missing $id"
    assert "version" in schema, f"{schema_name}: Schema missing version"
    assert "title" in schema, (
        f"{schema_name}: Schema missing title"
    )
    assert "description" in schema, (
        f"{schema_name}: Schema missing description"
    )

    # Check values are not empty
    assert schema.get("version"), (
        f"{schema_name}: Schema version is empty"
    )
    assert schema.get("title"), (
        f"{schema_name}: Schema title is empty"
    )
    assert schema.get("description"), (
        f"{schema_name}: Schema description is empty"
    )

    # Verify version format (semantic versioning: x.y.z)
    version = schema.get("version", "")
    assert version.count(".") >= 2, (
        f"{schema_name}: Schema version should be semantic "
        f"(e.g., 1.0.0), got: {version}"
    )


def test_schema_data_validity(schema, data, data_path, schema_config):
    """Test that data files validate against their schemas.

    This unified test validates both microsegment and
    cost/performance/lifetime data files against their respective
    schemas. It provides comprehensive error messages including:
    - Expected patterns and constraints (year ranges, minimums, etc.)
    - Schema descriptions for context
    - Data and schema paths for debugging

    Example validation errors caught:
    - Invalid year keys (e.g., "2051" instead of valid range 2020-2050)
    - Negative values for numeric fields (minimum: 0 constraint)
    - Invalid climate zone keys (must be AIA_CZ1 through AIA_CZ5)
    - Missing required properties
    - Additional properties not allowed by schema
    - Empty strings where minLength: 1 is required

    Tested schemas:
    - mseg: Microsegment stock and energy data
      (mseg_res_com_cz.json)
    - cpl: Cost, performance, and lifetime data
      (cpl_res_com_cz.gz)
    """
    _, config = schema_config
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    if errors:
        error_messages = []
        for e in errors:
            # Filter specific errors based on configuration
            if config["filter_errors"]:
                skip_error = False
                for filter_term in config["filter_errors"]:
                    if (filter_term in e.message and
                            "does not match any of the regexes" in e.message):
                        skip_error = True
                        break
                if skip_error:
                    continue

            data_path_str = "/".join(str(p) for p in e.path)
            schema_path_str = "/".join(str(p) for p in e.schema_path)

            # Build comprehensive error information
            allowable_info = []

            # Extract descriptions
            descriptions = extract_descriptions(e.schema, validator)

            # Extract patterns
            patterns = extract_patterns(e.schema, validator)
            if patterns:
                # Show first pattern (most relevant)
                allowable_info.append(f"expected pattern: {patterns[0]}")

            # Extract numeric constraints
            if "minimum" in e.schema:
                allowable_info.append(f"minimum: {e.schema['minimum']}")
            if "maximum" in e.schema:
                allowable_info.append(f"maximum: {e.schema['maximum']}")

            # Extract type constraints
            if "type" in e.schema:
                allowable_info.append(f"expected type: {e.schema['type']}")

            # Build error message parts with JSON filename
            # prominently displayed
            msg_parts = [
                f"ERROR: {e.message}",
                "",  # Blank line for readability
                "File:",
                f"  {data_path.name}",
                "",
                "Data Path:",
                f"  {data_path_str}",
            ]

            # Add description if available
            if descriptions:
                msg_parts.extend([
                    "",
                    "Description:",
                    f"  {descriptions[0]}",
                ])

            # Add constraints if any
            if allowable_info:
                msg_parts.extend([
                    "",
                    "Expected Constraints:",
                    f"  {', '.join(allowable_info)}",
                ])

            # Add schema path
            msg_parts.extend([
                "",
                "Schema Path:",
                f"  {schema_path_str}",
            ])

            error_messages.append("\n".join(msg_parts))

        if error_messages:
            error_report = (
                f"\n{'='*70}\n"
                f"{data_path.name} is invalid\n"
                f"{'='*70}\n\n" +
                "\n\n".join(f"{msg}" for msg in error_messages)
            )
            pytest.fail(error_report)

    # If we reach here, validation passed
    assert True, f"{data_path.name} is valid"
