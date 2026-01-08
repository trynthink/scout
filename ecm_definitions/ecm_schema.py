import json
import warnings
from pathlib import Path
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("C:/Users/ylou2/Desktop\/Scout/repo/scout/ecm_definitions/ecm_schema.json")
JSON_DIR = Path("C:/Users/ylou2/Desktop\/Scout/repo/scout/ecm_definitions")

schema = json.loads(SCHEMA_PATH.read_text())
validator = Draft202012Validator(schema)

# Files to exclude
exclude_files = {"ecm_schema.json", "package_ecms.json"}

for json_file in JSON_DIR.glob("*.json"):
    if json_file.name in exclude_files:
        continue  # Skip excluded files

    data = json.loads(json_file.read_text())
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
        if messages:
            warnings.warn(
                f"{json_file.name} is invalid:\n" +
                "\n".join(f"  - {e.message}" for e in errors)
            )