#!/usr/bin/env python3

"""Python script to automate the baseline calculator of Scout."""

import json

"""Read in the test JSON"""
with open('test_json_traverse.json', 'r') as f:
    test_file = json.load(f)


class ValidQueries(object):
    """ Defines valid query options to pull down EIA data API
    Attributes:
    years (list): A list of valid report years for this script to evaluate.

    """
    def __init__(self):
        self.years = ['2015', '2016']


class UsefulVars(object):
    """ Class of variables present in the test_json_traverse.json for now. 
    Currently, these are variables used globally in functions below.
    In future, these variables will be extended to those required for selection
    in the baseline calculator. """

    """Attributes:
    res_bldg_types (list) = Residential building types
    climate_zone (list) = Two of the five AIA climate zones
    end_uses (list) = Two end uses 
    fuel_type = One fuel type used in the test json file
    """

    def __init__(self, variables):
        self.res_bldg_types = ("single family home", "multi family home",
        "mobile home")
        self.climate_zones = ("AIA_CZ1", "AIA_CZ2")
        self.end_uses = ("heating", "refrigeration")
        self.fuel_type = ("electricity")
        self.electr_heating_tech = ("resistance heat", "ASHP", "GSHP")
        self.energy_values = {
            "heating"
                "resistance heat": {
                key: [2, 5, 2]
                for key in self.energy_values
                }
        }

