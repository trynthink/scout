import json
import warnings
import gzip
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
    / "cpl_res_com_cz_schema.json"
)

JSON_GZ_PATH = (
    Path(__file__).parent.parent
    / "scout"
    / "supporting_data"
    / "stock_energy_tech_data"
    / "cpl_res_com_cz.gz"
)

# Load schema
schema_text = SCHEMA_PATH.read_text()
schema = json.loads(schema_text)

# Open and read compressed JSON file
with gzip.open(JSON_GZ_PATH, "rt", encoding="utf-8") as f:
    data = json.load(f)

# Validate data
validator = Draft202012Validator(schema)
errors = sorted(validator.iter_errors(data), key=lambda e: e.path)

if errors:
    messages = []
    for e in errors:
        # Skip specific error messages about consumer choice regex non-match
        if (
            "consumer choice" in e.message
            and "does not match any of the regexes" in e.message
        ):
            continue

        data_path = "/".join(str(p) for p in e.path)
        schema_path = "/".join(str(p) for p in e.schema_path)

        messages.append(
            f"{e.message}\n"
            f"    data path: {data_path}\n"
            f"    schema path: {schema_path}"
        )

    if messages:
        warnings.warn(
            RED +
            f"{JSON_GZ_PATH.name} is invalid:\n" +
            "\n".join(messages) +
            RESET
        )
    else:
        print(GREEN + f"{JSON_GZ_PATH.name} is valid ✅" + RESET)
else:
    print(GREEN + f"{JSON_GZ_PATH.name} is valid ✅" + RESET)
    