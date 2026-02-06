#!/usr/bin/env python3

""" Tests for MergeMeasuresandApplyBenefitsTest """

from scout.ecm_prep import Measure, MeasurePackage, ECMPrepHelper, ECMPrep
from scout.ecm_prep_vars import UsefulVars, UsefulInputFiles
from scout.config import FilePaths as fp
from scout.ecm_prep_args import ecm_args
from pathlib import Path
import pytest
import numpy
import os
import copy
from tests.ecm_prep_test.common import NullOpts, dict_check


@pytest.fixture(scope="module")
def test_data():
    """Fixture providing test data."""
    # Base directory
    base_dir = os.getcwd()
    # Define additional energy savings and cost reduction benefits to
    # apply to the energy, carbon, and cost data for a package in the
    # 'merge_measures' test
    benefits_test1 = {
        "energy savings increase": 0,
        "cost reduction": 0}
    # Define additional energy savings and cost reduction benefits to
    # apply to the energy, carbon, and cost data for a package in the
    # 'apply_pkg_benefits' test
    benefits_test2 = {
        "energy savings increase": 0.3,
        "cost reduction": 0.2}
    cost_convert_data = {
        "building type conversions": {},
        "cost unit conversions": {
            "heating and cooling": {
                "supply": {
                    "heating equipment": {
                        "original units": "$/kBtu/h heating",
                        "revised units": "$/ft^2 floor",
                        "conversion factor": {
                            "description": "Example",
                            "value": 1,
                            "units": "kBtu/h heating/ft^2 floor",
                            "source": "Example",
                            "notes": "Example"}},
                    "cooling equipment": {
                        "original units": "$/kBtu/h cooling",
                        "revised units": "$/ft^2 floor",
                        "conversion factor": {
                            "description": "Example",
                            "value": 1,
                            "units": "kBtu/h cooling/ft^2 floor",
                            "source": "Example",
                            "notes": "Example"}}}}}}
    # Null user options/options dict
    opts, opts_dict = [NullOpts().opts, NullOpts().opts_dict]
    # Modify options for tests that include envelope costs
    opts_env_costs, opts_env_costs_dict = [
        copy.deepcopy(x) for x in [opts, opts_dict]]
    opts_env_costs.pkg_env_costs, \
        opts_env_costs_dict["pkg_env_costs"] = (True for n in range(2))
    # Modify options for tests that generate sector shapes
    opts_sect_shapes, opts_sect_shapes_dict = [
        copy.deepcopy(x) for x in [opts, opts_dict]]
    opts_sect_shapes.alt_regions, \
        opts_sect_shapes_dict["alt_regions"] = ("EMM" for n in range(2))
    opts_sect_shapes.sect_shapes, \
        opts_sect_shapes_dict["sect_shapes"] = (True for n in range(2))

    # Useful files for the sample package measure objects
    handyfiles = UsefulInputFiles(opts)
    # Version of files to use in tests of pkg. sector shapes
    handyfiles_sect_shapes = UsefulInputFiles(
        opts_sect_shapes)
    # Useful global vars for the sample package measure objects
    handyvars = UsefulVars(base_dir, handyfiles, opts)
    # Version of global vars to use in tests of pkg. sector shapes
    handyvars_sect_shapes = UsefulVars(
        base_dir, handyfiles_sect_shapes, opts_sect_shapes)
    # Hard code aeo_years to fit test years
    handyvars.aeo_years, handyvars_sect_shapes.aeo_years = (
            ["2009", "2010"] for n in range(2))
    # Set focus year for sector-level shape testing to be 2010
    handyvars_sect_shapes.aeo_years_summary = ["2010"]
    # Restrict tests to tech. potential adoption scenario
    handyvars.adopt_schemes_prep, \
        handyvars_sect_shapes.adopt_schemes_prep = (
            ["Technical potential"] for n in range(2))
    # Initialize limited out break data dicts for tests
    handyvars.out_break_in = {
        'AIA CZ1': {'Residential (New)': {
            'Heating (Env.)': {},
            'Heating (Equip.)': {},
            'Cooling (Equip.)': {}}}}
    handyvars_sect_shapes.out_break_in = {
        'TRE': {'Residential (New)': {
            'Heating (Env.)': {},
            'Heating (Equip.)': {},
            'Cooling (Equip.)': {}}}}
    # Initialize sample heating totals to use in applying envelope
    # impacts for tests
    handyvars.htcl_totals = {
        "AIA_CZ1": {
            "single family home": {
                "new": {
                    "electricity": {
                        "heating": {"2009": 20, "2010": 20}
                    }
                }
            },
            "multi family home": {
                "new": {
                    "electricity": {
                        "heating": {"2009": 20, "2010": 20}
                    }
                }
            }
        }
    }
    handyvars_sect_shapes.htcl_totals = {
        "TRE": {
            "single family home": {
                "new": {
                    "electricity": {
                        "heating": {"2009": 20, "2010": 20}
                    }
                }
            },
            "multi family home": {
                "new": {
                    "electricity": {
                        "heating": {"2009": 20, "2010": 20}
                    }
                }
            }
        }
    }
    # Define a series of sample measures to package for the high-level test
    # of output attributes
    sample_measures_in_mkts = [{
        "name": "sample measure pkg env",
        "market_entry_year": None,
        "market_exit_year": None,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new"],
        "climate_zone": ["AIA_CZ1"],
        "bldg_type": ["single family home"],
        "fuel_type": {
            "primary": ["electricity"],
            "secondary": None},
        "fuel_switch_to": None,
        "end_use": {"primary": ["heating"],
                    "secondary": None},
        "technology": {
            "primary": ["windows conduction", "wall"],
            "secondary": None},
        "technology_type": {
            "primary": ["demand"], "secondary": None},
        "markets": {
            "Technical potential": {
                "master_mseg": {
                    "stock": {
                        "total": {
                            "all": {"2009": 20, "2010": 20},
                            "measure": {"2009": 20, "2010": 20}},
                        "competed": {
                            "all": {"2009": 20, "2010": 20},
                            "measure": {"2009": 20, "2010": 20}}},
                    "energy": {
                        "total": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}},
                        "competed": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}}},
                    "carbon": {
                        "total": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}},
                        "competed": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}}},
                    "cost": {
                        "stock": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 20, "2010": 20}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 20, "2010": 20}}},
                        "energy": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}}}},
                    "lifetime": {
                        "baseline": {"2009": 10, "2010": 10},
                        "measure": 10},
                    "sub-market scaling": 1
                },
                "mseg_adjust": {
                    "contributing mseg keys and values": {
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'demand', "
                         "'windows conduction', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1},
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'demand', "
                         "'wall', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1}},
                    "competed choice parameters": {
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'demand', "
                         "'windows conduction', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}},
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'demand', "
                         "'wall', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}}},
                    "secondary mseg adjustments": {
                        "sub-market": {
                            "original energy (total)": {},
                            "adjusted energy (sub-market)": {}},
                        "stock-and-flow": {
                            "original energy (total)": {},
                            "adjusted energy (previously captured)": {},
                            "adjusted energy (competed)": {},
                            "adjusted energy (competed and captured)": {}},
                        "market share": {
                            "original energy (total captured)": {},
                            "original energy (competed and captured)": {},
                            "adjusted energy (total captured)": {},
                            "adjusted energy (competed and captured)": {}}
                    }
                },
                "mseg_out_break": {
                    "stock": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 20,
                                        "2010": 20},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}}
                    },
                    "energy": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 20,
                                        "2010": 20},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "savings": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}}},
                    "carbon": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 20,
                                        "2010": 20},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "savings": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}}},
                    "cost": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 20,
                                        "2010": 20},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "savings": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}}}
                }
            }
        }},
        {
        "name": "sample measure pkg hvac",
        "market_entry_year": None,
        "market_exit_year": None,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new"],
        "climate_zone": ["AIA_CZ1"],
        "bldg_type": ["single family home"],
        "fuel_type": {
            "primary": ["electricity"],
            "secondary": None},
        "fuel_switch_to": None,
        "end_use": {"primary": ["cooling", "heating"],
                    "secondary": None},
        "technology": {"primary": ["ASHP"], "secondary": None},
        "technology_type": {
            "primary": ["supply"], "secondary": None},
        "markets": {
            "Technical potential": {
                "master_mseg": {
                    "stock": {
                        "total": {
                            "all": {"2009": 20, "2010": 20},
                            "measure": {"2009": 20, "2010": 20}},
                        "competed": {
                            "all": {"2009": 20, "2010": 20},
                            "measure": {"2009": 20, "2010": 20}}},
                    "energy": {
                        "total": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}},
                        "competed": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}}},
                    "carbon": {
                        "total": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}},
                        "competed": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}}},
                    "cost": {
                        "stock": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 20, "2010": 20}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 20, "2010": 20}}},
                        "energy": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}}}},
                    "lifetime": {
                        "baseline": {"2009": 10, "2010": 10},
                        "measure": 10},
                    "sub-market scaling": 1
                },
                "mseg_adjust": {
                    "contributing mseg keys and values": {
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'cooling', 'supply', "
                         "'ASHP', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1},
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'supply', "
                         "'ASHP', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1}},
                    "competed choice parameters": {
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'cooling', 'supply', "
                         "'ASHP', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}},
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'supply', "
                         "'ASHP', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}}},
                    "secondary mseg adjustments": {
                        "sub-market": {
                            "original energy (total)": {},
                            "adjusted energy (sub-market)": {}},
                        "stock-and-flow": {
                            "original energy (total)": {},
                            "adjusted energy (previously captured)": {},
                            "adjusted energy (competed)": {},
                            "adjusted energy (competed and captured)": {}},
                        "market share": {
                            "original energy (total captured)": {},
                            "original energy (competed and captured)": {},
                            "adjusted energy (total captured)": {},
                            "adjusted energy (competed and captured)": {}}
                    }
                },
                "mseg_out_break": {
                    "stock": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}}
                    },
                    "energy": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}},
                        "savings": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}}},
                    "carbon": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}},
                        "savings": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}}},
                    "cost": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}},
                        "savings": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}}}
                }
            }
        }},
        {
        "name": "sample measure pkg ctl",
        "market_entry_year": None,
        "market_exit_year": None,
        "market_scaling_fractions": 0.5,
        "market_scaling_fractions_source": None,
        "measure_type": "add-on",
        "structure_type": ["new"],
        "climate_zone": ["AIA_CZ1"],
        "bldg_type": ["single family home", "multi family home"],
        "fuel_type": {
            "primary": ["electricity"],
            "secondary": None},
        "fuel_switch_to": None,
        "end_use": {"primary": ["heating"],
                    "secondary": None},
        "technology": {"primary": ["ASHP"], "secondary": None},
        "technology_type": {
            "primary": ["supply"], "secondary": None},
        "markets": {
            "Technical potential": {
                "master_mseg": {
                    "stock": {
                        "total": {
                            "all": {"2009": 10, "2010": 10},
                            "measure": {"2009": 10, "2010": 10}},
                        "competed": {
                            "all": {"2009": 10, "2010": 10},
                            "measure": {"2009": 10, "2010": 10}}},
                    "energy": {
                        "total": {
                            "baseline": {"2009": 10, "2010": 10},
                            "efficient": {
                                "2009": 5, "2010": 5}},
                        "competed": {
                            "baseline": {"2009": 10, "2010": 10},
                            "efficient": {
                                "2009": 5, "2010": 5}}},
                    "carbon": {
                        "total": {
                            "baseline": {"2009": 10, "2010": 10},
                            "efficient": {
                                "2009": 5, "2010": 5}},
                        "competed": {
                            "baseline": {"2009": 10, "2010": 10},
                            "efficient": {
                                "2009": 5, "2010": 5}}},
                    "cost": {
                        "stock": {
                            "total": {
                                "baseline": {
                                    "2009": 10, "2010": 10},
                                "efficient": {
                                    "2009": 10, "2010": 10}},
                            "competed": {
                                "baseline": {
                                    "2009": 10, "2010": 10},
                                "efficient": {
                                    "2009": 10, "2010": 10}}},
                        "energy": {
                            "total": {
                                "baseline": {
                                    "2009": 10, "2010": 10},
                                "efficient": {
                                    "2009": 5, "2010": 5}},
                            "competed": {
                                "baseline": {
                                    "2009": 10, "2010": 10},
                                "efficient": {
                                    "2009": 5, "2010": 5}}},
                        "carbon": {
                            "total": {
                                "baseline": {
                                    "2009": 10, "2010": 10},
                                "efficient": {
                                    "2009": 5, "2010": 5}},
                            "competed": {
                                "baseline": {
                                    "2009": 10, "2010": 10},
                                "efficient": {
                                    "2009": 5, "2010": 5}}}},
                    "lifetime": {
                        "baseline": {"2009": 10, "2010": 10},
                        "measure": 10},
                    "sub-market scaling": 0.5
                },
                "mseg_adjust": {
                    "contributing mseg keys and values": {
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'supply', "
                         "'ASHP', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 5, "2010": 5}},
                                "competed": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 5, "2010": 5}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}},
                                "competed": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}},
                                "competed": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1},
                        ("('primary', 'AIA_CZ1', 'multi family home', "
                         "'electricity', 'heating', 'supply', "
                         "'ASHP', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 5, "2010": 5}},
                                "competed": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 5, "2010": 5}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}},
                                "competed": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}},
                                "competed": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1}},
                    "competed choice parameters": {
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'supply', "
                         "'ASHP', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}},
                        ("('primary', 'AIA_CZ1', 'multi family home', "
                         "'electricity', 'heating', 'supply', "
                         "'ASHP', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}}},
                    "secondary mseg adjustments": {
                        "sub-market": {
                            "original energy (total)": {},
                            "adjusted energy (sub-market)": {}},
                        "stock-and-flow": {
                            "original energy (total)": {},
                            "adjusted energy (previously captured)": {},
                            "adjusted energy (competed)": {},
                            "adjusted energy (competed and captured)": {}},
                        "market share": {
                            "original energy (total captured)": {},
                            "original energy (competed and captured)": {},
                            "adjusted energy (total captured)": {},
                            "adjusted energy (competed and captured)": {}}
                    }
                },
                "mseg_out_break": {
                    "stock": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}}
                    },
                    "energy": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}},
                        "savings": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}}},
                    "carbon": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}},
                        "savings": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}}},
                    "cost": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}},
                        "savings": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}}}
                }
            }
        }}
        ]
    # Define a unique envelope measure to use in the test of packaging
    # envelope costs (has competed stock of zero to handle in one year)
    sample_measures_in_env_costs = [{
        "name": "sample measure pkg env",
        "market_entry_year": None,
        "market_exit_year": None,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new"],
        "climate_zone": ["AIA_CZ1"],
        "bldg_type": ["single family home"],
        "fuel_type": {
            "primary": ["electricity"],
            "secondary": None},
        "fuel_switch_to": None,
        "end_use": {"primary": ["heating"],
                    "secondary": None},
        "technology": {"primary": ["windows conduction", "wall"],
                       "secondary": None},
        "technology_type": {
            "primary": ["demand"], "secondary": None},
        "markets": {
            "Technical potential": {
                "master_mseg": {
                    "stock": {
                        "total": {
                            "all": {"2009": 20, "2010": 20},
                            "measure": {"2009": 20, "2010": 20}},
                        "competed": {
                            "all": {"2009": 20, "2010": 0},
                            "measure": {"2009": 20, "2010": 0}}},
                    "energy": {
                        "total": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}},
                        "competed": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}}},
                    "carbon": {
                        "total": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}},
                        "competed": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}}},
                    "cost": {
                        "stock": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 20, "2010": 20}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 0},
                                "efficient": {
                                    "2009": 20, "2010": 0}}},
                        "energy": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}}}},
                    "lifetime": {
                        "baseline": {"2009": 10, "2010": 10},
                        "measure": 10},
                    "sub-market scaling": 1
                },
                "mseg_adjust": {
                    "contributing mseg keys and values": {
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'demand', "
                         "'windows conduction', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "all": {"2009": 10, "2010": 0},
                                    "measure": {"2009": 10, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 0},
                                        "efficient": {
                                            "2009": 10, "2010": 0}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1},
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'demand', "
                         "'wall', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "all": {"2009": 10, "2010": 0},
                                    "measure": {"2009": 10, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 0},
                                        "efficient": {
                                            "2009": 15, "2010": 0}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1}},
                    "competed choice parameters": {
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'demand', "
                         "'windows conduction', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}},
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'demand', "
                         "'wall', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}}},
                    "secondary mseg adjustments": {
                        "sub-market": {
                            "original energy (total)": {},
                            "adjusted energy (sub-market)": {}},
                        "stock-and-flow": {
                            "original energy (total)": {},
                            "adjusted energy (previously captured)": {},
                            "adjusted energy (competed)": {},
                            "adjusted energy (competed and captured)": {}},
                        "market share": {
                            "original energy (total captured)": {},
                            "original energy (competed and captured)": {},
                            "adjusted energy (total captured)": {},
                            "adjusted energy (competed and captured)": {}}
                    }
                },
                "mseg_out_break": {
                    "stock": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 20,
                                        "2010": 20},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}}
                    },
                    "energy": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 20,
                                        "2010": 20},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "savings": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}}},
                    "carbon": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 20,
                                        "2010": 20},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "savings": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}}},
                    "cost": {
                        "baseline": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 20,
                                        "2010": 20},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "efficient": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "savings": {
                            'AIA CZ1': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}}}
                }
            }
        }}]
    # Define a series of sample measures to package for the test of sector-
    # level savings shapes for packages
    sample_measures_in_sect_shapes = [{
        "name": "sample measure pkg env",
        "market_entry_year": None,
        "market_exit_year": None,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new"],
        "climate_zone": ["TRE"],
        "bldg_type": ["single family home"],
        "fuel_type": {
            "primary": ["electricity"], "secondary": None},
        "fuel_switch_to": None,
        "end_use": {"primary": ["heating"],
                    "secondary": None},
        "technology": {"primary": ["windows conduction", "wall"],
                       "secondary": None},
        "technology_type": {
            "primary": ["demand"], "secondary": None},
        "sector_shapes": {
            "Technical potential": {
                "TRE": {"2010": {
                    "baseline": [(20/8760) for h in range(8760)],
                    "efficient": [(10/8760) for h in range(8760)]}}
            }
        },
        "markets": {
            "Technical potential": {
                "master_mseg": {
                    "stock": {
                        "total": {
                            "all": {"2009": 20, "2010": 20},
                            "measure": {"2009": 20, "2010": 20}},
                        "competed": {
                            "all": {"2009": 20, "2010": 20},
                            "measure": {"2009": 20, "2010": 20}}},
                    "energy": {
                        "total": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}},
                        "competed": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}}},
                    "carbon": {
                        "total": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}},
                        "competed": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}}},
                    "cost": {
                        "stock": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 20, "2010": 20}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 20, "2010": 20}}},
                        "energy": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}}}},
                    "lifetime": {
                        "baseline": {"2009": 10, "2010": 10},
                        "measure": 10},
                    "sub-market scaling": 1
                },
                "mseg_adjust": {
                    "contributing mseg keys and values": {
                        ("('primary', 'TRE', 'single family home', "
                         "'electricity', 'heating', 'demand', "
                         "'windows conduction', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1},
                        ("('primary', 'TRE', 'single family home', "
                         "'electricity', 'heating', 'demand', "
                         "'wall', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1}},
                    "competed choice parameters": {
                        ("('primary', 'TRE', 'single family home', "
                         "'electricity', 'heating', 'demand', "
                         "'windows conduction', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}},
                        ("('primary', 'TRE', 'single family home', "
                         "'electricity', 'heating', 'demand', "
                         "'wall', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}}},
                    "secondary mseg adjustments": {
                        "sub-market": {
                            "original energy (total)": {},
                            "adjusted energy (sub-market)": {}},
                        "stock-and-flow": {
                            "original energy (total)": {},
                            "adjusted energy (previously captured)": {},
                            "adjusted energy (competed)": {},
                            "adjusted energy (competed and captured)": {}},
                        "market share": {
                            "original energy (total captured)": {},
                            "original energy (competed and captured)": {},
                            "adjusted energy (total captured)": {},
                            "adjusted energy (competed and captured)": {}}
                    }
                },
                "mseg_out_break": {
                    "stock": {
                        "baseline": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 20,
                                        "2010": 20},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "efficient": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}}
                    },
                    "energy": {
                        "baseline": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 20,
                                        "2010": 20},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "efficient": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "savings": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}}},
                    "carbon": {
                        "baseline": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 20,
                                        "2010": 20},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "efficient": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "savings": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}}},
                    "cost": {
                        "baseline": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 20,
                                        "2010": 20},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "efficient": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}},
                        "savings": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Env.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Equip.)': {},
                                    'Cooling (Equip.)': {}}}}}
                }
            }
        }},
        {
        "name": "sample measure pkg hvac",
        "market_entry_year": None,
        "market_exit_year": None,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new"],
        "climate_zone": ["TRE"],
        "bldg_type": ["single family home"],
        "fuel_type": {
            "primary": ["electricity"], "secondary": None},
        "fuel_switch_to": None,
        "end_use": {"primary": ["cooling", "heating"],
                    "secondary": None},
        "technology": {"primary": ["ASHP"], "secondary": None},
        "technology_type": {
            "primary": ["supply"], "secondary": None},
        "sector_shapes": {
            "Technical potential": {
                "TRE": {"2010": {
                    "baseline": [(20/8760) for h in range(8760)],
                    "efficient": [(10/8760) for h in range(8760)]}}
            }
        },
        "markets": {
            "Technical potential": {
                "master_mseg": {
                    "stock": {
                        "total": {
                            "all": {"2009": 20, "2010": 20},
                            "measure": {"2009": 20, "2010": 20}},
                        "competed": {
                            "all": {"2009": 20, "2010": 20},
                            "measure": {"2009": 20, "2010": 20}}},
                    "energy": {
                        "total": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}},
                        "competed": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}}},
                    "carbon": {
                        "total": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}},
                        "competed": {
                            "baseline": {"2009": 20, "2010": 20},
                            "efficient": {
                                "2009": 10, "2010": 10}}},
                    "cost": {
                        "stock": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 20, "2010": 20}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 20, "2010": 20}}},
                        "energy": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}},
                            "competed": {
                                "baseline": {
                                    "2009": 20, "2010": 20},
                                "efficient": {
                                    "2009": 10, "2010": 10}}}},
                    "lifetime": {
                        "baseline": {"2009": 10, "2010": 10},
                        "measure": 10},
                    "sub-market scaling": 1
                },
                "mseg_adjust": {
                    "contributing mseg keys and values": {
                        ("('primary', 'TRE', 'single family home', "
                         "'electricity', 'cooling', 'supply', "
                         "'ASHP', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1},
                        ("('primary', 'TRE', 'single family home', "
                         "'electricity', 'heating', 'supply', "
                         "'ASHP', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 10, "2010": 10}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {
                                        "2009": 5, "2010": 5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1}},
                    "competed choice parameters": {
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'cooling', 'supply', "
                         "'ASHP', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}},
                        ("('primary', 'AIA_CZ1', 'single family home', "
                         "'electricity', 'heating', 'supply', "
                         "'ASHP', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}}},
                    "secondary mseg adjustments": {
                        "sub-market": {
                            "original energy (total)": {},
                            "adjusted energy (sub-market)": {}},
                        "stock-and-flow": {
                            "original energy (total)": {},
                            "adjusted energy (previously captured)": {},
                            "adjusted energy (competed)": {},
                            "adjusted energy (competed and captured)": {}},
                        "market share": {
                            "original energy (total captured)": {},
                            "original energy (competed and captured)": {},
                            "adjusted energy (total captured)": {},
                            "adjusted energy (competed and captured)": {}}
                    }
                },
                "mseg_out_break": {
                    "stock": {
                        "baseline": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}}
                    },
                    "energy": {
                        "baseline": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}},
                        "savings": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}}},
                    "carbon": {
                        "baseline": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}},
                        "savings": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}}},
                    "cost": {
                        "baseline": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}},
                        "savings": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Heating (Env.)': {}}}}}
                }
            }
        }},
        {
        "name": "sample measure pkg ctl",
        "market_entry_year": None,
        "market_exit_year": None,
        "market_scaling_fractions": 0.5,
        "market_scaling_fractions_source": None,
        "measure_type": "add-on",
        "structure_type": ["new"],
        "climate_zone": ["TRE"],
        "bldg_type": ["single family home", "multi family home"],
        "fuel_type": {
            "primary": ["electricity"], "secondary": None},
        "fuel_switch_to": None,
        "end_use": {"primary": ["heating"],
                    "secondary": None},
        "technology": {"primary": ["ASHP"], "secondary": None},
        "technology_type": {
            "primary": ["supply"], "secondary": None},
        "sector_shapes": {
            "Technical potential": {
                "TRE": {"2010": {
                    "baseline": [(10/8760) for h in range(8760)],
                    "efficient": [(5/8760) for h in range(8760)]}},
            }
        },
        "markets": {
            "Technical potential": {
                "master_mseg": {
                    "stock": {
                        "total": {
                            "all": {"2009": 10, "2010": 10},
                            "measure": {"2009": 10, "2010": 10}},
                        "competed": {
                            "all": {"2009": 10, "2010": 10},
                            "measure": {"2009": 10, "2010": 10}}},
                    "energy": {
                        "total": {
                            "baseline": {"2009": 10, "2010": 10},
                            "efficient": {
                                "2009": 5, "2010": 5}},
                        "competed": {
                            "baseline": {"2009": 10, "2010": 10},
                            "efficient": {
                                "2009": 5, "2010": 5}}},
                    "carbon": {
                        "total": {
                            "baseline": {"2009": 10, "2010": 10},
                            "efficient": {
                                "2009": 5, "2010": 5}},
                        "competed": {
                            "baseline": {"2009": 10, "2010": 10},
                            "efficient": {
                                "2009": 5, "2010": 5}}},
                    "cost": {
                        "stock": {
                            "total": {
                                "baseline": {
                                    "2009": 10, "2010": 10},
                                "efficient": {
                                    "2009": 10, "2010": 10}},
                            "competed": {
                                "baseline": {
                                    "2009": 10, "2010": 10},
                                "efficient": {
                                    "2009": 10, "2010": 10}}},
                        "energy": {
                            "total": {
                                "baseline": {
                                    "2009": 10, "2010": 10},
                                "efficient": {
                                    "2009": 5, "2010": 5}},
                            "competed": {
                                "baseline": {
                                    "2009": 10, "2010": 10},
                                "efficient": {
                                    "2009": 5, "2010": 5}}},
                        "carbon": {
                            "total": {
                                "baseline": {
                                    "2009": 10, "2010": 10},
                                "efficient": {
                                    "2009": 5, "2010": 5}},
                            "competed": {
                                "baseline": {
                                    "2009": 10, "2010": 10},
                                "efficient": {
                                    "2009": 5, "2010": 5}}}},
                    "lifetime": {
                        "baseline": {"2009": 10, "2010": 10},
                        "measure": 10},
                    "sub-market scaling": 0.5
                },
                "mseg_adjust": {
                    "contributing mseg keys and values": {
                        ("('primary', 'TRE', 'single family home', "
                         "'electricity', 'heating', 'supply', "
                         "'ASHP', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 5, "2010": 5}},
                                "competed": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 5, "2010": 5}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}},
                                "competed": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}},
                                "competed": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1},
                        ("('primary', 'TRE', 'multi family home', "
                         "'electricity', 'heating', 'supply', "
                         "'ASHP', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 5, "2010": 5}},
                                "competed": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 5, "2010": 5}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}},
                                "competed": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}},
                                "competed": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {
                                        "2009": 2.5, "2010": 2.5}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 5, "2010": 5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 5, "2010": 5},
                                        "efficient": {
                                            "2009": 2.5, "2010": 2.5}}}},
                            "lifetime": {
                                "baseline": {"2009": 10, "2010": 10},
                                "measure": 10},
                            "sub-market scaling": 1}},
                    "competed choice parameters": {
                        ("('primary', 'TRE', 'single family home', "
                         "'electricity', 'heating', 'supply', "
                         "'ASHP', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}},
                        ("('primary', 'TRE', 'multi family home', "
                         "'electricity', 'heating', 'supply', "
                         "'ASHP', 'new')"): {
                            "b1": {"2009": 1, "2010": 1},
                            "b2": {"2009": 1, "2010": 1}}},
                    "secondary mseg adjustments": {
                        "sub-market": {
                            "original energy (total)": {},
                            "adjusted energy (sub-market)": {}},
                        "stock-and-flow": {
                            "original energy (total)": {},
                            "adjusted energy (previously captured)": {},
                            "adjusted energy (competed)": {},
                            "adjusted energy (competed and captured)": {}},
                        "market share": {
                            "original energy (total captured)": {},
                            "original energy (competed and captured)": {},
                            "adjusted energy (total captured)": {},
                            "adjusted energy (competed and captured)": {}}
                    }
                },
                "mseg_out_break": {
                    "stock": {
                        "baseline": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}}
                    },
                    "energy": {
                        "baseline": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}},
                        "savings": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}}},
                    "carbon": {
                        "baseline": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}},
                        "savings": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}}},
                    "cost": {
                        "baseline": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 10,
                                        "2010": 10},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}
                                    }},
                        "efficient": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}},
                        "savings": {
                            'TRE': {
                                'Residential (New)': {
                                    'Heating (Equip.)': {
                                        "2009": 5,
                                        "2010": 5},
                                    'Cooling (Equip.)': {},
                                    'Heating (Env.)': {}}}}}
                }
            }
        }}]

    # Save the raw dictionary data before converting to Measure objects
    sample_measures_in_mkts_data = sample_measures_in_mkts[:]
    sample_measures_in_env_costs_data = sample_measures_in_env_costs[:]
    sample_measures_in_sect_shapes_data = sample_measures_in_sect_shapes[:]

    sample_measures_in_mkts = [Measure(
        base_dir, handyvars, handyfiles, opts_dict,
        **x) for x in sample_measures_in_mkts_data]
    sample_measures_in_env_costs = [Measure(
        base_dir, handyvars, handyfiles, opts_env_costs_dict,
        **x) for x in sample_measures_in_env_costs_data]
    sample_measures_in_sect_shapes = [Measure(
        base_dir, handyvars_sect_shapes, handyfiles, opts_sect_shapes_dict,
        **x) for x in sample_measures_in_sect_shapes_data]
    for ind, m in enumerate(sample_measures_in_mkts):
        m.technology_type = \
            sample_measures_in_mkts_data[ind]["technology_type"]
        m.markets = sample_measures_in_mkts_data[ind]["markets"]
    for ind, m in enumerate(sample_measures_in_env_costs):
        m.technology_type = \
            sample_measures_in_env_costs_data[ind]["technology_type"]
        m.markets = sample_measures_in_env_costs_data[ind]["markets"]
    for ind, m in enumerate(sample_measures_in_sect_shapes):
        m.technology_type = \
            sample_measures_in_sect_shapes_data[ind]["technology_type"]
        m.markets = sample_measures_in_sect_shapes_data[ind]["markets"]
        m.sector_shapes = \
            sample_measures_in_sect_shapes_data[ind]["sector_shapes"]
    # Set sample names for the packages to be tested
    sample_package_names_highlevel = [
        "Envelope + ASHP", "ASHP + Ctl.", "Envelope + ASHP + Ctl."]
    sample_package_names_sect_shapes = [
        "Envelope + ASHP + Ctl."]
    # Set the combinations of measures that each package in the high-level
    # output test represents
    sample_package_meas_pairs_highlevel = [
        sample_measures_in_mkts[0:2],
        sample_measures_in_mkts[1:3],
        sample_measures_in_mkts]
    sample_package_in_test1_highlevel = [
        None for n in range(len(sample_package_meas_pairs_highlevel))]
    for pkg in range(len(sample_package_names_highlevel)):
        sample_package_in_test1_highlevel[pkg] = \
            MeasurePackage(
            sample_package_meas_pairs_highlevel[pkg],
            sample_package_names_highlevel[pkg],
            benefits_test1, handyvars, handyfiles, opts,
            convert_data=None)
    # Versions of equipment measures to package with envelope that share
    # the same 'pkg_env_costs' setting
    sample_measures_in_mkts_envcosts_1, \
        sample_measures_in_mkts_envcosts_2 = [
            copy.deepcopy(x) for x in [
                sample_measures_in_mkts[1],
                sample_measures_in_mkts[2]]]
    sample_measures_in_mkts_envcosts_1.usr_opts["pkg_env_costs"] = True
    sample_measures_in_mkts_envcosts_2.usr_opts["pkg_env_costs"] = True
    sample_package_meas_pairs_env_costs = [
        sample_measures_in_env_costs[0],
        sample_measures_in_mkts_envcosts_1,
        sample_measures_in_mkts_envcosts_2]
    sample_package_in_test1_env_costs = MeasurePackage(
        sample_package_meas_pairs_env_costs,
        sample_package_names_highlevel[-1], benefits_test1,
        handyvars, handyfiles, opts_env_costs, cost_convert_data)
    sample_package_in_test1_attr_breaks = MeasurePackage(
        sample_package_meas_pairs_env_costs,
        sample_package_names_highlevel[-1],
        benefits_test1, handyvars, handyfiles, opts, convert_data=None)
    sample_package_in_sect_shapes = MeasurePackage(
        sample_measures_in_sect_shapes,
        sample_package_names_sect_shapes[0],
        benefits_test1, handyvars_sect_shapes, handyfiles,
        opts_sect_shapes, convert_data=None)
    sample_package_in_sect_shapes_bens = MeasurePackage(
        sample_measures_in_sect_shapes,
        sample_package_names_sect_shapes[0],
        benefits_test2, handyvars_sect_shapes, handyfiles,
        opts_sect_shapes, convert_data=None)
    sample_package_in_test2 = MeasurePackage(
        sample_measures_in_mkts,
        sample_package_names_highlevel[0],
        benefits_test2, handyvars, handyfiles, opts, convert_data=None)
    genattr_ok_out_test1 = [
        'Envelope + ASHP + Ctl.',
        ['AIA_CZ1'],
        ['single family home', 'multi family home'],
        ['new'],
        ['electricity'],
        ['cooling', 'heating']]
    breaks_ok_out_test1 = {
        "stock": {
            "baseline": {
                'AIA CZ1': {
                    'Residential (New)': {
                        'Cooling (Equip.)': {
                            "2009": 10, "2010": 10
                        },
                        'Heating (Equip.)': {
                            "2009": 15, "2010": 15
                        },
                        'Heating (Env.)': {}
                        },
                    },
                },
            "efficient": {
                'AIA CZ1': {
                    'Residential (New)': {
                        'Cooling (Equip.)': {
                            "2009": 5, "2010": 5
                        },
                        'Heating (Equip.)': {
                            "2009": 5, "2010": 5
                        },
                        'Heating (Env.)': {}
                        },
                    },
                }
        },
        "energy": {
            "baseline": {
                'AIA CZ1': {
                    'Residential (New)': {
                        'Cooling (Equip.)': {
                            "2009": 10, "2010": 10
                        },
                        'Heating (Equip.)': {
                            "2009": 15, "2010": 15
                        },
                        'Heating (Env.)': {}
                        },
                    },
                },
            "efficient": {
                'AIA CZ1': {
                    'Residential (New)': {
                        'Cooling (Equip.)': {
                            "2009": 5, "2010": 5
                        },
                        'Heating (Equip.)': {
                            "2009": 4.27, "2010": 4.27
                        },
                        'Heating (Env.)': {}
                        },
                    },
                },
            "savings": {
                'AIA CZ1': {
                    'Residential (New)': {
                        'Cooling (Equip.)': {
                            "2009": 5, "2010": 5
                        },
                        'Heating (Equip.)': {
                            "2009": 10.73, "2010": 10.73
                        },
                        'Heating (Env.)': {}
                        },
                    },
                }},
        "carbon": {
            "baseline": {
                'AIA CZ1': {
                    'Residential (New)': {
                        'Cooling (Equip.)': {
                            "2009": 10, "2010": 10
                        },
                        'Heating (Equip.)': {
                            "2009": 15, "2010": 15
                        },
                        'Heating (Env.)': {}
                        },
                    },
                },
            "efficient": {
                'AIA CZ1': {
                    'Residential (New)': {
                        'Cooling (Equip.)': {
                            "2009": 5, "2010": 5
                        },
                        'Heating (Equip.)': {
                            "2009": 4.27, "2010": 4.27
                        },
                        'Heating (Env.)': {}
                        },
                    },
                },
            "savings": {
                'AIA CZ1': {
                    'Residential (New)': {
                        'Cooling (Equip.)': {
                            "2009": 5, "2010": 5
                        },
                        'Heating (Equip.)': {
                            "2009": 10.73, "2010": 10.73
                        },
                        'Heating (Env.)': {}
                        },
                    },
                }},
        "cost": {
            "baseline": {
                'AIA CZ1': {
                    'Residential (New)': {
                        'Cooling (Equip.)': {
                            "2009": 10, "2010": 10
                        },
                        'Heating (Equip.)': {
                            "2009": 15, "2010": 15
                        },
                        'Heating (Env.)': {}
                        },
                    },
                },
            "efficient": {
                'AIA CZ1': {
                    'Residential (New)': {
                        'Cooling (Equip.)': {
                            "2009": 5, "2010": 5
                        },
                        'Heating (Equip.)': {
                            "2009": 4.27, "2010": 4.27
                        },
                        'Heating (Env.)': {}
                        },
                    },
                },
            "savings": {
                'AIA CZ1': {
                    'Residential (New)': {
                        'Cooling (Equip.)': {
                            "2009": 5, "2010": 5
                        },
                        'Heating (Equip.)': {
                            "2009": 10.73, "2010": 10.73
                        },
                        'Heating (Env.)': {}
                        },
                    },
                }}}
    contrib_ok_out_test1 = {
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'ASHP', 'new')"): {
            "stock": {
                "total": {
                    "all": {"2009": 10, "2010": 10},
                    "measure": {"2009": 10, "2010": 10}},
                "competed": {
                    "all": {"2009": 10, "2010": 10},
                    "measure": {"2009": 10, "2010": 10}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 10, "2010": 10},
                    "efficient": {
                        "2009": 5, "2010": 5}},
                "competed": {
                    "baseline": {"2009": 10, "2010": 10},
                    "efficient": {
                        "2009": 5, "2010": 5}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 10, "2010": 10},
                    "efficient": {
                        "2009": 5, "2010": 5}},
                "competed": {
                    "baseline": {"2009": 10, "2010": 10},
                    "efficient": {
                        "2009": 5, "2010": 5}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {
                            "2009": 10, "2010": 10},
                        "efficient": {
                            "2009": 10, "2010": 10}},
                    "competed": {
                        "baseline": {
                            "2009": 10, "2010": 10},
                        "efficient": {
                            "2009": 10, "2010": 10}}},
                "energy": {
                    "total": {
                        "baseline": {
                            "2009": 10, "2010": 10},
                        "efficient": {
                            "2009": 5, "2010": 5}},
                    "competed": {
                        "baseline": {
                            "2009": 10, "2010": 10},
                        "efficient": {
                            "2009": 5, "2010": 5}}},
                "carbon": {
                    "total": {
                        "baseline": {
                            "2009": 10, "2010": 10},
                        "efficient": {
                            "2009": 5, "2010": 5}},
                    "competed": {
                        "baseline": {
                            "2009": 10, "2010": 10},
                        "efficient": {
                            "2009": 5, "2010": 5}}}},
            "lifetime": {
                "baseline": {"2009": 10, "2010": 10},
                "measure": 10},
            "sub-market scaling": 1},
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'ASHP', 'new')"): {
            "stock": {
                "total": {
                    "all": {"2009": 10, "2010": 10},
                    "measure": {"2009": 10, "2010": 10}},
                "competed": {
                    "all": {"2009": 10, "2010": 10},
                    "measure": {"2009": 10, "2010": 10}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 10, "2010": 10},
                    "efficient": {
                        "2009": 1.77, "2010": 1.77}},
                "competed": {
                    "baseline": {"2009": 10, "2010": 10},
                    "efficient": {
                        "2009": 1.77, "2010": 1.77}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 10, "2010": 10},
                    "efficient": {
                        "2009": 1.77, "2010": 1.77}},
                "competed": {
                    "baseline": {"2009": 10, "2010": 10},
                    "efficient": {
                        "2009": 1.77, "2010": 1.77}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {
                            "2009": 10, "2010": 10},
                        "efficient": {
                            "2009": 10, "2010": 10}},
                    "competed": {
                        "baseline": {
                            "2009": 10, "2010": 10},
                        "efficient": {
                            "2009": 10, "2010": 10}}},
                "energy": {
                    "total": {
                        "baseline": {
                            "2009": 10, "2010": 10},
                        "efficient": {
                            "2009": 1.77, "2010": 1.77}},
                    "competed": {
                        "baseline": {
                            "2009": 10, "2010": 10},
                        "efficient": {
                            "2009": 1.77, "2010": 1.77}}},
                "carbon": {
                    "total": {
                        "baseline": {
                            "2009": 10, "2010": 10},
                        "efficient": {
                            "2009": 1.77, "2010": 1.77}},
                    "competed": {
                        "baseline": {
                            "2009": 10, "2010": 10},
                        "efficient": {
                            "2009": 1.77, "2010": 1.77}}}},
            "lifetime": {
                "baseline": {"2009": 20, "2010": 20},
                "measure": 20},
            "sub-market scaling": 1},
        ("('primary', 'AIA_CZ1', 'multi family home', "
         "'electricity', 'heating', 'supply', "
         "'ASHP', 'new')"): {
            "stock": {
                "total": {
                    "all": {"2009": 5, "2010": 5},
                    "measure": {"2009": 5, "2010": 5}},
                "competed": {
                    "all": {"2009": 5, "2010": 5},
                    "measure": {"2009": 5, "2010": 5}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 5, "2010": 5},
                    "efficient": {
                        "2009": 2.5, "2010": 2.5}},
                "competed": {
                    "baseline": {"2009": 5, "2010": 5},
                    "efficient": {
                        "2009": 2.5, "2010": 2.5}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 5, "2010": 5},
                    "efficient": {
                        "2009": 2.5, "2010": 2.5}},
                "competed": {
                    "baseline": {"2009": 5, "2010": 5},
                    "efficient": {
                        "2009": 2.5, "2010": 2.5}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {
                            "2009": 5, "2010": 5},
                        "efficient": {
                            "2009": 5, "2010": 5}},
                    "competed": {
                        "baseline": {
                            "2009": 5, "2010": 5},
                        "efficient": {
                            "2009": 5, "2010": 5}}},
                "energy": {
                    "total": {
                        "baseline": {
                            "2009": 5, "2010": 5},
                        "efficient": {
                            "2009": 2.5, "2010": 2.5}},
                    "competed": {
                        "baseline": {
                            "2009": 5, "2010": 5},
                        "efficient": {
                            "2009": 2.5, "2010": 2.5}}},
                "carbon": {
                    "total": {
                        "baseline": {
                            "2009": 5, "2010": 5},
                        "efficient": {
                            "2009": 2.5, "2010": 2.5}},
                    "competed": {
                        "baseline": {
                            "2009": 5, "2010": 5},
                        "efficient": {
                            "2009": 2.5, "2010": 2.5}}}},
            "lifetime": {
                "baseline": {"2009": 10, "2010": 10},
                "measure": 10},
            "sub-market scaling": 1}
        }
    markets_ok_out_test1 = [{
        "stock": {
            "total": {
                "all": {"2009": 20, "2010": 20},
                "measure": {"2009": 20, "2010": 20}},
            "competed": {
                "all": {"2009": 20, "2010": 20},
                "measure": {"2009": 20, "2010": 20}}},
        "energy": {
            "total": {
                "baseline": {"2009": 20, "2010": 20},
                "efficient": {"2009": 7.5, "2010": 7.5}},
            "competed": {
                "baseline": {"2009": 20, "2010": 20},
                "efficient": {"2009": 7.5, "2010": 7.5}}},
        "carbon": {
            "total": {
                "baseline": {"2009": 20, "2010": 20},
                "efficient": {"2009": 7.5, "2010": 7.5}},
            "competed": {
                "baseline": {"2009": 20, "2010": 20},
                "efficient": {"2009": 7.5, "2010": 7.5}}},
        "cost": {
            "stock": {
                "total": {
                    "baseline": {"2009": 20, "2010": 20},
                    "efficient": {"2009": 20, "2010": 20}},
                "competed": {
                    "baseline": {"2009": 20, "2010": 20},
                    "efficient": {"2009": 20, "2010": 20}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 20, "2010": 20},
                    "efficient": {"2009": 7.5, "2010": 7.5}},
                "competed": {
                    "baseline": {"2009": 20, "2010": 20},
                    "efficient": {"2009": 7.5, "2010": 7.5}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 20, "2010": 20},
                    "efficient": {"2009": 7.5, "2010": 7.5}},
                "competed": {
                    "baseline": {"2009": 20, "2010": 20},
                    "efficient": {"2009": 7.5, "2010": 7.5}}}},
        "lifetime": {
            "baseline": {"2009": 10, "2010": 10},
            "measure": 10}
        }, {
        "stock": {
            "total": {
                "all": {"2009": 25, "2010": 25},
                "measure": {"2009": 25, "2010": 25}},
            "competed": {
                "all": {"2009": 25, "2010": 25},
                "measure": {"2009": 25, "2010": 25}}},
        "energy": {
            "total": {
                "baseline": {"2009": 25, "2010": 25},
                "efficient": {"2009": 11.04167, "2010": 11.04167}},
            "competed": {
                "baseline": {"2009": 25, "2010": 25},
                "efficient": {"2009": 11.04167, "2010": 11.04167}}},
        "carbon": {
            "total": {
                "baseline": {"2009": 25, "2010": 25},
                "efficient": {"2009": 11.04167, "2010": 11.04167}},
            "competed": {
                "baseline": {"2009": 25, "2010": 25},
                "efficient": {"2009": 11.04167, "2010": 11.04167}}},
        "cost": {
            "stock": {
                "total": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 25, "2010": 25}},
                "competed": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 25, "2010": 25}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 11.04167, "2010": 11.04167}},
                "competed": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 11.04167, "2010": 11.04167}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 11.04167, "2010": 11.04167}},
                "competed": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 11.04167, "2010": 11.04167}}}},
        "lifetime": {
            "baseline": {"2009": 10, "2010": 10},
            "measure": 10}
        },
        {
        "stock": {
            "total": {
                "all": {"2009": 25, "2010": 25},
                "measure": {"2009": 25, "2010": 25}},
            "competed": {
                "all": {"2009": 25, "2010": 25},
                "measure": {"2009": 25, "2010": 25}}},
        "energy": {
            "total": {
                "baseline": {"2009": 25, "2010": 25},
                "efficient": {"2009": 9.270833, "2010": 9.270833}},
            "competed": {
                "baseline": {"2009": 25, "2010": 25},
                "efficient": {"2009": 9.270833, "2010": 9.270833}}},
        "carbon": {
            "total": {
                "baseline": {"2009": 25, "2010": 25},
                "efficient": {"2009": 9.270833, "2010": 9.270833}},
            "competed": {
                "baseline": {"2009": 25, "2010": 25},
                "efficient": {"2009": 9.270833, "2010": 9.270833}}},
        "cost": {
            "stock": {
                "total": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 25, "2010": 25}},
                "competed": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 25, "2010": 25}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 9.270833, "2010": 9.270833}},
                "competed": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 9.270833, "2010": 9.270833}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 9.270833, "2010": 9.270833}},
                "competed": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 9.270833, "2010": 9.270833}}}},
        "lifetime": {
            "baseline": {"2009": 10, "2010": 10},
            "measure": 10}
        }]
    markets_ok_out_test1_env_costs = {
        "stock": {
            "total": {
                "all": {"2009": 25, "2010": 25},
                "measure": {"2009": 25, "2010": 25}},
            "competed": {
                "all": {"2009": 25, "2010": 25},
                "measure": {"2009": 25, "2010": 25}}},
        "energy": {
            "total": {
                "baseline": {"2009": 25, "2010": 25},
                "efficient": {"2009": 9.270833, "2010": 9.270833}},
            "competed": {
                "baseline": {"2009": 25, "2010": 25},
                "efficient": {"2009": 9.270833, "2010": 9.270833}}},
        "carbon": {
            "total": {
                "baseline": {"2009": 25, "2010": 25},
                "efficient": {"2009": 9.270833, "2010": 9.270833}},
            "competed": {
                "baseline": {"2009": 25, "2010": 25},
                "efficient": {"2009": 9.270833, "2010": 9.270833}}},
        "cost": {
            "stock": {
                "total": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 27.5, "2010": 27.5}},
                "competed": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 27.5, "2010": 25}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 9.270833, "2010": 9.270833}},
                "competed": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 9.270833, "2010": 9.270833}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 9.270833, "2010": 9.270833}},
                "competed": {
                    "baseline": {"2009": 25, "2010": 25},
                    "efficient": {"2009": 9.270833, "2010": 9.270833}}}},
        "lifetime": {
            "baseline": {"2009": 10, "2010": 10},
            "measure": 10}
        }
    sect_shapes_ok_out = {
        "TRE": {
            "2010": {
                "baseline": [(25/8760) for n in range(8760)],
                "efficient": [(9.270833/8760) for n in range(8760)]}}}
    sect_shapes_ok_out_bens = {
        "TRE": {
            "2010": {
                "baseline": [(25/8760) for n in range(8760)],
                "efficient": [(9.270833/8760) * 0.7
                              for n in range(8760)]}}}
    mseg_ok_in_test2 = {
        "stock": {
            "total": {
                "all": {"2009": 40, "2010": 40},
                "measure": {"2009": 24, "2010": 24}},
            "competed": {
                "all": {"2009": 20, "2010": 20},
                "measure": {"2009": 4, "2010": 4}}},
        "energy": {
            "total": {
                "baseline": {"2009": 80, "2010": 80},
                "efficient": {"2009": 48, "2010": 48}},
            "competed": {
                "baseline": {"2009": 40, "2010": 40},
                "efficient": {"2009": 8, "2010": 8}}},
        "carbon": {
            "total": {
                "baseline": {"2009": 120, "2010": 120},
                "efficient": {"2009": 72, "2010": 72}},
            "competed": {
                "baseline": {"2009": 60, "2010": 60},
                "efficient": {"2009": 12, "2010": 12}}},
        "cost": {
            "stock": {
                "total": {
                    "baseline": {"2009": 40, "2010": 40},
                    "efficient": {"2009": 72, "2010": 72}},
                "competed": {
                    "baseline": {"2009": 40, "2010": 40},
                    "efficient": {"2009": 72, "2010": 72}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 80, "2010": 80},
                    "efficient": {"2009": 48, "2010": 48}},
                "competed": {
                    "baseline": {"2009": 40, "2010": 40},
                    "efficient": {"2009": 8, "2010": 8}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 120, "2010": 120},
                    "efficient": {"2009": 72, "2010": 72}},
                "competed": {
                    "baseline": {"2009": 60, "2010": 60},
                    "efficient": {"2009": 12, "2010": 12}}}},
        "lifetime": {
            "baseline": {"2009": 5, "2010": 5},
            "measure": 10}}
    mseg_ok_out_test2 = {
        "stock": {
            "total": {
                "all": {"2009": 40, "2010": 40},
                "measure": {"2009": 24, "2010": 24}},
            "competed": {
                "all": {"2009": 20, "2010": 20},
                "measure": {"2009": 4, "2010": 4}}},
        "energy": {
            "total": {
                "baseline": {"2009": 80, "2010": 80},
                "efficient": {"2009": 48 * 0.7, "2010": 48 * 0.7}},
            "competed": {
                "baseline": {"2009": 40, "2010": 40},
                "efficient": {"2009": 8 * 0.7, "2010": 8 * 0.7}}},
        "carbon": {
            "total": {
                "baseline": {"2009": 120, "2010": 120},
                "efficient": {"2009": 72 * 0.7, "2010": 72 * 0.7}},
            "competed": {
                "baseline": {"2009": 60, "2010": 60},
                "efficient": {"2009": 12 * 0.7, "2010": 12 * 0.7}}},
        "cost": {
            "stock": {
                "total": {
                    "baseline": {"2009": 40, "2010": 40},
                    "efficient": {"2009": 72 * 0.8, "2010": 72 * 0.8}},
                "competed": {
                    "baseline": {"2009": 40, "2010": 40},
                    "efficient": {"2009": 72 * 0.8, "2010": 72 * 0.8}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 80, "2010": 80},
                    "efficient": {"2009": 48 * 0.7, "2010": 48 * 0.7}},
                "competed": {
                    "baseline": {"2009": 40, "2010": 40},
                    "efficient": {"2009": 8 * 0.7, "2010": 8 * 0.7}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 120, "2010": 120},
                    "efficient": {"2009": 72 * 0.7, "2010": 72 * 0.7}},
                "competed": {
                    "baseline": {"2009": 60, "2010": 60},
                    "efficient": {"2009": 12 * 0.7, "2010": 12 * 0.7}}}},
        "lifetime": {
            "baseline": {"2009": 5, "2010": 5},
            "measure": 10}}

    return {
        "opts": opts,
        "opts_env_costs": opts_env_costs,
        "opts_sect_shapes": opts_sect_shapes,
        "cost_convert_data": cost_convert_data,
        "sample_measures_in_mkts": sample_measures_in_mkts,
        "sample_measures_in_env_costs": sample_measures_in_env_costs,
        "sample_measures_in_sect_shapes": sample_measures_in_sect_shapes,
        "sample_package_in_test1_highlevel": sample_package_in_test1_highlevel,
        "sample_package_in_test1_env_costs": sample_package_in_test1_env_costs,
        "sample_package_in_test1_attr_breaks": sample_package_in_test1_attr_breaks,
        "sample_package_in_sect_shapes": sample_package_in_sect_shapes,
        "sample_package_in_sect_shapes_bens": sample_package_in_sect_shapes_bens,
        "sample_package_in_test2": sample_package_in_test2,
        "genattr_ok_out_test1": genattr_ok_out_test1,
        "breaks_ok_out_test1": breaks_ok_out_test1,
        "contrib_ok_out_test1": contrib_ok_out_test1,
        "markets_ok_out_test1": markets_ok_out_test1,
        "markets_ok_out_test1_env_costs": markets_ok_out_test1_env_costs,
        "sect_shapes_ok_out": sect_shapes_ok_out,
        "sect_shapes_ok_out_bens": sect_shapes_ok_out_bens,
        "mseg_ok_in_test2": mseg_ok_in_test2,
        "mseg_ok_out_test2": mseg_ok_out_test2,
    }


def test_merge_measure_highlevel(test_data):
    """Test high-level 'merge_measures' outputs given valid inputs."""
    for ind, m in enumerate(test_data["sample_package_in_test1_highlevel"]):
        # Check for/record any potential heating/cooling equip/env measure
        # overlaps in the package
        m.htcl_adj_rec(test_data["opts"])
        # Merge packaged measure data
        m.merge_measures(test_data["opts"])
        # Check for correct high-level markets for packaged measure under
        # the technical potential scenario only
        dict_check(m.markets["Technical potential"]["master_mseg"],
                        test_data["markets_ok_out_test1"][ind])


def test_merge_measure_env_costs(test_data):
    """Test 'merge_measures' outputs given addition of envelope costs."""
    # Check for/record any potential heating/cooling equip/env measure
    # overlaps in the package
    test_data["sample_package_in_test1_env_costs"].htcl_adj_rec(
        test_data["opts_env_costs"])
    # Merge packaged measure data
    test_data["sample_package_in_test1_env_costs"].merge_measures(
        test_data["opts_env_costs"])
    # Check for correct high-level markets for packaged measure under
    # the technical potential scenario only, given envelope cost adder
    dict_check(
        test_data["sample_package_in_test1_env_costs"].markets[
            "Technical potential"]["master_mseg"],
        test_data["markets_ok_out_test1_env_costs"])


def test_merge_measure_detailed(test_data):
    """Test detailed 'merge_measures' outputs given valid inputs."""
    # Check for/record any potential heating/cooling equip/env measure
    # overlaps in the package
    test_data["sample_package_in_test1_attr_breaks"].htcl_adj_rec(test_data["opts"])
    # Merge packaged measure data
    test_data["sample_package_in_test1_attr_breaks"].merge_measures(test_data["opts"])
    output_lists = [
        test_data["sample_package_in_test1_attr_breaks"].name,
        test_data["sample_package_in_test1_attr_breaks"].climate_zone,
        test_data["sample_package_in_test1_attr_breaks"].bldg_type,
        test_data["sample_package_in_test1_attr_breaks"].structure_type,
        test_data["sample_package_in_test1_attr_breaks"].fuel_type["primary"],
        test_data["sample_package_in_test1_attr_breaks"].end_use["primary"]]
    # Test measure attributes (climate, building type, end use, etc.)
    for ind in range(0, len(output_lists)):
        assert sorted(test_data["genattr_ok_out_test1"][ind]) == \
            sorted(output_lists[ind])
    # Test detailed output breakouts
    dict_check(
        test_data["sample_package_in_test1_attr_breaks"].markets[
            "Technical potential"]["mseg_out_break"],
        test_data["breaks_ok_out_test1"])
    # Test contributing microsegments
    dict_check(
        test_data["sample_package_in_test1_attr_breaks"].markets[
            "Technical potential"]["mseg_adjust"][
            "contributing mseg keys and values"],
        test_data["contrib_ok_out_test1"])


def test_apply_pkg_benefits(test_data):
    """Test 'apply_pkg_benefits' function given valid inputs."""
    dict_check(
        test_data["sample_package_in_test2"].apply_pkg_benefits(
            test_data["mseg_ok_in_test2"], adopt_scheme="Technical potential",
            cm_key=""),
        test_data["mseg_ok_out_test2"])


def test_merge_measure_sect_shapes(test_data):
    """Test 'merge_measures' sector_shape outputs given valid inputs."""

    # Package without additional performance/cost benefits

    # Check for/record any potential heating/cooling equip/env measure
    # overlaps in the package
    test_data["sample_package_in_sect_shapes"].htcl_adj_rec(
        test_data["opts_sect_shapes"])
    # Merge packaged measure data
    test_data["sample_package_in_sect_shapes"].merge_measures(
        test_data["opts_sect_shapes"])
    # Check for correct sector shapes output for packaged measure under
    # the technical potential scenario only
    dict_check(
        test_data["sample_package_in_sect_shapes"].sector_shapes[
            "Technical potential"], test_data["sect_shapes_ok_out"])

    # Package with additional performance/cost benefits

    # Check for/record any potential heating/cooling equip/env measure
    # overlaps in the package
    test_data["sample_package_in_sect_shapes_bens"].htcl_adj_rec(
        test_data["opts_sect_shapes"])
    # Merge packaged measure data
    test_data["sample_package_in_sect_shapes_bens"].merge_measures(
        test_data["opts_sect_shapes"])
    # Check for correct sector shapes output for packaged measure under
    # the technical potential scenario only
    dict_check(
        test_data["sample_package_in_sect_shapes_bens"].sector_shapes[
            "Technical potential"], test_data["sect_shapes_ok_out_bens"])



