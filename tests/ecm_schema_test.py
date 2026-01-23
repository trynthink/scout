import json
from pathlib import Path
import pytest
from jsonschema import Draft202012Validator


# Paths
SCHEMA_PATH = Path(__file__).parent.parent / "ecm_definitions" / "ecm_schema.json"
JSON_DIR = Path(__file__).parent.parent / "ecm_definitions"

# Files to exclude from validation
EXCLUDE_FILES = {"ecm_schema.json", "package_ecms.json"}


@pytest.fixture(scope="module")
def validator():
    """Load and return the JSON schema validator."""
    schema = json.loads(SCHEMA_PATH.read_text())
    return Draft202012Validator(schema)


@pytest.fixture(scope="module")
def json_files():
    """Collect all JSON files to validate."""
    return [
        json_file
        for json_file in JSON_DIR.glob("*.json")
        if json_file.name not in EXCLUDE_FILES
    ]


@pytest.mark.parametrize(
    "json_file",
    [
        json_file
        for json_file in (Path(__file__).parent.parent / "ecm_definitions").glob("*.json")
        if json_file.name not in EXCLUDE_FILES
    ],
    ids=lambda f: f.name,
)
def test_ecm_json_schema_validation(json_file, validator):
    """Test that each ECM definition JSON file validates against the schema."""
    # Load JSON data
    data = json.loads(json_file.read_text())

    # Collect validation errors
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    # Build error message if validation fails
    if errors:
        messages = []
        for e in errors:
            data_path = "/".join(str(p) for p in e.path)
            schema_path = "/".join(str(p) for p in e.schema_path)

            # Get the actual value that failed validation
            actual_value = e.instance
            # Build allowable values info from schema
            allowable_info = []
            if "enum" in e.schema:
                allowable_info.append(f"allowed values: {e.schema['enum']}")
            if "type" in e.schema:
                allowable_info.append(f"expected type: {e.schema['type']}")
            if "pattern" in e.schema:
                allowable_info.append(f"expected pattern: {e.schema['pattern']}")
            if "minimum" in e.schema:
                allowable_info.append(f"minimum: {e.schema['minimum']}")
            if "maximum" in e.schema:
                allowable_info.append(f"maximum: {e.schema['maximum']}")
            if "minLength" in e.schema:
                allowable_info.append(f"min length: {e.schema['minLength']}")
            if "maxLength" in e.schema:
                allowable_info.append(f"max length: {e.schema['maxLength']}")
            if "format" in e.schema:
                allowable_info.append(f"expected format: {e.schema['format']}")
            # Build the error message
            msg_parts = [
                f"{e.message}",
                f"    data path: {data_path}",
                f"    actual value: {json.dumps(actual_value)}",
            ]
            if allowable_info:
                msg_parts.append(f"    constraints: {', '.join(allowable_info)}")
            msg_parts.append(f"    schema path: {schema_path}")
            messages.append("\n".join(msg_parts))

        error_message = (
            f"{json_file.name} is invalid:\n" +
            "\n".join(f"  - {msg}" for msg in messages)
        )
        pytest.fail(error_message)


def test_schema_file_exists():
    """Test that the ECM schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"


def test_schema_is_valid_json():
    """Test that the schema file is valid JSON."""
    try:
        json.loads(SCHEMA_PATH.read_text())
    except json.JSONDecodeError as e:
        pytest.fail(f"Schema file is not valid JSON: {e}")


def test_schema_is_valid_json_schema():
    """Test that the schema file is a valid JSON Schema."""
    schema = json.loads(SCHEMA_PATH.read_text())
    # Check if the validator can be created (validates schema structure)
    try:
        Draft202012Validator(schema)
        # Check the schema itself for validity
        Draft202012Validator.check_schema(schema)
    except Exception as e:
        pytest.fail(f"Schema file is not a valid JSON Schema: {e}")
