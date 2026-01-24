"""Test div_keyvals function for normalizing dictionary values."""

import pytest
import os
from scout.ecm_prep import Measure
from scout.ecm_prep_vars import UsefulVars, UsefulInputFiles
from .conftest import dict_check, NullOpts


class TestDivKeyVals:
    """Test 'div_keyvals' function.

    Ensure that the function properly divides the key values of one dict
    by those of another. Test inputs reflect the use of this function
    to generate output partitioning fractions (used to break out
    measure results by climate zone, building sector, end use).
    """

    @pytest.fixture(scope="class")
    def test_data(self):
        """Setup test data for div_keyvals tests."""
        # Base directory
        base_dir = os.getcwd()
        # Null user options/options dict
        null_opts = NullOpts()
        opts, opts_dict = [null_opts.opts, null_opts.opts_dict]
        handyfiles = UsefulInputFiles(opts)
        handyvars = UsefulVars(base_dir, handyfiles, opts)
        
        sample_measure_dict = {
            "name": "sample measure 1",
            "active": 1,
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "bldg_type": ["single family home"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None
            },
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["heating", "cooling"],
                "secondary": None
            },
            "technology": {
                "primary": ["resistance heat", "ASHP", "GSHP", "room AC"],
                "secondary": None
            }
        }
        
        sample_measure_in = Measure(
            base_dir, handyvars, handyfiles, opts_dict,
            **sample_measure_dict
        )
        
        ok_reduce_dict = {"2009": 100, "2010": 100}
        
        ok_dict_in = {
            "AIA CZ1": {
                "Residential": {
                    "Heating": {"2009": 10, "2010": 10},
                    "Cooling": {"2009": 15, "2010": 15}
                },
                "Commercial": {
                    "Heating": {"2009": 20, "2010": 20},
                    "Cooling": {"2009": 25, "2010": 25}
                }
            },
            "AIA CZ2": {
                "Residential": {
                    "Heating": {"2009": 30, "2010": 30},
                    "Cooling": {"2009": 35, "2010": 35}
                },
                "Commercial": {
                    "Heating": {"2009": 40, "2010": 40},
                    "Cooling": {"2009": 45, "2010": 45}
                }
            }
        }
        
        ok_out = {
            "AIA CZ1": {
                "Residential": {
                    "Heating": {"2009": .10, "2010": .10},
                    "Cooling": {"2009": .15, "2010": .15}
                },
                "Commercial": {
                    "Heating": {"2009": .20, "2010": .20},
                    "Cooling": {"2009": .25, "2010": .25}
                }
            },
            "AIA CZ2": {
                "Residential": {
                    "Heating": {"2009": .30, "2010": .30},
                    "Cooling": {"2009": .35, "2010": .35}
                },
                "Commercial": {
                    "Heating": {"2009": .40, "2010": .40},
                    "Cooling": {"2009": .45, "2010": .45}
                }
            }
        }
        
        return {
            'sample_measure_in': sample_measure_in,
            'ok_reduce_dict': ok_reduce_dict,
            'ok_dict_in': ok_dict_in,
            'ok_out': ok_out
        }

    def test_ok(self, test_data):
        """Test 'div_keyvals' function given valid inputs.
        
        Verify that the function correctly divides dictionary values
        and produces normalized output fractions.
        """
        result = test_data['sample_measure_in'].div_keyvals(
            test_data['ok_dict_in'],
            test_data['ok_reduce_dict']
        )
        dict_check(result, test_data['ok_out'])
