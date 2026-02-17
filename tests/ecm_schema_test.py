import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator

from tests.schema_test_helpers import (
    extract_enums,
    extract_descriptions,
    extract_patterns,
)


# ============================================================================
# Constants
# ============================================================================

# Paths
SCHEMA_PATH = (
    Path(__file__).parent.parent / "ecm_definitions" / "ecm_schema.json"
)
JSON_DIR = Path(__file__).parent.parent / "ecm_definitions"

# Files to exclude from validation
EXCLUDE_FILES = {"ecm_schema.json", "package_ecms.json"}

# ECM JSON files to validate
ECM_JSON_FILES = [
    json_file
    for json_file in JSON_DIR.glob("*.json")
    if json_file.name not in EXCLUDE_FILES
]


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture(scope="module")
def schema():
    """Load and return the ECM schema."""
    return json.loads(SCHEMA_PATH.read_text())


@pytest.fixture(scope="module")
def validator(schema):
    """Create and return the JSON schema validator."""
    return Draft202012Validator(schema)


# ============================================================================
# Tests
# ============================================================================

def test_schema_file_exists():
    """Test that the ECM schema file exists at expected location."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"


def test_schema_is_valid_json():
    """Test that the ECM schema file is valid JSON.

    Verifies that the schema file can be parsed as JSON without errors.
    """
    try:
        json.loads(SCHEMA_PATH.read_text())
    except json.JSONDecodeError as e:
        pytest.fail(f"Schema file is not valid JSON: {e}")


def test_schema_is_valid_json_schema(schema):
    """Test that the ECM schema is a valid JSON Schema (Draft-07).

    Verifies that the schema itself conforms to JSON Schema specification.
    This ensures the schema can be used for validation.
    """
    try:
        Draft202012Validator(schema)
        Draft202012Validator.check_schema(schema)
    except Exception as e:
        pytest.fail(f"Schema file is not a valid JSON Schema: {e}")


def test_schema_has_metadata(schema):
    """Test that ECM schema has proper metadata.

    Verifies the schema includes:
    - $schema: JSON Schema version (Draft-07)
    - $id: Unique schema identifier
    - version: Schema version number (semantic versioning)
    - title: Human-readable title
    - description: Comprehensive description

    These metadata fields are important for:
    - Schema identification and versioning
    - Documentation and tooling support
    - Professional schema quality standards
    - Integration with schema registries and validators
    """
    # Check required metadata fields exist
    assert "$schema" in schema, "Schema missing $schema"
    assert "$id" in schema, "Schema missing $id"
    assert "version" in schema, "Schema missing version"
    assert "title" in schema, "Schema missing title"
    assert "description" in schema, "Schema missing description"

    # Check values are not empty
    assert schema.get("version"), "Schema version is empty"
    assert schema.get("title"), "Schema title is empty"
    assert schema.get("description"), "Schema description is empty"

    # Verify version format (semantic versioning: x.y.z)
    version = schema.get("version", "")
    assert version.count(".") >= 2, (
        f"Schema version should be semantic (e.g., 1.0.0), "
        f"got: {version}"
    )


@pytest.mark.parametrize("json_file", ECM_JSON_FILES, ids=lambda f: f.name)
def test_ecm_json_schema_validation(json_file, validator):
    """Test that each ECM definition validates against ecm_schema.json.

    Validates all ECM definition JSON files in the ecm_definitions directory
    against the ECM schema. Provides comprehensive error messages including:
    - Actual value that failed validation
    - Schema descriptions for context
    - Allowed values (enums) or patterns (regex)
    - Numeric/string constraints (min/max, lengths)
    - Type requirements and format specifications
    - Data and schema paths for debugging

    Example validation errors caught:
    - Invalid cost_units
      (e.g., "20$/unit" missing 4-digit year prefix)
    - Invalid energy_efficiency_units
      (e.g., "kW/h" instead of enum value like "COP")
    - Out-of-range numeric values
      (e.g., negative energy_efficiency with minimum: 0)
    - Missing required properties
      (e.g., "name", "climate_zone")
    - Invalid TSV nested structure
      (shed/shift/shape with wrong properties)
    - Malformed htcl_tech_link patterns
    - Empty strings where minLength: 1 is required
    - Wrong data types (e.g., string instead of number)
    """
    # Load JSON data
    data = json.loads(json_file.read_text())

    # Collect validation errors
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    # Build error message if validation fails
    if errors:
        messages = []
        for e in errors:
            data_path = "/".join(str(p) for p in e.path)
            schema_path_str = "/".join(str(p) for p in e.schema_path)

            # Get the actual value that failed validation
            actual_value = e.instance

            # Build comprehensive error information
            allowable_info = []

            # Collect descriptions
            descriptions = extract_descriptions(e.schema, validator)

            # Handle anyOf/oneOf schemas by extracting enum values
            for schema_key in ["anyOf", "oneOf"]:
                if schema_key in e.schema:
                    all_enums = extract_enums(
                        e.schema, validator
                    )
                    # Remove duplicates
                    if all_enums:
                        all_enums = sorted(set(all_enums))
                        allowable_info.append(f"allowed values: {all_enums}")

                    # Extract patterns from anyOf/oneOf
                    all_patterns = extract_patterns(e.schema, validator)
                    if all_patterns:
                        # Show first pattern (usually most relevant)
                        allowable_info.append(
                            f"expected pattern: {all_patterns[0]}"
                        )
                    break  # Only process once

            # Extract direct constraints
            if "enum" in e.schema:
                allowable_info.append(f"allowed values: {e.schema['enum']}")
            if "type" in e.schema:
                allowable_info.append(f"expected type: {e.schema['type']}")
            if "pattern" in e.schema:
                pattern = e.schema['pattern']
                allowable_info.append(f"expected pattern: {pattern}")
            if "minimum" in e.schema:
                allowable_info.append(f"minimum: {e.schema['minimum']}")
            if "maximum" in e.schema:
                allowable_info.append(f"maximum: {e.schema['maximum']}")
            if "minLength" in e.schema:
                min_len = e.schema['minLength']
                allowable_info.append(f"min length: {min_len}")
            if "maxLength" in e.schema:
                max_len = e.schema['maxLength']
                allowable_info.append(f"max length: {max_len}")
            if "format" in e.schema:
                fmt = e.schema['format']
                allowable_info.append(f"expected format: {fmt}")

            msg_parts = [
                f"ERROR: {e.message}",
                "",  # Blank line for readability
                "Location:",
                f"  data path: {data_path}",
                f"  schema path: {schema_path_str}",
            ]

            # Add actual value section
            if isinstance(actual_value, (dict, list)) and len(
                json.dumps(actual_value)
            ) > 100:
                # For large objects, show truncated version
                value_str = json.dumps(actual_value)[:100] + "..."
                msg_parts.extend([
                    "",
                    "Actual Value:",
                    f"  {value_str}",
                ])
            else:
                msg_parts.extend([
                    "",
                    "Actual Value:",
                    f"  {json.dumps(actual_value)}",
                ])

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

            messages.append("\n".join(msg_parts))

        error_message = (
            f"\n{'='*70}\n"
            f"{json_file.name} is invalid\n"
            f"{'='*70}\n\n" +
            "\n\n".join(f"{msg}" for msg in messages)
        )
        pytest.fail(error_message)
