import json
import warnings
from pathlib import Path
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("C:/Users/ylou2/Desktop\/Scout/repo/scout/ecm_definitions/ecm_schema.json")
JSON_DIR = Path("C:/Users/ylou2/Desktop\/Scout/repo/scout/ecm_definitions")

schema = json.loads(SCHEMA_PATH.read_text())
validator = Draft202012Validator(schema)

for json_file in JSON_DIR.glob("*.json"):
    data = json.loads(json_file.read_text())

    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if errors:
        warnings.warn(
            f"{json_file.name} is invalid:\n" +
            "\n".join(f"  - {e.message}" for e in errors)
        )