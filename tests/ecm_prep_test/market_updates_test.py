#!/usr/bin/env python3

""" Tests for Market Updates (fill_mkts function) """

from scout.ecm_prep import Measure, MeasurePackage, ECMPrepHelper
from scout.ecm_prep_vars import UsefulVars, UsefulInputFiles
from scout.config import FilePaths as fp
import pytest
import numpy
import os
import copy
import warnings
from collections import OrderedDict
from pathlib import Path
from tests.ecm_prep_test.common import NullOpts, dict_check

# Import extracted test data
from tests.ecm_prep_test.test_data.market_updates_test_data import (
    ok_tpmeas_fullchk_break_out,
    sample_cpl_in,
    ok_tpmeas_partchk_msegout,
    sample_cpl_in_state,
    sample_cpl_in_emm,
    sample_mseg_in,
    ok_hpmeas_rates_breakouts,
    ok_partialmeas_in,
    ok_hpmeas_rates_mkts_out,
    ok_tpmeas_fullchk_msegout,
    sample_mseg_in_emm,
    sample_mseg_in_state,
    ok_tpmeas_partchk_msegout_emm,
    ok_tpmeas_partchk_msegout_state,
)


@pytest.fixture(scope="module")
def market_test_data():
    """Fixture providing test data for market updates tests."""
    # Base directory
    base_dir = os.getcwd()
    # Null user options/options dict
    opts, opts_dict = [NullOpts().opts, NullOpts().opts_dict]
    # National-level variables (AIA regions)
    handyfiles = UsefulInputFiles(opts)
    handyvars = UsefulVars(base_dir, handyfiles, opts)
    handyvars.com_eqp_eus_nostk = ["lighting", "PCs", "MELs"]
    # Site energy assessment settings
    opts_site_energy, opts_site_energy_dict = [
        copy.deepcopy(x) for x in [opts, opts_dict]]
    opts_site_energy.site_energy, \
        opts_site_energy_dict["site_energy"] = (True for n in range(2))
    # Regional-level variables (EIA EMM regions)
    opts_emm, opts_emm_dict = [
        copy.deepcopy(x) for x in [opts, opts_dict]]
    opts_emm.alt_regions, opts_emm_dict["alt_regions"] = (
        "EMM" for n in range(2))
    opts_emm.site_energy, opts_emm_dict["site_energy"] = (
        True for n in range(2))
    handyfiles_emm = UsefulInputFiles(opts_emm)
    handyvars_emm = UsefulVars(
        base_dir, handyfiles_emm, opts_emm)
    # Regional-level variables (states)
    opts_state, opts_state_dict = [
        copy.deepcopy(x) for x in [opts, opts_dict]]
    opts_state.alt_regions, opts_state_dict["alt_regions"] = (
        "State" for n in range(2))
    opts_state.site_energy, opts_state_dict["site_energy"] = (
        True for n in range(2))
    handyfiles_state = UsefulInputFiles(opts_state)
    handyfiles_state.local_cost_adj = \
        Path(__file__).parent.parent / "test_files" / "loc_cost_adj_test.csv"
    handyvars_state = UsefulVars(
        base_dir, handyfiles_state, opts_state)
    # Suppress regional cost adjustment factors for states
    handyvars_state.reg_cost_adj = None
    # Fuel switching with exogenous rates
    opts_hp_rates, opts_hp_rates_dict = [
        copy.deepcopy(x) for x in [opts_emm, opts_emm_dict]]
    opts_hp_rates.split_fuel, opts_hp_rates_dict["split_fuel"] = (
        True for n in range(2))
    opts_hp_rates.exog_hp_rates, opts_hp_rates_dict[
        "exog_hp_rates"] = (["gh-aggressive", '1'] for n in range(2))
    opts_hp_rates.adopt_scn_usr, opts_hp_rates_dict[
        "adopt_scn_usr"] = (["Max adoption potential"] for n in range(2))
    handyvars_hp_rates = UsefulVars(
        base_dir, handyfiles_emm, opts_hp_rates)
    handyvars_hp_rates.hp_rates_reg_map = {
        "midwest": [
            "SPPN", "MISW", "SPPC", "MISC",
            "PJMW", "PJMC", "MISE"],
        "northeast": [
            "PJME", "NYCW", "NYUP", "ISNE"],
        "south": [
            "SPPS", "TRE", "MISS", "SRCE", "PJMD",
            "SRCA", "SRSE", "FRCC"],
        "west": [
            "NWPP", "BASN", "RMRG", "SRSG", "CASO", "CANO"]
        }
    handyvars_hp_rates.hp_rates = {
        "data (by scenario)": {
            "gh-aggressive": {
                "south": {
                    "residential": {
                        "electricity": {
                            "heating": {
                                # Assume same rates as NG for simplicity
                                "resistance heat": {
                                    "existing": {
                                        "2009": 0.07500000000000001,
                                        "2010": 0.1
                                    },
                                    "new": {
                                        "2009": 0.29,
                                        "2010": 0.33
                                    }
                                }
                            }

                        },
                        "natural gas": {
                            "heating": {
                                "furnace (NG)": {
                                    "existing": {
                                        "2009": 0.07500000000000001,
                                        "2010": 0.1
                                    },
                                    "new": {
                                        "2009": 0.29,
                                        "2010": 0.33
                                    }
                                }
                            }
                        }

                    }
                }
            }
        }
    }
    # Fuel switching with no exogenous rates
    opts_hp_no_rates, opts_hp_no_rates_dict = [
        copy.deepcopy(x) for x in [opts_hp_rates, opts_hp_rates_dict]]
    opts_hp_no_rates.exog_hp_rates, opts_hp_no_rates_dict[
        "exog_hp_rates"] = (False for n in range(2))
    handyvars_hp_norates = UsefulVars(
        base_dir, handyfiles_emm, opts_hp_no_rates)
    handyvars_hp_rates.out_break_in, handyvars_hp_norates.out_break_in = (
        {'TRE': {'Residential (Existing)': {
            'Heating (Equip.)': {
                'Electric': {},
                'Non-Electric': {}
            },
            'Cooling (Equip.)': {
                'Electric': {},
                'Non-Electric': {}
            }}}} for n in range(2))
    # Fugitive emissions for supply chain methane leakage
    ok_fmeth_measures_in = [{
        "name": "sample measure 1 - with fugitive emissions + low leakage",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": {
            "cooling": 3,
            "heating": 3},
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": {
            "cooling": 0.5,
            "heating": 1},
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": ["electricity", "natural gas"],
        "fuel_switch_to": "electricity",
        "end_use": ["heating", "cooling"],
        "technology": ["furnace (NG)", "central AC"]},
        {
        "name": "sample fugitive emissions measure 2 + mid leakage",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": {
            "cooling": 3,
            "heating": 3},
        "energy_efficiency_units": "AFUE",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": {
            "cooling": 0.5,
            "heating": 1},
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": ["electricity", "natural gas"],
        "fuel_switch_to": None,
        "end_use": ["heating", "cooling"],
        "technology": ["furnace (NG)", "central AC"]},
        {
        "name": "sample fugitive emissions measure 3 + high leakage",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": {
            "cooling": 3,
            "heating": 3},
        "energy_efficiency_units": "AFUE",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": {
            "cooling": 0.5,
            "heating": 1},
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": ["electricity", "natural gas"],
        "fuel_switch_to": None,
        "end_use": ["heating", "cooling"],
        "technology": ["furnace (NG)", "central AC"]},
        {
        "name": "sample non-fugitive emissions measure 1",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": 3,
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "cooling",
        "technology": "central AC"}]
    opts_fmeth, opts_fmeth_dict = [[
        copy.deepcopy(n) for x in range(len(ok_fmeth_measures_in))]
        for n in [opts_emm, opts_emm_dict]]
    # Initialize measure-specific handy vars
    handyvars_fmeth = [None for x in range(len(ok_fmeth_measures_in))]
    # Initialize measure-specific low GWP settings
    mth_lkg_settings = [['1', '1', '1'], ['1', '1', '2'],
                        ['1', '1', '3'], ['1', '1', '1']]
    # Loop through refrigerant emissions measures and hard code user
    # settings and handy vars
    for x in range(len(ok_fmeth_measures_in)):
        # Measure-specific user options
        opts_fmeth[x].adopt_scn_restrict, opts_fmeth_dict[x][
            "adopt_scn_restrict"] = (
            ["Technical potential"] for n in range(2))
        opts_fmeth[x].fugitive_emissions, opts_fmeth_dict[x][
            "fugitive_emissions"] = (
                mth_lkg_settings[x] for n in range(2))
        # Measure-specific handy vars
        handyvars_fmeth[x] = UsefulVars(
            base_dir, handyfiles_emm, opts_fmeth[x])
        handyvars_fmeth[x].fugitive_emissions_map = numpy.array([
            ('TRE', 0., 0.,
                0., 0., 0., 0., 0., 0., 0.,
                0., 0., 0.,
                0., 0.,
                0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
                0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0., 0.,
                0., 1., 0., 0., 0., 0., 0., 0., 0.)],
            dtype=[('State', '<U25'), ('AL', '<f8'), ('AK', '<f8'),
                   ('AZ', '<f8'), ('AR', '<f8'), ('CA', '<f8'),
                   ('CO', '<f8'), ('CT', '<f8'), ('DE', '<f8'),
                   ('DC', '<f8'),
                   ('FL', '<f8'), ('GA', '<f8'),
                   ('HI', '<f8'),
                   ('ID', '<f8'), ('IL', '<f8'),
                   ('IN', '<f8'), ('IA', '<f8'), ('KS', '<f8'),
                   ('KY', '<f8'), ('LA', '<f8'), ('ME', '<f8'),
                   ('MD', '<f8'), ('MA', '<f8'), ('MI', '<f8'),
                   ('MN', '<f8'), ('MS', '<f8'), ('MO', '<f8'),
                   ('MT', '<f8'), ('NE', '<f8'), ('NV', '<f8'),
                   ('NH', '<f8'), ('NJ', '<f8'), ('NM', '<f8'),
                   ('NY', '<f8'), ('NC', '<f8'), ('ND', '<f8'),
                   ('OH', '<f8'), ('OK', '<f8'), ('OR', '<f8'),
                   ('PA', '<f8'), ('RI', '<f8'), ('SC', '<f8'),
                   ('SD', '<f8'), ('TN', '<f8'), ('TX', '<f8'),
                   ('UT', '<f8'), ('VT', '<f8'), ('VA', '<f8'),
                   ('WA', '<f8'), ('WV', '<f8'), ('WI', '<f8'),
                   ('WY', '<f8')])
        handyvars_fmeth[x].fug_emissions = {
            "methane": {
                "production_segment_leakage_rates": {
                    "High": {
                        "AL": 0.017,
                        "AZ": 0.046,
                        "AR": 0.018000000000000002,
                        "CA": 0.038,
                        "CO": 0.040999999999999995,
                        "CT": 0.012,
                        "DE": 0.012,
                        "FL": 0.015,
                        "GA": 0.015,
                        "ID": 0.027999999999999997,
                        "IL": 0.028999999999999998,
                        "IN": 0.032,
                        "IA": 0.027999999999999997,
                        "KS": 0.051,
                        "KY": 0.017,
                        "LA": 0.016,
                        "ME": 0.03,
                        "MD": 0.012,
                        "MA": 0.013000000000000001,
                        "MI": 0.019,
                        "MN": 0.022000000000000002,
                        "MS": 0.027000000000000003,
                        "MO": 0.032,
                        "MT": 0.027000000000000003,
                        "NE": 0.037000000000000005,
                        "NV": 0.025,
                        "NH": 0.027999999999999997,
                        "NJ": 0.012,
                        "NM": 0.044000000000000004,
                        "NY": 0.012,
                        "NC": 0.015,
                        "ND": 0.024,
                        "OH": 0.012,
                        "OK": 0.036000000000000004,
                        "OR": 0.026000000000000002,
                        "PA": 0.012,
                        "RI": 0.012,
                        "SC": 0.015,
                        "SD": 0.026000000000000002,
                        "TN": 0.012,
                        "TX": 0.025,
                        "UT": 0.021,
                        "VT": 0.03,
                        "VA": 0.013999999999999999,
                        "WA": 0.03,
                        "WV": 0.012,
                        "WI": 0.031,
                        "WY": 0.015
                     },
                    "Low": {
                        "AL": 0.006999999999999999,
                        "AZ": 0.021,
                        "AR": 0.008,
                        "CA": 0.023,
                        "CO": 0.02,
                        "CT": 0.006,
                        "DE": 0.006,
                        "FL": 0.006,
                        "GA": 0.006,
                        "ID": 0.023,
                        "IL": 0.016,
                        "IN": 0.016,
                        "IA": 0.023,
                        "KS": 0.024,
                        "KY": 0.008,
                        "LA": 0.006,
                        "ME": 0.03,
                        "MD": 0.006,
                        "MA": 0.008,
                        "MI": 0.01,
                        "MN": 0.017,
                        "MS": 0.012,
                        "MO": 0.015,
                        "MT": 0.02,
                        "NE": 0.018000000000000002,
                        "NV": 0.011000000000000001,
                        "NH": 0.027000000000000003,
                        "NJ": 0.006,
                        "NM": 0.021,
                        "NY": 0.006,
                        "NC": 0.006999999999999999,
                        "ND": 0.01,
                        "OH": 0.006,
                        "OK": 0.016,
                        "OR": 0.015,
                        "PA": 0.006,
                        "RI": 0.006,
                        "SC": 0.006999999999999999,
                        "SD": 0.015,
                        "TN": 0.006,
                        "TX": 0.01,
                        "UT": 0.009000000000000001,
                        "VT": 0.03,
                        "VA": 0.006999999999999999,
                        "WA": 0.03,
                        "WV": 0.006,
                        "WI": 0.019,
                        "WY": 0.006
                     },
                    "Mid": {
                        "AL": 0.011,
                        "AZ": 0.034,
                        "AR": 0.011,
                        "CA": 0.028,
                        "CO": 0.031,
                        "CT": 0.009,
                        "DE": 0.009,
                        "FL": 0.01,
                        "GA": 0.01,
                        "ID": 0.021,
                        "IL": 0.021,
                        "IN": 0.023,
                        "IA": 0.022,
                        "KS": 0.036,
                        "KY": 0.012,
                        "LA": 0.01,
                        "ME": 0.009,
                        "MD": 0.009,
                        "MA": 0.01,
                        "MI": 0.014,
                        "MN": 0.017,
                        "MS": 0.018,
                        "MO": 0.023,
                        "MT": 0.022,
                        "NE": 0.028,
                        "NV": 0.019,
                        "NH": 0.009,
                        "NJ": 0.009,
                        "NM": 0.033,
                        "NY": 0.009,
                        "NC": 0.01,
                        "ND": 0.022,
                        "OH": 0.009,
                        "OK": 0.025,
                        "OR": 0.019,
                        "PA": 0.009,
                        "RI": 0.009,
                        "SC": 0.01,
                        "SD": 0.02,
                        "TN": 0.009,
                        "TX": 0.017,
                        "UT": 0.015,
                        "VT": 0.009,
                        "VA": 0.011,
                        "WA": 0.022,
                        "WV": 0.009,
                        "WI": 0.022,
                        "WY": 0.011
                     }},
                "other_segment_leakage_rates": {
                    "Gathering": 0.004601769911504425,
                    "Processing": 0.0012743362831858407,
                    "Transmission & Storage": 0.003185840707964602,
                    "Local Distribution": 0.0007787610619469027,
                    "Oil Refining and Transportation": 6.017699115044e-05},
                "total_leakage_rate": {
                    "High": {
                        "AL": 0.027,
                        "AZ": 0.056,
                        "AR": 0.028,
                        "CA": 0.048,
                        "CO": 0.051,
                        "CT": 0.022,
                        "DE": 0.022,
                        "FL": 0.025,
                        "GA": 0.025,
                        "ID": 0.038,
                        "IL": 0.039,
                        "IN": 0.042,
                        "IA": 0.038,
                        "KS": 0.061,
                        "KY": 0.027,
                        "LA": 0.026,
                        "ME": 0.04,
                        "MD": 0.022,
                        "MA": 0.023,
                        "MI": 0.029,
                        "MN": 0.032,
                        "MS": 0.037,
                        "MO": 0.042,
                        "MT": 0.037,
                        "NE": 0.047,
                        "NV": 0.035,
                        "NH": 0.038,
                        "NJ": 0.022,
                        "NM": 0.054,
                        "NY": 0.022,
                        "NC": 0.025,
                        "ND": 0.034,
                        "OH": 0.022,
                        "OK": 0.046,
                        "OR": 0.036,
                        "PA": 0.022,
                        "RI": 0.022,
                        "SC": 0.025,
                        "SD": 0.036,
                        "TN": 0.022,
                        "TX": 0.035,
                        "UT": 0.031,
                        "VT": 0.04,
                        "VA": 0.024,
                        "WA": 0.04,
                        "WV": 0.022,
                        "WI": 0.041,
                        "WY": 0.025
                     },
                    "Low": {
                        "AL": 0.017,
                        "AZ": 0.031,
                        "AR": 0.018,
                        "CA": 0.033,
                        "CO": 0.03,
                        "CT": 0.016,
                        "DE": 0.016,
                        "FL": 0.016,
                        "GA": 0.016,
                        "ID": 0.033,
                        "IL": 0.026,
                        "IN": 0.026,
                        "IA": 0.033,
                        "KS": 0.034,
                        "KY": 0.018,
                        "LA": 0.016,
                        "ME": 0.04,
                        "MD": 0.016,
                        "MA": 0.018,
                        "MI": 0.02,
                        "MN": 0.027,
                        "MS": 0.022,
                        "MO": 0.025,
                        "MT": 0.03,
                        "NE": 0.028,
                        "NV": 0.021,
                        "NH": 0.037,
                        "NJ": 0.016,
                        "NM": 0.031,
                        "NY": 0.016,
                        "NC": 0.017,
                        "ND": 0.02,
                        "OH": 0.016,
                        "OK": 0.026,
                        "OR": 0.025,
                        "PA": 0.016,
                        "RI": 0.016,
                        "SC": 0.017,
                        "SD": 0.025,
                        "TN": 0.016,
                        "TX": 0.02,
                        "UT": 0.019,
                        "VT": 0.04,
                        "VA": 0.017,
                        "WA": 0.04,
                        "WV": 0.016,
                        "WI": 0.029,
                        "WY": 0.016
                     },
                    "Mid": {
                        "AL": 0.021,
                        "AZ": 0.044,
                        "AR": 0.021,
                        "CA": 0.038,
                        "CO": 0.041,
                        "CT": 0.019,
                        "DE": 0.019,
                        "FL": 0.02,
                        "GA": 0.02,
                        "ID": 0.031,
                        "IL": 0.031,
                        "IN": 0.033,
                        "IA": 0.032,
                        "KS": 0.046,
                        "KY": 0.022,
                        "LA": 0.02,
                        "ME": 0.019,
                        "MD": 0.019,
                        "MA": 0.02,
                        "MI": 0.024,
                        "MN": 0.027,
                        "MS": 0.028,
                        "MO": 0.033,
                        "MT": 0.032,
                        "NE": 0.038,
                        "NV": 0.029,
                        "NH": 0.019,
                        "NJ": 0.019,
                        "NM": 0.043,
                        "NY": 0.019,
                        "NC": 0.02,
                        "ND": 0.032,
                        "OH": 0.019,
                        "OK": 0.035,
                        "OR": 0.029,
                        "PA": 0.019,
                        "RI": 0.019,
                        "SC": 0.02,
                        "SD": 0.03,
                        "TN": 0.019,
                        "TX": 0.027,
                        "UT": 0.025,
                        "VT": 0.019,
                        "VA": 0.021,
                        "WA": 0.032,
                        "WV": 0.019,
                        "WI": 0.032,
                        "WY": 0.021
                     }}
                },
            "refrigerants": {}
        }
    # Sample refrigerant emissions measures to initialize below
    ok_frefr_measures_in = [{
        "name": "res. frefr. 1 â€“ CAC/NG to HP, low GWP",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": 3,
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": {
            "cooling": 0.5,
            "heating": 1},
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": ["electricity", "natural gas"],
        "fuel_switch_to": "electricity",
        "tech_switch_to": "ASHP",
        "end_use": ["heating", "cooling"],
        "technology": ["furnace (NG)", "central AC"],
        "low_gwp_refrigerant": "default"},
        {
        "name": "res. frefr. 2 â€“ CAC/rest. to HP, typ. GWP + phase outs",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": 3,
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": {
            "cooling": 0.5,
            "heating": 1},
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": ["electricity"],
        "fuel_switch_to": None,
        "tech_switch_to": "ASHP",
        "end_use": ["heating", "cooling"],
        "technology": ["resistance heat", "central AC"]},
        {
        "name": "res. frefr. 3 â€“ NGWH to HPWH, typ. GWP + phase outs",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": 3,
        "energy_efficiency_units": "UEF",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": ["natural gas"],
        "fuel_switch_to": "electricity",
        "tech_switch_to": "HPWH",
        "end_use": ["water heating"],
        "technology": None},
        {
        "name": "res. frefr. 4 â€“ rest. to HPWH, low GWP",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": 3,
        "energy_efficiency_units": "UEF",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": ["electricity"],
        "fuel_switch_to": None,
        "tech_switch_to": "HPWH",
        "end_use": ["water heating"],
        "technology": "electric WH",
        "low_gwp_refrigerant": "R-1234yf"},
        {
        "name": "res. frefr. 5 â€“ low GWP CAC",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": 3,
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": ["electricity"],
        "fuel_switch_to": None,
        "tech_switch_to": None,
        "end_use": ["cooling"],
        "technology": ["central AC"],
        "low_gwp_refrigerant": "R-1234yf"},
        {
        "name": "com. frefr. 1 â€“ RTU/NG to HP, typ. GWP + phase outs",
        "installed_cost": 100,
        "cost_units": "2009$/kBtu/h cooling",
        "energy_efficiency": 3,
        "energy_efficiency_units": "BTU out/BTU in",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "large office",
        "climate_zone": "TRE",
        "fuel_type": ["electricity", "natural gas"],
        "fuel_switch_to": "electricity",
        "tech_switch_to": "ASHP",
        "end_use": ["cooling", "heating"],
        "technology": ["rooftop_AC", "gas_furnace"]},
        {
        "name": "com. frefr. 2 â€“ RTU/rest. to HP, low GWP",
        "installed_cost": 100,
        "cost_units": "2009$/kBtu/h cooling",
        "energy_efficiency": 3,
        "energy_efficiency_units": "BTU out/BTU in",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "large office",
        "climate_zone": "TRE",
        "fuel_type": ["electricity"],
        "fuel_switch_to": None,
        "tech_switch_to": "ASHP",
        "end_use": ["cooling", "heating"],
        "technology": ["rooftop_AC", "electric_res-heat"],
        "low_gwp_refrigerant": "R-1234yf"},
        {
        "name": "com. frefr. 3 â€“ low GWP refrigeration",
        "installed_cost": 100,
        "cost_units": "2009$/kBtu/h refrigeration",
        "energy_efficiency": 3,
        "energy_efficiency_units": "BTU out/BTU in",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "large office",
        "climate_zone": "TRE",
        "fuel_type": ["electricity"],
        "fuel_switch_to": None,
        "tech_switch_to": None,
        "end_use": ["refrigeration"],
        "technology": ["Commercial Ice Machines"],
        "low_gwp_refrigerant": {
            "2009": "R-454C", "2010": "R-1234yf"}},
        {
        "name": "res. frefr. 1a â€“ CAC/NG to HP, low GWP, no exog. rates",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": 3,
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": {
            "cooling": 0.5,
            "heating": 1},
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": ["electricity", "natural gas"],
        "fuel_switch_to": "electricity",
        "tech_switch_to": "ASHP",
        "end_use": ["heating", "cooling"],
        "technology": ["furnace (NG)", "central AC"],
        "low_gwp_refrigerant": "default"},
        {
        "name": "res. frefr. 1b â€“ CAC/NG to HP, low GWP + no phase outs",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": 3,
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": {
            "cooling": 0.5,
            "heating": 1},
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": ["electricity", "natural gas"],
        "fuel_switch_to": "electricity",
        "tech_switch_to": "ASHP",
        "end_use": ["heating", "cooling"],
        "technology": ["furnace (NG)", "central AC"],
        "low_gwp_refrigerant": "default"}]
    # Fugitive emissions for refrigerant leakage
    opts_frefr, opts_frefr_dict = [[
        copy.deepcopy(n) for x in range(len(ok_frefr_measures_in))]
        for n in [opts_emm, opts_emm_dict]]
    # Initialize measure-specific handy vars
    handyvars_frefr = [None for x in range(len(ok_frefr_measures_in))]
    # Initialize measure-specific low GWP settings
    low_gwp_settings = [
        ['2', '3'], ['2', '2'], ['2', '2'], ['2', '3'],
        ['2', '3'], ['2', '2'], ['2', '3'], ['2', '3'],
        ['2', '3'], ['2', '1', '3']]
    # Initialize measure-specific exogenous HP rate settings
    exog_hp_rates_settings = [
        ["gh-aggressive", '1'] for n in (
            range(len(ok_frefr_measures_in) - 2))] + [False] + [False]
    # Sample exogenous HP switching rates to use in fugitive
    # refrigerant emissions calculations; for simplicity, set rates to 1
    frefr_hp_rates = {
        "data (by scenario)": {
            "gh-aggressive": {
                "south": {
                    "residential": {
                        "electricity": {
                            "heating": {
                                "resistance heat": {
                                    "existing": {
                                        "2009": 1,
                                        "2010": 1
                                    },
                                    "new": {
                                        "2009": 1,
                                        "2010": 1
                                    }
                                }
                            },
                            "water heating": {
                                "all": {
                                    "existing": {
                                        "2009": 1,
                                        "2010": 1
                                    },
                                    "new": {
                                        "2009": 1,
                                        "2010": 1
                                    }
                                }
                            }
                        },
                        "natural gas": {
                            "heating": {
                                "furnace (NG)": {
                                    "existing": {
                                        "2009": 1,
                                        "2010": 1
                                    },
                                    "new": {
                                        "2009": 1,
                                        "2010": 1
                                    }
                                }
                            },
                            "water heating": {
                                "all": {
                                    "existing": {
                                        "2009": 1,
                                        "2010": 1
                                    },
                                    "new": {
                                        "2009": 1,
                                        "2010": 1
                                    }
                                }
                            }
                        }
                    },
                    "commercial": {
                        "electricity": {
                            "heating": {
                                "RTUs": {
                                    "existing": {
                                        "2009": 1,
                                        "2010": 1
                                    },
                                    "new": {
                                        "2009": 1,
                                        "2010": 1
                                    }
                                }
                            }
                        },
                        "natural gas": {
                            "heating": {
                                "RTUs": {
                                    "existing": {
                                        "2009": 1,
                                        "2010": 1
                                    },
                                    "new": {
                                        "2009": 1,
                                        "2010": 1
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    # Loop through refrigerant emissions measures and hard code user
    # settings and handy vars
    for x in range(len(ok_frefr_measures_in)):
        # Measure-specific user options
        opts_frefr[x].adopt_scn_restrict, opts_frefr_dict[x][
            "adopt_scn_restrict"] = (
            ["Max adoption potential"] for n in range(2))
        opts_frefr[x].fugitive_emissions, opts_frefr_dict[x][
            "fugitive_emissions"] = (
                low_gwp_settings[x] for n in range(2))
        opts_frefr[x].exog_hp_rates, opts_frefr_dict[x][
            "exog_hp_rates"] = (
                exog_hp_rates_settings[x] for n in range(2))
        # Measure-specific handy vars
        handyvars_frefr[x] = UsefulVars(
            base_dir, handyfiles_emm, opts_frefr[x])
        # Reset exogenous HP rate settings to test vals where applicable
        if handyvars_frefr[x].hp_rates is not None:
            handyvars_frefr[x].hp_rates = frefr_hp_rates
    # Hard code sample fugitive refrigerant emissions input data
    frefr_fug_emissions = {
       "methane": {},
       "refrigerants": {
            "refrigerant_data_by_tech_type": {
                "commercial": {
                    "rooftop_ASHP-cool": {
                        "typ_refrigerant": {
                            "2009": "R-410A", "2010": "R-32"},
                        "low_gwp_refrigerant": "R-32",
                        "typ_charge": 1.571111111,
                        "typ_ann_leak_pct": 0.05,
                        "EOL_leak_pct": 0.15,
                        "References": ""
                    },
                    "rooftop_AC": {
                        "typ_refrigerant": {
                            "2009": "R-410A", "2010": "R-32"},
                        "low_gwp_refrigerant": "R-32",
                        "typ_charge": 1.571111111,
                        "typ_ann_leak_pct": 0.05,
                        "EOL_leak_pct": 0.15,
                        "References": ""
                    },
                    "Centralized refrigeration": {
                        "typ_refrigerant": {
                            "2009": "R-404A", "2010": "R-454C"},
                        "low_gwp_refrigerant": "R-454C",
                        "typ_charge": 1.78412132,
                        "typ_ann_leak_pct": 0.225,
                        "EOL_leak_pct": 0.15,
                        "References": ""
                    },
                    "Commercial Walk-In Freezers": {
                        "typ_refrigerant": {
                            "2009": "R-404A", "2010": "R-454C"},
                        "low_gwp_refrigerant": "R-454C",
                        "typ_charge": 1.78412132,
                        "typ_ann_leak_pct": 0.225,
                        "EOL_leak_pct": 0.15,
                        "References": ""
                    },
                    "Commercial Walk-In Refrigerators": {
                        "typ_refrigerant": {
                            "2009": "R-404A", "2010": "R-454C"},
                        "low_gwp_refrigerant": "R-454C",
                        "typ_charge": 1.78412132,
                        "typ_ann_leak_pct": 0.225,
                        "EOL_leak_pct": 0.15,
                        "References": ""
                    },
                    "Commercial Reach-In Refrigerators": {
                        "typ_refrigerant": {
                            "2009": "R-404A", "2010": "R-454C"},
                        "low_gwp_refrigerant": "R-454C",
                        "typ_charge": 1.78412132,
                        "typ_ann_leak_pct": 0.225,
                        "EOL_leak_pct": 0.15,
                        "References": ""
                    },
                    "Commercial Reach-In Freezers": {
                        "typ_refrigerant": {
                            "2009": "R-404A", "2010": "R-454C"},
                        "low_gwp_refrigerant": "R-454C",
                        "typ_charge": 1.78412132,
                        "typ_ann_leak_pct": 0.225,
                        "EOL_leak_pct": 0.15,
                        "References": ""
                    },
                    "Commercial Ice Machines": {
                        "typ_refrigerant": {
                            "2009": "R-404A", "2010": "R-454C"},
                        "low_gwp_refrigerant": "R-454C",
                        "typ_charge": 1.78412132,
                        "typ_ann_leak_pct": 0.225,
                        "EOL_leak_pct": 0.15,
                        "References": ""
                    },
                    "Commercial Beverage Merchandisers": {
                        "typ_refrigerant": {
                            "2009": "R-404A", "2010": "R-454C"},
                        "low_gwp_refrigerant": "R-454C",
                        "typ_charge": 1.78412132,
                        "typ_ann_leak_pct": 0.225,
                        "EOL_leak_pct": 0.15,
                        "References": ""
                    },
                    "Commercial Refrigerated Vending Machines": {
                        "typ_refrigerant": {
                            "2009": "R-404A", "2010": "R-454C"},
                        "low_gwp_refrigerant": "R-454C",
                        "typ_charge": 1.78412132,
                        "typ_ann_leak_pct": 0.225,
                        "EOL_leak_pct": 0.15,
                        "References": ""
                    }
                },
                "residential": {
                    "ASHP": {
                       "typ_refrigerant": {
                            "2009": "R-410A", "2010": "R-32"},
                       "low_gwp_refrigerant": "R-32",
                       "typ_charge": 3.59,
                       "typ_ann_leak_pct": 0.058,
                       "EOL_leak_pct": 0.15,
                       "References": ""
                    },
                    "central AC": {
                       "typ_refrigerant": {
                            "2009": "R-410A", "2010": "R-32"},
                       "low_gwp_refrigerant": "R-32",
                       "typ_charge": 2.95,
                       "typ_ann_leak_pct": 0.058,
                       "EOL_leak_pct": 0.15,
                       "References": ""
                    },
                    "HPWH": {
                       "typ_refrigerant": {
                            "2009": "R-134a", "2010": "R-1234yf"},
                       "low_gwp_refrigerant": "R-1234yf",
                       "typ_charge": 4.7,
                       "typ_ann_leak_pct": 0.02,
                       "EOL_leak_pct": 0.15,
                       "References": ""
                    },
                }
            },
            "refrigerant_GWP100": {
                "R-410A": 2088.0,
                "R-32": 675.0,
                "R-404A": 3900.0,
                "R-454C": 148.0,
                "R-1234ze": 1.0,
                "R-1234yf": 1.0,
                "R-134a": 1430.0
            },
       }
    }
    for x in range(len(ok_frefr_measures_in)):
        handyvars_frefr[x].fug_emissions = frefr_fug_emissions
    # Hard code aeo_years to fit test years
    handyvars.aeo_years, handyvars_emm.aeo_years, \
        handyvars_state.aeo_years, \
        handyvars_hp_rates.aeo_years, handyvars_hp_norates.aeo_years, \
        fmeth_aeo_years, frefr_aeo_years = (
            ["2009", "2010"] for n in range(7))
    for x in range(len(ok_fmeth_measures_in)):
        handyvars_fmeth[x].aeo_years = fmeth_aeo_years
    for x in range(len(ok_frefr_measures_in)):
        handyvars_frefr[x].aeo_years = frefr_aeo_years
    handyvars.retro_rate = {yr: 0.02 for yr in handyvars.aeo_years}
    handyvars_emm.retro_rate, handyvars_state.retro_rate, \
        handyvars_hp_rates.retro_rate, handyvars_hp_norates.retro_rate, \
        fmeth_retro_rate, frefr_retro_rate = (
            {yr: 0.01 for yr in handyvars.aeo_years} for n in range(6))
    for x in range(len(ok_fmeth_measures_in)):
        handyvars_fmeth[x].retro_rate = fmeth_retro_rate
    for x in range(len(ok_frefr_measures_in)):
        handyvars_frefr[x].retro_rate = frefr_retro_rate
    # Set dummy commercial equipment capacity factors
    cf_ones = {
        "data": {
            "assembly": {
                "heating": 1,
                "cooling": 1,
                "water heating": 1,
                "ventilation": 1,
                "cooking": 1,
                "lighting": 1,
                "refrigeration": 1
            },
            "large office": {
                "heating": 1,
                "cooling": 1,
                "water heating": 1,
                "ventilation": 1,
                "cooking": 1,
                "lighting": 1,
                "refrigeration": 1
            }
        }
    }
    # Set test capacity factors to dummy values above
    handyvars.cap_facts, handyvars_emm.cap_facts, \
        handyvars_state.cap_facts, handyvars_hp_rates.cap_facts, \
        handyvars_hp_norates.cap_facts, \
        fmeth_cap_facts, frefr_cap_facts = (
            cf_ones for n in range(7))
    for x in range(len(ok_fmeth_measures_in)):
        handyvars_fmeth[x].cap_facts = fmeth_cap_facts
    for x in range(len(ok_frefr_measures_in)):
        handyvars_frefr[x].cap_facts = frefr_cap_facts
    # Hard code carbon intensity, site-source conversion, and cost data for
    # tests such that these data are not dependent on an input file that
    # may change in the future
    handyvars.ss_conv = {
        "electricity": {"2009": 3.19, "2010": 3.20},
        "natural gas": {"2009": 1.01, "2010": 1.01},
        "distillate": {"2009": 1.01, "2010": 1.01},
        "other fuel": {"2009": 1.01, "2010": 1.01}}
    handyvars.carb_int = {
        "residential": {
            "electricity": {"2009": 56.84702689, "2010": 56.16823191},
            "natural gas": {"2009": 56.51576602, "2010": 54.91762852},
            "distillate": {"2009": 49.5454521, "2010": 52.59751597},
            "other fuel": {"2009": 49.5454521, "2010": 52.59751597}},
        "commercial": {
            "electricity": {"2009": 56.84702689, "2010": 56.16823191},
            "natural gas": {"2009": 56.51576602, "2010": 54.91762852},
            "distillate": {"2009": 49.5454521, "2010": 52.59751597},
            "other fuel": {"2009": 49.5454521, "2010": 52.59751597}}}
    handyvars.ecosts = {
        "residential": {
            "electricity": {"2009": 10.14, "2010": 9.67},
            "natural gas": {"2009": 11.28, "2010": 10.78},
            "distillate": {"2009": 21.23, "2010": 20.59},
            "other fuel": {"2009": 21.23, "2010": 20.59}},
        "commercial": {
            "electricity": {"2009": 9.08, "2010": 8.55},
            "natural gas": {"2009": 8.96, "2010": 8.59},
            "distillate": {"2009": 14.81, "2010": 14.87},
            "other fuel": {"2009": 14.81, "2010": 14.87}}}
    # Hard code carbon intensity, site-source conversion, and cost data
    # for tests of regional-level (EMM) analysis.
    handyvars_emm.regions, handyvars_hp_rates.regions, \
        handyvars_hp_norates.regions, \
        fmeth_regions, frefr_regions = (
            "EMM" for n in range(5))
    for x in range(len(ok_fmeth_measures_in)):
        handyvars_fmeth[x].regions = fmeth_regions
    for x in range(len(ok_frefr_measures_in)):
        handyvars_frefr[x].regions = frefr_regions
    handyvars_state.regions = "State"
    handyvars_emm.ss_conv, handyvars_state.ss_conv, \
        handyvars_hp_rates.ss_conv, handyvars_hp_norates.ss_conv, \
        fmeth_ss_conv, frefr_ss_conv = ({
            "electricity": {"2009": 2.917505, "2010": 2.889269},
            "natural gas": {"2009": 1.01, "2010": 1.01},
            "distillate": {"2009": 1.01, "2010": 1.01},
            "other fuel": {"2009": 1.01, "2010": 1.01}} for n in range(6))
    for x in range(len(ok_fmeth_measures_in)):
        handyvars_fmeth[x].ss_conv = fmeth_ss_conv
    for x in range(len(ok_frefr_measures_in)):
        handyvars_frefr[x].ss_conv = frefr_ss_conv
    handyvars_emm.carb_int, handyvars_hp_rates.carb_int, \
        handyvars_hp_rates.carb_int, handyvars_hp_norates.carb_int, \
        fmeth_carb_int, frefr_carb_int = ({
            "residential": {
                "electricity": {
                    'BASN': {"2009": 1.988e-07, "2010": 1.931e-07},
                    'CANO': {"2009": 4.73e-08, "2010": 3.82e-08},
                    'CASO': {"2009": 3.15e-08, "2010": 2.37e-08},
                    'FRCC': {"2009": 1.211e-07, "2010": 1.2e-07},
                    'ISNE': {"2009": 5.23e-08, "2010": 4.04e-08},
                    'MISC': {"2009": 2.398e-07, "2010": 2.1e-07},
                    'MISE': {"2009": 1.581e-07, "2010": 1.541e-07},
                    'MISS': {"2009": 1.274e-07, "2010": 1.291e-07},
                    'MISW': {"2009": 1.479e-07, "2010": 1.399e-07},
                    'NWPP': {"2009": 4.17e-08, "2010": 4.63e-08},
                    'NYCW': {"2009": 5.52e-08, "2010": 6.75e-08},
                    'NYUP': {"2009": 5.61e-08, "2010": 5.21e-08},
                    'PJMC': {"2009": 1.78e-08, "2010": 1.38e-08},
                    'PJMD': {"2009": 9.89e-08, "2010": 9.6e-08},
                    'PJME': {"2009": 1.254e-07, "2010": 1.162e-07},
                    'PJMW': {"2009": 1.766e-07, "2010": 1.76e-07},
                    'RMRG': {"2009": 2.221e-07, "2010": 2.154e-07},
                    'SPPC': {"2009": 1.852e-07, "2010": 1.888e-07},
                    'SPPN': {"2009": 1.594e-07, "2010": 1.392e-07},
                    'SPPS': {"2009": 1.543e-07, "2010": 1.516e-07},
                    'SRCA': {"2009": 7.72e-08, "2010": 7.16e-08},
                    'SRCE': {"2009": 1.323e-07, "2010": 1.3e-07},
                    'SRSE': {"2009": 1.583e-07, "2010": 1.473e-07},
                    'SRSG': {"2009": 1.51e-07, "2010": 1.264e-07},
                    'TRE': {"2009": 1.306e-07, "2010": 1.199e-07}},
                "natural gas": {"2009": 56.51576602, "2010": 54.91762852},
                "distillate": {"2009": 49.5454521, "2010": 52.59751597},
                "other fuel": {"2009": 49.5454521, "2010": 52.59751597}},
            "commercial": {
                "electricity": {
                    'BASN': {"2009": 1.988e-07, "2010": 1.931e-07},
                    'CANO': {"2009": 4.73e-08, "2010": 3.82e-08},
                    'CASO': {"2009": 3.15e-08, "2010": 2.37e-08},
                    'FRCC': {"2009": 1.211e-07, "2010": 1.2e-07},
                    'ISNE': {"2009": 5.23e-08, "2010": 4.04e-08},
                    'MISC': {"2009": 2.398e-07, "2010": 2.1e-07},
                    'MISE': {"2009": 1.581e-07, "2010": 1.541e-07},
                    'MISS': {"2009": 1.274e-07, "2010": 1.291e-07},
                    'MISW': {"2009": 1.479e-07, "2010": 1.399e-07},
                    'NWPP': {"2009": 4.17e-08, "2010": 4.63e-08},
                    'NYCW': {"2009": 5.52e-08, "2010": 6.75e-08},
                    'NYUP': {"2009": 5.61e-08, "2010": 5.21e-08},
                    'PJMC': {"2009": 1.78e-08, "2010": 1.38e-08},
                    'PJMD': {"2009": 9.89e-08, "2010": 9.6e-08},
                    'PJME': {"2009": 1.254e-07, "2010": 1.162e-07},
                    'PJMW': {"2009": 1.766e-07, "2010": 1.76e-07},
                    'RMRG': {"2009": 2.221e-07, "2010": 2.154e-07},
                    'SPPC': {"2009": 1.852e-07, "2010": 1.888e-07},
                    'SPPN': {"2009": 1.594e-07, "2010": 1.392e-07},
                    'SPPS': {"2009": 1.543e-07, "2010": 1.516e-07},
                    'SRCA': {"2009": 7.72e-08, "2010": 7.16e-08},
                    'SRCE': {"2009": 1.323e-07, "2010": 1.3e-07},
                    'SRSE': {"2009": 1.583e-07, "2010": 1.473e-07},
                    'SRSG': {"2009": 1.51e-07, "2010": 1.264e-07},
                    'TRE': {"2009": 1.306e-07, "2010": 1.199e-07}},
                "natural gas": {"2009": 56.51576602, "2010": 54.91762852},
                "distillate": {"2009": 49.5454521, "2010": 52.59751597},
                "other fuel": {"2009": 49.5454521, "2010": 52.59751597}}}
            for n in range(6))
    for x in range(len(ok_fmeth_measures_in)):
        handyvars_fmeth[x].carb_int = fmeth_carb_int
    for x in range(len(ok_frefr_measures_in)):
        handyvars_frefr[x].carb_int = frefr_carb_int
    handyvars_state.carb_int = {
        "residential": {
            "electricity": {
                'NH': {"2009": 3.15e-08, "2010": 2.37e-08},
                'CT': {"2009": 1.306e-07, "2010": 1.199e-07}},
            "natural gas": {"2009": 56.51576602, "2010": 54.91762852},
            "distillate": {"2009": 49.5454521, "2010": 52.59751597},
            "other fuel": {"2009": 49.5454521, "2010": 52.59751597}},
        "commercial": {
            "electricity": {
                'NH': {"2009": 3.15e-08, "2010": 2.37e-08},
                'CT': {"2009": 1.306e-07, "2010": 1.199e-07}},
            "natural gas": {"2009": 56.51576602, "2010": 54.91762852},
            "distillate": {"2009": 49.5454521, "2010": 52.59751597},
            "other fuel": {"2009": 49.5454521, "2010": 52.59751597}}}
    handyvars_emm.ecosts, handyvars_hp_rates.ecosts, \
        handyvars_hp_norates.ecosts, \
        fmeth_ecosts, frefr_ecosts = ({
            'residential': {
                "electricity": {
                    'BASN': {"2009": 32.41061, "2010": 33.817116},
                    'CANO': {"2009": 51.889215, "2010": 53.32034},
                    'CASO': {"2009": 57.729191, "2010": 60.453107},
                    'FRCC': {"2009": 33.395662, "2010": 32.073857},
                    'ISNE': {"2009": 57.175264, "2010": 55.654455},
                    'MISC': {"2009": 34.407679, "2010": 34.083529},
                    'MISE': {"2009": 46.220399, "2010": 45.131008},
                    'MISS': {"2009": 29.299531, "2010": 29.881594},
                    'MISW': {"2009": 38.494138, "2010": 38.640973},
                    'NWPP': {"2009": 26.405041, "2010": 27.175557},
                    'NYCW': {"2009": 77.19109, "2010": 76.021395},
                    'NYUP': {"2009": 40.442849, "2010": 39.199004},
                    'PJMC': {"2009": 37.823271, "2010": 37.899179},
                    'PJMD': {"2009": 29.718347, "2010": 27.902403},
                    'PJME': {"2009": 38.412661, "2010": 37.882181},
                    'PJMW': {"2009": 38.84027, "2010": 37.778136},
                    'RMRG': {"2009": 34.469812, "2010": 34.946952},
                    'SPPC': {"2009": 37.525205, "2010": 37.458675},
                    'SPPN': {"2009": 23.564478, "2010": 24.509379},
                    'SPPS': {"2009": 30.656506, "2010": 31.779015},
                    'SRCA': {"2009": 35.767585, "2010": 34.664127},
                    'SRCE': {"2009": 28.760844, "2010": 28.805686},
                    'SRSE': {"2009": 36.077667, "2010": 35.147128},
                    'SRSG': {"2009": 33.641559, "2010": 33.728898},
                    'TRE':  {"2009": 29.823857, "2010": 26.964537}},
                "natural gas": {"2009": 11.28, "2010": 10.78},
                "distillate": {"2009": 21.23, "2010": 20.59},
                "other fuel": {"2009": 21.23, "2010": 20.59}},
            'commercial': {
                "electricity": {
                    'BASN': {"2009": 25.014361, "2010": 24.92585},
                    'CANO': {"2009": 44.822392, "2010": 44.769343},
                    'CASO': {"2009": 51.503224, "2010": 52.344666},
                    'FRCC': {"2009": 26.159437, "2010": 25.639801},
                    'ISNE': {"2009": 48.544256, "2010": 47.556565},
                    'MISC': {"2009": 29.080891, "2010": 28.568875},
                    'MISE': {"2009": 32.957796, "2010": 32.324443},
                    'MISS': {"2009": 25.02374, "2010": 26.0},
                    'MISW': {"2009": 31.281067, "2010": 31.424091},
                    'NWPP': {"2009": 23.485346, "2010": 23.3432},
                    'NYCW': {"2009": 39.490035, "2010": 37.8517},
                    'NYUP': {"2009": 31.326495, "2010": 29.708089},
                    'PJMC': {"2009": 25.354924, "2010": 24.921747},
                    'PJMD': {"2009": 20.256155, "2010": 19.120164},
                    'PJME': {"2009": 29.182298, "2010": 28.130129},
                    'PJMW': {"2009": 31.539859, "2010": 30.44871},
                    'RMRG': {"2009": 29.485053, "2010": 28.664127},
                    'SPPC': {"2009": 30.472743, "2010": 30.504689},
                    'SPPN': {"2009": 20.518464, "2010": 21.192263},
                    'SPPS': {"2009": 23.531946, "2010": 24.911196},
                    'SRCA': {"2009": 27.798066, "2010": 27.446073},
                    'SRCE': {"2009": 28.048066, "2010": 28.53898},
                    'SRSE': {"2009": 30.667937, "2010": 30.463365},
                    'SRSG': {"2009": 28.156506, "2010": 27.199297},
                    'TRE': {"2009": 27.985639, "2010": 24.313013}},
                "natural gas": {"2009": 11.28, "2010": 10.78},
                "distillate": {"2009": 21.23, "2010": 20.59},
                "other fuel": {"2009": 21.23, "2010": 20.59}}}
            for n in range(5))
    for x in range(len(ok_fmeth_measures_in)):
        handyvars_fmeth[x].ecosts = fmeth_ecosts
    for x in range(len(ok_frefr_measures_in)):
        handyvars_frefr[x].ecosts = frefr_ecosts
    handyvars_state.ecosts = {
        'residential': {
            "electricity": {
                'NH': {"2009": 57.729191, "2010": 60.453107},
                'CT':  {"2009": 29.823857, "2010": 26.964537}},
            "natural gas": {"2009": 11.28, "2010": 10.78},
            "distillate": {"2009": 21.23, "2010": 20.59},
            "other fuel": {"2009": 21.23, "2010": 20.59}},
        'commercial': {
            "electricity": {
                'NH': {"2009": 51.503224, "2010": 52.344666},
                'CT': {"2009": 27.985639, "2010": 24.313013}},
            "natural gas": {"2009": 11.28, "2010": 10.78},
            "distillate": {"2009": 21.23, "2010": 20.59},
            "other fuel": {"2009": 21.23, "2010": 20.59}}}
    handyvars.ccosts = {"2009": 33, "2010": 33}
    handyvars_emm.ccosts, handyvars_state.ccosts, \
        handyvars_hp_rates.ccosts, handyvars_hp_norates.ccosts, \
        fmeth_ccosts, frefr_ccosts = (
            {"2009": 41, "2010": 42} for n in range(6))
    for x in range(len(ok_fmeth_measures_in)):
        handyvars_fmeth[x].ccosts = fmeth_ccosts
    for x in range(len(ok_frefr_measures_in)):
        handyvars_frefr[x].ccosts = frefr_ccosts

    # Zero out electrical infrastructure costs for now in tests
    handyvars.elec_infr_costs, handyvars_emm.elec_infr_costs, handyvars_state.elec_infr_costs, \
        handyvars_hp_rates.elec_infr_costs, handyvars_hp_norates.elec_infr_costs, \
        fmeth_elec_infr_costs, frefr_elec_infr_costs = ({
            "panel replacement": 0,
            "panel management": 0,  # BENEFIT panels cost data, averaged across regions
            "240V circuit": 0  # BTB "typical" dif., central ASHP w/ and w/o new circuit
        } for n in range(7))
    for x in range(len(ok_fmeth_measures_in)):
        handyvars_fmeth[x].elec_infr_costs = fmeth_elec_infr_costs
    for x in range(len(ok_frefr_measures_in)):
        handyvars_frefr[x].elec_infr_costs = frefr_elec_infr_costs
    # Hard code mapping array used to handle alternate regional breakouts
    # of measure performance or cost (e.g., IECC)
    handyvars.alt_attr_brk_map = {
        "IECC": numpy.array([
            (b"IECC_CZ1", 0, 0, 0.125, 0.125, 0.125),
            (b"IECC_CZ2", 0, 0.5, 0.125, 0.125, 0.125),
            (b"IECC_CZ3", 0.25, 0, 0.125, 0.125, 0.125),
            (b"IECC_CZ4", 0.75, 0, 0.125, 0.125, 0.125),
            (b"IECC_CZ5", 0, 0.5, 0.125, 0.125, 0.125),
            (b"IECC_CZ6", 0, 0, 0.125, 0.125, 0.125),
            (b"IECC_CZ7", 0, 0, 0.125, 0.125, 0.125),
            (b"IECC_CZ8", 0, 0, 0.125, 0.125, 0.125)], dtype=[
            ("IECC", "<U25"), ("AIA_CZ1", "<f8"),
            ("AIA_CZ2", "<f8"), ("AIA_CZ3", "<f8"),
            ("AIA_CZ4", "<f8"), ("AIA_CZ5", "<f8")]),
        "levels": str([
            "IECC_CZ" + str(n + 1) for n in range(8)])
    }
    # Note that in practice these coefficients are defined separately for each end use;
    # set to same coefficient values for convenience in testing
    handyvars.deflt_res_choice = {
        "electric": {
            x: [-0.01, -0.12] for x in [
                "heating", "secondary heating", "cooling", "water heating", "cooking",
                "drying", "lighting", "refrigeration", "ceiling fan", "fans and pumps",
                "computers", "TVs", "other"]},
        "non-electric": {
            x: [-0.01, -0.12] for x in [
                "heating", "secondary heating", "cooling", "water heating", "cooking",
                "drying"]}
    }
    convert_data = {}
    tsv_data = {}
    ok_measures_in = [{
        "name": "sample measure 1",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "AIA_CZ1": {"heating": 30,
                        "cooling": 25},
            "AIA_CZ2": {"heating": 30,
                        "cooling": 15}},
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["heating", "cooling"],
        "technology": ["resistance heat", "ASHP", "GSHP", "room AC"],
        "htcl_tech_link": "resistance+hpac"},
        {
        "name": "sample measure 2",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {"new": 25, "existing": 25},
        "energy_efficiency_units": "EF",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ1"],
        "fuel_type": "natural gas",
        "fuel_switch_to": None,
        "end_use": "water heating",
        "technology": None},
        {
        "name": "sample measure 3",
        "markets": None,
        "installed_cost": 500,
        "cost_units": {
            "refrigeration": "2010$/unit",
            "other": "2014$/unit"},
        "energy_efficiency": 0.1,
        "energy_efficiency_units": "relative savings (constant)",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "AIA_CZ1",
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["refrigeration", "other"],
        "technology": [None, "freezers"]},
        {
        "name": "sample measure 4",
        "markets": None,
        "installed_cost": 10,
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": {
            "windows conduction": 20,
            "windows solar": 1},
        "energy_efficiency_units": {
            "windows conduction": "R Value",
            "windows solar": "SHGC"},
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": "existing",
        "bldg_type": ["single family home",
                      "multi family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "heating",
        "technology": [
            "windows conduction",
            "windows solar"]},
        {
        "name": "sample measure 5",
        "markets": None,
        "installed_cost": 10,
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": 0.1,
        "energy_efficiency_units": "relative savings (constant)",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "add-on",
        "structure_type": "existing",
        "bldg_type": ["single family home",
                      "multi family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "lighting",
        "technology": "linear fluorescent (LED)"},
        {
        "name": "sample measure 6",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "primary": 25,
            "secondary": {
                "heating": 0.4,
                "secondary heating": 0.4,
                "cooling": -0.4}},
        "energy_efficiency_units": {
            "primary": "lm/W",
            "secondary": "relative savings (constant)"},
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": ["single family home",
                      "multi family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": {
            "primary": "lighting",
            "secondary": [
                "heating", "secondary heating",
                "cooling"]},
        "technology": [
            "linear fluorescent (LED)",
            "general service (LED)",
            "external (LED)"]},
        {
        "name": "sample measure 7",
        "markets": None,
        "installed_cost": 10,
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": {
            "windows conduction": 20,
            "windows solar": 1},
        "energy_efficiency_units": {
            "windows conduction": "R Value",
            "windows solar": "SHGC"},
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": ["single family home",
                      "multi family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "heating",
        "technology": [
            "windows conduction",
            "windows solar"]},
        {
        "name": "sample measure 8",
        "markets": None,
        "installed_cost": 10,
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": 1,
        "energy_efficiency_units": "SHGC",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "heating",
        "technology": "windows solar"},
        {
        "name": "sample measure 9",
        "markets": None,
        "installed_cost": 10,
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": {
            "windows conduction": 10, "windows solar": 1},
        "energy_efficiency_units": {
            "windows conduction": "R Value",
            "windows solar": "SHGC"},
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": [
            "heating", "secondary heating",
            "cooling"],
        "technology": [
            "windows conduction", "windows solar"]},
        {
        "name": "sample measure 10",
        "markets": None,
        "installed_cost": 10,
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": {
            "windows conduction": 0.4,
            "windows solar": 1},
        "energy_efficiency_units": {
            "windows conduction": "relative savings (constant)",
            "windows solar": "SHGC"},
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["heating", "secondary heating",
                    "cooling"],
        "technology": ["windows conduction",
                       "windows solar"]},
        {
        "name": "sample measure 11",  # Add heat/cool end uses later
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": 25,
        "energy_efficiency_units": "lm/W",
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "assembly",
        "climate_zone": "AIA_CZ1",
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "lighting",
        "market_entry_year": None,
        "market_exit_year": None,
        "technology": [
            "T5 F28"]},
        {
        "name": "sample measure 12",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": 25,
        "energy_efficiency_units": "EF",
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": "new",
        "bldg_type": "single family home",
        "climate_zone": "AIA_CZ1",
        "fuel_type": "natural gas",
        "fuel_switch_to": None,
        "end_use": "water heating",
        "market_entry_year": None,
        "market_exit_year": None,
        "technology": None},
        {
        "name": "sample measure 13",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": 25,
        "energy_efficiency_units": "EF",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": "existing",
        "bldg_type": "single family home",
        "climate_zone": "AIA_CZ1",
        "fuel_type": "natural gas",
        "fuel_switch_to": None,
        "end_use": "water heating",
        "technology": None},
        {
        "name": "sample measure 14",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "primary": 25,
            "secondary": {
                "heating": 0.4,
                "secondary heating": 0.4,
                "cooling": -0.4}},
        "energy_efficiency_units": {
            "primary": "lm/W",
            "secondary": "relative savings (constant)"},
        "market_entry_year": 2010,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": ["single family home",
                      "multi family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": {
            "primary": "lighting",
            "secondary": ["heating", "secondary heating",
                          "cooling"]},
        "technology": [
            "linear fluorescent (LED)",
            "general service (LED)",
            "external (LED)"]},
        {
        "name": "sample measure 15",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "primary": 25,
            "secondary": {
                "heating": 0.4,
                "secondary heating": 0.4,
                "cooling": -0.4}},
        "energy_efficiency_units": {
            "primary": "lm/W",
            "secondary": "relative savings (constant)"},
        "market_entry_year": None,
        "market_exit_year": 2010,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": ["single family home",
                      "multi family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": {
            "primary": "lighting",
            "secondary": ["heating", "secondary heating",
                          "cooling"]},
        "technology": [
            "linear fluorescent (LED)",
            "general service (LED)",
            "external (LED)"]},
        {
        "name": "sample measure 16",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "primary": 25,
            "secondary": {
                "heating": 0.4,
                "secondary heating": 0.4,
                "cooling": -0.4}},
        "energy_efficiency_units": {
            "primary": "lm/W",
            "secondary": [
                "relative savings (dynamic)", 2009]},
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": ["single family home",
                      "multi family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": {
            "primary": "lighting",
            "secondary": ["heating", "secondary heating",
                          "cooling"]},
        "technology": [
            "linear fluorescent (LED)",
            "general service (LED)",
            "external (LED)"]},
        {
        "name": "sample measure 17",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "new": 25, "existing": 25},
        "energy_efficiency_units": "EF",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ1"],
        "fuel_type": "natural gas",
        "fuel_switch_to": "electricity",
        "end_use": "water heating",
        "technology": None},
        {
        "name": "sample measure 18",
        "markets": None,
        "installed_cost": 11,
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": 0.44,
        "energy_efficiency_units":
            "relative savings (constant)",
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "add-on",
        "structure_type": ["new", "existing"],
        "bldg_type": "assembly",
        "climate_zone": "AIA_CZ1",
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "lighting",
        "market_entry_year": None,
        "market_exit_year": None,
        "technology": [
            "T5 F28"]},
        {
        "name": "sample measure 19",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "new": 25, "existing": 25},
        "energy_efficiency_units": "EF",
        "market_entry_year": None,
        "market_exit_year": None,
        "market_scaling_fractions": {
            "new": 0.25,
            "existing": 0.5},
        "market_scaling_fractions_source": {
            "new": {
                "title": 'Sample title 1',
                "author": 'Sample author 1',
                "organization": 'Sample org 1',
                "year": 'Sample year 1',
                "URL": ('http://www.eia.gov/consumption/'
                        'commercial/data/2012/'),
                "fraction_derivation": "Divide X by Y"},
            "existing": {
                "title": 'Sample title 1',
                "author": 'Sample author 1',
                "organization": 'Sample org 1',
                "year": 'Sample year 1',
                "URL": ('http://www.eia.gov/consumption/'
                        'commercial/data/2012/'),
                "fraction_derivation": "Divide X by Y"}},
        "product_lifetime": 1,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "AIA_CZ1",
        "fuel_type": "natural gas",
        "fuel_switch_to": None,
        "end_use": "water heating",
        "technology": None},
        {
        "name": "sample measure 20",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "primary": 25,
            "secondary": {
                "heating": 0.4,
                "secondary heating": 0.4,
                "cooling": -0.4}},
        "energy_efficiency_units": {
            "primary": "lm/W",
            "secondary": "relative savings (constant)"},
        "market_entry_year": None,
        "market_exit_year": None,
        "market_scaling_fractions": {
            "new": 0.25,
            "existing": 0.5},
        "market_scaling_fractions_source": {
            "new": {
                "title": 'Sample title 2',
                "author": 'Sample author 2',
                "organization": 'Sample org 2',
                "year": 'Sample year 2',
                "URL": ('http://www.eia.gov/consumption/'
                        'commercial/data/2012/'),
                "fraction_derivation": "Divide X by Y"},
            "existing": {
                "title": 'Sample title 2',
                "author": 'Sample author 2',
                "organization": 'Sample org 2',
                "year": 'Sample year 2',
                "URL": ('http://www.eia.gov/consumption/'
                        'residential/data/2009/'),
                "fraction_derivation": "Divide X by Y"}},
        "product_lifetime": 1,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": ["single family home",
                      "multi family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": {
            "primary": "lighting",
            "secondary": ["heating", "secondary heating",
                          "cooling"]},
        "technology": [
            "linear fluorescent (LED)",
            "general service (LED)",
            "external (LED)"]},
        {
        "name": "sample measure 21",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "$/ft^2 floor",
        "energy_efficiency": 0.25,
        "energy_efficiency_units": "relative savings (constant)",
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "add-on",
        "structure_type": ["new", "existing"],
        "bldg_type": "assembly",
        "climate_zone": "AIA_CZ1",
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["PCs", "MELs"],
        "market_entry_year": None,
        "market_exit_year": None,
        "technology": [None, "distribution transformers"]},
        {
        "name": "sample measure 22",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "$/unit",
        "energy_efficiency": 0.5,
        "energy_efficiency_units": "relative savings (constant)",
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "add-on",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["TVs", "computers", "other"],
        "market_entry_year": None,
        "market_exit_year": None,
        "technology": ["TVs", "desktop PC", "laptop PC", "electric other"]
        },
        {
        "name": "sample measure 23",
        "markets": None,
        "installed_cost": 10,
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": {
            "IECC_CZ1": {
                "windows conduction": 20,
                "windows solar": 1},
            "IECC_CZ2": {
                "windows conduction": 20,
                "windows solar": 1},
            "IECC_CZ3": {
                "windows conduction": 10,
                "windows solar": 1},
            "IECC_CZ4": {
                "windows conduction": 23.33333,
                "windows solar": 1},
            "IECC_CZ5": {
                "windows conduction": 20,
                "windows solar": 1},
            "IECC_CZ6": {
                "windows conduction": 20,
                "windows solar": 1},
            "IECC_CZ7": {
                "windows conduction": 20,
                "windows solar": 1},
            "IECC_CZ8": {
                "windows conduction": 20,
                "windows solar": 1}},
        "energy_efficiency_units": {
            "windows conduction": "R Value",
            "windows solar": "SHGC"},
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": ["single family home",
                      "multi family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "heating",
        "technology": [
            "windows conduction",
            "windows solar"]},
        {
        "name": "sample measure 24",  # Add heat/cool end uses later
        "markets": None,
        "installed_cost": {
            "IECC_CZ1": 25,
            "IECC_CZ2": 25,
            "IECC_CZ3": 25,
            "IECC_CZ4": 25,
            "IECC_CZ5": 25,
            "IECC_CZ6": 25,
            "IECC_CZ7": 25,
            "IECC_CZ8": 25},
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": 25,
        "energy_efficiency_units": "lm/W",
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "assembly",
        "climate_zone": "AIA_CZ1",
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "lighting",
        "market_entry_year": None,
        "market_exit_year": None,
        "technology": [
            "T5 F28"]},
        {
        "name": "sample measure 25",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": 25,
        "energy_efficiency_units": "lm/W",
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "assembly",
        "climate_zone": "AIA_CZ1",
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "lighting",
        "market_entry_year": None,
        "market_exit_year": None,
        "technology": "T5 F28"},
        {
        "name": "sample measure 26",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": 25,
        "energy_efficiency_units": "lm/W",
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "assembly",
        "climate_zone": "AIA_CZ1",
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "lighting",
        "market_entry_year": None,
        "market_exit_year": None,
        "technology": "T5 F28",
        "retro_rate": 0.02
        },
        {
        "name": "sample measure 27",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2009$/unit",
        "energy_efficiency": 0.5,
        "energy_efficiency_units": "relative savings (constant)",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": "all",
        "bldg_type": "single family home",
        "climate_zone": ["TRE", "CASO"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "cooling",
        "technology": "ASHP"},
        {
        "name": "sample measure 27 - COP units",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2009$/unit",
        "energy_efficiency": 24,
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": "all",
        "bldg_type": "single family home",
        "climate_zone": ["TRE", "CASO"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["heating", "cooling"],
        "technology": "ASHP"},
        {
        "name": "sample measure 28",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2009$/unit",
        "energy_efficiency": 0.5,
        "energy_efficiency_units": "relative savings (constant)",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": "all",
        "bldg_type": "single family home",
        "climate_zone": ["CT", "NH"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "cooling",
        "technology": "ASHP"}]
    ok_tpmeas_fullchk_in = [
        Measure(
            base_dir, handyvars, handyfiles, opts_dict,
            **x) for x in ok_measures_in[0:5]]
    ok_tpmeas_partchk_in = [
        Measure(
            base_dir, handyvars, handyfiles, opts_dict,
            **x) for x in ok_measures_in[5:24]]
    ok_tpmeas_partchk_emm_in = [
        Measure(
            base_dir, handyvars_emm, handyfiles_emm, opts_emm_dict,
            **x) for x in ok_measures_in[26:28]]
    ok_tpmeas_partchk_state_in = [
        Measure(
            base_dir, handyvars_state, handyfiles_state, opts_state_dict,
            **ok_measures_in[28])]
    ok_mapmeas_partchk_in = [
        Measure(
            base_dir, handyvars, handyfiles, opts_dict,
            **x) for x in ok_measures_in[24:26]]
    ok_measures_site_energy = [
        {"name": "sample measure 1 - site energy",
         "markets": None,
         "installed_cost": 25,
         "cost_units": "2014$/unit",
         "energy_efficiency": {
            "AIA_CZ1": {"heating": 30,
                        "cooling": 25},
            "AIA_CZ2": {"heating": 30,
                        "cooling": 15}},
         "energy_efficiency_units": "COP",
         "market_entry_year": None,
         "market_exit_year": None,
         "product_lifetime": 1,
         "market_scaling_fractions": None,
         "market_scaling_fractions_source": None,
         "measure_type": "full service",
         "structure_type": ["new", "existing"],
         "bldg_type": "single family home",
         "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
         "fuel_type": "electricity",
         "fuel_switch_to": None,
         "end_use": ["heating", "cooling"],
         "technology": ["resistance heat", "ASHP", "GSHP", "room AC"]}
        ]
    ok_tpmeas_sitechk_in = [Measure(
        base_dir, handyvars, handyfiles, opts_site_energy_dict,
        **x) for x in ok_measures_site_energy]
    ok_distmeas_in = [{
        "name": "distrib measure 1",
        "markets": None,
        "installed_cost": ["normal", 25, 5],
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "AIA_CZ1": {
                "heating": ["normal", 30, 1],
                "cooling": ["normal", 25, 2]},
            "AIA_CZ2": {
                "heating": 30,
                "cooling": ["normal", 15, 4]}},
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": ["single family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["heating", "cooling"],
        "technology": ["resistance heat", "ASHP", "GSHP", "room AC"]},
        {
        "name": "distrib measure 2",
        "markets": None,
        "installed_cost": ["lognormal", 3.22, 0.06],
        "cost_units": "2014$/unit",
        "energy_efficiency": ["normal", 25, 5],
        "energy_efficiency_units": "EF",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": ["normal", 1, 1],
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": ["single family home"],
        "climate_zone": ["AIA_CZ1"],
        "fuel_type": ["natural gas"],
        "fuel_switch_to": None,
        "end_use": "water heating",
        "technology": None},
        {
        "name": "distrib measure 3",
        "markets": None,
        "installed_cost": ["normal", 10, 5],
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": {
            "windows conduction": [
                "lognormal", 2.29, 0.14],
            "windows solar": [
                "normal", 1, 0.1]},
        "energy_efficiency_units": {
            "windows conduction": "R Value",
            "windows solar": "SHGC"},
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": ["single family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": [
            "heating", "secondary heating", "cooling"],
        "technology": [
            "windows conduction", "windows solar"]},
        {
        "name": "distrib measure 4",
        "markets": None,
        "installed_cost": 3,
        "cost_units": "2014$/unit",
        "energy_efficiency": 25,
        "energy_efficiency_units": "EF",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": ["single family home"],
        "climate_zone": ["AIA_CZ1"],
        "fuel_type": ["natural gas"],
        "fuel_switch_to": None,
        "end_use": "water heating",
        "technology": None,
        "retro_rate": ["uniform", 0.01, 0.1]}]
    # Seed random number generator to yield consistent retrofit rate
    # results
    numpy.random.seed(1234)
    ok_distmeas_in = [
        Measure(
            base_dir, handyvars, handyfiles, opts_dict,
            **x) for x in ok_distmeas_in]
    ok_partialmeas_in = [{
        "name": "partial measure 1",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": 25,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "bldg_type": ["single family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "cooling",
        "technology": ["resistance heat", "ASHP"]},
        {
        "name": "partial measure 2",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": 25,
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "energy_efficiency_units": "COP",
        "bldg_type": ["single family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["heating", "cooling"],
        "technology": [
            "linear fluorescent (LED)",
            "general service (LED)",
            "external (LED)", "GSHP", "ASHP"]}]
    failmeas_in = [{
        "name": "fail measure mkts 1",
        "markets": None,
        "installed_cost": 10,
        "cost_units": "2014$/unit",
        "energy_efficiency": 10,
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ19", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": "cooling",
        "technology": "resistance heat"},
        {
        "name": "fail measure mkts 2",
        "markets": None,
        "installed_cost": 10,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "AIA_CZ1": {
                "heating": 30, "cooling": 25},
            "AIA_CZ2": {
                "heating": 30, "cooling": 15}},
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family homer",
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["heating", "cooling"],
        "technology": [
            "linear fluorescent (LED)",
            "general service (LED)",
            "external (LED)"]},
        {
        "name": "fail measure mkts 3",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "primary": 25, "secondary": None},
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["newer", "existing"],
        "energy_efficiency_units": {
            "primary": "lm/W", "secondary": None},
        "market_entry_year": None,
        "market_exit_year": None,
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "natural gas",
        "fuel_switch_to": None,
        "end_use": {
            "primary": "lighting",
            "secondary": [
                "heating", "secondary heating",
                "cooling"]},
        "technology": [
            "linear fluorescent (LED)",
            "general service (LED)",
            "external (LED)"]},
        {
        "name": "fail measure mkts 4",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "primary": 25, "secondary": None},
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "energy_efficiency_units": {
            "primary": "lm/W", "secondary": None},
        "market_entry_year": None,
        "market_exit_year": None,
        "bldg_type": "single family home",
        "climate_zone": "AIA_CZ1",
        "fuel_type": "solar",
        "fuel_switch_to": None,
        "end_use": {
            "primary": "lighting",
            "secondary": [
                "heating", "secondary heating",
                "cooling"]},
        "technology": [
            "linear fluorescent (LED)",
            "general service (LED)",
            "external (LED)"]},
        {
        "name": "fail meas mkt entry",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": 3,
        "energy_efficiency_units": "COP",
        "market_entry_year": 2099,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["heating", "cooling"],
        "technology": ["resistance heat", "ASHP", "GSHP", "room AC"]},
        {
        "name": "fail meas performance",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": -3,
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["heating", "cooling"],
        "technology": ["resistance heat", "ASHP", "GSHP", "room AC"]},
        {
        "name": "fail meas cost",
        "markets": None,
        "installed_cost": -3,
        "cost_units": "2014$/unit",
        "energy_efficiency": 3,
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["heating", "cooling"],
        "technology": ["resistance heat", "ASHP", "GSHP", "room AC"]},
        {
        "name": "fail meas market scaling",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": 3,
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 1,
        "market_scaling_fractions": {
            "heating": 1.5,
            "cooling": 1},
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["heating", "cooling"],
        "technology": ["resistance heat", "ASHP", "GSHP", "room AC"]},
        {
        "name": "fail measure missing data",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/ft^2 floor",
        "energy_efficiency": 0.25,
        "energy_efficiency_units": "relative savings (constant)",
        "product_lifetime": 1,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "assembly",
        "climate_zone": "AIA_CZ1",
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": ["PCs", "MELs"],
        "market_entry_year": None,
        "market_exit_year": None,
        "technology": [None, "distribution transformers"]}]
    failmeas_inputs_in = [
        Measure(
            base_dir, handyvars, handyfiles, opts_dict,
            **x) for x in failmeas_in[0:-1]]
    failmeas_missing_in = Measure(
        base_dir, handyvars, handyfiles, opts_dict,
        **failmeas_in[-1])
    warnmeas_in = [{
        "name": "warn measure 1",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "primary": 25,
            "secondary": {
                "heating": 0.4,
                "secondary heating": 0.4,
                "cooling": -0.4}},
        "energy_efficiency_units": {
            "primary": "lm/W",
            "secondary": "relative savings (constant)"},
        "market_entry_year": None,
        "market_exit_year": None,
        "market_scaling_fractions": {
            "new": 0.25,
            "existing": 0.5},
        "market_scaling_fractions_source": {
            "new": {
                "title": None,
                "author": None,
                "organization": None,
                "year": None,
                "URL": None,
                "fraction_derivation": None},
            "existing": {
                "title": None,
                "author": None,
                "organization": None,
                "year": None,
                "URL": None,
                "fraction_derivation": None}},
        "product_lifetime": 1,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": [
            "single family home",
            "multi family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": {
            "primary": "lighting",
            "secondary": [
                "heating", "secondary heating",
                "cooling"]},
        "technology": [
            "linear fluorescent (LED)",
            "general service (LED)",
            "external (LED)"]},
        {
        "name": "warn measure 2",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "primary": 25,
            "secondary": {
                "heating": 0.4,
                "secondary heating": 0.4,
                "cooling": -0.4}},
        "energy_efficiency_units": {
            "primary": "lm/W",
            "secondary": "relative savings (constant)"},
        "market_entry_year": None,
        "market_exit_year": None,
        "market_scaling_fractions": {
            "new": 0.25,
            "existing": 0.5},
        "market_scaling_fractions_source": {
            "new": {
                "title": "Sample title",
                "author": "Sample author",
                "organization": "Sample organization",
                "year": "http://www.sciencedirectcom",
                "URL": "some BS",
                "fraction_derivation": None},
            "existing": {
                "title": "Sample title",
                "author": "Sample author",
                "organization": "Sample organization",
                "year": "Sample year",
                "URL": "http://www.sciencedirect.com",
                "fraction_derivation": None}},
        "product_lifetime": 1,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": [
            "single family home",
            "multi family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": {
            "primary": "lighting",
            "secondary": [
                "heating", "secondary heating",
                "cooling"]},
        "technology": [
            "linear fluorescent (LED)",
            "general service (LED)",
            "external (LED)"]},
        {
        "name": "warn measure 3",
        "markets": None,
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "primary": 25,
            "secondary": {
                "heating": 0.4,
                "secondary heating": 0.4,
                "cooling": -0.4}},
        "energy_efficiency_units": {
            "primary": "lm/W",
            "secondary": "relative savings (constant)"},
        "market_entry_year": None,
        "market_exit_year": None,
        "market_scaling_fractions": {
            "new": 0.25,
            "existing": 0.5},
        "market_scaling_fractions_source": {
            "new": {
                "title": "Sample title",
                "author": None,
                "organization": "Sample organization",
                "year": "Sample year",
                "URL": "https://bpd.lbl.gov/",
                "fraction_derivation": "Divide X by Y"},
            "existing": {
                "title": "Sample title",
                "author": None,
                "organization": None,
                "year": "Sample year",
                "URL": "https://cms.doe.gov/data/green-button",
                "fraction_derivation": "Divide X by Y"}},
        "product_lifetime": 1,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": [
            "single family home",
            "multi family home"],
        "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "end_use": {
            "primary": "lighting",
            "secondary": [
                "heating", "secondary heating",
                "cooling"]},
        "technology": [
            "linear fluorescent (LED)",
            "general service (LED)",
            "external (LED)"]}]
    warnmeas_in = [
        Measure(
            base_dir, handyvars, handyfiles, opts_dict,
            **x) for x in warnmeas_in]
    ok_hp_measures_in = [{
        "name": "sample hp measure 1 - with rates",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": {
            "cooling": 3,
            "heating": 3},
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": {
            "cooling": 0.5,
            "heating": 1},
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": ["electricity", "natural gas"],
        "fuel_switch_to": "electricity",
        "tech_switch_to": "ASHP",
        "end_use": ["heating", "cooling"],
        "technology": ["furnace (NG)", "central AC"]},
        {
        "name": "sample hp measure 2",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": {
            "cooling": 3,
            "heating": 3},
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": {
            "cooling": 0.5,
            "heating": 1},
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "tech_switch_to": "ASHP",
        "end_use": ["heating", "cooling"],
        "technology": ["resistance heat", "central AC"]},
        {
        "name": "sample non-hp measure 1",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": 3,
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": None,
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": "electricity",
        "fuel_switch_to": None,
        "tech_switch_to": None,
        "end_use": "cooling",
        "technology": "central AC"},
        {
        "name": "sample hp measure 1 - no rates",
        "installed_cost": 5000,
        "cost_units": "2009$/unit",
        "energy_efficiency": {
            "cooling": 3,
            "heating": 3},
        "energy_efficiency_units": "COP",
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 15,
        "market_scaling_fractions": {
            "cooling": 0.5,
            "heating": 1},
        "market_scaling_fractions_source": None,
        "measure_type": "full service",
        "structure_type": ["new", "existing"],
        "bldg_type": "single family home",
        "climate_zone": "TRE",
        "fuel_type": ["electricity", "natural gas"],
        "fuel_switch_to": "electricity",
        "tech_switch_to": "ASHP",
        "end_use": ["heating", "cooling"],
        "technology": ["furnace (NG)", "central AC"]}]
    ok_mapmeas_hp_chk_in = [
        Measure(
            base_dir, handyvars_hp_rates, handyfiles_emm,
            opts_hp_rates_dict, **x) for x in ok_hp_measures_in[0:3]]
    ok_mapmeas_hp_chk_in.extend([
        Measure(
            base_dir, handyvars_hp_norates, handyfiles_emm,
            opts_hp_rates_dict, **x) for x in ok_hp_measures_in[3:]])
    ok_tp_fmeth_chk_in = [
        Measure(
            base_dir, handyvars_fmeth[ind], handyfiles_emm,
            opts_fmeth_dict[ind], **x) for ind, x in enumerate(
            ok_fmeth_measures_in)]
    ok_map_frefr_chk_in = [
        Measure(
            base_dir, handyvars_frefr[ind], handyfiles_emm,
            opts_frefr_dict[ind], **x) for ind, x in enumerate(
                ok_frefr_measures_in)]
    # Correct consumer choice dict outputs
    compete_choice_val = [{
        "b1": {"2009": -0.01, "2010": -0.01},
        "b2": {"2009": -0.12, "2010": -0.12}},
        {
        "b1": {"2009": -0.01,
               "2010": -0.01},
        "b2": {"2009": -0.12,
               "2010": -0.12}},
        {
        "b1": {"2009": -0.01,
               "2010": -0.01},
        "b2": {"2009": -0.12,
               "2010": -0.12}},
        {
        "b1": {
            "2009": -0.01,
            "2010": -0.01},
        "b2": {
            "2009": -0.12,
            "2010": -0.12}},
        {
        "b1": {
            "2009": -0.01,
            "2010": -0.01},
        "b2": {
            "2009": -0.12,
            "2010": -0.12}}]
    ok_tpmeas_fullchk_competechoiceout = [{
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'resistance heat-resistance+hpac', 'new')"):
        compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'ASHP-resistance+hpac', 'new')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'GSHP-resistance+hpac', 'new')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'ASHP-resistance+hpac', 'new')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'GSHP-resistance+hpac', 'new')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'room AC-resistance+hpac', 'new')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'resistance heat-resistance+hpac', 'new')"):
        compete_choice_val[0],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'ASHP-resistance+hpac', 'new')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'GSHP-resistance+hpac', 'new')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'ASHP-resistance+hpac', 'new')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'GSHP-resistance+hpac', 'new')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'room AC-resistance+hpac', 'new')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'resistance heat-resistance+hpac', 'existing')"):
        compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'ASHP-resistance+hpac', 'existing')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'GSHP-resistance+hpac', 'existing')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'ASHP-resistance+hpac', 'existing')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'GSHP-resistance+hpac', 'existing')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'room AC-resistance+hpac', 'existing')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'resistance heat-resistance+hpac', 'existing')"):
        compete_choice_val[0],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'ASHP-resistance+hpac', 'existing')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'heating', 'supply', "
         "'GSHP-resistance+hpac', 'existing')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'ASHP-resistance+hpac', 'existing')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'GSHP-resistance+hpac', 'existing')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'cooling', 'supply', "
         "'room AC-resistance+hpac', 'existing')"): compete_choice_val[0]},
        {
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'natural gas', 'water heating', "
         "None, 'new')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'natural gas', 'water heating', "
         "None, 'existing')"): compete_choice_val[0]},
        {
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'other', "
         "'freezers', 'new')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'other', "
         "'freezers', 'existing')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'refrigeration', None, "
         "'existing')"): compete_choice_val[0],
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'refrigeration', None, "
         "'new')"): compete_choice_val[0]},
        {
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'heating', 'demand', 'windows', "
         "'existing')"): compete_choice_val[1],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'heating', 'demand', 'windows', "
         "'existing')"): compete_choice_val[1],
        ("('primary', 'AIA_CZ1', 'multi family home', "
         "'electricity', 'heating', 'demand', 'windows', "
         "'existing')"): compete_choice_val[2],
        ("('primary', 'AIA_CZ2', 'multi family home', "
         "'electricity', 'heating', 'demand', 'windows', "
         "'existing')"): compete_choice_val[2]},
        {
        ("('primary', 'AIA_CZ1', 'single family home', "
         "'electricity', 'lighting', 'linear fluorescent (LED)', "
         "'existing')"): compete_choice_val[3],
        ("('primary', 'AIA_CZ2', 'single family home', "
         "'electricity', 'lighting', 'linear fluorescent (LED)', "
         "'existing')"): compete_choice_val[3],
        ("('primary', 'AIA_CZ1', 'multi family home', "
         "'electricity', 'lighting', 'linear fluorescent (LED)', "
         "'existing')"): compete_choice_val[4],
        ("('primary', 'AIA_CZ2', 'multi family home', "
         "'electricity', 'lighting', 'linear fluorescent (LED)', "
         "'existing')"): compete_choice_val[4]}]
    ok_tpmeas_fullchk_msegadjout = [{
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
            "adjusted energy (competed and captured)": {}}},
        {
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
            "adjusted energy (competed and captured)": {}}},
        {
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
            "adjusted energy (competed and captured)": {}}}]
    ok_tpmeas_fullchk_supplydemandout = [{
        "savings": {
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'resistance heat', 'new')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'ASHP', 'new')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'GSHP', 'new')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'ASHP', 'new')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'GSHP', 'new')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'room AC', 'new')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'resistance heat', 'new')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'ASHP', 'new')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'GSHP', 'new')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'ASHP', 'new')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'GSHP', 'new')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'room AC', 'new')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'resistance heat', 'existing')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'ASHP', 'existing')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'GSHP', 'existing')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'ASHP', 'existing')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'GSHP', 'existing')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'room AC', 'existing')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'resistance heat', 'existing')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'ASHP', 'existing')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'GSHP', 'existing')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'ASHP', 'existing')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'GSHP', 'existing')"): {"2009": 0, "2010": 0},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'room AC', 'existing')"): {"2009": 0, "2010": 0}},
        "total": {
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'resistance heat', 'new')"): {
                "2009": 28.71, "2010": 28.80},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'ASHP', 'new')"): {"2009": 28.71, "2010": 28.80},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'GSHP', 'new')"): {"2009": 28.71, "2010": 28.80},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'ASHP', 'new')"): {"2009": 108.46, "2010": 108.8},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'GSHP', 'new')"): {"2009": 108.46, "2010": 108.8},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'room AC', 'new')"): {"2009": 108.46, "2010": 108.8},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'resistance heat', 'new')"): {
                "2009": 28.71, "2010": 28.80},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'ASHP', 'new')"): {"2009": 28.71, "2010": 28.80},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'GSHP', 'new')"): {"2009": 28.71, "2010": 28.80},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'ASHP', 'new')"): {"2009": 108.46, "2010": 108.8},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'GSHP', 'new')"): {"2009": 108.46, "2010": 108.8},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'room AC', 'new')"): {"2009": 108.46, "2010": 108.8},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'resistance heat', 'existing')"): {
                "2009": 28.71, "2010": 28.80},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'ASHP', 'existing')"): {"2009": 28.71, "2010": 28.80},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'GSHP', 'existing')"): {"2009": 28.71, "2010": 28.80},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'ASHP', 'existing')"): {"2009": 108.46, "2010": 108.8},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'GSHP', 'existing')"): {"2009": 108.46, "2010": 108.8},
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'room AC', 'existing')"): {"2009": 108.46, "2010": 108.8},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'resistance heat', 'existing')"): {
                "2009": 28.71, "2010": 28.80},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'ASHP', 'existing')"): {"2009": 28.71, "2010": 28.80},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'GSHP', 'existing')"): {"2009": 28.71, "2010": 28.80},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'ASHP', 'existing')"): {"2009": 108.46, "2010": 108.8},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'GSHP', 'existing')"): {"2009": 108.46, "2010": 108.8},
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'room AC', 'existing')"): {"2009": 108.46, "2010": 108.8}}},
        {"savings": {}, "total": {}},
        {"savings": {}, "total": {}}]
    ok_mapmas_partchck_msegout = [{
        "stock": {
            "total": {
                "all": {"2009": 11000000, "2010": 11000000},
                "measure": {"2009": 298571.43, "2010": 597142.86}},
            "competed": {
                "all": {"2009": 298571.43, "2010": 298571.43},
                "measure": {"2009": 298571.43, "2010": 298571.43}}},
        "energy": {
            "total": {
                "baseline": {"2009": 31.90, "2010": 32.00},
                "efficient": {"2009": 31.52, "2010": 31.24}},
            "competed": {
                "baseline": {"2009": 0.87, "2010": 0.87},
                "efficient": {"2009": 0.48, "2010": 0.49}}},
        "carbon": {
            "total": {
                "baseline": {"2009": 1813.42, "2010": 1797.38},
                "efficient": {"2009": 1791.76, "2010": 1754.45}},
            "competed": {
                "baseline": {"2009": 49.22, "2010": 48.79},
                "efficient": {"2009": 27.56, "2010": 27.32}}},
        "cost": {
            "stock": {
                "total": {
                    "baseline": {"2009": 4180000, "2010": 8360000},
                    "efficient": {
                        "2009": 7464285.71, "2010": 14928571.43}},
                "competed": {
                    "baseline": {"2009": 4180000, "2010": 4180000},
                    "efficient": {
                        "2009": 7464285.71, "2010": 7464285.71}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 289.65, "2010": 273.60},
                    "efficient": {"2009": 286.19, "2010": 267.06}},
                "competed": {
                    "baseline": {"2009": 7.86, "2010": 7.43},
                    "efficient": {"2009": 4.40, "2010": 4.16}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 59842.87, "2010": 59313.65},
                    "efficient": {"2009": 59128.17, "2010": 57896.90}},
                "competed": {
                    "baseline": {"2009": 1624.31, "2010": 1609.94},
                    "efficient": {"2009": 909.61, "2010": 901.57}}}},
        "lifetime": {"baseline": {"2009": 140, "2010": 140},
                     "measure": 1}},
        {
        "stock": {
            "total": {
                "all": {"2009": 11000000, "2010": 11000000},
                "measure": {"2009": 298571.43, "2010": 597142.86}},
            "competed": {
                "all": {"2009": 298571.43, "2010": 298571.43},
                "measure": {"2009": 298571.43, "2010": 298571.43}}},
        "energy": {
            "total": {
                "baseline": {"2009": 31.90, "2010": 32.00},
                "efficient": {"2009": 31.52, "2010": 31.24}},
            "competed": {
                "baseline": {"2009": 0.87, "2010": 0.87},
                "efficient": {"2009": 0.48, "2010": 0.49}}},
        "carbon": {
            "total": {
                "baseline": {"2009": 1813.42, "2010": 1797.38},
                "efficient": {"2009": 1791.76, "2010": 1754.45}},
            "competed": {
                "baseline": {"2009": 49.22, "2010": 48.79},
                "efficient": {"2009": 27.56, "2010": 27.32}}},
        "cost": {
            "stock": {
                "total": {
                    "baseline": {"2009": 4180000, "2010": 8360000},
                    "efficient": {
                        "2009": 7464285.71, "2010": 14928571.43}},
                "competed": {
                    "baseline": {"2009": 4180000, "2010": 4180000},
                    "efficient": {
                        "2009": 7464285.71, "2010": 7464285.71}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 289.65, "2010": 273.60},
                    "efficient": {"2009": 286.19, "2010": 267.06}},
                "competed": {
                    "baseline": {"2009": 7.86, "2010": 7.43},
                    "efficient": {"2009": 4.40, "2010": 4.16}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 59842.87, "2010": 59313.65},
                    "efficient": {"2009": 59128.17, "2010": 57896.90}},
                "competed": {
                    "baseline": {"2009": 1624.31, "2010": 1609.94},
                    "efficient": {"2009": 909.61, "2010": 901.57}}}},
        "lifetime": {"baseline": {"2009": 140, "2010": 140},
                     "measure": 1}}]
    ok_distmeas_out = [
        [120.86, 100, 790.91, 100, 1.0, 1,
         {yr: 0.02 for yr in handyvars.aeo_years}, 1],
        [11.9, 100, 374.73, 100, 1.28, 100,
         {yr: 0.02 for yr in handyvars.aeo_years}, 1],
        [56.12, 100, 6577018856.89, 100, 1.0, 1,
         {yr: 0.02 for yr in handyvars.aeo_years}, 1],
        [10.91, 1, 45, 1, 1, 1,
         {yr: 0.06 for yr in handyvars.aeo_years}, 100]]
    ok_tpmeas_sitechk_msegout = [{
        "stock": {
            "total": {
                "all": {"2009": 32, "2010": 32},
                "measure": {"2009": 32, "2010": 32}},
            "competed": {
                "all": {"2009": 32, "2010": 32},
                "measure": {"2009": 32, "2010": 32}}},
        "energy": {
            "total": {
                "baseline": {"2009": 229.68 / 3.19, "2010": 230.4 / 3.20},
                "efficient": {"2009": 117.0943 / 3.19,
                              "2010": 117.4613 / 3.20}},
            "competed": {
                "baseline": {"2009": 229.68 / 3.19, "2010": 230.4 / 3.20},
                "efficient": {"2009": 117.0943 / 3.19,
                              "2010": 117.4613 / 3.20}}},
        "carbon": {
            "total": {
                "baseline": {"2009": 13056.63, "2010": 12941.16},
                "efficient": {"2009": 6656.461, "2010": 6597.595}},
            "competed": {
                "baseline": {"2009": 13056.63, "2010": 12941.16},
                "efficient": {"2009": 6656.461, "2010": 6597.595}}},
        "cost": {
            "stock": {
                "total": {
                    "baseline": {"2009": 208, "2010": 208},
                    "efficient": {"2009": 800, "2010": 800}},
                "competed": {
                    "baseline": {"2009": 208, "2010": 208},
                    "efficient": {"2009": 800, "2010": 800}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 2328.955, "2010": 2227.968},
                    "efficient": {"2009": 1187.336, "2010": 1135.851}},
                "competed": {
                    "baseline": {"2009": 2328.955, "2010": 2227.968},
                    "efficient": {"2009": 1187.336, "2010": 1135.851}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 430868.63, "2010": 427058.3},
                    "efficient": {"2009": 219663.21, "2010": 217720.65}},
                "competed": {
                    "baseline": {"2009": 430868.63, "2010": 427058.3},
                    "efficient": {"2009": 219663.21, "2010": 217720.65}}}},
        "lifetime": {"baseline": {"2009": 33.75, "2010": 33.75},
                     "measure": 1}}]
    ok_partialmeas_out = [{
        "stock": {
            "total": {
                "all": {"2009": 36, "2010": 36},
                "measure": {"2009": 36, "2010": 36}},
            "competed": {
                "all": {"2009": 36, "2010": 36},
                "measure": {"2009": 36, "2010": 36}}},
        "energy": {
            "total": {
                "baseline": {"2009": 57.42, "2010": 57.6},
                "efficient": {"2009": 27.5616, "2010": 27.648}},
            "competed": {
                "baseline": {"2009": 57.42, "2010": 57.6},
                "efficient": {"2009": 27.5616, "2010": 27.648}}},
        "carbon": {
            "total": {
                "baseline": {"2009": 3264.156, "2010": 3235.29},
                "efficient": {"2009": 1566.795, "2010": 1552.939}},
            "competed": {
                "baseline": {"2009": 3264.156, "2010": 3235.29},
                "efficient": {"2009": 1566.795, "2010": 1552.939}}},
        "cost": {
            "stock": {
                "total": {
                    "baseline": {"2009": 864, "2010": 864},
                    "efficient": {"2009": 900, "2010": 900}},
                "competed": {
                    "baseline": {"2009": 864, "2010": 864},
                    "efficient": {"2009": 900, "2010": 900}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 582.2388, "2010": 556.992},
                    "efficient": {"2009": 279.4746, "2010": 267.3562}},
                "competed": {
                    "baseline": {"2009": 582.2388, "2010": 556.992},
                    "efficient": {"2009": 279.4746, "2010": 267.3562}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 107717.16, "2010": 106764.58},
                    "efficient": {"2009": 51704.24, "2010": 51247}},
                "competed": {
                    "baseline": {"2009": 107717.16, "2010": 106764.58},
                    "efficient": {"2009": 51704.24, "2010": 51247}}}},
        "lifetime": {"baseline": {"2009": 120, "2010": 120},
                     "measure": 1}},
        {
        "stock": {
            "total": {
                "all": {"2009": 28, "2010": 28},
                "measure": {"2009": 28, "2010": 28}},
            "competed": {
                "all": {"2009": 28, "2010": 28},
                "measure": {"2009": 28, "2010": 28}}},
        "energy": {
            "total": {
                "baseline": {"2009": 165.88, "2010": 166.4},
                "efficient": {"2009": 67.1176, "2010": 67.328}},
            "competed": {
                "baseline": {"2009": 165.88, "2010": 166.4},
                "efficient": {"2009": 67.1176, "2010": 67.328}}},
        "carbon": {
            "total": {
                "baseline": {"2009": 9429.785, "2010": 9346.394},
                "efficient": {"2009": 3815.436, "2010": 3781.695}},
            "competed": {
                "baseline": {"2009": 9429.785, "2010": 9346.394},
                "efficient": {"2009": 3815.436, "2010": 3781.695}}},
        "cost": {
            "stock": {
                "total": {
                    "baseline": {"2009": 200, "2010": 200},
                    "efficient": {"2009": 700, "2010": 700}},
                "competed": {
                    "baseline": {"2009": 200, "2010": 200},
                    "efficient": {"2009": 700, "2010": 700}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 1682.023, "2010": 1609.088},
                    "efficient": {"2009": 680.5725, "2010": 651.0618}},
                "competed": {
                    "baseline": {"2009": 1682.023, "2010": 1609.088},
                    "efficient": {"2009": 680.5725, "2010": 651.0618}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 311182.9, "2010": 308431},
                    "efficient": {"2009": 125909.39, "2010": 124795.93}},
                "competed": {
                    "baseline": {"2009": 311182.9, "2010": 308431},
                    "efficient": {"2009": 125909.39, "2010": 124795.93}}}},
        "lifetime": {"baseline": {"2009": 35.71, "2010": 35.71},
                     "measure": 1}}]
    ok_warnmeas_out = [
        [("WARNING: 'warn measure 1' has invalid "
          "sub-market scaling fraction source title, author, "
          "organization, and/or year information"),
         ("WARNING: 'warn measure 1' has invalid "
          "sub-market scaling fraction source URL information"),
         ("WARNING: 'warn measure 1' has invalid "
          "sub-market scaling fraction derivation information"),
         ("WARNING (CRITICAL): 'warn measure 1' has "
          "insufficient sub-market source information and "
          "will be removed from analysis")],
        [("WARNING: 'warn measure 2' has invalid "
          "sub-market scaling fraction source URL information"),
         ("WARNING: 'warn measure 2' has invalid "
          "sub-market scaling fraction derivation information"),
         ("WARNING (CRITICAL): 'warn measure 2' has "
          "insufficient sub-market source information and "
          "will be removed from analysis")],
        [("WARNING: 'warn measure 3' has invalid "
          "sub-market scaling fraction source title, author, "
          "organization, and/or year information")]]
    ok_tp_fmeth_mkts_out = [
        {
            'total': {
                'baseline': {'2009': 0.0000010908390,
                             '2010': 0.0000010908390},
                'efficient': {'2009': 0, '2010': 0}},
            'competed': {
                'baseline': {'2009': 0.0000010908390,
                             '2010': 0.0000010908390},
                'efficient': {'2009': 0, '2010': 0}}
        },
        {
            'total': {
                'baseline': {'2009': 0.000001472633,
                             '2010': 0.000001472633},
                'efficient': {'2009': 0.000000490878,
                              '2010': 0.000000490878}},
            'competed': {
                'baseline': {'2009': 0.000001472633,
                             '2010': 0.000001472633},
                'efficient': {'2009': 0.000000490878,
                              '2010': 0.000000490878}}
        },
        {
            'total': {
                'baseline': {'2009': 0.000001908968,
                             '2010': 0.000001908968},
                'efficient': {'2009': 0.000000636323,
                              '2010': 0.000000636323}},
            'competed': {
                'baseline': {'2009': 0.000001908968,
                             '2010': 0.000001908968},
                'efficient': {'2009': 0.000000636323,
                              '2010': 0.000000636323}}
        },
        {
            'total': {
                'baseline': {'2009': 0, '2010': 0},
                'efficient': {'2009': 0, '2010': 0}},
            'competed': {
                'baseline': {'2009': 0, '2010': 0},
                'efficient': {'2009': 0, '2010': 0}}
        }]
    ok_map_frefr_mkts_out = [
        {"total": {
             "baseline": {
                "2009": 0.00000353930616, "2010": 0.000004319013285},
             "efficient": {
                "2009": 0.0000027847989, "2010": 0.00000468252675}},
         "competed": {
             "baseline": {
                "2009": 0.00000353930616, "2010": 0.000000779707125},
             "efficient": {
                "2009": 0.0000027847989, "2010": 0.00000189772785}}},
        {"total": {
             "baseline": {
                "2009": 0.00000353930616, "2010": 0.000004319013285},
             "efficient": {
                "2009": 0.000008614311264, "2010": 0.00001051203911}},
         "competed": {
             "baseline": {
                "2009": 0.00000353930616, "2010": 0.000000779707125},
             "efficient": {
                "2009": 0.000008614311264, "2010": 0.00000189772785}}},
        {"total": {
             "baseline": {
                "2009": 0, "2010": 0},
             "efficient": {
                "2009": 0.000003407547, "2010": 0.00000340917085}},
         "competed": {
             "baseline": {
                "2009": 0, "2010": 0},
             "efficient": {
                "2009": 0.000003407547, "2010": 0.00000000162385}}},
        {"total": {
             "baseline": {
                "2009": 0, "2010": 0},
             "efficient": {
                "2009": 0.0000000023829, "2010": 0.00000000400675}},
         "competed": {
             "baseline": {
                "2009": 0, "2010": 0},
             "efficient": {
                "2009": 0.0000000023829, "2010": 0.00000000162385}}},
        {"total": {
             "baseline": {
                "2009": 0.00004188528, "2010": 0.00003862090617},
             "efficient": {
                "2009": 0.00003481005782, "2010": 0.00002998857998}},
         "competed": {
             "baseline": {
                "2009": 0.00000707861232, "2010": 0.00000155941425},
             "efficient": {
                "2009": 0.00000000339014, "2010": 0.000000002310243333}}},
        {"total": {
             "baseline": {
                "2009": 0.3797267945, "2010": 0.46338039042},
             "efficient": {
                "2009": 0.3797267945, "2010": 0.4633803904}},
         "competed": {
             "baseline": {
                "2009": 0.3797267945, "2010": 0.08365359588},
             "efficient": {
                "2009": 0.3797267945, "2010": 0.08365359588}}},
        {"total": {
             "baseline": {
                "2009": 0.3797267945, "2010": 0.46338039042},
             "efficient": {
                "2009": 0.0001818614916, "2010": 0.0003057927448}},
         "competed": {
             "baseline": {
                "2009": 0.3797267945, "2010": 0.08365359588},
             "efficient": {
                "2009": 0.0001818614916, "2010": 0.0001239312532}}},
        {"total": {
             "baseline": {
                "2009": 18.66606381, "2010": 16.59793414},
             "efficient": {
                "2009": 15.63121072, "2010": 13.48205357}},
         "competed": {
             "baseline": {
                "2009": 3.154564784, "2010": 0.0815786758},
             "efficient": {
                "2009": 0.1197116892, "2010": 0.0005512072689}}},
        {"total": {
             "baseline": {
                "2009": 0.00002094264, "2010": 0.00001931045309},
             "efficient": {
                "2009": 0.00002018813274, "2010": 0.00001967396655}},
         "competed": {
             "baseline": {
                "2009": 0.00000353930616, "2010": 0.000000779707125},
             "efficient": {
                "2009": 0.0000027847989, "2010": 0.00000189772785}}},
        {"total": {
             "baseline": {
                "2009": 0.00002094264, "2010": 0.0000209426},
             "efficient": {
                "2009": 0.0000260176451, "2010": 0.0000294761}},
         "competed": {
             "baseline": {
                "2009": 0.00000353930616, "2010": 0.0000024119},
             "efficient": {
                "2009": 0.000008614311264, "2010": 0.0000058703}}}
        ]

    # Convert ok_partialmeas_in from dicts to Measure objects
    ok_partialmeas_in_measures = [
        Measure(base_dir, handyvars, handyfiles, opts_dict, **x)
        for x in ok_partialmeas_in
    ]

    # Return all test data (imported + generated)
    return {
        "ok_tpmeas_fullchk_break_out": ok_tpmeas_fullchk_break_out,
        "sample_cpl_in": sample_cpl_in,
        "ok_tpmeas_partchk_msegout": ok_tpmeas_partchk_msegout,
        "sample_cpl_in_state": sample_cpl_in_state,
        "sample_cpl_in_emm": sample_cpl_in_emm,
        "sample_mseg_in": sample_mseg_in,
        "ok_hpmeas_rates_breakouts": ok_hpmeas_rates_breakouts,
        "ok_partialmeas_in": ok_partialmeas_in_measures,
        "ok_hpmeas_rates_mkts_out": ok_hpmeas_rates_mkts_out,
        "ok_tpmeas_fullchk_msegout": ok_tpmeas_fullchk_msegout,
        "sample_mseg_in_emm": sample_mseg_in_emm,
        "sample_mseg_in_state": sample_mseg_in_state,
        "ok_tpmeas_partchk_msegout_emm": ok_tpmeas_partchk_msegout_emm,
        "ok_tpmeas_partchk_msegout_state": ok_tpmeas_partchk_msegout_state,
        "opts": opts,
        "opts_site_energy": opts_site_energy,
        "opts_emm": opts_emm,
        "opts_state": opts_state,
        "opts_hp_rates": opts_hp_rates,
        "opts_hp_no_rates": opts_hp_no_rates,
        "opts_fmeth": opts_fmeth,
        "opts_frefr": opts_frefr,
        "convert_data": convert_data,
        "tsv_data": tsv_data,
        "ok_tpmeas_fullchk_in": ok_tpmeas_fullchk_in,
        "ok_tpmeas_partchk_in": ok_tpmeas_partchk_in,
        "ok_tpmeas_partchk_emm_in": ok_tpmeas_partchk_emm_in,
        "ok_tpmeas_partchk_state_in": ok_tpmeas_partchk_state_in,
        "ok_mapmeas_partchk_in": ok_mapmeas_partchk_in,
        "ok_tpmeas_sitechk_in": ok_tpmeas_sitechk_in,
        "ok_distmeas_in": ok_distmeas_in,
        "failmeas_inputs_in": failmeas_inputs_in,
        "warnmeas_in": warnmeas_in,
        "ok_mapmeas_hp_chk_in": ok_mapmeas_hp_chk_in,
        "ok_tp_fmeth_chk_in": ok_tp_fmeth_chk_in,
        "ok_map_frefr_chk_in": ok_map_frefr_chk_in,
        "ok_tpmeas_fullchk_competechoiceout": ok_tpmeas_fullchk_competechoiceout,
        "ok_tpmeas_fullchk_msegadjout": ok_tpmeas_fullchk_msegadjout,
        "ok_tpmeas_fullchk_supplydemandout": ok_tpmeas_fullchk_supplydemandout,
        "ok_mapmas_partchck_msegout": ok_mapmas_partchck_msegout,
        "ok_distmeas_out": ok_distmeas_out,
        "ok_tpmeas_sitechk_msegout": ok_tpmeas_sitechk_msegout,
        "ok_partialmeas_out": ok_partialmeas_out,
        "ok_warnmeas_out": ok_warnmeas_out,
        "ok_tp_fmeth_mkts_out": ok_tp_fmeth_mkts_out,
        "ok_map_frefr_mkts_out": ok_map_frefr_mkts_out,
    }


def test_mseg_ok_full_tp(market_test_data):
    """Test 'fill_mkts' function given valid inputs.

    Notes:
        Checks the all branches of measure 'markets' attribute
        under a Technical potential scenario.

    Raises:
        AssertionError: If function yields unexpected results.
    """
    # Run function on all measure objects and check output
    for idx, measure in enumerate(market_test_data["ok_tpmeas_fullchk_in"]):
        measure.fill_mkts(
            market_test_data["sample_mseg_in"], market_test_data["sample_cpl_in"],
            market_test_data["convert_data"], market_test_data["tsv_data"],
            market_test_data["opts"], ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
        # Restrict the full check of all branches of 'markets' to only
        # the first three measures in this set. For the remaining two
        # measures, only check the competed choice parameter outputs.
        # These last two measures are intended to test a special case where
        # measure cost units are in $/ft^2 floor rather than $/unit and
        # competed choice parameters must be scaled accordingly
        if idx < 3:
            dict_check(
                measure.markets['Technical potential']['master_mseg'],
                market_test_data["ok_tpmeas_fullchk_msegout"][idx])
            dict_check(
                measure.markets['Technical potential']['mseg_adjust'][
                    'secondary mseg adjustments'],
                market_test_data["ok_tpmeas_fullchk_msegadjout"][idx])
            dict_check(
                measure.markets['Technical potential'][
                    'mseg_out_break'],
                market_test_data["ok_tpmeas_fullchk_break_out"][idx])
        dict_check(
            measure.markets['Technical potential']['mseg_adjust'][
                'competed choice parameters'],
            market_test_data["ok_tpmeas_fullchk_competechoiceout"][idx])


def test_mseg_ok_part_tp(market_test_data):
    """Test 'fill_mkts' function given valid inputs.

    Notes:
        Checks the 'master_mseg' branch of measure 'markets' attribute
        under a Technical potential scenario with AIA regions specified.

    Raises:
        AssertionError: If function yields unexpected results.
    """
    for idx, measure in enumerate(market_test_data["ok_tpmeas_partchk_in"]):
        measure.fill_mkts(
            market_test_data["sample_mseg_in"], market_test_data["sample_cpl_in"],
            market_test_data["convert_data"], market_test_data["tsv_data"],
            market_test_data["opts"], ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
        dict_check(
            measure.markets['Technical potential']['master_mseg'],
            market_test_data["ok_tpmeas_partchk_msegout"][idx])


def test_mseg_ok_part_map(market_test_data):
    """Test 'fill_mkts' function given valid inputs.

    Notes:
        Checks the 'master_mseg' branch of measure 'markets' attribute
        under a Max adoption potential scenario.

    Raises:
        AssertionError: If function yields unexpected results.
    """
    # Run function on all measure objects and check for correct
    # output
    for idx, measure in enumerate(market_test_data["ok_mapmeas_partchk_in"]):
        measure.fill_mkts(
            market_test_data["sample_mseg_in"], market_test_data["sample_cpl_in"],
            market_test_data["convert_data"], market_test_data["tsv_data"],
            market_test_data["opts"], ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
        dict_check(
            measure.markets['Max adoption potential']['master_mseg'],
            market_test_data["ok_mapmas_partchck_msegout"][idx])


def test_mseg_ok_distrib(market_test_data):
    """Test 'fill_mkts' function given valid inputs.

    Notes:
        Valid input measures are assigned distributions on
        their cost, performance, and/or lifetime attributes.

    Raises:
        AssertionError: If function yields unexpected results.
    """
    # Seed random number generator to yield repeatable cost, performance
    # and lifetime results
    numpy.random.seed(1234)
    for idx, measure in enumerate(market_test_data["ok_distmeas_in"]):
        # Generate lists of energy and cost output values
        measure.fill_mkts(
            market_test_data["sample_mseg_in"], market_test_data["sample_cpl_in"],
            market_test_data["convert_data"], market_test_data["tsv_data"],
            market_test_data["opts"], ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
        test_outputs = measure.markets[
            'Technical potential']['master_mseg']
        test_e = test_outputs["energy"]["total"]["efficient"]["2009"]
        test_c = test_outputs[
            "cost"]["stock"]["total"]["efficient"]["2009"]
        test_l = test_outputs["lifetime"]["measure"]
        test_r = measure.retro_rate
        test_e, test_c, test_l, test_r = [
            [x] if type(x) is float else x for x in [
                test_e, test_c, test_l, test_r]]
        # Calculate mean values from output lists for testing
        param_e = round(sum(test_e) / len(test_e), 2)
        param_c = round(sum(test_c) / len(test_c), 2)
        param_l = round(sum(test_l) / len(test_l), 2)
        param_r = {}
        for ind, k in enumerate(test_r.keys()):
            # Pull out the retrofit rate value; find mean value for cases
            # with a distribution of values
            if not isinstance(test_r[k], float):
                # Pull out the length of the first year's retrofit value
                if ind == 0:
                    len_test_r = len(test_r[k])
                param_r[k] = round(sum(test_r[k]) / len(test_r[k]), 2)
            else:
                # Case where retrofit value is a float of length 1
                if ind == 0:
                    len_test_r = 1
                param_r[k] = test_r[k]

        # Check mean values and length of output lists to ensure
        # correct
        assert [
            param_e, len(test_e), param_c, len(test_c),
            param_l, len(test_l), param_r, len_test_r] == \
            market_test_data["ok_distmeas_out"][idx]


def test_mseg_sitechk(market_test_data):
    """Test 'fill_mkts' function given site energy output.

    Raises:
        AssertionError: If function yields unexpected results.
    """
    # Run function on all measure objects and check output
    for idx, measure in enumerate(market_test_data["ok_tpmeas_sitechk_in"]):
        measure.fill_mkts(market_test_data["sample_mseg_in"], market_test_data["sample_cpl_in"],
                          market_test_data["convert_data"], market_test_data["tsv_data"],
                          market_test_data["opts_site_energy"],
                          ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
        dict_check(
            measure.markets['Technical potential']['master_mseg'],
            market_test_data["ok_tpmeas_sitechk_msegout"][idx])


def test_mseg_partial(market_test_data):
    """Test 'fill_mkts' function given partially valid inputs.

    Raises:
        AssertionError: If function yields unexpected results.
    """
    # Run function on all measure objects and check output
    for idx, measure in enumerate(market_test_data["ok_partialmeas_in"]):
        measure.fill_mkts(
            market_test_data["sample_mseg_in"], market_test_data["sample_cpl_in"],
            market_test_data["convert_data"], market_test_data["tsv_data"],
            market_test_data["opts"], ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
        dict_check(
            measure.markets['Technical potential']['master_mseg'],
            market_test_data["ok_partialmeas_out"][idx])


def test_mseg_fail_inputs(market_test_data):
    """Test 'fill_mkts' function given invalid inputs.

    Raises:
        AssertionError: If ValueError is not raised.
    """
    # Run function on all measure objects and check output
    for idx, measure in enumerate(market_test_data["failmeas_inputs_in"]):
        with pytest.raises(Exception):
            measure.check_meas_inputs()


def test_mseg_warn(market_test_data):
    """Test 'fill_mkts' function given incomplete inputs.

    Raises:
        AssertionError: If function yields unexpected results or
        UserWarning is not raised.
    """
    # Run function on all measure objects and check output
    for idx, mw in enumerate(market_test_data["warnmeas_in"]):
        # Assert that inputs generate correct warnings and that measure
        # is marked inactive where necessary
        with warnings.catch_warnings(record=True) as w:
            mw.fill_mkts(
                market_test_data["sample_mseg_in"], market_test_data["sample_cpl_in"],
                market_test_data["convert_data"], market_test_data["tsv_data"],
                market_test_data["opts"], ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
            # Check correct number of warnings is yielded
            assert all([issubclass(wn.category, UserWarning) for wn in w])
            for wm in market_test_data["ok_warnmeas_out"][idx]:
                assert wm in str([wmt.message for wmt in w])
            # Check that measure is marked inactive when a critical
            # warning message is yielded
            if any(['CRITICAL' in x for x in market_test_data["ok_warnmeas_out"][
                    idx]]):
                assert mw.remove is True
            else:
                assert mw.remove is False


def test_mseg_ok_part_tp_emm(market_test_data):
    """Test 'fill_mkts' function given valid inputs.

    Notes:
        Checks the 'master_mseg' branch of measure 'markets' attribute
        under a Technical potential scenario with EMM regions specified.

    Raises:
        AssertionError: If function yields unexpected results.
    """
    for idx, measure in enumerate(market_test_data["ok_tpmeas_partchk_emm_in"]):
        # Assert that inputs generate correct warnings and that measure
        # is marked inactive where necessary
        measure.fill_mkts(
            market_test_data["sample_mseg_in_emm"],
            market_test_data["sample_cpl_in_emm"],
            market_test_data["convert_data"], market_test_data["tsv_data"],
            market_test_data["opts_emm"], ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
        dict_check(
            measure.markets['Technical potential']['master_mseg'],
            market_test_data["ok_tpmeas_partchk_msegout_emm"][idx])


def test_mseg_ok_part_tp_state(market_test_data):
    """Test 'fill_mkts' function given valid inputs.

    Notes:
        Checks the 'master_mseg' branch of measure 'markets' attribute
        under a Technical potential scenario with states specified.

    Raises:
        AssertionError: If function yields unexpected results.
    """
    for idx, measure in enumerate(market_test_data["ok_tpmeas_partchk_state_in"]):
        measure.fill_mkts(
            market_test_data["sample_mseg_in_state"],
            market_test_data["sample_cpl_in_state"],
            market_test_data["convert_data"], market_test_data["tsv_data"],
            market_test_data["opts_state"], ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
        dict_check(
            measure.markets['Technical potential']['master_mseg'],
            market_test_data["ok_tpmeas_partchk_msegout_state"][idx])


def test_mseg_ok_hp_rates_map(market_test_data):
    """Test 'fill_mkts' function given valid inputs.

    Notes:
        Checks the 'master_mseg' and 'mseg_out_break' branches of measure
        'markets' attribute under a max adoption potential scenario with
        EMM regions, fuel splits, and HP measures, where some HPs fuel
        switch under exogenous rates, as well as other non-HP measures
        that are used to ensure HP settings are not erroneously applied
        to other measure types.

    Raises:
        AssertionError: If function yields unexpected results.
    """
    for idx, measure in enumerate(market_test_data["ok_mapmeas_hp_chk_in"]):
        # Handle test measures with and without exogenous HP conversion
        # rates specified
        if "no rates" in measure.name:
            measure.fill_mkts(
                market_test_data["sample_mseg_in_emm"],
                market_test_data["sample_cpl_in_emm"],
                market_test_data["convert_data"], market_test_data["tsv_data"],
                market_test_data["opts_hp_no_rates"],
                ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
        else:
            measure.fill_mkts(
                market_test_data["sample_mseg_in_emm"],
                market_test_data["sample_cpl_in_emm"],
                market_test_data["convert_data"], market_test_data["tsv_data"],
                market_test_data["opts_hp_rates"],
                ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
        dict_check(
            measure.markets['Max adoption potential']['master_mseg'],
            market_test_data["ok_hpmeas_rates_mkts_out"][idx])

        # Check output breakouts including fuel splits for the first HP
        # measure (which uses exogenous fuel switching rates) and the last
        # HP measure (which does not use exogenous fuel switching rates)
        if "with rates" in measure.name:
            dict_check(measure.markets['Max adoption potential'][
                'mseg_out_break'], market_test_data["ok_hpmeas_rates_breakouts"][0])
        elif "no rates" in measure.name:
            dict_check(
                measure.markets['Max adoption potential'][
                    'mseg_out_break'], market_test_data["ok_hpmeas_rates_breakouts"][1])


def test_mseg_ok_fmeth_co2_tp(market_test_data):
    """Test 'fill_mkts' function given valid inputs.

    Notes:
        Checks the 'master_mseg' branch of measure 'markets' attribute
        under a technical potential scenario with EMM regions and
        fugitive methane emissions, where some measures have fugitive
        methane emissions impacts and others do not to ensure fugitive
        methane emissions settings are not erroneously applied.

    Raises:
        AssertionError: If function yields unexpected results.
    """
    for idx, measure in enumerate(market_test_data["ok_tp_fmeth_chk_in"]):
        measure.fill_mkts(
            market_test_data["sample_mseg_in_emm"],
            market_test_data["sample_cpl_in_emm"],
            market_test_data["convert_data"], market_test_data["tsv_data"],
            market_test_data["opts_fmeth"][idx],
            ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
        dict_check(
            measure.markets['Technical potential']['master_mseg'][
                            'fugitive emissions']['methane'],
            market_test_data["ok_tp_fmeth_mkts_out"][idx])


def test_mseg_ok_frefr_co2_map(market_test_data):
    """Test 'fill_mkts' function given valid inputs.

    Notes:
        Checks the 'master_mseg' and 'mseg_out_break' branches of measure
        'markets' attribute under a max adoption potential scenario with
        EMM regions and fugitive refrigerant emissions.

    Raises:
        AssertionError: If function yields unexpected results.
    """
    for idx, measure in enumerate(market_test_data["ok_map_frefr_chk_in"]):
        measure.fill_mkts(
            market_test_data["sample_mseg_in_emm"],
            market_test_data["sample_cpl_in_emm"],
            market_test_data["convert_data"], market_test_data["tsv_data"],
            market_test_data["opts_frefr"][idx],
            ctrb_ms_pkg_prep=[], tsv_data_nonfs=None)
        dict_check(
            measure.markets['Max adoption potential']['master_mseg'][
                            'fugitive emissions']['refrigerants'],
            market_test_data["ok_map_frefr_mkts_out"][idx])


def test_dual_fuel(market_test_data):
    """
    Dual-fuel (STATE breakout, CA) â€” verify the outputs  master_mseg and
    mseg_out_break are produced, contains both Electric and Non-Electric
    for Heating (Equip.), and compare against the expected one.
    """

    # Initialize dummy measure with state-level inputs to draw from
    base_state_meas = market_test_data["ok_tpmeas_partchk_state_in"][0]
    # Pull handyvars from first sample measure and set year range
    hv = copy.deepcopy(base_state_meas.handyvars)
    years = [str(y) for y in hv.aeo_years]

    # Options: split fuel reporting + pick Max adoption potential
    opts = copy.deepcopy(market_test_data["opts_state"])
    opts.split_fuel = True
    opts.adopt_scn_usr = ["Max adoption potential"]

    # Ensure fuel-split breakouts (Electric vs Non-Electric)
    hv.out_break_fuels = OrderedDict([
        ("Electric", ["electricity"]),
        ("Non-Electric", ["natural gas", "distillate",
                          "residual", "other fuel"]),
    ])
    # Rebuild the blank breakout template (mirrors UsefulVars behavior)
    out_levels = [
        list(hv.out_break_czones.keys()),
        list(hv.out_break_bldgtypes.keys()),
        list(hv.out_break_enduses.keys()),
    ]
    hv.out_break_in = OrderedDict()
    for cz in out_levels[0]:
        hv.out_break_in.setdefault(cz, OrderedDict())
        for b in out_levels[1]:
            hv.out_break_in[cz].setdefault(b, OrderedDict())
            for eu in out_levels[2]:
                if (len(hv.out_break_fuels) != 0) and (
                        eu in hv.out_break_eus_w_fsplits):
                    hv.out_break_in[cz][b][eu] = OrderedDict(
                        [(f, OrderedDict()) for f in hv.out_break_fuels.keys()]
                    )
                else:
                    hv.out_break_in[cz][b][eu] = OrderedDict()

    # Seed BY-YEAR carbon price
    carb_prices = hv.ccosts
    carb_prices.update({y: 1 for y in years})

    # Seed BY-YEAR energy price & carbon intensities
    el_prices = hv.ecosts.setdefault(
        "residential", {}).setdefault("electricity", {})
    el_prices.update({y: 60.0 for y in years})
    ng_prices = hv.ecosts["residential"].setdefault("natural gas", {})
    ng_prices.update({y: 11.0 for y in years})

    el_carb = hv.carb_int.setdefault(
        "residential", {}).setdefault("electricity", {})
    el_carb.update({y: 5.0e-08 for y in years})
    ng_carb = hv.carb_int["residential"].setdefault("natural gas", {})
    ng_carb.update({y: 5.0e-08 for y in years})

    hv.ss_conv.setdefault("electricity", {})
    hv.ss_conv.setdefault("natural gas", {})
    for y in years:
        hv.ss_conv["electricity"][y] = 1.0
        hv.ss_conv["natural gas"][y] = 1.0

    # Baseline microsegment (STATE: CA, SFH, NG heating â†’ furnace (NG))
    mseg_in_dual = {
        "CA": {
            "single family home": {
                "total square footage": {y: 100 for y in years},
                "total homes": {y: 1000 for y in years},
                "new homes": {y: 50 for y in years},
                "natural gas": {
                    "heating": {
                        "supply": {
                            "furnace (NG)": {
                                "stock": {y: 10 for y in years},
                                "energy": {y: 100.0 for y in years},
                            }
                        }
                    }
                },
            }
        }
    }

    # C/P/L for baseline NG furnace and switched-to ELECTRIC ASHP


def test_added_cooling(market_test_data):
    """
    Added cooling only (no dual-fuel).
    Construct a minimal NGâ†’Electric (ASHP) full-service HP measure that
    adds cooling where baseline has (effectively) none.
    Validate that mseg_out_break is populated and
    contains Cooling (Equip.) under the efficient branch for CA.
    """
    # Initialize dummy measure with state-level inputs to draw from
    base_state_meas = market_test_data["ok_tpmeas_partchk_state_in"][0]
    # Pull handyvars from first sample measure and set year range
    hv = copy.deepcopy(base_state_meas.handyvars)
    years = [str(y) for y in hv.aeo_years]

    # Options: split fuel reporting + pick Max adoption potential
    opts = copy.deepcopy(market_test_data["opts_state"])
    opts.split_fuel = True
    opts.adopt_scn_usr = ["Max adoption potential"]

    # Ensure fuel-split breakouts (Electric vs Non-Electric)
    hv.out_break_fuels = OrderedDict([
        ("Electric", ["electricity"]),
        ("Non-Electric", ["natural gas", "distillate",
         "residual", "other fuel"]),
    ])
    # Rebuild the blank breakout template (mirrors UsefulVars behavior)
    out_levels = [
        list(hv.out_break_czones.keys()),
        list(hv.out_break_bldgtypes.keys()),
        list(hv.out_break_enduses.keys()),
    ]
    hv.out_break_in = OrderedDict()
    for cz in out_levels[0]:
        hv.out_break_in.setdefault(cz, OrderedDict())
        for b in out_levels[1]:
            hv.out_break_in[cz].setdefault(b, OrderedDict())
            for eu in out_levels[2]:
                if (len(hv.out_break_fuels) != 0) and (
                        eu in hv.out_break_eus_w_fsplits):
                    hv.out_break_in[cz][b][eu] = OrderedDict(
                        (f, OrderedDict()) for f in hv.out_break_fuels.keys()
                    )
                else:
                    hv.out_break_in[cz][b][eu] = OrderedDict()

    # Seed BY-YEAR carbon price
    carb_prices = hv.ccosts
    carb_prices.update({y: 1 for y in years})

    # Seed BY-YEAR electricity price & carbon intensities
    el_prices = hv.ecosts.setdefault(
        "residential", {}).setdefault("electricity", {})
    el_prices.update({y: 60.0 for y in years})
    ng_prices = hv.ecosts["residential"].setdefault("natural gas", {})
    ng_prices.update({y: 11.0 for y in years})

    el_carb = hv.carb_int.setdefault(
        "residential", {}).setdefault("electricity", {})
    el_carb.update({y: 5.0e-08 for y in years})
    ng_carb = hv.carb_int["residential"].setdefault("natural gas", {})
    ng_carb.update({y: 5.0e-08 for y in years})

    hv.ss_conv.setdefault("electricity", {})
    hv.ss_conv.setdefault("natural gas", {})
    for y in years:
        hv.ss_conv["electricity"][y] = 1.0
        hv.ss_conv["natural gas"][y] = 1.0

    # Baseline microsegments (STATE: CA, SFH)
    # - Heating on NG furnace (present)
    # - Cooling: absent in portion of baseline measure applies to
    mseg_in = {
        "CA": {
            "single family home": {
                "total square footage": {y: 100 for y in years},
                "total homes": {y: 1000 for y in years},
                "new homes": {y: 50 for y in years},
                "natural gas": {
                    "heating": {
                        "supply": {
                            "furnace (NG)": {
                                "stock": {y: 10 for y in years},
                                "energy": {y: 100.0 for y in years},
                            }
                        }
                    }
                },
                "electricity": {
                    "cooling": {
                        "supply": {
                            "central AC": {
                                "stock": {y: 1 for y in years},
                                "energy": {y: 100 for y in years},
                            },
                            "ASHP": {
                                "stock": {y: 1 for y in years},
                                "energy": {y: 100 for y in years},
                            }
                        }
                    },
                    "heating": {
                        "supply": {
                            "ASHP": {
                                "stock": {y: 1 for y in years},
                                "energy": {y: 100 for y in years},
                            }
                        }
                    }
                },
            }
        }
    }


def test_incentives(market_test_data):
    """Test 'apply_incentives' in 'fill_mkts' function given user-defined incentive inputs."""

    # Initialize dummy measure with state-level inputs to draw from
    base_state_meas = market_test_data["ok_tpmeas_partchk_state_in"][0]
    # Pull handyvars from first sample measure and set year range
    hv = copy.deepcopy(base_state_meas.handyvars)
    # Set user-defined incentives information; test stacked federal and non-federal incentives
    hv.incentives = [[
        "CA", "single family home", "existing", "heating", "ASHP",
        "electricity", "natural gas", "no", "replace", "federal", False,
        0, "warm climates: 2.6; cold climates: 2.8", "COP", 30, 2000,
        "$/unit", 2010, 2050, 1],
        [
        "CA", "single family home", "existing", "heating", "ASHP",
        "electricity", "natural gas", "no", "replace", "non-federal", False,
        0, 2.6, "COP", 50, float('nan'), "$/unit", 2010, 2050, 1]
        ]
    years = [str(y) for y in hv.aeo_years]

    # Seed BY-YEAR carbon price
    carb_prices = hv.ccosts
    carb_prices.update({y: 1 for y in years})

    # Seed BY-YEAR electricity price & carbon intensities
    el_prices = hv.ecosts.setdefault(
        "residential", {}).setdefault("electricity", {})
    el_prices.update({y: 60.0 for y in years})
    ng_prices = hv.ecosts["residential"].setdefault("natural gas", {})
    ng_prices.update({y: 11.0 for y in years})

    el_carb = hv.carb_int.setdefault(
        "residential", {}).setdefault("electricity", {})
    el_carb.update({y: 5.0e-08 for y in years})
    ng_carb = hv.carb_int["residential"].setdefault("natural gas", {})
    ng_carb.update({y: 5.0e-08 for y in years})

    hv.ss_conv.setdefault("electricity", {})
    hv.ss_conv.setdefault("natural gas", {})
    for y in years:
        hv.ss_conv["electricity"][y] = 1.0
        hv.ss_conv["natural gas"][y] = 1.0

    # Options: split fuel reporting + pick Max adoption potential
    opts = copy.deepcopy(market_test_data["opts_state"])
    opts.adopt_scn_usr = ["Max adoption potential"]

    # Baseline microsegments (STATE: CA, SFH)
    mseg_in = {
        "CA": {
            "single family home": {
                "total square footage": {y: 100 for y in years},
                "total homes": {y: 1000 for y in years},
                "new homes": {y: 50 for y in years},
                "natural gas": {
                    "heating": {
                        "supply": {
                            "furnace (NG)": {
                                "stock": {y: 10 for y in years},
                                "energy": {y: 100.0 for y in years},
                            }
                        }
                    }
                },
                "electricity": {
                    "cooling": {
                        "supply": {
                            "central AC": {
                                "stock": {y: 1 for y in years},
                                "energy": {y: 100 for y in years},
                            },
                            "ASHP": {
                                "stock": {y: 1 for y in years},
                                "energy": {y: 100 for y in years},
                            }
                        }
                    },
                    "heating": {
                        "supply": {
                            "ASHP": {
                                "stock": {y: 1 for y in years},
                                "energy": {y: 100 for y in years},
                            }
                        }
                    }
                },
            }
        }
    }

    # Function to produce year range


def test_alt_rates(market_test_data):
    """Test 'fill_mkts' function given user-defined alternate electricity rate inputs.

    Notes:
        Alternate rate inputs can be specific to a technology (ASHP) or general across
        an electric end use (e.g., all electric heating).
    """

    # Initialize dummy measure with state-level inputs to draw from
    base_state_meas = market_test_data["ok_tpmeas_partchk_state_in"][0]
    # Pull handyvars from first sample measure and set year range
    hv = copy.deepcopy(base_state_meas.handyvars)
    # Set user-defined alternate electricity rates for CA
    hv.low_volume_rate = [[
        "CA", "single family home", "existing", "heating", "ASHP",
        "electricity", 0.06, False, 302, 2010, 2050, 1],
        [
        "CA", "single family home", "new", "heating", "ASHP",
        "electricity", False, 25, 302, 2010, 2050, 1]]
    years = [str(y) for y in hv.aeo_years]

    # Seed BY-YEAR carbon price
    carb_prices = hv.ccosts
    carb_prices.update({y: 1 for y in years})

    # Seed BY-YEAR electricity price (before alternate rate) & carbon intensities
    el_prices = hv.ecosts.setdefault(
        "residential", {}).setdefault("electricity", {})
    el_prices.update({y: 60.0 for y in years})
    ng_prices = hv.ecosts["residential"].setdefault("natural gas", {})
    ng_prices.update({y: 11.0 for y in years})

    el_carb = hv.carb_int.setdefault(
        "residential", {}).setdefault("electricity", {})
    el_carb.update({y: 5.0e-08 for y in years})
    ng_carb = hv.carb_int["residential"].setdefault("natural gas", {})
    ng_carb.update({y: 5.0e-08 for y in years})

    hv.ss_conv.setdefault("electricity", {})
    hv.ss_conv.setdefault("natural gas", {})
    for y in years:
        hv.ss_conv["electricity"][y] = 1.0
        hv.ss_conv["natural gas"][y] = 1.0

    # Options: split fuel reporting + pick Max adoption potential
    opts = copy.deepcopy(market_test_data["opts_state"])
    opts.adopt_scn_usr = ["Max adoption potential"]

    # Baseline microsegments (STATE: CA, SFH)
    mseg_in = {
        "CA": {
            "single family home": {
                "total square footage": {y: 100 for y in years},
                "total homes": {y: 1000 for y in years},
                "new homes": {y: 50 for y in years},
                "natural gas": {
                    "heating": {
                        "supply": {
                            "furnace (NG)": {
                                "stock": {y: 10 for y in years},
                                "energy": {y: 100.0 for y in years},
                            }
                        }
                    }
                },
                "electricity": {
                    "heating": {
                        "supply": {
                            "ASHP": {
                                "stock": {y: 1 for y in years},
                                "energy": {y: 100 for y in years},
                            }
                        }
                    }
                },
            }
        }
    }

    # Function to produce year range

