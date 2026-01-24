"""Test check_meas_inputs function for validating market inputs."""

import pytest
import os
from scout.ecm_prep import Measure
from scout.ecm_prep_vars import UsefulVars, UsefulInputFiles
from .conftest import NullOpts


class TestCheckMarkets:
    """Test 'check_meas_inputs' function.

    Ensure that the function properly raises a ValueError when
    a measure's applicable baseline market input names are invalid.
    """

    @pytest.fixture(scope="class")
    def sample_measures_fail(self):
        """Setup sample measures with invalid market inputs."""
        # Base directory
        base_dir = os.getcwd()
        # Null user options/options dict
        null_opts = NullOpts()
        opts, opts_dict = [null_opts.opts, null_opts.opts_dict]
        handyfiles = UsefulInputFiles(opts)
        handyvars = UsefulVars(base_dir, handyfiles, opts)
        
        sample_measures_fail_dicts = [
            {
                "name": "sample measure 5",
                "market_entry_year": None,
                "market_exit_year": None,
                "installed_cost": 999,
                "cost_units": "dummy",
                "energy_efficiency": {
                    "primary": 999, "secondary": None
                },
                "energy_efficiency_units": {
                    "primary": "dummy", "secondary": None
                },
                "product_lifetime": 999,
                "climate_zone": "all",
                "bldg_type": "all commercial",
                "structure_type": "all",
                "fuel_type": {
                    "primary": [
                        "electricity", "natty gas"
                    ],
                    "secondary": None
                },
                "fuel_switch_to": None,
                "end_use": {
                    "primary": [
                        "heating", "water heating"
                    ],
                    "secondary": None
                },
                "technology": {
                    "primary": [
                        "all heating", "electric WH"
                    ],
                    "secondary": None
                }
            },
            {
                "name": "sample measure 6",
                "market_entry_year": None,
                "market_exit_year": None,
                "installed_cost": 999,
                "cost_units": "dummy",
                "energy_efficiency": {
                    "primary": 999, "secondary": None
                },
                "energy_efficiency_units": {
                    "primary": "dummy", "secondary": None
                },
                "product_lifetime": 999,
                "climate_zone": "all",
                "bldg_type": ["assembling", "education"],
                "structure_type": "all",
                "fuel_type": {
                    "primary": "natural gas",
                    "secondary": None
                },
                "fuel_switch_to": None,
                "end_use": {
                    "primary": "heating",
                    "secondary": None
                },
                "technology": {
                    "primary": "all",
                    "secondary": None
                }
            }
        ]
        
        sample_measures_fail = [
            Measure(base_dir, handyvars, handyfiles, opts_dict, **x)
            for x in sample_measures_fail_dicts
        ]
        
        return sample_measures_fail

    def test_invalid_mkts(self, sample_measures_fail):
        """Test 'check_meas_inputs' function given invalid inputs.
        
        Verify that measures with invalid market input names raise
        exceptions when checked.
        """
        for m in sample_measures_fail:
            with pytest.raises(Exception):
                m.check_meas_inputs()
