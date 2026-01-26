"""Shared pytest fixtures and utilities for ECM prep tests."""

# Import code to be tested
from scout.ecm_prep import ECMPrepHelper, ECMPrep  # noqa: F401
from scout.ecm_prep_vars import UsefulVars, UsefulInputFiles
from scout.config import FilePaths as fp  # noqa: F401
from scout.ecm_prep_args import ecm_args

# Import needed packages
from pathlib import Path
import pytest
import numpy
import os
import warnings  # noqa: F401
import copy  # noqa: F401
import json  # noqa: F401
import itertools
import pandas as pd  # noqa: F401
from collections import OrderedDict  # noqa: F401


def dict_check(dict1, dict2):
    """Check the equality of two dicts.

    This replaces the CommonMethods.dict_check method from the original
    unittest-based tests. Can be used as: dict_check(result, expected)

    Args:
        dict1 (dict): First dictionary to be compared
        dict2 (dict): Second dictionary to be compared

    Raises:
        AssertionError: If dictionaries are not equal.
    """
    # zip() and zip_longest() produce tuples for the items
    # identified, where in the case of a dict, the first item
    # in the tuple is the key and the second item is the value;
    # in the case where the dicts are not of identical size,
    # zip_longest() will use the fill value created below as a
    # substitute in the dict that has missing content; this
    # value is given as a tuple to be of comparable structure
    # to the normal output from zip_longest()
    fill_val = ('substituted entry', 5.2)

    # In this structure, k and k2 are the keys that correspond to
    # the dicts or unitary values that are found in i and i2,
    # respectively, at the current level of the recursive
    # exploration of dict1 and dict2, respectively
    for (k, i), (k2, i2) in itertools.zip_longest(
        sorted(dict1.items()),
        sorted(dict2.items()),
        fillvalue=fill_val
    ):
        # Confirm that at the current location in the dict structure,
        # the keys are equal; this should fail if one of the dicts
        # is empty, is missing section(s), or has different key names
        assert k == k2

        # If the recursion has not yet reached the terminal/leaf node
        if isinstance(i, dict):
            # Test that the dicts from the current keys are equal
            assert set(i.keys()) == set(i2.keys())
            # Continue to recursively traverse the dict
            dict_check(i, i2)
        # At the terminal/leaf node, formatted as a numpy array or list
        # (for time sensitive valuation test cases)
        elif isinstance(i, numpy.ndarray) or isinstance(i, list):
            assert type(i) is type(i2) and len(i) == len(i2)
            for x in range(0, len(i)):
                # Handle lists of strings
                if isinstance(i[x], str):
                    assert i[x] == i2[x]
                # Ensure that very small numbers do not reduce to 0
                elif round(i[x], 5) != 0:
                    assert i[x] == pytest.approx(i2[x], abs=1e-5)
                else:
                    assert i[x] == pytest.approx(i2[x], abs=1e-10)
        elif isinstance(i, str):
            assert i == i2
        # At the terminal/leaf node, formatted as a point value
        else:
            # Compare the values, allowing for floating point inaccuracy.
            # Ensure that very small numbers do not reduce to 0
            if round(i, 1) != 0:
                assert i == pytest.approx(i2, abs=0.01)
            else:
                assert i == pytest.approx(i2, abs=1e-10)


class UserOptions:
    """Generate sample user-specified execution options."""

    def __init__(self, site_energy, capt_energy, regions, tsv_metrics,
                 sect_shapes, rp_persist, health_costs, split_fuel,
                 no_scnd_lgt, floor_start, pkg_env_costs, exog_hp_rates,
                 grid_decarb, adopt_scn_restrict, retro_set, add_typ_eff,
                 pkg_env_sep, alt_ref_carb, detail_brkout, fugitive_emissions,
                 verbose, no_eff_capt, no_lnkd_stk, no_lnkd_op,
                 elec_upgrade_costs,
                 low_volume_rate, state_appl_regs, bps, codes, incentive_levels,
                 incentive_restrictions):
        # Options include site energy outputs, captured energy site-source
        # calculation method, alternate regions, time sensitive output metrics,
        # sector-level load shapes, and verbose mode that prints all warnings
        self.site_energy = site_energy
        self.captured_energy = capt_energy
        self.alt_regions = regions
        self.rp_persist = rp_persist
        self.verbose = verbose
        self.tsv_metrics = tsv_metrics
        self.health_costs = health_costs
        self.sect_shapes = sect_shapes
        self.split_fuel = split_fuel
        self.no_scnd_lgt = no_scnd_lgt
        self.floor_start = floor_start
        self.pkg_env_costs = pkg_env_costs
        self.exog_hp_rates = exog_hp_rates
        self.grid_decarb = grid_decarb
        self.adopt_scn_restrict = adopt_scn_restrict
        self.retro_set = retro_set
        self.add_typ_eff = add_typ_eff
        self.pkg_env_sep = pkg_env_sep
        self.alt_ref_carb = alt_ref_carb
        self.detail_brkout = detail_brkout
        self.fugitive_emissions = fugitive_emissions
        self.no_eff_capt = no_eff_capt
        self.no_lnkd_stk_costs = no_lnkd_stk
        self.no_lnkd_op_costs = no_lnkd_op
        self.elec_upgrade_costs = elec_upgrade_costs
        self.low_volume_rate = low_volume_rate
        self.state_appl_regs = state_appl_regs
        self.bps = bps
        self.codes = codes
        self.incentive_levels = incentive_levels
        self.incentive_restrictions = incentive_restrictions


class NullOpts:
    """Generate null set of user-specified execution options.

    Attributes:
        opts (object): Sample null user options.
        opts_dict (dict): Dict-formatted sample null user options.
    """

    def __init__(self):
        # Note: technically, the 'detail_brkout' opt should be set to
        # False for this null case; however, because tests in this suite
        # were previously developed using the most detailed regional
        # breakouts, the option is set to continue using those breakouts
        # for regions only
        test_ecms = Path(__file__).parent.parent / "test_files" / "ecm_definitions"
        self.opts = ecm_args([
            "--ecm_directory", str(test_ecms),
            "--detail_brkout", "regions",
            "--alt_regions", "AIA",
            "--no_eff_capt",
            "--no_lnkd_stk_costs", "in_adopt_and_report",
            "--elec_upgrade_costs", "ignore"
        ])
        self.opts_dict = vars(self.opts)


# Pytest fixtures
@pytest.fixture
def null_opts():
    """Fixture providing null options."""
    return NullOpts()


@pytest.fixture
def base_dir():
    """Fixture providing base directory."""
    return os.getcwd()


@pytest.fixture
def handy_files(null_opts):
    """Fixture providing UsefulInputFiles object."""
    return UsefulInputFiles(null_opts.opts)


@pytest.fixture
def handy_vars(base_dir, handy_files, null_opts):
    """Fixture providing UsefulVars object."""
    return UsefulVars(base_dir, handy_files, null_opts.opts)
