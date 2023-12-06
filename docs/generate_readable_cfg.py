from scout.config import Config
from scout.constants import FilePaths as fp
from pathlib import Path
import yaml

schema_file = fp.SUPPORTING_DATA / "config_schema.yml"
schema_data = Config._load_config(schema_file)
output_file = Path(__file__).resolve().parents[0] / "config_readable.yml"


def convert_yaml_structure(input_yaml, required=None, parent_key=None):
    """Translate schema file to more readable version for documentation"""
    output_yaml = {}
    for key, value in input_yaml.items():
        if type(value) != dict:
            continue
        if value.get("type") == "object":
            required = value.get("required", [])
            output_yaml[key] = convert_yaml_structure(value["properties"], required, key)
        elif type(value.get("description")) == str:
            description = value["description"]
            dtype = value["type"]
            default = value.get("default")
            enum = value.get("enum")
            enum_txt = ""
            if enum:
                enum_txt = f" Allowable options are {set(enum)}."
            req_txt = ""
            if key in required:
                req_txt = ", required"
                if parent_key:
                    req_txt += f" if the {parent_key} key is present"

            desc_str = f"({dtype}{req_txt}) {description}{enum_txt} Default {default}"
            output_yaml[key] = desc_str

    return output_yaml


output_cfg = convert_yaml_structure(schema_data["properties"], (schema_data["required"], None))
with open(output_file, "w") as file:
    yaml.dump(output_cfg, file, default_flow_style=False, width=60)
