import json
import numpy
import logging
from pathlib import Path, PurePath


class JsonIO:
    @staticmethod
    def load_json(filepath: Path) -> dict:
        """Loads data from a .json file

        Args:
            filepath (pathlib.Path): filepath of .json file

        Returns:
            dict: .json data as a dict
        """
        with open(filepath, 'r') as handle:
            try:
                data = json.load(handle)
            except ValueError as e:
                raise ValueError(f"Error reading in '{filepath}': {str(e)}") from None
        return data

    @staticmethod
    def dump_json(data, filepath: Path):
        """Export data to .json file

        Args:
            data: data to write to .json file
            filepath (pathlib.Path): filepath of .json file
        """
        with open(filepath, "w") as handle:
            json.dump(data, handle, indent=2, cls=MyEncoder)


class MyEncoder(json.JSONEncoder):
    """Convert numpy arrays to list for JSON serializing."""

    def default(self, obj):
        """Modify 'default' method from JSONEncoder."""
        # Case where object to be serialized is numpy array
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        if isinstance(obj, PurePath):
            return str(obj)
        # All other cases
        else:
            return super(MyEncoder, self).default(obj)


class PrintFormat:
    """Class for customizing print messages."""

    @staticmethod
    def custom_showwarning(message, category, filename, lineno, file=None, line=None):
        """Define a custom warning message format."""
        # Other message details suppressed because error location and type are not relevant
        print(message)

    @staticmethod
    def verboseprint(verbose, msg, log_type, logger=None):
        """Print input message when the code is run in verbose mode.

        Args:
            verbose (boolean): Indicator of verbose mode
            msg (string): Message to print to console when in verbose mode
            logger: Logger instance to use for logging
        """
        if not verbose:
            return
        if not logger:
            logger = logging.getLogger(__name__)

        if log_type == "info":
            logger.info(msg)
        elif log_type == "warning":
            logger.warning(msg)
        elif log_type == "error":
            logger.error(msg)

    @staticmethod
    def format_console_list(list_to_format):
        return [f"  {elem}\n" for elem in list_to_format]
