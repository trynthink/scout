import json
import pytest
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
        / "mseg_res_com_cz_schema.json"
    )


@pytest.fixture
def json_path():
    """Return the path to the JSON data file."""
    return (
        Path(__file__).parent.parent
        / "scout"
        / "supporting_data"
        / "stock_energy_tech_data"
        / "mseg_res_com_cz.json"
    )


@pytest.fixture
def schema(schema_path):
    """Load and return the JSON schema."""
    schema_text = schema_path.read_text()
    return json.loads(schema_text)


@pytest.fixture
def data(json_path):
    """Load and return the JSON data."""
    data_text = json_path.read_text()
    return json.loads(data_text)


def test_mseg_res_com_cz_schema_validity(schema, data, json_path):
    """Test that mseg_res_com_cz.json is valid according to its schema."""
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

    if errors:
        error_messages = []
        for e in errors:
            data_path = "/".join(str(p) for p in e.path)
            schema_path = "/".join(str(p) for p in e.schema_path)

            error_messages.append(
                f"{e.message}\n"
                f"    data path: {data_path}\n"
                f"    schema path: {schema_path}"
            )

        error_report = (
            f"{json_path.name} is invalid:\n" +
            "\n".join(error_messages)
        )
        pytest.fail(error_report)
    
    # If we reach here, validation passed
    assert True, f"{json_path.name} is valid"
