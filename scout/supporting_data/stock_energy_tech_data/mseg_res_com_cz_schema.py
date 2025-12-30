import json
import warnings
from pathlib import Path
from jsonschema import Draft202012Validator

SCHEMA_PATH = Path("C:/Users/ylou2/Desktop\Scout/repo/scout/scout/supporting_data/stock_energy_tech_data/mseg_res_com_cz_schema.json")
JSON_PATH = Path("C:/Users/ylou2/Desktop\Scout/repo/scout/scout/supporting_data/stock_energy_tech_data/mseg_res_com_cz.json")

schema_text = SCHEMA_PATH.read_text()
schema = json.loads(schema_text)

data_text = JSON_PATH.read_text()
data = json.loads(data_text)

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
        f"{JSON_PATH.name} is invalid:\n" + "\n".join(messages)
    )