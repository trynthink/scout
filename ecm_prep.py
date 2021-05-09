#!/usr/bin/env python3
import numpy
import re
import itertools
import json
from collections import OrderedDict
from os import listdir, getcwd, stat, path
from os.path import isfile, join
import copy
import warnings
from urllib.parse import urlparse
import gzip
import pickle
from functools import reduce  # forward compatibility for Python 3
import operator
from argparse import ArgumentParser
from ast import literal_eval
from datetime import datetime


class MyEncoder(json.JSONEncoder):
    """Convert numpy arrays to list for JSON serializing."""

    def default(self, obj):
        """Modify 'default' method from JSONEncoder."""
        # Case where object to be serialized is numpy array
        if isinstance(obj, numpy.ndarray):
            return obj.tolist()
        # All other cases
        else:
            return super(MyEncoder, self).default(obj)


class UsefulInputFiles(object):
    """Class of input file paths to be used by this routine.

    Attributes:
        msegs_in (tuple): Database of baseline microsegment stock/energy.
        msegs_cpl_in (tuple): Database of baseline technology characteristics.
        iecc_reg_map (tuple): Maps IECC climates to AIA or EMM regions/states.
        ash_emm_map (tuple): Maps ASHRAE climates to EMM regions.
        aia_altreg_map (tuple): Maps AIA climates to EMM regions or states.
        metadata (tuple) = Baseline metadata inc. min/max for year range.
        cost_convert_in (tuple): Database of measure cost unit conversions.
        cbecs_sf_byvint (tuple): Commercial sq.ft. by vintage data.
        indiv_ecms (tuple): Individual ECM JSON definitions folder.
        ecm_packages (tuple): Measure package data.
        ecm_prep (tuple): Prepared measure attributes data for use in the
            analysis engine.
        ecm_compete_data (tuple): Folder with contributing microsegment data
            needed to run measure competition in the analysis engine.
        run_setup (tuple): Names of active measures that should be run in
            the analysis engine.
        cpi_data (CSV): Historical Consumer Price Index data.
        ss_data (JSON): Site-source, emissions, and price data, national.
        ss_data_altreg (JSON): Emissions/price data, EMM- or state-resolved.
        tsv_load_data (JSON): Time sensitive energy demand data.
        tsv_cost_data (JSON): Time sensitive electricity price data.
        tsv_carbon_data (JSON): Time sensitive average CO2 emissions data.
        tsv_shape_data (CSV): Custom time sensitive hourly savings shape data.
        tsv_metrics_data_tot (CSV): Total system load shape data by EMM region.
        tsv_metrics_data_net (CSV): Net system load shape data by EMM region.
        health_data (CSV): EPA public health benefits data by EMM region.
        htcl_totals (tuple): Heating/cooling energy totals by climate zone,
            building type, and structure type.
        regions (str): Specifies which baseline data file to choose, based on
            intended regional breakout.
        ash_emm_map (TXT): Factors for mapping ASHRAE climates to EMM regions.
    """

    def __init__(self, capt_energy, regions, site_energy):
        if regions == 'AIA':
            # UNCOMMENT WITH ISSUE 188
            # self.msegs_in = ("supporting_data", "stock_energy_tech_data",
            #                  "mseg_res_com_cz_2017.json")
            self.msegs_in = ("supporting_data", "stock_energy_tech_data",
                             "mseg_res_com_cz.json")
            # UNCOMMENT WITH ISSUE 188
            # self.msegs_cpl_in = ("supporting_data", "stock_energy_tech_data",
            #                      "cpl_res_com_cz_2017.json")
            self.msegs_cpl_in = ("supporting_data", "stock_energy_tech_data",
                                 "cpl_res_com_cz.json")
            self.iecc_reg_map = ("supporting_data", "convert_data", "geo_map",
                                 "IECC_AIA_ColSums.txt")
        elif regions == 'EMM':
            self.msegs_in = ("supporting_data", "stock_energy_tech_data",
                             "mseg_res_com_emm.json")
            self.msegs_cpl_in = ("supporting_data", "stock_energy_tech_data",
                                 "cpl_res_com_emm.gz")
            self.ash_emm_map = ("supporting_data", "convert_data", "geo_map",
                                "ASH_EMM_ColSums.txt")
            self.aia_altreg_map = ("supporting_data", "convert_data",
                                   "geo_map", "AIA_EMM_ColSums.txt")
            self.iecc_reg_map = ("supporting_data", "convert_data", "geo_map",
                                 "IECC_EMM_ColSums.txt")
            self.ss_data_altreg = ("supporting_data", "convert_data",
                                   "emm_region_emissions_prices-updated.json")
        elif regions == 'State':
            self.msegs_in = ("supporting_data", "stock_energy_tech_data",
                             "mseg_res_com_state.gz")
            self.msegs_cpl_in = ("supporting_data", "stock_energy_tech_data",
                                 "cpl_res_com_cdiv.json")
            self.aia_altreg_map = ("supporting_data", "convert_data",
                                   "geo_map", "AIA_State_ColSums.txt")
            self.iecc_reg_map = ("supporting_data", "convert_data", "geo_map",
                                 "IECC_State_ColSums.txt")
            self.ss_data_altreg = ("supporting_data", "convert_data",
                                   "state_emissions_prices-updated.json")
        else:
            raise ValueError("Unsupported regional breakout (" + regions + ")")

        self.metadata = "metadata.json"
        # UNCOMMENT WITH ISSUE 188
        # self.metadata = "metadata_2017.json"
        self.cost_convert_in = ("supporting_data", "convert_data",
                                "ecm_cost_convert.json")
        self.cbecs_sf_byvint = \
            ("supporting_data", "convert_data", "cbecs_sf_byvintage.json")
        self.indiv_ecms = "ecm_definitions"
        self.ecm_packages = ("ecm_definitions", "package_ecms.json")
        self.ecm_prep = ("supporting_data", "ecm_prep.json")
        self.ecm_compete_data = ("supporting_data", "ecm_competition_data")
        self.run_setup = "run_setup.json"
        self.cpi_data = ("supporting_data", "convert_data", "cpi.csv")
        # Use the user-specified captured energy method flag to determine
        # which site-source conversions file to select
        if capt_energy is True:
            self.ss_data = ("supporting_data", "convert_data",
                            "site_source_co2_conversions-ce.json")
        else:
            self.ss_data = ("supporting_data", "convert_data",
                            "site_source_co2_conversions.json")
        self.tsv_load_data = (
            "supporting_data", "tsv_data", "tsv_load.json")
        self.tsv_cost_data = (
            "supporting_data", "tsv_data", "tsv_cost.json")
        self.tsv_carbon_data = (
            "supporting_data", "tsv_data", "tsv_carbon.json")
        self.tsv_shape_data = (
            "ecm_definitions", "energyplus_data", "savings_shapes")
        self.tsv_metrics_data_tot_ref = (
            "supporting_data", "tsv_data", "tsv_hrs_tot_ref.csv")
        self.tsv_metrics_data_net_ref = (
            "supporting_data", "tsv_data", "tsv_hrs_net_ref.csv")
        self.tsv_metrics_data_tot_hr = (
            "supporting_data", "tsv_data", "tsv_hrs_tot_hr.csv")
        self.tsv_metrics_data_net_hr = (
            "supporting_data", "tsv_data", "tsv_hrs_net_hr.csv")
        self.health_data = (
            "supporting_data", "convert_data", "epa_costs.csv")
        # Set heating/cooling energy totals file conditional on: 1) regional
        # breakout used, and 2) whether site energy data, source energy data
        # (fossil equivalent site-source conversion), or source energy data
        # (captured energy site-source conversion) are needed; these data
        # are later used to work out overlaps across measures in a package
        if regions == "AIA":
            if site_energy is True:
                self.htcl_totals = (
                    "supporting_data", "stock_energy_tech_data",
                    "htcl_totals-site.json")
            elif capt_energy is not True:
                self.htcl_totals = (
                    "supporting_data", "stock_energy_tech_data",
                    "htcl_totals.json")
            elif capt_energy is True:
                self.htcl_totals = (
                    "supporting_data", "stock_energy_tech_data",
                    "htcl_totals-ce.json")
            else:
                raise ValueError(
                    "Unsupported energy output type (site, source "
                    "(fossil fuel equivalent), and source (captured "
                    "energy) are currently supported)")
        elif regions == "EMM":
            if site_energy is True:
                self.htcl_totals = (
                    "supporting_data", "stock_energy_tech_data",
                    "htcl_totals-site_emm.json")
            elif capt_energy is not True:
                self.htcl_totals = (
                    "supporting_data", "stock_energy_tech_data",
                    "htcl_totals_emm.json")
            elif capt_energy is True:
                self.htcl_totals = (
                    "supporting_data", "stock_energy_tech_data",
                    "htcl_totals-ce_emm.json")
            else:
                raise ValueError(
                    "Unsupported energy output type (site, source "
                    "(fossil fuel equivalent), and source (captured "
                    "energy) are currently supported)")
        elif regions == "State":
            if site_energy is True:
                self.htcl_totals = (
                    "supporting_data", "stock_energy_tech_data",
                    "htcl_totals-site_state.json")
            elif capt_energy is not True:
                self.htcl_totals = (
                    "supporting_data", "stock_energy_tech_data",
                    "htcl_totals_state.json")
            elif capt_energy is True:
                self.htcl_totals = (
                    "supporting_data", "stock_energy_tech_data",
                    "htcl_totals-ce_state.json")
            else:
                raise ValueError(
                    "Unsupported energy output type (site, source "
                    "(fossil fuel equivalent), and source (captured "
                    "energy) are currently supported)")
        else:
            raise ValueError("Unsupported regional breakout (" + regions + ")")


class UsefulVars(object):
    """Class of variables that are used globally across functions.

    Attributes:
        adopt_schemes (list): Possible consumer adoption scenarios.
        discount_rate (float): Rate to use in discounting costs/savings.
        retro_rate (float): Rate at which existing stock is retrofitted.
        nsamples (int): Number of samples to draw from probability distribution
            on measure inputs.
        regions (string): User region settings.
        aeo_years (list): Modeling time horizon.
        aeo_years_summary (list): Reduced set of snapshot years in the horizon.
        demand_tech (list): All demand-side heating/cooling technologies.
        zero_cost_tech (list): All baseline technologies with cost of zero.
        inverted_relperf_list (list) = Performance units that require
            an inverted relative performance calculation (e.g., an air change
            rate where lower numbers indicate higher performance).
        valid_submkt_urls (list) = Valid URLs for sub-market scaling fractions.
        consumer_price_ind (numpy.ndarray) = Historical Consumer Price Index.
        ss_conv (dict): Site-source conversion factors by fuel type.
        fuel_switch_conv (dict): Performance unit conversions for expected
            fuel switching cases.
        carb_int (dict): Carbon intensities by fuel type (MMTon/quad).
        ecosts (dict): Energy costs by building and fuel type ($/MMBtu).
        ccosts (dict): Carbon costs ($/MTon).
        com_timeprefs (dict): Commercial adoption time preference premiums.
        in_all_map (dict): Maps any user-defined measure inputs marked 'all' to
            list of climates, buildings, fuels, end uses, or technologies.
        valid_mktnames (list): List of all valid applicable baseline market
            input names for a measure.
        out_break_czones (OrderedDict): Maps measure climate zone names to
            the climate zone categories used in summarizing measure outputs.
        out_break_bldgtypes (OrderedDict): Maps measure building type names to
            the building sector categories used in summarizing measure outputs.
        out_break_enduses (OrderedDict): Maps measure end use names to
            the end use categories used in summarizing measure outputs.
        out_break_fuels (OrderedDict): Maps measure fuel types to electric vs.
            non-electric fuels (for heating, cooling, WH, and cooking).
        out_break_in (OrderedDict): Breaks out key measure results by
            climate zone, building sector, and end use.
        cconv_topkeys_map (dict): Maps measure cost units to top-level keys in
            an input cost conversion data dict.
        cconv_whlbldgkeys_map (dict): Maps measure cost units to whole
            building-level cost conversion dict keys.
        tech_units_rmv (list): Flags baseline performance units that cannot
            currently be handled, thus the associated segment must be removed.
        tech_units_map (dict): Maps baseline performance units to measure units
            in cases where the conversion is expected (e.g., EER to COP).
        cconv_htclkeys_map (dict): Maps measure cost units to cost conversion
            dict keys for the heating and cooling end uses.
        cconv_tech_htclsupply_map (dict): Maps measure cost units to cost
            conversion dict keys for supply-side heating/cooling technologies.
        cconv_tech_mltstage_map (dict): Maps measure cost units to cost
            conversion dict keys for demand-side heating/cooling
            technologies and controls technologies requiring multiple
            conversion steps (e.g., $/ft^2 glazing -> $/ft^2 wall ->
            $/ft^2 floor; $/node -> $/ft^2 floor -> $/unit).
        cconv_bybldg_units (list): Flags cost unit conversions that must
            be re-initiated for each new microsegment building type.
        cconv_bytech_units_res (list): Flags cost unit conversions that must
            be re-initiated for each new microsegment technology type (
            applies only to the residential sector, where conversions from
            $/ft^2 floor to $/unit depend on number of units per household,
            which varies according to technology type).
        res_typ_sf_household (dict): Typical household-level square footages,
            used to translate ECM costs from $/ft^2 floor to $/household.
        res_typ_units_household (dict): Typical number of technology units per
            household, used to translate ECM costs from $/household to the
            $/unit scale expected by the residential ECM competition approach
        deflt_choice (list): Residential technology choice capital/operating
            cost parameters to use when choice data are missing.
        regions (str): Regions to use in geographically breaking out the data.
        region_cpl_mapping (str or dict): Maps states to census divisions for
            the case where states are used; otherwise empty string.
        alt_perfcost_brk_map (dict): Mapping factors used to handle alternate
            regional breakouts in measure performance or cost units.
        months (str): Month sequence for accessing time-sensitive data.
        tsv_feature_types (list): Possible types of TSV features.
        tsv_climate_regions (list): Possible ASHRAE/IECC climate regions for
            time-sensitive analysis and metrics.
        tsv_nerc_regions (list): Possible NERC regions for time-sensitive data.
        tsv_metrics_data (str): Includes information on max/min net system load
            hours, peak/take net system load windows, and peak days by EMM
            region/season, as well as days of year to attribute to each season.
        tsv_hourly_price (dict): Dict for storing hourly price factors.
        tsv_hourly_emissions (dict): Dict for storing hourly emissions factors.
        tsv_hourly_lafs (dict): Dict for storing annual energy, cost, and
            carbon adjustment factors by region, building type, and end use.
        emm_name_num_map (dict): Maps EMM region names to EIA region numbers.
        cz_emm_map (dict): Maps climate zones to EMM region net system load
            shape data.
        health_scn_names (list): List of public health data scenario names.
        health_scn_data (numpy.ndarray): Public health cost data.
        htcl_totals (tuple): Heating/cooling energy totals by region,
            building type, and building structure type.
        heat_ls_tech_scrn (tuple): Heat gains to screen out of time-
            sensitive valuation for heating (no load shapes for these gains).
    """

    def __init__(self, base_dir, handyfiles, regions, tsv_metrics,
                 health_costs, split_fuel):
        # * DECARBONIZATION ANALYSIS: RESTRICT TO MAX ADOPTION POTENTIAL *
        self.adopt_schemes = ['Max adoption potential']
        self.discount_rate = 0.07
        self.retro_rate = 0.01
        self.nsamples = 100
        self.regions = regions
        # Load metadata including AEO year range
        with open(path.join(base_dir, handyfiles.metadata), 'r') as aeo_yrs:
            try:
                aeo_yrs = json.load(aeo_yrs)
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.metadata + "': " + str(e)) from None
        # # Set minimum AEO modeling year
        # aeo_min = aeo_yrs["min year"]
        # Set minimum year to current year
        aeo_min = datetime.today().year
        # Set maximum AEO modeling year
        aeo_max = aeo_yrs["max year"]
        # Derive time horizon from min/max years
        self.aeo_years = [
            str(i) for i in range(aeo_min, aeo_max + 1)]
        self.aeo_years_summary = ["2030", "2050"]
        self.demand_tech = [
            'roof', 'ground', 'lighting gain', 'windows conduction',
            'equipment gain', 'floor', 'infiltration', 'people gain',
            'windows solar', 'ventilation', 'other heat gain', 'wall']
        self.zero_cost_tech = ['infiltration']
        self.inverted_relperf_list = ["ACH", "CFM/ft^2 @ 0.3 in. w.c.",
                                      "kWh/yr", "kWh/day", "SHGC", "HP/CFM"]
        self.valid_submkt_urls = [
            '.eia.gov', '.doe.gov', '.energy.gov', '.data.gov',
            '.energystar.gov', '.epa.gov', '.census.gov', '.pnnl.gov',
            '.lbl.gov', '.nrel.gov', 'www.sciencedirect.com', 'www.costar.com',
            'www.navigantresearch.com']
        try:
            self.consumer_price_ind = numpy.genfromtxt(
                path.join(base_dir, *handyfiles.cpi_data),
                names=True, delimiter=',',
                dtype=[('DATE', 'U10'), ('VALUE', '<f8')])
        except ValueError as e:
            raise ValueError(
                "Error reading in '" +
                handyfiles.cpi_data + "': " + str(e)) from None
        # Read in national-level site-source, emissions, and costs data
        with open(path.join(base_dir, *handyfiles.ss_data), 'r') as ss:
            try:
                cost_ss_carb = json.load(ss)
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.ss_data + "': " + str(e)) from None
        # Set national site to source conversion factors
        self.ss_conv = {
            "electricity": cost_ss_carb[
                "electricity"]["site to source conversion"]["data"],
            "natural gas": {yr: 1 for yr in self.aeo_years},
            "distillate": {yr: 1 for yr in self.aeo_years},
            "other fuel": {yr: 1 for yr in self.aeo_years}}
        # Set electric emissions intensities and prices differently
        # depending on whether EMM regions are specified (use EMM-specific
        # data) or not (use national data)
        if self.regions in ["EMM", "State"]:
            # Read in EMM- or state-specific emissions factors and price data
            with open(path.join(base_dir,
                                *handyfiles.ss_data_altreg), 'r') as ss:
                try:
                    cost_ss_carb_altreg = json.load(ss)
                except ValueError as e:
                    raise ValueError(
                        "Error reading in '" +
                        handyfiles.ss_data_altreg + "': " + str(e)) from None
            # Initialize CO2 intensities based on electricity intensities by
            # EMM region or state; convert CO2 intensities from Mt/TWh site to
            # MMTon/MMBTu site to match expected multiplication by site energy
            self.carb_int = {bldg: {"electricity": {reg: {
                yr: round((cost_ss_carb_altreg["CO2 intensity of electricity"][
                    "data"][reg][yr] / 3412141.6331), 10) for
                yr in self.aeo_years} for reg in cost_ss_carb_altreg[
                    "CO2 intensity of electricity"]["data"].keys()}} for
                bldg in ["residential", "commercial"]}
            # Initialize energy costs based on electricity prices by EMM region
            # or state; convert prices from $/kWh site to $/MMBTu site to match
            # expected multiplication by site energy units
            self.ecosts = {bldg: {"electricity": {reg: {
                yr: round((cost_ss_carb_altreg["End-use electricity price"][
                    "data"][bldg][reg][yr] / 0.003412), 6) for
                yr in self.aeo_years} for reg in cost_ss_carb_altreg[
                    "End-use electricity price"]["data"][bldg].keys()}} for
                bldg in ["residential", "commercial"]}
        else:
            # Initialize CO2 intensities based on national CO2 intensities
            # for electricity; convert CO2 intensities from Mt/quad source to
            # Mt/MMBTu source to match expected multiplication by source energy
            self.carb_int = {bldg: {"electricity": {yr: cost_ss_carb[
                "electricity"]["CO2 intensity"]["data"][bldg][yr] /
                1000000000 for yr in self.aeo_years}} for bldg in [
                "residential", "commercial"]}
            # Initialize energy costs based on national electricity prices; no
            # conversion needed as the prices will be multiplied by MMBtu
            # source energy units and are already in units of $/MMBtu source
            self.ecosts = {bldg: {"electricity": {yr: cost_ss_carb[
                "electricity"]["price"]["data"][bldg][yr] for
                yr in self.aeo_years}} for bldg in [
                "residential", "commercial"]}
        # Pull non-electric CO2 intensities and energy prices and update
        # the CO2 intensity and energy cost dicts initialized above
        # accordingly; convert CO2 intensities from Mt/quad source to
        # Mt/MMBTu source to match expected multiplication by source energy;
        # price data are already in units of $/MMBtu source and do not require
        # further conversion
        carb_int_nonelec = {bldg: {fuel: {yr: (
            cost_ss_carb[fuel_map]["CO2 intensity"]["data"][
                bldg][yr] / 1000000000) for yr in self.aeo_years}
                for fuel, fuel_map in zip(
                ["natural gas", "distillate", "other fuel"],
                ["natural gas", "other", "other"])
            } for bldg in ["residential", "commercial"]}
        ecosts_nonelec = {bldg: {fuel: {yr: cost_ss_carb[
            fuel_map]["price"]["data"][bldg][yr] for yr in
            self.aeo_years} for fuel, fuel_map in zip([
                "natural gas", "distillate", "other fuel"], [
                "natural gas", "other", "other"])} for bldg in [
            "residential", "commercial"]}
        for bldg in ["residential", "commercial"]:
            self.carb_int[bldg].update(carb_int_nonelec[bldg])
            self.ecosts[bldg].update(ecosts_nonelec[bldg])
        # Set carbon costs
        ccosts_init = cost_ss_carb["CO2 price"]["data"]
        # Multiply carbon costs by 1000000 to reflect
        # conversion from import units of $/MTon to $/MMTon
        self.ccosts = {
            yr_key: (ccosts_init[yr_key] * 1000000) for
            yr_key in self.aeo_years}
        self.com_timeprefs = {
            "rates": [10.0, 1.0, 0.45, 0.25, 0.15, 0.065, 0.0],
            "distributions": {
                "heating": {
                    key: [0.265, 0.226, 0.196, 0.192, 0.105, 0.013, 0.003]
                    for key in self.aeo_years},
                "cooling": {
                    key: [0.264, 0.225, 0.193, 0.192, 0.106, 0.016, 0.004]
                    for key in self.aeo_years},
                "water heating": {
                    key: [0.263, 0.249, 0.212, 0.169, 0.097, 0.006, 0.004]
                    for key in self.aeo_years},
                "ventilation": {
                    key: [0.265, 0.226, 0.196, 0.192, 0.105, 0.013, 0.003]
                    for key in self.aeo_years},
                "cooking": {
                    key: [0.261, 0.248, 0.214, 0.171, 0.097, 0.005, 0.004]
                    for key in self.aeo_years},
                "lighting": {
                    key: [0.264, 0.225, 0.193, 0.193, 0.085, 0.013, 0.027]
                    for key in self.aeo_years},
                "refrigeration": {
                    key: [0.262, 0.248, 0.213, 0.170, 0.097, 0.006, 0.004]
                    for key in self.aeo_years}}}
        # Set valid region names and regional output categories
        if regions == "AIA":
            valid_regions = [
             "AIA_CZ1", "AIA_CZ2", "AIA_CZ3", "AIA_CZ4", "AIA_CZ5"]
            regions_out = [
                ('AIA CZ1', 'AIA_CZ1'), ('AIA CZ2', 'AIA_CZ2'),
                ('AIA CZ3', 'AIA_CZ3'), ('AIA CZ4', 'AIA_CZ4'),
                ('AIA CZ5', 'AIA_CZ5')]
            self.region_cpl_mapping = ''
            # Read in mapping for alternate performance/cost unit breakouts
            # IECC -> AIA mapping
            try:
                iecc_reg_map = numpy.genfromtxt(
                    path.join(base_dir, *handyfiles.iecc_reg_map),
                    names=True, delimiter='\t', dtype=(
                        ['<U25'] * 1 + ['<f8'] * len(valid_regions)))
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.iecc_reg_map + "': " + str(e)) from None
            # Store alternate breakout mapping in dict for later use
            self.alt_perfcost_brk_map = {
                "IECC": iecc_reg_map, "levels": str([
                    "IECC_CZ" + str(n + 1) for n in range(8)])}
        elif regions in ["EMM", "State"]:
            if regions == "EMM":
                valid_regions = [
                    'TRE', 'FRCC', 'MISW', 'MISC', 'MISE', 'MISS',
                    'ISNE', 'NYCW', 'NYUP', 'PJME', 'PJMW', 'PJMC',
                    'PJMD', 'SRCA', 'SRSE', 'SRCE', 'SPPS', 'SPPC',
                    'SPPN', 'SRSG', 'CANO', 'CASO', 'NWPP', 'RMRG', 'BASN']
                self.region_cpl_mapping = ''
                try:
                    self.ash_emm_map = numpy.genfromtxt(
                        path.join(base_dir, *handyfiles.ash_emm_map),
                        names=True, delimiter='\t', dtype=(
                            ['<U25'] * 1 + ['<f8'] * len(valid_regions)))
                except ValueError as e:
                    raise ValueError(
                        "Error reading in '" +
                        handyfiles.ash_emm_map + "': " + str(e)) from None
            else:
                # Note: for now, exclude AK and HI
                valid_regions = [
                    'AL', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
                    'GA', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
                    'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
                    'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
                    'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI',
                    'WY']
                self.region_cpl_mapping = {
                    "new england": ['CT', 'MA', 'ME', 'NH', 'RI', 'VT'],
                    "mid atlantic": ['NJ', 'NY', 'PA'],
                    "east north central": ['IL', 'IN', 'MI', 'OH', 'WI'],
                    "west north central": [
                        'IA', 'KS', 'MN', 'MO', 'ND', 'NE', 'SD'],
                    "south atlantic": [
                        'DC', 'DE', 'FL', 'GA', 'MD', 'NC', 'SC', 'VA', 'WV'],
                    "east south central": ['AL', 'KY', 'MS', 'TN'],
                    "west south central": ['AR', 'LA', 'OK', 'TX'],
                    "mountain": [
                        'AZ', 'CO', 'ID', 'MT', 'NM', 'NV', 'UT', 'WY'],
                    "pacific": ['AK', 'CA', 'HI', 'OR', 'WA']}
            regions_out = [(x, x) for x in valid_regions]

            # Read in mapping for alternate performance/cost unit breakouts
            # AIA -> EMM or State mapping
            try:
                aia_altreg_map = numpy.genfromtxt(
                    path.join(base_dir, *handyfiles.aia_altreg_map),
                    names=True, delimiter='\t', dtype=(
                        ['<U25'] * 1 + ['<f8'] * len(valid_regions)))
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.aia_altreg_map + "': " + str(e)) from None
            # IECC -> EMM or State mapping
            try:
                iecc_altreg_map = numpy.genfromtxt(
                    path.join(base_dir, *handyfiles.iecc_reg_map),
                    names=True, delimiter='\t', dtype=(
                        ['<U25'] * 1 + ['<f8'] * len(valid_regions)))
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.iecc_reg_map + "': " + str(e)) from None
            # Store alternate breakout mapping in dict for later use
            self.alt_perfcost_brk_map = {
                "IECC": iecc_altreg_map, "AIA": aia_altreg_map,
                "levels": str([
                    "IECC_CZ" + str(n + 1) for n in range(8)]) + " 0R " + str([
                        "AIA_CZ" + str(n + 1) for n in range(5)])}
        self.months = ["january", "february", "march", "april", "may", "june",
                       "july", "august", "september", "october", "november",
                       "december"]
        self.in_all_map = {
            "climate_zone": valid_regions,
            "bldg_type": {
                "residential": [
                    "single family home", "multi family home", "mobile home"],
                "commercial": [
                    "assembly", "education", "food sales", "food service",
                    "health care", "lodging", "large office", "small office",
                    "mercantile/service", "warehouse", "other"]},
            "structure_type": ["new", "existing"],
            "fuel_type": {
                "residential": [
                    "electricity", "natural gas", "distillate", "other fuel"],
                "commercial": [
                    "electricity", "natural gas", "distillate"]},
            "end_use": {
                "residential": {
                    "electricity": [
                        'drying', 'other', 'water heating',
                        'cooling', 'cooking', 'computers', 'lighting',
                        'secondary heating', 'TVs', 'heating', 'refrigeration',
                        'fans and pumps', 'ceiling fan'],
                    "natural gas": [
                        'drying', 'water heating', 'cooling', 'heating',
                        'cooking', 'secondary heating', 'other'],
                    "distillate": [
                        'water heating', 'heating', 'secondary heating',
                        'other'],
                    "other fuel": [
                        'water heating', 'cooking', 'heating',
                        'secondary heating', 'other']},
                "commercial": {
                    "electricity": [
                        'ventilation', 'water heating', 'cooling',
                        'heating', 'refrigeration', 'MELs',
                        'non-PC office equipment', 'PCs', 'lighting',
                        'cooking'],
                    "natural gas": [
                        'cooling', 'water heating', 'cooking', 'heating'],
                    "distillate": ['water heating', 'heating']}},
            "technology": {
                "residential": {
                    "supply": {
                        "electricity": {
                            'other': [
                                'dishwasher', 'clothes washing', 'freezers',
                                'rechargeables', 'coffee maker',
                                'dehumidifier', 'electric other',
                                'microwave', 'pool heaters and pumps',
                                'security system', 'portable electric spas',
                                'wine coolers'],
                            'water heating': ['solar WH', 'electric WH'],
                            'cooling': [
                                'room AC', 'ASHP', 'GSHP', 'central AC'],
                            'computers': [
                                'desktop PC', 'laptop PC', 'network equipment',
                                'monitors'],
                            'lighting': [
                                'linear fluorescent (T-8)',
                                'linear fluorescent (T-12)',
                                'reflector (LED)', 'general service (CFL)',
                                'external (high pressure sodium)',
                                'general service (incandescent)',
                                'external (CFL)',
                                'external (LED)', 'reflector (CFL)',
                                'reflector (incandescent)',
                                'general service (LED)',
                                'external (incandescent)',
                                'linear fluorescent (LED)',
                                'reflector (halogen)'],
                            'secondary heating': ['secondary heater'],
                            'TVs': [
                                'home theater and audio', 'set top box',
                                'video game consoles', 'DVD', 'TV'],
                            'heating': ['GSHP', 'resistance heat', 'ASHP'],
                            'ceiling fan': [None],
                            'fans and pumps': [None],
                            'refrigeration': [None],
                            'drying': [None],
                            'cooking': [None]},
                        "natural gas": {
                            'cooling': ['NGHP'],
                            'heating': ['furnace (NG)', 'NGHP', 'boiler (NG)'],
                            'secondary heating': ['secondary heater'],
                            'drying': [None],
                            'water heating': [None],
                            'cooking': [None],
                            'other': ["other appliances"]},
                        "distillate": {
                            'heating': [
                                'boiler (distillate)', 'furnace (distillate)'],
                            'secondary heating': ['secondary heater'],
                            'water heating': [None],
                            'other': ["other appliances"]},
                        "other fuel": {
                            'heating': [
                                'resistance', 'furnace (kerosene)',
                                'stove (wood)', 'furnace (LPG)'],
                            'secondary heating': [
                                'secondary heater (wood)',
                                'secondary heater (coal)',
                                'secondary heater (kerosene)',
                                'secondary heater (LPG)'],
                            'cooking': [None],
                            'water heating': [None],
                            'other': ["other appliances"]}},
                    "demand": [
                        'roof', 'ground', 'windows solar',
                        'windows conduction', 'equipment gain',
                        'people gain', 'wall', 'infiltration']},
                "commercial": {
                    "supply": {
                        "electricity": {
                            'ventilation': ['VAV_Vent', 'CAV_Vent'],
                            'water heating': [
                                'Solar water heater', 'HP water heater',
                                'elec_booster_water_heater',
                                'elec_water_heater'],
                            'cooling': [
                                'rooftop_AC', 'scroll_chiller',
                                'res_type_central_AC', 'reciprocating_chiller',
                                'comm_GSHP-cool', 'centrifugal_chiller',
                                'rooftop_ASHP-cool', 'wall-window_room_AC',
                                'screw_chiller'],
                            'heating': [
                                'electric_res-heat', 'comm_GSHP-heat',
                                'rooftop_ASHP-heat', 'elec_boiler'],
                            'refrigeration': [
                                'Commercial Beverage Merchandisers',
                                'Commercial Compressor Rack Systems',
                                'Commercial Condensers',
                                'Commercial Ice Machines',
                                'Commercial Reach-In Freezers',
                                'Commercial Reach-In Refrigerators',
                                'Commercial Refrigerated Vending Machines',
                                'Commercial Supermarket Display Cases',
                                'Commercial Walk-In Freezers',
                                'Commercial Walk-In Refrigerators'],
                            'MELs': [
                                'elevators', 'escalators', 'coffee brewers',
                                'kitchen ventilation', 'laundry',
                                'lab fridges and freezers', 'fume hoods',
                                'medical imaging', 'large video boards',
                                'shredders', 'private branch exchanges',
                                'voice-over-IP telecom', 'IT equipment',
                                'office UPS', 'data center UPS',
                                'security systems',
                                'distribution transformers',
                                'non-road electric vehicles'
                            ],
                            'lighting': [
                                '100W A19 Incandescent',
                                '100W Equivalent A19 Halogen',
                                '100W Equivalent CFL Bare Spiral',
                                '100W Equivalent LED A Lamp',
                                'Halogen Infrared Reflector (HIR) PAR38',
                                'Halogen PAR38',
                                'LED Integrated Luminaire',
                                'LED PAR38',
                                'Mercury Vapor',
                                'Metal Halide',
                                'Sodium Vapor',
                                'T5 4xF54 HO High Bay',
                                'T5 F28',
                                'T8 F28',
                                'T8 F32',
                                'T8 F59',
                                'T8 F96'
                            ],
                            'cooking': [
                                'electric_range_oven_24x24_griddle'],
                            'PCs': [None],
                            'non-PC office equipment': [None]},
                        "natural gas": {
                            'cooling': [
                                'gas_eng-driven_RTAC', 'gas_chiller',
                                'res_type_gasHP-cool',
                                'gas_eng-driven_RTHP-cool'],
                            'water heating': [
                                'gas_water_heater', 'gas_instantaneous_WH',
                                'gas_booster_WH'],
                            'cooking': [
                                'gas_range_oven_24x24_griddle'],
                            'heating': [
                                'gas_eng-driven_RTHP-heat',
                                'res_type_gasHP-heat', 'gas_boiler',
                                'gas_furnace']},
                        "distillate": {
                            'water heating': ['oil_water_heater'],
                            'heating': ['oil_boiler', 'oil_furnace']}},
                    "demand": [
                        'roof', 'ground', 'lighting gain',
                        'windows conduction', 'equipment gain',
                        'floor', 'infiltration', 'people gain',
                        'windows solar', 'ventilation',
                        'other heat gain', 'wall']}}}
        # Find the full set of valid names for describing a measure's
        # applicable baseline that do not begin with 'all'
        mktnames_non_all = self.append_keyvals(
            self.in_all_map, keyval_list=[]) + ['supply', 'demand']
        # Find the full set of valid names for describing a measure's
        # applicable baseline that do begin with 'all'
        mktnames_all_init = ["all", "all residential", "all commercial"] + \
            self.append_keyvals(self.in_all_map["end_use"], keyval_list=[])
        mktnames_all = ['all ' + x if 'all' not in x else x for
                        x in mktnames_all_init]
        self.valid_mktnames = mktnames_non_all + mktnames_all
        self.out_break_czones = OrderedDict(regions_out)
        self.out_break_bldgtypes = OrderedDict([
            ('Residential (New)', [
                'new', 'single family home', 'multi family home',
                'mobile home']),
            ('Residential (Existing)', [
                'existing', 'single family home', 'multi family home',
                'mobile home'],),
            ('Commercial (New)', [
                'new', 'assembly', 'education', 'food sales',
                'food service', 'health care', 'mercantile/service',
                'lodging', 'large office', 'small office', 'warehouse',
                'other']),
            ('Commercial (Existing)', [
                'existing', 'assembly', 'education', 'food sales',
                'food service', 'health care', 'mercantile/service',
                'lodging', 'large office', 'small office', 'warehouse',
                'other'])])
        self.out_break_enduses = OrderedDict([
            ('Heating (Equip.)', ["heating", "secondary heating"]),
            ('Cooling (Equip.)', ["cooling"]),
            ('Heating (Env.)', ["heating", "secondary heating"]),
            ('Cooling (Env.)', ["cooling"]),
            ('Ventilation', ["ventilation"]),
            ('Lighting', ["lighting"]),
            ('Water Heating', ["water heating"]),
            ('Refrigeration', ["refrigeration", "other"]),
            ('Cooking', ["cooking"]),
            ('Computers and Electronics', [
                "PCs", "non-PC office equipment", "TVs", "computers"]),
            ('Other', [
                "drying", "ceiling fan", "fans and pumps",
                "MELs", "other"])])
        # Configure output breakouts for fuel type if user has set this option
        if split_fuel is True:
            self.out_break_fuels = OrderedDict([
                ('Electric', ["electricity"]),
                ('Non-Electric', ["natural gas", "distillate", "other fuel"])])
        else:
            self.out_break_fuels = {}
        # Use the above output categories to establish a dictionary with blank
        # values at terminal leaf nodes; this dict will eventually store
        # partitioning fractions needed to breakout the measure results
        # Determine all possible outcome category combinations
        out_levels = [
            self.out_break_czones.keys(), self.out_break_bldgtypes.keys(),
            self.out_break_enduses.keys()]
        out_levels_keys = list(itertools.product(*out_levels))
        # Create dictionary using outcome category combinations as key chains
        self.out_break_in = OrderedDict()
        for kc in out_levels_keys:
            current_level = self.out_break_in
            for ind, elem in enumerate(kc):
                # If fuel splits are desired and applicable for the current
                # end use breakout, add the fuel splits to the dict vals
                if len(self.out_break_fuels.keys()) != 0 and (elem in [
                    "Heating (Equip.)", "Cooling (Equip.)", "Heating (Env.)",
                    "Cooling (Env.)", "Water Heating", "Cooking"]) and \
                        elem not in current_level:
                    current_level[elem] = OrderedDict(
                        [(x, OrderedDict()) for x in
                         self.out_break_fuels.keys()])
                # Otherwise, set dict vals to another empty dict
                elif elem not in current_level:
                    current_level[elem] = OrderedDict()
                current_level = current_level[elem]
        self.cconv_bybldg_units = [
            "$/ft^2 glazing", "$/ft^2 roof", "$/ft^2 wall",
            "$/ft^2 footprint", "$/ft^2 floor", "$/occupant", "$/node"]
        self.cconv_bytech_units_res = ["$/ft^2 floor", "$/occupant", "$/node"]
        self.cconv_topkeys_map = {
            "whole building": ["$/ft^2 floor", "$/node", "$/occupant"],
            "heating and cooling": [
                "$/kBtu/h heating", "$/kBtu/h cooling", "$/ft^2 glazing",
                "$/ft^2 roof", "$/ft^2 wall", "$/ft^2 footprint"],
            "ventilation": ["$/1000 CFM"],
            "lighting": ["$/1000 lm"],
            "water heating": ["$/kBtu/h water heating"],
            "refrigeration": ["$/kBtu/h refrigeration"],
            "cooking": ["$/kBtu/h cooking"],
            "PCs": ["$/computer"]}
        self.cconv_htclkeys_map = {
            "supply": [
                "$/kBtu/h heating", "$/kBtu/h cooling"],
            "demand": [
                "$/ft^2 glazing", "$/ft^2 roof",
                "$/ft^2 wall", "$/ft^2 footprint"]}
        self.cconv_tech_htclsupply_map = {
            "heating equipment": ["$/kBtu/h heating"],
            "cooling equipment": ["$/kBtu/h cooling"]}
        self.cconv_tech_mltstage_map = {
            "windows": {
                "key": ["$/ft^2 glazing"],
                "conversion stages": ["windows", "walls"]},
            "roof": {
                "key": ["$/ft^2 roof"],
                "conversion stages": ["roof", "footprint"]},
            "walls": {
                "key": ["$/ft^2 wall"],
                "conversion stages": ["walls"]},
            "footprint": {
                "key": ["$/ft^2 footprint"],
                "conversion stages": ["footprint"]}}
        self.cconv_whlbldgkeys_map = {
            "wireless sensor network": ["$/node"],
            "occupant-centered sensing and controls": ["$/occupant"]}
        self.tech_units_rmv = ["HHV"]
        # Note: EF handling for ECMs written before scout v0.5 (AEO 2019)
        self.tech_units_map = {
            "COP": {"AFUE": 1, "EER": 0.2930712},
            "AFUE": {"COP": 1}, "UEF": {"SEF": 1},
            "EF": {"UEF": 1, "SEF": 1, "CEF": 1},
            "SEF": {"UEF": 1}}
        # Typical household square footages based on RECS 2015 Table HC 1.10,
        # "Total square footage of U.S. homes, 2015"; divide total square
        # footage for each housing type by total number of homes for each
        # housing type (combine single family detached/attached into single
        # family home, combine apartments with 2-4 and 5 or more units into
        # multi family home)
        self.res_typ_sf_household = {
            "single family home": 2491, "mobile home": 1176,
            "multi family home": 882}
        # Typical number of lighting units per household based on RECS 2015
        # Table HC 5.1, "Lighting in U.S. homes by housing unit type, 2015";
        # take the median value for each bin in the table rows (e.g., for
        # bin 0-20 lights, median is 10), and compute a housing unit-weighted
        # sum across all the bins and housing types (combine single family
        # detached/attached into single family home, combine apartments with
        # 2-4 and 5 or more units into multi family home). Assume one unit
        # per household for all other technologies; note that windows are
        # included in this assumption (homeowners install/replace multiple
        # windows at once as one 'unit').
        self.res_typ_units_household = {
            "lighting": {"single family home": 36, "mobile home": 18,
                         "multi family home": 15},
            "all other technologies": 1}
        # Assume that missing technology choice parameters come from the
        # appliances/MELs areas; default is thus the EIA choice parameters
        # for refrigerator technologies
        self.deflt_choice = [-0.01, -0.12]

        # Set valid types of TSV feature types
        self.tsv_feature_types = ["shed", "shift", "shape"]

        # Use EMM region setting as a proxy for desired time-sensitive
        # valuation (TSV) and associated need to initialize handy TSV variables
        if regions == "EMM":
            self.tsv_climate_regions = [
                "2A", "2B", "3A", "3B", "3C", "4A", "4B",
                "4C", "5A", "5B", "5C", "6A", "6B", "7"]
            self.tsv_nerc_regions = [
                "FRCC", "MRO", "NPCC", "RFC", "SERC", "SPP", "TRE", "WECC"]
            # Set a dict that maps each ASH climate zone to an EMM region
            # in the climate zone with the most representative set of
            # min/max system load hour and peak/take system load hour
            # windows to use for that climate zone. For most climates, two
            # of these representative regions is assumed to account for
            # varying types of renewable mixes (e.g., high solar vs. low
            # solar, which yield differences in net load shapes and net
            # peak/take periods). In these cases, the terminal value is
            # formatted as a list with the EMM region number with the
            # representative load hour data stored in the first element,
            # and all other EMM regions in the climate that are covered
            # by that representative load hour data stored in the second
            # element. NOTE: the selection of representative EMM regions
            # for each ASH region is based on the plots found here:
            # https://drive.google.com/drive/folders/
            # 1JSoQb78LgooUD_uXqBOzAC7Nl7eLJZnc?usp=sharing
            self.cz_emm_map = {
                "2A": {
                    "set 1": [2, (1, 2, 17)],
                    "set 2": [6, (6, 15)]},
                "2B": {
                    "set 1": [20, (1, 20)]},
                "3A": {
                    "set 1": [15, (6, 13, 14, 15, 16)],
                    "set 2": [1, (1, 17)]},
                "3B": {
                    "set 1": [22, (21, 22)],
                    "set 2": [25, (1, 17, 20, 25)]},
                "3C": {
                    "set 1": [21, (21, 22)]},
                "4A": {
                    "set 1": [10, (4, 8, 10, 11, 17, 18)],
                    "set 2": [16, (6, 13, 14, 15, 16)]},
                "4B": {
                    "set 1": [20, (1, 17, 20, 24)],
                    "set 2": [21, (21, 22)]},
                "4C": {
                    "set 1": [23, (23,)],
                    "set 2": [21, (21,)]},
                "5A": {
                    "set 1": [11, (3, 4, 7, 9, 10, 11, 18, 19, 24)],
                    "set 2": [5, (5, 12, 14)]},
                "5B": {
                    "set 1": [24, (20, 23, 24, 25)],
                    "set 2": [21, (21,)]},
                "5C": {
                    "set 1": [23, (23,)]},
                "6A": {
                    "set 1": [3, (3, 5, 19)],
                    "set 2": [7, (7, 9, 10, 24)]},
                "6B": {
                    "set 1": [23, (3, 19, 23, 24, 25)],
                    "set 2": [22, (21, 22)]},
                "7": {
                    "set 1": [3, (3, 19)],
                    "set 2": [24, (7, 24, 25)]}}
            if tsv_metrics is not None:
                # Develop weekend day flags
                wknd_day_flags = [0 for n in range(365)]
                current_wkdy = 1
                for d in range(365):
                    # Flag weekend day
                    if current_wkdy in [1, 7]:
                        wknd_day_flags[d] = 1
                    # Advance day of week by one unless Saturday (7), in which
                    # case day switches back to 1 (Sunday)
                    if current_wkdy <= 6:
                        current_wkdy += 1
                    else:
                        current_wkdy = 1

                # Develop lists with seasonal day of year ranges, both with and
                # without weekends

                # Summer days of year
                sum_days = list(range(152, 274))
                sum_days_wkdy = [
                    x for x in sum_days if wknd_day_flags[(x - 1)] != 1]
                sum_days_wknd = [
                    x for x in sum_days if wknd_day_flags[(x - 1)] == 1]
                # Winter days of year
                wint_days = (list(
                            range(1, 91)) + list(range(335, 366)))
                wint_days_wkdy = [
                    x for x in wint_days if wknd_day_flags[(x - 1)] != 1]
                wint_days_wknd = [
                    x for x in wint_days if wknd_day_flags[(x - 1)] == 1]
                # Intermediate days of year
                inter_days = (list(
                            range(91, 152)) + list(range(274, 335)))
                inter_days_wkdy = [
                    x for x in inter_days if wknd_day_flags[(x - 1)] != 1]
                inter_days_wknd = [
                    x for x in inter_days if wknd_day_flags[(x - 1)] == 1]

                # Set column names for a dataset that includes information on
                # max/min net system load hours and peak/take net system load
                # hour windows by season and EMM region
                peak_take_names = (
                    "Region", "Year", "SummerMaxHr", "SummerMinHr",
                    "SummerPeakStartHr", "SummerPeakEndHr",
                    "SummerTakeStartHr1", "SummerTakeEndHr1",
                    "SummerTakeStartHr2", "SummerTakeEndHr2",
                    "SummerTakeStartHr3", "SummerTakeEndHr3",
                    "WinterMaxHr", "WinterMinHr",
                    "WinterPeakStartHr", "WinterPeakEndHr",
                    "WinterTakeStartHr1", "WinterTakeEndHr1",
                    "WinterTakeStartHr2", "WinterTakeEndHr2",
                    "WinterTakeStartHr3", "WinterTakeEndHr3",
                    "InterMaxHr", "InterMinHr",
                    "InterPeakStartHr", "InterPeakEndHr",
                    "InterTakeStartHr1", "InterTakeEndHr1",
                    "InterTakeStartHr2", "InterTakeEndHr2",
                    "InterTakeStartHr3", "InterTakeEndHr3")

                # Choose the appropriate data to use in determining peak/take
                # windows (total vs. net system load under reference vs. "Low
                # Renewable Cost" supply-side AEO case)
                if tsv_metrics[-2] == "1":
                    metrics_data = handyfiles.tsv_metrics_data_tot_ref
                elif tsv_metrics[-2] == "2":
                    metrics_data = handyfiles.tsv_metrics_data_tot_hr
                elif tsv_metrics[-2] == "3":
                    metrics_data = handyfiles.tsv_metrics_data_net_ref
                else:
                    metrics_data = handyfiles.tsv_metrics_data_net_hr

                # Import system max/min and peak/take hour load by EMM region
                sysload_dat = numpy.genfromtxt(
                        path.join(base_dir, *metrics_data),
                        names=peak_take_names, delimiter=',', dtype="<i4",
                        encoding="latin1", skip_header=1)
                # Find unique set of projection years in system peak/take data
                sysload_dat_yrs = numpy.unique(sysload_dat["Year"])
                # Set a dict that maps EMM region names to region
                # numbers as defined by EIA
                # (https://www.eia.gov/outlooks/aeo/pdf/f2.pdf)
                self.emm_name_num_map = {
                    name: (ind + 1) for ind, name in enumerate(valid_regions)}
                # Initialize a set of dicts that will store representative
                # system load data for the summer, winter, and intermediate
                # seasons by projection year
                sysld_sum, sysld_wint, sysld_int = ({
                    str(yr): {key: {key_sub: None for
                              key_sub in self.cz_emm_map[key].keys()} if
                              type(self.cz_emm_map[key]) is dict else None
                              for key in self.cz_emm_map.keys()} for yr in
                    sysload_dat_yrs} for n in range(3))
                # Fill in the dicts with seasonal system load data by year
                # Loop through all projection years available in the system
                # peak/take period data
                for sys_yr in sysload_dat_yrs:
                    # Convert projection year to string for dict keys
                    sys_yr_str = str(sys_yr)
                    sysload_dat_yr = sysload_dat[
                        numpy.where((sysload_dat["Year"] == sys_yr))]
                    # Loop through all climate zones
                    for cz in self.cz_emm_map.keys():
                        # Handle climate zones with one representative system
                        # load shape differently than those with more than one
                        # such shape
                        if type(self.cz_emm_map[cz]) == int:
                            # Fill in seasonal system load data
                            sysld_sum[sys_yr_str][cz], \
                                sysld_wint[sys_yr_str][cz], \
                                sysld_int[sys_yr_str][cz] = self.set_peak_take(
                                    sysload_dat_yr, self.cz_emm_map[cz])
                        else:
                            # Loop through the multiple EMM regions with
                            # representative system load data for the current
                            # climate zone
                            for set_v in self.cz_emm_map[cz].keys():
                                # Fill in seasonal system load data
                                sysld_sum[sys_yr_str][cz][set_v], \
                                    sysld_wint[sys_yr_str][cz][set_v], \
                                    sysld_int[sys_yr_str][cz][set_v] = \
                                    self.set_peak_take(
                                        sysload_dat_yr,
                                        self.cz_emm_map[cz][set_v][0])
                self.tsv_metrics_data = {
                    "season days": {
                        "all": {
                            "summer": sum_days,
                            "winter": wint_days,
                            "intermediate": inter_days
                        },
                        "weekdays": {
                            "summer": sum_days_wkdy,
                            "winter": wint_days_wkdy,
                            "intermediate": inter_days_wkdy

                        },
                        "weekends": {
                            "summer": sum_days_wknd,
                            "winter": wint_days_wknd,
                            "intermediate": inter_days_wknd

                        }
                    },
                    "system load hours": {
                        "summer": sysld_sum,
                        "winter": sysld_wint,
                        "intermediate": sysld_int
                    },
                    "peak days": {
                        "summer": {
                            "2A": 199,
                            "2B": 186,
                            "3A": 192,
                            "3B": 171,
                            "3C": 220,
                            "4A": 192,
                            "4B": 206,
                            "4C": 241,
                            "5A": 199,
                            "5B": 178,
                            "5C": 206,
                            "6A": 186,
                            "6B": 220,
                            "7": 206},
                        "winter": {
                            "2A": 24,
                            "2B": 17,
                            "3A": 31,
                            "3B": 10,
                            "3C": 10,
                            "4A": 31,
                            "4B": 339,
                            "4C": 38,
                            "5A": 26,
                            "5B": 10,
                            "5C": 12,
                            "6A": 10,
                            "6B": 17,
                            "7": 31}
                    },
                    "hourly index": list(enumerate(
                        itertools.product(range(365), range(24))))
                }
            else:
                self.tsv_metrics_data = None
                self.emm_name_num_map = {
                    name: (ind + 1) for ind, name in enumerate(valid_regions)}
            self.tsv_hourly_price, self.tsv_hourly_emissions = ({
                reg: None for reg in valid_regions
            } for n in range(2))

            self.tsv_hourly_lafs = {
                reg: {
                    "residential": {
                        bldg: {
                            eu: None for eu in self.in_all_map[
                                "end_use"]["residential"]["electricity"]
                        } for bldg in self.in_all_map[
                            "bldg_type"]["residential"]
                    },
                    "commercial": {
                        bldg: {
                            eu: None for eu in self.in_all_map[
                                "end_use"]["commercial"]["electricity"]
                        } for bldg in self.in_all_map[
                            "bldg_type"]["commercial"]
                    }
                } for reg in valid_regions
            }
        else:
            self.tsv_hourly_lafs = None

        # Condition health data scenario initialization on whether user
        # has requested that public health costs be accounted for
        if health_costs is True:
            # For each health data scenario, set the intended measure name
            # appendage (tuple element 1), type of efficiency to attach health
            # benefits to (element 2), and column in the data file from which
            # to retrieve these benefit values (element 3)
            self.health_scn_names = [
                ("PHC-EE (low)", "Uniform EE", "2017cents_kWh_7pct_low"),
                ("PHC-EE (high)", "Uniform EE", "2017cents_kWh_3pct_high")]
            # Set data file with public health benefits information
            self.health_scn_data = numpy.genfromtxt(
                    path.join(base_dir, *handyfiles.health_data),
                    names=("AVERT_Region", "EMM_Region", "Category",
                           "2017cents_kWh_3pct_low", "2017cents_kWh_3pct_high",
                           "2017cents_kWh_7pct_low",
                           "2017cents_kWh_7pct_high"),
                    delimiter=',', dtype=(['<U25'] * 3 + ['<f8'] * 4))
        # Import total absolute heating and cooling energy use data, used in
        # removing overlaps between equipment and envelope heating/cooling
        # contributing ECMs in the packaging operations
        with open(path.join(base_dir, *handyfiles.htcl_totals), 'r') as msi:
            try:
                self.htcl_totals = json.load(msi)
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.htcl_totals + "': " + str(e)) from None
        self.heat_ls_tech_scrn = (
            "windows solar", "equipment gain", "people gain",
            "other heat gain")

    def set_peak_take(self, sysload_dat, restrict_key):
        """Fill in dicts with seasonal system load shape data.

            Args:
                sysload_dat (numpy.ndarray): System load shape data.
                restrict_key (int): EMM region to restrict net load data to.

            Returns:
                Appropriate min/max net system load hour and peak/take net
                system load hour window data for the EMM region of interest,
                stored in dicts that are distinguished by season.
        """

        # Restrict net system load data to the representative EMM region for
        # the current climate zone
        peak_take_cz = sysload_dat[numpy.where(
            (sysload_dat["Region"] == restrict_key))]
        # Set summer max load hour, min load hour, and peak/take windows
        sum_peak_take = {
            "max": peak_take_cz["SummerMaxHr"][0],
            "min": peak_take_cz["SummerMinHr"][0],
            "peak range": list(range(peak_take_cz["SummerPeakStartHr"][0],
                                     peak_take_cz["SummerPeakEndHr"][0] + 1)),
            "take range": list(range(peak_take_cz["SummerTakeStartHr1"][0],
                                     peak_take_cz["SummerTakeEndHr1"][0] + 1))}
        # Set winter max load hour, min load hour, and peak/take windows
        wint_peak_take = {
            "max": peak_take_cz["WinterMaxHr"][0],
            "min": peak_take_cz["WinterMinHr"][0],
            "peak range": list(range(peak_take_cz["WinterPeakStartHr"][0],
                                     peak_take_cz["WinterPeakEndHr"][0] + 1)),
            "take range": list(range(peak_take_cz["WinterTakeStartHr1"][0],
                                     peak_take_cz["WinterTakeEndHr1"][0] + 1))}
        # Set intermediate max load hour, min load hour, and peak/take windows
        inter_peak_take = {
            "max": peak_take_cz["InterMaxHr"][0],
            "min": peak_take_cz["InterMinHr"][0],
            "peak range": list(range(peak_take_cz["InterPeakStartHr"][0],
                                     peak_take_cz["InterPeakEndHr"][0] + 1)),
            "take range": list(range(peak_take_cz["InterTakeStartHr1"][0],
                                     peak_take_cz["InterTakeEndHr1"][0] + 1))}
        # Handle cases where seasonal low demand periods cover two or three
        # non-contiguous time segments (e.g., 2-6AM, 10AM-2PM)

        # Loop through seasonal take variable names
        for seas in ["SummerTake", "WinterTake", "InterTake"]:
            # Loop through segment number in the variable name
            for seg in ["2", "3"]:
                # Sandwich start/end hour information between season and
                # segment information in the variable name
                st_key = seas + "StartHr" + seg
                end_key = seas + "EndHr" + seg
                # Check to see whether data are present for the given season
                # and segment (use segment starting hour variable as indicator)
                if numpy.isfinite(peak_take_cz[st_key][0]):
                    # Append additional low demand periods as appropriate for
                    # the given season
                    if "Summer" in seas:
                        sum_peak_take["take range"].extend(list(
                            range(peak_take_cz[st_key][0],
                                  peak_take_cz[end_key][0])))
                    elif "Winter" in seas:
                        wint_peak_take["take range"].extend(list(
                            range(peak_take_cz[st_key][0],
                                  peak_take_cz[end_key][0])))
                    else:
                        inter_peak_take["take range"].extend(list(
                            range(peak_take_cz[st_key][0],
                                  peak_take_cz[end_key][0])))

        return sum_peak_take, wint_peak_take, inter_peak_take

    def append_keyvals(self, dict1, keyval_list):
        """Append all terminal key values in a dict to a list.

        Note:
            Values already in the list should not be appended.

        Args:
            dict1 (dict): Dictionary with terminal key values
                to append.

        Returns:
            List including all terminal key values from dict.

        Raises:
            ValueError: If terminal key values are not formatted as
                either lists or strings.
        """
        for (k, i) in dict1.items():
            if isinstance(i, dict):
                self.append_keyvals(i, keyval_list)
            elif isinstance(i, list):
                keyval_list.extend([
                    x for x in i if x not in keyval_list])
            elif isinstance(i, str) and i not in keyval_list:
                keyval_list.append(i)
            else:
                raise ValueError(
                    "Input dict terminal key values expected to be "
                    "lists or strings in the 'append_keyvals' function"
                    "for ECM '" + self.name + "'")

        return keyval_list


class EPlusMapDicts(object):
    """Class of dicts used to map Scout measure definitions to EnergyPlus.

    Attributes:
        czone (dict): Scout-EnergyPlus climate zone mapping.
        bldgtype (dict): Scout-EnergyPlus building type mapping. Shown are
            the EnergyPlus commercial reference building names that correspond
            to each AEO commercial building type, and the weights needed in
            some cases to map multiple EnergyPlus reference building types to
            a single AEO type. See 'convert_data' JSON for more details.
        fuel (dict): Scout-EnergyPlus fuel type mapping.
        enduse (dict): Scout-EnergyPlus end use mapping.
        structure_type (dict): Scout-EnergyPlus structure type mapping.
    """

    def __init__(self):
        self.czone = {
            "sub arctic": "BA-SubArctic",
            "very cold": "BA-VeryCold",
            "cold": "BA-Cold",
            "marine": "BA-Marine",
            "mixed humid": "BA-MixedHumid",
            "mixed dry": "BA-MixedDry",
            "hot dry": "BA-HotDry",
            "hot humid": "BA-HotHumid"}
        self.bldgtype = {
            "assembly": {
                "Hospital": 1},
            "education": {
                "PrimarySchool": 0.26,
                "SecondarySchool": 0.74},
            "food sales": {
                "Supermarket": 1},
            "food service": {
                "QuickServiceRestaurant": 0.31,
                "FullServiceRestaurant": 0.69},
            "health care": None,
            "lodging": {
                "SmallHotel": 0.26,
                "LargeHotel": 0.74},
            "large office": {
                "LargeOfficeDetailed": 0.9,
                "MediumOfficeDetailed": 0.1},
            "small office": {
                "SmallOffice": 0.12,
                "OutpatientHealthcare": 0.88},
            "mercantile/service": {
                "RetailStandalone": 0.53,
                "RetailStripmall": 0.47},
            "warehouse": {
                "Warehouse": 1},
            "other": None}
        self.fuel = {
            'electricity': 'electricity',
            'natural gas': 'gas',
            'distillate': 'other_fuel'}
        self.enduse = {
            'heating': [
                'heating_electricity', 'heat_recovery_electricity',
                'humidification_electricity', 'pump_electricity',
                'heating_gas', 'heating_other_fuel'],
            'cooling': [
                'cooling_electricity', 'pump_electricity',
                'heat_rejection_electricity'],
            'water heating': [
                'service_water_heating_electricity',
                'service_water_heating_gas',
                'service_water_heating_other_fuel'],
            'ventilation': ['fan_electricity'],
            'cooking': [
                'interior_equipment_gas', 'interior_equipment_other_fuel'],
            'lighting': ['interior_lighting_electricity'],
            'refrigeration': ['refrigeration_electricity'],
            'PCs': ['interior_equipment_electricity'],
            'non-PC office equipment': ['interior_equipment_electricity'],
            'MELs': ['interior_equipment_electricity']}
        # Note: assumed year range for each structure vintage shown in lists
        self.structure_type = {
            "new": '90.1-2013',
            "retrofit": {
                '90.1-2004': [2004, 2009],
                '90.1-2010': [2010, 2012],
                'DOE Ref 1980-2004': [1980, 2003],
                'DOE Ref Pre-1980': [0, 1979]}}


class EPlusGlobals(object):
    """Class of global variables used in parsing EnergyPlus results file.

    Attributes:
        cbecs_sh (xlrd sheet object): CBECs square footages Excel sheet.
        vintage_sf (dict): Summary of CBECs square footages by vintage.
        eplus_coltypes (list): Expected EnergyPlus variable data types.
        eplus_basecols (list): Variable columns that should never be removed.
        eplus_perf_files (list): EnergyPlus simulation output file names.
        eplus_vintages (list): EnergyPlus building vintage types.
        eplus_vintage_weights (dicts): Square-footage-based weighting factors
            for EnergyPlus vintages.
    """

    def __init__(self, eplus_dir, cbecs_sf_byvint):
        # Set building vintage square footage data from CBECS
        self.vintage_sf = cbecs_sf_byvint
        self.eplus_coltypes = [
            ('building_type', '<U50'), ('climate_zone', '<U50'),
            ('template', '<U50'), ('measure', '<U50'), ('status', '<U50'),
            ('ep_version', '<U50'), ('os_version', '<U50'),
            ('timestamp', '<U50'), ('cooling_electricity', '<f8'),
            ('cooling_water', '<f8'), ('district_chilled_water', '<f8'),
            ('district_hot_water_heating', '<f8'),
            ('district_hot_water_service_hot_water', '<f8'),
            ('exterior_equipment_electricity', '<f8'),
            ('exterior_equipment_gas', '<f8'),
            ('exterior_equipment_other_fuel', '<f8'),
            ('exterior_equipment_water', '<f8'),
            ('exterior_lighting_electricity', '<f8'),
            ('fan_electricity', '<f8'),
            ('floor_area', '<f8'), ('generated_electricity', '<f8'),
            ('heat_recovery_electricity', '<f8'),
            ('heat_rejection_electricity', '<f8'),
            ('heating_electricity', '<f8'), ('heating_gas', '<f8'),
            ('heating_other_fuel', '<f8'), ('heating_water', '<f8'),
            ('humidification_electricity', '<f8'),
            ('humidification_water', '<f8'),
            ('interior_equipment_electricity', '<f8'),
            ('interior_equipment_gas', '<f8'),
            ('interior_equipment_other_fuel', '<f8'),
            ('interior_equipment_water', '<f8'),
            ('interior_lighting_electricity', '<f8'),
            ('net_site_electricity', '<f8'), ('net_water', '<f8'),
            ('pump_electricity', '<f8'),
            ('refrigeration_electricity', '<f8'),
            ('service_water', '<f8'),
            ('service_water_heating_electricity', '<f8'),
            ('service_water_heating_gas', '<f8'),
            ('service_water_heating_other_fuel', '<f8'), ('total_gas', '<f8'),
            ('total_other_fuel', '<f8'), ('total_site_electricity', '<f8'),
            ('total_water', '<f8')]
        self.eplus_basecols = [
            'building_type', 'climate_zone', 'template', 'measure']
        # Set EnergyPlus data file name list, given local directory
        self.eplus_perf_files = [
            f for f in listdir(eplus_dir) if
            isfile(join(eplus_dir, f)) and '_scout_' in f]
        # Import the first of the EnergyPlus measure performance files and use
        # it to establish EnergyPlus vintage categories
        eplus_file = numpy.genfromtxt(
            (eplus_dir + '/' + self.eplus_perf_files[0]), names=True,
            dtype=self.eplus_coltypes, delimiter=",", missing_values='')
        self.eplus_vintages = numpy.unique(eplus_file['template'])
        # Determine appropriate weights for mapping EnergyPlus vintages to the
        # 'new' and 'retrofit' building structure types of Scout
        self.eplus_vintage_weights = self.find_vintage_weights()

    def find_vintage_weights(self):
        """Find square-footage-based weighting factors for building vintages.

        Note:
            Use CBECs building vintage square footage data to derive weighting
            factors that will map the EnergyPlus building vintages to the 'new'
            and 'retrofit' building structure types of Scout.

        Returns:
            Weights needed to map each EnergyPlus vintage category to the 'new'
            and 'retrofit' structure types defined in Scout.

        Raises:
            ValueError: If vintage weights do not sum to 1.
            KeyError: If unexpected vintage names are discovered in the
                EnergyPlus file.
        """
        handydicts = EPlusMapDicts()

        # Set the expected names of the EnergyPlus building vintages and the
        # low and high year limits of each building vintage category
        expected_eplus_vintage_yr_bins = [
            handydicts.structure_type['new']] + \
            list(handydicts.structure_type['retrofit'].keys())
        # Initialize a variable meant to translate the summed square footages
        # of multiple 'retrofit' building vintages into weights that sum to 1;
        # also initialize a variable used to check that these weights indeed
        # sum to 1
        total_retro_sf, retro_weight_sum = (0 for n in range(2))

        # Check for expected EnergyPlus vintage names
        if sorted(self.eplus_vintages) == sorted(
                expected_eplus_vintage_yr_bins):
            # Initialize a dictionary with the EnergyPlus vintages as keys and
            # associated square footage values starting at zero
            eplus_vintage_weights = dict.fromkeys(self.eplus_vintages, 0)

            # Loop through the EnergyPlus vintages and assign associated
            # weights by mapping to cbecs square footage data
            for k in eplus_vintage_weights.keys():
                # If looping through the EnergyPlus vintage associated with the
                # 'new' Scout structure type, set vintage weight to 1 (only one
                # vintage category will be associated with this structure type)
                if k == handydicts.structure_type['new']:
                    eplus_vintage_weights[k] = 1
                # Otherwise, set EnergyPlus vintage weight initially to the
                # square footage that corresponds to that vintage in cbecs
                else:
                    # Loop through all cbecs vintage bins
                    for k2 in self.vintage_sf.keys():
                        # Find the limits of the cbecs vintage bin
                        cbecs_match = re.search(
                            r'(\D*)(\d*)(\s*)(\D*)(\s*)(\d*)', k2)
                        cbecs_t1 = cbecs_match.group(2)
                        cbecs_t2 = cbecs_match.group(6)
                        # Handle a 'Before Year X' case in cbecs (e.g., 'Before
                        # 1920'),  setting the lower year limit to zero
                        if cbecs_t2 == '':
                            cbecs_t2 = 0
                        # Determine a single average year that represents the
                        # current cbecs vintage bin
                        cbecs_yr = (int(cbecs_t1) + int(cbecs_t2)) / 2
                        # If the cbecs bin year falls within the year limits of
                        # the current EnergyPlus vintage bin, add the
                        # associated cbecs ft^2 data to the EnergyPlus
                        # vintage weight value
                        if cbecs_yr >= handydicts.structure_type[
                            'retrofit'][k][0] and \
                           cbecs_yr < handydicts.structure_type[
                           'retrofit'][k][1]:
                            eplus_vintage_weights[k] += self.vintage_sf[k2]
                            total_retro_sf += self.vintage_sf[k2]

            # Run through all EnergyPlus vintage weights, normalizing the
            # square footage-based weights for each 'retrofit' vintage to the
            # total square footage across all 'retrofit' vintage categories
            for k in eplus_vintage_weights.keys():
                # If running through the 'new' EnergyPlus vintage bin, register
                # the value of its weight (should be 1)
                if k == handydicts.structure_type['new']:
                    new_weight_sum = eplus_vintage_weights[k]
                # If running through a 'retrofit' EnergyPlus vintage bin,
                # normalize the square footage for that vintage by total
                # square footages across 'retrofit' vintages to arrive at the
                # final weight for that EnergyPlus vintage
                else:
                    eplus_vintage_weights[k] /= total_retro_sf
                    retro_weight_sum += eplus_vintage_weights[k]

            # Check that the 'new' EnergyPlus vintage weight equals 1 and that
            # all 'retrofit' EnergyPlus vintage weights sum to 1
            if new_weight_sum != 1:
                raise ValueError("Incorrect new vintage weight total when "
                                 "instantiating 'EPlusGlobals' object")
            elif retro_weight_sum != 1:
                raise ValueError("Incorrect retrofit vintage weight total when"
                                 "instantiating 'EPlusGlobals' object")

        else:
            raise KeyError(
                "Unexpected EnergyPlus vintage(s) when instantiating "
                "'EPlusGlobals' object; "
                "check EnergyPlus vintage assumptions in structure_type "
                "attribute of 'EPlusMapDict' object")

        return eplus_vintage_weights


class Measure(object):
    """Set up a class representing efficiency measures as objects.

    Attributes:
        **kwargs: Arbitrary keyword arguments used to fill measure attributes
            from an input dictionary.
        remove (boolean): Determines whether measure should be removed from
            analysis engine due to insufficient market source data.
        energy_outputs (dict): Indicates whether site energy or captured
            energy site-source conversions were used in measure preparation,
            as well as regions used for this preparation and whether or not
            public health cost adders were specified.
        handyvars (object): Global variables useful across class methods.
        retro_rate (float or list): Stock retrofit rate specific to the ECM.
        technology_type (string): Flag for supply- or demand-side technology.
        yrs_on_mkt (list): List of years that the measure is active on market.
        markets (dict): Data grouped by adoption scheme on:
            a) 'master_mseg': a measure's master market microsegments (stock,
               energy, carbon, cost),
            b) 'mseg_adjust': all microsegments that contribute to each master
               microsegment (required later for measure competition).
            c) 'mseg_out_break': master microsegment breakdowns by key
               variables (climate zone, building class, end use)
        sector_shapes (dict): Sector-level hourly baseline and efficient load
            shapes by adopt scheme, EMM region, and year
        sector_shapes_pkg (dict): Sector-level hourly baseline and efficient
            load shapes by adopt scheme, contributing microsegment, and year
            (used to generate package sector shapes data if applicable).
    """

    def __init__(
            self, base_dir, handyvars, handyfiles, site_energy, capt_energy,
            regions, tsv_metrics, health_costs, split_fuel, **kwargs):
        # Read Measure object attributes from measures input JSON.
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Check to ensure that measure name is proper length for plotting;
        # for now, exempt measures with public health cost adders
        if len(self.name) > 45 and "PHC" not in self.name:
            raise ValueError(
                "ECM '" + self.name + "' name must be <= 45 characters")
        self.remove = False
        # Flag custom energy output settings (user-defined)
        self.energy_outputs = {
            "site_energy": False, "captured_energy_ss": False,
            "alt_regions": False, "tsv_metrics": False, "health_costs": False,
            "split_fuel": False}
        if site_energy is True:
            self.energy_outputs["site_energy"] = True
        if capt_energy is True:
            self.energy_outputs["captured_energy_ss"] = True
        if regions != "AIA":
            self.energy_outputs["alt_regions"] = regions
        if tsv_metrics is not None:
            if (self.fuel_type not in ["electricity", ["electricity"]]) and \
                    self.fuel_switch_to != "electricity":
                raise ValueError(
                    "Non-electric fuel found for measure '" + self.name +
                    " alongside '--tsv_metrics' option. Such metrics cannot "
                    "be calculated for non-electric baseline segments of "
                    "energy use. To address this issue, restrict the "
                    "measure's fuel type to electricity.")
            self.energy_outputs["tsv_metrics"] = tsv_metrics
        if health_costs is not None:
            # Look for pre-determined health cost scenario names in the
            # UsefulVars class, "health_scn_names" attribute
            if "PHC-EE (low)" in self.name:
                self.energy_outputs["health_costs"] = "Uniform EE-low"
            elif "PHC-EE (high)" in self.name:
                self.energy_outputs["health_costs"] = "Uniform EE-high"
        if split_fuel is True:
            self.energy_outputs["split_fuel"] = True
        self.sector_shapes, self.sector_shapes_pkg = (
            {a_s: {} for a_s in handyvars.adopt_schemes} for n in range(2))
        # Deep copy handy vars to avoid any dependence of changes to these vars
        # across other measures that use them
        self.handyvars = copy.deepcopy(handyvars)
        # Set the rate of baseline retrofitting for ECM stock-and-flow calcs
        try:
            # Check first to see whether pulling up retrofit rate errors
            self.retro_rate
            # Accommodate retrofit rate input as a probability distribution
            if type(self.retro_rate) is list and isinstance(
                    self.retro_rate[0], str):
                # Sample measure retrofit rate values
                self.retro_rate = self.rand_list_gen(
                    self.retro_rate, self.handyvars.nsamples)
            # Raise error in case where distribution is incorrectly specified
            elif type(self.retro_rate) is list:
                raise ValueError(
                    "ECM " + self.name + " 'retro_rate' distribution must " +
                    "be formatted as [<distribution name> (string), " +
                    "<distribution parameters> (floats)]")
            # If retrofit rate is set to None, use default retrofit rate value
            elif self.retro_rate is None:
                self.retro_rate = self.handyvars.retro_rate
            # Do nothing in case where retrofit rate is specified as float
            else:
                pass
        except AttributeError:
            # If no 'retro_rate' attribute was given for the ECM, use default
            # retrofit rate value
            self.retro_rate = self.handyvars.retro_rate

        # Determine whether the measure replaces technologies pertaining to
        # the supply or the demand of energy services
        self.technology_type = None
        # Measures replacing technologies in a pre-specified
        # 'demand_tech' list are of the 'demand' side technology type
        if (isinstance(self.technology, list) and all([
            x in self.handyvars.demand_tech for x in self.technology])) or \
                self.technology in self.handyvars.demand_tech:
            self.technology_type = "demand"
        # Measures replacing technologies not in a pre-specified
        # 'demand_tech' list are of the 'supply' side technology type
        else:
            self.technology_type = "supply"
        # Reset market entry year if None or earlier than min. year
        if self.market_entry_year is None or (int(
                self.market_entry_year) < int(self.handyvars.aeo_years[0])):
            self.market_entry_year = int(self.handyvars.aeo_years[0])
        # Reset measure market exit year if None or later than max. year
        if self.market_exit_year is None or (int(
                self.market_exit_year) > (int(
                    self.handyvars.aeo_years[-1]) + 1)):
            self.market_exit_year = int(self.handyvars.aeo_years[-1]) + 1
        self.yrs_on_mkt = [str(i) for i in range(
            self.market_entry_year, self.market_exit_year)]
        # Test for whether a user has set time sensitive valuation features
        # for the given measure. If no "tsv_features" parameter was
        # specified for the ECM, set this parameter to None
        try:
            # Try to access the ECM's TSV feature dict keys
            self.tsv_features.keys()
            # If TSV features are present, ensure that EMM regions are selected
            # and that the measure only applies to electricity (and no fuel
            # switching is selected)
            if regions != "EMM":
                raise ValueError(
                    "Measure '" + self.name + "' has time sensitive "
                    "assessment features (see 'tsv_features' attribute) but "
                    "regions are not set to EMM; try running 'ecm_prep.py' "
                    "again with the --alt_regions option included and select "
                    "EMM regions when prompted.")
            if (self.fuel_type not in ["electricity", ["electricity"]]) and \
                    self.fuel_switch_to != "electricity":
                raise ValueError(
                    "Non-electric fuel found for measure '" + self.name +
                    " alongside time sensitive valuation features. Such "
                    "features cannot be implemented for non-electric "
                    "baseline segments of energy use. To address this issue, "
                    "restrict the measure's fuel type to electricity.")
            # If the ECM is assigned a custom savings shape, load the
            # associated custom savings shape data from a CSV file
            if "shape" in self.tsv_features.keys() and \
                "custom_annual_savings" in \
                    self.tsv_features["shape"].keys():
                # Determine the CSV file name
                csv_shape_file_name = \
                    self.tsv_features["shape"]["custom_annual_savings"]
                # Assuming the standard location for ECM savings shape CSV
                # files, import custom savings shape data as numpy array and
                # store it in the ECM's custom savings shape attribute for
                # subsequent use in the 'apply_tsv' function
                self.tsv_features["shape"]["custom_annual_savings"] = \
                    numpy.genfromtxt(
                        path.join(base_dir, *handyfiles.tsv_shape_data,
                                  csv_shape_file_name),
                        names=True, delimiter=',', dtype=[
                            ('Hour_of_Year', '<i4'),
                            ('Climate_Zone', '<U25'),
                            ('Net_Load_Version', '<i4'),
                            ('Building_Type', '<U25'),
                            ('End_Use', '<U25'),
                            ('Baseline_Load', '<f8'),
                            ('Measure_Load', '<f8'),
                            ('Relative_Savings', '<f8')],
                        encoding="latin1")

                # Retrieve custom savings shapes for all applicable
                # end use, building type, and climate zone combinations
                # and store within a dict for use in 'apply_tsv' function

                print("Retrieving custom savings shape data for measure "
                      + self.name + "...", end="", flush=True)

                # Set shorthand for custom savings shape data
                css_dat = self.tsv_features["shape"][
                    "custom_annual_savings"]
                # Initialize dict to use in storing shape data
                css_dict = {}
                # Find all unique end uses in the shape data
                euses = numpy.unique(css_dat["End_Use"])
                # Loop through all end uses in the data
                for eu in euses:
                    # Handle case where end use names in the data are
                    # read in with added quotes (e.g., 'heating' comes in
                    # as '"heating"'), or are not strings. In the first
                    # instance, use eval() to strip the added quotes from the
                    # end use name and key in the savings shape information
                    # by the result
                    try:
                        eu_key = eval(eu)
                    except (NameError, SyntaxError):
                        eu_key = eu
                    if type(eu_key) != str:
                        eu_key = str(eu_key)
                    # Restrict shape data to that of the current end use
                    css_dat_eu = css_dat[
                        numpy.in1d(css_dat["End_Use"], eu)]
                    # Initialize dict under the current end use key
                    css_dict[eu_key] = {}
                    # Find all unique building types and climate zones in
                    # the end-use-restricted shape data
                    bldg_types = numpy.unique(
                        css_dat_eu["Building_Type"])
                    czones = numpy.unique(
                        css_dat_eu["Climate_Zone"])
                    # Loop through all building types under the current
                    # end use
                    for bd in bldg_types:
                        # Handle case where building type names in the data
                        # are read in with added quotes, or are not strings
                        try:
                            bd_key = eval(bd)
                        except (NameError, SyntaxError):
                            bd_key = bd
                        if type(bd_key) != str:
                            bd_key = str(bd_key)
                        # Account for possible use of StandAlone naming in
                        # savings shape CSV, vs. Standalone naming in Scout's
                        # baseline load shapes file
                        if bd_key == "RetailStandAlone":
                            bd_key = "RetailStandalone"
                        # Account for possible use of MediumOffice naming
                        # in savings shape CSV, vs. MediumOfficeDetailed in
                        # Scout's baseline load shapes file
                        elif bd_key == "MediumOffice":
                            bd_key = "MediumOfficeDetailed"
                        # Account for possible use of MediumOffice naming
                        # in savings shape CSV, vs. MediumOfficeDetailed in
                        # Scout's baseline load shapes file
                        elif bd_key == "LargeOffice":
                            bd_key = "LargeOfficeDetailed"
                        # Initialize dict under the current end use and
                        # building type keys
                        css_dict[eu_key][bd_key] = {}
                        # Loop through all climate zones under the current
                        # end use
                        for cz in czones:
                            # Handle case where climate zone names in the
                            # data are read in with added quotes, or are not
                            # strings
                            try:
                                cz_key = eval(cz)
                            except (NameError, SyntaxError):
                                cz_key = cz
                            if type(cz_key) != str:
                                cz_key = str(cz_key)
                            # Account for possible use of climate 7A naming
                            # in savings shape CSV, vs. 7 naming in Scout's
                            # baseline load shapes file
                            if cz_key == "7A":
                                cz_key = "7"
                            # Restrict shape data to that of the current
                            # end use, building type, and climate zone
                            # combination
                            css_dat_eu_bldg_cz = css_dat_eu[
                                numpy.in1d(css_dat_eu["Building_Type"], bd) &
                                numpy.in1d(css_dat_eu["Climate_Zone"], cz)]
                            # Initialize dict under the current end use and
                            # building type keys
                            css_dict[eu_key][bd_key][cz_key] = {}
                            # Find all unique representative system load
                            # shapes for the current climate zone
                            sys_v = numpy.unique(
                                css_dat_eu_bldg_cz["Net_Load_Version"])
                            # If "Net_Load_Version" column is blank, set unique
                            # net load versions to 1
                            if len(sys_v) == 0 or (
                                    len(sys_v) == 1 and sys_v[0] == -1):
                                sys_v = [1]
                            for sv in sys_v:
                                v_key = "set " + str(sv)
                                css_dict[eu_key][bd_key][cz_key][v_key] = \
                                    css_dat_eu_bldg_cz[numpy.in1d(
                                        css_dat_eu_bldg_cz[
                                            "Net_Load_Version"], sv)][
                                    "Relative_Savings"]
                                # Check to ensure that the resultant dict
                                # value is the expected 8760 elements long; if
                                # not, throw error
                                if len(css_dict[eu_key][bd_key][cz_key][
                                        v_key]) != 8760:
                                    raise ValueError(
                                        "Measure '" + self.name +
                                        "', requires "
                                        "custom savings shape data, but the "
                                        "custom shape given for climate "
                                        "zone " + cz_key +
                                        ", building type "
                                        + bd_key + ", and end use " + eu_key +
                                        " has more or less than 8760 values. "
                                        "Check that 8760 hourly savings " +
                                        "fractions are available for all " +
                                        "baseline market segments the " +
                                        "measure applies to in "
                                        "./ecm_definitions/energy_plus_data"
                                        "/savings_shapes.")
                # Set custom savings shape information to populated dict
                self.tsv_features["shape"]["custom_annual_savings"] = \
                    css_dict
                print("Data import complete")
        except AttributeError:
            self.tsv_features = None
        # Check to ensure that the proper EMM regions are defined in the
        # measure 'climate_zone' attribute if time sensitive ECM features
        # and/or output metrics are desired
        valid_tsv_regions = [
            'TRE', 'FRCC', 'MISW', 'MISC', 'MISE', 'MISS',
            'ISNE', 'NYCW', 'NYUP', 'PJME', 'PJMW', 'PJMC',
            'PJMD', 'SRCA', 'SRSE', 'SRCE', 'SPPS', 'SPPC',
            'SPPN', 'SRSG', 'CANO', 'CASO', 'NWPP', 'RMRG', 'BASN']
        if (any([x is not None for x in [
            self.tsv_features, tsv_metrics]]) and ((
                type(self.climate_zone) == list and any([
                    x not in valid_tsv_regions for x in self.climate_zone])) or
            (type(self.climate_zone) != list and self.climate_zone != "all"
                and (self.climate_zone not in valid_tsv_regions)))):
            raise ValueError(
                "Invalid 'climate_zone' attribute value(s) for ECM '" +
                self.name + "' given desired time sensitive valuation "
                "operations/outputs. Currently, only EMM regions are "
                "supported for time sensitive valuation. This issue can "
                "be addressed by ensuring all ECM 'climate_zone' values "
                "reflect one of the EMM regions.")
        self.markets = {}

        for adopt_scheme in handyvars.adopt_schemes:
            self.markets[adopt_scheme] = OrderedDict([(
                "master_mseg", OrderedDict([(
                    "stock", {
                        "total": {
                            "all": None, "measure": None},
                        "competed": {
                            "all": None, "measure": None}}),
                    (
                    "energy", {
                        "total": {
                            "baseline": None, "efficient": None},
                        "competed": {
                            "baseline": None, "efficient": None}}),
                    (
                    "carbon", {
                        "total": {
                            "baseline": None, "efficient": None},
                        "competed": {
                            "baseline": None, "efficient": None}}),
                    (
                    "cost", {
                        "stock": {
                            "total": {
                                "baseline": None, "efficient": None},
                            "competed": {
                                "baseline": None, "efficient": None}},
                        "energy": {
                            "total": {
                                "baseline": None, "efficient": None},
                            "competed": {
                                "baseline": None, "efficient": None}},
                        "carbon": {
                            "total": {
                                "baseline": None, "efficient": None},
                            "competed": {
                                "baseline": None, "efficient": None}}}),
                    (
                    "lifetime", {"baseline": None, "measure": None})])),
                (
                "mseg_adjust", {
                    "contributing mseg keys and values": {},
                    "competed choice parameters": {},
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
                            "adjusted energy (competed and captured)": {}}}}),
                (
                "mseg_out_break", {key: {
                    "baseline": copy.deepcopy(self.handyvars.out_break_in),
                    "efficient": copy.deepcopy(self.handyvars.out_break_in),
                    "savings": copy.deepcopy(self.handyvars.out_break_in)} for
                    key in ["energy", "carbon", "cost"]})])

    def fill_eplus(self, msegs, eplus_dir, eplus_coltypes,
                   eplus_files, vintage_weights, base_cols):
        """Fill in measure performance with EnergyPlus simulation results.

        Note:
            Find the appropriate set of EnergyPlus simulation results for
            the current measure, and use the relative savings percentages
            in these results to determine the measure performance attribute.

        Args:
            msegs (dict): Baseline microsegment stock/energy data to use in
                validating categorization of measure performance information.
            eplus_dir (string): Directory of EnergyPlus performance files.
            eplus_coltypes (list): Expected EnergyPlus variable data types.
            eplus_files (list): EnergyPlus performance file names.
            vintage_weights (dict): Square-footage-derived weighting factors
                for each EnergyPlus building vintage type.

        Returns:
            Updated Measure energy_efficiency, energy_efficiency_source, and
            energy_efficiency_source attribute values.

        Raises:
            ValueError: If EnergyPlus file is not matched to Measure
                definition or more than one EnergyPlus file matches the
                Measure definition.
        """
        # Instantiate useful EnergyPlus-Scout mapping dicts
        handydicts = EPlusMapDicts()
        # Determine the relevant EnergyPlus building type name(s)
        bldg_type_names = []
        for x in self.bldg_type:
            bldg_type_names.extend(handydicts.bldgtype[x].keys())
        # Find all EnergyPlus files including the relevant building type
        # name(s)
        eplus_perf_in = [(eplus_dir + '/' + x) for x in eplus_files if any([
            y.lower() in x for y in bldg_type_names])]

        # Import EnergyPlus input file as array and use it to fill a dict
        # of measure performance data
        if len(eplus_perf_in) > 0:
            # Assemble the EnergyPlus data into a record array
            eplus_perf_array = self.build_array(eplus_coltypes, eplus_perf_in)
            # Create a measure performance dictionary, zeroed out, to
            # be updated with data from EnergyPlus array
            perf_dict_empty = self.create_perf_dict(msegs)

            # Update measure performance based on EnergyPlus data
            # (* Note: only update efficiency information for
            # secondary microsegments if applicable)
            if perf_dict_empty['secondary'] is not None:
                self.energy_efficiency = self.fill_perf_dict(
                    perf_dict_empty, eplus_perf_array,
                    vintage_weights, base_cols, eplus_bldg_types={})
            else:
                self.energy_efficiency = self.fill_perf_dict(
                    perf_dict_empty['primary'], eplus_perf_array,
                    vintage_weights, base_cols, eplus_bldg_types={})
            # Set the energy efficiency data source for the measure to
            # EnergyPlus and set to highest data quality rating
            self.energy_efficiency_source = 'EnergyPlus/OpenStudio'
        else:
            raise ValueError(
                "Failure to find relevant EPlus files for " +
                "Scout building type(s) " + str(self.bldg_type) +
                "in ECM '" + self.name + "'")

    def fill_mkts(self, msegs, msegs_cpl, convert_data, tsv_data, opts,
                  contrib_meas_pkg):
        """Fill in a measure's market microsegments using EIA baseline data.

        Args:
            msegs (dict): Baseline microsegment stock and energy use.
            msegs_cpl (dict): Baseline technology cost, performance, and
                lifetime.
            convert_data (dict): Measure -> baseline cost unit conversions.
            tsv_data (dict): Data for time sensitive valuation of efficiency.
            opts (object): Stores user-specified execution options.
            contrib_meas_pkg (list): List of measure names that contribute
                to active packages in the preparation run.

        Returns:
            Updated measure stock, energy/carbon, and cost market microsegment
            information, as stored in the 'markets' attribute.

        Raises:
            KeyError: If measure and baseline performance or cost units are
                inconsistent, or no valid baseline market microsegments can
                be found for the given measure definition.
            ValueError: If an input value from the measure definition is
                invalid, or if baseline market microsegment information cannot
                be mapped to a valid breakout category for measure outputs.
        """
        # Check that the measure's applicable baseline market input definitions
        # are valid before attempting to retrieve data on this baseline market
        self.check_mkt_inputs()

        # Notify user that ECM is being updated; suppress new line
        # if not in verbose mode ('Success' is appended to this message on
        # the same line of the console upon completion of ECM update)
        if opts is not None and opts.verbose is True:
            print("Updating ECM '" + self.name + "'...")
        else:
            print("Updating ECM '" + self.name + "'...", end="", flush=True)

        # If multiple runs are required to handle probability distributions on
        # measure inputs, set a number to seed each random draw of cost,
        # performance, and or lifetime with for consistency across all
        # microsegments that contribute to the measure's master microsegment
        if self.handyvars.nsamples is not None:
            rnd_sd = numpy.random.randint(10000)

        # Initialize a counter of key chains that yield "stock" and "energy"
        # keys in the baseline data dict; that have valid stock/energy data;
        # that have valid cost/performance/lifetime data; and that have valid
        # consumer choice data. Also initialize a cost conversion flag
        valid_keys, valid_keys_stk_energy, valid_keys_cpl, \
            valid_keys_consume, cost_converts = (0 for n in range(5))
        # Initialize lists of technology names that have yielded warnings
        # for invalid stock/energy data, cost/performance/lifetime data
        # and consumer data, EIA baseline cost adjustments (in the case
        # of heat pump HVAC) and a list of the climate zones, building types,
        # and structure type of removed primary microsegments (used to remove
        # associated secondary microsegments)
        stk_energy_warn, cpl_warn, consume_warn, hp_warn, removed_primary = (
            [] for n in range(5))

        # Initialize flags for invalid information about sub-market fraction
        # source, URL, and derivation
        sbmkt_source_invalid, sbmkt_url_invalid, sbmkt_derive_invalid = (
            0 for n in range(3))

        # Initialize variable indicating use of ft^2 floor area as microsegment
        # stock
        sqft_subst = 0

        # Establish a flag for a commercial lighting case where the user has
        # not specified secondary end use effects on heating and cooling.  In
        # this case, secondary effects are added automatically by adjusting
        # the "lighting gain" thermal load component in accordance with the
        # lighting efficiency change (e.g., a 40% relative savings from
        # efficient lighting equipment translates to a 40% increase in heating
        # loads and 40% decrease in cooling load)
        light_scnd_autoperf = False

        # Initialize a list that tracks completed cost conversions - including
        # converted values and units - for cases where the cost conversion need
        # occur only once per microsegment building type
        bldgs_costconverted = {}

        # Fill out any "secondary" end use impact information and any climate
        # zone, building type, fuel type, end use, and/or technology attributes
        # marked 'all' by users
        self.fill_attr()

        # Fill in sector baseline/efficient 8760 shapes attribute across all
        # applicable regions for the measure with a list of 8760 zeros (if
        # necessary)
        if opts.sect_shapes is True:
            # Find applicable region list (ensure it is in list format)s
            if type(self.climate_zone) is str:
                grid_regions = copy.deepcopy([self.climate_zone])
            else:
                grid_regions = copy.deepcopy(self.climate_zone)
            for a_s in self.handyvars.adopt_schemes:
                self.sector_shapes[a_s] = {reg: {yr: {
                    "baseline": [0 for x in range(8760)],
                    "efficient": [0 for x in range(8760)]} for yr in
                    self.handyvars.aeo_years_summary} for reg in grid_regions}

        # Find all possible microsegment key chains.  First, determine all
        # "primary" microsegment key chains, where "primary" refers to the
        # baseline microsegment(s) directly affected by a measure (e.g.,
        # incandescent bulb lights for an LED replacement measure).  Second,
        # if needed, determine all "secondary" microsegment key chains, where
        # "secondary" refers to baseline microsegments that are indirectly
        # affected by the measure (e.g., heating and cooling for the above
        # LED replacement).  Secondary microsegments are only relevant for
        # energy/carbon and associated energy/carbon cost calculations, as
        # they do not indicate additional equipment purchases (and thus do not
        # affect stock, stock costs, or equipment lifetime calculations)

        # Determine "primary" microsegment key chains
        ms_iterable, ms_lists = self.create_keychain("primary")

        # If needed, fill out any secondary microsegment fuel type, end use,
        # and/or technology input attributes marked 'all' by users. Determine
        # secondary microsegment key chains and add to the primary
        # microsegment key chain list. In a commercial lighting measure case
        # where no heating/cooling effects from lighting are directly
        # specified, use the "lighting gain" thermal load component
        # microsegments to represent secondary effects of the lighting measure
        if self.end_use["secondary"] is not None:
            ms_iterable_second, ms_lists_second = self.create_keychain(
                "secondary")
            ms_iterable.extend(ms_iterable_second)
        elif "lighting" in self.end_use["primary"] and (
            not opts or opts.no_scnd_lgt is not True) and any([
                x not in self.end_use["primary"] for x in [
                "heating", "cooling"]]) and \
            any([x not in ["single family home", "multi family home",
                           "mobile home"] for x in self.bldg_type]):
            # Set secondary lighting mseg performance flag to True
            light_scnd_autoperf = True
            # Set secondary energy efficiency value to "Missing"
            # (used below as a flag)
            self.energy_efficiency["secondary"] = \
                "Missing (secondary lighting)"
            # Set secondary energy efficiency units to "relative
            # savings"
            self.energy_efficiency_units["secondary"] = \
                "relative savings (constant)"
            # Set secondary fuel type to include all heating/cooling
            # fuels
            self.fuel_type["secondary"] = [
                "electricity", "natural gas", "distillate"]
            # Set relevant secondary end uses
            self.end_use["secondary"] = ["heating", "cooling"]
            # Set secondary technology type ("demand" as the lighting
            # measure affects heating/cooling loads)
            self.technology_type["secondary"] = "demand"
            # Set secondary technology class to "lighting gain", which
            # will access the portion of commercial heating/cooling
            # demand that is attributable to waste heat from lights
            self.technology["secondary"] = "lighting gain"

            # Determine secondary microsegment key chains and add to
            # the primary microsegment key chain list
            ms_iterable_second, ms_lists_second = self.create_keychain(
                "secondary")
            ms_iterable.extend(ms_iterable_second)

        # Loop through discovered key chains to find needed performance/cost
        # and stock/energy information for measure
        for ind, mskeys in enumerate(ms_iterable):

            # Set building sector for the current microsegment
            if mskeys[2] in [
                    "single family home", "mobile home", "multi family home"]:
                bldg_sect = "residential"
            else:
                bldg_sect = "commercial"

            # Adjust the key chain to be used in registering contributing
            # microsegment information for cases where 'windows solar'
            # or 'windows conduction' are in the key chain. Change
            # such entries to just 'windows' to ensure the competition
            # of 'windows conduction' and 'windows solar' contributing
            # microsegments in the 'adjust_savings' function below
            contrib_mseg_key = mskeys
            if any([x is not None and "windows" in x for x in
                    contrib_mseg_key]):
                contrib_mseg_key = list(contrib_mseg_key)
                contrib_mseg_key[numpy.where([x is not None and "windows" in x
                                 for x in contrib_mseg_key])[0][0]] = "windows"
                contrib_mseg_key = tuple(contrib_mseg_key)

            # Initialize measure performance/cost/lifetime, associated units,
            # and sub-market scaling fractions/sources if: a) For loop through
            # all measure mseg key chains is in first iteration, b) A switch
            # has been made from updating "primary" microsegment info. to
            # updating "secondary" microsegment info. (relevant to cost/
            # lifetime units only), c) Any of performance/cost/lifetime units
            # is a dict which must be parsed further to reach the final value,
            # or d) A new cost conversion is required for the current mseg
            # (relevant to cost only). * Note: cost/lifetime/sub-market
            # information is not updated for "secondary" microsegments, which
            # do not pertain to these variables; lifetime units are in years
            if ind == 0 or (ms_iterable[ind][0] != ms_iterable[ind - 1][0]) \
               or isinstance(self.energy_efficiency, dict):
                perf_meas = self.energy_efficiency
            if ind == 0 or (ms_iterable[ind][0] != ms_iterable[ind - 1][0]) \
               or isinstance(self.energy_efficiency_units, dict):
                perf_units = self.energy_efficiency_units
            if mskeys[0] == "secondary":
                cost_meas, life_meas = (0 for n in range(2))
                cost_units = "NA"
                # * Note: no unique sub-market scaling fractions for secondary
                # microsegments; secondary microsegments are only scaled down
                # by the sub-market fraction for their associated primary
                # microsegments
                mkt_scale_frac, mkt_scale_frac_source = (
                    None for n in range(2))
            else:
                # Set ECM cost attribute to value previously calculated for
                # current microsegment building type, provided microsegment
                # does not require re-initiating cost conversions for each
                # new technology type (applicable to residential sector)
                if mskeys[2] in bldgs_costconverted.keys() and (
                    bldg_sect != "residential" or all([
                        x not in self.cost_units for x in
                        self.handyvars.cconv_bytech_units_res])) and (
                        not isinstance(self.installed_cost, dict)):
                    cost_meas, cost_units = [x for x in bldgs_costconverted[
                        mskeys[2]]]
                # Re-initialize ECM cost attribute for each new building
                # type or technology type if required for the given cost units
                elif ind == 0 or any([
                    x in self.cost_units for x in
                    self.handyvars.cconv_bybldg_units]) or (
                    bldg_sect == "residential" and any([
                        y in self.cost_units for y in
                        self.handyvars.cconv_bytech_units_res])):
                    cost_meas, cost_units = [
                        self.installed_cost, self.cost_units]
                elif isinstance(self.installed_cost, dict) or \
                        isinstance(self.cost_units, dict):
                    cost_meas, cost_units = [
                        self.installed_cost, self.cost_units]
                # Set lifetime attribute to initial value
                if ind == 0 or isinstance(
                        self.product_lifetime, dict):
                    life_meas = self.product_lifetime
                # Set market scaling attributes to initial values
                if ind == 0 or isinstance(
                        self.market_scaling_fractions, dict):
                    mkt_scale_frac = self.market_scaling_fractions
                if ind == 0 or isinstance(
                        self.market_scaling_fractions_source, dict):
                    mkt_scale_frac_source = \
                        self.market_scaling_fractions_source

            # Set baseline and measure site-source conversion factors,
            # accounting for any fuel switching from baseline to measure tech.
            if self.fuel_switch_to is None:
                # Set site-source conversions to 1 if user flagged
                # site energy use outputs, to appropriate input data otherwise
                if opts is not None and opts.site_energy is True:
                    site_source_conv_base, site_source_conv_meas = [{
                        yr: 1 for yr in self.handyvars.aeo_years}
                        for n in range(2)]
                else:
                    site_source_conv_base, site_source_conv_meas = (
                        self.handyvars.ss_conv[mskeys[3]] for
                        n in range(2))
            else:
                # Set site-source conversions to 1 if user flagged
                # site energy use outputs, to appropriate input data otherwise
                if opts is not None and opts.site_energy is True:
                    site_source_conv_base, site_source_conv_meas = [{
                        yr: 1 for yr in self.handyvars.aeo_years}
                        for n in range(2)]
                else:
                    site_source_conv_base = self.handyvars.ss_conv[
                        mskeys[3]]
                    site_source_conv_meas = self.handyvars.ss_conv[
                        self.fuel_switch_to]

            # Set baseline and measure carbon intensities, accounting for any
            # fuel switching from baseline technology to measure technology
            if self.fuel_switch_to is None:
                # Case where use has flagged site energy outputs
                if opts is not None and opts.site_energy is True:
                    # Intensities are specified by EMM region or state based on
                    # site energy and require no further conversion to match
                    # the user's site energy setting
                    try:
                        intensity_carb_base, intensity_carb_meas = [{
                            yr: self.handyvars.carb_int[bldg_sect][mskeys[3]][
                                mskeys[1]][yr] for
                            yr in self.handyvars.aeo_years} for n in range(2)]
                    # Intensities are specified nationally based on source
                    # energy and require multiplication by site-source factor
                    # to match the user's site energy setting
                    except KeyError:
                        intensity_carb_base, intensity_carb_meas = [{
                            yr: self.handyvars.carb_int[bldg_sect][
                                mskeys[3]][yr] *
                            self.handyvars.ss_conv[mskeys[3]][yr] for
                            yr in self.handyvars.aeo_years} for n in range(2)]
                # Case where user has not flagged site energy outputs
                else:
                    # Intensities are specified by EMM region or state based on
                    # site energy and require division by site-source factor to
                    # match the user's source energy setting
                    try:
                        intensity_carb_base, intensity_carb_meas = [{
                            yr: self.handyvars.carb_int[bldg_sect][mskeys[3]][
                                mskeys[1]][yr] /
                            self.handyvars.ss_conv[mskeys[3]][yr] for
                            yr in self.handyvars.aeo_years} for n in range(2)]
                    # Intensities are specified nationally based on source
                    # energy and require no further conversion to match the
                    # user's source energy setting
                    except KeyError:
                        intensity_carb_base, intensity_carb_meas = (
                            self.handyvars.carb_int[bldg_sect][
                                mskeys[3]] for n in range(2))
            else:
                # Interpretation of the calculations below is the same as for
                # the case above without fuel switching; the only difference
                # here is that baseline vs. measure settings use different
                # fuels and must therefore be calculated separately

                # Case where use has flagged site energy outputs
                if opts is not None and opts.site_energy is True:
                    # Intensities broken out by EMM region or state
                    try:
                        # Base fuel intensity broken by region
                        intensity_carb_base = self.handyvars.carb_int[
                            bldg_sect][mskeys[3]][mskeys[1]]
                    except KeyError:
                        # Base fuel intensity not broken by region
                        intensity_carb_base = {yr: self.handyvars.carb_int[
                            bldg_sect][mskeys[3]][yr] *
                            self.handyvars.ss_conv[mskeys[3]][yr]
                            for yr in self.handyvars.aeo_years}
                    try:
                        # Measure fuel intensity broken by region
                        intensity_carb_meas = self.handyvars.carb_int[
                            bldg_sect][self.fuel_switch_to][mskeys[1]]
                    except KeyError:
                        # Measure fuel intensity not broken by region
                        intensity_carb_meas = {yr: self.handyvars.carb_int[
                            bldg_sect][self.fuel_switch_to][yr] *
                            self.handyvars.ss_conv[self.fuel_switch_to][yr]
                            for yr in self.handyvars.aeo_years}
                # Case where user has not flagged site energy outputs
                else:
                    try:
                        # Base fuel intensity broken by region
                        intensity_carb_base = {yr: self.handyvars.carb_int[
                            bldg_sect][mskeys[3]][mskeys[1]][yr] /
                            self.handyvars.ss_conv[mskeys[3]][yr]
                            for yr in self.handyvars.aeo_years}
                    except KeyError:
                        # Base fuel intensity not broken by region
                        intensity_carb_base = self.handyvars.carb_int[
                            bldg_sect][mskeys[3]]
                    try:
                        # Measure fuel intensity broken by region
                        intensity_carb_meas = {yr: self.handyvars.carb_int[
                            bldg_sect][self.fuel_switch_to][mskeys[1]][yr] /
                            self.handyvars.ss_conv[self.fuel_switch_to][yr]
                            for yr in self.handyvars.aeo_years}
                    except KeyError:
                        # Measure fuel intensity not broken by region
                        intensity_carb_meas = self.handyvars.carb_int[
                            bldg_sect][self.fuel_switch_to]

            # Set baseline and measure fuel costs, accounting for any
            # fuel switching from baseline technology to measure technology;
            # interpretation of the calculations is the same as for the carbon
            # intensity calculations above
            if self.fuel_switch_to is None:
                # Case where use has flagged site energy outputs
                if opts is not None and opts.site_energy is True:
                    # Costs broken out by EMM region or state
                    try:
                        cost_energy_base, cost_energy_meas = (
                            self.handyvars.ecosts[bldg_sect][mskeys[3]][
                                mskeys[1]] for n in range(2))
                    # National fuel costs
                    except KeyError:
                        cost_energy_base, cost_energy_meas = [{
                            yr: self.handyvars.ecosts[bldg_sect][
                                mskeys[3]][yr] * self.handyvars.ss_conv[
                                mskeys[3]][yr] for yr in
                            self.handyvars.aeo_years} for n in range(2)]
                # Case where user has not flagged site energy outputs
                else:
                    # Costs broken out by EMM region or state
                    try:
                        cost_energy_base, cost_energy_meas = [{
                            yr: self.handyvars.ecosts[
                                bldg_sect][mskeys[3]][mskeys[1]][yr] /
                            self.handyvars.ss_conv[mskeys[3]][yr] for
                            yr in self.handyvars.aeo_years} for
                            n in range(2)]
                    # National fuel costs
                    except KeyError:
                        cost_energy_base, cost_energy_meas = (
                            self.handyvars.ecosts[bldg_sect][mskeys[3]] for
                            n in range(2))
            else:
                # Case where use has flagged site energy outputs
                if opts is not None and opts.site_energy is True:
                    try:
                        # Base fuel cost broken out by region
                        cost_energy_base = self.handyvars.ecosts[bldg_sect][
                            mskeys[3]][mskeys[1]]
                    except KeyError:
                        # Base fuel cost not broken out by region
                        cost_energy_base = {
                            yr: self.handyvars.ecosts[bldg_sect][
                                mskeys[3]][yr] * self.handyvars.ss_conv[
                                mskeys[3]][yr] for yr in
                            self.handyvars.aeo_years}
                    try:
                        # Measure fuel cost broken out by region
                        cost_energy_meas = self.handyvars.ecosts[bldg_sect][
                            self.fuel_switch_to][mskeys[1]]
                    except KeyError:
                        # Measure fuel cost not broken out by region
                        cost_energy_meas = {
                            yr: self.handyvars.ecosts[bldg_sect][
                                self.fuel_switch_to][yr] *
                            self.handyvars.ss_conv[self.fuel_switch_to][yr] for
                            yr in self.handyvars.aeo_years}
                # Case where user has not flagged site energy outputs
                else:
                    try:
                        # Base fuel cost broken out by region
                        cost_energy_base = {
                            yr: self.handyvars.ecosts[bldg_sect][mskeys[3]][
                                mskeys[1]][yr] / self.handyvars.ss_conv[
                                mskeys[3]][yr] for yr in
                            self.handyvars.aeo_years}
                    except KeyError:
                        # Base fuel cost not broken out by region
                        cost_energy_base = self.handyvars.ecosts[bldg_sect][
                            mskeys[3]]
                    try:
                        # Measure fuel cost broken out by region
                        cost_energy_meas = {
                            yr: self.handyvars.ecosts[bldg_sect][
                                self.fuel_switch_to][mskeys[1]][yr] /
                            self.handyvars.ss_conv[self.fuel_switch_to][yr] for
                            yr in self.handyvars.aeo_years}
                    except KeyError:
                        # Measure fuel cost not broken out by region
                        cost_energy_meas = self.handyvars.ecosts[bldg_sect][
                            self.fuel_switch_to]

            # For electricity microsegments in measure scenarios that
            # require the addition of public health cost data, retrieve
            # the appropriate cost data for the given EMM region and add
            if opts is not None and opts.health_costs is True and (
                    "PHC" in self.name and (
                        "electricity" in mskeys or
                        self.fuel_switch_to == "electricity")):
                # Set row/column key information for the public health
                # cost scenario suggested by the measure name
                row_key = [x[1] for x in self.handyvars.health_scn_names if
                           x[0] in self.name][0]
                col_key = [x[2] for x in self.handyvars.health_scn_names if
                           x[0] in self.name][0]
                # Public health costs are specified in units of $/MMBtu source;
                # add a multiplier to account for the case where the energy
                # outputs that these data will be multiplied by are specified
                # in site units; otherwise, set this multiplier to 1
                if opts is not None and opts.site_energy is True:
                    phc_site_mult = self.handyvars.ss_conv["electricity"]
                else:
                    phc_site_mult = {yr: 1 for yr in self.handyvars.aeo_years}
                # Pull the appropriate public health cost information for
                # the current health cost scenario and EMM region; convert
                # from units of cents/primary kWh to $/MMBtu source and add
                # source-site multiplier, if necessary
                phc_dat = {yr: ((self.handyvars.health_scn_data[
                    numpy.in1d(
                        self.handyvars.health_scn_data["Category"], row_key) &
                    numpy.in1d(
                        self.handyvars.health_scn_data["EMM_Region"],
                        mskeys[1])][col_key])[0] / 100) * 293.07107 *
                    phc_site_mult[yr] for yr in self.handyvars.aeo_years}
                # Update energy costs with public health data; in fuel switch
                # case, do not add to baseline as baseline was non-electric
                if self.fuel_switch_to == "electricity":
                    # Update measure
                    cost_energy_meas = {yr: (val + phc_dat[yr]) for yr, val in
                                        cost_energy_meas.items()}
                else:
                    # Update baseline
                    cost_energy_base = {yr: (val + phc_dat[yr]) for yr, val in
                                        cost_energy_base.items()}
                    # Update measure
                    cost_energy_meas = {yr: (val + phc_dat[yr]) for yr, val in
                                        cost_energy_meas.items()}

            # Initialize cost/performance/lifetime, stock/energy, square
            # footage, and new building fraction variables for the baseline
            # microsegment associated with the current key chain
            base_cpl = msegs_cpl
            mseg = msegs
            mseg_sqft_stock = msegs
            new_constr = {"annual new": {}, "total new": {},
                          "total": {}, "new fraction": {}}

            # Initialize a variable for measure relative performance (broken
            # out by year in modeling time horizon)
            rel_perf = {}

            # In cases where measure and baseline cost/performance/lifetime
            # data and/or baseline stock/energy market size data are formatted
            # as nested dicts, loop recursively through dict levels until
            # appropriate terminal value is reached
            for i in range(0, len(mskeys)):
                # For use of state regions, cost/performance/lifetime data
                # are broken out by census division; map the state of the
                # current microsegment to the census division it belongs to,
                # to enable retrieval of the cost/performance/lifetime data
                if (i == 1) and self.handyvars.region_cpl_mapping:
                    mskeys_cpl_map = [
                        x[0] for x in
                        self.handyvars.region_cpl_mapping.items() if
                        mskeys[1] in x[1]][0]
                    # Mapping should yield single string for census division
                    if not isinstance(mskeys_cpl_map, str):
                        raise ValueError("State " + mskeys[1] +
                                         " could not be mapped to a census "
                                         "division for the purpose of "
                                         "retrieving baseline cost, "
                                         "performance, and lifetime data")
                else:
                    mskeys_cpl_map = ''

                # Check whether baseline microsegment cost/performance/lifetime
                # data are in dict format and current key is in dict keys; if
                # so, proceed further with the recursive loop. * Note: dict key
                # hierarchies and syntax are assumed to be consistent across
                # all measure and baseline cost/performance/lifetime and
                # stock/energy market data, with the exception of state data,
                # where cost/performance/lifetime data are broken out by
                # census divisions and must be mapped to the state breakouts
                # used in the stock_energy market data
                if (isinstance(base_cpl, dict) and (
                    (mskeys[i] in base_cpl.keys()) or (
                     mskeys_cpl_map and mskeys_cpl_map in base_cpl.keys())) or
                    mskeys[i] in [
                        "primary", "secondary", "new", "existing", None]):
                    # Skip over "primary", "secondary", "new", and "existing"
                    # keys in updating baseline stock/energy, cost and lifetime
                    # information (this information is not broken out by these
                    # categories)
                    if mskeys[i] not in [
                            "primary", "secondary", "new", "existing", None]:

                        # Restrict base cost/performance/lifetime dict to key
                        # chain info.
                        if mskeys_cpl_map:
                            base_cpl = base_cpl[mskeys_cpl_map]
                        else:
                            base_cpl = base_cpl[mskeys[i]]

                        # Restrict stock/energy dict to key chain info.
                        mseg = mseg[mskeys[i]]

                        # Restrict ft^2 floor area dict to key chain info.
                        if i < 3:  # Note: ft^2 floor area broken out 2 levels
                            mseg_sqft_stock = mseg_sqft_stock[mskeys[i]]

                    # Handle a superfluous 'undefined' key in the ECM
                    # cost, performance, and lifetime fields that is generated
                    # by the 'Add ECM' web form in certain cases *** NOTE: WILL
                    # FIX IN FUTURE UI VERSION ***
                    if (any([type(x) is dict and "undefined" in x.keys()
                             for x in [perf_meas, perf_units, cost_meas,
                                       cost_units, life_meas]])):
                        if isinstance(perf_meas, dict) and "undefined" in \
                           perf_meas.keys():
                            perf_meas = perf_meas["undefined"]
                        if isinstance(perf_units, dict) and "undefined" in \
                           perf_units.keys():
                            perf_units = perf_units["undefined"]
                        if isinstance(cost_meas, dict) and "undefined" in \
                           cost_meas.keys():
                            cost_meas = cost_meas["undefined"]
                        if isinstance(cost_units, dict) and "undefined" in \
                           cost_units.keys():
                            cost_units = cost_units["undefined"]
                        if isinstance(life_meas, dict) and "undefined" in \
                           life_meas.keys():
                            life_meas = life_meas["undefined"]

                    # Check for/handle breakouts of performance, cost,
                    # lifetime, or market scaling information

                    # Determine the full set of potential breakout keys
                    # that should be represented in the given ECM attribute for
                    # the current microsegment level (used to check for
                    # missing information below); for region (level 2), provide
                    # a set of alternate breakout keys that may be used
                    if (any([(type(x) is dict or type(x) is list) for x in [
                        perf_meas, perf_units, cost_meas, cost_units,
                        life_meas, mkt_scale_frac,
                            mkt_scale_frac_source]])):
                        # primary/secondary level
                        if (i == 0):
                            break_keys = ["primary", "secondary"]
                            alt_break_keys = ''
                            err_message = ''
                        # full set of climate breakouts
                        elif (i == 1):
                            break_keys = self.climate_zone
                            # set of alternate regional breakout possibilities
                            alt_break_keys = \
                                self.handyvars.alt_perfcost_brk_map["levels"]
                            err_message = "regions the measure applies to: "
                        # full set of building breakouts
                        elif (i == 2):
                            break_keys = self.bldg_type
                            alt_break_keys = ''
                            err_message = "buildings the measure applies to: "
                        # full set of fuel breakouts
                        elif (i == 3):
                            break_keys = self.fuel_type[mskeys[0]]
                            alt_break_keys = ''
                            err_message = "fuel types the measure applies to: "
                        # full set of end use breakouts
                        elif (i == 4):
                            break_keys = self.end_use[mskeys[0]]
                            alt_break_keys = ''
                            err_message = "end uses the measure applies to: "
                        # full set of technology breakouts
                        elif (i == (len(mskeys) - 2)):
                            break_keys = self.technology[mskeys[0]]
                            alt_break_keys = ''
                            err_message = \
                                "technologies the measure applies to: "
                        # full set of vintage breakouts
                        elif (i == (len(mskeys) - 1)):
                            break_keys = self.structure_type
                            alt_break_keys = ''
                            err_message = \
                                "building vintages the measure applies to: "
                        else:
                            break_keys = ''
                            alt_break_keys = ''
                            err_message = ''

                        # Restrict any measure cost/performance/lifetime/market
                        # scaling info. that is a dict type to key chain info.
                        # - in the process, check to ensure that if there is
                        # breakout information provided for the given level in
                        # the microsegment, this breakout information is
                        # complete (for example, if performance is broken out
                        # by climate region, ALL climate regions should be
                        # present in the breakout keys)

                        # Performance data

                        # Case where data are broken out directly by mseg info.
                        if isinstance(perf_meas, dict) and break_keys and all([
                                x in perf_meas.keys() for x in break_keys]):
                            perf_meas = perf_meas[mskeys[i]]
                        # Case where region is being looped through in the mseg
                        # and performance data use alternate regional breakout
                        elif isinstance(perf_meas, dict) and alt_break_keys:
                            # Determine the alternate regions by which the
                            # performance data are broken out (e.g., IECC, or
                            # - if the analysis uses EMM regions or states -
                            # AIA)
                            alt_key_reg_typ = [
                                x for x in
                                self.handyvars.alt_perfcost_brk_map.keys()
                                if any([
                                    x in y for y in perf_meas.keys()])]
                            # If the alternate regional breakout is supported,
                            # reformat the performance data for subsequent
                            # calculations
                            if len(alt_key_reg_typ) > 0:
                                alt_key_reg_typ = alt_key_reg_typ[0]
                                # Check to ensure the expected alternate
                                # breakout keys are provided
                                if sorted(perf_meas.keys()) == sorted(
                                    self.handyvars.alt_perfcost_brk_map[
                                        alt_key_reg_typ][alt_key_reg_typ]):
                                    # Store data in a list, where the first
                                    # element is a dict of performance data
                                    # broken out by each alternate region and
                                    # the second element is the portion of
                                    # each alternate region that falls in the
                                    # current mseg region
                                    perf_meas = copy.deepcopy([
                                        perf_meas,
                                        self.handyvars.alt_perfcost_brk_map[
                                            alt_key_reg_typ][mskeys[1]]])
                                # If unexpected keys are present, yield error
                                else:
                                    raise KeyError(
                                        self.name +
                                        ' energy performance (energy_'
                                        'efficiency) must be broken out '
                                        'by ALL ' + err_message +
                                        str(break_keys) + ' OR alternate '
                                        'regions ' + alt_break_keys)
                        # Case where performance data broken out by alternate
                        # regions were reformatted as a list and require
                        # further work to finalize as a single value for the
                        # current mseg
                        elif isinstance(perf_meas, list) and \
                                isinstance(perf_meas[0], dict):
                            # Check the first element of the list for
                            # performance data in each of the alternate regions
                            # that is still in dict format and must be keyed
                            # in further by info. for the current mseg.
                            for k in perf_meas[0].keys():
                                if isinstance(perf_meas[0][k], dict) and \
                                    break_keys and all([
                                        x in perf_meas[0][k].keys()
                                        for x in break_keys]):
                                    perf_meas[0][k] = perf_meas[0][k][
                                        mskeys[i]]
                            # If none of the performance data in the first
                            # element of the list needs to be keyed in further,
                            # perform a weighted sum of the data across the
                            # alternate regions into the current mseg region,
                            # to arrive at a final performance value for that
                            # region
                            if all([type(x) != dict for
                                    x in perf_meas[0].values()]):
                                perf_meas = sum([x * y for x, y in zip(
                                    perf_meas[0].values(), perf_meas[1])])
                        # If none of the above cases holds, yield error
                        elif isinstance(perf_meas, dict) and any(
                                [x in perf_meas.keys() for x in break_keys]):
                            raise KeyError(
                                    self.name +
                                    ' energy performance (energy_efficiency) '
                                    'must be broken out '
                                    'by ALL ' + err_message + str(break_keys))
                        # Cost data - same approach as performance data

                        # Case where data are broken out directly by mseg info.
                        if isinstance(cost_meas, dict) and break_keys and \
                            all([x in cost_meas.keys() for
                                 x in break_keys]):
                            cost_meas = cost_meas[mskeys[i]]
                        # Case where region is being looped through in the mseg
                        # and cost data use alternate regional breakout
                        elif isinstance(cost_meas, dict) and alt_break_keys:
                            # Determine the alternate regions by which the
                            # cost data are broken out (e.g., IECC, or
                            # - if the analysis uses EMM regions or states -
                            # AIA)
                            alt_key_reg_typ = [
                                x for x in
                                self.handyvars.alt_perfcost_brk_map.keys()
                                if any([
                                    x in y for y in cost_meas.keys()])]
                            # If the alternate regional breakout is supported,
                            # reformat the cost data for subsequent
                            # calculations
                            if len(alt_key_reg_typ) > 0:
                                alt_key_reg_typ = alt_key_reg_typ[0]
                                # Check to ensure the expected alternate
                                # breakout keys are provided
                                if sorted(cost_meas.keys()) == sorted(
                                    self.handyvars.alt_perfcost_brk_map[
                                        alt_key_reg_typ][alt_key_reg_typ]):
                                    # Store data in a list, where the first
                                    # element is a dict of cost data
                                    # broken out by each alternate region and
                                    # the second element is the portion of
                                    # each alternate region that falls in the
                                    # current mseg region
                                    cost_meas = copy.deepcopy([
                                        cost_meas,
                                        self.handyvars.alt_perfcost_brk_map[
                                            alt_key_reg_typ][mskeys[1]]])
                                # If unexpected keys are present, yield error
                                else:
                                    raise KeyError(
                                        self.name +
                                        ' installed cost (installed_'
                                        'cost) must be broken out '
                                        'by ALL ' + err_message +
                                        str(break_keys) + ' OR alternate '
                                        'regions ' + alt_break_keys)
                        # Case where cost data broken out by alternate
                        # regions were reformatted as a list and require
                        # further work to finalize as a single value for the
                        # current mseg
                        elif isinstance(cost_meas, list) and \
                                isinstance(cost_meas[0], dict):
                            # Check the first element of the list for
                            # cost data in each of the alternate regions
                            # that is still in dict format and must be keyed
                            # in further by info. for the current mseg.
                            for k in cost_meas[0].keys():
                                if isinstance(cost_meas[0][k], dict) and \
                                    break_keys and all([
                                        x in cost_meas[0][k].keys()
                                        for x in break_keys]):
                                    cost_meas[0][k] = cost_meas[0][k][
                                        mskeys[i]]
                            # If none of the cost data in the first element of
                            # the list needs to be keyed in further, perform a
                            # weighted sum of the data across the alternate
                            # regions into the current mseg region, to arrive
                            # at a final cost value for that region
                            if all([type(x) != dict for
                                    x in cost_meas[0].values()]):
                                cost_meas = sum([x * y for x, y in zip(
                                    cost_meas[0].values(), cost_meas[1])])
                        elif isinstance(cost_meas, dict) and any(
                                [x in cost_meas.keys() for x in break_keys]):
                            if alt_break_keys:
                                pass
                            else:
                                raise KeyError(
                                    self.name +
                                    ' installed cost (installed_cost) must '
                                    'be broken out '
                                    'by ALL ' + err_message + str(break_keys))

                        # Performance units data
                        if isinstance(perf_units, dict) and break_keys and \
                                all([x in perf_units.keys() for
                                     x in break_keys]):
                            perf_units = perf_units[mskeys[i]]
                        elif isinstance(perf_units, dict) and any(
                                [x in perf_units.keys() for x in break_keys]):
                            raise KeyError(
                                self.name +
                                ' energy performance units ('
                                'energy_efficiency_units) must be broken '
                                'out by ALL ' + err_message +
                                str(break_keys))
                        # Cost units data
                        if isinstance(cost_units, dict) and break_keys and \
                            all([x in cost_units.keys() for
                                 x in break_keys]):
                            cost_units = cost_units[mskeys[i]]
                        elif isinstance(cost_units, dict) and any(
                                [x in cost_units.keys() for x in break_keys]):
                            raise KeyError(
                                self.name +
                                ' installed cost units (installed_cost_'
                                'units) must be broken out '
                                'by ALL ' + err_message + str(break_keys))
                        # Lifetime data
                        if isinstance(life_meas, dict) and break_keys and all([
                                x in life_meas.keys() for x in break_keys]):
                            life_meas = life_meas[mskeys[i]]
                        elif isinstance(life_meas, dict) and any(
                                [x in life_meas.keys() for x in break_keys]):
                            raise KeyError(
                                self.name +
                                ' lifetime (product_lifetime) must be '
                                'broken out '
                                'by ALL ' + err_message + str(break_keys))
                        # Market scaling fractions
                        if isinstance(mkt_scale_frac, dict) and break_keys \
                            and all([x in mkt_scale_frac.keys() for
                                     x in break_keys]):
                            mkt_scale_frac = mkt_scale_frac[mskeys[i]]
                        elif isinstance(mkt_scale_frac, dict) and any(
                                [x in mkt_scale_frac.keys() for
                                 x in break_keys]):
                            raise KeyError(
                                self.name +
                                ' market scaling fractions (market_'
                                'scaling_fractions) must be '
                                'broken out by ALL ' + err_message +
                                str(break_keys))
                        # Market scaling fraction source
                        if isinstance(mkt_scale_frac_source, dict) and \
                            break_keys and all([
                                x in mkt_scale_frac_source.keys() for
                                x in break_keys]):
                            mkt_scale_frac_source = \
                                mkt_scale_frac_source[mskeys[i]]
                        elif isinstance(mkt_scale_frac_source, dict) and any(
                                [x in mkt_scale_frac_source.keys() for
                                 x in break_keys]):
                            raise KeyError(
                                self.name +
                                ' market scaling fraction source (market_'
                                'scaling_fraction_source) must be '
                                'broken out by ALL ' + err_message +
                                str(break_keys))

                # If no key match, break the loop
                else:
                    if mskeys[i] is not None:
                        mseg = {}
                    break

            # Continue loop if key chain doesn't yield "stock"/"energy" keys
            if any([x not in list(mseg.keys()) for x in ["stock", "energy"]]):
                continue
            # Continue loop if time-sensitive valuation is required and the
            # current microsegment technology does not have the necessary
            # load shape information (pertinent to internal heat gains)
            elif (((self.energy_outputs["tsv_metrics"] is not False or
                   opts.sect_shapes is True) or self.tsv_features is not None)
                  and (mskeys[4] in ["heating", "secondary heating"] and
                       mskeys[-2] in self.handyvars.heat_ls_tech_scrn)):
                continue
            # Continue loop if key chain yields "stock"/"energy" keys but
            # the stock or energy data are missing
            elif any([x == {} for x in [mseg["stock"], mseg["energy"]]]):
                if mskeys[-2] not in stk_energy_warn:
                    stk_energy_warn.append(mskeys[-2])
                    verboseprint(
                        opts.verbose,
                        "WARNING: ECM '" + self.name +
                        "' missing valid baseline "
                        "stock/energy data " +
                        "for technology '" + str(mskeys[-2]) +
                        "'; removing technology from analysis")
                # Add to the overall number of key chains that yield "stock"/
                # "energy" keys (but in this case, are missing data)
                valid_keys += 1
                continue
            # Otherwise update all stock/energy/cost information for each year
            else:
                # Restrict count of key chains with valid stock/energy data to
                # "primary" microsegment key chains only (the key chain
                # count is used later in stock and stock cost calculations,
                # which secondary microsegments do not contribute to)
                if mskeys[0] == "primary":
                    valid_keys += 1
                    valid_keys_stk_energy += 1
                    # Flag use of ft^2 floor area as stock when number of stock
                    # units is unavailable, or in any residential add-on ECM
                    # case where user has not defined the add-on cost in terms
                    # of '$/unit'
                    if mseg["stock"] == "NA" or (
                        bldg_sect == "residential" and
                        '$/unit' not in cost_units and
                            self.measure_type == "add-on"):
                        sqft_subst = 1

                # If sub-market scaling fraction is non-numeric (indicating
                # it is not applicable to current microsegment), set to 1
                if mkt_scale_frac is None or isinstance(mkt_scale_frac, dict):
                    mkt_scale_frac = 1

                # If a sub-market scaling fraction is to be applied to the
                # current baseline microsegment, check that the source
                # information for the fraction is sufficient; if not, remove
                # the measure from further analysis
                if isinstance(mkt_scale_frac_source, dict) and \
                        "title" in mkt_scale_frac_source.keys():
                    # Establish sub-market fraction general source, URL, and
                    # derivation information

                    # Set general source info. for the sub-market fraction
                    source_info = [
                        mkt_scale_frac_source['title'],
                        mkt_scale_frac_source['organization']]
                    # Set URL for the sub-market fraction
                    url = mkt_scale_frac_source['URL']
                    # Set information about how sub-market fraction was derived
                    frac_derive = mkt_scale_frac_source['fraction_derivation']

                    # Check the validity of sub-market fraction source, URL,
                    # and derivation information

                    # Check sub-market fraction general source information,
                    # yield warning if source information is invalid and
                    # invalid source information flag hasn't already been
                    # raised for this measure
                    if sbmkt_source_invalid != 1 and (any([
                        not isinstance(x, str) or
                       len(x) < 2 for x in source_info]) is True):
                        # Print invalid source information warning
                        warnings.warn(
                            "WARNING: '" + self.name + "' has invalid "
                            "sub-market scaling fraction source title, author,"
                            " organization, and/or year information")
                        # Set invalid source information flag to 1
                        sbmkt_source_invalid = 1
                    # Check sub-market fraction URL, yield warning if URL is
                    # invalid and invalid URL flag hasn't already been raised
                    # for this measure
                    if sbmkt_url_invalid != 1:
                        # Parse the URL into components (addressing scheme,
                        # network location, etc.)
                        url_check = urlparse(url)
                        # Check for valid URL address scheme and network
                        # location components
                        if (any([len(url_check.scheme),
                                 len(url_check.netloc)]) == 0 or
                            all([x not in url_check.netloc for x in
                                 self.handyvars.valid_submkt_urls])):
                            # Print invalid URL warning
                            warnings.warn(
                                "WARNING: '" + self.name + "' has invalid "
                                "sub-market scaling fraction source URL "
                                "information")
                            # Set invalid URL flag to 1
                            sbmkt_url_invalid = 1
                    # Check sub-market fraction derivation information, yield
                    # warning if invalid
                    if not isinstance(frac_derive, str):
                        # Print invalid derivation warning
                        warnings.warn(
                            "WARNING: '" + self.name + "' has invalid "
                            "sub-market scaling fraction derivation "
                            "information")
                        # Set invalid derivation flag to 1
                        sbmkt_derive_invalid = 1

                    # If the derivation information or the general source
                    # and URL information for the sub-market fraction are
                    # invalid, yield warning that measure will be removed from
                    # analysis, reset the current valid contributing key chain
                    # count to a 999 flag, and flag the measure as inactive
                    # such that it will be removed from all further routines
                    if sbmkt_derive_invalid == 1 or (
                            sbmkt_source_invalid == 1 and
                            sbmkt_url_invalid == 1):
                        # Print measure removal warning
                        warnings.warn(
                            "WARNING (CRITICAL): '" + self.name + "' has "
                            "insufficient sub-market source information and "
                            "will be removed from analysis")
                        # Reset measure 'active' attribute to zero
                        self.remove = True
                        # Break from all further baseline stock/energy/carbon
                        # and cost information updates for the measure
                        break

                # Seed the random number generator such that performance, cost,
                # and lifetime draws are consistent across all microsegments
                # that contribute to a measure's master microsegment (e.g, if
                # measure performance, cost, and/or lifetime distributions
                # are identical relative to two contributing baseline
                # microsegments, the numpy arrays yielded by the random number
                # generator for these measure parameters and microsegments
                # will also be identical)
                numpy.random.seed(rnd_sd)

                # If the measure performance/cost/lifetime variable is list
                # with distribution information, sample values accordingly
                if isinstance(perf_meas, list) and isinstance(perf_meas[0],
                                                              str):
                    # Sample measure performance values
                    perf_meas = self.rand_list_gen(
                        perf_meas, self.handyvars.nsamples)
                    # Set any measure performance values less than zero to
                    # zero, for cases where performance isn't relative
                    if perf_units != 'relative savings (constant)' and \
                        type(perf_units) is not list and any(
                            perf_meas < 0) is True:
                        perf_meas[numpy.where(perf_meas < 0)] = 0
                # Ensure that the code errors if a user has requested
                # data from EnergyPlus simulations anywhere in the ECM's
                # energy performance input value (currently unsupported)
                elif perf_meas == "From EnergyPlus":
                    raise ValueError(
                        "ECM '" + self.name + "' requires EnergyPlus data for "
                        "its performance input; EnergyPlus-based ECM "
                        "performance data are currently unsupported.")

                if isinstance(cost_meas, list) and isinstance(cost_meas[0],
                                                              str):
                    # Sample measure cost values
                    cost_meas = self.rand_list_gen(
                        cost_meas, self.handyvars.nsamples)
                    # Set any measure cost values less than zero to zero
                    if any(cost_meas < 0) is True:
                        cost_meas[numpy.where(cost_meas < 0)] = 0
                if isinstance(life_meas, list) and isinstance(life_meas[0],
                                                              str):
                    # Sample measure lifetime values
                    life_meas = self.rand_list_gen(
                        life_meas, self.handyvars.nsamples)
                    # Set any measure lifetime values in list less than zero
                    # to 1
                    if any(life_meas < 0) is True:
                        life_meas[numpy.where(life_meas < 0)] = 1
                elif isinstance(life_meas, float) or \
                        isinstance(life_meas, int) and mskeys[0] == "primary":
                    # Set measure lifetime point values less than zero to 1
                    # (minimum lifetime)
                    if life_meas < 1:
                        life_meas = 1

                # For primary microsegments, set baseline technology cost,
                # cost units, performance, performance units, and lifetime, if
                # data are available on these parameters; if data are not
                # available, remove primary microsegment from further analysis,
                # and later remove any associated secondary microsegments
                if mskeys[0] == "primary":
                    try:
                        # Check for cases where baseline data are available but
                        # set to zero, "NA", or 999 values (excepting cases
                        # where baseline cost is expected to be zero). In such
                        # cases, raise a ValueError
                        if any([((("lighting" in mskeys and (isinstance(
                            x[1], float) and round(x[1]) in [0, 999])) or
                            x[1] in [0, "NA", 999]) and mskeys[-2] not in
                            self.handyvars.zero_cost_tech) for x in base_cpl[
                                "installed cost"]["typical"].items()]) or any([
                                (("lighting" in mskeys and (isinstance(
                                    y[1], float) and round(y[1]) in [0, 999]))
                                 or y[1] in [0, "NA", 999]) for y in base_cpl[
                                "performance"]["typical"].items()]):
                            raise ValueError
                        # Handle lifetime separately, as in some cases it may
                        # be broken out by year, and in others it is a single
                        # point value, when available
                        if (((type(base_cpl["lifetime"]["average"]) in [
                            float, int]) and base_cpl[
                            "lifetime"]["average"] == 0) or (
                            (type(base_cpl["lifetime"]["average"]) is dict) and
                            any([z[1] in [0, "NA"] for z in base_cpl[
                                "lifetime"]["average"].items()]))):
                            raise ValueError

                        # Set baseline performance; try for case where baseline
                        # performance is broken out by new and existing
                        # vintage; given an exception, expect a single set of
                        # values across both vintages
                        try:
                            perf_base = base_cpl[
                                "performance"]["typical"][mskeys[-1]]
                        except KeyError:
                            perf_base = base_cpl[
                                "performance"]["typical"]

                        # Set baseline performance units
                        perf_base_units = base_cpl["performance"]["units"]

                        # Handle case where measure units do not equal
                        # baseline units and baseline units cannot be
                        # converted to measure units; the baseline segment
                        # must be removed from the analysis
                        if (not (
                            perf_units == 'relative savings (constant)' or
                           (isinstance(perf_units, list) and perf_units[0] ==
                            'relative savings (dynamic)')) and
                                (perf_units != perf_base_units)) and \
                                (perf_base_units in
                                 self.handyvars.tech_units_rmv):
                            # Warn user of the removal of the baseline segment
                            if mskeys[-2] is not None and \
                                    mskeys[-2] not in cpl_warn:
                                cpl_warn.append(mskeys[-2])
                                verboseprint(
                                    opts.verbose,
                                    "WARNING: ECM '" + self.name +
                                    "' uses invalid performance units for "
                                    "technology '" + str(mskeys[-2]) +
                                    "' (requires " + str(perf_base_units) +
                                    "); removing technology from analysis")
                            # Continue to the next microsegment
                            continue
                        # Handle case where measure units do not equal baseline
                        # units but baseline units can be converted to measure
                        # units
                        elif (not (
                            perf_units == 'relative savings (constant)' or
                              (isinstance(perf_units, list) and
                               perf_units[0] == 'relative savings (dynamic)'))
                                and (perf_units != perf_base_units)) and \
                            (perf_units in
                                self.handyvars.tech_units_map.keys()):
                            convert_fact = self.handyvars.tech_units_map[
                                perf_units][perf_base_units]
                            # Convert base performance values to values in
                            # measure performance units
                            perf_base = {yr: (perf_base[yr] * convert_fact) for
                                         yr in self.handyvars.aeo_years}
                            # Set baseline performance units to measure units
                            perf_base_units = perf_units
                            # Warn the user of the value/units conversions
                            if mskeys[-2] is not None and \
                                    mskeys[-2] not in cpl_warn:
                                verboseprint(
                                    opts.verbose, "WARNING: ECM '" +
                                    self.name + "' uses units of COP for "
                                    "technology '" + str(mskeys[-2]) +
                                    "' (requires " + str(perf_base_units) +
                                    "); base units changed to " +
                                    str(perf_base_units) + " and base values"
                                    " multiplied by " + str(convert_fact))

                        # Handle case where user has defined a 'windows
                        # conduction' technology without 'windows solar',
                        # or vice versa, and the additional market must be
                        # added at the baseline performance level (relative
                        # savings percentage of zero)
                        if not isinstance(perf_units, list) and \
                            perf_units != 'relative savings (constant)' and (
                            perf_base_units != perf_units and any([
                                x is not None and "windows" in x for
                                x in mskeys])):
                            perf_meas, perf_units = [
                                0, "relative savings (constant)"]

                        # Handle residential add-on ECM case where user has not
                        # defined the add-on cost in terms of '$/unit'; in such
                        # cases, baseline costs should always be zero, in units
                        # of $/ft^2 floor
                        if bldg_sect == "residential" and (
                            '$/unit' not in cost_units and
                                self.measure_type == "add-on"):
                            cost_base, cost_base_units = \
                                [{yr: 0 for yr in self.handyvars.aeo_years},
                                 "$/ft^2 floor"]
                        # For all other baseline technologies, pull baseline
                        # costs and cost units in as is from the baseline data
                        else:
                            # Set baseline cost units
                            cost_base, cost_base_units = \
                                [base_cpl["installed cost"]["typical"],
                                 base_cpl["installed cost"]["units"]]

                        # Set baseline lifetime; handle some cases where base
                        # lifetime is not broken out across all years; extend
                        # across year range in these cases
                        if type(base_cpl["lifetime"]["average"]) in [
                                float, int]:
                            life_base = {
                                yr: base_cpl["lifetime"]["average"] for
                                yr in self.handyvars.aeo_years}
                        elif type(base_cpl["lifetime"]["average"]) is dict:
                            life_base = base_cpl["lifetime"]["average"]
                        else:
                            raise ValueError(
                                "Lifetime data for microsegment " +
                                mskeys + " must be a dict or point value")
                        # Adjust residential baseline lighting lifetimes to
                        # reflect the fact that input data assume 24 h/day of
                        # lighting use, rather than 3 h/day as assumed for
                        # measure lifetime definitions
                        if bldg_sect == "residential" and \
                                mskeys[4] == "lighting":
                            life_base = {
                                yr: life_base[yr] * (24 / 3) for
                                yr in self.handyvars.aeo_years}
                        # Add to count of primary microsegment key chains with
                        # valid cost/performance/lifetime data
                        valid_keys_cpl += 1
                    except (TypeError, ValueError):
                        # In cases with missing baseline technology cost,
                        # performance, or lifetime data where the user
                        # specifies the measure as an 'add-on' type AND
                        # specifies relative savings for energy performance
                        # units, set the baseline cost to zero and - if no
                        # baseline lifetime data are available - set baseline
                        # lifetime to 10 to ensure that all subsequent stock
                        # and energy impact calculations will continue for that
                        # baseline segment. Note: this marks a special
                        # exception to the general rule that baseline
                        # market segments without complete unit-level cost,
                        # performance, and/or lifetime data will be removed
                        # from further analysis. The exception is needed to
                        # handle controls-focused ECMs that apply to baseline
                        # market segments with poor technology-level data - for
                        # example, residential vacancy sensors that reduce MELs
                        # energy use by turning off power draws to circuits
                        # when an occupant isn't home. The user will now be
                        # able to evaluate such measures given measure relative
                        # performance, incremental cost, and lifetime data
                        if self.measure_type == "add-on" and \
                                perf_units == "relative savings (constant)":
                            # Set baseline cost to zero with appropriate units
                            # for the building sector of interest
                            cost_base = {yr: 0 for
                                         yr in self.handyvars.aeo_years}
                            if bldg_sect == "commercial" or sqft_subst == 1:
                                cost_base_units = "$/ft^2 floor"
                            else:
                                cost_base_units = "$/unit"
                            # Attempt to retrieve baseline lifetime data, if
                            # that fails set baseline lifetime to 10 years
                            try:
                                if any([x[1] in [0, "NA"] for x in base_cpl[
                                        "lifetime"]["average"].items()]):
                                    raise ValueError
                                life_base = base_cpl["lifetime"]["average"]
                            except (TypeError, ValueError):
                                life_base = {yr: 10 for
                                             yr in self.handyvars.aeo_years}
                            # Add to count of primary microsegment key chains
                            # with valid cost/performance/lifetime data,
                            # given special exception
                            valid_keys_cpl += 1
                            # Nevertheless, warn the user about the
                            # special exception and how it's handled
                            if mskeys[-2] not in cpl_warn:
                                cpl_warn.append(mskeys[-2])
                                verboseprint(
                                    opts.verbose,
                                    "WARNING: ECM '" + self.name +
                                    "' missing valid baseline "
                                    "cost/performance/lifetime data " +
                                    "for technology '" + str(mskeys[-2]) +
                                    "'; ECM is 'add-on' type with constant " +
                                    "relative savings and technology will " +
                                    "remain in analysis with cost of zero; " +
                                    "; if lifetime data are missing, " +
                                    "lifetime is set to 10 years")

                        # Additionally, include an exception for commercial
                        # lighting cases, where some segments of commercial
                        # lighting energy use at or near zero contribution lack
                        # cost, performance, and lifetime data but do not
                        # have enough influence on results to warrant
                        # additional adjustments to associated secondary
                        # microsegments. In such cases, set the baseline cost
                        # and performance to the measure cost and performance;
                        # if lifetime data are not available, set the baseline
                        # lifetime to 10 years.
                        elif "lighting" in mskeys and \
                                bldg_sect == "commercial":
                            # Set baseline performance/units to measure
                            # performance/units
                            perf_base = {yr: perf_meas for
                                         yr in self.handyvars.aeo_years}
                            perf_base_units = perf_units
                            # Set baseline cost/units to measure cost/units;
                            # account for possible formatting of measure costs
                            # as a dict broken out by year
                            cost_base = {yr: cost_meas if not isinstance(
                                cost_meas, dict) else cost_meas[yr] for
                                yr in self.handyvars.aeo_years}
                            cost_base_units = cost_units
                            # Attempt to retrieve baseline lifetime data, if
                            # that fails set baseline lifetime to 10 years
                            try:
                                if any([x[1] in [0, "NA"] for x in base_cpl[
                                        "lifetime"]["average"].items()]):
                                    raise ValueError
                                life_base = base_cpl["lifetime"]["average"]
                            except (TypeError, ValueError):
                                life_base = {yr: 10 for
                                             yr in self.handyvars.aeo_years}
                            # Add to count of primary microsegment key chains
                            # with valid cost/performance/lifetime data,
                            # given special exception
                            valid_keys_cpl += 1
                            # Nevertheless, warn the user about the special
                            # exception and how it's handled
                            if mskeys[-2] not in cpl_warn:
                                cpl_warn.append(mskeys[-2])
                                verboseprint(
                                    opts.verbose,
                                    "WARNING: ECM '" + self.name +
                                    "' missing valid baseline "
                                    "cost/performance/lifetime data " +
                                    "for technology '" + str(mskeys[-2]) +
                                    "'; technology applies to special " +
                                    "commercial lighting case and will " +
                                    "remain in analysis at same cost/" +
                                    "performance as ECM; if lifetime data " +
                                    "are missing, lifetime is set to 10 years")
                        # For all other cases, record missing baseline data; if
                        # in verbose mode and the user has not already been
                        # warned about missing data for the given technology,
                        # print warning; exclude technologies without data from
                        # further analysis
                        else:
                            if mskeys[-2] is not None and \
                                    mskeys[-2] not in cpl_warn:
                                cpl_warn.append(mskeys[-2])
                                verboseprint(
                                    opts.verbose,
                                    "WARNING: ECM '" + self.name +
                                    "' missing valid baseline "
                                    "cost/performance/lifetime data " +
                                    "for technology '" + str(mskeys[-2]) +
                                    "'; removing technology from analysis")
                            continue
                else:
                    # Set baseline cost and performance characteristics for any
                    # remaining secondary microsegments to that of the measure
                    # and baseline lifetime to ten years (typical commercial
                    # lighting lifetime)
                    cost_base, perf_base, life_base = [
                        {yr: x for yr in self.handyvars.aeo_years} for x in [
                            cost_meas, perf_meas, 10]]
                    cost_base_units, perf_base_units = [cost_units, perf_units]

                # Convert user-defined measure cost units to align with
                # baseline cost units, given input cost conversion data
                if mskeys[0] == "primary" and cost_base_units != cost_units:
                    # Case where measure cost has not yet been recast across
                    # AEO years
                    if not isinstance(cost_meas, dict):
                        cost_meas, cost_units = self.convert_costs(
                            convert_data, bldg_sect, mskeys, cost_meas,
                            cost_units, cost_base_units, opts.verbose)
                    # Case where measure cost has been recast across AEO years
                    else:
                        # Loop through all AEO years by which measure cost
                        # data are broken out and make the conversion
                        for yr in self.handyvars.aeo_years:
                            cost_meas[yr], cost_units = self.convert_costs(
                                convert_data, bldg_sect, mskeys, cost_meas[yr],
                                cost_units, cost_base_units, opts.verbose)
                    cost_converts += 1
                    # Add microsegment building type to cost conversion
                    # tracking list for cases where cost conversion need
                    # occur only once per building type
                    bldgs_costconverted[mskeys[2]] = [cost_meas, cost_units]

                # Determine relative measure performance after checking for
                # consistent baseline/measure performance and cost units;
                # make an exception for cases where performance is specified
                # in 'relative savings' units (no explicit check
                # of baseline units needed in this case)
                if (perf_units == 'relative savings (constant)' or
                   (isinstance(perf_units, list) and perf_units[0] ==
                    'relative savings (dynamic)') or
                    perf_base_units == perf_units) and (
                        mskeys[0] == "secondary" or
                        cost_base_units == cost_units):

                    # Relative performance calculation depends on whether the
                    # performance units are already specified as 'relative
                    # savings' over the baseline technology; if not, the
                    # calculation depends on the technology case (i.e. COP  of
                    # 4 is higher relative performance than a baseline COP 3,
                    # but 1 ACH50 is higher rel. performance than 13 ACH50).
                    # Note that relative performance values are stored in a
                    # dict with keys for each year in the modeling time horizon
                    if perf_units == 'relative savings (constant)' or \
                       (isinstance(perf_units, list) and perf_units[0] ==
                            'relative savings (dynamic)'):
                        # In a commercial lighting case where the relative
                        # savings impact of the lighting change on a secondary
                        # end use (heating/cooling) has not been user-
                        # specified, draw from the "light_scnd_autoperf"
                        # variable to determine relative performance for this
                        # secondary microsegment; in all other cases where
                        # relative savings are directly user-specified in the
                        # measure definition, calculate relative performance
                        # based on the relative savings value
                        if type(perf_meas) != numpy.ndarray and \
                           perf_meas == "Missing (secondary lighting)":
                            rel_perf = light_scnd_autoperf
                        else:
                            # Set the original measure relative savings value
                            # (potentially adjusted via re-baselining)
                            perf_meas_orig = perf_meas
                            # Loop through all years in modeling time horizon
                            # and calculate relative measure performance
                            for yr in self.handyvars.aeo_years:
                                # If relative savings must be adjusted to
                                # account for changes in baseline performance,
                                # scale the relative savings value by the
                                # ratio of current year baseline to that of
                                # an anchor year specified with the measure
                                # performance units
                                if isinstance(perf_units, list):
                                    try:
                                        if perf_base_units not in \
                                            self.handyvars.\
                                                inverted_relperf_list:
                                            perf_meas = 1 - (perf_base[yr] / (
                                                perf_base[str(perf_units[1])] /
                                                (1 - perf_meas_orig)))
                                        else:
                                            perf_meas = 1 - ((
                                                perf_base[str(perf_units[1])] *
                                                (1 - perf_meas_orig)) /
                                                perf_base[yr])
                                    except ZeroDivisionError:
                                        verboseprint(
                                            opts.verbose,
                                            "WARNING: Measure '" + self.name +
                                            "' has baseline " +
                                            "or measure performance of zero;" +
                                            " baseline and measure " +
                                            "performance set equal")
                                    # Ensure that the adjusted relative savings
                                    # fraction is not greater than 1 or less
                                    # than 0 if not originally specified as
                                    # less than 0. * Note: savings will
                                    # initially be specified as less than zero
                                    # in lighting efficiency cases, which
                                    # secondarily increase heating energy use
                                    if type(perf_meas) == numpy.array:
                                        if any(perf_meas > 1):
                                            perf_meas[
                                                numpy.where(perf_meas > 1)] = 1
                                        elif any(perf_meas < 0) and \
                                                all(perf_meas_orig) > 0:
                                            perf_meas[
                                                numpy.where(perf_meas < 0)] = 0
                                    elif type(perf_meas) != numpy.array and \
                                            perf_meas > 1:
                                        perf_meas = 1
                                    elif type(perf_meas) != numpy.array and \
                                            perf_meas < 0 and \
                                            perf_meas_orig > 0:
                                        perf_meas = 0
                                # Calculate relative performance
                                rel_perf[yr] = 1 - perf_meas
                    elif perf_units not in \
                            self.handyvars.inverted_relperf_list:
                        for yr in self.handyvars.aeo_years:
                            # Suppress numpy warnings about ZeroDivision
                            # errors, which are handled explicitly
                            with numpy.errstate(all='ignore'):
                                try:
                                    # In cases where an ECM enhances the
                                    # performance of a baseline technology,
                                    # add the ECM and baseline performance
                                    # values and compare to the baseline
                                    # performance value; otherwise, compare
                                    # the ECM performance
                                    # value to the baseline performance value
                                    if self.measure_type == "add-on":
                                        rel_perf[yr] = (
                                            perf_base[yr] /
                                            (perf_meas + perf_base[yr]))
                                    else:
                                        rel_perf[yr] = (
                                            perf_base[yr] / perf_meas)
                                except ZeroDivisionError:
                                    verboseprint(
                                        opts.verbose,
                                        "WARNING: Measure '" + self.name +
                                        "' has measure performance of zero; " +
                                        "baseline and measure performance set "
                                        + "equal")
                                    rel_perf[yr] = 1
                                # Ensure that relative performance is a finite
                                # number; if not, set to 1
                                if (type(rel_perf[yr]) != numpy.ndarray and (
                                    not numpy.isfinite(rel_perf[yr]))) or (
                                   type(rel_perf[yr]) == numpy.ndarray and
                                   any([not numpy.isfinite(x) for
                                        x in rel_perf[yr]])):
                                    rel_perf[yr] = 1
                    else:
                        for yr in self.handyvars.aeo_years:
                            try:
                                rel_perf[yr] = (perf_meas / perf_base[yr])
                            except ZeroDivisionError:
                                verboseprint(
                                    opts.verbose,
                                    "WARNING: Measure '" + self.name +
                                    "' has baseline performance of zero; " +
                                    "baseline and measure performance set " +
                                    "equal")
                                rel_perf[yr] = 1

                    # If looping through a commercial lighting microsegment
                    # where secondary end use effects (heating/cooling) are not
                    # specified by the user and must be added, store the
                    # relative performance of the efficient lighting equipment
                    # for later use in updating these secondary microsegments
                    if mskeys[4] == "lighting" and mskeys[0] == "primary" and \
                            light_scnd_autoperf is True:
                        light_scnd_autoperf = rel_perf

                    # Check whether the user has optionally locked measure
                    # relative performance across the model time horizon to
                    # that of the measure's market entry year (for example,
                    # a user may wish to assume that the 'Best Available'
                    # measure on the market maintains a consistent degree of
                    # improvement over the comparable baseline technology
                    # across its lifetime). In this case, set the measure's
                    # relative performance value for all years to that
                    # calculated for its market entry year; *NOTE*, preclude
                    # consistent performance improvements for prospective
                    # measures, which tend to already be at performance limits
                    if opts.rp_persist is True and all([
                        x not in self.name for x in [
                            "Prospective", "Emerging", "Target"]]):
                        rel_perf = {
                            yr: rel_perf[str(self.market_entry_year)] for
                            yr in self.handyvars.aeo_years}
                        # If performance is escalated at the baseline rate,
                        # also increase/decrease measure cost at the baseline
                        # rate, anchored on the measure market entry year

                        # Determine baseline cost change rate for the
                        # current microsegment; set to 1 if baseline cost
                        # at market entry is zero
                        cost_chg = {yr: cost_base[yr] / cost_base[
                            str(self.market_entry_year)] if (numpy.isfinite(
                                cost_base[str(self.market_entry_year)]) and
                                cost_base[str(self.market_entry_year)] != 0)
                            else 1 for yr in self.handyvars.aeo_years}
                        # Multiple measure cost by rate of change in baseline
                        # cost for each year in the AEO horizon; handle case
                        # where measure cost has not yet been broken out by
                        # AEO year
                        try:
                            cost_meas = {yr: cost_meas * cost_chg[yr] for yr in
                                         self.handyvars.aeo_years}
                        except TypeError:
                            cost_meas = {yr: cost_meas[str(
                                self.market_entry_year)] * cost_chg[yr] for
                                yr in self.handyvars.aeo_years}
                    else:
                        # If measure performance is not escalated at the
                        # baseline rate, assume no mapping between changes in
                        # baseline cost and measure cost and set measure cost
                        # to the same value across all AEO years
                        if not isinstance(cost_meas, dict):
                            cost_meas = {yr: cost_meas for yr in
                                         self.handyvars.aeo_years}
                else:
                    raise KeyError(
                        "Invalid performance or cost units for ECM '" +
                        self.name + "'")

                # Set stock turnover info. and consumer choice info. to
                # appropriate building type
                if bldg_sect == "residential":
                    # Update new building construction information
                    for yr in self.handyvars.aeo_years:
                        # Find new and total buildings for current year
                        new_constr["annual new"][yr] = \
                            mseg_sqft_stock["new homes"][yr]
                        new_constr["total"][yr] = \
                            mseg_sqft_stock["total homes"][yr]

                    # Update technology choice parameters needed to choose
                    # between multiple efficient technology options that
                    # access this baseline microsegment. For the residential
                    # sector, these parameters are found in the baseline
                    # technology cost, performance, and lifetime JSON
                    if mskeys[0] == "secondary":
                        choice_params = {}  # No choice params for 2nd msegs
                    else:
                        # Add technology choice parameter scaling factor for
                        # residential ECMs with costs specified in units of
                        # $/ft^2 floor. This scaling factor effectively
                        # translates the technology choice cost inputs
                        # for such ECMs from $/ft^2 floor to $/unit
                        if sqft_subst == 1:
                            # Calculate the choice parameter scaling factor as
                            # the typical square footage of the building type
                            # divided by the typical number of technology units
                            # for the current end use and building type. If the
                            # necessary data for the calculation are not
                            # available, set the scaling factor to one
                            try:
                                choice_param_adj = \
                                    self.handyvars.res_typ_sf_household[
                                        mskeys[2]] / \
                                    self.handyvars.res_typ_units_household[
                                        mskeys[4]][mskeys[2]]
                            except KeyError:
                                try:
                                    choice_param_adj = \
                                        self.handyvars.res_typ_sf_household[
                                            mskeys[2]] / 1
                                except KeyError:
                                    choice_param_adj = 1
                        else:
                            choice_param_adj = 1

                        # Use try/except to handle cases with missing
                        # or invalid consumer choice data (where choice
                        # parameter values of 0 or "NA" are invalid)
                        try:
                            if any([x[1] in [0, "NA"] for x in base_cpl[
                                "consumer choice"]["competed market share"][
                                    "parameters"]["b1"].items()]):
                                raise ValueError
                            choice_params = {
                                "b1": {
                                    key: base_cpl["consumer choice"][
                                        "competed market share"]["parameters"][
                                        "b1"][yr] * choice_param_adj for key in
                                    self.handyvars.aeo_years},
                                "b2": {
                                    key: base_cpl["consumer choice"][
                                        "competed market share"]["parameters"][
                                        "b2"][yr] * choice_param_adj for key in
                                    self.handyvars.aeo_years}}
                            # Add to count of primary microsegment key chains
                            # with valid consumer choice data
                            valid_keys_consume += 1
                        # Update invalid consumer choice parameters
                        except (ValueError, TypeError, KeyError):
                            # Record missing consumer data for primary
                            # technologies; if in verbose mode and the user
                            # has not already been warned about missing data
                            # for the given technology, print warning message
                            if mskeys[0] == "primary":
                                if mskeys[4] not in consume_warn:
                                    consume_warn.append(mskeys[4])
                                    verboseprint(
                                        opts.verbose,
                                        "WARNING: ECM '" + self.name +
                                        "' missing valid consumer choice "
                                        "data for end use '" + str(mskeys[4]) +
                                        "'; using default choice data for " +
                                        "refrigeration end use")
                            choice_params = {
                                "b1": {
                                    key: self.handyvars.deflt_choice[0] *
                                    choice_param_adj for key in
                                    self.handyvars.aeo_years},
                                "b2": {
                                    key: self.handyvars.deflt_choice[1] *
                                    choice_param_adj for key in
                                    self.handyvars.aeo_years}}
                else:
                    # Update new building construction information
                    for yr in self.handyvars.aeo_years:
                        # Find new and total square footage for current year
                        new_constr["annual new"][yr] = \
                            mseg_sqft_stock["new square footage"][yr]
                        new_constr["total"][yr] = \
                            mseg_sqft_stock["total square footage"][yr]

                    # Update technology choice parameters needed to choose
                    # between multiple efficient technology options that
                    # access this baseline microsegment. For the commercial
                    # sector, these parameters are specified at the
                    # beginning of run.py in com_timeprefs (* Note:
                    # com_timeprefs info. may eventually be integrated into
                    # the  baseline technology cost, performance, and
                    # lifetime JSON as for residential)
                    if mskeys[0] == "secondary":
                        choice_params = {}  # No choice params for 2nd msegs
                    else:
                        # Use try/except to handle cases with missing
                        # consumer choice data
                        try:
                            choice_params = {"rate distribution":
                                             self.handyvars.com_timeprefs[
                                                 "distributions"][mskeys[4]]}
                            # Add to count of primary microsegment key chains
                            # with valid consumer choice data
                            valid_keys_consume += 1
                        except KeyError:
                            # Record missing consumer data for primary
                            # technologies; if in verbose mode and the user
                            # has not already been warned about missing data
                            # for the given technology, print warning message
                            if mskeys[4] not in consume_warn:
                                consume_warn.append(mskeys[4])
                                verboseprint(
                                    opts.verbose,
                                    "WARNING: ECM '" + self.name +
                                    "' missing valid consumer choice data " +
                                    "for end use '" + str(mskeys[4]) +
                                    "'; using default choice data for " +
                                    "refrigeration end use")
                            choice_params = {"rate distribution":
                                             self.handyvars.com_timeprefs[
                                                 "distributions"][
                                                 "refrigeration"]}

                # Find fraction of total new buildings in each year.
                # Note: in each year, this fraction is calculated by summing
                # the annual new building/floor space figures for all
                # preceding years
                for yr in self.handyvars.aeo_years:
                    # Find cumulative total of new building/floor space stock
                    if yr == self.handyvars.aeo_years[0]:
                        new_constr["total new"][yr] = \
                            new_constr["annual new"][yr]
                    else:
                        # Handle case where data for previous year are
                        # unavailable; set to current year's data
                        try:
                            new_constr["total new"][yr] = \
                                new_constr["annual new"][yr] + \
                                new_constr["total new"][str(int(yr) - 1)]
                        except KeyError:
                            new_constr["total new"][yr] = \
                                new_constr["annual new"][yr]
                    # Calculate new vs. existing fraction of stock
                    if new_constr["total new"][yr] <= new_constr["total"][yr]:
                        new_constr["new fraction"][yr] = \
                            new_constr["total new"][yr] / \
                            new_constr["total"][yr]
                    else:
                        new_constr["new fraction"][yr] = 1

                # Determine the fraction to use in scaling down the stock,
                # energy, and carbon microsegments to the applicable structure
                # type indicated in the microsegment key chain (e.g., new
                # structures or existing structures)
                if mskeys[-1] == "new":
                    new_existing_frac = {key: val for key, val in
                                         new_constr["new fraction"].items()}
                else:
                    new_existing_frac = {key: (1 - val) for key, val in
                                         new_constr["new fraction"].items()}

                # Update bass diffusion parameters needed to determine the
                # fraction of the baseline microsegment that will be captured
                # by efficient alternatives to the baseline technology
                # (* BLANK FOR NOW, WILL CHANGE IN FUTURE *)
                diffuse_params = None
                # diffuse_params = base_cpl["consumer choice"][
                #    "competed market"]["parameters"]

                # For primary lighting microsegments with secondary effects,
                # initialize a variable used to track the total lighting
                # energy for the microsegment's climate zone, building
                # type, and structure type
                if mskeys[4] == "lighting" and self.end_use[
                        "secondary"] != [None]:
                    # Initialize total lighting energy
                    energy_total_scnd = True
                else:
                    energy_total_scnd = False

                # Update total stock, energy use, and carbon emissions for the
                # current contributing microsegment. Note that secondary
                # microsegments make no contribution to the stock calculation,
                # as they only affect energy/carbon and associated costs.

                # Total stock
                if mskeys[0] == 'secondary':
                    add_stock = dict.fromkeys(self.handyvars.aeo_years, 0)
                elif sqft_subst == 1:  # Use ft^2 floor area in lieu of # units
                    add_stock = {
                        key: val * new_existing_frac[key] * 1000000 for
                        key, val in mseg_sqft_stock[
                            "total square footage"].items()
                        if key in self.handyvars.aeo_years}
                else:
                    add_stock = {
                        key: val * new_existing_frac[key] for key, val in
                        mseg["stock"].items() if key in
                        self.handyvars.aeo_years}
                # Total energy use
                add_energy = {
                    key: val * site_source_conv_base[key] *
                    new_existing_frac[key] for key, val in mseg[
                        "energy"].items() if key in
                    self.handyvars.aeo_years}
                # Total lighting energy use for climate zone, building type,
                # and structure type of current primary lighting
                # microsegment (used to adjust secondary effects)
                if energy_total_scnd is True:
                    energy_total_scnd = self.find_scnd_overlp(
                        new_existing_frac, site_source_conv_base, reduce(
                            operator.getitem, mskeys[1:5], msegs),
                        energy_tot=dict.fromkeys(
                            self.handyvars.aeo_years, 0))
                # Total carbon emissions
                add_carb = {key: val * intensity_carb_base[key]
                            for key, val in add_energy.items()
                            if key in self.handyvars.aeo_years}

                # Check for time-sensitive efficiency valuation (e.g., a
                # measure has time sensitive features and/or the user has
                # optionally specified time sensitive output metrics or sector-
                # level load shapes for the given year). If this type of
                # valuation is necessary and the current microsegment pertains
                # to electricity, develop the factors needed to reweight
                # energy/cost/carbon data to reflect hourly changes in energy
                # load, energy price, and average carbon emissions across the
                # desired annual or sub-annual time horizon; also pull hourly
                # fraction of annual load data needed to calculate sector-level
                # shapes below if the user has specified the '--sect_shapes'
                # option and simulation is in a year where such shapes are
                # desired (per self.handyvars.aeo_years_summary attribute).
                if (self.energy_outputs["tsv_metrics"] is not False or
                    self.tsv_features is not None or (
                    opts.sect_shapes is True and
                    yr in self.handyvars.aeo_years_summary)) and (
                    mskeys[0] == "secondary" or (mskeys[0] == "primary" and ((
                        mskeys[3] == "electricity") or (
                            self.fuel_switch_to == "electricity")))):
                    tsv_scale_fracs, tsv_shapes = self.gen_tsv_facts(
                        tsv_data, mskeys, bldg_sect, convert_data, opts)
                else:
                    tsv_scale_fracs = {
                        "energy": {"baseline": 1, "efficient": 1},
                        "cost": {"baseline": 1, "efficient": 1},
                        "carbon": {"baseline": 1, "efficient": 1}}
                    tsv_shapes = None

                for adopt_scheme in self.handyvars.adopt_schemes:
                    # Update total, competed, and efficient stock, energy,
                    # carbon and baseline/measure cost info. based on adoption
                    # scheme
                    [add_stock_total, add_energy_total, add_carb_total,
                     add_stock_total_meas, add_energy_total_eff,
                     add_carb_total_eff, add_stock_compete, add_energy_compete,
                     add_carb_compete, add_stock_compete_meas,
                     add_energy_compete_eff, add_carb_compete_eff,
                     add_stock_cost, add_energy_cost, add_carb_cost,
                     add_stock_cost_meas, add_energy_cost_eff,
                     add_carb_cost_eff, add_stock_cost_compete,
                     add_energy_cost_compete, add_carb_cost_compete,
                     add_stock_cost_compete_meas, add_energy_cost_compete_eff,
                     add_carb_cost_compete_eff, add_fs_energy_eff_remain,
                     add_fs_carb_eff_remain, add_fs_energy_cost_eff_remain] = \
                        self.partition_microsegment(
                            adopt_scheme, diffuse_params, mskeys,
                            mkt_scale_frac, new_constr, add_stock,
                            add_energy, add_carb, cost_base, cost_meas,
                            cost_energy_base, cost_energy_meas, rel_perf,
                            life_base, life_meas, site_source_conv_base,
                            site_source_conv_meas, intensity_carb_base,
                            intensity_carb_meas, energy_total_scnd,
                            tsv_scale_fracs, tsv_shapes, opts,
                            contrib_mseg_key, contrib_meas_pkg)

                    # Combine stock/energy/carbon/cost/lifetime updating info.
                    # into a dict. Note that baseline lighting lifetimes are
                    # adjusted by the stock of the contributing microsegment
                    # such that a total weighted baseline lifetime may be
                    # calculated below for the measure across all contributing
                    # microsegments
                    add_dict = {
                        "stock": {
                            "total": {
                                "all": add_stock_total,
                                "measure": add_stock_total_meas},
                            "competed": {
                                "all": add_stock_compete,
                                "measure": add_stock_compete_meas}},
                        "energy": {
                            "total": {
                                "baseline": add_energy_total,
                                "efficient": add_energy_total_eff},
                            "competed": {
                                "baseline": add_energy_compete,
                                "efficient": add_energy_compete_eff}},
                        "carbon": {
                            "total": {
                                "baseline": add_carb_total,
                                "efficient": add_carb_total_eff},
                            "competed": {
                                "baseline": add_carb_compete,
                                "efficient": add_carb_compete_eff}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": add_stock_cost,
                                    "efficient": add_stock_cost_meas},
                                "competed": {
                                    "baseline": add_stock_cost_compete,
                                    "efficient": add_stock_cost_compete_meas}},
                            "energy": {
                                "total": {
                                    "baseline": add_energy_cost,
                                    "efficient": add_energy_cost_eff},
                                "competed": {
                                    "baseline": add_energy_cost_compete,
                                    "efficient": add_energy_cost_compete_eff}},
                            "carbon": {
                                "total": {
                                    "baseline": add_carb_cost,
                                    "efficient": add_carb_cost_eff},
                                "competed": {
                                    "baseline": add_carb_cost_compete,
                                    "efficient": add_carb_cost_compete_eff}}},
                        "lifetime": {
                            "baseline": {
                                yr: life_base[yr] * add_stock_total[yr] for
                                yr in self.handyvars.aeo_years},
                            "measure": life_meas}}

                    # Using the key chain for the current microsegment,
                    # determine the output climate zone, building type, and end
                    # use breakout categories to which the current microsegment
                    # applies

                    # Establish applicable climate zone breakout
                    for cz in self.handyvars.out_break_czones.items():
                        if mskeys[1] in cz[1]:
                            out_cz = cz[0]
                    # Establish applicable building type breakout
                    for bldg in self.handyvars.out_break_bldgtypes.items():
                        if all([x in bldg[1] for x in [
                                mskeys[2], mskeys[-1]]]):
                            out_bldg = bldg[0]
                    # Establish applicable end use breakout
                    for eu in self.handyvars.out_break_enduses.items():
                        # * Note: The 'other' microsegment end
                        # use may map to either the 'Refrigeration' output
                        # breakout or the 'Other' output breakout, depending on
                        # the technology type specified in the measure
                        # definition. Also note that 'supply' side
                        # heating/cooling microsegments map to the
                        # 'Heating (Equip.)'/'Cooling (Equip.)' end uses, while
                        # 'demand' side heating/cooling microsegments map to
                        # the 'Heating (Env.)'/'Cooling (Env.) end use, with
                        # the exception of 'demand' side heating/cooling
                        # microsegments that represent waste heat from lights -
                        # these are categorized as part of the 'Lighting' end
                        # use
                        if mskeys[4] == "other":
                            if mskeys[5] == "freezers":
                                out_eu = "Refrigeration"
                            else:
                                out_eu = "Other"
                        elif mskeys[4] in eu[1]:
                            if (eu[0] in ["Heating (Equip.)",
                                          "Cooling (Equip.)"] and
                                mskeys[5] == "supply") or (
                                eu[0] in ["Heating (Env.)",
                                          "Cooling (Env.)"] and
                                mskeys[5] == "demand" and
                                mskeys[0] == "primary") or (
                                eu[0] not in ["Heating (Equip.)",
                                              "Cooling (Equip.)",
                                              "Heating (Env.)",
                                              "Cooling (Env.)"]):
                                out_eu = eu[0]
                        elif "lighting gain" in mskeys:
                            out_eu = "Lighting"
                    # If applicable, establish fuel type breakout (electric vs.
                    # non-electric); note – only applicable to end uses that
                    # are at least in part fossil-fired
                    if (len(self.handyvars.out_break_fuels.keys()) != 0) and (
                        out_eu in ["Heating (Equip.)", "Cooling (Equip.)",
                                   "Heating (Env.)", "Cooling (Env.)",
                                   "Water Heating", "Cooking"]):
                        # Establish breakout of fuel type that is being
                        # reduced (e.g., through efficiency or fuel switching
                        # away from the fuel)
                        for f in self.handyvars.out_break_fuels.items():
                            if mskeys[3] in f[1]:
                                out_fuel_save = f[0]
                        # Establish breakout of fuel type that is being added
                        # to via fuel switching, if applicable
                        if self.fuel_switch_to == "electricity" and \
                                out_fuel_save != "Electric":
                            out_fuel_gain = "Electric"
                        elif self.fuel_switch_to not in [None, "electricity"] \
                                and out_fuel_save == "Electric":
                            out_fuel_gain = "Non-Electric"
                        else:
                            out_fuel_gain = ""
                    else:
                        out_fuel_save, out_fuel_gain = ("" for n in range(2))

                    # Given the contributing microsegment's applicable climate
                    # zone, building type, and end use categories, add the
                    # microsegment's energy/ecost/carbon baseline, efficient
                    # energy/ecost/carbon, and energy/ecost/carbon savings val.
                    # to the appropriate leaf node of the dictionary used to
                    # store measure output breakout information. * Note: the
                    # values in this dictionary will be normalized in run.py by
                    # the measure's energy/ecost/carbon baseline, efficient
                    # energy/ecost/carbon, and energy/ecost/carbon savings
                    # totals (post-competition) to yield the fractions of
                    # measure energy, carbon, and cost markets/savings that are
                    # attributable to each climate zone, building type, and
                    # end use that the measure applies to
                    try:
                        # Create a shorthand for baseline and efficient
                        # energy/carbon/cost data to add to the breakout dict
                        base_data = [add_energy_total, add_energy_cost,
                                     add_carb_total]
                        eff_data = [add_energy_total_eff, add_energy_cost_eff,
                                    add_carb_total_eff]
                        # For a fuel switching case, create shorthands for
                        # any efficient energy/carbon/cost that remains with
                        # the baseline fuel
                        if self.fuel_switch_to is not None:
                            eff_data_fs = [add_fs_energy_eff_remain,
                                           add_fs_energy_cost_eff_remain,
                                           add_fs_carb_eff_remain]
                        # Handle case where output breakout includes fuel type
                        # breakout or not
                        if out_fuel_save:
                            # Update results for the baseline fuel; handle
                            # case where results for the current region, bldg.,
                            # end use, and fuel have not yet been initialized
                            try:
                                for yr in self.handyvars.aeo_years:
                                    for ind, key in enumerate([
                                            "energy", "cost", "carbon"]):
                                        # Baseline; add in baseline data
                                        # as-is
                                        self.markets[adopt_scheme][
                                            "mseg_out_break"][key][
                                            "baseline"][out_cz][out_bldg][
                                            out_eu][out_fuel_save][yr] += \
                                            base_data[ind][yr]
                                        # Efficient and savings; if there is
                                        # fuel switching, only the portion
                                        # of the efficient case results that
                                        # have not yet switched (due to stock
                                        # turnover limitations) remain, and
                                        # savings are the delta between what
                                        # remains unswitched in the efficient
                                        # case and the baseline
                                        if not out_fuel_gain:
                                            self.markets[adopt_scheme][
                                                "mseg_out_break"][key][
                                                "efficient"][out_cz][out_bldg][
                                                out_eu][out_fuel_save][yr] += \
                                                eff_data[ind][yr]
                                            self.markets[adopt_scheme][
                                                "mseg_out_break"][key][
                                                "savings"][out_cz][out_bldg][
                                                out_eu][out_fuel_save][yr] += (
                                                    base_data[ind][yr] -
                                                    eff_data[ind][yr])
                                        else:
                                            self.markets[adopt_scheme][
                                                "mseg_out_break"][key][
                                                "efficient"][out_cz][out_bldg][
                                                out_eu][out_fuel_save][yr] += \
                                                eff_data_fs[ind][yr]
                                            self.markets[adopt_scheme][
                                                "mseg_out_break"][key][
                                                "savings"][out_cz][out_bldg][
                                                out_eu][out_fuel_save][yr] += (
                                                    base_data[ind][yr] -
                                                    eff_data_fs[ind][yr])
                            except KeyError:
                                for ind, key in enumerate([
                                        "energy", "cost", "carbon"]):
                                    # Baseline; add in baseline data
                                    # as-is
                                    self.markets[adopt_scheme][
                                        "mseg_out_break"][key][
                                        "baseline"][out_cz][out_bldg][
                                        out_eu][out_fuel_save] = {
                                            yr: base_data[ind][yr] for
                                            yr in self.handyvars.aeo_years}
                                    # Efficient and savings; if there is fuel
                                    # switching, only the portion of the
                                    # efficient case results that have not yet
                                    # switched (due to stock turnover
                                    # limitations) remain, and savings are the
                                    # delta between what remains unswitched in
                                    # the efficient case and the baseline
                                    if not out_fuel_gain:
                                        self.markets[adopt_scheme][
                                            "mseg_out_break"][key][
                                            "efficient"][out_cz][out_bldg][
                                            out_eu][out_fuel_save] = {
                                                yr: eff_data[ind][yr] for
                                                yr in self.handyvars.aeo_years}
                                        self.markets[adopt_scheme][
                                            "mseg_out_break"][key][
                                            "savings"][out_cz][out_bldg][
                                                out_eu][out_fuel_save] = {
                                                yr: (base_data[ind][yr] -
                                                     eff_data[ind][yr]) for
                                                yr in self.handyvars.aeo_years}
                                    else:
                                        self.markets[adopt_scheme][
                                            "mseg_out_break"][key][
                                            "efficient"][out_cz][out_bldg][
                                            out_eu][out_fuel_save] = {
                                                yr: eff_data_fs[ind][yr] for
                                                yr in self.handyvars.aeo_years}
                                        self.markets[adopt_scheme][
                                            "mseg_out_break"][key][
                                            "savings"][out_cz][out_bldg][
                                                out_eu][out_fuel_save] = {
                                                yr: (base_data[ind][yr] -
                                                     eff_data_fs[ind][yr]) for
                                                yr in self.handyvars.aeo_years}
                            # In a fuel switching case, update results for
                            # the fuel being switched/added to
                            if out_fuel_gain:
                                # Handle case where results for the current
                                # region, bldg., end use, and fuel have not yet
                                # been initialized
                                try:
                                    for yr in self.handyvars.aeo_years:
                                        for ind, key in enumerate([
                                                "energy", "cost", "carbon"]):
                                            # Note: no need to add to baseline
                                            # for fuel being switched to,
                                            # which remains zero

                                            # Efficient and savings; efficient
                                            # case energy/emissions/cost that
                                            # do not remain with the baseline
                                            # fuel are added to the switched to
                                            # fuel and represented as negative
                                            # savings for the switched to fuel
                                            self.markets[adopt_scheme][
                                                "mseg_out_break"][key][
                                                "efficient"][out_cz][out_bldg][
                                                out_eu][out_fuel_gain][yr] += \
                                                (eff_data[ind][yr] -
                                                 eff_data_fs[ind][yr])
                                            self.markets[adopt_scheme][
                                                "mseg_out_break"][key][
                                                "savings"][out_cz][out_bldg][
                                                out_eu][out_fuel_gain][yr] -= (
                                                    eff_data[ind][yr] -
                                                    eff_data_fs[ind][yr])
                                except KeyError:
                                    for ind, key in enumerate([
                                            "energy", "cost", "carbon"]):
                                        # Baseline for the fuel being switched
                                        # to is initialized as zero
                                        self.markets[adopt_scheme][
                                            "mseg_out_break"][key][
                                            "baseline"][out_cz][out_bldg][
                                            out_eu][out_fuel_gain] = {
                                                yr: 0 for yr in
                                                self.handyvars.aeo_years}
                                        # Efficient and savings; efficient
                                        # case energy/emissions/cost that
                                        # do not remain with the baseline
                                        # fuel are added to the switched to
                                        # fuel and represented as negative
                                        # savings for the switched to fuel
                                        self.markets[adopt_scheme][
                                            "mseg_out_break"][key][
                                            "efficient"][out_cz][out_bldg][
                                            out_eu][out_fuel_gain] = {
                                                yr: (eff_data[ind][yr] -
                                                     eff_data_fs[ind][yr]) for
                                                yr in self.handyvars.aeo_years}
                                        self.markets[adopt_scheme][
                                            "mseg_out_break"][key][
                                            "savings"][out_cz][out_bldg][
                                                out_eu][out_fuel_gain] = {
                                                yr: -(eff_data[ind][yr] -
                                                      eff_data_fs[ind][yr]) for
                                                yr in self.handyvars.aeo_years}
                        else:
                            # Handle case where results for the current region,
                            # bldg., end use, and fuel have not yet been
                            # initialized
                            try:
                                for yr in self.handyvars.aeo_years:
                                    for ind, key in enumerate([
                                            "energy", "cost", "carbon"]):
                                        self.markets[adopt_scheme][
                                            "mseg_out_break"][key][
                                            "baseline"][out_cz][out_bldg][
                                            out_eu][yr] += base_data[ind][yr]
                                        self.markets[adopt_scheme][
                                            "mseg_out_break"][key][
                                            "efficient"][out_cz][out_bldg][
                                            out_eu][yr] += eff_data[ind][yr]
                                        self.markets[adopt_scheme][
                                            "mseg_out_break"][key][
                                            "savings"][out_cz][out_bldg][
                                            out_eu][yr] += (
                                                base_data[ind][yr] -
                                                eff_data[ind][yr])
                            except KeyError:
                                for ind, key in enumerate([
                                        "energy", "cost", "carbon"]):
                                    self.markets[adopt_scheme][
                                        "mseg_out_break"][key]["baseline"][
                                        out_cz][out_bldg][out_eu] = {
                                            yr: base_data[ind][yr] for
                                            yr in self.handyvars.aeo_years}
                                    self.markets[adopt_scheme][
                                        "mseg_out_break"][key]["efficient"][
                                        out_cz][out_bldg][out_eu] = {
                                            yr: eff_data[ind][yr] for
                                            yr in self.handyvars.aeo_years}
                                    self.markets[adopt_scheme][
                                        "mseg_out_break"][key]["savings"][
                                        out_cz][out_bldg][out_eu] = {
                                            yr: (base_data[ind][yr] -
                                                 eff_data[ind][yr]) for
                                            yr in self.handyvars.aeo_years}

                    # Yield error if current contributing microsegment cannot
                    # be mapped to an output breakout category
                    except KeyError:
                        print("Baseline market key chain: '" + str(mskeys) +
                              "' for ECM '" + self.name + "' does not map to "
                              "output breakout categories")

                    # Record contributing microsegment data needed for ECM
                    # competition in the analysis engine

                    # Case with no existing 'windows' contributing microsegment
                    # for the current climate zone, building type, fuel type,
                    # and end use (create new 'contributing mseg keys and
                    # values' and 'competed choice parameters' microsegment
                    # information)
                    if str(contrib_mseg_key) not in self.markets[adopt_scheme][
                        "mseg_adjust"][
                            "contributing mseg keys and values"].keys():
                        # Register contributing microsegment information for
                        # later use in determining savings overlaps for
                        # measures that apply to this microsegment
                        self.markets[adopt_scheme]["mseg_adjust"][
                            "contributing mseg keys and values"][
                            str(contrib_mseg_key)] = add_dict
                        # Register choice parameters associated with
                        # contributing microsegment for later use in
                        # apportioning out various technology options across
                        # competed stock
                        self.markets[adopt_scheme]["mseg_adjust"][
                            "competed choice parameters"][
                            str(contrib_mseg_key)] = choice_params
                    # Case with existing 'windows' contributing microsegment
                    # for the current climate zone, building type, fuel type,
                    # and end use (add to existing 'contributing mseg keys and
                    # values' information)
                    else:
                        self.markets[adopt_scheme]["mseg_adjust"][
                            "contributing mseg keys and values"][
                            str(contrib_mseg_key)] = self.add_keyvals(
                                self.markets[adopt_scheme]["mseg_adjust"][
                                    "contributing mseg keys and values"][
                                    str(contrib_mseg_key)], add_dict)
                    # Record the sub-market scaling fraction associated with
                    # the current contributing microsegment
                    self.markets[adopt_scheme]["mseg_adjust"][
                        "contributing mseg keys and values"][
                        str(contrib_mseg_key)]["sub-market scaling"] = \
                        mkt_scale_frac

                    # Add all updated contributing microsegment stock, energy
                    # carbon, cost, and lifetime information to existing master
                    # mseg dict and move to next iteration of the loop through
                    # key chains
                    self.markets[adopt_scheme]["master_mseg"] = \
                        self.add_keyvals(self.markets[adopt_scheme][
                            "master_mseg"], add_dict)

        # Further normalize a measure's lifetime and stock information (where
        # the latter is based on square footage) to the number of microsegments
        # that contribute to the measure's overall master microsegment and
        # have valid stock/energy and cost/performance/lifetime data
        if valid_keys_stk_energy != 0 and valid_keys_cpl != 0:

            for adopt_scheme in self.handyvars.adopt_schemes:
                # Calculate overall average baseline and measure lifetimes
                for yr in self.handyvars.aeo_years:
                    # Divide summed baseline lifetimes * stock values for
                    # contributing microsegments by total stock across all
                    # contributing microsegments
                    if self.markets[adopt_scheme][
                            "master_mseg"]["stock"]["total"]["all"][yr] != 0:
                        self.markets[adopt_scheme]["master_mseg"]["lifetime"][
                            "baseline"][yr] = self.markets[adopt_scheme][
                            "master_mseg"]["lifetime"]["baseline"][yr] / \
                            self.markets[adopt_scheme][
                            "master_mseg"]["stock"]["total"]["all"][yr]
                # Divide summed measure lifetimes by total number of
                # contributing microsegment key chains with valid
                # cost/performance/lifetime data
                self.markets[adopt_scheme][
                    "master_mseg"]["lifetime"]["measure"] = \
                    self.markets[adopt_scheme]["master_mseg"][
                    "lifetime"]["measure"] / valid_keys_cpl

                # Remove stock multipliers from lifetime values in
                # contributing microsegment (values used in competition later)
                contrib_msegs = self.markets[adopt_scheme]["mseg_adjust"][
                    "contributing mseg keys and values"]
                for key in contrib_msegs.keys():
                    contrib_msegs[key]["lifetime"]["baseline"] = {yr: (
                        contrib_msegs[key]["lifetime"]["baseline"][yr] /
                        contrib_msegs[key]["stock"]["total"]["all"][yr]) if
                        contrib_msegs[key]["stock"]["total"]["all"][yr] != 0
                        else 10 for yr in self.handyvars.aeo_years}

                # In microsegments where square footage must be used as stock,
                # the square footages cannot be summed to calculate the master
                # microsegment stock values (as is the case when using no. of
                # units).  For example, 1000 Btu of cooling and heating in the
                # same 1000 square foot building should not yield 2000 total
                # square feet of stock in the master microsegment even though
                # there are two contributing microsegments in this case
                # (heating and cooling). This is remedied by dividing summed
                # square footage values by (# valid key chains / (# czones * #
                # bldg types * # structure types)), where the numerator refers
                # to the number of full dict key chains that contributed to the
                # mseg stock, energy, and cost calcs, and the denominator
                # reflects the breakdown of square footage by climate zone,
                # building type, and the structure type that the measure
                # applies to.
                if sqft_subst == 1:
                    # Determine number of structure types the measure applies
                    # to (could be just new, just existing, or both)
                    if isinstance(self.structure_type, list) and len(
                            self.structure_type) > 1:
                        structure_types = 2
                    else:
                        structure_types = 1
                    # Create a factor for reduction of msegs with ft^2 floor
                    # area stock
                    reduce_num = valid_keys_cpl / (
                        len(ms_lists[0]) * len(ms_lists[1]) * structure_types)
                    # Adjust master microsegment by above factor
                    self.markets[adopt_scheme]["master_mseg"] = \
                        self.div_keyvals_float_restrict(self.markets[
                            adopt_scheme]["master_mseg"], reduce_num)
                    # Adjust all recorded microsegments that contributed to the
                    # master microsegment by above factor
                    contrib_msegs = self.div_keyvals_float_restrict(
                        contrib_msegs, reduce_num)
                else:
                    reduce_num = 1

        # Generate an error message when no contributing microsegments
        # with a full set of stock/energy and cost/performance/lifetime data
        # have been found for the measure's master microsegment
        elif self.remove is False:
            raise KeyError(
                "No data retrieved for applicable baseline market "
                "definition of ECM '" + self.name + "'")

        # Print update on measure status

        # If not in verbose mode, suppress summaries about missing data;
        # otherwise, summarize the extent of the missing data
        if opts is not None and opts.verbose is True:
            # Summarize percentage of baseline stock and energy
            # data that were missing (if any)
            if valid_keys_stk_energy == valid_keys:
                bstk_msg = ""
            else:
                bstk_msg = "\n" + " - " + str(
                    round((1 - (valid_keys_stk_energy / valid_keys)) *
                          100)) + \
                    " % of baseline technologies were missing valid" + \
                    " baseline stock or energy data and" + \
                    " removed from analysis"
            # Summarize percentage of baseline cost, performance, and lifetime
            # data that were missing (if any)
            if valid_keys_cpl == valid_keys_stk_energy:
                bcpl_msg = ""
            else:
                bcpl_msg = "\n" + " - " + str(
                    round((1 - (valid_keys_cpl / valid_keys_stk_energy)) *
                          100)) + \
                    " % of baseline technologies were missing valid" + \
                    " baseline cost, performance, or lifetime data and" + \
                    " removed from analysis"
            # Summarize percentage of baseline consumer choice data that
            # were missing (if any)
            if valid_keys_consume == valid_keys_stk_energy:
                bcc_msg = ""
            else:
                bcc_msg = "\n" + " - " + str(
                    round((1 - (valid_keys_consume / valid_keys_stk_energy)) *
                          100)) + \
                    " % of baseline technologies were missing" + \
                    " valid consumer choice data"
            cc_msg = ""
        else:
            # Missing baseline stock and energy data, cost, performance, and
            # lifetime data and consumer data summaries are blank
            bstk_msg, bcpl_msg, bcc_msg = ("" for n in range(3))
            # If one or more conversion to ECM unit cost has been made, note
            # this in the update message
            if cost_converts == 0:
                cc_msg = ""
            else:
                cc_msg = " (cost units converted)"

        # Print message to console; if in verbose mode, print to new line,
        # otherwise append to existing message on the console
        if opts is not None and opts.verbose is True:
            print("ECM '" + self.name + "' successfully updated" +
                  bstk_msg + bcpl_msg + bcc_msg + cc_msg)
        else:
            print("Success" + bstk_msg + bcpl_msg + bcc_msg + cc_msg)

    def gen_tsv_facts(self, tsv_data, mskeys, bldg_sect, cost_conv, opts):
        """Set annual re-weighting factors and hourly load fractions for TSV.

        Args:
            tsv_data (data): Time-resolved load/energy cost/emissions data.
            mskeys (tuple): Microsegment information needed to key load shapes.
            bldg_sect (string): Building sector of the current microsegment.
            cost_conv (dict): Conversion factors, EPlus->Scout building types.
            opts (object): Stores user-specified execution options.

        Returns:
            Dict of microsegment-specific energy, cost, and emissions annual
            re-weighting factors that reflect time-sensitive evaluation of
            energy efficiency and associated energy costs/carbon emissions, and
            (if desired by user) hourly fractions of annual energy load.
        """

        # If time-sensitive valuation is needed and energy, cost, and carbon
        # re-weighting and load shape information does not already exist for
        # the current combination of region, building type, and end use, set
        # energy load shapes for given climate, building type, and end use
        if self.handyvars.tsv_hourly_lafs is not None and \
            self.handyvars.tsv_hourly_lafs[mskeys[1]][bldg_sect][
                mskeys[2]][mskeys[4]] is None:
            # Primary microsegment case: find the load shape associated with
            # the primary end use
            if mskeys[0] == "primary":
                # First, assume there is a load shape for the current end use
                try:
                    # Do not assign the "other" load shape directly to the
                    # "other" end use in Scout, as this end use has
                    # sub-categories (e.g., dishwashing, pool pumps/heaters,
                    # etc.) that should be used to key in the appropriate load
                    # shape information
                    if mskeys[4] == "other":
                        raise(KeyError)
                    else:
                        # Set load data end use key for use in 'apply_tsv'
                        eu = mskeys[4]
                        # Key in the appropriate load shape data
                        load_fact = tsv_data["load"][bldg_sect][eu]
                except KeyError:
                    # If there is no load shape for the current end use, handle
                    # the resultant error differently for res./com.
                    if bldg_sect == "residential":
                        # Secondary heating maps to heating load shape
                        if mskeys[4] == "secondary heating":
                            eu = "heating"
                        # Computers and TVs map to plug loads load shape
                        elif mskeys[4] in ["computers", "TVs"]:
                            eu = "plug loads"
                        # Ceiling fan maps to cooling load shape
                        elif mskeys[4] == "ceiling fan":
                            eu = "cooling"
                        # Other end use maps to various load shapes
                        elif mskeys[4] == "other":
                            # Dishwasher technology maps to dishwasher
                            if mskeys[5] == "dishwasher":
                                eu = "dishwasher"
                            # Clothes washing tech. maps to clothes washing
                            elif mskeys[5] == "clothes washing":
                                eu = "clothes washing"
                            # Clothes drying technology maps to clothes drying
                            elif mskeys[5] == "clothes drying":
                                eu = "clothes drying"
                            # Pool heaters/pumps map to pool heaters/pumps
                            elif mskeys[5] == "pool heaters and pumps":
                                eu = "pool heaters and pumps"
                            # Freezers map to refrigeration
                            elif mskeys[5] == "freezers":
                                eu = "refrigeration"
                            # All other other maps to other
                            else:
                                eu = "other"
                        # In all other cases, error
                        else:
                            raise KeyError(
                                "The following baseline segment could not be "
                                "mapped to any baseline load shape in the "
                                "Scout database: " + str(mskeys))
                    elif bldg_sect == "commercial":
                        # For commercial PCs/non-PC office equipment, use the
                        # load shape for plug loads
                        if mskeys[4] in ["PCs", "non-PC office equipment"]:
                            eu = "plug loads"
                        # For commercial MELs end uses, use the generic 'other'
                        # load shape
                        elif mskeys[4] == "MELs":
                            eu = "other"
                        # In all other cases, error
                        else:
                            raise KeyError(
                                "The following baseline segment could not be "
                                "mapped to any baseline load shape in the "
                                "Scout database: " + str(mskeys))
                    # Key in the appropriate load shape data
                    load_fact = tsv_data["load"][bldg_sect][eu]

            # Commercial secondary lighting microsegment case: use the lighting
            # load shape for secondary heating/cooling impacts from lighting
            else:
                eu = "lighting"
                # Key in the appropriate load shape data
                load_fact = tsv_data["load"][bldg_sect][eu]

            # Find weights needed to map ASHRAE/IECC climate zones to EMM
            # region, and EnergyPlus building type to Scout building type

            # Find ASHRAE/IECC -> EMM weighting factors for current EMM region
            ash_czone_wts = [[x["ASHRAE"], x[mskeys[1]]] for x in
                             self.handyvars.ash_emm_map if (
                                numpy.isfinite(x[mskeys[1]]) and
                                x[mskeys[1]] != 0)]
            # Check to ensure that region weighting factors sum to 1
            if round(sum([x[1] for x in ash_czone_wts]), 2) != 1:
                raise ValueError(
                    "ASHRAE climate -> EMM region weights for region " +
                    mskeys[1] + " and building type " + mskeys[2] +
                    " do not sum to 1")

            # Find EnergyPlus -> Scout building type weighting factors for
            # current building type. Note that residential buildings map
            # directly to the ResStock single family building type
            if bldg_sect == "commercial":
                eplus_bldg_wts = cost_conv["building type conversions"][
                    "conversion data"]["value"]["commercial"][mskeys[2]]
                # Handle case where there is no EnergyPlus analogue for a Scout
                # commercial building type (e.g., for the other Scout building
                # type and the health care Scout building type)
                if eplus_bldg_wts is None:
                    if mskeys[2] == "other":
                        eplus_bldg_wts = {"MediumOfficeDetailed": 1}
                    elif mskeys[2] == "health care":
                        eplus_bldg_wts = {"Hospital": 1}
            else:
                eplus_bldg_wts = {"ResStockSingleFamily": 1}
            # Check to ensure that building type weighting factors sum to 1
            if round(sum([x[1] for x in eplus_bldg_wts.items()]), 2) != 1:
                raise ValueError(
                    "EPlus building -> Scout building mapping weights for "
                    "region " + mskeys[1] + " and building type " + mskeys[2] +
                    " do not sum to 1")

            # Generate appropriate 8760 price and emissions scaling shapes if
            # either measure TSV features are present or the user desires
            # TSV metrics outputs; assume these shapes are not necessary if
            # the user only desires sector-level load shapes
            if ((opts and opts.sect_shapes is True) and
                self.energy_outputs["tsv_metrics"] is False and
                    self.tsv_features is None):
                cost_fact_hourly, carbon_fact_hourly, cost_yr_map, \
                    carb_yr_map = (None for n in range(4))
            else:
                # Set time-varying electricity price scaling factors for the
                # EMM region (dict with keys distinguished by year, *CURRENTLY*
                # every two years beginning in 2018)
                if self.handyvars.tsv_hourly_price[mskeys[1]] is None:
                    cost_fact_hourly,  self.handyvars.tsv_hourly_price[
                        mskeys[1]] = ({yr: tsv_data["price"][
                            "electricity price shapes"][yr][
                            mskeys[1]] for yr in tsv_data["price"][
                            "electricity price shapes"].keys()} for
                            n in range(2))
                else:
                    cost_fact_hourly = \
                        self.handyvars.tsv_hourly_price[mskeys[1]]
                # Set TSV data -> AEO year mapping to use in preparing cost
                # scaling factors
                cost_yr_map = tsv_data["price_yr_map"]
                # Set time-varying emissions scaling factors for the EMM
                # region (dict with keys distinguished by year, *CURRENTLY*
                # every two years beginning in 2018)
                if self.handyvars.tsv_hourly_emissions[mskeys[1]] is None:
                    carbon_fact_hourly,  self.handyvars.tsv_hourly_emissions[
                        mskeys[1]] = ({yr: tsv_data["emissions"][
                            "average carbon emissions rates"][yr][
                            mskeys[1]] for yr in tsv_data["emissions"][
                            "average carbon emissions rates"].keys()} for
                            n in range(2))
                else:
                    carbon_fact_hourly = self.handyvars.tsv_hourly_emissions[
                        mskeys[1]]
                # Set TSV data -> AEO year mapping to use in preparing
                # emissions scaling factors
                carb_yr_map = tsv_data["emissions_yr_map"]

            # Use 8760 load shape information, combined with 8760 price and
            # emissions shape information above, to calculate factors that
            # modify annually-determined baseline and efficient energy, cost,
            # and carbon totals such that they reflect sub-annual assessment
            # of these totals
            updated_tsv_fracs, updated_tsv_shapes = self.apply_tsv(
                load_fact, ash_czone_wts, eplus_bldg_wts, cost_fact_hourly,
                carbon_fact_hourly, mskeys, bldg_sect, eu, opts, cost_yr_map,
                carb_yr_map)
            # Set adjustment factors for current combination of
            # region, building type, and end use such that they
            # need not be calculated again for this combination in
            # subsequent technology microsegments
            self.handyvars.tsv_hourly_lafs[mskeys[1]][bldg_sect][
                mskeys[2]][mskeys[4]] = {
                    "annual adjustment fractions": updated_tsv_fracs,
                    "hourly shapes": updated_tsv_shapes}
        elif self.handyvars.tsv_hourly_lafs is not None:
            updated_tsv_fracs, updated_tsv_shapes = [
                self.handyvars.tsv_hourly_lafs[mskeys[1]][bldg_sect][
                    mskeys[2]][mskeys[4]]["annual adjustment fractions"],
                self.handyvars.tsv_hourly_lafs[mskeys[1]][bldg_sect][
                    mskeys[2]][mskeys[4]]["hourly shapes"]]
        else:
            updated_tsv_fracs = {
                "energy": {"baseline": 1, "efficient": 1},
                "cost": {"baseline": 1, "efficient": 1},
                "carbon": {"baseline": 1, "efficient": 1}}
            updated_tsv_shapes = None

        return updated_tsv_fracs, updated_tsv_shapes

    def apply_tsv(self, load_fact, ash_cz_wts, eplus_bldg_wts,
                  cost_fact_hourly, carbon_fact_hourly, mskeys, bldg_sect,
                  eu, opts, cost_yr_map, carb_yr_map):
        """Apply time varying efficiency levels to base load profile.

        Args:
            load_fact (dict): Hourly energy load fractions of annual load.
            ash_cz_wts (list): Factors to map ASH climates -> EMM regions.
            eplus_bldg_wts (dict): Factors to map EPlus -> Scout bldg. types.
            cost_fact_hourly (list): 8760 electricity price scaling factors.
            carbon_fact_hourly (list): 8760 emissions scaling factors.
            mskeys (tuple): Microsegment information.
            bldg_sect (str): Building sector flag (residential/commercial).
            eu (str): End use for keying time sensitive load data.
            opts (object): Stores user-specified execution options.
            cost_yr_map (dict): Mapping 8760 TSV price data years -> AEO years.
            carb_yr_map (dict): Mapping 8760 TSV carbon data yrs. -> AEO years.

        Returns:
            Dict of microsegment-specific energy, cost, and emissions re-
            weighting factors that reflect time-sensitive evaluation of energy
            efficiency and associated energy costs/carbon emissions; list
            with hourly fractions of annual baseline and efficient energy use
            (if desired by the user)
        """

        # Initialize overall factors to use in scaling annually-determined
        # baseline and efficient energy, cost and emissions data

        # Note: energy scaling data is not broken out by projection year
        energy_scale_base, energy_scale_eff = (0 for n in range(2))

        # Initialize hourly fractions of annual baseline and efficient energy
        # if sector-level load shape information is desired by the user
        if opts.sect_shapes is True:
            energy_base_shape, energy_eff_shape = ([
                0 for x in range(8760)] for n in range(2))
        # Create shorthand for measure's time sensitive metrics settings
        tsv_metrics = self.energy_outputs["tsv_metrics"]

        # Initialize carbon/cost scaling factor variables, but only if
        # either measure TSV features are present or the user desires
        # TSV metrics outputs; assume these shapes are not necessary if
        # the user only desires sector-level load shapes
        if tsv_metrics is not False or self.tsv_features is not None:
            # Initial format of cost/carbon scaling factor data (broken out by
            # years available in the 8760 TSV cost/carbon input data)
            cost_scale_base, cost_scale_eff = (
                {yr: 0 for yr in cost_yr_map.keys()} for n in range(2))
            carb_scale_base, carb_scale_eff = (
                {yr: 0 for yr in carb_yr_map.keys()} for n in range(2))
            # Final format of cost/carbon scaling factor data (broken out by
            # AEO years)
            cost_scale_base_aeo, cost_scale_eff_aeo, carb_scale_base_aeo, \
                carb_scale_eff_aeo = (
                    {yr: 0 for yr in self.handyvars.aeo_years} for
                    n in range(4))

        # Set the user-specified time-sensitive valuation features
        # for the current ECM; handle cases where this parameter is
        # broken out by EMM region, building type, and/or end use.
        # If no time sensitive valuation features are given, reflect
        # this with an empty dict

        if self.tsv_features is not None:
            if (type(self.tsv_features) is dict and all([
                x not in self.handyvars.tsv_feature_types for x in
                    self.tsv_features.keys()])):

                # By EMM region, building type, and end use
                try:
                    tsv_adjustments = self.tsv_features[mskeys[1]][mskeys[2]][
                        mskeys[4]]
                # By EMM region and building type
                except KeyError:
                    try:
                        tsv_adjustments = self.tsv_features[mskeys[1]][
                            mskeys[2]]
                    # By EMM region and end use
                    except KeyError:
                        try:
                            tsv_adjustments = self.tsv_features[mskeys[1]][
                                mskeys[4]]
                        # By building type and end use
                        except KeyError:
                            try:
                                tsv_adjustments = self.tsv_features[mskeys[2]][
                                    mskeys[4]]
                            # By EMM region
                            except KeyError:
                                try:
                                    tsv_adjustments = self.tsv_features[
                                        mskeys[1]]
                                # By building type
                                except KeyError:
                                    try:
                                        tsv_adjustments = self.tsv_features[
                                            mskeys[2]]
                                    # By end use
                                    except KeyError:
                                        try:
                                            tsv_adjustments = \
                                                self.tsv_features[
                                                    mskeys[4]]
                                        # Not broken out by any of these
                                        except KeyError:
                                            raise KeyError(
                                                "Unexpected breakout of "
                                                "tsv_features parameter for"
                                                "measure " + self.name +
                                                ". If this parameter is "
                                                "broken out by region, "
                                                "building type, or "
                                                "end use, ensure that ALL "
                                                "categories of these "
                                                "variables are correctly "
                                                "represented in the breakout.")
            else:
                tsv_adjustments = self.tsv_features
        else:
            tsv_adjustments = {}

        # Loop through all EPlus building types (which commercial load profiles
        # are broken out by) that map to the current Scout building type
        for bldg in eplus_bldg_wts.keys():
            # Find the appropriate key in the load shape information for the
            # current EnergyPlus building type; in the residential sector,
            # there is currently no building type breakout, set key to None
            if bldg_sect == "commercial":
                load_fact_bldg_key = [
                    x for x in load_fact.keys() if (bldg in load_fact[x][
                        "represented building types"] or load_fact[x][
                        "represented building types"] == "all")][0]
            else:
                load_fact_bldg_key = "SFD Home"

            # Ensure that all applicable ASHRAE climate zones are represented
            # in the keys for time sensitive metrics data; if a zone is not
            # represented, remove it from the weighting and renormalize weights
            ash_cz_wts = [
                [x[0], x[1]] for x in ash_cz_wts if x[0] in
                self.handyvars.tsv_climate_regions]
            # Ensure that ASHRAE climate zone weightings sum to 1
            ash_cz_renorm = sum([x[1] for x in ash_cz_wts])
            if round(ash_cz_renorm, 2) != 1:
                ash_cz_wts = [[x[0], (x[1] / ash_cz_renorm)] for
                              x in ash_cz_wts]
            # Loop through all ASHRAE/IECC climate zones (which load profiles
            # are broken out by) that map to the current EMM region
            for cz in ash_cz_wts:
                # Set the climate zone key to use in keying in savings
                # shape information
                load_fact_climate_key = cz[0]
                # Flag for cases where multiple sets of system load shape
                # information are germane to the current climate zone
                if type(self.handyvars.cz_emm_map[cz[0]]) == int:
                    mult_sysshp = False
                    mult_sysshp_key_metrics, mult_sysshp_key_save = (
                        "set 1" for n in range(2))
                elif type(self.handyvars.cz_emm_map[cz[0]]) == dict:
                    mult_sysshp = True
                    # Given multiple possible system load shape data
                    # sets, find the key for the set that is representative
                    # of the current EMM region; initialize separate keys to
                    # use in retrieving TSV metrics data vs. savings shape
                    # data (the approaches to keying in these different types
                    # of data differ below)
                    mult_sysshp_key_metrics, mult_sysshp_key_save = ([
                        y[0] for y in self.handyvars.cz_emm_map[cz[0]].items()
                        if self.handyvars.emm_name_num_map[mskeys[1]]
                        in y[1][1]][0] for n in range(2))
                else:
                    raise ValueError(
                        "Unable to determine representative utility system "
                        "load data for climate " + cz[0])

                # Set the weighting factor to map the current EPlus building
                # and ASHRAE/IECC climate to Scout building and EMM region,
                # and set the appropriate baseline load shape (8760 hourly
                # fractions of annual load)
                if bldg_sect == "commercial":
                    # Set the weighting factor
                    emm_adj_wt = eplus_bldg_wts[bldg] * cz[1]
                    # Set the baseline load shape

                    # Handle case where the load shape is not broken out by
                    # climate zone
                    try:
                        base_load_hourly = load_fact[
                            load_fact_bldg_key]["load shape"][cz[0]]
                    except (KeyError, TypeError):
                        base_load_hourly = load_fact[
                            load_fact_bldg_key]["load shape"]
                else:
                    # Set the weighting factor
                    emm_adj_wt = cz[1]
                    # Set the baseline load shape (8760 hourly fractions of
                    # annual load)

                    # Handle case where the load shape is not broken out by
                    # climate zone
                    try:
                        base_load_hourly = load_fact[cz[0]]
                    except (KeyError, TypeError):
                        base_load_hourly = load_fact

                # Initialize efficient load shape as equal to base load
                eff_load_hourly = copy.deepcopy(base_load_hourly)

                # Loop through all time-varying efficiency features in sorted
                # order, applying each successively to the base load shape
                for a in [x for x in sorted(tsv_adjustments.keys())]:

                    # Set the applicable days on which time-varying efficiency
                    # impact applies; if no start and stop information is
                    # specified by the user, assume the impact applies all year
                    try:
                        # Set the starting and stopping days for the impact
                        start_stop_dy = [
                            tsv_adjustments[a][x] for x in [
                                "start_day", "stop_day"]]
                        # Generate a list of all days in which the
                        # time-varying efficiency impact applies
                        try:
                            applicable_days = list(
                                range(start_stop_dy[0] - 1, start_stop_dy[1]))
                        # Error sets applicable day range to the full year
                        except TypeError:
                            # Assume two day ranges are specified
                            try:
                                # Start/stop set 1
                                start_1 = start_stop_dy[0][0]
                                stop_1 = start_stop_dy[1][0]
                                # Start/stop set 2
                                start_2 = start_stop_dy[0][1]
                                stop_2 = start_stop_dy[1][1]
                                # Patch together two day ranges
                                applicable_days = list(
                                    range(start_1 - 1, stop_1)) + list(
                                    range(start_2 - 1, stop_2))
                            except TypeError:
                                applicable_days = range(365)
                    except (TypeError, KeyError):
                        applicable_days = range(365)

                    # Set the applicable hours in which to apply the
                    # time-varying efficiency impact; if no start and stop
                    # information is specified by the user, assume the impact
                    # applies across all 24 hours
                    try:
                        # Set the starting and stopping hours for the impact
                        start_stop_hr = [
                            tsv_adjustments[a][x] for x in [
                                "start_hour", "stop_hour"]]
                        # Generate a list of all hours of day in which the
                        # time-varying efficiency impact applies
                        try:
                            # Handle case where user specifies an overnight
                            # start/stop time (e.g., 11AM to 5AM)
                            if start_stop_hr[0] <= start_stop_hr[1]:
                                applicable_hrs = list(range(
                                    start_stop_hr[0] - 1, start_stop_hr[1]))
                            else:
                                applicable_hrs = list(range(
                                    0, start_stop_hr[1])) + \
                                    list(range(start_stop_hr[0], 24))
                        # Error sets applicable hour range to all day
                        except TypeError:
                            applicable_hrs = list(range(0, 24))
                    except (TypeError, KeyError):
                        applicable_hrs = list(range(0, 24))

                    # Set enumerate object for applicable day/hour ranges
                    enumerate_list = list(
                        enumerate(itertools.product(
                            range(365), range(24))))

                    # Apply time-varying impacts based on type of time-varying
                    # efficiency feature(s) specified for the measure

                    # "Shed" time-varying efficiency feature applies a %
                    # hourly load reduction across the user-specified hours
                    if "shed" in a:
                        # Determine the relative impact of the shed on the
                        # baseline load (specified as a change fraction)
                        # during the specified hour range
                        try:
                            rel_save_tsv = tsv_adjustments[a][
                                "relative energy change fraction"]
                        except KeyError:
                            rel_save_tsv = 0
                        # Reflect the shed impacts on efficient load shape
                        # across all relevant hours of the year
                        eff_load_hourly = [base_load_hourly[i] * (
                            1 - rel_save_tsv) if (
                            x in applicable_days and y in applicable_hrs) else
                            eff_load_hourly[i] for
                            i, (x, y) in enumerate_list]
                    # "Shift" time-varying efficiency features move a certain
                    # percentage of baseline load from one time period into
                    # another time period
                    elif "shift" in a:
                        # Set the number of hours earlier to shift the load
                        offset_hrs = tsv_adjustments[a]["offset_hrs_earlier"]
                        # If the user has not specified a time range for the
                        # load shifting, assume the measure shifts the entire
                        # load shape earlier by the number of hours set above
                        if len(applicable_hrs) == 24:
                            # Reflect load shifting in efficient load shape
                            # across all 8760 hours of the year; the initial
                            # efficient load in hour X is now the load in hour
                            # X minus user-specified hour offset
                            eff_load_hourly = [
                                base_load_hourly[i + offset_hrs] if ((
                                    i + offset_hrs) <= 8759 and
                                    x in applicable_days) else
                                base_load_hourly[(y + offset_hrs) - 24] for
                                i, (x, y) in enumerate_list]
                        # If the user has specified a time range for the load
                        # shifting, shift the load in accordance with range
                        else:
                            # Determine the relative amount of baseline load
                            # to shift out of the specified time window
                            try:
                                rel_save_tsv = tsv_adjustments[a][
                                    "relative energy change fraction"]
                            except KeyError:
                                rel_save_tsv = 0
                            # Determine the hour range to shift the load to (
                            # take the user-specified hour range and shift it
                            # backward by the user-specified number of hours
                            # to reflect e.g., pre-heating or cooling)
                            new_start, new_end = [
                                (x - offset_hrs) if (
                                    x - offset_hrs) >= 0 else
                                ((x - offset_hrs) + 24) for x in [
                                    min(applicable_hrs), max(applicable_hrs)]]
                            # Handle case where load is shifted to an overnight
                            # start/stop time (e.g., 11AM-5AM the next morning)
                            if new_start <= new_end:
                                hrs_to_shift_to = list(
                                    range(new_start, new_end + 1))
                            else:
                                hrs_to_shift_to = \
                                    list(range(new_start, 24)) + \
                                    list(range(0, new_end + 1))

                            # Reflect load shifting impacts on efficient load
                            # shape across all 8670 hours of the year; take the
                            # user-specified % of load in the user-specified
                            # hour range and move it X hours earlier, where X
                            # is determined by the "offset_hours" parameter
                            eff_load_hourly = [
                                    (base_load_hourly[i] + (
                                        base_load_hourly[
                                            i + offset_hrs] *
                                        rel_save_tsv)) if (
                                        ((i + offset_hrs) <= 8759 and
                                         x in applicable_days)
                                        and y in hrs_to_shift_to and
                                        y not in applicable_hrs) else
                                    (base_load_hourly[i] * (
                                      1 - rel_save_tsv) + (base_load_hourly[
                                        i + offset_hrs] *
                                        rel_save_tsv)) if (
                                        ((i + offset_hrs) <= 8759 and
                                         x in applicable_days)
                                        and y in hrs_to_shift_to and
                                        y in applicable_hrs) else
                                    (base_load_hourly[i] +
                                     base_load_hourly[
                                        (y + offset_hrs) - 24] * rel_save_tsv)
                                    if (y in hrs_to_shift_to and
                                        y not in applicable_hrs and
                                        x in applicable_days) else
                                    (base_load_hourly[i] * (
                                        1 - rel_save_tsv) + base_load_hourly[
                                        (y + offset_hrs) - 24] * rel_save_tsv)
                                    if (y in hrs_to_shift_to and
                                        y in applicable_hrs and
                                        x in applicable_days) else
                                    eff_load_hourly[i] * (
                                        1 - rel_save_tsv) if (
                                        y in applicable_hrs and
                                        x in applicable_days) else
                                    eff_load_hourly[i] for i, (x, y) in
                                    enumerate_list]

                    # "Shape" time-sensitive efficiency features reshape
                    # the baseline load shape in accordance with custom load
                    # savings shape information specified either for a typical
                    # day or across all 8760 hours of the year
                    elif "shape" in a:
                        # Custom daily load savings shape information is
                        # applied across all applicable days of the year
                        if "custom_daily_savings" in \
                            tsv_adjustments[a].keys() and tsv_adjustments[a][
                                "custom_daily_savings"] is not None:
                            # Set the custom daily savings shape (each element
                            # of the list represents hourly savings fraction)
                            custom_save_shape = \
                                tsv_adjustments[a]["custom_daily_savings"]
                            # Reflect custom load savings in efficient load
                            # shape
                            eff_load_hourly = [
                                base_load_hourly[i] * (
                                    1 - custom_save_shape[y]) if (
                                    x in applicable_days) else
                                eff_load_hourly[i] for
                                i, (x, y) in enumerate_list]

                        # Custom annual load savings shape information contains
                        # savings fractions for all 8760 hours of the year
                        elif "custom_annual_savings" in \
                            tsv_adjustments[a].keys() and tsv_adjustments[a][
                                "custom_annual_savings"] is not None:
                            # Set the custom 8760 savings shape data, which are
                            # stored in a dict initialized with the measure
                            # from a CSV, where the dict will be keyed in by
                            # the current combination of end use, building
                            # type, and climate zone to yield the 8760 shape
                            try:
                                custom_hr_save_shape = tsv_adjustments[a][
                                    "custom_annual_savings"][eu][
                                    load_fact_bldg_key][load_fact_climate_key][
                                    mult_sysshp_key_save]
                            except KeyError:
                                # Try again with the assumption that there is
                                # only one savings shape version per climate,
                                # building, and end use combination (e.g.,
                                # this will be the case for EE measures, vs.
                                # DR measures which may respond to more than
                                # one peak period range)
                                try:
                                    custom_hr_save_shape = tsv_adjustments[a][
                                        "custom_annual_savings"][eu][
                                        load_fact_bldg_key][
                                        load_fact_climate_key]["set 1"]
                                except KeyError:
                                    custom_hr_save_shape = []

                            # Ensure that the resultant custom savings shape
                            # for the current combination of climate zone,
                            # building type, and end use is not zero elements.
                            # If the savings shape is zero elements, warn the
                            # user (in verbose mode) that no savings shape
                            # data were found for the current climate/building/
                            # end use combination and that the savings will be
                            # assumed to be zero.
                            if len(custom_hr_save_shape) == 0:
                                verboseprint(
                                    opts.verbose,
                                    "Measure '" + self.name + "', requires "
                                    "custom savings shape data, but none were "
                                    "found for the combination of climate "
                                    "zone " + load_fact_climate_key +
                                    " (system load " + mult_sysshp_key_save +
                                    "), building type " +
                                    load_fact_bldg_key + ", and end use " +
                                    eu + ". Assuming savings are zero for "
                                    " this combination. If this is "
                                    "unexpected, check that 8760 hourly "
                                    "savings fractions are available for "
                                    "all baseline market segments the "
                                    "measure applies to in ./ecm_definitions/"
                                    "energy_plus_data/savings_shapes.")
                                custom_hr_save_shape = [0 for x in range(8760)]
                            # Reflect custom load savings in efficient load
                            # shape; screen for NaNs in the CSV
                            eff_load_hourly = [(
                                base_load_hourly[x] +
                                custom_hr_save_shape[x]) if
                                numpy.isfinite(custom_hr_save_shape[x]) else
                                eff_load_hourly[x] for x in range(8760)]
                            # Ensure all efficient load fractions are greater
                            # than zero
                            eff_load_hourly = [
                                eff_load_hourly[x] if eff_load_hourly[x] >= 0
                                else 0 for x in range(8760)]
                        else:
                            # Throw an error if the load reshaping operation
                            # name is invalid
                            raise KeyError(
                                "Invalid load reshaping operation name for "
                                "measure: " + self.name + ". Valid reshaping "
                                "operations include 'custom_daily_savings' "
                                "or 'custom_annual_savings'.")
                    # Yield error if unexpected TSV feature type is present
                    else:
                        raise KeyError(
                            "Invalid feature type present in tsv_features "
                            "attribute for measure " + self.name +
                            " - valid types include: " +
                            str(self.handyvars.tsv_feature_types))
                # Update hourly fractions of annual baseline and efficient
                # energy to reflect baseline hourly load shape plus effects of
                # time-sensitive measure features on the baseline load (if any)
                if opts.sect_shapes is True:
                    # Base load weighted by contribution of climate for load
                    # to EMM region
                    base_ls_wt = [
                        x * emm_adj_wt for x in base_load_hourly]
                    # Efficient load weighted by contribution of climate for
                    # load to current EMM region
                    eff_ls_wt = [
                        x * emm_adj_wt for x in eff_load_hourly]
                    # Add to existing base load fractions (across all climates
                    # that overlap with the current EMM region)
                    energy_base_shape = [
                        energy_base_shape[x] + base_ls_wt[x] for
                        x in range(len(energy_base_shape))]
                    # Add to existing efficient load fractions (across all
                    # climates that overlap with the current EMM region)
                    energy_eff_shape = [
                        energy_eff_shape[x] + eff_ls_wt[x] for
                        x in range(len(energy_eff_shape))]

                # Further adjust baseline and efficient load shapes
                # to account for time sensitive valuation (TSV) output metrics
                if tsv_metrics is not False:

                    # Set legible name for each TSV metrics input

                    # Output type (energy/power)
                    if tsv_metrics[0] == "1":
                        output = "energy"
                    else:
                        output = "power"
                    # Applicable hours of focus (all/peak/take)
                    if tsv_metrics[1] == "1":
                        hours = "all"
                    elif tsv_metrics[1] == "2":
                        hours = "peak"
                    else:
                        hours = "take"
                    # Applicable season of focus (summer/winter/intermediate)
                    if tsv_metrics[2] == '1':
                        season = "summer"
                    elif tsv_metrics[2] == '2':
                        season = "winter"
                    elif tsv_metrics[2] == '3':
                        season = "intermediate"
                    # Type of calculation (sum/max/avg depending on output)
                    if output == "energy" and tsv_metrics[3] == "1":
                        calc = "sum"
                    elif output == "power" and tsv_metrics[3] == "1":
                        calc = "max"
                    else:
                        calc = "avg"
                    # Days to perform operations over (applicable to sum
                    # and averaging calculations)
                    if tsv_metrics[-1] == "1":
                        days = "all"
                    elif tsv_metrics[-1] == "2":
                        days = "weekdays"
                    elif tsv_metrics[-1] == "3":
                        days = "weekends"
                    else:
                        days = None

                    # Set applicable day range

                    # Sum or average calcs (spans multiple days)
                    if calc == "sum" or calc == "avg":
                        tsv_metrics_days = self.handyvars.tsv_metrics_data[
                            "season days"][days][season]
                    # Maximum calc type (pertains only to a peak day)
                    else:
                        tsv_metrics_days = [
                            self.handyvars.tsv_metrics_data[
                                "peak days"][season][cz[0]]]

                    # Set applicable daily hour range
                    # NOTE: for now, use peak/take periods from 2050 only

                    # Sum or average calc type (spans multiple hours)
                    if calc in ["sum", "avg"]:
                        # All hours of the day
                        if hours == "all":
                            tsv_metrics_hrs = list(range(1, 25))
                        # Peak hours only
                        elif hours == "peak":
                            # Handle one set of net load shape data differently
                            # than multiple sets
                            if mult_sysshp is False:
                                tsv_metrics_hrs = \
                                    self.handyvars.tsv_metrics_data[
                                        "system load hours"][season]["2050"][
                                        cz[0]]["peak range"]
                            else:
                                tsv_metrics_hrs = \
                                    self.handyvars.tsv_metrics_data[
                                        "system load hours"][season]["2050"][
                                        cz[0]][mult_sysshp_key_metrics][
                                        "peak range"]
                        # Take hours only
                        else:
                            # Handle one set of net load shape data differently
                            # than multiple sets
                            if mult_sysshp is False:
                                tsv_metrics_hrs = \
                                    self.handyvars.tsv_metrics_data[
                                        "system load hours"][season]["2050"][
                                        cz[0]]["take range"]
                            else:
                                tsv_metrics_hrs = \
                                    self.handyvars.tsv_metrics_data[
                                        "system load hours"][season]["2050"][
                                        cz[0]][mult_sysshp_key_metrics][
                                        "take range"]
                    # Maximum calc type (pertains only to a max/min hour)
                    else:
                        # All hours (assume max peak hour) or max peak hour
                        if hours == "all" or hours == "peak":
                            # Handle one set of net load shape data differently
                            # than multiple sets
                            if mult_sysshp is False:
                                tsv_metrics_hrs = [
                                    self.handyvars.tsv_metrics_data[
                                        "system load hours"][season]["2050"][
                                        cz[0]]["max"]]
                            else:
                                tsv_metrics_hrs = [
                                    self.handyvars.tsv_metrics_data[
                                        "system load hours"][season]["2050"][
                                        cz[0]][mult_sysshp_key_metrics]["max"]]
                        # Min take hour
                        else:
                            # Handle one set of net load shape data differently
                            # than multiple sets
                            if mult_sysshp is False:
                                tsv_metrics_hrs = [
                                    self.handyvars.tsv_metrics_data[
                                        "system load hours"][season]["2050"][
                                        cz[0]]["min"]]
                            else:
                                tsv_metrics_hrs = [
                                    self.handyvars.tsv_metrics_data[
                                        "system load hours"][season]["2050"][
                                        cz[0]][mult_sysshp_key_metrics]["min"]]

                    # Determine number of days to average over; if peak day
                    # only, set this number to one
                    if calc == 'avg':
                        # Power (single hour) output case; divide by total
                        # applicable hours for the appropriate season times
                        # total applicable days
                        if output == "power":
                            avg_len = len(tsv_metrics_days) * \
                                      len(tsv_metrics_hrs)
                        # Energy (multiple hour) output case; divide by total
                        # applicable days
                        else:
                            avg_len = len(tsv_metrics_days)
                    else:
                        avg_len = 1

                    # Adjust the baseline and efficient loads to reflect
                    # only the hourly values that fall within the applicable
                    # hour and day ranges from above; set all inapplicable
                    # values to zero (to maintain full 8760 list length)
                    base_load_hourly, eff_load_hourly = [[
                        (x[i] / avg_len) if (
                            (d + 1) in tsv_metrics_days and
                            (h + 1) in tsv_metrics_hrs)
                        else 0 for
                        i, (d, h) in
                        self.handyvars.tsv_metrics_data["hourly index"]] for
                        x in [base_load_hourly, eff_load_hourly]]

                    # Sum across all 8760 hourly baseline and efficient load
                    # values to arrive at final factor used to rescale
                    # annually-determined energy totals
                    energy_scale_base += numpy.sum([
                        x * emm_adj_wt for x in base_load_hourly])
                    energy_scale_eff += numpy.sum([
                        x * emm_adj_wt for x in eff_load_hourly])
                else:
                    # If no tsv metrics are specified, annually-determined
                    # baseline energy total requires no rescaling (8760
                    # baseline hourly values sum to 1)
                    energy_scale_base = 1
                    # Sum across all 8760 hourly efficient load values
                    # to arrive at final factor used to rescale annually-
                    # determined energy totals
                    energy_scale_eff += numpy.sum([
                        x * emm_adj_wt for x in eff_load_hourly])

        # Finalize carbon/cost scaling factor variables, but only if
        # either measure TSV features are present or the user desires
        # TSV metrics outputs; assume these shapes are not necessary if
        # the user only desires sector-level load shapes
        if tsv_metrics is not False or self.tsv_features is not None:

            # Calculate baseline/efficient cost rescaling factors as the sums
            # of the hourly baseline/efficient load shape multiplied by the
            # hourly price scaling factors; calculate across available
            # projection years for the price scaling factors
            for yr in cost_scale_base.keys():
                cost_scale_base[yr] += numpy.sum([
                    x * y for x, y in zip(
                        base_load_hourly, cost_fact_hourly[yr])])
                cost_scale_eff[yr] += numpy.sum([
                    x * y for x, y in zip(
                        eff_load_hourly, cost_fact_hourly[yr])])

            # Calculate baseline/efficient emissions rescaling factors as the
            # sums of the hourly baseline/efficient load shape multiplied by
            # the hourly emissions scaling factors; calculate across available
            # projection years for the emissions scaling factors
            for yr in carb_scale_base.keys():
                carb_scale_base[yr] += numpy.sum([
                    x * y for x, y in zip(
                        base_load_hourly, carbon_fact_hourly[yr])])
                carb_scale_eff[yr] += numpy.sum([
                    x * y for x, y in zip(
                        eff_load_hourly, carbon_fact_hourly[yr])])

            # Extend price/emissions factors across all years in the AEO time
            # horizon
            for yr in self.handyvars.aeo_years:
                # Find year in the cost scaling factors data that maps to the
                # current AEO year
                tsv_yr_cost = [
                    x[0] for x in cost_yr_map.items() if yr in x[1]][0]
                # Find year in the emissions scaling factors data that maps to
                # the current AEO year
                tsv_yr_carb = [
                    x[0] for x in carb_yr_map.items() if yr in x[1]][0]
                # Finalize the cost/emissions scaling factors data for the
                # current AEO year

                # APPROACH 1: TAKE THE DATA AS IS
                cost_scale_base_aeo[yr], cost_scale_eff_aeo[yr], \
                    carb_scale_base_aeo[yr], carb_scale_eff_aeo[yr] = [
                    cost_scale_base[tsv_yr_cost],
                    cost_scale_eff[tsv_yr_cost],
                    carb_scale_base[tsv_yr_carb],
                    carb_scale_eff[tsv_yr_carb]]
                # # APPROACH 2: RUNNING MEAN
                # if yr == self.handyvars.aeo_years[0]:
                #     cost_scale_base_aeo[yr], cost_scale_eff_aeo[yr], \
                #         carb_scale_base_aeo[yr], carb_scale_eff_aeo[yr] = [
                #         cost_scale_base[tsv_yr_cost],
                #         cost_scale_eff[tsv_yr_cost],
                #         carb_scale_base[tsv_yr_carb],
                #         carb_scale_eff[tsv_yr_carb]]
                # else:
                #     cost_scale_base_aeo[yr], cost_scale_eff_aeo[yr], \
                #         carb_scale_base_aeo[yr], carb_scale_eff_aeo[yr] = [
                #         x * (1 / len(self.handyvars.aeo_years)) + y * (
                #             1 - (1 / len(self.handyvars.aeo_years))) for
                #         x, y in zip([
                #             cost_scale_base[tsv_yr_cost],
                #             cost_scale_eff[tsv_yr_cost],
                #             carb_scale_base[tsv_yr_carb],
                #             carb_scale_eff[tsv_yr_carb]], [
                #             cost_scale_base_aeo[str(int(yr) - 1)],
                #             cost_scale_eff_aeo[str(int(yr) - 1)],
                #             carb_scale_base_aeo[str(int(yr) - 1)],
                #             carb_scale_eff_aeo[str(int(yr) - 1)]])]
        else:
            cost_scale_base_aeo, cost_scale_eff_aeo, carb_scale_base_aeo, \
                carb_scale_eff_aeo = (1 for n in range(4))

        # After calculations are complete, if measure fuel switches from
        # fossil to electricity and the current baseline microsegment indicates
        # fossil fuel, set all 8760 baseline values to zero (it is assumed that
        # sector-level load shapes will only be relevant to the electricity
        # system, which will not see a baseline load that is satisfied by
        # non-electric fuel (fro this perspective, measures that fuel switch
        # heating or water heating to electricity add load to the electricity
        # system that wasn't there before)
        if self.fuel_switch_to == "electricity" and \
                "electricity" not in mskeys and opts.sect_shapes is True:
            energy_base_shape = [0 for x in range(len(energy_base_shape))]

        # Return hourly fractions of annual baseline and efficient energy
        # if sector-level load shape information is desired by the user
        if opts.sect_shapes is True:
            updated_tsv_shapes = {
                "baseline": energy_base_shape,
                "efficient": energy_eff_shape}
        else:
            updated_tsv_shapes = None
        # Return the final energy, cost, and emissions rescaling factors
        # to use in modifying annually-determined energy, cost, and emissions
        # totals such that they reflect sub-annual assessment of these totals
        updated_tsv_fracs = {
            "energy": {
                "baseline": energy_scale_base,
                "efficient": energy_scale_eff},
            "cost": {
                "baseline": cost_scale_base_aeo,
                "efficient": cost_scale_eff_aeo
            },
            "carbon": {
                "baseline": carb_scale_base_aeo,
                "efficient": carb_scale_eff_aeo
            }}

        return updated_tsv_fracs, updated_tsv_shapes

    def convert_costs(self, convert_data, bldg_sect, mskeys, cost_meas,
                      cost_meas_units, cost_base_units, verbose):
        """Convert measure cost to comparable baseline cost units.

        Args:
            convert_data (dict): Measure cost unit conversions.
            bldg_sect (string): Applicable building sector for measure cost.
            mskeys (tuple): Full applicable market microsegment information for
                measure cost (mseg type->reg->bldg->fuel->end use->technology
                type->structure type).
            cost_meas (float): Initial user-defined measure cost.
            cost_meas_units (string): Initial user-defined measure cost units.
            cost_base_units (string): Comparable baseline cost units.
            verbose (bool or NoneType): Determines whether to print all
                user warnings and messages.

        Returns:
            Updated measure costs and cost units that are consistent with
            baseline technology cost units.

        Raises:
            KeyError: If no cost conversion data are available for
                the particular measure microsegment
            ValueError: If initial user-defined measure cost units are
                determined to be invalid/unsupported.
        """
        # Separate cost units into the cost year and everything else
        cost_meas_units_unpack, cost_base_units_unpack = [re.search(
            r'(\d*)(.*)', x) for x in [cost_meas_units, cost_base_units]]
        # Establish measure and baseline cost year
        cost_meas_yr, cost_base_yr = \
            cost_meas_units_unpack.group(1), cost_base_units_unpack.group(1)
        # Establish measure and baseline cost units (excluding cost year)
        cost_meas_noyr, cost_base_noyr = \
            cost_meas_units_unpack.group(2), cost_base_units_unpack.group(2)

        # If the cost units of the measure are inconsistent with the baseline
        # cost units (with the cost year removed), map measure cost units to
        # baseline cost units
        if cost_meas_noyr != cost_base_noyr:
            # Retrieve whole building or end use-specific cost unit conversion
            # data. Conversion data should be formatted in a list to simplify
            # its handling in subsequent operations

            # Find top-level key for retrieving data from cost translation
            # dictionary
            top_keys = self.handyvars.cconv_topkeys_map
            try:
                top_key = next(x for x in top_keys.keys() if
                               cost_meas_noyr in top_keys[x])
            except StopIteration as e:
                raise KeyError("No conversion data for ECM '" +
                               self.name + "' cost units '" +
                               cost_meas_units + "'") from e

            if top_key == "whole building":
                # Retrieve whole building-level cost conversion data
                whlbldg_keys = self.handyvars.cconv_whlbldgkeys_map
                try:
                    whlbldg_key = next(
                        x for x in whlbldg_keys.keys() if
                        cost_meas_noyr in whlbldg_keys[x])
                except StopIteration as e:
                    raise KeyError("No conversion data for ECM '" +
                                   self.name + "' cost units '" +
                                   cost_meas_units + "'") from e
                # Retrieve node to square footage or occupant to square
                # footage conversion data
                convert_units_data = [
                    convert_data['cost unit conversions'][top_key][
                        whlbldg_key]]
            elif top_key == "heating and cooling":
                # Retrieve heating/cooling cost conversion data
                htcl_keys = self.handyvars.cconv_htclkeys_map
                try:
                    htcl_key = next(
                        x for x in htcl_keys.keys() if
                        cost_meas_noyr in htcl_keys[x])
                except StopIteration as e:
                    raise KeyError("No conversion data for ECM '" +
                                   self.name + "' cost units" +
                                   cost_meas_units + "'") from e
                if htcl_key == "supply":
                    # Retrieve supply-side heating/cooling conversion data
                    supply_keys = self.handyvars.cconv_tech_htclsupply_map
                    try:
                        supply_key = next(
                            x for x in supply_keys.keys() if
                            cost_meas_noyr in supply_keys[x])
                    except StopIteration as e:
                        raise KeyError("No conversion data for ECM '" +
                                       self.name + "' cost units" +
                                       cost_meas_units + "'") from e
                    convert_units_data = [
                        convert_data['cost unit conversions'][top_key][
                            htcl_key][supply_key]]
                else:
                    # Retrieve demand-side heating/cooling conversion data
                    demand_keys = self.handyvars.cconv_tech_mltstage_map
                    try:
                        demand_key = next(
                            x for x in demand_keys.keys() if
                            cost_meas_noyr in demand_keys[x]['key'])
                    except StopIteration as e:
                        raise KeyError("No conversion data for ECM '" +
                                       self.name + "' cost units" +
                                       cost_meas_units + "'") from e
                    convert_units_data = [
                        convert_data['cost unit conversions'][top_key][
                            htcl_key][x] for x in
                        demand_keys[demand_key]["conversion stages"]]
            else:
                # Retrieve conversion data for costs outside of the
                # whole building or heating/cooling cases
                convert_units_data = [
                    convert_data['cost unit conversions'][top_key]]

            # Finalize cost conversion information retrieved above

            # Initialize a final cost conversion value for the microsegment
            convert_units = 1
            # Loop through list of conversion data, multiplying initial
            # conversion value by successive list elements and weighting
            # results as needed to map conversion factors for multiple
            # non-Scout building types to the single Scout building type of
            # the current microsegment
            for cval in convert_units_data:
                # Case where conversion data is split by building sector
                if isinstance(cval['conversion factor']['value'], dict):
                    # Restrict to building sector of current microsegment
                    cval_bldgtyp = \
                        cval['conversion factor']['value'][bldg_sect]
                    # Case where conversion data is further nested
                    # by Scout building type and technology type (needed for
                    # conversion to $/unit)
                    if cval['original units'] == "$/ft^2 floor":
                        cval_bldgtyp = cval_bldgtyp[mskeys[2]]
                        # Case with $/ft^2 floor to $/unit cost conversion
                        # for lighting technology (multiple units per house)
                        if mskeys[5] is not None and any([
                                k in mskeys[5] for k in cval_bldgtyp.keys()]):
                            convert_units *= next(
                                x[1] for x in cval_bldgtyp.items() if
                                x[0] in mskeys[5])
                        # Case with $/ft^2 floor to $/unit cost conversion
                        # for non-lighting technology (one unit per house)
                        else:
                            convert_units *= cval_bldgtyp[
                                "all other technologies"]
                    # Case where conversion data is further nested by
                    # Scout building type and EnergyPlus building type
                    elif isinstance(cval_bldgtyp, dict) and isinstance(
                            cval_bldgtyp[mskeys[2]], dict):
                        # Develop weighting factors to map conversion data
                        # from multiple EnergyPlus building types to the
                        # single Scout building type of the current
                        # microsegment
                        cval_bldgtyp = cval_bldgtyp[mskeys[2]].values()
                        bldgtyp_wts = convert_data[
                            'building type conversions'][
                            'conversion data']['value'][bldg_sect][
                            mskeys[2]].values()
                        convert_units *= sum([a * b for a, b in zip(
                            cval_bldgtyp, bldgtyp_wts)])
                    # Case where conversion data is further nested by
                    # Scout building type
                    elif isinstance(cval_bldgtyp, dict):
                        convert_units *= cval_bldgtyp[mskeys[2]]
                    # Case where conversion data is not nested further
                    else:
                        convert_units *= cval_bldgtyp
                else:
                    convert_units *= cval['conversion factor']['value']
        else:
            convert_units = 1

        # Map the year of measure cost units to the year of baseline cost units

        # If measure and baseline cost years are inconsistent, map measure
        # to baseline cost year using Consumer Price Index (CPI) data
        if cost_meas_yr != cost_base_yr:
            # Set full CPI dataset
            cpi = self.handyvars.consumer_price_ind
            # Find array of rows in CPI dataset associatd with the measure
            # cost year
            cpi_row_meas = [x for x in cpi if cost_meas_yr in x['DATE']]
            if len(cpi_row_meas) == 0:
                cpi_row_meas = cpi
            # Find array of rows in CPI dataset associated with the baseline
            # cost year
            cpi_row_base = [x for x in cpi if cost_base_yr in x['DATE']]
            if len(cpi_row_base) == 0:
                cpi_row_base = cpi
            # Calculate year conversion using last row in each array
            # (representing the latest CPI value listed for each year)
            convert_yr = cpi_row_base[-1][1] / cpi_row_meas[-1][1]
        else:
            convert_yr = 1

        # Apply finalized cost conversion and year conversion factors
        # to measure costs to map to baseline cost units
        cost_meas_fin = cost_meas * convert_units * convert_yr

        # Adjust initial measure cost units to reflect the conversion (should
        # now be consistent with baseline cost units, this is checked in
        # a subsequent step of the 'fill_mkts' routine)

        # Cost year/unit adjustment involving multiple conversion stages
        # (use the revised measure units for the final conversion stage)
        if convert_units != 1 and isinstance(convert_units_data, list):
            cost_meas_units_fin = cost_base_yr + \
                convert_units_data[-1]['revised units']
        # Cost year/unit adjustments involving a single stage of conversion
        elif convert_units != 1:
            cost_meas_units_fin = cost_base_yr + \
                convert_units_data['revised units']
        # Cost year adjustment only
        else:
            cost_meas_units_fin = cost_base_yr + cost_base_noyr

        # Case where cost conversion has succeeded
        if cost_meas_units_fin == cost_base_units:
            # If in verbose mode, notify user of cost conversion details
            if verbose:
                # Set base user message
                if not isinstance(cost_meas, numpy.ndarray):
                    user_message = "ECM '" + self.name + \
                        "' cost converted from " + \
                        str(cost_meas) + " " + cost_meas_units + " to " + \
                        str(round(cost_meas_fin, 3)) + " " + \
                        cost_meas_units_fin
                else:
                    user_message = "ECM '" + self.name + \
                        "' cost converted from " + \
                        str(numpy.mean(cost_meas)) + " " + cost_meas_units + \
                        " to " + str(round(numpy.mean(cost_meas_fin), 3)) + \
                        " " + cost_meas_units_fin
                # Add building type information to base message in cases where
                # cost conversion depends on building type (e.g., for envelope
                # components) or technology type (e.g., for residential
                # controls ECMs)
                if (bldg_sect != "residential" or cost_meas_noyr not in
                    self.handyvars.cconv_bytech_units_res) and \
                    (cost_meas_noyr in self.handyvars.cconv_bybldg_units or
                     isinstance(self.installed_cost, dict)):
                    user_message += " for '" + mskeys[2] + "'"
                elif (cost_meas_noyr in
                      self.handyvars.cconv_bytech_units_res and
                        bldg_sect == "residential"):
                    user_message += " for '" + mskeys[2] + \
                        "' and technology '" + str(mskeys[-2]) + "'"

                # Print user message
                print(user_message)
        # Case where cost conversion has not succeeded
        else:
            raise ValueError(
                "ECM '" + self.name + "' cost units '" +
                str(cost_meas_units_fin) + "' not equal to base units '" +
                str(cost_base_units) + "'")

        return cost_meas_fin, cost_meas_units_fin

    def partition_microsegment(
            self, adopt_scheme, diffuse_params, mskeys, mkt_scale_frac,
            new_constr, stock_total_init, energy_total_init,
            carb_total_init, cost_base, cost_meas, cost_energy_base,
            cost_energy_meas, rel_perf, life_base, life_meas,
            site_source_conv_base, site_source_conv_meas, intensity_carb_base,
            intensity_carb_meas, energy_total_scnd, tsv_adj, tsv_shapes, opts,
            contrib_mseg_key, contrib_meas_pkg):
        """Find total, competed, and efficient portions of a mkt. microsegment.

        Args:
            adopt_scheme (string): Assumed consumer adoption scenario.
            diffuse_params (NoneType): Parameters relating to the 'adjusted
                adoption' consumer choice model (currently a placeholder).
            mskeys (tuple): Dictionary key information for the currently
                partitioned market microsegment (mseg type->reg->bldg->
                fuel->end use->technology type->structure type)
            mkt_scale_frac (float): Microsegment scaling fraction (used to
                break market microsegments into more granular sub-markets).
            new_constr (dict): Data needed to determine the portion of the
                total microsegment stock that is added in each year.
            stock_total_init (dict): Baseline technology stock, by year.
            energy_total_init (dict): Baseline microsegment primary energy use,
                by year.
            carb_total_init (dict): Baseline microsegment carbon emissions,
                by year.
            cost_base (dict): Baseline technology installed cost, by year.
            cost_meas (float): Measure installed cost, by year.
            cost_energy_base (dict): Baseline fuel cost, by year.
            cost_energy_meas (dict): Measure fuel cost, by year.
            rel_perf (float): Measure performance relative to baseline.
            life_base (dict): Baseline technology lifetime.
            life_meas (float): Measure lifetime.
            site_source_conv_base (dict): Baseline fuel site-source conversion,
                by year.
            site_source_conv_meas (dict): Measure fuel site-source conversion,
                by year.
            intensity_carb_base (dict): Baseline fuel carbon intensity,
                by year.
            intensity_carb_meas (dict): Measure fuel carbon intensity, by year.
            tsv_adj (dict): Adjustment for time sensitive efficiency valuation.
            tsv_shapes (dict): 8760 hourly adjustments (sum to tsv_adj values)
            opts (object): Stores user-specified execution options.
            contrib_mseg_key (tuple): The same as mskeys, but adjusted to merge
                windows solar/conduction msegs into "windows" if applicable.
            contrib_meas_pkg (list): Names of measures that contribute to pkgs.

        Returns:
            Total, total-efficient, competed, and competed-efficient
            stock, energy, carbon, and cost market microsegments by year; for
            fuel switching measures, also reports out any remaining
            (unswitched) energy, carbon, and cost segments by year.
        """
        # Initialize stock, energy, and carbon mseg partition dicts, where the
        # dict keys will be years in the modeling time horizon
        stock_total, energy_total, carb_total, energy_total_sbmkt, \
            carb_total_sbmkt, stock_total_meas, \
            energy_total_eff, carb_total_eff, stock_compete, \
            energy_compete, carb_compete, energy_compete_sbmkt, \
            carb_compete_sbmkt, stock_compete_meas, \
            energy_compete_eff, carb_compete_eff, stock_total_cost, \
            energy_total_cost, carb_total_cost, stock_total_cost_eff, \
            energy_total_eff_cost, carb_total_eff_cost, \
            stock_compete_cost, energy_compete_cost, carb_compete_cost, \
            stock_compete_cost_eff, energy_compete_cost_eff, \
            carb_compete_cost_eff = ({} for n in range(28))

        # Initialize the portion of microsegment already captured by the
        # efficient measure as 0, and the portion baseline stock as 1.
        captured_eff_frac = 0
        captured_base_frac = 1

        # Initialize variables that capture the portion of baseline
        # energy, carbon, and energy cost that remains with the baseline fuel
        # (for fuel switching measures only)
        fs_energy_eff_remain, fs_carb_eff_remain, fs_energy_cost_eff_remain = (
            {yr: 0 for yr in self.handyvars.aeo_years} for n in range(3))

        # Set the relative energy performance of the current year's
        # competed and uncompeted stock that goes uncaptured
        rel_perf_uncapt = 1
        # Set time sensitive energy scaling factors for all baseline stock
        tsv_energy_base = tsv_adj["energy"]["baseline"]
        # Set time-sensitive energy scaling factors for all efficient stock
        tsv_energy_eff = tsv_adj["energy"]["efficient"]

        # In cases where secondary microsegments are present, initialize a
        # dict of year-by-year secondary microsegment adjustment information
        # that will be used to scale down the secondary microsegment(s) in
        # accordance with the portion of the total applicable primary stock
        # that is captured by the measure in each year
        if energy_total_scnd is not False or mskeys[0] == "secondary":
            # Set short names for secondary adjustment information dicts
            secnd_adj_sbmkt = self.markets[adopt_scheme]["mseg_adjust"][
                "secondary mseg adjustments"]["sub-market"]
            secnd_adj_stk = self.markets[adopt_scheme]["mseg_adjust"][
                "secondary mseg adjustments"]["stock-and-flow"]
            secnd_adj_mktshr = self.markets[adopt_scheme]["mseg_adjust"][
                "secondary mseg adjustments"]["market share"]
            # Determine a dictionary key indicating the climate zone, building
            # type, and structure type that is shared by the primary
            # microsegment and secondary microsegment
            secnd_mseg_adjkey = str((mskeys[1], mskeys[2], mskeys[-1]))
            # If no year-by-year secondary microsegment adjustment information
            # exists for the given climate zone, building type, and structure
            # type, initialize all year-by-year adjustment values as 0
            if secnd_mseg_adjkey not in secnd_adj_stk[
                    "original energy (total)"].keys():
                # Initialize sub-market secondary adjustment information

                # Initialize original primary microsegment stock information
                secnd_adj_sbmkt["original energy (total)"][
                    secnd_mseg_adjkey] = {
                        key: energy_total_scnd[key] for key in
                        self.handyvars.aeo_years}
                # Initialize sub-market adjusted microsegment stock information
                secnd_adj_sbmkt["adjusted energy (sub-market)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        self.handyvars.aeo_years, 0)

                # Initialize stock-and-flow secondary adjustment information

                # Initialize original primary microsegment stock information
                secnd_adj_stk["original energy (total)"][secnd_mseg_adjkey] = \
                    dict.fromkeys(self.handyvars.aeo_years, 0)
                # Initialize previously captured primary microsegment stock
                # information
                secnd_adj_stk["adjusted energy (previously captured)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        self.handyvars.aeo_years, 0)
                # Initialize competed primary microsegment stock information
                secnd_adj_stk["adjusted energy (competed)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        self.handyvars.aeo_years, 0)
                # Initialize competed and captured primary microsegment stock
                # information
                secnd_adj_stk["adjusted energy (competed and captured)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        self.handyvars.aeo_years, 0)

                # Initialize market share secondary adjustment information

                # Initialize original total captured stock information
                secnd_adj_mktshr["original energy (total captured)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        self.handyvars.aeo_years, 0)
                # Initialize original competed and captured stock information
                secnd_adj_mktshr["original energy (competed and captured)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        self.handyvars.aeo_years, 0)
                # Initialize adjusted total captured stock information
                secnd_adj_mktshr["adjusted energy (total captured)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        self.handyvars.aeo_years, 0)
                # Initialize adjusted competed and captured stock information
                secnd_adj_mktshr["adjusted energy (competed and captured)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        self.handyvars.aeo_years, 0)

        # In cases where no secondary heating/cooling microsegment is present,
        # set secondary microsegment adjustment key to None
        else:
            secnd_mseg_adjkey = None

        # Initialize data needed to merge sector-level information about the
        # current microsegment into a package, if the current measure is part
        # of a package
        if opts.sect_shapes is True and tsv_shapes is not None and \
                self.name in contrib_meas_pkg:
            self.sector_shapes_pkg[adopt_scheme][str(contrib_mseg_key)] = {
                yr: {"baseline": [], "efficient": []} for yr in
                self.handyvars.aeo_years_summary}

        # Loop through and update stock, energy, and carbon mseg partitions for
        # each year in the modeling time horizon
        for yr in self.handyvars.aeo_years:
            # Set time sensitive cost/emissions scaling factors for all
            # baseline stock; handle cases where these factors are/are not
            # broken out by AEO projection year
            try:
                tsv_ecost_base, tsv_carb_base = [
                    tsv_adj[x]["baseline"][yr] for x in ["cost", "carbon"]]
            except TypeError:
                tsv_ecost_base, tsv_carb_base = [
                    tsv_adj[x]["baseline"] for x in ["cost", "carbon"]]
            # Set time sensitive cost/emissions scaling factors for all
            # efficient stock; handle cases where these factors are/are not
            # broken out by AEO projection year
            try:
                tsv_ecost_eff, tsv_carb_eff = [
                    tsv_adj[x]["efficient"][yr] for x in ["cost", "carbon"]]
            except TypeError:
                tsv_ecost_eff, tsv_carb_eff = [
                    tsv_adj[x]["efficient"] for x in ["cost", "carbon"]]

            # For secondary microsegments only, update: a) sub-market scaling
            # fraction, based on any sub-market scaling in the associated
            # primary microsegment, and b) the portion of associated primary
            # microsegment stock that has been captured by the measure in
            # previous years
            if mskeys[0] == "secondary":
                # Adjust sub-market scaling fraction
                if secnd_adj_sbmkt["original energy (total)"][
                        secnd_mseg_adjkey][yr] != 0:
                    mkt_scale_frac = secnd_adj_sbmkt[
                        "adjusted energy (sub-market)"][
                        secnd_mseg_adjkey][yr] / \
                        secnd_adj_sbmkt["original energy (total)"][
                        secnd_mseg_adjkey][yr]
                # Adjust previously captured efficient fraction
                if secnd_adj_stk["original energy (total)"][
                        secnd_mseg_adjkey][yr] != 0:
                    captured_eff_frac = secnd_adj_stk[
                        "adjusted energy (previously captured)"][
                        secnd_mseg_adjkey][yr] / secnd_adj_stk[
                        "original energy (total)"][secnd_mseg_adjkey][yr]
                else:
                    captured_eff_frac = 0
                # Update portion of existing primary stock remaining with the
                # baseline technology
                captured_base_frac = 1 - captured_eff_frac

            # Stock, energy, and carbon adjustments
            stock_total[yr] = stock_total_init[yr] * mkt_scale_frac
            energy_total_sbmkt[yr] = energy_total_init[yr] * mkt_scale_frac
            energy_total[yr] = energy_total_sbmkt[yr] * tsv_energy_base
            carb_total_sbmkt[yr] = carb_total_init[yr] * mkt_scale_frac
            carb_total[yr] = carb_total_sbmkt[yr] * tsv_carb_base

            # Re-apportion total baseline microsegment energy across all 8760
            # hours of the year, if necessary (supports sector-level savings
            # shapes)

            # Only update sector-level shapes for certain years of focus;
            # ensure that load shape information is available for the
            # update and if not, yield an error message
            if opts.sect_shapes is True and yr in \
                self.handyvars.aeo_years_summary and \
                    tsv_shapes is not None:
                self.sector_shapes[adopt_scheme][mskeys[1]][yr]["baseline"] = [
                    self.sector_shapes[adopt_scheme][mskeys[1]][yr][
                        "baseline"][x] + tsv_shapes["baseline"][x] *
                    energy_total_sbmkt[yr] for x in range(8760)]
                # If current measure is part of an active package, add sector-
                # level information for the current baseline mseg to the
                # attribute that is later used to feed these data into the pkg.
                if str(contrib_mseg_key) in \
                        self.sector_shapes_pkg[adopt_scheme].keys():
                    self.sector_shapes_pkg[adopt_scheme][
                        str(contrib_mseg_key)][yr]["baseline"] = [
                        tsv_shapes["baseline"][x] * energy_total_sbmkt[yr] for
                        x in range(8760)]
            elif opts.sect_shapes is True and tsv_shapes is None and (
                mskeys[0] == "secondary" or (
                    mskeys[0] == "primary" and
                    mskeys[3] == "electricity")):
                raise ValueError(
                    "Missing hourly fraction of annual load data for "
                    "baseline energy use segment: " + str(mskeys) + ". ")

            # For a primary microsegment and adjusted adoption potential case,
            # determine the portion of competed stock that remains with the
            # baseline technology or changes to the efficient alternative
            # technology; for all other scenarios, set both fractions to 1
            if adopt_scheme == "Adjusted adoption potential" and \
               mskeys[0] == "primary":
                # PLACEHOLDER
                diffuse_eff_frac = 999
            else:
                diffuse_eff_frac = 1

            # Calculate replacement fractions for the baseline and efficient
            # stock. * Note: these fractions are both 0 for secondary
            # microsegments
            if mskeys[0] == "primary":
                # Calculate the portions of existing baseline and efficient
                # stock that are up for replacement

                # Update base replacement fraction

                # For a case where the current microsegment applies to new
                # structures, determine whether enough years have passed
                # since the baseline technology was first adopted in new
                # homes in the years before a measure was on mkt. to begin
                # replacing that baseline stock; if so, represent replacement
                # of this new baseline stock
                if mskeys[-1] == "new":
                    # Replacement fraction is only relevant in cases where a
                    # measure enters the market after the beginning of the
                    # modeling time horizon
                    if int(self.handyvars.aeo_years[0]) < int(
                            self.market_entry_year):
                        # Set an indicator for when the previously captured
                        # base stock begins to turnover, using the baseline
                        # lifetime (zero or negative value indicates turnover)
                        turnover_base = int(life_base[yr]) - (
                            int(yr) - int(sorted(self.handyvars.aeo_years)[0]))
                        # If the previously captured baseline stock has
                        # begun to turnover, the replacement rate equals the
                        # ratio of baseline stock captured in a given previous
                        # year over the total stock in the current year
                        if turnover_base <= 0:
                            # Determine the pre-market-entry year in which
                            # the new stock was captured by the baseline
                            pre_mkt_yr = int(yr) - int(life_base[yr])
                            # Ensure that pre-market-entry year is not
                            # earlier than the earliest year in the AEO
                            # range
                            if pre_mkt_yr >= int(
                                    self.handyvars.aeo_years[0]) and \
                                    pre_mkt_yr < self.market_entry_year:
                                # Calculate the ratio of the new stock
                                # captured by the baseline in the pre-
                                # market-entry year to the total new
                                # stock in the current analysis year

                                # Pre-market-entry year is not first
                                # AEO year and non-zero denominator
                                if (str(pre_mkt_yr) !=
                                    self.handyvars.aeo_years[0]) and \
                                        stock_total[yr] != 0:
                                    captured_base_replace_frac = (
                                        stock_total[str(pre_mkt_yr)] -
                                        stock_total[str(pre_mkt_yr - 1)]
                                        ) / stock_total[yr]
                                # Pre-market-entry year is first
                                # AEO year and non-zero denominator
                                elif stock_total[yr] != 0:
                                    captured_base_replace_frac = (
                                        stock_total[str(pre_mkt_yr)] /
                                        stock_total[yr])
                                else:
                                    captured_base_replace_frac = 0
                            else:
                                captured_base_replace_frac = 0
                        # Otherwise, the turnover rate is zero
                        else:
                            captured_base_replace_frac = 0
                    else:
                        captured_base_replace_frac = 0

                # For a case where the current microsegment applies to
                # existing structures, the baseline replacement fraction
                # is the lesser of (1 / baseline lifetime) + retrofit rate
                # and the fraction of existing stock from previous years that
                # has already been captured by the baseline technology
                else:
                    # Set maximum annual baseline replacement rate
                    base_repl_rt_max = (1 / life_base[yr]) + self.retro_rate
                    # Handle case without lifetime or retro. rate distributions
                    if type(base_repl_rt_max) != numpy.ndarray:
                        captured_base_replace_frac = base_repl_rt_max
                    # Handle case with lifetime or retro. rate distributions
                    else:
                        # Ensure that all variables involved in the
                        # calculation are set to lists with the same length
                        # (and that list elements are of the float type)
                        base_repl_rt_max, captured_base_frac, \
                            captured_eff_frac = [numpy.repeat(
                                float(x), self.handyvars.nsamples) if type(x)
                                in (int, float) else x for x in [
                                base_repl_rt_max, captured_base_frac,
                                captured_eff_frac]]
                        # Initialize the final base replacement fraction output
                        # as a list of zeros with the appropriate length
                        captured_base_replace_frac = numpy.zeros(
                            self.handyvars.nsamples)
                        # Using a for loop, complete the set of operations
                        # used above (under 'try') for each list element
                        for ind in range(self.handyvars.nsamples):
                            captured_base_replace_frac[ind] = \
                                base_repl_rt_max[ind]

            else:
                captured_base_replace_frac = (0 for n in range(2))

            # Determine the fraction of total stock, energy, and carbon
            # in a given year that the measure will compete for given the
            # microsegment type and technology adoption scenario

            # Secondary microsegment (competed fraction tied to the associated
            # primary microsegment)
            if int(yr) >= self.market_entry_year and \
                    int(yr) < self.market_exit_year:
                if mskeys[0] == "secondary" and secnd_mseg_adjkey is not None \
                    and secnd_adj_stk["original energy (total)"][
                        secnd_mseg_adjkey][yr] != 0:
                    competed_frac = secnd_adj_stk[
                        "adjusted energy (competed)"][
                        secnd_mseg_adjkey][yr] / secnd_adj_stk[
                        "original energy (total)"][secnd_mseg_adjkey][yr]
                # Primary microsegment in the first year of a technical
                # potential scenario (all stock competed)
                elif mskeys[0] == "primary" and \
                        adopt_scheme == "Technical potential":
                    competed_frac = 1
                # Primary microsegment not in the first year where current
                # microsegment applies to new structure type
                elif mskeys[0] == "primary" and mskeys[-1] == "new":
                    # Calculate the newly added portion of the total new
                    # stock (where 'new' is all stock added since year one of
                    # the modeling time horizon)

                    # After the first year in the modeling time horizon,
                    # the newly added stock fraction is the difference in
                    # stock between the current and previous year divided
                    # by the current year's stock (assuming it is not zero)
                    if yr != self.handyvars.aeo_years[0] and \
                            stock_total[yr] != 0:
                        # Handle case where data for previous year are
                        # unavailable; set newly added fraction to 1
                        try:
                            new_stock_add_frac = (
                                stock_total[yr] - stock_total[
                                    str(int(yr) - 1)]) / stock_total[yr]
                        except KeyError:
                            new_stock_add_frac = 1
                    # For the first year in the modeling time horizon, the
                    # newly added stock fraction is 1
                    elif yr == self.handyvars.aeo_years[0]:
                        new_stock_add_frac = 1
                    # If the total new stock in the current year is zero,
                    # the newly added stock fraction is also zero
                    else:
                        new_stock_add_frac = 0

                    # The total competed stock fraction is the sum of the
                    # newly added stock fraction and the portion of the
                    # total stock that was previously captured by the baseline
                    # technology and is up for replacement or retrofit
                    competed_frac = new_stock_add_frac + \
                        captured_base_replace_frac

                # Primary microsegment not in the first year where current
                # microsegment applies to existing structure type
                elif mskeys[0] == "primary" and mskeys[-1] == "existing":

                    # Ensure that replacement fraction does not exceed 1

                    # Handle case without lifetime or retro. rate distributions
                    try:
                        if captured_base_replace_frac <= 1:
                            competed_frac = captured_base_replace_frac
                        else:
                            competed_frac = 1
                    # Handle case with lifetime or retro. rate distributions
                    except ValueError:
                        if all(captured_base_replace_frac <= 1):
                            competed_frac = captured_base_replace_frac
                        else:
                            captured_base_replace_frac[
                                numpy.where(
                                    captured_base_replace_frac > 1)] = 1
                            competed_frac = captured_base_replace_frac

                else:
                    competed_frac = 0
            # For all other cases, set competed fraction to 0
            else:
                competed_frac = 0

            # Determine the fraction of total stock, energy, and carbon
            # in a given year that is competed and captured by the measure

            # Secondary microsegment (competed and captured fraction tied
            # to the associated primary microsegment)
            if mskeys[0] == "secondary" and secnd_adj_stk[
                    "original energy (total)"][secnd_mseg_adjkey][yr] != 0:
                competed_captured_eff_frac = secnd_adj_stk[
                    "adjusted energy (competed and captured)"][
                    secnd_mseg_adjkey][yr] / secnd_adj_stk[
                    "original energy (total)"][secnd_mseg_adjkey][yr]
            # Primary microsegment and year when measure is on the market
            else:
                competed_captured_eff_frac = competed_frac * diffuse_eff_frac

            # In the case of a primary microsegment with secondary effects,
            # update the information needed to scale down the secondary
            # microsegment(s) by a sub-market fraction and previously captured,
            # competed, and competed and captured stock fractions for the
            # primary microsegment
            if mskeys[0] == "primary" and mskeys[4] == "lighting" and \
                    secnd_mseg_adjkey is not None:
                # Sub-market stock
                secnd_adj_sbmkt["adjusted energy (sub-market)"][
                    secnd_mseg_adjkey][yr] += energy_total_sbmkt[yr]
                # Total stock
                secnd_adj_stk[
                    "original energy (total)"][secnd_mseg_adjkey][yr] += \
                    energy_total_sbmkt[yr]
                # Previously captured stock
                secnd_adj_stk["adjusted energy (previously captured)"][
                    secnd_mseg_adjkey][yr] += \
                    captured_eff_frac * energy_total_sbmkt[yr]
                # Competed stock
                secnd_adj_stk["adjusted energy (competed)"][
                    secnd_mseg_adjkey][yr] += competed_frac * \
                    energy_total_sbmkt[yr]
                # Competed and captured stock
                secnd_adj_stk["adjusted energy (competed and captured)"][
                    secnd_mseg_adjkey][yr] += \
                    competed_captured_eff_frac * energy_total_sbmkt[yr]

            # Update competed stock, energy, and carbon
            stock_compete[yr] = stock_total[yr] * competed_frac
            energy_compete_sbmkt[yr] = energy_total_sbmkt[yr] * competed_frac
            energy_compete[yr] = energy_total[yr] * competed_frac
            carb_compete_sbmkt[yr] = carb_total_sbmkt[yr] * competed_frac
            carb_compete[yr] = carb_total[yr] * competed_frac

            # Determine the competed stock that is captured by the measure
            stock_compete_meas[yr] = stock_total[yr] * \
                competed_captured_eff_frac

            # Determine the amount of existing stock that has already
            # been captured by the measure up until the current year;
            # subsequently, update the number of total and competed stock units
            # captured by the measure to reflect additions from the current
            # year

            # First year in the modeling time horizon
            if yr == self.handyvars.aeo_years[0]:
                stock_total_meas[yr] = stock_compete_meas[yr]
            # Subsequent year in modeling time horizon
            else:
                # Technical potential case where the measure is on the
                # market: the stock captured by the measure should equal the
                # total stock (measure captures all stock)
                if adopt_scheme == "Technical potential" and (
                    int(yr) >= self.market_entry_year) and (
                        int(yr) < self.market_exit_year):
                    stock_total_meas[yr] = stock_total[yr]
                # All other cases
                else:
                    # For microsegments applying to existing stock, calculate
                    # a fraction for mapping the portion of captured stock as
                    # of the previous year to the stock total for the current
                    # year, such that the captured portion remains consistent

                    # Handle case where data for previous year are
                    # unavailable; set total captured stock to current year's
                    # competed/captured stock
                    try:
                        if "existing" in mskeys and \
                            yr != self.handyvars.aeo_years[0] and \
                                (stock_total[str(int(yr) - 1)]) != 0:
                            stock_adj_frac = stock_total[yr] / \
                                stock_total[str(int(yr) - 1)]
                        else:
                            stock_adj_frac = 1
                        # Update total number of stock units captured by the
                        # measure (reflects all previously captured stock +
                        # captured competed stock from the current year). Note
                        # that previously captured stock that is now competed
                        # must be subtracted from the previously captured stock
                        stock_total_meas[yr] = (stock_total_meas[
                            str(int(yr) - 1)]) * stock_adj_frac + \
                            stock_compete_meas[yr]
                    except KeyError:
                        stock_total_meas[yr] = \
                            copy.deepcopy(stock_compete_meas[yr])
                    # Ensure captured stock never exceeds total stock

                    # Handle case where stock captured by measure is an array
                    if type(stock_total_meas[yr]) == numpy.ndarray and \
                       any(stock_total_meas[yr] > stock_total[yr]) \
                            is True:
                        stock_total_meas[yr][
                            numpy.where(
                                stock_total_meas[yr] > stock_total[yr])] = \
                            stock_total[yr]
                    # Handle case where stock captured by measure is point val
                    elif type(stock_total_meas[yr]) != numpy.ndarray and \
                            stock_total_meas[yr] > stock_total[yr]:
                        stock_total_meas[yr] = stock_total[yr]

            # Update the relative performance and time-sensitive efficiency
            # scaling factors of the current year's captured stock. Set to the
            # relative performance/scaling factors of the current year only
            # for all years through market entry; after market entry, these
            # values are weighted combinations of the relative performance/
            # scaling factor values for captured stock in both the current year
            # and all previous years since market entry
            if int(yr) <= self.market_entry_year:
                # Update relative performance
                rel_perf_capt = rel_perf[yr]
            else:
                # Set a turnover weight to use in balancing the current year's
                # relative performance with that of all previous years since
                # market entry
                base_turnover_wt = (1 / life_base[yr]) + self.retro_rate

                # Ensure the turnover weight never exceeds 1

                # Handle case without lifetime or retro. rate distributions
                try:
                    if base_turnover_wt > 1:
                        base_turnover_wt = 1
                # Handle case with lifetime or retro. rate distributions
                except ValueError:
                    base_turnover_wt[numpy.where(base_turnover_wt > 1)] = 1

                # Update relative performance
                rel_perf_capt = (
                    rel_perf[yr] * base_turnover_wt +
                    rel_perf_capt * (1 - base_turnover_wt))

            # Update total-efficient and competed-efficient energy and
            # carbon, where "efficient" signifies the total and competed
            # energy/carbon remaining after measure implementation plus
            # non-competed energy/carbon. * Note: Efficient energy and
            # carbon is dependent upon whether the measure is on the market
            # for the given year (if not, use baseline energy and carbon)

            # Set common variables for the efficient energy calculations

            # Competed energy captured by measure
            energy_tot_comp_meas = energy_total_sbmkt[yr] * \
                competed_captured_eff_frac * rel_perf_capt * (
                    site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                tsv_energy_eff
            # Competed energy remaining with baseline
            energy_tot_comp_base = energy_total_sbmkt[yr] * (
                    competed_frac - competed_captured_eff_frac) * \
                rel_perf_uncapt * tsv_energy_base
            # Uncompeted energy captured by measure
            energy_tot_uncomp_meas = (
                energy_total_sbmkt[yr] - energy_compete_sbmkt[yr]) * \
                captured_eff_frac * rel_perf_capt * (
                    site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                tsv_energy_eff
            # Uncompeted energy remaining with baseline
            energy_tot_uncomp_base = (
                energy_total_sbmkt[yr] - energy_compete_sbmkt[yr]) * \
                (1 - captured_eff_frac) * rel_perf_uncapt * tsv_energy_base

            # Competed-efficient energy
            energy_compete_eff[yr] = energy_tot_comp_meas + \
                energy_tot_comp_base
            # Total-efficient energy
            energy_total_eff[yr] = energy_compete_eff[yr] + \
                energy_tot_uncomp_meas + energy_tot_uncomp_base

            # Re-apportion total efficient microsegment energy across all 8760
            # hours of the year, if necessary (supports sector-level savings
            # shapes)
            if opts.sect_shapes is True and \
                yr in self.handyvars.aeo_years_summary and \
                    tsv_shapes is not None:
                self.sector_shapes[adopt_scheme][mskeys[1]][yr][
                    "efficient"] = [
                    self.sector_shapes[adopt_scheme][
                        mskeys[1]][yr]["efficient"][x] + (
                        energy_tot_comp_meas * tsv_shapes["efficient"][x] +
                        energy_tot_comp_base * tsv_shapes["baseline"][x] +
                        energy_tot_uncomp_meas * tsv_shapes["efficient"][x] +
                        energy_tot_uncomp_base * tsv_shapes["baseline"][x])
                    for x in range(8760)]
                # If current measure is part of an active package, add sector-
                # level information for the current efficient mseg to the
                # attribute that is later used to feed these data into the pkg.
                if str(contrib_mseg_key) in \
                        self.sector_shapes_pkg[adopt_scheme].keys():
                    self.sector_shapes_pkg[adopt_scheme][
                        str(contrib_mseg_key)][yr]["efficient"] = [(
                            energy_tot_comp_meas * tsv_shapes["efficient"][x] +
                            energy_tot_comp_base * tsv_shapes["baseline"][x] +
                            energy_tot_uncomp_meas *
                            tsv_shapes["efficient"][x] +
                            energy_tot_uncomp_base *
                            tsv_shapes["baseline"][x]) for x in range(8760)]
            # Anticipate and handle case with base carbon intensity of zero for
            # electricity; in this case, assume the measure and baseline
            # intensity is the same (zero intensity is only possible for
            # electricity; assume measures will not be switched away from
            # electricity)
            try:
                intensity_carb_ratio = (
                    intensity_carb_meas[yr] / intensity_carb_base[yr])
            except ZeroDivisionError:
                intensity_carb_ratio = 1

            # Set common variables for the carbon calculations

            # Competed carbon captured by measure
            carb_tot_comp_meas = carb_total_sbmkt[yr] * \
                competed_captured_eff_frac * rel_perf_capt * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                intensity_carb_ratio * tsv_carb_eff
            # Competed carbon remaining with baseline
            carb_tot_comp_base = carb_total_sbmkt[yr] * (
                    competed_frac - competed_captured_eff_frac) * \
                rel_perf_uncapt * tsv_carb_base
            # Uncompeted carbon captured by measure
            carb_tot_uncomp_meas = (
                carb_total_sbmkt[yr] - carb_compete_sbmkt[yr]) * \
                captured_eff_frac * rel_perf_capt * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                intensity_carb_ratio * tsv_carb_eff
            # Uncompeted carbon remaining with baseline
            carb_tot_uncomp_base = (
                carb_total_sbmkt[yr] - carb_compete_sbmkt[yr]) * (
                1 - captured_eff_frac) * rel_perf_uncapt * tsv_carb_base

            # Competed-efficient carbon
            carb_compete_eff[yr] = carb_tot_comp_meas + \
                carb_tot_comp_base
            # Total-efficient energy
            carb_total_eff[yr] = carb_compete_eff[yr] + \
                carb_tot_uncomp_meas + carb_tot_uncomp_base

            # Update total and competed stock, energy, and carbon
            # costs. * Note: total-efficient and competed-efficient stock
            # cost for the measure are dependent upon whether that measure is
            # on the market for the given year (if not, use baseline technology
            # cost)

            # Baseline cost of the competed stock
            stock_compete_cost[yr] = stock_compete[yr] * cost_base[yr]
            # Baseline cost of the total stock
            stock_total_cost[yr] = stock_total[yr] * cost_base[yr]
            # Total and competed-efficient stock cost for add-on and
            # full service measures. * Note: the baseline technology installed
            # cost must be added to the measure installed cost in the case of
            # an add-on measure type
            if self.measure_type == "add-on":
                # Competed-efficient stock cost (add-on measure)
                stock_compete_cost_eff[yr] = \
                    stock_compete_meas[yr] * (
                        cost_meas[yr] + cost_base[yr]) + (
                        stock_compete[yr] - stock_compete_meas[yr]) * \
                    cost_base[yr]
                # Total-efficient stock cost (add-on measure)
                stock_total_cost_eff[yr] = stock_total_meas[yr] * (
                    cost_meas[yr] + cost_base[yr]) + (
                    stock_total[yr] - stock_total_meas[yr]) * cost_base[yr]
            else:
                # Competed-efficient stock cost (full service measure)
                stock_compete_cost_eff[yr] = \
                    stock_compete_meas[yr] * cost_meas[yr] + (
                        stock_compete[yr] - stock_compete_meas[yr]) * \
                    cost_base[yr]
                # Total-efficient stock cost (full service measure)
                stock_total_cost_eff[yr] = \
                    stock_total_meas[yr] * cost_meas[yr] \
                    + (stock_total[yr] - stock_total_meas[yr]) * cost_base[yr]
            # Competed baseline energy cost
            energy_compete_cost[yr] = energy_compete_sbmkt[yr] * \
                cost_energy_base[yr] * tsv_ecost_base
            # Total baseline energy cost
            energy_total_cost[yr] = energy_total_sbmkt[yr] * \
                cost_energy_base[yr] * tsv_ecost_base

            # Set common variables for the energy cost calculations

            # Competed energy cost captured by measure
            energy_cost_tot_comp_meas = energy_total_sbmkt[yr] * \
                competed_captured_eff_frac * rel_perf_capt * (
                    site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                cost_energy_meas[yr] * tsv_ecost_eff
            # Competed energy cost remaining with baseline
            energy_cost_tot_comp_base = energy_total_sbmkt[yr] * (
                    competed_frac - competed_captured_eff_frac) * \
                rel_perf_uncapt * cost_energy_base[yr] * tsv_ecost_base
            # Total energy cost captured by measure
            energy_cost_tot_uncomp_meas = (
                energy_total_sbmkt[yr] - energy_compete_sbmkt[yr]) * \
                captured_eff_frac * rel_perf_capt * (
                    site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                cost_energy_meas[yr] * tsv_ecost_eff
            # Total energy cost remaining with baseline
            energy_cost_tot_uncomp_base = (
                energy_total_sbmkt[yr] - energy_compete_sbmkt[yr]) * \
                (1 - captured_eff_frac) * rel_perf_uncapt * \
                cost_energy_base[yr] * tsv_ecost_base

            # Competed-efficient energy cost
            energy_compete_cost_eff[yr] = energy_cost_tot_comp_meas + \
                energy_cost_tot_comp_base
            # Total-efficient energy cost
            energy_total_eff_cost[yr] = energy_compete_cost_eff[yr] + \
                energy_cost_tot_uncomp_meas + energy_cost_tot_uncomp_base

            # Competed baseline carbon cost
            carb_compete_cost[yr] = carb_compete[yr] * \
                self.handyvars.ccosts[yr]
            # Competed carbon-efficient cost
            carb_compete_cost_eff[yr] = \
                carb_compete_eff[yr] * self.handyvars.ccosts[yr]
            # Total baseline carbon cost
            carb_total_cost[yr] = carb_total[yr] * self.handyvars.ccosts[yr]
            # Total carbon-efficient cost
            carb_total_eff_cost[yr] = \
                carb_total_eff[yr] * self.handyvars.ccosts[yr]

            # For fuel switching measures only, record the portion of total
            # baseline energy, carbon, and energy cost that remains with the
            # baseline fuel in the given year
            if self.fuel_switch_to is not None:
                fs_energy_eff_remain[yr] = \
                    energy_tot_comp_base + energy_tot_uncomp_base
                fs_carb_eff_remain[yr] = \
                    carb_tot_comp_base + carb_tot_uncomp_base
                fs_energy_cost_eff_remain[yr] = \
                    energy_cost_tot_comp_base + energy_cost_tot_uncomp_base

            # For primary microsegments only, update portion of stock captured
            # by efficient measure in previous years to reflect gains from the
            # current modeling year. If this portion is already 1 or the total
            # stock for the year is 0, do not update the captured portion from
            # the previous year
            if mskeys[0] == "primary":
                # Handle case where captured efficient stock total/fraction
                # is a point value
                try:
                    if stock_total[yr] != 0 and captured_eff_frac != 1:
                        captured_eff_frac = \
                            stock_total_meas[yr] / stock_total[yr]
                # Handle case where captured efficient stock total/fraction
                # is a numpy array
                except ValueError:
                    try:
                        for i in range(0, self.handyvars.nsamples):
                            if stock_total[yr] != 0 and \
                                    captured_eff_frac[i] != 1:
                                captured_eff_frac[i] = \
                                    (stock_total_meas[yr][i] / stock_total[yr])
                    except TypeError:
                        # Handle case where captured efficient stock is forced
                        # to total stock point value (Technical potential)
                        if stock_total_meas[yr] == stock_total[yr]:
                            captured_eff_frac = 1

                # Update portion of existing stock remaining with the baseline
                # technology
                captured_base_frac = 1 - captured_eff_frac

        # Return partitioned stock, energy, and cost mseg information
        return [stock_total, energy_total, carb_total,
                stock_total_meas, energy_total_eff, carb_total_eff,
                stock_compete, energy_compete,
                carb_compete, stock_compete_meas, energy_compete_eff,
                carb_compete_eff, stock_total_cost, energy_total_cost,
                carb_total_cost, stock_total_cost_eff, energy_total_eff_cost,
                carb_total_eff_cost, stock_compete_cost, energy_compete_cost,
                carb_compete_cost, stock_compete_cost_eff,
                energy_compete_cost_eff, carb_compete_cost_eff,
                fs_energy_eff_remain, fs_carb_eff_remain,
                fs_energy_cost_eff_remain]

    def check_mkt_inputs(self):
        """Check for valid applicable baseline market inputs for a measure.

        Note:
            The inputs are checked against a list of valid baseline market
            input names, determined from the 'valid_mktnames' attribute of the
            'UsefulVars' object type.

        Raises:
            ValueError: If 'technology_type' attribute is improperly formatted
                or input names are not in the list of valid names.
        """
        # Initialize the list of input names to check
        check_list = []
        # Loop through all inputs related to a measure's applicable baseline
        # market and add input names to the list
        for x in [
            self.climate_zone, self.bldg_type, self.structure_type,
            self.fuel_type, self.end_use, self.technology_type,
                self.technology]:
            # Handle input values formatted as dicts, lists, or strings
            if isinstance(x, dict):
                [check_list.extend(x[ms]) if isinstance(x[ms], list) else
                 check_list.append(x[ms]) for ms in ["primary", "secondary"]]
            elif isinstance(x, list):
                check_list.extend(x)
            elif isinstance(x, str) or x is None:
                check_list.append(x)
            else:
                raise ValueError(
                    "ECM '" + self.name + "'applicable baseline market "
                    "input in unexpected format (need dict, list, or string)")
        # Find subset of input names that are not in the list of valid names
        invalid_names = [
            y for y in check_list if y not in self.handyvars.valid_mktnames]
        # If invalid names are discovered, report them in an error message
        if len(invalid_names) > 0:
            raise ValueError(
                "Input names in the following list are invalid for ECM '" +
                self.name + "': " + str(invalid_names))

    def fill_attr(self):
        """Fill out missing ECM attribute data.

        Note:
            Handles the following:
            a) Adds a 'windows conduction' technology market when only
            'windows solar' is defined for the ECM, and vice versa (assuming
            that both pertain to the same window unit).
            b) Splits the 'energy_efficiency', 'energy_efficiency_units',
            'energy_fuel_type', 'end_use', 'technology', and 'technology_type'
            attributes into 'primary' and 'secondary' keys, ensuring that
            secondary end use impacts are properly processed by the remainder
            of the 'fill_mkts' routine. Note: if the user has not specified
            any secondary end use impacts, secondary key values for all
            relevant attributes are set to None.
            c) Fills out any attributes marked 'all'. For example, if a user
            has specified 'all' for the 'climate_zone' measure attribute, this
            function will translate that entry into the full list of climate
            zones: ['AIA_CZ1', 'AIA_CZ2', 'AIA_CZ3', 'AIA_CZ4', 'AIA_CZ5'].
        """
        # Ensure that 'windows conduction' and 'windows solar' markets are
        # always defined together in the technology attribute
        if not isinstance(self.technology, list) and \
                self.technology is not None and "windows" in self.technology:
            self.technology = ["windows conduction", "windows solar"]
        elif isinstance(self.technology, list) and any([
                x is not None and "windows" in x for x in self.technology]):
            self.technology.extend(
                list(set(["windows conduction", "windows solar"]) -
                     set(self.technology)))

        # Split attributes relevant to representing secondary end use impacts
        # into 'primary' and 'secondary' keys

        # Case where user has flagged secondary end use impacts for the measure
        # via the 'end_use' attribute; fill in secondary 'fuel_type',
        # 'technology', and 'technology_type' information. Note: it is assumed
        # the user has already filled in secondary performance information via
        # the 'energy_efficiency' and 'energy_efficiency_units' attributes
        if isinstance(self.end_use, dict):
            # Assume secondary effects pertain to all fuel types and
            # technologies associated with the given secondary end use(s)
            self.fuel_type, self.technology = [{
                "primary": x, "secondary": "all"} for
                x in [self.fuel_type, self.technology]]
            # Assume secondary heating/cooling effects pertain to demand-side
            # heating/cooling technologies (e.g., secondary 'technology_type'
            # is set to 'demand')
            if (isinstance(self.end_use["secondary"], list) and any([
                x not in ["heating", "secondary heating", "cooling"] for
                x in self.end_use["secondary"]])) or (
                not isinstance(self.end_use["secondary"], list) and
                self.end_use["secondary"] not in [
                    "heating", "secondary heating", "cooling"]):
                self.technology_type = {
                    "primary": self.technology_type, "secondary": "supply"}
            else:
                self.technology_type = {
                    "primary": self.technology_type, "secondary": "demand"}
        # Case where the user has not flagged any secondary end use impacts;
        # set 'secondary' key values for relevant attributes to None
        else:
            self.energy_efficiency, self.energy_efficiency_units, \
                self.fuel_type, self.end_use, self.technology, \
                self.technology_type = [
                    {"primary": x, "secondary": None} for x in [
                        self.energy_efficiency, self.energy_efficiency_units,
                        self.fuel_type, self.end_use, self.technology,
                        self.technology_type]]

        # Fill out an 'all' climate zone input
        if self.climate_zone == 'all' or 'all' in self.climate_zone:
            self.climate_zone = self.handyvars.in_all_map["climate_zone"]

        # Fill out an 'all' structure type input
        if self.structure_type == 'all' or 'all' in self.structure_type:
            self.structure_type = self.handyvars.in_all_map["structure_type"]

        # Fill out an 'all' building type, fuel type, end use, and/or
        # technology input. Note that these attributes are affected by whether
        # or not the user has flagged secondary end use impacts
        for mseg_type in [
                x[0] for x in self.end_use.items() if x[1] is not None]:
            # Fill out a building type input that is marked 'all',
            # 'all residential' or 'all commercial', or is formatted as a list
            # with certain elements containing 'all' (e.g.,
            # ['all residential,' 'assembly', 'education'])
            if self.bldg_type == "all" or (
                "all" in self.bldg_type and
                self.bldg_type != "small office") or (
                type(self.bldg_type) == list and any([
                    "all" in b for b in self.bldg_type if
                    b != "small office"])):
                # Record the initial 'bldg_type' attribute the user has defined
                # for the measure before this attribute is reset below
                map_bldgtype_orig = self.bldg_type
                # Reset the measure 'bldg_type' attribute as a list that does
                # not contain any elements including 'all' (e.g., if the
                # 'bldg_type' attribute value was initially 'all', 'all
                # residential', or 'all commercial', it would be reset as a
                # blank list; if the 'bldg_type' attribute value was initially
                # ['all residential', 'assembly', 'education'], it would be
                # reset as ['assembly', 'education'])
                if self.bldg_type == 'all' or 'all' in self.bldg_type:
                    self.bldg_type = []
                else:
                    self.bldg_type = [
                        b for b in self.bldg_type if (
                            'all' not in b or b == 'small office')]
                # Fill 'bldg_type' attribute. Note that the comprehension below
                # handles 'all', 'all residential', or 'all commercial' values
                # for the initial user-defined 'bldg_type' attribute as well as
                # a list value for this attribute that contains elements with
                # 'all'(e.g., ['all residential,' 'assembly', 'education'])
                [self.bldg_type.extend(b[1]) for b in
                    self.handyvars.in_all_map["bldg_type"].items() if
                    b[1] not in self.bldg_type and (
                        map_bldgtype_orig == "all" or b[0] in
                        map_bldgtype_orig or
                        any([b[0] in borig for borig in map_bldgtype_orig if
                            'all ' in borig]))]
                # Record the measure's applicability to the residential and/or
                # the commercial building sectors in a list (for use in filling
                # 'fuel_type,' 'end_use,' and 'technology' attributes below)
                bldgsect_list = [x[0] for x in self.handyvars.in_all_map[
                    "bldg_type"].items() if any([
                        bt in x[1] for bt in self.bldg_type])]

                # For an 'all' building type case, measure 'installed_cost,'
                # 'cost_units,' 'energy_efficiency,' 'energy_efficiency_units,'
                # and/or 'product_lifetime' attributes may be formatted as
                # dictionaries broken out by building sector (e.g., with
                # 'all residential' and/or 'all commercial' keys). This part of
                # the code replaces such keys and their associated values with
                # the appropriate set of building types. For example a
                # ('all commercial', 1) key, value pair would be replaced with
                # [('assembly', 1), ('education', 1), ...]
                for attr in [self.installed_cost, self.cost_units,
                             self.energy_efficiency[mseg_type],
                             self.energy_efficiency_units[mseg_type],
                             self.product_lifetime]:
                    # Check whether attribute is a dict before moving further
                    if isinstance(attr, dict):
                        # Loop through each building sector and the building
                        # type names in that sector. If the sector has been
                        # assigned an 'all' breakout for the current attribute,
                        # add new key, value pairs to the attribute dict where
                        # the building type name is each key and the original
                        # value for the building sector is the value for the
                        # new pair
                        for b in bldgsect_list:
                            # Check whether the sector is assigned an 'all'
                            # breakout in the attribute (e.g., 'all
                            # residential')
                            sect_val = [
                                x[1] for x in attr.items() if b in x[0]]
                            # If sector is assigned 'all' breakout, add
                            # appropriate building type keys and values to
                            # attribute dict
                            if sect_val:
                                for kn in self.handyvars.in_all_map[
                                        "bldg_type"][b]:
                                    attr[kn] = sect_val[0]
                        # Remove the original 'all residential' and
                        # 'all commercial' branches from the attribute dict
                        del_keys = [x for x in attr.keys() if x in [
                                    'all residential', 'all commercial']]
                        for dk in del_keys:
                            del(attr[dk])
            # If there is no 'all' building type input, still record the
            # measure's applicability to the residential and/or
            # the commercial building sector in a list (for use in filling out
            # 'fuel_type,' 'end_use,' and 'technology' attributes below)
            else:
                bldgsect_list = [b[0] for b in self.handyvars.in_all_map[
                    "bldg_type"].items() if any([
                        bta == self.bldg_type for bta in b[1]]) or
                    any([bta in b[1] for bta in self.bldg_type])]

            # Fill out an 'all' fuel type input
            if self.fuel_type[mseg_type] == 'all' or \
                    'all' in self.fuel_type[mseg_type]:
                # Reset measure 'fuel_type' attribute as a list and fill with
                # all fuels for the measure's applicable building sector(s)
                self.fuel_type[mseg_type] = []
                for b in bldgsect_list:
                    [self.fuel_type[mseg_type].append(f) for f in
                     self.handyvars.in_all_map["fuel_type"][b] if
                     f not in self.fuel_type[mseg_type]]

            # Record the measure's applicable fuel type(s) in a list (for use
            # in filling out 'end_use,' and 'technology' attributes below)
            if not isinstance(self.fuel_type[mseg_type], list):
                fueltype_list = [self.fuel_type[mseg_type]]
            else:
                fueltype_list = self.fuel_type[mseg_type]

            # Fill out an 'all' end use input
            if self.end_use[mseg_type] == 'all' or \
                    'all' in self.end_use[mseg_type]:
                # Reset measure 'end_use' attribute as a list and fill with
                # all end uses for the measure's applicable building sector(s)
                # and fuel type(s)
                self.end_use[mseg_type] = []
                for b in bldgsect_list:
                    for f in [x for x in fueltype_list if
                              x in self.handyvars.in_all_map["fuel_type"][b]]:
                        [self.end_use[mseg_type].append(e) for e in
                         self.handyvars.in_all_map["end_use"][b][f] if
                         e not in self.end_use[mseg_type]]

            # Record the measure's applicable end use(s) in a list (for use in
            # filling out 'technology' attribute below)
            if not isinstance(self.end_use[mseg_type], list):
                enduse_list = [self.end_use[mseg_type]]
            else:
                enduse_list = self.end_use[mseg_type]

            # Fill out a technology input that is marked 'all' or is
            # formatted as a list with certain elements containing 'all' (e.g.,
            # ['all heating,' 'central AC', 'room AC'])
            if self.technology[mseg_type] == 'all' or \
                self.technology[mseg_type] == ['all'] or \
                (type(self.technology[mseg_type]) == list and any([
                 t is not None and 'all ' in t for t in
                 self.technology[mseg_type]])) or (
                    type(self.technology[mseg_type]) == str and
                    self.technology[mseg_type] is not None and
                    'all ' in self.technology[mseg_type]):
                # Record the initial 'technology' attribute the user has
                # defined for the measure before this attribute is reset below
                map_tech_orig = self.technology[mseg_type]
                # Reset the measure 'technology' attribute as a list that does
                # not contain any elements including 'all' (e.g., if the
                # 'technology' attribute value was initially 'all', it would be
                # reset as a blank list; if the 'technology' attribute value
                # was initially ['all heating', 'central AC', 'room AC'], it
                # would be reset as ['central AC', 'room AC'])
                if self.technology[mseg_type] == 'all':
                    self.technology[mseg_type] = []
                elif isinstance(self.technology[mseg_type], list):
                    self.technology[mseg_type] = [
                        t for t in self.technology[mseg_type] if
                        ('all ' not in t and t != 'all')]
                else:
                    self.technology[mseg_type] = [self.technology[mseg_type]]

                # Fill 'technology' attribute
                for b in bldgsect_list:
                    # Case concerning a demand-side technology, for which the
                    # set of 'all' technologies depends only on the measure's
                    # applicable building sector(s)
                    if self.technology_type[mseg_type] == "demand":
                        [self.technology[mseg_type].append(t) for t in
                            self.handyvars.in_all_map["technology"][b][
                            self.technology_type[mseg_type]] if t not in
                            self.technology[mseg_type]]
                    # Case concerning a supply-side technology, for which the
                    # set of 'all' technologies depends on the measure's
                    # applicable building sector(s), fuel type(s), and
                    # end use(s)
                    else:
                        for f in [ft for ft in fueltype_list if
                                  ft in self.handyvars.in_all_map[
                                "fuel_type"][b]]:
                            for e in [eu for eu in enduse_list if eu in
                                      self.handyvars.in_all_map[
                                    "end_use"][b][f]]:
                                # Note that the comprehension below handles
                                # both an 'all' value for the initial
                                # user-defined 'technology' attribute and a
                                # list value for this attribute that contains
                                # elements with 'all' (e.g., ['all heating',
                                # 'central AC', 'room AC'])
                                [self.technology[mseg_type].append(t) for
                                 t in self.handyvars.in_all_map["technology"][
                                 b][self.technology_type[mseg_type]][f][e] if
                                 t not in self.technology[mseg_type] and
                                 (map_tech_orig == "all" or
                                  map_tech_orig == ["all"] or any([
                                     e in torig for torig in map_tech_orig if
                                     'all ' in torig])) or e in map_tech_orig]

    def create_keychain(self, mseg_type):
        """Create list of dictionary keys used to find baseline microsegments.

        Args:
            mseg_type (string): Identifies the type of baseline microsegments
                to generate keys for ('primary' or 'secondary').

        Returns:
            List of key chains to use in retreiving data for the measure's
            applicable baseline market microsegments.
        """
        # Ensure that all variables relevant to forming key chains are lists
        self.climate_zone, self.bldg_type, self.fuel_type[mseg_type], \
            self.end_use[mseg_type], self.technology_type[mseg_type], \
            self.technology[mseg_type], self.structure_type = [
                [x] if not isinstance(x, list) else x for x in [
                    self.climate_zone, self.bldg_type,
                    self.fuel_type[mseg_type], self.end_use[mseg_type],
                    self.technology_type[mseg_type],
                    self.technology[mseg_type], self.structure_type]]
        # Flag heating/cooling end use microsegments. For heating/cooling
        # cases, an extra 'supply' or 'demand' key is required in the key
        # chain; this key indicates the supply-side and demand-side variants
        # of heating/ cooling technologies (e.g., ASHP for the former,
        # envelope air sealing for the latter).
        ht_cl_euses = ["heating", "secondary heating", "cooling"]

        # Case with heating and/or cooling microsegments
        if any([x in ht_cl_euses for x in self.end_use[mseg_type]]):
            # Format measure end use attribute as numpy array
            eu = numpy.array(self.end_use[mseg_type])
            # Set a list of heating and/or cooling end uses
            eu_hc = list(eu[numpy.where([x in ht_cl_euses for x in eu])])
            # Set a list of all other end uses
            eu_non_hc = list(eu[numpy.where([
                x not in ht_cl_euses for x in eu])])
            # Set a list including all measure microsegment attributes,
            # constraining the 'end_use' attribute to only heating/cooling
            # end uses
            ms_lists = [
                self.climate_zone, self.bldg_type, self.fuel_type[mseg_type],
                eu_hc, self.technology_type[mseg_type],
                self.technology[mseg_type]]
            # Generate a list of all possible combinations of the elements
            # in 'ms_lists' above
            ms_iterable_init = list(itertools.product(*ms_lists))
            # If there are also non-heating/cooling microsegments, set
            # a list including all measure microsegment attributes,
            # constraining the 'end_use' attribute to only non-heating/cooling
            # end uses
            if len(eu_non_hc) > 0:
                ms_lists_add = [self.climate_zone, self.bldg_type,
                                self.fuel_type[mseg_type], eu_non_hc,
                                self.technology[mseg_type]]
                # Generate a list of all possible combinations of the
                # elements in 'ms_lists_add' above and add this list
                # to 'ms_iterable_init', also adding 'ms_lists_add'
                # to 'ms_lists'
                ms_iterable_init.extend(
                    list(itertools.product(*ms_lists_add)))
                ms_lists.extend(ms_lists_add)

        # Case without heating or cooling microsegments
        else:
            # Set a list including all measure microsegment attributes
            ms_lists = [self.climate_zone, self.bldg_type,
                        self.fuel_type[mseg_type], self.end_use[mseg_type],
                        self.technology[mseg_type]]
            # Generate a list of all possible combinations of the elements
            # in 'ms_lists' above
            ms_iterable_init = list(itertools.product(*ms_lists))

        # Add primary or secondary microsegment type indicator to beginning
        # of each key chain and the applicable structure type (new or existing)
        # to the end of each key chain

        # Case where measure applies to both new and existing structures
        # (final ms_iterable list length is double that of ms_iterable_init)
        if len(self.structure_type) > 1:
            ms_iterable1, ms_iterable2 = ([] for n in range(2))
            for i in range(0, len(ms_iterable_init)):
                ms_iterable1.append((mseg_type,) + ms_iterable_init[i] +
                                    (self.structure_type[0], ))
                ms_iterable2.append((mseg_type,) + ms_iterable_init[i] +
                                    (self.structure_type[1], ))
            ms_iterable = ms_iterable1 + ms_iterable2
        # Case where measure applies to only new or existing structures
        # (final ms_iterable list length is same as that of ms_iterable_init)
        else:
            ms_iterable = []
            for i in range(0, len(ms_iterable_init)):
                ms_iterable.append(((mseg_type, ) + ms_iterable_init[i] +
                                    (self.structure_type[0], )))

        # Output list of key chains
        return ms_iterable, ms_lists

    def find_scnd_overlp(self, vint_frac, ss_conv, dict1, energy_tot):
        """Find total lighting energy for climate/building/structure type.

        Note:
            Primary/secondary microsegments are linked by climate zone,
            building type, and structure type (new/existing).

        Args:
            vint_frac (dict): New/existing fraction by year.
            ss_conv (dict): Site/source conversion factors by year.
            dict1 (dict): Dict of lighting stock/energy data for given
            climate zone, building type, and structure type.
            energy_tot (float): Total lighting energy value.

        Returns:
            Total lighting energy for given climate, building, and structure
            type.
        """
        for k, i in dict1.items():
            # Ignore stock data
            if k == "stock":
                continue
            # Proceed further into nested dict if terminal node with stock/
            # energy data has not been reached
            elif isinstance(i, dict) and k != "energy":
                self.find_scnd_overlp(
                    vint_frac, ss_conv, i, energy_tot)
            # If terminal node energy data has been reached, add energy
            # data to the total energy use variable
            elif k == "energy":
                for yr in self.handyvars.aeo_years:
                    energy_tot[yr] += dict1["energy"][yr] * \
                        vint_frac[yr] * ss_conv[yr]
            # Raise error if no energy data are available
            else:
                raise ValueError(
                    'No energy data available for total '
                    'lighting energy use calculation')

        return energy_tot

    def add_keyvals(self, dict1, dict2):
        """Add key values of two dicts together.

        Note:
            Dicts must be identically structured.

        Args:
            dict1 (dict): First dictionary to add.
            dict2 (dict): Second dictionary to add.

        Returns:
            Single dictionary of combined values.

        Raises:
            KeyError: When added dict keys do not match.
        """
        for (k, i), (k2, i2) in zip(
                sorted(dict1.items()), sorted(dict2.items())):
            if k == k2:
                if isinstance(i, dict):
                    self.add_keyvals(i, i2)
                else:
                    if dict1[k] is None:
                        dict1[k] = copy.deepcopy(dict2[k2])
                    else:
                        dict1[k] = dict1[k] + dict2[k]
            else:
                raise KeyError("When adding together two dicts "
                               "for ECM '" + self.name +
                               "' update, dict key structures "
                               "do not match")
        return dict1

    def add_keyvals_restrict(self, dict1, dict2):
        """Add key values of two dicts, with restrictions.

        Note:
            Restrict the addition of 'lifetime' information. This
            function is used to merge baseline microsegments for
            windows conduction and windows solar components; the
            lifetimes for these components will be the same and
            need not be added and averaged later, as is the case
            for summed lifetime information yielded by 'add_keyvals'.
            Dicts must be identically structured.

        Args:
            dict1 (dict): First dictionary to add.
            dict2 (dict): Second dictionary to add.

        Returns:
            Single dictionary of combined values.

        Raises:
            KeyError: When added dict keys do not match.
        """
        for (k, i), (k2, i2) in zip(
                sorted(dict1.items()), sorted(dict2.items())):
            if k == k2 and k == "lifetime":
                continue
            elif k == k2 and k != "lifetime":
                if isinstance(i, dict):
                    self.add_keyvals(i, i2)
                else:
                    if dict1[k] is None:
                        dict1[k] = copy.deepcopy(dict2[k2])
                    else:
                        dict1[k] = dict1[k] + dict2[k]
            else:
                raise KeyError("When adding together two dicts "
                               "for ECM '" + self.name +
                               "' update, dict key structures "
                               "do not match")
        return dict1

    def div_keyvals(self, dict1, dict2):
        """Divide key values of one dict by analogous values of another.

        Note:
            This function is used to generate partitioning fractions
            for key measure results. In that case the function divides a
            measure's climate, building, and end use-specific
            baseline energy use by its total baseline energy use
            (both organized by year). Dicts must be identically structured.

        Args:
            dict1 (dict): Dict with values to divide.
            dict2 (dict): Dict with factors to divide values of first dict by.

        Returns:
            An updated version of the first dict with all original
            values divided by the analogous values in the second dict.
        """
        for (k, i) in dict1.items():
            if isinstance(i, dict):
                self.div_keyvals(i, dict2)
            else:
                # Handle total energy use of zero
                if ((type(dict2[k]) == numpy.ndarray and all(dict2[k]) != 0) or
                        (type(dict2[k]) != numpy.ndarray and dict2[k] != 0)):
                    dict1[k] = dict1[k] / dict2[k]
                else:
                    dict1[k] = 0
        return dict1

    def div_keyvals_float(self, dict1, reduce_num):
        """Divide a dict's key values by a single number.

        Args:
            dict1 (dict): Dictionary with values to divide.
            reduce_num (float): Factor to divide dict values by.

        Returns:
            An updated dict with all original values divided by the
            number.

        """
        for (k, i) in dict1.items():
            if isinstance(i, dict):
                self.div_keyvals_float(i, reduce_num)
            else:
                # Handle zero values
                if ((type(reduce_num) == numpy.ndarray and
                     all(reduce_num) != 0) or (
                        type(reduce_num) != numpy.ndarray and
                        reduce_num != 0)):
                    dict1[k] = dict1[k] / reduce_num
                else:
                    dict1[k] = 0
        return dict1

    def div_keyvals_float_restrict(self, dict1, reduce_num):
        """Divide a dict's key values by a factor, with restrictions.

        Note:
            This function handles the special case where square footage
            is used as microsegment stock and double counted stock/stock
            cost must be factored out. As this special case only concerns
            microsegment stock and stock cost numbers, the function
            does not apply the input factor to microsegment energy,
            carbon, and lifetime information in the dict.

        Args:
            dict1 (dict): Dictionary with values to divide.
            reduce_num (float): Number to divide dict values by.

        Returns:
            An updated dict with all non-restricted original values divided
            by the number.
        """
        for (k, i) in dict1.items():
            # Do not divide any energy, carbon, lifetime, or sub-market
            # scaling information
            if (k == "energy" or k == "carbon" or k == "lifetime" or
                    k == "sub-market scaling"):
                continue
            else:
                if isinstance(i, dict):
                    self.div_keyvals_float_restrict(i, reduce_num)
                else:
                    dict1[k] = dict1[k] / reduce_num
        return dict1

    def adj_pkg_mseg_keyvals(self, cmsegs, base_adj, eff_adj, base_eff_flag):
        """ Adjust contributing microsegments in a package to remove overlaps.

        Args:
            cmsegs (dict): Contributing microsegment data to adjust.
            base_adj (dict): Adjustment factors for baseline mseg values.
            eff_adj (dict): Adjustment factors for efficient mseg values.
            base_eff_flag (boolean): Flag to determine whether current
                adjustment is to a baseline or efficient value.

        Returns:
            Dict of adjusted contributing microsegments for a measure in a
            package that accounts for/removes overlaps with the contributing
            microsegments of other measures in the package.
        """

        # Move down the dict until a non-dict terminal value is encountered
        for (k, i) in cmsegs.items():
            # If a "baseline" or "efficient" key is encountered, flag the
            # adjustment appropriately. Note that these keys will only be
            # encountered for "energy" and "carbon" msegs; other msegs are
            # not broken out by these keys and will yield a flag of None.
            if k in ["baseline", "efficient"]:
                base_eff_flag = k
            if isinstance(i, dict):
                self.adj_pkg_mseg_keyvals(i, base_adj, eff_adj, base_eff_flag)
            else:
                # Set the appropriate overlap adjustment factor based on
                # the flag for baseline/efficient adjustments; if this flag
                # is None, set the adjustment to the baseline value
                if base_eff_flag == "baseline" and k in \
                        self.handyvars.aeo_years:
                    # Handle cases where the baseline adjustment is not
                    # broken out by year
                    try:
                        adj_fact = base_adj[k]
                    except TypeError:
                        adj_fact = base_adj
                elif base_eff_flag == "efficient" and k in \
                        self.handyvars.aeo_years:
                    # Handle cases where the efficient adjustment is not
                    # broken out by year
                    try:
                        adj_fact = eff_adj[k]
                    except TypeError:
                        adj_fact = eff_adj
                else:
                    try:
                        adj_fact = base_adj[k]
                    except TypeError:
                        adj_fact = base_adj
                # Apply the adjustment to the mseg value
                cmsegs[k] = cmsegs[k] * adj_fact

        return cmsegs

    def rand_list_gen(self, distrib_info, nsamples):
        """Generate N samples from a given probability distribution.

        Args:
            distrib_info (list): Distribution type and parameters.
            nsamples (int): Number of samples to draw from distribution.

        Returns:
            Numpy array of samples from the input distribution.

        Raises:
            ValueError: When unsupported probability distribution is present.
        """
        # Generate a list of randomly generated numbers using the
        # distribution name and parameters provided in "distrib_info".
        # Check that the correct number of parameters is specified for
        # each distribution.
        if len(distrib_info) == 3 and distrib_info[0] == "normal":
            rand_list = numpy.random.normal(distrib_info[1],
                                            distrib_info[2], nsamples)
        elif len(distrib_info) == 3 and distrib_info[0] == "lognormal":
            rand_list = numpy.random.lognormal(distrib_info[1],
                                               distrib_info[2], nsamples)
        elif len(distrib_info) == 3 and distrib_info[0] == "uniform":
            rand_list = numpy.random.uniform(distrib_info[1],
                                             distrib_info[2], nsamples)
        elif len(distrib_info) == 3 and distrib_info[0] == "gamma":
            rand_list = numpy.random.gamma(distrib_info[1],
                                           distrib_info[2], nsamples)
        elif len(distrib_info) == 3 and distrib_info[0] == "weibull":
            rand_list = numpy.random.weibull(distrib_info[1], nsamples)
            rand_list = distrib_info[2] * rand_list
        elif len(distrib_info) == 4 and distrib_info[0] == "triangular":
            rand_list = numpy.random.triangular(distrib_info[1],
                                                distrib_info[2],
                                                distrib_info[3], nsamples)
        else:
            raise ValueError(
                "Unsupported input distribution specification for ECM '" +
                self.name + "'")

        return rand_list

    def fill_perf_dict(
            self, perf_dict, eplus_perf_array, vintage_weights,
            base_cols, eplus_bldg_types):
        """Fill an empty dict with updated measure performance information.

        Note:
            Use structured array data drawn from an EnergyPlus output file
            and building type/vintage weighting data to fill a dictionary of
            final measure performance information.

        Args:
            perf_dict (dict): Empty dictionary to fill with EnergyPlus-based
                performance information broken down by climate zone, building
                type/vintage, fuel type, and end use.
            eplus_perf_array (numpy recarray): Structured array of EnergyPlus
                energy savings information for the Measure.
            vintage_weights (dict): Square-footage-derived weighting factors
                for each EnergyPlus building vintage type.
            eplus_bldg_types (dict): Scout-EnergyPlus building type mapping
                data, including weighting factors needed to map multiple
                EnergyPlus building types to a single Scout building type.
                Drawn from EPlusMapDicts object's 'bldgtype' attribute.

        Returns:
            A measure performance dictionary filled with relative energy
            savings values from an EnergyPlus simulation output file.

        Raises:
            KeyError: If an EnergyPlus category name cannot be mapped to the
                input perf_dict keys.
            ValueError: If weights used to map multiple EnergyPlus reference
                building types to a single Scout building type do not sum to 1.
        """
        # Instantiate useful EnergyPlus-Scout mapping dicts
        handydicts = EPlusMapDicts()

        # Set the header of the EnergyPlus input array (used when reducing
        # columns of the array to the specific performance categories being
        # updated below)
        eplus_header = list(eplus_perf_array.dtype.names)

        # Loop through zeroed out measure performance dictionary input and
        # update the values with data from the EnergyPlus input array
        for key, item in perf_dict.items():
            # If current dict item is itself a dict, reduce EnergyPlus array
            # based on the current dict key and proceed further down the dict
            # levels
            if isinstance(item, dict):
                # Microsegment type level (no update to EnergyPlus array
                # required)
                if key in ['primary', 'secondary']:
                    updated_perf_array = eplus_perf_array
                # Climate zone level
                elif key in handydicts.czone.keys():
                    # Reduce EnergyPlus array to only rows with climate zone
                    # currently being updated in the performance dictionary
                    updated_perf_array = eplus_perf_array[numpy.where(
                        eplus_perf_array[
                            'climate_zone'] == handydicts.czone[key])].copy()
                    if len(updated_perf_array) == 0:
                        raise KeyError(
                            "EPlus climate zone name not found for ECM '" +
                            self.name + "'")
                # Building type level
                elif key in handydicts.bldgtype.keys():
                    # Determine relevant EnergyPlus building types for current
                    # Scout building type
                    eplus_bldg_types = handydicts.bldgtype[key]
                    if sum(eplus_bldg_types.values()) != 1:
                        raise ValueError(
                            "EPlus building type weights do not sum to 1 "
                            "for ECM '" + self.name + "'")
                    # Reduce EnergyPlus array to only rows with building type
                    # relevant to current Scout building type
                    updated_perf_array = eplus_perf_array[numpy.in1d(
                        eplus_perf_array['building_type'],
                        list(eplus_bldg_types.keys()))].copy()
                    if len(updated_perf_array) == 0:
                        raise KeyError(
                            "EPlus building type name not found for ECM '" +
                            self.name + "'")
                # Fuel type level
                elif key in handydicts.fuel.keys():
                    # Reduce EnergyPlus array to only columns with fuel type
                    # currently being updated in the performance dictionary,
                    # plus bldg. type/vintage, climate, and measure columns
                    colnames = base_cols + [
                        x for x in eplus_header if handydicts.fuel[key] in x]
                    if len(colnames) == len(base_cols):
                        raise KeyError(
                            "EPlus fuel type name not found for ECM '" +
                            self.name + "'")
                    updated_perf_array = eplus_perf_array[colnames].copy()
                # End use level
                elif key in handydicts.enduse.keys():
                    # Reduce EnergyPlus array to only columns with end use
                    # currently being updated in the performance dictionary,
                    # plus bldg. type/vintage, climate, and measure columns
                    colnames = base_cols + [
                        x for x in eplus_header if x in handydicts.enduse[
                            key]]
                    if len(colnames) == len(base_cols):
                        raise KeyError(
                            "EPlus end use name not found for ECM '" +
                            self.name + "'")
                    updated_perf_array = eplus_perf_array[colnames].copy()
                else:
                    raise KeyError(
                        "Invalid performance dict key for ECM '" +
                        self.name + "'")

                # Given updated EnergyPlus array, proceed further down the
                # dict level hierarchy
                self.fill_perf_dict(
                    item, updated_perf_array, vintage_weights,
                    base_cols, eplus_bldg_types)
            else:
                # Reduce EnergyPlus array to only rows with structure type
                # currently being updated in the performance dictionary
                # ('new' or 'retrofit')
                if key in handydicts.structure_type.keys():
                    # A 'new' structure type will match only one of the
                    # EnergyPlus building vintage names
                    if key == "new":
                        updated_perf_array = eplus_perf_array[numpy.where(
                            eplus_perf_array['template'] ==
                            handydicts.structure_type['new'])].copy()
                    # A 'retrofit' structure type will match multiple
                    # EnergyPlus building vintage names
                    else:
                        updated_perf_array = eplus_perf_array[numpy.in1d(
                            eplus_perf_array['template'], list(
                                handydicts.structure_type[
                                    'retrofit'].keys()))].copy()
                    if len(updated_perf_array) == 0 or \
                       (key == "new" and
                        len(numpy.unique(updated_perf_array[
                            'template'])) != 1 or key == "retrofit" and
                        len(numpy.unique(updated_perf_array[
                            'template'])) != len(
                            handydicts.structure_type["retrofit"].keys())):
                        raise ValueError(
                            "EPlus vintage name not found for ECM '" +
                            self.name + "'")
                else:
                    raise KeyError(
                        "Invalid performance dict key for ECM '" +
                        self.name + "'")

                # Separate filtered array into the rows representing measure
                # consumption and those representing baseline consumption
                updated_perf_array_m, updated_perf_array_b = [
                    updated_perf_array[updated_perf_array[
                        'measure'] != 'none'],
                    updated_perf_array[updated_perf_array[
                        'measure'] == 'none']]
                # Ensure that a baseline consumption row exists for every
                # measure consumption row retrieved
                if len(updated_perf_array_m) != len(updated_perf_array_b):
                    raise ValueError(
                        "Lengths of ECM and baseline EPlus data arrays "
                        "are unequal for ECM '" + self.name + "'")
                # Initialize total measure and baseline consumption values
                val_m, val_b = (0 for n in range(2))

                # Weight and combine the measure/baseline consumption values
                # left in the EnergyPlus arrays; subtract total measure
                # consumption from baseline consumption and divide by baseline
                # consumption to reach relative savings value for the current
                # dictionary branch
                for ind in range(0, len(updated_perf_array_m)):
                    row_m, row_b = [
                        updated_perf_array_m[ind], updated_perf_array_b[ind]]
                    # Loop through remaining columns with consumption data
                    for n in eplus_header:
                        if row_m[n].dtype.char != 'S' and \
                                row_m[n].dtype.char != 'U':
                            # Find appropriate building type to weight
                            # consumption data points by
                            eplus_bldg_type_wt_row_m, \
                                eplus_bldg_type_wt_row_b = [
                                    eplus_bldg_types[row_m['building_type']],
                                    eplus_bldg_types[row_b['building_type']]]
                            # Weight consumption data points by factors for
                            # appropriate building type and vintage
                            row_m_val, row_b_val = [(
                                row_m[n] * eplus_bldg_type_wt_row_m *
                                vintage_weights[row_m['template'].copy()]),
                                (row_b[n] * eplus_bldg_type_wt_row_b *
                                 vintage_weights[row_b['template'].copy()])]
                            # Add weighted measure consumption data point to
                            # total measure consumption
                            val_m += row_m_val
                            # Add weighted baseline consumption data point to
                            # total base consumption
                            val_b += row_b_val
                    # Find relative savings if total baseline use != zero
                    if val_b != 0:
                        end_key_val = (val_b - val_m) / val_b
                    else:
                        end_key_val = 0

                # Update the current dictionary branch value to the final
                # measure relative savings value derived above
                perf_dict[key] = round(end_key_val, 3)

        return perf_dict

    def create_perf_dict(self, msegs):
        """Create dict to fill with updated measure performance information.

        Note:
            Given a measure's applicable climate zone, building type,
            structure type, fuel type, and end use, create a dict of zeros
            with a hierarchy that is defined by these measure properties.

        Args:
            msegs (dict): Baseline microsegment stock and energy use
                information to use in validating categorization of
                measure performance information.

        Returns:
            Empty dictionary to fill with EnergyPlus-based performance
            information broken down by climate zone, building type/vintage,
            fuel type, and end use.
        """
        # Initialize performance dict
        perf_dict_empty = {"primary": None, "secondary": None}
        # Create primary dict structure from baseline market properties
        perf_dict_empty["primary"] = self.create_nested_dict(
            msegs, "primary")

        # Create secondary dict structure from baseline market properties
        # (if needed)
        if isinstance(self.end_use, dict):
            perf_dict_empty["secondary"] = self.create_nested_dict(
                msegs, "secondary")

        return perf_dict_empty

    def create_nested_dict(self, msegs, mseg_type):
        """Create a nested dictionary based on a pre-defined branch structure.

        Note:
            Create a nested dictionary with a structure that is defined by a
            measure's applicable baseline market, with end leaf node values set
            to zero.

        Args:
            msegs (dict): Baseline microsegment stock and energy use
                information to use in validating categorization of
                measure performance information.
            mseg_type (string): Primary or secondary microsegment type flag.

        Returns:
            Nested dictionary of zeros with desired branch structure.
        """
        # Initialize output dictionary
        output_dict = {}
        # Establish levels of the dictionary key hierarchy from measure's
        # applicable baseline market information
        keylevels = [
            self.climate_zone, self.bldg_type, self.fuel_type[mseg_type],
            self.end_use[mseg_type], self.structure_type]
        # Find all possible dictionary key chains from the above key level
        # info.
        dict_keys = list(itertools.product(*keylevels))
        # Remove all natural gas cooling key chains (EnergyPlus output
        # files do not include a column for natural gas cooling)
        dict_keys = [x for x in dict_keys if not(
            'natural gas' in x and 'cooling' in x)]

        # Use an input dictionary with valid baseline microsegment information
        # to check that each of the microsegment key chains generated above is
        # valid for the current measure; if not, remove each invalid key chain
        # from further operations

        # Initialize a list of valid baseline microsegment key chains for the
        # measure
        dict_keys_fin = []
        # Loop through the initial set of candidate key chains generated above
        for kc in dict_keys:
            # Copy the input dictionary containing valid key chains
            dict_check = copy.deepcopy(msegs)
            # Loop through all keys in the candidate key chain and move down
            # successive levels of the input dict until either the end of the
            # key chain is reached or a key is not found in the list of valid
            # keys for the current input dict level. In the former case, the
            # resultant dict will point to all technologies associated with the
            # current key chain (e.g., ASHP, LFL, etc.) If none of these
            # technologies are found in the list of technologies covered by the
            # measure, the key chain is deemed invalid
            for ind, key in enumerate(kc):
                # If key is found in the list of valid keys for the current
                # input microsegment dict level, move on to next level in the
                # dict; otherwise, break the current loop
                if key in dict_check.keys():
                    dict_check = dict_check[key]
                    # In the case of heating or cooling end uses, an additional
                    # 'technology type' key must be accounted for ('supply' or
                    # 'demand')
                    if key in ['heating', 'cooling']:
                        dict_check = \
                            dict_check[self.technology_type[mseg_type]]
                else:
                    break

            # If any of the technology types listed in the measure definition
            # are found in the keys of the dictionary yielded by the above
            # loop, add the key chain to the list that is used to define the
            # final nested dictionary output (e.g., the key chain is valid)
            if any([x in self.technology[mseg_type]
                   for x in dict_check.keys()]):
                dict_keys_fin.append(kc)

        # Loop through each of the valid key chains and create an
        # associated path in the dictionary, terminating with a zero value
        # to be updated in a subsequent routine with EnergyPlus output data
        for kc in dict_keys_fin:
            current_level = output_dict
            for ind, elem in enumerate(kc):
                if elem not in current_level and (ind + 1) != len(kc):
                    current_level[elem] = {}
                elif elem not in current_level and (ind + 1) == len(kc):
                    current_level[elem] = 0
                current_level = current_level[elem]

        return output_dict

    def build_array(self, eplus_coltyp, files_to_build):
        """Assemble EnergyPlus data from one or more CSVs into a record array.

        Args:
            eplus_coltypes (list): Expected EnergyPlus variable data types.
            files_to_build (CSV objects): CSV files of EnergyPlus energy
                consumption information under measure and baseline cases.

        Returns:
            Structured array of EnergyPlus energy savings information for the
            Measure.
        """
        # Loop through CSV file objects and import/add to record array
        for ind, f in enumerate(files_to_build):
            # Read in CSV file to array
            eplus_file = numpy.genfromtxt(f, names=True, dtype=eplus_coltyp,
                                          delimiter=",", missing_values='')
            # Find only those rows in the array that represent
            # completed simulation runs for the measure of interest
            eplus_file = eplus_file[(eplus_file[
                'measure'] == self.energy_efficiency['EnergyPlus file']) |
                (eplus_file['measure'] == 'none') &
                (eplus_file['status'] == 'completed normal')]
            # Initialize or add to a master array that covers all CSV data
            if ind == 0:
                eplus_perf_array = eplus_file
            else:
                eplus_perf_array = \
                    numpy.concatenate((eplus_perf_array, eplus_file))

        return eplus_perf_array


class MeasurePackage(Measure):
    """Set up a class representing packaged efficiency measures as objects.

    The MeasurePackage class is a subclass of the Measure class.

    Attributes:
        handyvars (object): Global variables useful across class methods.
        contributing_ECMs (list): List of measures to package.
        htcl_ECMs (dict): Dict to store contributing ECM objects that apply to
            either heating/cooling equipment or envelope.
        name (string): Package name.
        benefits (dict): Percent improvements in energy savings and/or cost
            reductions from packaging measures.
        remove (boolean): Determines whether package should be removed from
            analysis engine due to insufficient market source data.
        energy_outputs (dict): Indicates whether site energy or captured
            energy site-source conversions were used in measure preparation;
            whether alternate regions were used; whether tsv metrics were
            used; whether public health cost adders were used; and whether
            fuel splits were used.
        market_entry_year (int): Earliest year of market entry across all
            measures in the package.
        market_exit_year (int): Latest year of market exit across all
            measures in the package.
        yrs_on_mkt (list): List of years that the measure is active on market.
        measure_type (string): "full service", "add-on", or "mixed".
        climate_zone (list): Applicable climate zones for package.
        bldg_type (list): Applicable building types for package.
        structure_type (list): Applicable structure types for package.
        fuel_type (dict): Applicable primary fuel type for package.
        end_use (dict): Applicable primary end use type for package.
        technology (list): Applicable technologies for package.
        technology_type (dict): Applicable technology types (supply/demand) for
            package.
        markets (dict): Data grouped by adoption scheme on:
            a) 'master_mseg': a package's master market microsegments (stock,
               energy, carbon, cost),
            b) 'mseg_adjust': all microsegments that contribute to each master
               microsegment (required later for measure competition).
            c) 'mseg_out_break': master microsegment breakdowns by key
               variables (e.g., climate zone, building type, end use, etc.)
        htcl_overlaps (dict): Dict to store data on heating/cooling overlaps
            across contributing equipment vs. envelope ECMs that apply to the
            same region, building type/vintage, fuel type, and end use.
        sector_shapes (dict): Sector-level hourly baseline and efficient load
            shapes by adopt scheme, EMM region, and year.

    """

    def __init__(self, measure_list_package, p, bens, handyvars, handyfiles,
                 opts):
        self.handyvars = handyvars
        self.contributing_ECMs = copy.deepcopy(measure_list_package)
        # Sort contributing ECMs in the package such that any measures that
        # affect envelope (of the "demand" technology type attribute) come
        # last in the updating order; this assumption is necessary to
        # correctly remove overlaps between heating/cooling ECMs that affect
        # to equipment ("supply" technology type) vs. envelope - that
        # process assumes any overlaps across "supply" measures are
        # removed first, and then overlaps between "supply" and "demand"
        # measures are removed
        self.contributing_ECMs.sort(
            key=lambda x: x.technology_type["primary"][0], reverse=True)
        # Check to ensure energy output settings for all measures that
        # contribute to the package are identical
        if not all([all([m.energy_outputs[x] ==
                         self.contributing_ECMs[0].energy_outputs[x] for
                         x in self.contributing_ECMs[0].energy_outputs.keys()]
                        for m in self.contributing_ECMs[1:])]):
            raise ValueError(
                "Package '" + self.name + "' attempts to merge measures with "
                "different energy output settings; re-prepare package's "
                "contributing ECMs to ensure these settings are identical")
        self.htcl_ECMs = {}
        self.name = p
        # Check to ensure that measure name is proper length for plotting
        if len(self.name) > 40:
            raise ValueError(
                "ECM '" + self.name + "' name must be <= 40 characters")
        self.benefits = bens
        self.remove = False
        self.energy_outputs = {
            "site_energy": False, "captured_energy_ss": False,
            "alt_regions": False, "tsv_metrics": False, "health_costs": False,
            "split_fuel": False}
        # Check for consistent use of site or source energy units for all
        # ECMs in package
        if all([x.energy_outputs["site_energy"] is True for
                x in self.contributing_ECMs]):
            self.energy_outputs["site_energy"] = True
        elif all([x.energy_outputs["site_energy"] is False for
                  x in self.contributing_ECMs]):
            self.energy_outputs["site_energy"] = False
        else:
            raise ValueError(
                "Inconsistent energy output units (site vs. source) "
                "across contributing ECMs for package: '" + str(self.name) +
                "'. To address this issue, delete the file "
                "./supporting_data/ecm_prep.json and rerun ecm_prep.py.")
        # Check for consistent use of site-source energy conversion methods
        # across all ECMs in a package
        if all([x.energy_outputs["captured_energy_ss"] is True for
                x in self.contributing_ECMs]):
            self.energy_outputs["captured_energy_ss"] = True
        elif all([x.energy_outputs["captured_energy_ss"] is False for
                 x in self.contributing_ECMs]):
            self.energy_outputs["captured_energy_ss"] = False
        else:
            raise ValueError(
                'Inconsistent site-source conversion methods '
                'across contributing ECMs for package: ' + str(self.name) +
                "'. To address this issue, delete the file "
                "./supporting_data/ecm_prep.json and rerun ecm_prep.py.")
        # Check for consistent use of alternate regional breakouts
        # across all ECMs in a package
        if all([x.energy_outputs["alt_regions"] is not False and (
            x.energy_outputs["alt_regions"] ==
            self.contributing_ECMs[0].energy_outputs["alt_regions"]) for
                x in self.contributing_ECMs]):
            self.energy_outputs["alt_regions"] = \
                self.contributing_ECMs[0].energy_outputs["alt_regions"]
        elif all([x.energy_outputs["alt_regions"] is False for
                 x in self.contributing_ECMs]):
            self.energy_outputs["alt_regions"] = False
        else:
            raise ValueError(
                'Inconsistent regional breakout used '
                'across contributing ECMs for package: ' + str(self.name) +
                "'. To address this issue, delete the file "
                "./supporting_data/ecm_prep.json and rerun ecm_prep.py.")
        # Check for consistent use of tsv metrics across all ECMs in a package
        if all([x.energy_outputs["tsv_metrics"] is not False and (
            x.energy_outputs["tsv_metrics"] ==
            self.contributing_ECMs[0].energy_outputs["tsv_metrics"]) for
                x in self.contributing_ECMs]):
            self.energy_outputs["tsv_metrics"] = \
                self.contributing_ECMs[0].energy_outputs["tsv_metrics"]
        elif all([x.energy_outputs["tsv_metrics"] is False for
                 x in self.contributing_ECMs]):
            self.energy_outputs["tsv_metrics"] = False
        else:
            raise ValueError(
                'Inconsistent time sensitive valuation metrics used '
                'across contributing ECMs for package: ' + str(self.name) +
                "'. To address this issue, delete the file "
                "./supporting_data/ecm_prep.json and rerun ecm_prep.py.")
        # Check for consistent use of health costs across all ECMs in a package
        if all([x.energy_outputs["health_costs"] is not False and (
            x.energy_outputs["health_costs"] ==
            self.contributing_ECMs[0].energy_outputs["health_costs"]) for
                x in self.contributing_ECMs]):
            self.energy_outputs["health_costs"] = \
                self.contributing_ECMs[0].energy_outputs["health_costs"]
        elif all([x.energy_outputs["health_costs"] is False for
                 x in self.contributing_ECMs]):
            self.energy_outputs["health_costs"] = False
        else:
            raise ValueError(
                'Inconsistent public health cost assumptions used '
                'across contributing ECMs for package: ' + str(self.name) +
                "'. To address this issue, delete the file "
                "./supporting_data/ecm_prep.json and rerun ecm_prep.py.")
        # Check for consistent use of fuel splits across all ECMs in a package
        if all([x.energy_outputs["split_fuel"] is not False and (
            x.energy_outputs["split_fuel"] ==
            self.contributing_ECMs[0].energy_outputs["split_fuel"]) for
                x in self.contributing_ECMs]):
            self.energy_outputs["split_fuel"] = \
                self.contributing_ECMs[0].energy_outputs["split_fuel"]
        elif all([x.energy_outputs["split_fuel"] is False for
                 x in self.contributing_ECMs]):
            self.energy_outputs["split_fuel"] = False
        else:
            raise ValueError(
                'Inconsistent fuel splitting output settings used '
                'across contributing ECMs for package: ' + str(self.name) +
                "'. To address this issue, delete the file "
                "./supporting_data/ecm_prep.json and rerun ecm_prep.py.")
        # Set market entry year as earliest of all the packaged measures
        if any([x.market_entry_year is None or (int(
                x.market_entry_year) < int(x.handyvars.aeo_years[0])) for x in
               self.contributing_ECMs]):
            self.market_entry_year = int(handyvars.aeo_years[0])
        else:
            self.market_entry_year = min([
                x.market_entry_year for x in self.contributing_ECMs])
        # Set market exit year is latest of all the packaged measures
        if any([x.market_exit_year is None or (int(
                x.market_exit_year) > (int(x.handyvars.aeo_years[0]) + 1)) for
                x in self.contributing_ECMs]):
            self.market_exit_year = int(handyvars.aeo_years[-1]) + 1
        else:
            self.market_exit_year = max([
                x.market_entry_year for x in self.contributing_ECMs])
        self.yrs_on_mkt = [
            str(i) for i in range(
                self.market_entry_year, self.market_exit_year)]
        if all([m.measure_type == "full service" for m in
                self.contributing_ECMs]):
            self.measure_type = "full service"
        elif all([m.measure_type == "add-on" for m in
                  self.contributing_ECMs]):
            self.measure_type = "add-on"
        else:
            self.measure_type = "mixed"
        self.climate_zone, self.bldg_type, self.structure_type, \
            self.fuel_type, self.technology = (
                [] for n in range(5))
        self.end_use, self.technology_type = (
            {"primary": [], "secondary": None} for n in range(2))
        self.markets = {}
        self.htcl_overlaps = {adopt: {"keys": [], "data": {}} for
                              adopt in handyvars.adopt_schemes}
        # Only initialize sector-level load shape information for the package
        # if this option is specified by the user
        if opts.sect_shapes is True:
            self.sector_shapes = {a_s: {} for a_s in handyvars.adopt_schemes}
        else:
            self.sector_shapes = None
        for adopt_scheme in handyvars.adopt_schemes:
            self.markets[adopt_scheme] = {
                "master_mseg": {
                    "stock": {
                        "total": {
                            "all": None, "measure": None},
                        "competed": {
                            "all": None, "measure": None}},
                    "energy": {
                        "total": {
                            "baseline": None, "efficient": None},
                        "competed": {
                            "baseline": None, "efficient": None}},
                    "carbon": {
                        "total": {
                            "baseline": None, "efficient": None},
                        "competed": {
                            "baseline": None, "efficient": None}},
                    "cost": {
                        "stock": {
                            "total": {
                                "baseline": None, "efficient": None},
                            "competed": {
                                "baseline": None, "efficient": None}},
                        "energy": {
                            "total": {
                                "baseline": None, "efficient": None},
                            "competed": {
                                "baseline": None, "efficient": None}},
                        "carbon": {
                            "total": {
                                "baseline": None, "efficient": None},
                            "competed": {
                                "baseline": None, "efficient": None}}},
                    "lifetime": {"baseline": None, "measure": None}},
                "mseg_adjust": {
                    "contributing mseg keys and values": {},
                    "competed choice parameters": {},
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
                            "adjusted energy (competed and captured)": {}}}},
                "mseg_out_break": {key: {
                    "baseline": copy.deepcopy(self.handyvars.out_break_in),
                    "efficient": copy.deepcopy(self.handyvars.out_break_in),
                    "savings": copy.deepcopy(self.handyvars.out_break_in)} for
                    key in ["energy", "carbon", "cost"]}}

    def merge_measures(self, opts):
        """Merge the markets information of multiple individual measures.

        Attributes:
            opts (object): Stores user-specified execution options.

        Note:
            Combines the 'markets' attributes of each individual measure into
            a packaged 'markets' attribute.

        Returns:
            Updated 'markets' attribute for a packaged measure that combines
            the 'markets' attributes of multiple individual measures.
        """
        # Initialize a list of dicts for storing measure microsegment data as
        # it is looped through and updated
        mseg_dat_rec = [{} for n in range(len(self.contributing_ECMs))]
        # Loop through each measure and either adjust and record its attributes
        # for further processing or directly add its attributes to the merged
        # package measure definition
        for ind, m in enumerate(self.contributing_ECMs):
            # Add measure climate zones
            self.climate_zone.extend(
                list(set(m.climate_zone) - set(self.climate_zone)))
            # Add measure building types
            self.bldg_type.extend(
                list(set(m.bldg_type) - set(self.bldg_type)))
            # Add measure structure types
            self.structure_type.extend(
                list(set(m.structure_type) - set(self.structure_type)))
            # Add measure fuel types
            self.fuel_type.extend(
                list(set(m.fuel_type) - set(self.fuel_type)))
            # Add measure end uses
            self.end_use["primary"].extend(
                list(set(m.end_use["primary"]) -
                     set(self.end_use["primary"])))
            # Add measure technologies
            self.technology.extend(
                list(set(m.technology) - set(self.technology)))
            # Add measure technology types
            self.technology_type["primary"].extend(
                list(set(m.technology_type["primary"]) -
                     set(self.technology_type["primary"])))

            # Update measure contributing mseg data by adoption scheme
            for adopt_scheme in self.handyvars.adopt_schemes:
                # Set contributing microsegment data for individual measure;
                # deep copy to ensure that initial measure data are retained
                # throughout the updates
                msegs_meas_init = copy.deepcopy(
                    m.markets[adopt_scheme]["mseg_adjust"])
                # Set output breakout data for individual measure (used to
                # break out results by climate, building, and end use)
                mseg_out_break_init = copy.deepcopy(
                    m.markets[adopt_scheme]["mseg_out_break"])
                # Set contributing microsegment data to update for package
                # under the current adoption scheme
                msegs_pkg_init = self.markets[adopt_scheme]["mseg_adjust"]
                # Set sector-level load shape data for individual measure,
                # if sector-level load shapes are being generated for the
                # package; otherwise set to None
                if self.sector_shapes:
                    sect_shapes_init = copy.deepcopy(
                        m.sector_shapes_pkg[adopt_scheme])
                else:
                    sect_shapes_init = None
                # Loop through/update all microsegment data for measure
                for k in msegs_meas_init.keys():
                    # Remove any direct overlaps between the measure's
                    # contributing msegs and those of other measures in the
                    # package (e.g., msegs with the exact same key information)
                    if k == "contributing mseg keys and values":
                        for cm in msegs_meas_init[k].keys():
                            msegs_meas_init[k][cm], mseg_out_break_init, \
                                sect_shapes_init = self.merge_direct_overlaps(
                                    msegs_meas_init[k][cm], cm, adopt_scheme,
                                    mseg_out_break_init, m.name,
                                    m.technology_type["primary"][0],
                                    sect_shapes_init, m.fuel_switch_to)
                    # Add all other contributing microsegment data for
                    # the measure
                    elif k in ["competed choice parameters",
                               "secondary mseg adjustments"]:
                        self.update_dict(msegs_pkg_init[k], msegs_meas_init[k])
                # Record adjusted contributing microsegment, output
                # breakout data, and sector shapes data for the measure for
                # subsequent use in removing any overlaps between heating/
                # cooling equipment and envelope measures (if applicable) and
                # finalizing the measure's contribution to the package
                mseg_dat_rec[ind][adopt_scheme] = {
                    "name": m.name,
                    "htcl_type": m.technology_type["primary"][0],
                    "microsegments": msegs_meas_init,
                    "breakouts": mseg_out_break_init,
                    "sector_shapes": sect_shapes_init,
                    "fuel_switch_to": m.fuel_switch_to}

        # Loop through all previously adjusted/recorded microsegment and
        # outbreak data for the measures that contribute to the package;
        # if necessary, remove remaining overlaps between heating/cooling
        # equipment and envelope measures in the package; finalize the
        # contributing data for the package
        for m in mseg_dat_rec:
            # Update measure contributing mseg data by adoption scheme
            for adopt_scheme in self.handyvars.adopt_schemes:
                # Set shorthands for contributing mseg, outbreak, sector shapes
                # data (if applicable), and package data to finalize
                msegs_meas_fin = m[adopt_scheme]["microsegments"][
                    "contributing mseg keys and values"]
                mseg_out_break_fin = m[adopt_scheme]["breakouts"]
                if self.sector_shapes:
                    sect_shapes_fin = m[adopt_scheme]["sector_shapes"]
                else:
                    sect_shapes_fin = None
                msegs_pkg_fin = self.markets[adopt_scheme]["mseg_adjust"][
                    "contributing mseg keys and values"]
                # Loop through/update all microsegment data for measure
                for cm in msegs_meas_fin.keys():
                    msegs_meas_fin[cm], mseg_out_break_fin, \
                        sect_shapes_fin = self.merge_htcl_overlaps(
                            msegs_meas_fin[cm], cm, adopt_scheme,
                            mseg_out_break_fin, m[adopt_scheme]["name"],
                            m[adopt_scheme]["htcl_type"], sect_shapes_fin,
                            m[adopt_scheme]["fuel_switch_to"])
                    # Add finalized contributing microsegment information for
                    # individual measure to the packaged measure, creating a
                    # new contributing microsegment key if one does not already
                    # exist for the package
                    if cm not in msegs_pkg_fin.keys():
                        msegs_pkg_fin[cm] = msegs_meas_fin[cm]
                    else:
                        msegs_pkg_fin[cm] = self.add_keyvals(
                            msegs_pkg_fin[cm], msegs_meas_fin[cm])
                    # Check for additional energy savings and/or installed cost
                    # benefits from packaging and apply if applicable
                    self.apply_pkg_benefits(
                        msegs_pkg_fin[cm], adopt_scheme, sect_shapes_fin, cm)
                # Generate a dictionary including data on how much of the
                # packaged measure's baseline energy/carbon/cost is attributed
                # to each of the output climate zones, building types, and end
                # uses it applies to
                for v in ["energy", "carbon", "cost"]:
                    for s in ["baseline", "efficient", "savings"]:
                        self.merge_out_break(self.markets[adopt_scheme][
                            "mseg_out_break"][v][s],
                            mseg_out_break_fin[v][s])

        # Generate a packaged master microsegment based on the contributing
        # microsegment information defined above
        for adopt_scheme in self.handyvars.adopt_schemes:
            # Loop through all contributing microsegments for the packaged
            # measure and add to the packaged master microsegment
            for k in (self.markets[adopt_scheme]["mseg_adjust"][
                    "contributing mseg keys and values"].keys()):
                self.add_keyvals(
                    self.markets[adopt_scheme]["master_mseg"],
                    self.markets[adopt_scheme]["mseg_adjust"][
                        "contributing mseg keys and values"][k])

            # Determine contributing microsegment key chain count for use in
            # calculating an average baseline and measure lifetime below
            key_chain_ct_package = len(
                self.markets[adopt_scheme]["mseg_adjust"][
                    "contributing mseg keys and values"].keys())
            # Reduce summed lifetimes across all microsegments that contribute
            # to the packaged master microsegment by the number of
            # microsegments that contributed to the sums, to arrive at an
            # average baseline/measure lifetime for the packaged measure
            for yr in self.handyvars.aeo_years:
                self.markets[adopt_scheme]["master_mseg"][
                    "lifetime"]["baseline"][yr] = \
                    self.markets[adopt_scheme]["master_mseg"][
                    "lifetime"]["baseline"][yr] / key_chain_ct_package
            self.markets[adopt_scheme]["master_mseg"]["lifetime"][
                "measure"] = self.markets[adopt_scheme][
                "master_mseg"]["lifetime"]["measure"] / key_chain_ct_package

    def htcl_adj_rec(self):
        """Record overlaps in heating/cooling supply and demand-side energy."""

        # Determine the subset of the package's contributing ECMs that applies
        # to heating/cooling equipment
        self.htcl_ECMs["supply"] = [m for m in self.contributing_ECMs if (
            any([x in m.end_use["primary"] for x in [
                "heating", "cooling", "secondary heating"]]) and
            "supply" in m.technology_type["primary"])]
        # Determine the subset of the package's contributing ECMs that applies
        # to building envelope
        self.htcl_ECMs["demand"] = [m for m in self.contributing_ECMs if
                                    "demand" in m.technology_type["primary"]]
        # If there are both heating/cooling equipment and envelope measures,
        # in the package, continue further to check for overlaps
        if all([len(self.htcl_ECMs[x]) != 0 for x in ["supply", "demand"]]):
            # Loop through the heating/cooling equipment measures, check for
            # overlaps with envelope measures, and record the overlaps
            for ind, m in enumerate(self.htcl_ECMs["supply"]):
                # Record unique data for each adoption scheme
                for adopt_scheme in self.handyvars.adopt_schemes:
                    # Use shorthand for measure contributing microsegment data
                    msegs_meas = copy.deepcopy(m.markets[adopt_scheme][
                        "mseg_adjust"]["contributing mseg keys and values"])
                    # Loop through all contributing microsegment keys for the
                    # equipment measure that apply to heating/cooling end uses
                    # and have not previously been parsed for overlapping data
                    for cm_key in [x for x in msegs_meas.keys() if (any([
                        e in x for e in [
                            "heating", "cooling", "secondary heating"]]) and x
                            not in self.htcl_overlaps[adopt_scheme]["keys"])]:
                        # Record that the contributing microsegment key has
                        # been parsed for overlapping data
                        self.htcl_overlaps[adopt_scheme]["keys"].append(cm_key)
                        # Translate the contributing microsegment key (which
                        # is in string format) to list format
                        keys = literal_eval(cm_key)
                        # Pull out region, building type/vintage,
                        # fuel type, and end use from the key list
                        cm_key_match = [str(x) for x in [
                            keys[1], keys[2], keys[-1], keys[3], keys[4]]]
                        # Determine which, if any, envelope ECMs overlap with
                        # the region, building type/vintage, fuel type, and
                        # end use for the current contributing mseg for the
                        # equipment ECM
                        dmd_match_ECMs = [
                            x for x in self.htcl_ECMs["demand"] if
                            any([all([k in z for k in cm_key_match]) for z in
                                x.markets[adopt_scheme]["mseg_adjust"][
                                "contributing mseg keys and values"].keys()])]
                        # If an overlap is identified, record all necessary
                        # data for the current contributing microsegment
                        # across both the equipment and envelope side
                        # that are needed to remove the overlap subsequently
                        if dmd_match_ECMs != 0:
                            # Record equipment energy savings. Note: this is
                            # initialized to zero as total savings across
                            # all equipment measures that apply to the current
                            # microsegment are determined subsequently
                            supply_save, supply_base = ({
                                yr: 0 for yr in self.handyvars.aeo_years} for
                                n in range(2))
                            # Determine the specific contributing microsegment
                            # key(s) to use in pulling data from overlapping
                            # envelope measures for the current region/bldg/
                            # vintage/fuel/end use combination
                            cm_keys_dmd = [[x for x in z.markets[adopt_scheme][
                                "mseg_adjust"][
                                "contributing mseg keys and values"].keys()
                                if all([k in x for k in cm_key_match])] for
                                z in dmd_match_ECMs]
                            # Record envelope energy savings across all
                            # envelope measures that overlap with current mseg
                            dmd_save = {yr: sum([sum([(
                                dmd_match_ECMs[m].markets[adopt_scheme][
                                    "mseg_adjust"][
                                    "contributing mseg keys and values"][
                                    cm_keys_dmd[m][k]]["energy"][
                                    "total"]["baseline"][yr] -
                                dmd_match_ECMs[m].markets[adopt_scheme][
                                    "mseg_adjust"][
                                    "contributing mseg keys and values"][
                                    cm_keys_dmd[m][k]]["energy"][
                                    "total"]["efficient"][yr]) for k in range(
                                        len(cm_keys_dmd[m]))]) for
                                m in range(len(dmd_match_ECMs))]) for yr in
                                self.handyvars.aeo_years}
                            # Record envelope energy baselines across all
                            # envelope measures that overlap with current mseg
                            dmd_base = {yr: sum([sum([
                                dmd_match_ECMs[m].markets[adopt_scheme][
                                    "mseg_adjust"][
                                    "contributing mseg keys and values"][
                                    cm_keys_dmd[m][k]]["energy"][
                                    "total"]["baseline"][yr] for k in range(
                                        len(cm_keys_dmd[m]))]) for
                                m in range(len(dmd_match_ECMs))]) for yr in
                                self.handyvars.aeo_years}

                            # Translate key used to identify overlaps to str
                            cm_key_store = str(cm_key_match)
                            # Record the overlap data if it has not already
                            # been recorded for the current overlapping
                            # region, building type, building vintage,
                            # fuel, and end use
                            if cm_key_store not in self.htcl_overlaps[
                                    adopt_scheme]["data"].keys():
                                # Data include the overlapping energy savings
                                # and baselines recorded for the equipment/
                                # envelope measures above, as well as the
                                # total energy use that could have overlapped,
                                # pulled from pre-calculated values
                                self.htcl_overlaps[adopt_scheme]["data"][
                                        cm_key_store] = {
                                    "supply": {"affected savings": supply_save,
                                               "total affected": supply_base},
                                    "demand": {"affected savings": dmd_save,
                                               "total affected": dmd_base},
                                    "total": self.handyvars.htcl_totals[
                                        cm_key_match[0]][
                                        cm_key_match[1]][cm_key_match[2]][
                                        cm_key_match[3]][cm_key_match[4]]}

    def merge_direct_overlaps(
            self, msegs_meas, cm_key, adopt_scheme,
            mseg_out_break_adj, name_meas, tech_htcl_meas,
            sect_shapes_meas, fuel_switch_to):
        """Adjust measure mseg data to address direct overlaps in package.

        Args:
            msegs_meas (dict): Data for the contributing microsegment of an
                individual measure that is being merged into the package.
            cm_key (tuple): Microsegment key describing the contributing
                microsegment currently being added (e.g. reg->bldg, etc.)
            adopt_scheme (string): Assumed consumer adoption scenario.
            mseg_out_break_adj (dict): Contributing measure baseline energy/
                carbon/cost baseline and savings data split by climate zone,
                building type, and end use.
            name_meas (string): Measure name.
            tech_htcl_meas (string): Measure applicability to either
                equipment ("supply") or envelope ("demand").
            sect_shapes_meas (dict or NoneType): Sector-level baseline and
                efficient load shape information for the current contributing
                microsegment, if applicable (otherwise, None).
            fuel_switch_to (string): Indicator of which baseline fuel the
                measure switches to (if applicable).

        Returns:
            Updated contributing microsegment, out break info., and (if
            applicable), sector shape data for the measure that accounts for
            direct overlaps between the measure and other contributing measures
            in the package given the current contributing microsegment
            information (e.g., an exact key match).
        """

        # Translate mseg key string to list elements
        key_list = literal_eval(cm_key)
        # Pull keys from the current contributing microsegment info. that
        # can be used to match across heating/cooling equip/env measures
        htcl_key_match = str([str(x) for x in [
            key_list[1], key_list[2], key_list[-1], key_list[3],
            key_list[4]]])
        # If the keys are not found in the package attribute that stores data
        # needed to adjust across equip/env msegs, set key to empty string
        if htcl_key_match not in self.htcl_overlaps[
                adopt_scheme]["data"].keys():
            htcl_key_match = ""
        # Determine what other measures in the package, if any, share an
        # exact match of the current contributing microsegment key information
        # for the individual measure; exclude the measure itself from this list
        overlap_meas = [
            x for x in self.contributing_ECMs if cm_key in x.markets[
                adopt_scheme]["mseg_adjust"][
                "contributing mseg keys and values"].keys() and
            x.name != name_meas]
        # If an exact match with other measures is identified for the current
        # contributing microsegment, update the contributing microsegment data
        # to account for/remove direct overlaps with other measures
        if len(overlap_meas) != 0:
            # Make a copy of the mseg info. that is unaffected by subsequent
            # operations in the loop
            msegs_meas_init = copy.deepcopy(msegs_meas)
            # Find base and efficient adjustment fractions
            base_adj, eff_adj = self.find_base_eff_adj_fracs(
                msegs_meas_init, cm_key, adopt_scheme, tech_htcl_meas,
                name_meas, htcl_key_match, overlap_meas)
            # Adjust energy, carbon, and energy/carbon cost data based on
            # savings contribution of the measure and overlapping measure(s)
            # in this contributing microsegment, as well as the relative
            # performance of the overlapping measure(s)
            for k in ["energy", "carbon"]:
                # Adjust sector-level energy load shape for the current
                # contributing microsegment, if applicable
                if k == "energy" and self.sector_shapes and (
                    sect_shapes_meas and
                        cm_key in sect_shapes_meas.keys()):
                    # Update baseline/efficient sector-level load data by year
                    for yr in self.handyvars.aeo_years_summary:
                        sect_shapes_meas[cm_key][yr]["baseline"] = [
                            x * base_adj[yr] for x in sect_shapes_meas[cm_key][
                                yr]["baseline"]]
                        sect_shapes_meas[cm_key][yr]["efficient"] = [
                            x * eff_adj[yr] for x in sect_shapes_meas[cm_key][
                                yr]["efficient"]]
                # Make adjustments to energy/carbon/cost microsegments
                mseg_adj, mseg_cost_adj, tot_base_orig, tot_eff_orig, \
                    tot_save_orig, tot_base_orig_ecost, tot_eff_orig_ecost, \
                    tot_save_orig_ecost = self.make_base_eff_adjs(
                        k, cm_key, msegs_meas, base_adj, eff_adj)
                # Make adjustments to energy/carbon/cost output breakouts
                mseg_out_break_adj = self.find_adj_out_break_cats(
                    k, cm_key, mseg_adj, mseg_cost_adj, mseg_out_break_adj,
                    tot_base_orig, tot_eff_orig, tot_save_orig,
                    tot_base_orig_ecost, tot_eff_orig_ecost,
                    tot_save_orig_ecost, key_list, fuel_switch_to)
            # Adjust stock and stock cost data based to be consistent with the
            # energy-based baseline adjustment fractions calculated above
            self.adj_pkg_mseg_keyvals(
                msegs_meas["stock"], base_adj, base_adj, base_eff_flag=None)
            self.adj_pkg_mseg_keyvals(msegs_meas["cost"]["stock"], base_adj,
                                      base_adj, base_eff_flag=None)
            # Adjust measure lifetime for contributing microsegment such that
            # when added to package, it averages with the lifetime data for
            # overlapping measures in the package for the current mseg
            self.div_keyvals_float(
                msegs_meas["lifetime"], (len(overlap_meas) + 1))
            # Adjust measure sub-market scaling for contributing microsegment
            # such that when recombined into the package, the maximum
            # sub-market scaling fraction across overlapping measures in
            # the current microsegment is yielded
            max_submkt_scale = max([msegs_meas["sub-market scaling"], max([
                x.markets[adopt_scheme]["mseg_adjust"][
                    "contributing mseg keys and values"][cm_key][
                    "sub-market scaling"] for x in overlap_meas])])
            msegs_meas["sub-market scaling"] = \
                max_submkt_scale / (len(overlap_meas) + 1)
        # For heating/cooling equipment measures that overlap with envelope
        # measures in the package, add energy/carbon data post-adjustment with
        # other overlapping equipment measures for current msegs to record of
        # overlapping energy baselines and savings between equipment and
        # envelope measures for the current region, building, vintage, fuel,
        # and end use combination
        if tech_htcl_meas == "supply" and htcl_key_match:
            for yr in self.handyvars.aeo_years:
                # Update total affected energy baseline in overlapping segment
                self.htcl_overlaps[adopt_scheme]["data"][htcl_key_match][
                    tech_htcl_meas]["total affected"][yr] += \
                        msegs_meas["energy"]["total"]["baseline"][yr]
                # Update total energy savings in overlapping segment
                self.htcl_overlaps[adopt_scheme]["data"][htcl_key_match][
                    tech_htcl_meas]["affected savings"][yr] += (
                        msegs_meas["energy"]["total"]["baseline"][yr] -
                        msegs_meas["energy"]["total"]["efficient"][yr])

        return msegs_meas, mseg_out_break_adj, sect_shapes_meas

    def merge_htcl_overlaps(
            self, msegs_meas, cm_key, adopt_scheme,
            mseg_out_break_adj, name_meas, tech_htcl_meas,
            sect_shapes_meas, fuel_switch_to):
        """Adjust measure mseg data to address equip/env overlaps in package.

        Args:
            msegs_meas (dict): Data for the contributing microsegment of an
                individual measure that is being merged into the package.
            cm_key (tuple): Microsegment key describing the contributing
                microsegment currently being added (e.g. reg->bldg, etc.)
            adopt_scheme (string): Assumed consumer adoption scenario.
            mseg_out_break_adj (dict): Contributing measure baseline energy/
                carbon/cost baseline and savings data split by climate zone,
                building type, and end use.
            name_meas (string): Measure name.
            tech_htcl_meas (string): Measure applicability to either
                equipment ("supply") or envelope ("demand").
            sect_shapes_meas (dict or NoneType): Sector-level baseline and
                efficient load shape information for the current contributing
                microsegment, if applicable (otherwise, None).
            fuel_switch_to (string): Indicator of which baseline fuel the
                measure switches to (if applicable).

        Returns:
            Updated contributing microsegment, out break info., and (if
            applicable), sector shape data for the measure that accounts for
            indirect overlaps between the measure and other heating/cooling
            equipment or envelope measures in the package given the current
            contributing microsegment information (e.g., key match by region,
            bldg. type/vintage, fuel, and end use).
        """
        # Translate mseg key string to list elements
        key_list = literal_eval(cm_key)
        # Pull keys from the current contributing microsegment info. that
        # can be used to match across heating/cooling equip/env measures
        htcl_key_match = str([str(x) for x in [
            key_list[1], key_list[2], key_list[-1], key_list[3],
            key_list[4]]])
        # If the keys are not found in the package attribute that stores data
        # needed to adjust across equip/env msegs, stop operation
        if htcl_key_match in self.htcl_overlaps[
                adopt_scheme]["data"].keys():
            # Make a copy of the mseg info. that is unaffected by subsequent
            # operations in the loop
            msegs_meas_init = copy.deepcopy(msegs_meas)
            # Find base and efficient adjustment fractions; directly
            # overlapping measures are none in this case
            base_adj, eff_adj = self.find_base_eff_adj_fracs(
                    msegs_meas_init, cm_key, adopt_scheme, tech_htcl_meas,
                    name_meas, htcl_key_match, overlap_meas="")
            # Adjust energy, carbon, and energy/carbon cost data based on
            # savings contribution of the measure and overlapping measure(s)
            # in this contributing microsegment, as well as the relative
            # performance of the overlapping measure(s)
            for k in ["energy", "carbon"]:
                # Adjust sector-level energy load shape for the current
                # contributing microsegment, if applicable
                if k == "energy" and self.sector_shapes and (
                        sect_shapes_meas and cm_key in
                        sect_shapes_meas.keys()):
                    # Update baseline/efficient sector-level load data by year
                    for yr in self.handyvars.aeo_years_summary:
                        sect_shapes_meas[cm_key][yr]["baseline"] = [
                            x * base_adj[yr] for x in sect_shapes_meas[cm_key][
                                yr]["baseline"]]
                        sect_shapes_meas[cm_key][yr]["efficient"] = [
                            x * eff_adj[yr] for x in sect_shapes_meas[cm_key][
                                yr]["efficient"]]
                    # Merge updated sector-level load shape information for
                    # current contributing microsegment into a final
                    # sector-level load dataset for the package that is
                    # broken out by adopt scheme, EMM region, and year

                    # If data do not already exist for the EMM region that the
                    # current mseg applies to, initialize the sector shape
                    # information for that region; otherwise add to exist. key
                    if str(key_list[1]) not in \
                            self.sector_shapes[adopt_scheme].keys():
                        self.sector_shapes[adopt_scheme][str(key_list[1])] = {
                            yr: {"baseline": sect_shapes_meas[
                                cm_key][yr]["baseline"],
                                 "efficient": sect_shapes_meas[
                                 cm_key][yr]["efficient"]}
                            for yr in self.handyvars.aeo_years_summary}
                    else:
                        for yr in self.handyvars.aeo_years_summary:
                            self.sector_shapes[
                                adopt_scheme][str(key_list[1])][yr][
                                "baseline"] = [x + y for x, y in zip(
                                    self.sector_shapes[adopt_scheme][
                                        str(key_list[1])][yr]["baseline"],
                                    sect_shapes_meas[cm_key][yr]["baseline"])]
                            self.sector_shapes[
                                adopt_scheme][str(key_list[1])][yr][
                                "efficient"] = [x + y for x, y in zip(
                                    self.sector_shapes[adopt_scheme][
                                        str(key_list[1])][yr]["efficient"],
                                    sect_shapes_meas[cm_key][yr]["efficient"])]
                # Make adjustments to energy/carbon/cost microsegments
                mseg_adj, mseg_cost_adj, tot_base_orig, tot_eff_orig, \
                    tot_save_orig, tot_base_orig_ecost, tot_eff_orig_ecost, \
                    tot_save_orig_ecost = self.make_base_eff_adjs(
                        k, cm_key, msegs_meas, base_adj, eff_adj)
                # Make adjustments to energy/carbon/cost output breakouts
                mseg_out_break_adj = self.find_adj_out_break_cats(
                    k, cm_key, mseg_adj, mseg_cost_adj, mseg_out_break_adj,
                    tot_base_orig, tot_eff_orig, tot_save_orig,
                    tot_base_orig_ecost, tot_eff_orig_ecost,
                    tot_save_orig_ecost, key_list, fuel_switch_to)

        return msegs_meas, mseg_out_break_adj, sect_shapes_meas

    def find_base_eff_adj_fracs(self, msegs_meas, cm_key, adopt_scheme,
                                tech_htcl_meas, name_meas, htcl_key_match,
                                overlap_meas):
        """Calculate overlap adjustments for measure mseg in a package.

        Args:
            msegs_meas (dict): Data for the contributing microsegment of an
                individual measure that is being merged into the package.
            cm_key (tuple): Microsegment key describing the contributing
                microsegment currently being added (e.g. reg->bldg, etc.)
            adopt_scheme (string): Assumed consumer adoption scenario.
            tech_htcl_meas (string): Measure applicability to either
                equipment ("supply") or envelope ("demand").
            name_meas (string): Measure name.
            overlap_meas (list or str): List of measure objs that also apply
                to the current contributing microsegment; will be an empty
                string when heating/cooling equipment and envelope overlaps
                are being addressed.

        Returns:
            Fractions for adjusting baseline and efficient energy, carbon,
            and cost data for the current contributing microsegment to
            account for overlaps with other measures.
        """

        # Develop baseline/efficient data adjustment fractions for two
        # overlap cases:

        # Case 1: overlap between heating/cooling equipment and
        # envelope microsegments with required adjustment data available;
        # here, microsegments will not overlap exactly, but will be linked by
        # region, building type/vintage, fuel, and end use
        if not overlap_meas and htcl_key_match:
            # For heating/cooling equipment/envelope overlap adjustments,
            # first determine the technology type of the current microsegment
            # being adjusted (equipment = supply; envelope = demand),
            # as well as the tech type of the overlapping microsegment
            if tech_htcl_meas == "supply":
                tech_htcl_overlp = "demand"
            elif tech_htcl_meas == "demand":
                tech_htcl_overlp = "supply"
            else:
                raise ValueError(
                    "Encountered unexpected technology type when adding "
                    "contributing measure '" + name_meas + "' "
                    "to package " + self.name)
            # Initialize estimates of the portion of total potential
            # overlapping energy use in the current microsegment that is
            # affected by measure(s) of the overlapping tech type; the savings
            # of these overlapping measure(s); the portion of total overlapping
            # savings that the current measure contributes; and the relative
            # performance of the overlapping measure(s)
            affected_htcl_frac, save_overlp_htcl, save_meas_htcl, \
                save_wt_meas_htcl, rp_overlp_htcl = ({
                    yr: 1 for yr in self.handyvars.aeo_years} for
                    n in range(5))
            # Set shorthand for total potential overlapping energy use
            totals = self.htcl_overlaps[adopt_scheme][
                    "data"][htcl_key_match]["total"]
            # Set shorthand for total savings and affected energy use
            # for the tech type of the current contributing mseg/measure
            tech_data = self.htcl_overlaps[adopt_scheme]["data"][
                htcl_key_match][tech_htcl_meas]
            # Set shorthand for total savings and affected energy use
            # for the overlapping tech type in the current contributing mseg
            overlp_data = self.htcl_overlaps[adopt_scheme]["data"][
                htcl_key_match][tech_htcl_overlp]

            # Loop through all years in the modeling time horizon and use
            # data above to develop baseline/efficient adjustment factors
            for yr in self.handyvars.aeo_years:
                # Ignore numpy divide by zero errors and handle NaNs
                with numpy.errstate(all='ignore'):
                    # Find the fraction of total potential overlapping energy
                    # use for given region region, building type/vintage, fuel
                    # type, and end use combination that is affected by the
                    # overlapping measure(s); handle zero denominator
                    try:
                        affected_htcl_frac[yr] = (
                            overlp_data["total affected"][yr] / totals[yr])
                    except ZeroDivisionError:
                        affected_htcl_frac[yr] = 0
                    # Handle numpy NaNs
                    if not numpy.isfinite(affected_htcl_frac[yr]):
                        affected_htcl_frac[yr] = 0
                    # Find relative savings fraction for the measure;
                    # handle zero denominator
                    try:
                        save_meas_htcl[yr] = (
                            tech_data["affected savings"][yr] /
                            tech_data["total affected"][yr])
                    except ZeroDivisionError:
                        save_meas_htcl[yr] = 0
                    # Handle numpy NaNs
                    if not numpy.isfinite(save_meas_htcl[yr]):
                        save_meas_htcl[yr] = 0
                    # Find relative savings fraction for the overlapping
                    # measure(s); handle zero denominator
                    try:
                        save_overlp_htcl[yr] = (
                            overlp_data["affected savings"][yr] /
                            overlp_data["total affected"][yr])
                    except ZeroDivisionError:
                        save_overlp_htcl[yr] = 0
                    # Handle numpy NaNs
                    if not numpy.isfinite(save_overlp_htcl[yr]):
                        save_overlp_htcl[yr] = 0
                    # Set relative performance for the overlapping measure(s)
                    rp_overlp_htcl[yr] = 1 - save_overlp_htcl[yr]

                    # Establish the ratio of the measure's savings fraction in
                    # current microsegment to that of the overlapping
                    # measure(s); use absolute savings values for the ratio to
                    # ensure that fractions sum to one; handle zero denominator
                    try:
                        save_wt_meas_htcl[yr] = (abs(save_meas_htcl[yr]) / (
                            abs(save_meas_htcl[yr]) +
                            abs(save_overlp_htcl[yr])))
                    except ZeroDivisionError:
                        save_wt_meas_htcl[yr] = 0.5
                    # Handle numpy NaNs
                    if not numpy.isfinite(save_wt_meas_htcl[yr]):
                        save_wt_meas_htcl[yr] = 0.5
            # Final baseline adjustment factor is determined by the measure's
            # fractional contribution to total affected overlapping savings
            # for the fraction of affected overlapping energy use
            base_adj = {
                yr: (1 - affected_htcl_frac[yr]) + (
                    affected_htcl_frac[yr] * save_wt_meas_htcl[yr]) for
                yr in self.handyvars.aeo_years}
            # Final efficient adjustment factor adds multiplication of the
            # relative performance of the overlapping measure(s) to the
            # baseline adjustment calculation
            eff_adj = {
                yr: (1 - affected_htcl_frac[yr]) + (
                    affected_htcl_frac[yr] * save_wt_meas_htcl[yr] *
                    rp_overlp_htcl[yr]) for
                yr in self.handyvars.aeo_years}
        # Case 2: direct overlap between the exact same applicable microsegment
        # (e.g., a supply and supply mseg that apply to the exact same region,
        # bldg/vintage, fuel, end use, tech)
        elif overlap_meas:
            # Initialize an additional adjustment to account for sub-market
            # scaling fractions across overlapping measure(s)
            sbmkt_wt_meas = {yr: 0 for yr in self.handyvars.aeo_years}
            # Establish a common baseline microsegment value for calculations
            # below; baseline microsegments will not be identical in cases
            # where one or more of the overlapping measures has a sub-market
            # scaling fraction, and the inapplicable portion of the common
            # baseline must be accounted for across measures
            common_base = {}
            sbmkts_all = {}
            for yr in self.handyvars.aeo_years:
                # Record the baseline microsegments for all
                # measures in the given year (e.g., the current measure being
                # adjusted and those that overlap for the given baseline
                # microsegment), and store in a list
                base_mkts_all = [
                    msegs_meas["energy"]["total"]["baseline"][yr]]
                base_mkts_all.extend([
                    x.markets[adopt_scheme]["mseg_adjust"][
                        "contributing mseg keys and values"][cm_key][
                        "energy"]["total"]["baseline"][yr] for
                    x in overlap_meas])
                # Common baseline is set to the max baseline mseg value across
                # measures (since differences are driven by down-scaling)
                common_base[yr] = max(base_mkts_all)
                # Record the difference between the baseline mseg value of each
                # measure and the common baseline value
                sbmkts_all[yr] = [common_base[yr] - x for x in base_mkts_all]
            # Find total savings of the measure being adjusted
            save_meas = {yr: (
                msegs_meas["energy"]["total"]["baseline"][yr] -
                msegs_meas["energy"]["total"]["efficient"][yr]) for
                yr in self.handyvars.aeo_years}
            # Find total savings of overlapping measure(s); store in list
            save_overlp = {yr: [(
                overlap_meas[x].markets[adopt_scheme]["mseg_adjust"][
                    "contributing mseg keys and values"][cm_key][
                    "energy"]["total"]["baseline"][yr] -
                overlap_meas[x].markets[adopt_scheme]["mseg_adjust"][
                    "contributing mseg keys and values"][cm_key][
                    "energy"]["total"]["efficient"][yr]) for x in range(
                    len(overlap_meas))] for yr in
                self.handyvars.aeo_years}
            # Establish the ratio of the measure's savings in the
            # current microsegment to those of the overlapping measure(s)
            save_wt_meas = {yr: (
                (abs(save_meas[yr]) / (
                    abs(save_meas[yr]) + abs(sum(save_overlp[yr])))) if (
                    abs(save_meas[yr]) + abs(sum(save_overlp[yr]))) != 0
                else 0) for yr in self.handyvars.aeo_years}
            # Establish the ratio of each of the overlapping measure's savings
            # to total savings across the overlapping measures (e.g., excluding
            # the current measure being adjusted)
            save_wt_overlp = {
                yr: [save_overlp[yr][x] / sum(save_overlp[yr]) if
                     sum(save_overlp[yr]) != 0 else 0 for x in range(
                     len(save_overlp[yr]))] for yr in self.handyvars.aeo_years}
            # Calculate overall relative performance of overlapping measures (
            # excluding the current measure being adjusted), relative to the
            # common baseline across all measures being considered
            rp_overlp = {yr: (1 - (
                sum([x * y for x, y in zip(
                    save_wt_overlp[yr], save_overlp[yr])]) / common_base[yr]))
                if common_base[yr] != 0 else 1
                for yr in self.handyvars.aeo_years}
            # If applicable, update the sub-market adjustment for each year
            # in the analysis time horizon
            for yr in self.handyvars.aeo_years:
                # Only update sub-market adjustment in cases where at least
                # one of the measures being compared has a sub-market scaling
                # fraction and it is not the current measure being adjusted
                if sum(sbmkts_all[yr]) != 0 and sbmkts_all[yr][0] == 0:
                    # Determine the total savings for all overlapping measures
                    # that do not have sub-market scaling fractions for the
                    # current microsegment
                    save_overlp_sbmkt = {yr: [
                        save_overlp[yr][(x - 1)] if (sbmkts_all[yr][x] == 0)
                        else 0 for x in range(1, len(sbmkts_all[yr]))]
                        for yr in self.handyvars.aeo_years}
                    # Use the savings of the current measure being adjusted
                    # to determine its share of the common baseline that is
                    # inapplicable due to sub-market scaling across overlapping
                    # measures; if there are no savings to compare, assign
                    # evenly across all measures without sub-market scaling;
                    # handle zero denominator

                    # Ignore numpy divide by zero errors and handle NaNs
                    with numpy.errstate(all='ignore'):
                        try:
                            sbmkt_save_wt_meas = (abs(save_meas[yr]) / (
                                abs(save_meas[yr]) +
                                abs(sum(save_overlp_sbmkt[yr]))))
                        except ZeroDivisionError:
                            sbmkt_save_wt_meas = (
                                1 / len([x for x in sbmkts_all[yr] if x == 0]))
                        # Handle numpy NaNs
                        if not numpy.isfinite(sbmkt_save_wt_meas):
                            sbmkt_save_wt_meas = (
                                1 / len([x for x in sbmkts_all[yr] if x == 0]))

                    # Determine the total fraction of the common baseline
                    # that overlapping measures do not apply to due to
                    # sub-market scaling fractions
                    # Record the savings-based fractions of the current
                    # baseline microsegment for each measure being considered
                    save_all_yr = [save_meas[yr]]
                    save_all_yr.extend(save_overlp[yr])
                    save_all_wts = {
                        yr: [(x / sum(save_all_yr)) if sum(save_all_yr) != 0
                             else (1 / (len(overlap_meas) + 1))
                             for x in save_all_yr]}
                    # Multiply the fractions calculated above by each
                    # measure's inapplicable portion of the common baseline,
                    # and normalize by the common baseline
                    sbmkt_base_frac = sum(
                        [sbmkts_all[yr][x] * save_all_wts[yr][x] for
                         x in range(len(sbmkts_all[yr]))]) / common_base[yr]

                    # Calculate additional fraction of the common baseline to
                    # assign current measure to account for sub-market scaling
                    sbmkt_wt_meas[yr] = sbmkt_save_wt_meas * sbmkt_base_frac
            # Final baseline adjustment factor is determined by the measure's
            # fractional contribution to total overlapping savings, plus
            # any adjustment to account for sub-market scaling across
            # overlapping measures; if the savings fraction is zero, assume
            # even weight across overlapping measures
            base_adj = {
                yr: (save_wt_meas[yr] + sbmkt_wt_meas[yr]) if
                save_wt_meas[yr] != 0 else (
                    1 / (len(overlap_meas) + 1) + sbmkt_wt_meas[yr]) for
                yr in self.handyvars.aeo_years}
            # Final efficient adjustment factor adds multiplication of the
            # relative performance of the overlapping measure(s) to the
            # baseline adjustment calculation
            eff_adj = {yr: (save_wt_meas[yr] + sbmkt_wt_meas[yr]) *
                       rp_overlp[yr] if save_wt_meas[yr] != 0 else (
                        1 / (len(overlap_meas) + 1) + sbmkt_wt_meas[yr]) for
                       yr in self.handyvars.aeo_years}
        # If neither case 1 or 2 above, set baseline/efficient adjustments to 1
        else:
            base_adj, eff_adj = (
              {yr: 1 for yr in self.handyvars.aeo_years} for n in range(2))

        return base_adj, eff_adj

    def make_base_eff_adjs(self, k, cm_key, msegs_meas, base_adj, eff_adj):
        """Apply overlap adjustments for measure mseg in a package.

        Args:
            k (str): Data type indicator ("energy" or "carbon")
            cm_key (tuple): Microsegment key describing the contributing
                microsegment currently being added (e.g. reg->bldg, etc.)
            msegs_meas (dict): Data for the contributing microsegment of an
                individual measure that is being merged into the package.
            base_adj (dict): Overlap adjustments for baseline data.
            eff_adj (dict): Overlap adjustments for efficient data

        Returns:
            Adjusted baseline/efficient energy and carbon data that accounts
            account for overlaps between a given measure and other measures
            in a package.
        """

        # Initialize variables used to track pre-adjusted mseg data
        tot_base_orig, tot_eff_orig, tot_save_orig, tot_base_orig_ecost, \
            tot_eff_orig_ecost, tot_save_orig_ecost = ('' for n in range(6))
        # Create shorthand for stock/energy/carbon/lifetime msegs data
        mseg_adj = msegs_meas[k]
        # Create shorthand for cost data
        mseg_cost_adj = msegs_meas["cost"][k]
        # Total baseline energy/carbon
        tot_base_orig = copy.deepcopy(mseg_adj["total"]["baseline"])
        # Total efficient energy/carbon
        tot_eff_orig = copy.deepcopy(mseg_adj["total"]["efficient"])
        # Total energy/carbon savings
        tot_save_orig = {yr: (
            copy.deepcopy(mseg_adj["total"]["baseline"][yr]) -
            copy.deepcopy(mseg_adj["total"]["efficient"][yr]))
            for yr in self.handyvars.aeo_years}
        # Record total energy cost data before adjustment
        if k == "energy" and mseg_cost_adj:
            # Total baseline energy cost
            tot_base_orig_ecost = copy.deepcopy(
                mseg_cost_adj["total"]["baseline"])
            # Total efficient energy cost
            tot_eff_orig_ecost = copy.deepcopy(
                mseg_cost_adj["total"]["efficient"])
            # Total energy cost savings
            tot_save_orig_ecost = {yr: (
                copy.deepcopy(mseg_cost_adj["total"]["baseline"][yr]) -
                copy.deepcopy(mseg_cost_adj["total"]["efficient"][yr]))
                for yr in self.handyvars.aeo_years}
        # Adjust msegs using base/efficient adjustment fractions
        self.adj_pkg_mseg_keyvals(
            mseg_adj, base_adj, eff_adj, base_eff_flag=None)
        # If applicable, adjust energy/carbon cost msegs
        if mseg_cost_adj:
            self.adj_pkg_mseg_keyvals(
                mseg_cost_adj, base_adj, eff_adj, base_eff_flag=None)

        return mseg_adj, mseg_cost_adj, tot_base_orig, tot_eff_orig, \
            tot_save_orig, tot_base_orig_ecost, tot_eff_orig_ecost, \
            tot_save_orig_ecost

    def find_adj_out_break_cats(
            self, k, cm_key, msegs_ecarb, msegs_ecarb_cost, mseg_out_break_adj,
            tot_base_orig, tot_eff_orig, tot_save_orig, tot_base_orig_ecost,
            tot_eff_orig_ecost, tot_save_orig_ecost, key_list, fuel_switch_to):
        """Adjust output breakouts after removing energy/carbon data overlaps.

        Args:
            k (str): Data type indicator ("energy" or "carbon")
            cm_key (tuple): Microsegment key describing the contributing
                microsegment currently being added (e.g. reg->bldg, etc.)
            msegs_ecarb (dict): Shorthand for energy/carbon data.
            msegs_ecarb_cost (dict): Shorthand for energy/carbon cost data.
            mseg_out_break_adj (dict): Initial output breakout data.
            tot_base_orig (dict): Unadjusted baseline energy/carbon data.
            tot_eff_orig (dict): Unadjusted efficient energy/carbon data.
            tot_save_orig (dict): Unadjusted energy/carbon savings data.
            tot_base_orig_ecost (dict): Unadjusted base energy cost data.
            tot_eff_orig_ecost (dict): Unadjusted efficient energy cost data.
            tot_save_orig_ecost (dict): Unadjusted energy cost savings data.
            key_list (list): List of microsegment keys.
            fuel_switch_to (string): Indicator of which baseline fuel the
                measure switches to (if applicable).

        Returns:
            Updated energy, carbon, and energy cost output breakouts adjusted
            to account for removal of overlaps between measure and other
            measures in a package.
        """

        # Establish applicable climate zone breakout
        for cz in self.handyvars.out_break_czones.items():
            if key_list[1] in cz[1]:
                out_cz = cz[0]
        # Establish applicable building type breakout
        for bldg in self.handyvars.out_break_bldgtypes.items():
            if all([x in bldg[1] for x in [
                    key_list[2], key_list[-1]]]):
                out_bldg = bldg[0]
        # Establish applicable end use breakout
        for eu in self.handyvars.out_break_enduses.items():
            # * Note: The 'other' microsegment end
            # use may map to either the 'Refrigeration' output
            # breakout or the 'Other' output breakout, depending on
            # the technology type specified in the measure
            # definition. Also note that 'supply' side
            # heating/cooling microsegments map to the
            # 'Heating (Equip.)'/'Cooling (Equip.)' end uses, while
            # 'demand' side heating/cooling microsegments map to
            # the 'Heating (Env.)'/'Cooling (Env.) end use, with the
            # exception of 'demand' side heating/cooling microsegments that
            # represent waste heat from lights - these are
            # categorized as part of the 'Lighting' end use
            if key_list[4] == "other":
                if key_list[5] == "freezers":
                    out_eu = "Refrigeration"
                else:
                    out_eu = "Other"
            elif key_list[4] in eu[1]:
                if (eu[0] in ["Heating (Equip.)", "Cooling (Equip.)"] and
                    key_list[5] == "supply") or (
                    eu[0] in ["Heating (Env.)", "Cooling (Env.)"] and
                    key_list[5] == "demand" and key_list[0] == "primary") or (
                    eu[0] not in ["Heating (Equip.)", "Cooling (Equip.)",
                                  "Heating (Env.)", "Cooling (Env.)"]):
                    out_eu = eu[0]
            elif "lighting gain" in key_list:
                out_eu = "Lighting"
        # If applicable, establish fuel type breakout (electric vs.
        # non-electric); note – only applicable to end uses that
        # are at least in part fossil-fired
        if len(self.handyvars.out_break_fuels.keys()) != 0 and out_eu in [
            "Heating (Equip.)", "Cooling (Equip.)", "Heating (Env.)",
                "Cooling (Env.)", "Water Heating", "Cooking"]:
            # Establish breakout of fuel type that is being
            # reduced (e.g., through efficiency or fuel switching
            # away from the fuel)
            for f in self.handyvars.out_break_fuels.items():
                if key_list[3] in f[1]:
                    out_fuel_save = f[0]
            # Establish breakout of fuel type that is being added
            # to via fuel switching, if applicable
            if fuel_switch_to == "electricity" and out_fuel_save != "Electric":
                out_fuel_gain = "Electric"
            elif fuel_switch_to not in [None, "electricity"] and \
                    out_fuel_save == "Electric":
                out_fuel_gain = "Non-Electric"
            else:
                out_fuel_gain = ""
        else:
            out_fuel_save, out_fuel_gain = ("" for n in range(2))

        # Shorthands for data used to adjust original output breakouts
        base_orig, eff_orig, save_orig, base_adj, eff_adj = [
            tot_base_orig, tot_eff_orig, tot_save_orig, msegs_ecarb[
                "total"]["baseline"], msegs_ecarb["total"]["efficient"]]
        # If necessary, shorthands for data used to adjust original cost output
        if all([x for x in [tot_base_orig_ecost, tot_eff_orig_ecost,
                            tot_save_orig_ecost]]):
            # Shorthands for data used to adjust original output breakouts
            base_cost_orig, eff_cost_orig, save_cost_orig, base_cost_adj, \
                eff_cost_adj = [tot_base_orig_ecost, tot_eff_orig_ecost,
                                tot_save_orig_ecost,
                                msegs_ecarb_cost["total"]["baseline"],
                                msegs_ecarb_cost["total"]["efficient"]]

        # Fuel switching case
        if out_fuel_save and out_fuel_gain:
            # Use individual measure fuel splits to determine how much
            # efficient case energy, carbon, and cost remains with the baseline
            # fuel; use absolute values in the split to address the use of
            # negative values to represent fuel additions
            eff_split = {yr: (abs(mseg_out_break_adj[k]["efficient"][
                out_cz][out_bldg][out_eu][out_fuel_save][yr]) / (
                abs(mseg_out_break_adj[k]["efficient"][
                    out_cz][out_bldg][out_eu][out_fuel_gain][yr]) +
                abs(mseg_out_break_adj[k]["efficient"][
                    out_cz][out_bldg][out_eu][out_fuel_save][yr])) if (
                abs(mseg_out_break_adj[k]["efficient"][
                    out_cz][out_bldg][out_eu][out_fuel_gain][yr]) +
                abs(mseg_out_break_adj[k]["efficient"][
                    out_cz][out_bldg][out_eu][out_fuel_save][yr])) != 0 else 1)
                for yr in self.handyvars.aeo_years}
            # Energy/carbon; original fuel
            mseg_out_break_adj[k]["baseline"][
                out_cz][out_bldg][out_eu][out_fuel_save], \
                mseg_out_break_adj[k]["efficient"][
                    out_cz][out_bldg][out_eu][out_fuel_save], \
                mseg_out_break_adj[k]["savings"][
                    out_cz][out_bldg][out_eu][out_fuel_save] = [
                # Remove adjusted baseline
                {yr: mseg_out_break_adj[k]["baseline"][
                    out_cz][out_bldg][out_eu][out_fuel_save][yr] - (
                        base_orig[yr] - base_adj[yr]) for
                 yr in self.handyvars.aeo_years},
                # Remove adjusted efficient case that remains with base fuel
                {yr: mseg_out_break_adj[k]["efficient"][
                    out_cz][out_bldg][out_eu][out_fuel_save][yr] - (
                        eff_orig[yr] - eff_adj[yr]) * eff_split[yr] for
                 yr in self.handyvars.aeo_years},
                # Savings is difference between adjusted baseline and efficient
                # and is subtracted from existing savings for baseline fuel (
                # e.g., savings becomes less positive)
                {yr: mseg_out_break_adj[k]["savings"][
                    out_cz][out_bldg][out_eu][out_fuel_save][yr] - (
                        (base_orig[yr] - base_adj[yr]) -
                        (eff_orig[yr] - eff_adj[yr]) * eff_split[yr]) for
                 yr in self.handyvars.aeo_years}]
            # Energy/carbon; switched to fuel
            mseg_out_break_adj[k]["efficient"][
                out_cz][out_bldg][out_eu][out_fuel_gain], \
                mseg_out_break_adj[k]["savings"][
                    out_cz][out_bldg][out_eu][out_fuel_gain] = [
                # Note: Baseline case remains zero (no baseline before switch)

                # Remove adjusted efficient case that switched from base fuel
                {yr: mseg_out_break_adj[k]["efficient"][
                    out_cz][out_bldg][out_eu][out_fuel_gain][yr] - ((
                        eff_orig[yr] - eff_adj[yr]) * (1 - eff_split[yr])) for
                 yr in self.handyvars.aeo_years},
                # Adjusted efficient is added to the existing savings for
                # baseline fuel (e.g., savings becomes less negative)
                {yr: mseg_out_break_adj[k]["savings"][
                    out_cz][out_bldg][out_eu][out_fuel_gain][yr] + ((
                        eff_orig[yr] - eff_adj[yr]) * (1 - eff_split[yr])) for
                 yr in self.handyvars.aeo_years}]
            # Energy costs
            if all([x for x in [tot_base_orig_ecost, tot_eff_orig_ecost,
                                tot_save_orig_ecost]]):
                # Energy cost; original fuel
                mseg_out_break_adj["cost"]["baseline"][
                    out_cz][out_bldg][out_eu][out_fuel_save], \
                    mseg_out_break_adj["cost"]["efficient"][
                        out_cz][out_bldg][out_eu][out_fuel_save], \
                    mseg_out_break_adj["cost"]["savings"][
                        out_cz][out_bldg][out_eu][out_fuel_save] = [
                    # Remove adjusted baseline
                    {yr: mseg_out_break_adj["cost"]["baseline"][
                        out_cz][out_bldg][out_eu][out_fuel_save][yr] - (
                            base_cost_orig[yr] - base_cost_adj[yr]) for
                     yr in self.handyvars.aeo_years},
                    # Remove adjusted efficient case that remains with base
                    # fuel
                    {yr: mseg_out_break_adj["cost"]["efficient"][
                        out_cz][out_bldg][out_eu][out_fuel_save][yr] - (
                            eff_cost_orig[yr] - eff_cost_adj[yr]) *
                     eff_split[yr] for yr in self.handyvars.aeo_years},
                    # Adjusted savings is difference between adjusted baseline
                    # and efficient and is subtracted from existing savings for
                    # baseline fuel (e.g., savings becomes less positive)
                    {yr: mseg_out_break_adj["cost"]["savings"][
                        out_cz][out_bldg][out_eu][out_fuel_save][yr] - (
                            (base_cost_orig[yr] - base_cost_adj[yr]) -
                            (eff_cost_orig[yr] - eff_cost_adj[yr]) *
                     eff_split[yr]) for yr in self.handyvars.aeo_years}]
                # Switched to fuel
                mseg_out_break_adj["cost"]["efficient"][
                    out_cz][out_bldg][out_eu][out_fuel_gain], \
                    mseg_out_break_adj["cost"]["savings"][
                        out_cz][out_bldg][out_eu][out_fuel_gain] = [
                    # Note: Baseline case remains zero (no baseline before
                    # switch)

                    # Remove adjusted efficient case that switched from base
                    # fuel
                    {yr: mseg_out_break_adj["cost"]["efficient"][
                        out_cz][out_bldg][out_eu][out_fuel_gain][yr] - ((
                            eff_cost_orig[yr] - eff_cost_adj[yr]) * (
                            1 - eff_split[yr])) for
                     yr in self.handyvars.aeo_years},
                    # Adjusted efficient is added to the existing savings for
                    # baseline fuel (e.g., savings becomes less negative)
                    {yr: mseg_out_break_adj["cost"]["savings"][
                        out_cz][out_bldg][out_eu][out_fuel_gain][yr] + ((
                            eff_cost_orig[yr] - eff_cost_adj[yr]) * (
                            1 - eff_split[yr])) for
                     yr in self.handyvars.aeo_years}]
        # Fuel splits without fuel switching
        elif out_fuel_save:
            # Energy/carbon
            mseg_out_break_adj[k]["baseline"][
                out_cz][out_bldg][out_eu][out_fuel_save], \
                mseg_out_break_adj[k]["efficient"][
                    out_cz][out_bldg][out_eu][out_fuel_save], \
                mseg_out_break_adj[k]["savings"][
                    out_cz][out_bldg][out_eu][out_fuel_save] = [
                # Remove adjusted baseline
                {yr: mseg_out_break_adj[k]["baseline"][
                    out_cz][out_bldg][out_eu][out_fuel_save][yr] - (
                        base_orig[yr] - base_adj[yr]) for
                    yr in self.handyvars.aeo_years},
                # Remove adjusted efficient
                {yr: mseg_out_break_adj[k]["efficient"][
                    out_cz][out_bldg][out_eu][out_fuel_save][yr] - (
                        eff_orig[yr] - eff_adj[yr]) for
                 yr in self.handyvars.aeo_years},
                # Adjusted savings is difference between adjusted
                # baseline/efficient
                {yr: mseg_out_break_adj[k]["savings"][
                    out_cz][out_bldg][out_eu][out_fuel_save][yr] - (
                    save_orig[yr] - (base_adj[yr] - eff_adj[yr])) for
                 yr in self.handyvars.aeo_years}]
            # Energy costs
            if all([x for x in [tot_base_orig_ecost, tot_eff_orig_ecost,
                                tot_save_orig_ecost]]):
                mseg_out_break_adj["cost"]["baseline"][
                    out_cz][out_bldg][out_eu][out_fuel_save], \
                    mseg_out_break_adj["cost"]["efficient"][
                        out_cz][out_bldg][out_eu][out_fuel_save], \
                    mseg_out_break_adj["cost"]["savings"][
                        out_cz][out_bldg][out_eu][out_fuel_save] = [
                    # Remove adjusted baseline
                    {yr: mseg_out_break_adj["cost"]["baseline"][
                            out_cz][out_bldg][out_eu][out_fuel_save][yr] - (
                        base_cost_orig[yr] - base_cost_adj[yr]) for
                     yr in self.handyvars.aeo_years},
                    # Remove adjusted efficient
                    {yr: mseg_out_break_adj["cost"]["efficient"][
                        out_cz][out_bldg][out_eu][out_fuel_save][yr] - (
                        eff_cost_orig[yr] - eff_cost_adj[yr]) for
                     yr in self.handyvars.aeo_years},
                    # Adjusted savings is difference between adjusted
                    # baseline/efficient
                    {yr: mseg_out_break_adj["cost"]["savings"][
                        out_cz][out_bldg][out_eu][out_fuel_save][yr] - (
                        save_cost_orig[yr] - (
                            base_cost_adj[yr] - eff_cost_adj[yr])) for
                     yr in self.handyvars.aeo_years}]
        # All other cases
        else:
            # Energy/carbon
            mseg_out_break_adj[k]["baseline"][out_cz][out_bldg][out_eu], \
                mseg_out_break_adj[k]["efficient"][out_cz][out_bldg][out_eu], \
                mseg_out_break_adj[k]["savings"][out_cz][out_bldg][out_eu] = [
                # Remove adjusted baseline
                {yr: mseg_out_break_adj[k]["baseline"][
                    out_cz][out_bldg][out_eu][yr] - (
                        base_orig[yr] - base_adj[yr]) for
                    yr in self.handyvars.aeo_years},
                # Remove adjusted efficient
                {yr: mseg_out_break_adj[k]["efficient"][
                    out_cz][out_bldg][out_eu][yr] - (
                        eff_orig[yr] - eff_adj[yr]) for
                 yr in self.handyvars.aeo_years},
                # Adjusted savings is difference between adjusted
                # baseline/efficient
                {yr: mseg_out_break_adj[k]["savings"][
                    out_cz][out_bldg][out_eu][yr] - (
                    save_orig[yr] - (base_adj[yr] - eff_adj[yr])) for
                 yr in self.handyvars.aeo_years}]
            # Energy costs
            if all([x for x in [tot_base_orig_ecost, tot_eff_orig_ecost,
                                tot_save_orig_ecost]]):
                mseg_out_break_adj["cost"]["baseline"][
                    out_cz][out_bldg][out_eu], \
                    mseg_out_break_adj["cost"]["efficient"][
                        out_cz][out_bldg][out_eu], \
                    mseg_out_break_adj["cost"]["savings"][
                        out_cz][out_bldg][out_eu] = [
                    # Remove adjusted baseline
                    {yr: mseg_out_break_adj["cost"]["baseline"][
                            out_cz][out_bldg][out_eu][yr] - (
                        base_cost_orig[yr] - base_cost_adj[yr]) for
                     yr in self.handyvars.aeo_years},
                    # Remove adjusted efficient
                    {yr: mseg_out_break_adj["cost"]["efficient"][
                        out_cz][out_bldg][out_eu][yr] - (
                        eff_cost_orig[yr] - eff_cost_adj[yr]) for
                     yr in self.handyvars.aeo_years},
                    # Adjusted savings is difference between adjusted
                    # baseline/efficient
                    {yr: mseg_out_break_adj["cost"]["savings"][
                        out_cz][out_bldg][out_eu][yr] - (
                        save_cost_orig[yr] - (
                            base_cost_adj[yr] - eff_cost_adj[yr])) for
                     yr in self.handyvars.aeo_years}]

        return mseg_out_break_adj

    def update_dict(self, dict1, dict2):
        """Merge data from one dict into another dict.

        Note:
            Adds all branches in the second dict that are not already in
            the first dict to the first dict, given that the first dict
            is either blank or includes data nested under keys that include
            'primary' or 'secondary' (indicating the intended level of the
            data merge).

        Args:
            dict1 (dict): Dict to merge data into.
            dict2 (dict): Dict to merge data from.
        """
        # If the first dict is nested and the intended level of the data
        # merge has not yet been reached, proceed further down its branches
        if len(dict1.keys()) != 0 and all([
                "," not in x for x in dict1.keys()]):
            for (k, i), (k2, i2) in zip(
                    dict1.items(), dict2.items()):
                self.update_dict(i, i2)
        # If the first dict is not nested, or the dict is nested but the
        # intended level of the data merge has been reached, merge the
        # second dict's data into the first dict
        else:
            dict1.update(dict2)

    def apply_pkg_benefits(
            self, msegs_meas, adopt_scheme, sect_shapes_meas, cm_key):
        """Apply additional energy savings or cost benefits from packaging.

        Attributes:
            msegs_meas (dict): Data for the contributing microsegment of an
                individual measure that is being merged into the package.
            adopt_scheme (string): Assumed consumer adoption scenario.
            sect_shapes_meas (dict or NoneType): Sector-level baseline and
                efficient load shape information for the current contributing
                microsegment, if applicable (otherwise, None).
            cm_key (tuple): Microsegment key describing the contributing
                microsegment currently being added (e.g. reg->bldg, etc.)

        Note:
            Users may define additional percent energy savings improvements or
            installed cost reductions for a measure package; this function
            applies those benefits to the package's energy, carbon, and cost
            data.

        Args:
            msegs_meas (dict): Original energy, carbon, and cost data to
                apply packaging benefits to (if applicable)

        Returns:
            Updated energy, carbon, and cost data for the packaged measure
            that reflects the additional user-defined energy savings and
            installed cost benefits for the package.
        """
        # Set additional energy savings and cost benefits defined by the user
        # for the current package being updated
        energy_ben = self.benefits["energy savings increase"]
        cost_ben = self.benefits["cost reduction"]

        # If additional energy savings benefits are not None and are non-zero,
        # apply them to the measure's energy, carbon, and energy/carbon costs
        if energy_ben not in [None, 0]:
            for x in ["energy", "carbon"]:
                for cs in ["competed", "total"]:
                    # Set short variable names for baseline and efficient
                    # energy and carbon data
                    base = msegs_meas[x][cs]["baseline"]
                    eff = msegs_meas[x][cs]["efficient"]
                    # Apply the additional energy savings % benefit to the
                    # efficient energy and carbon data (disallow result
                    # below zero)
                    msegs_meas[x][cs]["efficient"] = {
                        key: 0 if (
                            not isinstance(eff[key], numpy.ndarray) and
                            eff[key] > 0 and (base[key] - eff[key]) *
                            energy_ben > eff[key]) or (
                            isinstance(eff[key], numpy.ndarray) and
                            all([x > 0 for x in eff[key]]) and
                            all(((base[key] - x) * energy_ben > x) for
                                x in eff[key]))
                        else eff[key] - (base[key] - eff[key]) * energy_ben
                        for key in self.handyvars.aeo_years}
                    # Set short variable names for baseline and efficient
                    # energy and carbon cost data
                    base_c = msegs_meas["cost"][x][cs]["baseline"]
                    eff_c = msegs_meas["cost"][x][cs]["efficient"]
                    # Apply the additional energy savings % benefit to the
                    # efficient energy and carbon cost data (disallow result
                    # below zero)
                    msegs_meas["cost"][x][cs]["efficient"] = {
                        key: 0 if (
                            not isinstance(eff_c[key], numpy.ndarray) and
                            eff_c[key] > 0 and (base_c[key] - eff_c[key]) *
                            energy_ben > eff_c[key]) or (
                            isinstance(eff_c[key], numpy.ndarray) and
                            all([x > 0 for x in eff_c[key]]) and
                            all(((base_c[key] - x) * energy_ben > x) for
                                x in eff_c[key]))
                        else eff_c[key] - (base_c[key] - eff_c[key]) *
                        energy_ben for key in self.handyvars.aeo_years}
                # Adjust sector-level energy load shapes for the current mseg
                # to reflect additional energy performance benefits, if needed
                if x == "energy" and self.sector_shapes:
                    # Translate mseg key string to list elements
                    key_list = literal_eval(cm_key)
                    # Pull out EMM region from the contributing mseg info.
                    reg = key_list[1]
                    # Loop through all years with sector-level load data
                    for yr in self.handyvars.aeo_years_summary:
                        # Shorthand for baseline values
                        base_s = sect_shapes_meas[cm_key][yr]["baseline"]
                        # Shorthand for efficient values
                        eff_s = sect_shapes_meas[cm_key][yr]["efficient"]
                        save_s = [x - y for x, y in zip(base_s, eff_s)]
                        # Adjust efficient values to reflect additional
                        # performance benefits
                        self.sector_shapes[adopt_scheme][reg][yr][
                            "efficient"] = [y - x * energy_ben if (
                                (y - x * energy_ben) >= 0) else
                                0 for x, y in zip(save_s, self.sector_shapes[
                                    adopt_scheme][reg][yr]["efficient"])]

        # If additional installed cost benefits are not None and are non-zero,
        # apply them to the measure's stock cost
        if cost_ben not in [None, 0]:
            for cs in ["competed", "total"]:
                msegs_meas["cost"]["stock"][cs]["efficient"] = {
                    key: msegs_meas["cost"]["stock"][cs]["efficient"][key] *
                    (1 - cost_ben) for key in self.handyvars.aeo_years}

        return msegs_meas

    def merge_out_break(self, pkg_brk, meas_brk):
        """Merge output breakout data for an individual measure into a package.

        Note:
            The 'markets' attribute of an individual measure to be merged
            into a package includes partitioning fractions needed to breakout
            the measure's output markets/savings by key variables (e.g.,
            climate zone, building type, end use, etc.). These fractions are
            based on the portion of the measure's total energy use market that
            is attributable to each breakout variable (e.g., 50% of the
            measure's total energy market is attributed to the heating end
            use). This function unnormalizes the measure's breakout fractions
            and adds the resultant energy use sub-market to a new set of
            breakout information for a measure package. Output breakout dicts
            must be identically structured for the merge to work.

        Args:
            pkg_brk (dict): Packaged measure output breakout information to
                merge individual measure breakout information into.
            meas_brk (dict): Individual measure output breakout information
                to merge into the package breakout information.

        Returns:
            Updated output breakout information for the packaged measure
            that incorporates the individual measure's breakout information.
        """
        for (k, i), (k2, i2) in zip(
                sorted(pkg_brk.items()), sorted(meas_brk.items())):
            if isinstance(i2, dict) and (
                    sorted(list(i2.keys())) != self.handyvars.aeo_years):
                self.merge_out_break(i, i2)
            else:
                if k == k2 and (isinstance(i, dict) == isinstance(i2, dict)):
                    # If individual measure output breakout data is
                    # available to add to the current terminal leaf
                    # node for the package, either set the leaf node value
                    # to the unnormalized breakout data if no data already
                    # exist, or otherwise add the unnormalized breakout data
                    # for the individual measure to that of the package
                    if len(i.keys()) == 0:
                        pkg_brk[k] = {yr: i2[yr] for
                                      yr in self.handyvars.aeo_years}
                    else:
                        pkg_brk[k] = {yr: pkg_brk[k][yr] + i2[yr] for
                                      yr in self.handyvars.aeo_years}
                else:
                    raise KeyError(
                        "Output data dicts to merge for ECM '" + self.name +
                        " are not identically structured")
        return pkg_brk


def prepare_measures(measures, convert_data, msegs, msegs_cpl, handyvars,
                     handyfiles, cbecs_sf_byvint, tsv_data, base_dir, opts,
                     regions, tsv_metrics, contrib_meas_pkg):
    """Finalize measure markets for subsequent use in the analysis engine.

    Note:
        Determine which in a list of measures require updates to finalize
        stock, energy, carbon, and cost markets for further use in the
        analysis engine; instantiate these measures as Measure objects;
        execute the necessary updates for each object; and update the
        original list of measures accordingly.

    Args:
        measures (list): List of dicts with efficiency measure attributes.
        convert_data (dict): Measure cost unit conversion data.
        msegs (dict): Baseline microsegment stock and energy use.
        msegs_cpl (dict): Baseline technology cost, performance, and lifetime.
        handyvars (object): Global variables of use across Measure methods.
        handyfiles (object): Input files of use across Measure methods.
        cbecs_sf_byvint (dict): Commercial square footage by vintage data.
        tsv_data (dict): Data needed for time sensitive efficiency valuation.
        base_dir (string): Base directory.
        opts (object): Stores user-specified execution options.
        regions (string): Regional breakouts to use.
        tsv_metrics (boolean or list): TSV metrics settings.
        contrib_meas_pkg (list): Names of measures that contribute to pkgs.

    Returns:
        A list of dicts, each including a set of measure attributes that has
        been prepared for subsequent use in the analysis engine.

    Raises:
        ValueError: If more than one Measure object matches the name of a
            given input efficiency measure.
    """
    # Initialize Measure() objects based on 'measures_update' list
    meas_update_objs = [Measure(
        base_dir, handyvars, handyfiles, opts.site_energy,
        opts.captured_energy, regions, tsv_metrics, opts.health_costs,
        opts.split_fuel, **m) for m in measures]

    # Fill in EnergyPlus-based performance information for Measure objects
    # with a 'From EnergyPlus' flag in their 'energy_efficiency' attribute

    # Handle a superfluous 'undefined' key in the ECM performance field that is
    # generated by the 'Add ECM' web form in certain cases *** NOTE: WILL
    # FIX IN FUTURE UI VERSION ***
    if any([isinstance(m.energy_efficiency, dict) and (
        "undefined" in m.energy_efficiency.keys() and
        m.energy_efficiency["undefined"] == "From EnergyPlus") for
            m in meas_update_objs]):
        # NOTE: Comment out operations related to the import of ECM performance
        # data from EnergyPlus and yield an error until these operations are
        # fully supported in the future

        # Set default directory for EnergyPlus simulation output files
        # eplus_dir = base_dir + '/ecm_definitions/energyplus_data'
        # # Set EnergyPlus global variables
        # handyeplusvars = EPlusGlobals(eplus_dir, cbecs_sf_byvint)
        # # Fill in EnergyPlus-based measure performance information
        # [m.fill_eplus(
        #     msegs, eplus_dir, handyeplusvars.eplus_coltypes,
        #     handyeplusvars.eplus_files, handyeplusvars.eplus_vintage_weights,
        #     handyeplusvars.eplus_basecols) for m in meas_update_objs
        #     if 'EnergyPlus file' in m.energy_efficiency.keys()]
        raise ValueError(
            'One or more ECMs require EnergyPlus data for ECM performance; '
            'EnergyPlus-based ECM performance data are currently unsupported.')

    # Finalize 'markets' attribute for all Measure objects
    [m.fill_mkts(
        msegs, msegs_cpl, convert_data, tsv_data, opts, contrib_meas_pkg)
     for m in meas_update_objs]

    return meas_update_objs


def prepare_packages(packages, meas_update_objs, meas_summary,
                     handyvars, handyfiles, base_dir, opts,
                     regions, tsv_metrics):
    """Combine multiple measures into a single packaged measure.

    Args:
        packages (dict): Names of packages and measures that comprise them.
        meas_update_objs (dict): Attributes of individual efficiency measures.
        meas_summary (): List of dicts including previously prepared ECM data.
        handyvars (object): Global variables of use across Measure methods.
        handyfiles (object): Input files of use across Measure methods.
        base_dir (string): Base directory.
        opts (object): Stores user-specified execution options.
        regions (string): Regional breakouts to use.
        tsv_metrics (boolean or list): TSV metrics settings.

    Returns:
        A dict with packaged measure attributes that can be added to the
        existing measures database.
    """
    # Run through each unique measure package and merge the measures that
    # contribute to this package
    for p in packages:
        # Notify user that measure is being updated
        print("Updating ECM '" + p["name"] + "'...", end="", flush=True)

        # Establish a list of names for measures that contribute to the
        # package
        package_measures = p["contributing_ECMs"]
        # Determine the subset of all previously initialized measure
        # objects that contribute to the current package
        measure_list_package = [
            x for x in meas_update_objs if x.name in package_measures]
        # Determine which contributing measures have not yet been
        # initialized as objects
        measures_to_add = [mc for mc in package_measures if mc not in [
            x.name for x in measure_list_package]]
        # Initialize any missing contributing measure objects and add to
        # the existing list of contributing measure objects for the package
        for m in measures_to_add:
            # Load and set high level summary data for the missing measure
            meas_summary_data = [x for x in meas_summary if x["name"] == m]
            if len(meas_summary_data) == 1:
                # Initialize the missing measure as an object
                meas_obj = Measure(
                    base_dir, handyvars, handyfiles, opts.site_energy,
                    opts.captured_energy, regions, tsv_metrics,
                    opts.health_costs, opts.split_fuel, **meas_summary_data[0])
                # Reset measure technology type and total energy (used to
                # normalize output breakout fractions) to their values in the
                # high level summary data (reformatted during initialization)
                meas_obj.technology_type = meas_summary_data[0][
                    "technology_type"]
                # Assemble folder path for measure competition data
                meas_folder_name = path.join(*handyfiles.ecm_compete_data)
                # Assemble file name for measure competition data
                meas_file_name = meas_obj.name + ".pkl.gz"
                # Load and set competition data for the missing measure object
                with gzip.open(path.join(base_dir, meas_folder_name,
                                         meas_file_name), 'r') as zp:
                    try:
                        meas_comp_data = pickle.load(zp)
                    except Exception as e:
                        raise Exception(
                            "Error reading in competition data of " +
                            "contributing ECM '" + meas_obj.name +
                            "' for package '" + p["name"] + "': " +
                            str(e)) from None
                for adopt_scheme in handyvars.adopt_schemes:
                    meas_obj.markets[adopt_scheme]["master_mseg"] = \
                        meas_summary_data[0]["markets"][adopt_scheme][
                            "master_mseg"]
                    meas_obj.markets[adopt_scheme]["mseg_adjust"] = \
                        meas_comp_data[adopt_scheme]
                    meas_obj.markets[adopt_scheme]["mseg_out_break"] = \
                        meas_summary_data[0]["markets"][adopt_scheme][
                            "mseg_out_break"]
                # Add missing measure object to the existing list
                measure_list_package.append(meas_obj)
            # Raise an error if no existing data exist for the missing
            # contributing measure
            elif len(meas_summary_data) == 0:
                raise ValueError(
                    "Contributing ECM '" + m +
                    "' cannot be added to package '" + p["name"] +
                    "' due to missing attribute data for this ECM")
            else:
                raise ValueError(
                    "More than one set of attribute data for " +
                    "contributing ECM '" + m + "'; ECM cannot be added to" +
                    "package '" + p["name"])

        # Determine which (if any) measure objects that contribute to
        # the package are invalid due to unacceptable input data sourcing
        measure_list_package_rmv = [
            x for x in measure_list_package if x.remove is True]

        # Warn user of no valid measures to package
        if len(measure_list_package_rmv) > 0:
            warnings.warn("WARNING (CRITICAL): Package '" + p["name"] +
                          "' removed due to invalid contributing ECM(s)")
            packaged_measure = False
        # Update package if valid contributing measures are available
        else:
            # Instantiate measure package object based on packaged measure
            # subset above
            packaged_measure = MeasurePackage(
                measure_list_package, p["name"], p["benefits"],
                handyvars, handyfiles, opts)
            # Record heating/cooling overlaps in package
            packaged_measure.htcl_adj_rec()
            # Merge measures in the package object
            packaged_measure.merge_measures(opts)
            # Print update on measure status
            print("Success")

        # Add the new packaged measure to the measure list (if it exists)
        # for further evaluation like any other regular measure
        if packaged_measure is not False:
            meas_update_objs.append(packaged_measure)

    return meas_update_objs


def split_clean_data(meas_prepped_objs):
    """Reorganize and remove data from input Measure objects.

    Note:
        The input Measure objects have updated data, which must
        be reorganized/condensed for the purposes of writing out
        to JSON files.

    Args:
        meas_prepped_objs (object): Measure objects with data to
            be split in to separate dicts or removed.

    Returns:
        Two lists of dicts, one containing competition data for
        each updated measure, and one containing high level summary
        data for each updated measure.
    """
    # Initialize lists of measure competition/summary data
    meas_prepped_compete = []
    meas_prepped_summary = []
    # Loop through all Measure objects and reorganize/remove the
    # needed data.
    for m in meas_prepped_objs:
        # Initialize a reorganized measure competition data dict
        comp_data_dict = {}
        # Retrieve measure contributing microsegment data that
        # is relevant to markets competition in the analysis
        # engine, then remove these data from measure object
        for adopt_scheme in m.handyvars.adopt_schemes:
            # Delete contributing microsegment data that are
            # not relevant to competition in the analysis engine
            del m.markets[adopt_scheme]["mseg_adjust"][
                "secondary mseg adjustments"]["sub-market"]
            del m.markets[adopt_scheme]["mseg_adjust"][
                "secondary mseg adjustments"]["stock-and-flow"]
            # Add remaining contributing microsegment data to
            # competition data dict, then delete from measure
            comp_data_dict[adopt_scheme] = \
                m.markets[adopt_scheme]["mseg_adjust"]
            del m.markets[adopt_scheme]["mseg_adjust"]
        # Append updated competition data from measure to
        # list of competition data across all measures
        meas_prepped_compete.append(comp_data_dict)
        # Delete 'handyvars' measure attribute (not relevant to
        # analysis engine)
        del m.handyvars
        # Delete 'tsv_features' and 'sector_shapes_pkg' measure attributes
        # (not relevant) for individual measures
        if not isinstance(m, MeasurePackage):
            del m.tsv_features
            del m.sector_shapes_pkg
        # For measure packages, replace 'contributing_ECMs'
        # objects list with a list of these measures' names and remove
        # unnecessary heating/cooling equip/env overlap data
        if isinstance(m, MeasurePackage):
            m.contributing_ECMs = [
                x.name for x in m.contributing_ECMs]
            del m.htcl_ECMs
            del m.htcl_overlaps
        # Append updated measure __dict__ attribute to list of
        # summary data across all measures
        meas_prepped_summary.append(m.__dict__)

    return meas_prepped_compete, meas_prepped_summary


def custom_formatwarning(msg, *a):
    """Given a warning object, return only the warning message."""
    return str(msg) + '\n'


def verboseprint(verbose, msg):
    """Print input message when the code is run in verbose mode.

    Args:
        verbose (boolean): Indicator of verbose mode
        msg (string): Message to print to console when in verbose mode

    Returns:
        Printed console message when code is run in verbose mode.
    """
    print(msg) if verbose else lambda *a, **k: None


def tsv_cost_carb_yrmap(tsv_data, aeo_years):
    """Map 8760 TSV cost/carbon data years to AEO years.

    Args:
        tsv_data: TSV cost or carbon input datasets.
        aeo_years: AEO year range.

    Returns:
        Mapping between TSV cost/carbon data years and AEO years.
    """

    # Set up a matrix mapping each AEO year to the years available in the
    # TSV data

    # Pull available years from TSV data
    tsv_yrs = list(sorted(tsv_data.keys()))
    # Establish the mapping from available TSV years to AEO years
    tsv_yr_map = {
        yr_tsv: [str(x) for x in range(
            int(yr_tsv), int(tsv_yrs[ind + 1]))]
        if (ind + 1) < len(tsv_yrs) else [str(x) for x in range(
            int(yr_tsv), int(aeo_years[-1]) + 1)]
        for ind, yr_tsv in enumerate(tsv_yrs)
    }
    # Prepend AEO years preceding the start year in the TSV data, if needed
    if (aeo_years[0] not in tsv_yr_map[tsv_yrs[0]]):
        yrs_to_prepend = range(int(aeo_years[0]), min([
            int(x) for x in tsv_yr_map[tsv_yrs[0]]]))
        tsv_yr_map[tsv_yrs[0]] = [str(x) for x in yrs_to_prepend] + \
            tsv_yr_map[tsv_yrs[0]]

    return tsv_yr_map


def main(base_dir):
    """Import and prepare measure attributes for analysis engine.

    Note:
        Determine which measure definitions in an 'ecm_definitions'
        sub-folder are new or edited; prepare the cost, performance, and
        markets attributes for these measures for use in the analysis
        engine; and write prepared data to analysis engine input files.

    Args:
        base_dir (string): Root Scout directory.
    """
    # If a user has specified the use of an alternate regional breakout
    # than the AIA climate zones, prompt the user to directly select that
    # alternate regional breakout. Currently the only alternate is NEMS EMM.
    if opts.alt_regions is True:
        input_var = 0
        # Determine the regional breakdown to use (NEMS EMM (1) vs. State (2)
        # vs. AIA (3))
        while input_var not in ['1', '2', '3']:
            input_var = input(
                "Enter 1 to use an EIA NEMS Electricity Market Module (EMM) "
                "geographical breakdown,\n 2 to use a state geographical "
                "breakdown,\n or 3 to use an AIA climate zone"
                " geographical breakdown: ")
            if input_var not in ['1', '2', '3']:
                print('Please try again. Enter either 1, 2, or 3. '
                      'Use ctrl-c to exit.')
        if input_var == '1':
            regions = "EMM"
        elif input_var == '2':
            regions = "State"
        else:
            regions = "AIA"
    else:
        regions = "AIA"

    # Screen for cases where user desires time-sensitive valuation metrics
    # or hourly sector-level load shapes but EMM regions are not used (such
    # options require baseline data to be resolved by EMM region)
    if regions != "EMM" and any([
            x is True for x in [opts.tsv_metrics, opts.sect_shapes]]):
        opts.alt_regions, regions = [True, "EMM"]
        # Craft custom warning message based on the option provided
        if all([x is True for x in [opts.tsv_metrics, opts.sect_shapes]]):
            warn_text = "tsv metrics and sector-level 8760 savings shapes"
        elif opts.tsv_metrics is True:
            warn_text = "tsv metrics"
        else:
            warn_text = "sector-level 8760 load shapes"
        warnings.warn(
            "WARNING: Analysis regions were set to EMM to allow " +
            warn_text + ": ensure that ECM data reflect these EMM regions "
            "(and not the default AIA regions)")

    # If a user wishes to change the outputs to metrics relevant for
    # time-sensitive efficiency valuation, prompt them for information needed
    # to reach the desired metric type
    if opts and opts.tsv_metrics is True:
        # Determine the desired output type (change in energy, power)
        output_type = input(
            "Enter the type of time-sensitive metric desired "
            "(1 = change in energy (e.g., multiple hour GWh), "
            "2 = change in power (e.g., single hour GW)): ")

        # Determine the hourly range to restrict results to (24h, peak, take)
        hours = input(
            "Enter the daily hour range to restrict to (1 = all hours, "
            "2 = peak demand period hours, 3 = low demand period hours): ")

        # If peak/take hours are chosen, determine whether total or net
        # system shapes should be used to determine the hour ranges
        if hours == '2' or hours == '3':
            sys_shape = input(
                "Enter the basis for determining peak or low demand hour "
                "ranges: 1 = total system load (reference case), 2 = total "
                "system load (high renewables case), 3 = total system load "
                "net renewables (reference case), 4 = total system load "
                "net renewables (high renewables case): "
                )
        else:
            sys_shape = '0'

        # Determine the season to restrict results to (summer, winter,
        # intermediate)
        season = input(
            "Enter the desired season of focus (1 = summer, "
            "2 = winter, 3 = intermediate): ")

        # Determine desired calculations (dependent on output type) for given
        # flexibility mode, output type, and temporal boundaries

        # Energy output case (multiple hours)
        if output_type == '1':
            # Sum/average energy change across all hours
            if hours == '1':
                calc_type = input(
                    "Enter calculation type (1 = sum across all "
                    "hours, 2 = daily average): ")
            # Sum/average energy change across peak hours
            elif hours == '2':
                calc_type = input(
                    "Enter calculation type (1 = sum across peak "
                    "hours, 2 = daily peak period average): ")
            # Sum/average energy change across take hours
            elif hours == '3':
                calc_type = input(
                    "Enter calculation type (1 = sum across low demand "
                    "hours, 2 = daily low demand period average): ")
        # Power output case (single hour)
        else:
            # Max/average power change across all hours
            if hours == '1':
                calc_type = input(
                    "Enter calculation type (1 = peak day maximum, "
                    "2 = daily hourly average): ")
            # Max/average power change across peak hours
            elif hours == '2':
                calc_type = input(
                    "Enter calculation type (1 = peak day, peak period "
                    "maximum, 2 = daily peak period hourly average): ")
            # Max/average power change across take hours
            elif hours == '3':
                calc_type = input(
                    "Enter calculation type (1 = peak day, low demand period "
                    "maximum, 2 = daily low demand period hourly average): ")
        # Determine the day type to average over (if needed)
        if output_type == '1' or calc_type == '2':
            day_type = input(
                "Enter day type to calculate across (1 = all days, "
                "2 = weekdays, 3 = weekends): ")
        else:
            day_type = "0"

        # Summarize user TSV metric settings in a single dict for further use
        tsv_metrics = [
            output_type, hours, season, calc_type, sys_shape, day_type]
    else:
        tsv_metrics = None

    # Ensure that if public cost health data are to be applied, EMM regional
    # breakouts are set (health data use this resolution)
    if opts and opts.health_costs is True and regions != "EMM":
        opts.alt_regions, regions = [True, "EMM"]
        warnings.warn(
            "WARNING: Analysis regions were set to EMM to allow public health "
            "cost adders: ensure that ECM data reflect these EMM regions "
            "(and not the default AIA regions)")

    # Custom format all warning messages (ignore everything but
    # message itself) *** Note: sometimes yields error; investigate ***
    # warnings.formatwarning = custom_formatwarning
    # Instantiate useful input files object
    handyfiles = UsefulInputFiles(
        opts.captured_energy, regions, opts.site_energy)

    # UNCOMMENT WITH ISSUE 188
    # # Ensure that all AEO-based JSON data are drawn from the same AEO version
    # if len(numpy.unique([splitext(x)[0][-4:] for x in [
    #         handyfiles.msegs_in, handyfiles.msegs_cpl_in,
    #         handyfiles.metadata]])) > 1:
    #     raise ValueError("Inconsistent AEO version used across input files")

    # Instantiate useful variables object
    handyvars = UsefulVars(
        base_dir, handyfiles, regions, tsv_metrics, opts.health_costs,
        opts.split_fuel)

    # Import file to write prepared measure attributes data to for
    # subsequent use in the analysis engine (if file does not exist,
    # provide empty list as substitute, since file will be created
    # later when writing ECM data)
    try:
        es = open(path.join(base_dir, *handyfiles.ecm_prep), 'r')
        try:
            meas_summary = json.load(es)
        except ValueError as e:
            raise ValueError(
                "Error reading in '" + handyfiles.ecm_prep +
                "': " + str(e)) from None
        es.close()
    except FileNotFoundError:
        meas_summary = []

    # Import packages JSON
    with open(path.join(base_dir, *handyfiles.ecm_packages), 'r') as mpk:
        try:
            meas_toprep_package_init = json.load(mpk)
        except ValueError as e:
            raise ValueError(
                "Error reading in ECM package '" + handyfiles.ecm_packages +
                "': " + str(e)) from None

    # Determine which individual and package measure definitions
    # require further preparation for use in the analysis engine

    # Find individual measure definitions that are new (e.g., they have
    # not already been fully prepared for use in the analysis engine) or
    # have been edited since last the 'ecm_prep.py' routine was run

    # Determine full list of individual measure JSON names
    meas_toprep_indiv_names = [
        x for x in listdir(handyfiles.indiv_ecms) if x.endswith(".json") and
        'package' not in x]
    # Initialize list of individual measures to prepare
    meas_toprep_indiv = []
    # Import all individual measure JSONs
    for mi in meas_toprep_indiv_names:
        with open(path.join(base_dir, handyfiles.indiv_ecms, mi), 'r') as jsf:
            try:
                # Load each JSON into a dict
                meas_dict = json.load(jsf)
                # Determine whether dict should be added to list of measure
                # definitions to update. Add a measure dict to the list
                # requiring further prepartion if: a) measure name is not
                # already included in database of prepared measure attributes
                # ('ecm_prep.json'); b) measure does not already have
                # competition data prepared for it (in
                # '/supporting_data/ecm_competition_data' folder), or
                # c) measure JSON time stamp indicates it has been modified
                # since the last run of 'ecm_prep.py' or d) the user added/
                # removed the "site_energy," "captured_energy", "alt_regions",
                # "tsv_metrics", "health_costs", or "split_fuel" cmd line
                # arguments and the measure def. was not already prepared using
                # these settings or e) the user added the "sect_shapes" cmd
                # line argument and the measure does not already have
                # sector-level load shape data or f) the user specified the
                # "sect_shapes" cmd line argument with a package present, and
                # the measure contributes to the package (measure information
                # needed to generate sector shapes for the package was not
                # previously written out and must be regenerated)
                if all([meas_dict["name"] != y["name"] for
                       y in meas_summary]) or \
                   all([meas_dict["name"] not in y for y in listdir(
                        path.join(*handyfiles.ecm_compete_data))]) or \
                   (stat(path.join(handyfiles.indiv_ecms, mi)).st_mtime >
                    stat(path.join(
                        "supporting_data", "ecm_prep.json")).st_mtime) or \
                   (opts is not None and opts.site_energy is True and
                    all([y["energy_outputs"]["site_energy"] is False for
                         y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is not None and opts.captured_energy is True and
                    all([y["energy_outputs"]["captured_energy_ss"] is False
                         for y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is not None and opts.alt_regions is True and
                    all([(y["energy_outputs"]["alt_regions"] is False or
                          y["energy_outputs"]["alt_regions"] != regions)
                         for y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is not None and opts.tsv_metrics is True and
                    all([y["energy_outputs"]["tsv_metrics"] is False or
                         y["energy_outputs"]["tsv_metrics"] != tsv_metrics
                         for y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is not None and opts.health_costs is True and
                    all([y["energy_outputs"]["health_costs"] is False
                         for y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is not None and opts.split_fuel is True and
                    all([y["energy_outputs"]["split_fuel"] is False
                         for y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is None or opts.site_energy is False and
                    all([y["energy_outputs"]["site_energy"] is True for
                         y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is None or opts.captured_energy is False and
                    all([y["energy_outputs"]["captured_energy_ss"] is True
                         for y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is None or opts.alt_regions is False and
                    all([y["energy_outputs"]["alt_regions"] is not False
                         for y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is None or opts.tsv_metrics is False and
                    all([y["energy_outputs"]["tsv_metrics"] is not False
                         for y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is None or opts.health_costs is False and
                    all([y["energy_outputs"]["health_costs"] is not False
                         for y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is None or opts.split_fuel is False and
                    all([y["energy_outputs"]["split_fuel"] is not False
                         for y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is not None and opts.sect_shapes is True and any([
                    all([x not in y["sector_shapes"].keys() or
                         len(y["sector_shapes"][x]) == 0
                         for y in meas_summary if y["name"] ==
                         meas_dict["name"]])
                    for x in handyvars.adopt_schemes])) or \
                   (opts is not None and opts.sect_shapes is True and
                    any([meas_dict["name"] in pkg["contributing_ECMs"]
                         for pkg in meas_toprep_package_init])):
                    # Append measure dict to list of measure definitions
                    # to update if it meets the above criteria
                    meas_toprep_indiv.append(meas_dict)
                    # Add copies of the measure that examine multiple scenarios
                    # of public health cost data additions, assuming the
                    # measure is not already a previously prepared copy
                    # that reflects these additions (judging by name)
                    if opts is not None and opts.health_costs is True and \
                            "PHC" not in meas_dict["name"]:
                        # Check to ensure that the measure applies to the
                        # electric fuel type (or switches to it); if not, do
                        # not prepare additional versions of the measure with
                        # health costs
                        if ((((type(meas_dict["fuel_type"]) is not list) and
                              meas_dict["fuel_type"] not in [
                            "electricity", "all"]) or ((type(
                                meas_dict["fuel_type"]) is list) and all([
                                x not in ["electricity", "all"] for x in
                                meas_dict["fuel_type"]]))) and
                                meas_dict["fuel_switch_to"] != "electricity"):
                            # Warn the user that ECMs that do not apply to the
                            # electric fuel type will not be prepared with
                            # public cost health adders
                            warnings.warn(
                                "WARNING: " + meas_dict["name"] + " does not "
                                "apply to the electric fuel type; versions of "
                                "this ECM with low/high public health cost "
                                "adders will not be prepared.")
                        else:
                            for scn in handyvars.health_scn_names:
                                # Determine unique measure copy name
                                new_name = meas_dict["name"] + "-" + scn[0]
                                # Copy the measure
                                new_meas = copy.deepcopy(meas_dict)
                                # Set the copied measure name to the name above
                                new_meas["name"] = new_name
                                # Append the copied measure to list of measure
                                # definitions to update
                                meas_toprep_indiv.append(new_meas)
            except ValueError as e:
                raise ValueError(
                    "Error reading in ECM '" + mi + "': " +
                    str(e)) from None

    # Find package measure definitions that are new or were edited since
    # the last time 'ecm_prep.py' routine was run, or are comprised of
    # individual measures that are new or were edited since the last time
    # 'ecm_prep.py' routine was run

    # Initialize list of measure package dicts to prepare
    meas_toprep_package = []
    # Initialize a list to track which individual ECMs contribute to packages
    contrib_meas_pkg = []
    # Identify all previously prepared measure packages
    meas_prepped_pkgs = [
        mpkg for mpkg in meas_summary if "contributing_ECMs" in mpkg.keys()]
    # Loop through each package dict in the current list and determine which
    # of these package measures require further preparation
    for m in meas_toprep_package_init:
        # Determine the subset of previously prepared package measures
        # with the same name as the current package measure
        m_exist = [
            me for me in meas_prepped_pkgs if me["name"] == m["name"]]
        # Add a package dict to the list requiring further prepartion if:
        # a) any of the package's contributing measures have been updated,
        # b) the package is new, c) package does not already have competition
        # data prepared for it; or d) package "contributing_ECMs" and/or
        # "benefits" parameters have been edited from a previous version
        if any([x["name"] in m["contributing_ECMs"] for
                x in meas_toprep_indiv]) or len(m_exist) == 0 or \
            all([m["name"] not in y for y in listdir(path.join(
                *handyfiles.ecm_compete_data))]) or (len(m_exist) == 1 and (
                    sorted(m["contributing_ECMs"]) !=
                    sorted(m_exist[0]["contributing_ECMs"]) or (
                        m["benefits"]["energy savings increase"] !=
                        m_exist[0]["benefits"]["energy savings increase"]) or (
                        m["benefits"]["cost reduction"] !=
                        m_exist[0]["benefits"]["cost reduction"]))):
            meas_toprep_package.append(m)
            contrib_meas_pkg.extend(m["contributing_ECMs"])
        # Raise an error if the current package matches the name of
        # multiple previously prepared packages
        elif len(m_exist) > 1:
            raise ValueError(
                "Multiple existing ECM names match '" + m["name"] + "'")

    print("Importing supporting data...", end="", flush=True)
    # If one or more measure definition is new or has been edited, proceed
    # further with 'ecm_prep.py' routine; otherwise end the routine
    if len(meas_toprep_indiv) > 0 or len(meas_toprep_package) > 0:

        # Import baseline microsegments
        if regions == 'State':  # Extract compressed state stock/energy data
            bjszip = path.join(base_dir, *handyfiles.msegs_in)
            # bjszip = path.splitext(bjs)[0] + '.gz'
            with gzip.GzipFile(bjszip, 'r') as zip_ref:
                msegs = json.loads(zip_ref.read().decode('utf-8'))
        else:
            with open(path.join(base_dir, *handyfiles.msegs_in), 'r') as msi:
                try:
                    msegs = json.load(msi)
                except ValueError as e:
                    raise ValueError(
                        "Error reading in '" +
                        handyfiles.msegs_in + "': " + str(e)) from None
        # Import baseline cost, performance, and lifetime data
        if regions == 'EMM':  # Extract compressed CPL EMM file
            bjszip = path.join(base_dir, *handyfiles.msegs_cpl_in)
            # bjszip = path.splitext(bjs)[0] + '.gz'
            with gzip.GzipFile(bjszip, 'r') as zip_ref:
                msegs_cpl = json.loads(zip_ref.read().decode('utf-8'))
        else:
            with open(
                    path.join(base_dir, *handyfiles.msegs_cpl_in), 'r') as bjs:
                try:
                    msegs_cpl = json.load(bjs)
                except ValueError as e:
                    raise ValueError(
                        "Error reading in '" +
                        handyfiles.msegs_cpl_in + "': " + str(e)) from None
        # Import measure cost unit conversion data
        with open(path.join(base_dir, *handyfiles.cost_convert_in), 'r') as cc:
            try:
                convert_data = json.load(cc)
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.cost_convert_in + "': " + str(e)) from None
        # Import CBECs square footage by vintage data (used to map EnergyPlus
        # commercial building vintages to Scout building vintages)
        with open(path.join(
                base_dir, *handyfiles.cbecs_sf_byvint), 'r') as cbsf:
            try:
                cbecs_sf_byvint = json.load(cbsf)[
                    "commercial square footage by vintage"]
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.cbecs_sf_byvint + "': " + str(e)) from None
        if (regions == 'EMM' and ((tsv_metrics is not None or any([
                ("tsv_features" in m.keys() and m["tsv_features"] is not None)
                for m in meas_toprep_indiv])) or
                opts is not None and opts.sect_shapes is True)):
            # Import load, price, and emissions shape data needed for time
            # sensitive analysis of measure energy efficiency impacts
            tsv_l = path.join(base_dir, *handyfiles.tsv_load_data)
            tsv_l_zip = path.splitext(tsv_l)[0] + '.gz'
            with gzip.GzipFile(tsv_l_zip, 'r') as zip_ref_l:
                tsv_load_data = json.loads(zip_ref_l.read().decode('utf-8'))
            # When sector shapes are specified and no other time sensitive
            # valuation or features are present, assume that hourly price
            # and emissions data will not be needed
            if ((opts and opts.sect_shapes is True)
                and tsv_metrics is None and all([(
                    "tsv_features" not in m.keys() or
                    m["tsv_features"] is None) for m in meas_toprep_indiv])):
                tsv_data = {
                    "load": tsv_load_data, "price": None,
                    "price_yr_map": None, "emissions": None,
                    "emissions_yr_map": None}
            else:
                tsv_c = path.join(base_dir, *handyfiles.tsv_cost_data)
                tsv_c_zip = path.splitext(tsv_c)[0] + '.gz'
                with gzip.GzipFile(tsv_c_zip, 'r') as zip_ref_c:
                    tsv_cost_data = \
                        json.loads(zip_ref_c.read().decode('utf-8'))
                tsv_cb = path.join(base_dir, *handyfiles.tsv_carbon_data)
                tsv_cb_zip = path.splitext(tsv_cb)[0] + '.gz'
                with gzip.GzipFile(tsv_cb_zip, 'r') as zip_ref_cb:
                    tsv_carbon_data = \
                        json.loads(zip_ref_cb.read().decode('utf-8'))
                # Map years available in 8760 TSV cost/carbon data to AEO yrs.
                tsv_cost_yrmap = tsv_cost_carb_yrmap(
                    tsv_cost_data["electricity price shapes"],
                    handyvars.aeo_years)
                tsv_carbon_yrmap = tsv_cost_carb_yrmap(
                    tsv_carbon_data["average carbon emissions rates"],
                    handyvars.aeo_years)
                # Stitch together load shape, cost, emissions, and year
                # mapping datasets
                tsv_data = {
                    "load": tsv_load_data, "price": tsv_cost_data,
                    "price_yr_map": tsv_cost_yrmap,
                    "emissions": tsv_carbon_data,
                    "emissions_yr_map": tsv_carbon_yrmap}
        else:
            tsv_data = None

        # Import analysis engine setup file to write prepared ECM names
        # to (if file does not exist, provide empty active/inactive ECM
        # list as substitute, since file will be overwritten/created
        # later when writing ECM data)
        try:
            am = open(path.join(base_dir, handyfiles.run_setup), 'r')
            try:
                run_setup = json.load(am, object_pairs_hook=OrderedDict)
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.run_setup + "': " + str(e)) from None
            am.close()
        except FileNotFoundError:
            run_setup = {"active": [], "inactive": []}

        print("Complete")

        # Prepare new or edited measures for use in analysis engine
        meas_prepped_objs = prepare_measures(
            meas_toprep_indiv, convert_data, msegs, msegs_cpl, handyvars,
            handyfiles, cbecs_sf_byvint, tsv_data, base_dir, opts, regions,
            tsv_metrics, contrib_meas_pkg)

        # Prepare measure packages for use in analysis engine (if needed)
        if meas_toprep_package:
            meas_prepped_objs = prepare_packages(
                meas_toprep_package, meas_prepped_objs, meas_summary,
                handyvars, handyfiles, base_dir, opts, regions, tsv_metrics)

        print("All ECM updates complete; finalizing data...",
              end="", flush=True)
        # Split prepared measure data into subsets needed to set high-level
        # measure attributes information and to execute measure competition
        # in the analysis engine
        meas_prepped_compete, meas_prepped_summary = split_clean_data(
            meas_prepped_objs)

        # Add all prepared high-level measure information to existing
        # high-level data and to list of active measures for analysis
        for m in meas_prepped_summary:
            # Measure has been prepared from existing case (replace
            # high-level data for measure)
            if m["name"] in [x["name"] for x in meas_summary]:
                [x.update(m) for x in meas_summary if x["name"] == m["name"]]
            # Measure is new (add high-level data for measure)
            else:
                meas_summary.append(m)
            # Add measures to active list; in a scenario where public health
            # costs are assumed, add only the "high" health costs versions of
            # prepared measures to the active list
            if ((opts is not None and opts.health_costs is True) and (
                    "PHC-EE (high)" not in m["name"])):
                # Measure not already in inactive measures list (add to list)
                if m["name"] not in run_setup["inactive"]:
                    run_setup["inactive"].append(m["name"])
                # Measure in active measures list (remove name from list)
                if m["name"] in run_setup["active"]:
                    run_setup["active"] = [x for x in run_setup[
                        "active"] if x != m["name"]]
            else:
                # Measure not already in active measures list (add to list)
                if m["name"] not in run_setup["active"]:
                    run_setup["active"].append(m["name"])
                # Measure in inactive measures list (remove name from list)
                if m["name"] in run_setup["inactive"]:
                    run_setup["inactive"] = [x for x in run_setup[
                        "inactive"] if x != m["name"]]

        # Notify user that all measure preparations are completed
        print('Writing output data...')

        # Write prepared measure competition data to zipped JSONs; do not
        # write competition data for a case when sector shapes are being
        # generated, in which it is assumed subsequent measure competition
        # calculations will not be performed
        if opts is None or opts.sect_shapes is not True:
            for ind, m in enumerate(meas_prepped_objs):
                # Assemble folder path for measure competition data
                meas_folder_name = path.join(*handyfiles.ecm_compete_data)
                # Assemble file name for measure competition data
                meas_file_name = m.name + ".pkl.gz"
                with gzip.open(path.join(base_dir, meas_folder_name,
                                         meas_file_name), 'w') as zp:
                    pickle.dump(meas_prepped_compete[ind], zp, -1)
        # Write prepared high-level measure attributes data to JSON
        with open(path.join(base_dir, *handyfiles.ecm_prep), "w") as jso:
            json.dump(meas_summary, jso, indent=2, cls=MyEncoder)

        # Write any newly prepared measure names to the list of active
        # measures to be run in the analysis engine
        with open(path.join(base_dir, handyfiles.run_setup), "w") as jso:
            json.dump(run_setup, jso, indent=2)
    else:
        print('No new ECM updates available')


if __name__ == "__main__":
    import time
    start_time = time.time()
    # Handle option user-specified execution arguments
    parser = ArgumentParser()
    # Optional flag to calculate site (rather than source) energy outputs
    parser.add_argument("--site_energy", action="store_true",
                        help="Flag site energy output")
    # Optional flag to calculate site-source energy conversions using the
    # captured energy (rather than fossil fuel equivalent) method
    parser.add_argument("--captured_energy", action="store_true",
                        help="Flag captured energy site-source conversions")
    # Optional flag for non-AIA regional breakdown
    parser.add_argument("--alt_regions", action="store_true",
                        help="Flag alternate regional breakdown")
    # Optional flag for TSV metrics
    parser.add_argument("--tsv_metrics", action="store_true",
                        help="Flag time sensitive valuation metrics")
    # Optional flag for generating sector-level load shapes
    parser.add_argument("--sect_shapes", action="store_true",
                        help="Flag sector-level load shapes")
    # Optional flag for persistent relative performance after market entry
    parser.add_argument("--rp_persist", action="store_true",
                        help="Flag consistent relative performance value "
                        "after market entry")
    # Optional flag to print all warning messages to stdout
    parser.add_argument("--verbose", action="store_true",
                        help="Print all warnings to stdout")
    # Optional flag to introduce public health cost assessment
    parser.add_argument("--health_costs", action="store_true",
                        help="Flag addition of public health cost data")
    # Optional flag to introduce output fuel splits
    parser.add_argument("--split_fuel", action="store_true",
                        help="Split electric vs. non-electric fuel in results")
    # Optional flag to suppress secondary lighting calculations
    parser.add_argument("--no_scnd_lgt", action="store_true",
                        help="Suppress secondary lighting calculations")
    # Object to store all user-specified execution arguments
    opts = parser.parse_args()

    # Set current working directory
    base_dir = getcwd()
    main(base_dir)
    hours, rem = divmod(time.time() - start_time, 3600)
    minutes, seconds = divmod(rem, 60)
    print("--- Runtime: %s (HH:MM:SS.mm) ---" %
          "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds))
