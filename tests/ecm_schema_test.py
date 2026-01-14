import json
import warnings
from pathlib import Path
from jsonschema import Draft202012Validator

# ANSI color codes
RED = "\033[91m"
GREEN = "\033[92m"
RESET = "\033[0m"

# Paths
SCHEMA_PATH = Path(__file__).parent.parent / "ecm_definitions" / "ecm_schema.json"
JSON_DIR = Path(__file__).parent.parent / "ecm_definitions"

# Load schema
schema = json.loads(SCHEMA_PATH.read_text())
validator = Draft202012Validator(schema)

# Files to exclude from validation
exclude_files = {"ecm_schema.json", "package_ecms.json"}

# Validate each JSON file
for json_file in JSON_DIR.glob("*.json"):
    if json_file.name in exclude_files:
        continue  # Skip excluded files

    # Load JSON data
    data = json.loads(json_file.read_text())

    # Collect validation errors
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

        # Display colored warning
        warnings.warn(
            RED +
            f"{json_file.name} is invalid:\n" +
            "\n".join(f"  - {msg}" for msg in messages) +
            RESET
        )
    else:
        # Display colored success message
        print(GREEN + f"{json_file.name} is valid ✅" + RESET)
        