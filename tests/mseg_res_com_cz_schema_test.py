import json
import warnings
from pathlib import Path
from jsonschema import Draft202012Validator

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

# File paths
SCHEMA_PATH = (
    Path(__file__).parent.parent
    / "scout"
    / "supporting_data"
    / "stock_energy_tech_data"
    / "mseg_res_com_cz_schema.json"
)

JSON_PATH = (
    Path(__file__).parent.parent
    / "scout"
    / "supporting_data"
    / "stock_energy_tech_data"
    / "mseg_res_com_cz.json"
)

# Load schema
schema_text = SCHEMA_PATH.read_text()
schema = json.loads(schema_text)

# Load data
data_text = JSON_PATH.read_text()
data = json.loads(data_text)

# Validate data
validator = Draft202012Validator(schema)
errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

if errors:
    messages = []
    for e in errors:
        data_path = "/".join(str(p) for p in e.path)
        schema_path = "/".join(str(p) for p in e.schema_path)

        messages.append(
            f"{e.message}\n"
            f"    data path: {data_path}\n"
            f"    schema path: {schema_path}"
        )

    warnings.warn(
        RED +
        f"{JSON_PATH.name} is invalid:\n" +
        "\n".join(messages) +
        RESET
    )
else:
    print(GREEN + f"{JSON_PATH.name} is valid ✅" + RESET)
    