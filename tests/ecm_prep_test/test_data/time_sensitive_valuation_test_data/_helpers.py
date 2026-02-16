#!/usr/bin/env python3

"""
Test data for Time-Sensitive Valuation (TSV) tests.

Extracted from test_time_sensitive_valuation_test.py.
"""


def _convert_numpy_strings_to_python(obj):
    """Recursively convert numpy strings to Python strings in nested data structures.

    This fixes KeyError issues when looking up dictionary keys that are numpy.str_ objects
    with regular Python str objects.
    """
    import numpy as np

    if isinstance(obj, np.str_):
        return str(obj)
    elif isinstance(obj, dict):
        return {
            _convert_numpy_strings_to_python(k): _convert_numpy_strings_to_python(v)
            for k, v in obj.items()
        }
    elif isinstance(obj, (list, tuple)):
        return type(obj)(_convert_numpy_strings_to_python(item) for item in obj)
    else:
        return obj
