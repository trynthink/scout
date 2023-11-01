from __future__ import annotations
import yaml
from jsonschema import validate
from scout.constants import FilePaths as fp


class Config:
    """Methods to handle yml configuration files, including writing argparse arguments based on
        the schema (supporting_data/config_schema.yml) and enabling validation of inputted
        configuration files.

    Attributes:
        schema_file (Pathlib.filepath): Location of the configuration schema yml
        schema_data (dict): Parsed schema data
        key (str): Workflow step on which to validate and set arguments {ecm_prep, run}
    """

    def __init__(self, parser, key):
        self.schema_file = fp.SUPPORTING_DATA / "config_schema.yml"
        self.schema_data = self._load_config(self.schema_file)
        self.key = key
        schema_block = self.schema_data.get("properties", {}).get(self.key, {})
        self.create_argparse(parser, schema_block)

    def _load_config(self, filepath):
        with open(filepath, "r") as file:
            return yaml.safe_load(file)

    def get_args(self, config_path):
        config_data = self._load_config(config_path)
        validate(config_data, self.schema_data)

        parsed_data = config_data.get(self.key, {})
        args_dict = {}
        args_dict.update(parsed_data)
        return args_dict

    def update_args(self, existing_args: argparse.NameSpace, new_args: dict):  # noqa: F821
        """ Update argparse arguments NameSpace with dictionary of args"""

        for k, v in new_args.items():
            if isinstance(v, dict):
                self.update_args(existing_args, v)
            else:
                existing_args.__dict__.update({k: v})

        return existing_args

    def check_dependencies(self, opts: argparse.NameSpace):  # noqa: F821
        # Verify that arguments are valid that are not captured in the yml schema
        if "fuel types" in vars(opts).get("detail_brkout", []) and opts.split_fuel is True:
            raise ValueError(
                "Detailed breakout (detail_brkout) cannot include `fuel types` if split_fuel==True")

    def create_argparse(self, parser, schema_data, group=None):
        """Extracts arguments from the config schema and writes argparse arguments"""
        if group:
            parser = group
        arguments = schema_data.get("properties", {})
        for arg_name, data in arguments.items():
            arg_type = data["type"]
            arg_choices = data.get("enum")
            arg_help = data.get("description")
            arg_default = data.get("default")
            arg_arr_choices = data.get("items", {}).get("enum")

            if arg_type == "string" and arg_choices:
                arg_help += f". Allowed values are {{{', '.join(arg_choices)}}}"
                parser.add_argument(
                    f"--{arg_name}",
                    choices=arg_choices,
                    help=arg_help,
                    default=arg_default,
                    metavar=''
                )
            elif arg_type == "string":
                parser.add_argument(f"--{arg_name}", type=str, help=arg_help, default=arg_default)
            elif arg_type == "integer":
                parser.add_argument(f"--{arg_name}", type=int, help=arg_help, default=arg_default)
            elif arg_type == "number":
                parser.add_argument(f"--{arg_name}", type=float, help=arg_help, default=arg_default)
            elif arg_type == "boolean":
                parser.add_argument(f"--{arg_name}", action="store_true", help=arg_help)
            elif arg_type == "array":
                arg_help += f". Allowed values are 0 or more of {{{', '.join(arg_arr_choices)}}}"
                parser.add_argument(
                    f"--{arg_name}",
                    nargs="*",
                    choices=arg_arr_choices,
                    help=arg_help,
                    default=arg_default,
                    metavar='')
            elif arg_type == "object" and "properties" in data:
                new_group = parser.add_argument_group(arg_name)
                self.create_argparse(parser, data, group=new_group)
            else:
                raise ValueError(f"Unsupported argument type: {arg_type}")
