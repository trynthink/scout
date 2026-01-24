"""Test add_keyvals and add_keyvals_restrict functions."""

import pytest
import os
from scout.ecm_prep import Measure
from scout.ecm_prep_vars import UsefulVars, UsefulInputFiles
from .conftest import dict_check, NullOpts


class TestAddKeyVals:
    """Test 'add_keyvals' and 'add_keyvals_restrict' functions.

    Ensure that the functions properly add together input dictionaries.
    """

    @pytest.fixture(scope="class")
    def test_data(self):
        """Setup test data for add_keyvals tests."""
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
        
        ok_dict1_in = {
            "level 1a": {
                "level 2aa": {"2009": 2, "2010": 3},
                "level 2ab": {"2009": 4, "2010": 5}
            },
            "level 1b": {
                "level 2ba": {"2009": 6, "2010": 7},
                "level 2bb": {"2009": 8, "2010": 9}
            }
        }
        
        ok_dict2_in = {
            "level 1a": {
                "level 2aa": {"2009": 2, "2010": 3},
                "level 2ab": {"2009": 4, "2010": 5}
            },
            "level 1b": {
                "level 2ba": {"2009": 6, "2010": 7},
                "level 2bb": {"2009": 8, "2010": 9}
            }
        }
        
        ok_dict3_in = {
            "level 1a": {
                "level 2aa": {"2009": 2, "2010": 3},
                "level 2ab": {"2009": 4, "2010": 5}
            },
            "lifetime": {
                "level 2ba": {"2009": 6, "2010": 7},
                "level 2bb": {"2009": 8, "2010": 9}
            }
        }
        
        ok_dict4_in = {
            "level 1a": {
                "level 2aa": {"2009": 2, "2010": 3},
                "level 2ab": {"2009": 4, "2010": 5}
            },
            "lifetime": {
                "level 2ba": {"2009": 6, "2010": 7},
                "level 2bb": {"2009": 8, "2010": 9}
            }
        }
        
        fail_dict1_in = {
            "level 1a": {
                "level 2aa": {"2009": 2, "2010": 3},
                "level 2ab": {"2009": 4, "2010": 5}
            },
            "level 1b": {
                "level 2ba": {"2009": 6, "2010": 7},
                "level 2bb": {"2009": 8, "2010": 9}
            }
        }
        
        fail_dict2_in = {
            "level 1a": {
                "level 2aa": {"2009": 2, "2010": 3},
                "level 2ab": {"2009": 4, "2010": 5}
            },
            "level 1b": {
                "level 2ba": {"2009": 6, "2010": 7},
                "level 2bb": {"2009": 8, "2011": 9}
            }
        }
        
        ok_out = {
            "level 1a": {
                "level 2aa": {"2009": 4, "2010": 6},
                "level 2ab": {"2009": 8, "2010": 10}
            },
            "level 1b": {
                "level 2ba": {"2009": 12, "2010": 14},
                "level 2bb": {"2009": 16, "2010": 18}
            }
        }
        
        ok_out_restrict = {
            "level 1a": {
                "level 2aa": {"2009": 4, "2010": 6},
                "level 2ab": {"2009": 8, "2010": 10}
            },
            "lifetime": {
                "level 2ba": {"2009": 6, "2010": 7},
                "level 2bb": {"2009": 8, "2010": 9}
            }
        }
        
        return {
            'sample_measure_in': sample_measure_in,
            'ok_dict1_in': ok_dict1_in,
            'ok_dict2_in': ok_dict2_in,
            'ok_dict3_in': ok_dict3_in,
            'ok_dict4_in': ok_dict4_in,
            'fail_dict1_in': fail_dict1_in,
            'fail_dict2_in': fail_dict2_in,
            'ok_out': ok_out,
            'ok_out_restrict': ok_out_restrict
        }

    def test_ok_add_keyvals(self, test_data):
        """Test 'add_keyvals' function given valid inputs.
        
        Verify that the function correctly adds together dictionary values.
        """
        result = test_data['sample_measure_in'].add_keyvals(
            test_data['ok_dict1_in'],
            test_data['ok_dict2_in']
        )
        dict_check(result, test_data['ok_out'])

    def test_fail_add_keyvals(self, test_data):
        """Test 'add_keyvals' function given invalid inputs.
        
        Verify that KeyError is raised when dict keys don't match.
        """
        with pytest.raises(KeyError):
            test_data['sample_measure_in'].add_keyvals(
                test_data['fail_dict1_in'],
                test_data['fail_dict2_in']
            )

    def test_ok_add_keyvals_restrict(self, test_data):
        """Test 'add_keyvals_restrict' function given valid inputs.
        
        Verify that the function correctly adds together dictionary values
        while allowing restricted keys.
        """
        result = test_data['sample_measure_in'].add_keyvals_restrict(
            test_data['ok_dict3_in'],
            test_data['ok_dict4_in']
        )
        dict_check(result, test_data['ok_out_restrict'])
