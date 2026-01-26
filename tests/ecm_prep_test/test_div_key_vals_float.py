"""Test div_keyvals_float and div_keyvals_float_restrict functions."""

import pytest
import os
import copy
from scout.ecm_prep import Measure
from scout.ecm_prep_vars import UsefulVars, UsefulInputFiles
from .conftest import dict_check, NullOpts


class TestDivKeyValsFloat:
    """Test 'div_keyvals_float' and div_keyvals_float_restrict' functions.

    Ensure that the functions properly divide dict key values by a given
    factor.
    """

    @pytest.fixture(scope="class")
    def test_data(self):
        """Setup test data for div_keyvals_float tests."""
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

        ok_reduce_num = 4

        ok_dict_in = {
            "stock": {
                "total": {"2009": 100, "2010": 200},
                "competed": {"2009": 300, "2010": 400}
            },
            "energy": {
                "total": {"2009": 500, "2010": 600},
                "competed": {"2009": 700, "2010": 800},
                "efficient": {"2009": 700, "2010": 800}
            },
            "carbon": {
                "total": {"2009": 500, "2010": 600},
                "competed": {"2009": 700, "2010": 800},
                "efficient": {"2009": 700, "2010": 800}
            },
            "cost": {
                "baseline": {
                    "stock": {"2009": 900, "2010": 1000},
                    "energy": {"2009": 900, "2010": 1000},
                    "carbon": {"2009": 900, "2010": 1000}
                },
                "measure": {
                    "stock": {"2009": 1100, "2010": 1200},
                    "energy": {"2009": 1100, "2010": 1200},
                    "carbon": {"2009": 1100, "2010": 1200}
                }
            }
        }

        ok_out = {
            "stock": {
                "total": {"2009": 25, "2010": 50},
                "competed": {"2009": 75, "2010": 100}
            },
            "energy": {
                "total": {"2009": 125, "2010": 150},
                "competed": {"2009": 175, "2010": 200},
                "efficient": {"2009": 175, "2010": 200}
            },
            "carbon": {
                "total": {"2009": 125, "2010": 150},
                "competed": {"2009": 175, "2010": 200},
                "efficient": {"2009": 175, "2010": 200}
            },
            "cost": {
                "baseline": {
                    "stock": {"2009": 225, "2010": 250},
                    "energy": {"2009": 225, "2010": 250},
                    "carbon": {"2009": 225, "2010": 250}
                },
                "measure": {
                    "stock": {"2009": 275, "2010": 300},
                    "energy": {"2009": 275, "2010": 300},
                    "carbon": {"2009": 275, "2010": 300}
                }
            }
        }

        ok_out_restrict = {
            "stock": {
                "total": {"2009": 25, "2010": 50},
                "competed": {"2009": 75, "2010": 100}
            },
            "energy": {
                "total": {"2009": 500, "2010": 600},
                "competed": {"2009": 700, "2010": 800},
                "efficient": {"2009": 700, "2010": 800}
            },
            "carbon": {
                "total": {"2009": 500, "2010": 600},
                "competed": {"2009": 700, "2010": 800},
                "efficient": {"2009": 700, "2010": 800}
            },
            "cost": {
                "baseline": {
                    "stock": {"2009": 225, "2010": 250},
                    "energy": {"2009": 900, "2010": 1000},
                    "carbon": {"2009": 900, "2010": 1000}
                },
                "measure": {
                    "stock": {"2009": 275, "2010": 300},
                    "energy": {"2009": 1100, "2010": 1200},
                    "carbon": {"2009": 1100, "2010": 1200}
                }
            }
        }

        return {
            'sample_measure_in': sample_measure_in,
            'ok_reduce_num': ok_reduce_num,
            'ok_dict_in': ok_dict_in,
            'ok_out': ok_out,
            'ok_out_restrict': ok_out_restrict
        }

    def test_ok_div(self, test_data):
        """Test 'div_keyvals_float' function given valid inputs.

        Verify that the function correctly divides dictionary values
        by a given factor.
        """
        result = test_data['sample_measure_in'].div_keyvals_float(
            copy.deepcopy(test_data['ok_dict_in']),
            test_data['ok_reduce_num']
        )
        dict_check(result, test_data['ok_out'])

    def test_ok_div_restrict(self, test_data):
        """Test 'div_keyvals_float_restrict' function given valid inputs.

        Verify that the function correctly divides dictionary values
        by a given factor while respecting restricted keys.
        """
        result = test_data['sample_measure_in'].div_keyvals_float_restrict(
            copy.deepcopy(test_data['ok_dict_in']),
            test_data['ok_reduce_num']
        )
        dict_check(result, test_data['ok_out_restrict'])
