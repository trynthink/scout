from __future__ import annotations
import yaml
from pathlib import Path
from jsonschema import validate
from scout.constants import FilePaths as fp


class Config:
    """Methods to handle yml configuration files, including writing argparse arguments based on
        the schema (supporting_data/config_schema.yml) and enabling validation of inputted
        configuration files.

    Attributes:
        parser (argparse.ArgumentParser): Argument parser
        schema_file (Pathlib.filepath): Location of the configuration schema yml
        schema_data (dict): Parsed schema data
        key (str): Workflow step on which to validate and set arguments {ecm_prep, run}
    """

    def __init__(self, parser, key, cli_args: list):
        self.parser = parser
        self.key = key
        self.cli_args = cli_args
        self.schema_file = fp.SUPPORTING_DATA / "config_schema.yml"
        self.schema_data = self._load_config(self.schema_file)

        # Generate argparse, set initial cli args
        schema_block = self.schema_data.get("properties", {}).get(self.key, {})
        self.initialize_argparse(parser)
        self.create_argparse(parser, schema_block)
        self.set_config_args(self.cli_args)

    def _load_config(self, filepath):
        with open(filepath, "r") as file:
            return yaml.safe_load(file)

    def _validate(self, input_data: dict, schema_data: dict = None):
        """Validate argument data against schema data

        Args:
            input_data (dict): Data to validate.
            schema_data (dict, optional): Data to validate against, "None" value will use the yml
                                          schema data in supporting_data/config_schema.
        """

        if not schema_data:
            schema_data = self.schema_data
        validate(input_data, schema_data)

    def initialize_argparse(self, parser):
        # Initialize arguments with a yml config file argument
        parser.add_argument(
            "-y", "--yaml",
            type=Path,
            help=("Path to YAML configuration file, arguments in this file will take priority over "
                  "arguments passed via the CLI")
            )

    def set_config_args(self, cli_args: list[str] = []):
        # If applicable, set yml arguments to dict object
        self.config_args = {}
        self.args = self.parser.parse_args(cli_args)
        if self.args.yaml:
            self.config_args = self._load_config(self.args.yaml)
            self._validate(self.config_args, self.schema_data)

    def parse_args(self):
        # Update args with yaml arguments
        if self.config_args:
            config_key_args = self.config_args.get(self.key, {})
            self.args = self.update_args(self.args, config_key_args)

        # Ensure command-line args take precendence
        self.args = self.parser.parse_args(self.cli_args, namespace=self.args)

        # Check for valid arguments
        self.check_dependencies(self.args)

        return self.args

    def update_args(self, existing_args: argparse.NameSpace, new_args: dict):  # noqa: F821
        """ Update argparse arguments NameSpace with dictionary of args"""

        for k, v in new_args.items():
            if isinstance(v, dict):
                self.update_args(existing_args, v)
            else:
                existing_args.__dict__.update({k: v})

        return existing_args

    def check_dependencies(self, args: argparse.NameSpace):  # noqa: F821
        # Verify that arguments are valid that are not captured in the yml schema
        if "fuel types" in vars(args).get("detail_brkout", []) and args.split_fuel is True:
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
