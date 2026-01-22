import json
import pytest
import gzip
from pathlib import Path
from jsonschema import Draft202012Validator


@pytest.fixture
def schema_path():
    """Return the path to the schema file."""
    return (
        Path(__file__).parent.parent
        / "scout"
        / "supporting_data"
        / "stock_energy_tech_data"
        / "cpl_res_com_cz_schema.json"
    )


@pytest.fixture
def json_gz_path():
    """Return the path to the compressed JSON data file."""
    return (
        Path(__file__).parent.parent
        / "scout"
        / "supporting_data"
        / "stock_energy_tech_data"
        / "cpl_res_com_cz.gz"
    )


@pytest.fixture
def schema(schema_path):
    """Load and return the JSON schema."""
    schema_text = schema_path.read_text()
    return json.loads(schema_text)


@pytest.fixture
def data(json_gz_path):
    """Load and return the compressed JSON data."""
    with gzip.open(json_gz_path, "rt", encoding="utf-8") as f:
        return json.load(f)


def test_cpl_res_com_cz_schema_validity(schema, data, json_gz_path):
    """Test that cpl_res_com_cz.gz is valid according to its schema."""
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    if errors:
        error_messages = []
        for e in errors:
            # Skip specific error messages about consumer choice regex non-match
            if (
                "consumer choice" in e.message
                and "does not match any of the regexes" in e.message
            ):
                continue

            data_path = "/".join(str(p) for p in e.path)
            schema_path = "/".join(str(p) for p in e.schema_path)

            error_messages.append(
                f"{e.message}\n"
                f"    data path: {data_path}\n"
                f"    schema path: {schema_path}"
            )

        if error_messages:
            error_report = (
                f"{json_gz_path.name} is invalid:\n" +
                "\n".join(error_messages)
            )
            pytest.fail(error_report)
    
    # If we reach here, validation passed
    assert True, f"{json_gz_path.name} is valid"
