from scout.config import Config
from scout.constants import FilePaths as fp
from pathlib import Path
import yaml
import argparse


def convert_yaml_structure(schema_data: dict, required: list = [], parent_key: str = None) -> dict:
    """Translate schema file data to more readable version for documentation.

    Args:
        schema_data (dict): Block of schema data to convert. If a value is of type `object`, then
            the function will be called recursively to populate each argument.
        required (list, optional): List of required keys for the schema_data block. Defaults to [].
        parent_key (str, optional): Parent key of schema_data, may be needed to specify arguments
            that are required only if the parent key is present. Defaults to None.

    Returns:
        dict: Schema data organized to more easily show the structure, descriptions, data types,
            defaults, and argument requirements.
    """

    output_yaml = {}
    # Iterate key-values of schema data to populate details about each argument
    for key, value in schema_data.items():
        if type(value) != dict:
            continue
        # Recursively call function if arguments belong to a group
        if value.get("type") == "object":
            required = value.get("required", [])
            output_yaml[key] = convert_yaml_structure(value["properties"], required, key)
        # Otherwise, populate output_yaml with details about description, defaults, etc
        elif type(value.get("description")) == str:
            description = value["description"]
            dtype = value["type"]
            if "null" in dtype:
                dtype.remove("null")
                dtype = dtype[0]
            default = value.get("default")
            if not default:
                default = "null"
            enum = value.get("enum")
            arr_enum = value.get("items", {}).get("enum")
            enum_txt = ""
            # If applicable, update description for allowable string enumerations
            if enum:
                enum = sorted(filter(None, enum)) + ["null"] * enum.count(None)
                enum_txt = f" Allowed values are {{{', '.join(str(x) for x in enum)}}}."
            # If applicable, update description for allowable array enumerations
            if dtype == "array" and arr_enum:
                arr_enum = sorted(filter(None, arr_enum)) + ["null"] * arr_enum.count(None)
                enum_txt = (
                    f" Allowed values are 0 or more of {{{', '.join(str(x) for x in arr_enum)}}}."
                )
            req_txt = ""
            if key in required:
                req_txt = ", required"
                if parent_key:
                    req_txt += f" if the {parent_key} key is present"

            desc_str = f"({dtype}{req_txt}) {description}{enum_txt} Default {default}"
            output_yaml[key] = desc_str

    return output_yaml


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description="Convert schema file data to a more readable version for documentation."
    )
    parser.add_argument(
        "-o",
        "--output_file",
        type=str,
        help="Path to the output file. If not provided, the output will be printed to the console.",
    )
    args = parser.parse_args()

    schema_file = fp.SUPPORTING_DATA / "config_schema.yml"
    schema_data = Config._load_config(schema_file)
    output_file = args.output_file
    if args.output_file:
        output_file = Path(args.output_file)
    else:
        output_file = Path(__file__).resolve().parent / "config_readable.yml"

    output_cfg = convert_yaml_structure(schema_data["properties"], (schema_data["required"], None))
    with open(output_file, "w") as file:
        yaml.dump(output_cfg, file, default_flow_style=False, width=60)
