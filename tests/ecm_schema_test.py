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
            descriptions = []

            # Helper function to resolve $ref
            def resolve_ref(schema, depth=0, max_depth=10):
                """Resolve a $ref to its actual schema definition."""
                if depth > max_depth or "$ref" not in schema:
                    return schema
                ref_path = schema["$ref"]
                if ref_path.startswith("#/definitions/"):
                    def_name = ref_path.split("/")[-1]
                    resolved = validator.schema.get("definitions", {}).get(def_name, {})
                    return resolve_ref(resolved, depth + 1)
                return schema

            # Helper function to recursively extract enums from schema
            def extract_enums(schema, depth=0, max_depth=10):
                """Recursively extract enum values from a schema.

                Handles anyOf (and legacy oneOf) structures with nested
                $ref definitions and array items.
                """
                if depth > max_depth:
                    return []

                enums = []

                # Direct enum
                if "enum" in schema:
                    enums.extend(schema["enum"])
                    return enums

                # Handle anyOf (standard) and oneOf (legacy support)
                for key in ["anyOf", "oneOf"]:
                    if key in schema:
                        for sub_schema in schema[key]:
                            enums.extend(extract_enums(sub_schema, depth + 1))

                # Handle $ref
                if "$ref" in schema:
                    resolved = resolve_ref(schema, depth)
                    if resolved != schema:
                        enums.extend(extract_enums(resolved, depth + 1))

                # Handle array items
                if "items" in schema:
                    enums.extend(extract_enums(schema["items"], depth + 1))

                return enums

            # Extract descriptions from anyOf/oneOf schemas
            def extract_descriptions(schema, depth=0, max_depth=10):
                """Extract descriptions from schema and its references."""
                if depth > max_depth:
                    return []
                descs = []
                if "description" in schema:
                    descs.append(schema["description"])
                
                for key in ["anyOf", "oneOf"]:
                    if key in schema:
                        for sub_schema in schema[key]:
                            resolved = resolve_ref(sub_schema, depth)
                            descs.extend(extract_descriptions(resolved, depth + 1))
                
                if "$ref" in schema and "description" not in schema:
                    resolved = resolve_ref(schema, depth)
                    if resolved != schema:
                        descs.extend(extract_descriptions(resolved, depth + 1))
                
                return descs

            # Extract patterns from anyOf/oneOf schemas
            def extract_patterns(schema, depth=0, max_depth=10):
                """Extract pattern constraints from schema and its references."""
                if depth > max_depth:
                    return []
                patterns = []
                if "pattern" in schema:
                    patterns.append(schema["pattern"])
                
                for key in ["anyOf", "oneOf"]:
                    if key in schema:
                        for sub_schema in schema[key]:
                            resolved = resolve_ref(sub_schema, depth)
                            patterns.extend(extract_patterns(resolved, depth + 1))
                
                if "$ref" in schema and "pattern" not in schema:
                    resolved = resolve_ref(schema, depth)
                    if resolved != schema:
                        patterns.extend(extract_patterns(resolved, depth + 1))
                
                return patterns

            # Collect descriptions
            descriptions = extract_descriptions(e.schema)
            
            # Handle anyOf/oneOf schemas by extracting enum values
            for schema_key in ["anyOf", "oneOf"]:
                if schema_key in e.schema:
                    all_enums = extract_enums(e.schema)
                    # Remove duplicates
                    if all_enums:
                        all_enums = sorted(set(all_enums))
                        allowable_info.append(f"allowed values: {all_enums}")
                    
                    # Extract patterns from anyOf/oneOf
                    all_patterns = extract_patterns(e.schema)
                    if all_patterns:
                        # Show first pattern (usually most relevant)
                        allowable_info.append(f"expected pattern: {all_patterns[0]}")
                    break  # Only process once

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
            # Build the error message
            msg_parts = [
                f"{e.message}",
                f"    data path: {data_path}",
                f"    actual value: {json.dumps(actual_value)}",
            ]
            if descriptions:
                # Show first description (most specific)
                msg_parts.append(f"    description: {descriptions[0]}")
            if allowable_info:
                constraints = ', '.join(allowable_info)
                msg_parts.append(f"    constraints: {constraints}")
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
