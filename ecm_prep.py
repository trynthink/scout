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
        msegs_in (JSON): Database of baseline microsegment stock/energy.
        msegs_cpl_in (JSON): Database of baseline technology characteristics.
        metadata (JSON) = Baseline metadata inc. min/max for year range.
        cost_convert_in (JSON): Database of measure cost unit conversions.
        cbecs_sf_byvint (JSON): Commercial sq.ft. by vintage data.
        indiv_ecms: Individual ECM JSON definitions folder.
        ecm_packages (JSON): Measure package data.
        ecm_prep (JSON): Prepared measure attributes data for use in the
            analysis engine.
        ecm_compete_data: Folder with contributing microsegment data needed
            to run measure competition in the analysis engine.
        run_setup (JSON): Names of active measures that should be run in
            the analysis engine.
        cpi_data (CSV) = Historical Consumer Price Index data.
        ss_data (JSON) = Site-source conversion data.
        tsv_data (JSON) = Time sensitive energy, price, and emissions data.
    """

    def __init__(self, capt_energy):
        self.msegs_in = ("supporting_data", "stock_energy_tech_data",
                         "mseg_res_com_cz.json")
        # UNCOMMENT WITH ISSUE 188
        # self.msegs_in = ("supporting_data", "stock_energy_tech_data",
        #                  "mseg_res_com_cz_2017.json")
        self.msegs_cpl_in = ("supporting_data", "stock_energy_tech_data",
                             "cpl_res_com_cz.json")
        # UNCOMMENT WITH ISSUE 188
        # self.msegs_cpl_in = ("supporting_data", "stock_energy_tech_data",
        #                      "cpl_res_com_cz_2017.json")
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
        self.tsv_data = ("supporting_data", "convert_data", "tsv.json")


class UsefulVars(object):
    """Class of variables that are used globally across functions.

    Attributes:
        adopt_schemes (list): Possible consumer adoption scenarios.
        discount_rate (float): Rate to use in discounting costs/savings.
        retro_rate (float): Rate at which existing stock is retrofitted.
        nsamples (int): Number of samples to draw from probability distribution
            on measure inputs.
        aeo_years (list): Modeling time horizon.
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
        tsv_order (list): Order in which to implement time-sensitive
            efficiency impacts.
    """

    def __init__(self, base_dir, handyfiles):
        self.adopt_schemes = ['Technical potential', 'Max adoption potential']
        self.discount_rate = 0.07
        self.retro_rate = 0.01
        self.nsamples = 100
        # Load metadata including AEO year range
        with open(path.join(base_dir, handyfiles.metadata), 'r') as aeo_yrs:
            try:
                aeo_yrs = json.load(aeo_yrs)
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.metadata + "': " + str(e)) from None
        # Set minimum AEO modeling year
        aeo_min = aeo_yrs["min year"]
        # Set maximum AEO modeling year
        aeo_max = aeo_yrs["max year"]
        # Derive time horizon from min/max years
        self.aeo_years = [
            str(i) for i in range(aeo_min, aeo_max + 1)]
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
        # Read in JSON with site to source conversion, fuel CO2 intensity,
        # and energy/carbon costs data
        with open(path.join(base_dir, *handyfiles.ss_data), 'r') as ss:
            try:
                cost_ss_carb = json.load(ss)
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.ss_data + "': " + str(e)) from None
        # Set site to source conversions
        self.ss_conv = {
            "electricity": cost_ss_carb[
                "electricity"]["site to source conversion"]["data"],
            "natural gas": {yr: 1 for yr in self.aeo_years},
            "distillate": {yr: 1 for yr in self.aeo_years},
            "other fuel": {yr: 1 for yr in self.aeo_years}}
        # Set CO2 intensity by fuel type
        carb_int_init = {
            "residential": {
                "electricity": cost_ss_carb[
                    "electricity"]["CO2 intensity"]["data"]["residential"],
                "natural gas": cost_ss_carb[
                    "natural gas"]["CO2 intensity"]["data"]["residential"],
                "distillate": cost_ss_carb[
                    "other"]["CO2 intensity"]["data"]["residential"],
                "other fuel": cost_ss_carb[
                    "other"]["CO2 intensity"]["data"]["residential"]},
            "commercial": {
                "electricity": cost_ss_carb[
                    "electricity"]["CO2 intensity"]["data"]["commercial"],
                "natural gas": cost_ss_carb[
                    "natural gas"]["CO2 intensity"]["data"]["commercial"],
                "distillate": cost_ss_carb[
                    "other"]["CO2 intensity"]["data"]["commercial"],
                "other fuel": cost_ss_carb[
                    "other"]["CO2 intensity"]["data"]["commercial"]}}
        # Divide CO2 intensity by fuel type data by 1000000000 to reflect
        # conversion from import units of MMTon/quad to MMTon/MMBtu
        self.carb_int = {bldg: {fuel: {
            yr: (carb_int_init[bldg][fuel][yr] / 1000000000) for
            yr in self.aeo_years} for fuel in carb_int_init[bldg].keys()} for
            bldg in carb_int_init.keys()}
        # Set energy costs
        self.ecosts = {
            "residential": {
                "electricity": cost_ss_carb[
                    "electricity"]["price"]["data"]["residential"],
                "natural gas": cost_ss_carb[
                    "natural gas"]["price"]["data"]["residential"],
                "distillate": cost_ss_carb[
                    "other"]["price"]["data"]["residential"],
                "other fuel": cost_ss_carb[
                    "other"]["price"]["data"]["residential"]},
            "commercial": {
                "electricity": cost_ss_carb[
                    "electricity"]["price"]["data"]["commercial"],
                "natural gas": cost_ss_carb[
                    "natural gas"]["price"]["data"]["commercial"],
                "distillate": cost_ss_carb[
                    "other"]["price"]["data"]["commercial"],
                "other fuel": cost_ss_carb[
                    "other"]["price"]["data"]["commercial"]}}
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
        self.in_all_map = {
            "climate_zone": [
                "AIA_CZ1", "AIA_CZ2", "AIA_CZ3", "AIA_CZ4", "AIA_CZ5"],
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
                                'Range, Electric, 4 burner, oven, 11-inch gr',
                                'Range, Electric-induction, 4 burner, oven'],
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
                                'Range, Gas, 4 burner, oven, 11-inch griddle',
                                'Range, Gas, 4 powered burners, convect. ove'],
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
        self.out_break_czones = OrderedDict([
            ('AIA CZ1', 'AIA_CZ1'), ('AIA CZ2', 'AIA_CZ2'),
            ('AIA CZ3', 'AIA_CZ3'), ('AIA CZ4', 'AIA_CZ4'),
            ('AIA CZ5', 'AIA_CZ5')])
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
            ('Envelope', ["heating", "secondary heating", "cooling"]),
            ('Ventilation', ["ventilation"]),
            ('Lighting', ["lighting"]),
            ('Water Heating', ["water heating"]),
            ('Refrigeration', ["refrigeration", "other"]),
            ('Computers and Electronics', [
                "PCs", "non-PC office equipment", "TVs", "computers"]),
            ('Other', [
                "cooking", "drying", "ceiling fan", "fans and pumps",
                "MELs", "other"])])
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
                if elem not in current_level:
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
            "refrigeration": ["$/kBtu/h refrigeration"]}
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
        # Establish the assumed order in which time sensitive ECM
        # adjustments are applied
        self.tsv_order = ["conventional", "shave", "fill", "shift", "shape"]

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
                "LargeOffice": 0.9,
                "MediumOffice": 0.1},
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
            energy site-source conversions were used in measure preparation.
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
        out_break_norm (dict): Total energy use data to normalize
            savings values summed by climate zone, building class, and end use.
    """

    def __init__(self, handyvars, site_energy, capt_energy, **kwargs):
        # Read Measure object attributes from measures input JSON.
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Check to ensure that measure name is proper length for plotting
        if len(self.name) > 45:
            raise ValueError(
                "ECM '" + self.name + "' name must be <= 45 characters")
        self.remove = False
        self.energy_outputs = {
            "site_energy": False, "captured_energy_ss": False}
        if site_energy is True:
            self.energy_outputs["site_energy"] = True
        if capt_energy is True:
            self.energy_outputs["captured_energy_ss"] = True
        self.handyvars = handyvars
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
        # If no "time_sensitive_valuation" parameter was specified for the
        # ECM, set this parameter to None
        try:
            self.time_sensitive_valuation
        except AttributeError:
            self.time_sensitive_valuation = None
        self.markets, self.out_break_norm = ({} for n in range(2))
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
                "mseg_out_break", copy.deepcopy(
                    self.handyvars.out_break_in))])
            self.out_break_norm[adopt_scheme] = {
                yr: 0 for yr in self.handyvars.aeo_years}

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

    def fill_mkts(self, msegs, msegs_cpl, convert_data, tsv_data, opts):
        """Fill in a measure's market microsegments using EIA baseline data.

        Args:
            msegs (dict): Baseline microsegment stock and energy use.
            msegs_cpl (dict): Baseline technology cost, performance, and
                lifetime.
            convert_data (dict): Measure -> baseline cost unit conversions.
            tsv_data (dict): Data for time sensitive valuation of efficiency.
            opts (object): Stores user-specified execution options.

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
        # where no secondary microsegment is specified, use the "lighting
        # gain" thermal load component microsegments to represent secondary
        # end use effects of the lighting measure
        if self.end_use["secondary"] is not None:
            ms_iterable_second, ms_lists_second = self.create_keychain(
                "secondary")
            ms_iterable.extend(ms_iterable_second)
        elif "lighting" in self.end_use["primary"] and \
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

            # Set appropriate site-source conversion factor, energy cost, and
            # carbon intensity for given key chain
            if mskeys[3] in self.handyvars.ss_conv.keys():
                # Set baseline and measure site-source conversions and
                # carbon intensities, accounting for any fuel switching from
                # baseline technology to measure technology
                if self.fuel_switch_to is None:
                    # Set site-source conversions to 1 if user flagged
                    # site energy use outputs, while multiplying CO2
                    # intensities by the appropriate site-source conversion
                    # factor (CO2 conversions are based on primary energy use)
                    if opts is not None and opts.site_energy is True:
                        site_source_conv_base, site_source_conv_meas = [{
                            yr: 1 for yr in self.handyvars.aeo_years}
                            for n in range(2)]
                        intensity_carb_base, intensity_carb_meas = [{
                            yr: self.handyvars.carb_int[bldg_sect][
                                mskeys[3]][yr] *
                            self.handyvars.ss_conv[mskeys[3]][yr] for
                            yr in self.handyvars.aeo_years} for n in range(2)]
                    else:
                        site_source_conv_base, site_source_conv_meas = (
                            self.handyvars.ss_conv[mskeys[3]] for
                            n in range(2))
                        intensity_carb_base, intensity_carb_meas = (
                            self.handyvars.carb_int[bldg_sect][
                                mskeys[3]] for n in range(2))
                else:
                    # Set site-source conversions to 1 if user flagged
                    # site energy use outputs, while multiplying CO2
                    # intensities by the appropriate site-source conversion
                    # factor (CO2 conversions are based on primary energy use)
                    if opts is not None and opts.site_energy is True:
                        site_source_conv_base, site_source_conv_meas = [{
                            yr: 1 for yr in self.handyvars.aeo_years}
                            for n in range(2)]
                        intensity_carb_base = {yr: self.handyvars.carb_int[
                            bldg_sect][mskeys[3]][yr] *
                            self.handyvars.ss_conv[mskeys[3]][yr]
                            for yr in self.handyvars.aeo_years}
                        intensity_carb_meas = {yr: self.handyvars.carb_int[
                            bldg_sect][self.fuel_switch_to][yr] *
                            self.handyvars.ss_conv[self.fuel_switch_to][yr]
                            for yr in self.handyvars.aeo_years}
                    else:
                        site_source_conv_base = self.handyvars.ss_conv[
                            mskeys[3]]
                        site_source_conv_meas = self.handyvars.ss_conv[
                            self.fuel_switch_to]
                        intensity_carb_base = self.handyvars.carb_int[
                            bldg_sect][mskeys[3]]
                        intensity_carb_meas = self.handyvars.carb_int[
                            bldg_sect][self.fuel_switch_to]

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
                # Check whether baseline microsegment cost/performance/lifetime
                # data are in dict format and current key is in dict keys; if
                # so, proceed further with the recursive loop. * Note: dict key
                # hierarchies and syntax are assumed to be consistent across
                # all measure and baseline cost/performance/lifetime and
                # stock/energy market data
                if isinstance(base_cpl, dict) and mskeys[i] in \
                    base_cpl.keys() or mskeys[i] in [
                        "primary", "secondary", "new", "existing", None]:
                    # Skip over "primary", "secondary", "new", and "existing"
                    # keys in updating baseline stock/energy, cost and lifetime
                    # information (this information is not broken out by these
                    # categories)
                    if mskeys[i] not in [
                            "primary", "secondary", "new", "existing", None]:

                        # Restrict base cost/performance/lifetime dict to key
                        # chain info.
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

                    # Restrict any measure cost/performance/lifetime/market
                    # scaling info. that is a dict type to key chain info.
                    if isinstance(perf_meas, dict) and mskeys[i] in \
                       perf_meas.keys():
                        perf_meas = perf_meas[mskeys[i]]
                    if isinstance(perf_units, dict) and mskeys[i] in \
                       perf_units.keys():
                        perf_units = perf_units[mskeys[i]]
                    if isinstance(cost_meas, dict) and mskeys[i] in \
                       cost_meas.keys():
                        cost_meas = cost_meas[mskeys[i]]
                    if isinstance(cost_units, dict) and mskeys[i] in \
                       cost_units.keys():
                        cost_units = cost_units[mskeys[i]]
                    if isinstance(life_meas, dict) and mskeys[i] in \
                       life_meas.keys():
                        life_meas = life_meas[mskeys[i]]
                    if isinstance(mkt_scale_frac, dict) and mskeys[i] in \
                            mkt_scale_frac.keys():
                        mkt_scale_frac = mkt_scale_frac[mskeys[i]]
                    if isinstance(mkt_scale_frac_source, dict) and \
                            mskeys[i] in mkt_scale_frac_source.keys():
                        mkt_scale_frac_source = \
                            mkt_scale_frac_source[mskeys[i]]
                # If no key match, break the loop
                else:
                    if mskeys[i] is not None:
                        mseg = {}
                    break

            # Continue loop if key chain doesn't yield "stock"/"energy" keys
            if any([x not in list(mseg.keys()) for x in ["stock", "energy"]]):
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
                        # set to zero or "NA" values (excepting cases where
                        # baseline cost is expected to be zero). In such cases,
                        # raise a ValueError
                        if any([(x[1] in [0, "NA"] and mskeys[-2] not in
                                 self.handyvars.zero_cost_tech) for
                                x in base_cpl[
                                "installed cost"]["typical"].items()]) or \
                           any([y[1] in [0, "NA"] for y in base_cpl[
                                "performance"]["typical"].items()]) or \
                           any([z[1] in [0, "NA"] for z in base_cpl[
                                "lifetime"]["average"].items()]):
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
                        # If the baseline technology is a heat pump in the
                        # residential sector, account for the fact that EIA
                        # divides all heat pump costs by 2 when separately
                        # considered across the heating and cooling services
                        elif bldg_sect == "residential" and (
                                mskeys[-2] is not None and "HP" in mskeys[-2]):
                            # Multiply heat pump baseline cost units by 2
                            # to account for EIA heat pump cost handling
                            cost_base, cost_base_units = \
                                [{yr: base_cpl[
                                    "installed cost"]["typical"][yr] * 2
                                    for yr in self.handyvars.aeo_years},
                                 base_cpl["installed cost"]["units"]]
                            # Warn the user about the modification to EIA's
                            # baseline cost data for this stock segment
                            if mskeys[-2] not in hp_warn:
                                hp_warn.append(mskeys[-2])
                                verboseprint(
                                    opts.verbose,
                                    "WARNING: Cost data for comparable "
                                    "residential baseline technology '" +
                                    str(mskeys[-2]) + "' "
                                    "multiplied by two to account for EIA "
                                    "handling of heat pump costs for the "
                                    "residential heating and cooling end uses "
                                    "(equipment costs are divided by 2 when "
                                    "separately considered across heating and "
                                    "cooling in the raw EIA data)")
                        # For all other baseline technologies, pull baseline
                        # costs and cost units in as is from the baseline data
                        else:
                            # Set baseline cost units
                            cost_base, cost_base_units = \
                                [base_cpl["installed cost"]["typical"],
                                 base_cpl["installed cost"]["units"]]

                        # Set baseline cost and lifetime
                        life_base = base_cpl["lifetime"]["average"]
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
                            # Set baseline cost/units to measure cost/units
                            cost_base = {yr: cost_meas for
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
                    cost_meas, cost_units = self.convert_costs(
                        convert_data, bldg_sect, mskeys, cost_meas,
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
                            try:
                                # In cases where an ECM enhances the
                                # performance of a baseline technology,
                                # add the ECM and baseline performance values
                                # and compare to the baseline performance
                                # value; otherwise, compare the ECM performance
                                # value to the baseline performance value
                                if self.measure_type == "add-on":
                                    rel_perf[yr] = (
                                        perf_base[yr] /
                                        (perf_meas + perf_base[yr]))
                                else:
                                    rel_perf[yr] = (perf_base[yr] / perf_meas)
                            except ZeroDivisionError:
                                verboseprint(
                                    opts.verbose,
                                    "WARNING: Measure '" + self.name +
                                    "' has measure performance of zero; " +
                                    "baseline and measure performance set " +
                                    "equal")
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
                else:
                    raise KeyError(
                        "Invalid performance or cost units for ECM '" +
                        self.name + "'")

                # Reduce energy costs and stock turnover info. to appropriate
                # building type and - for energy costs - fuel, before
                # entering into "partition_microsegment"
                if bldg_sect == "residential":
                    # Update residential baseline and measure energy cost
                    # information, accounting for any fuel switching from
                    # baseline technology to measure technology
                    if self.fuel_switch_to is None:
                        # If user flagged site energy use outputs, multiply
                        # energy costs by the appropriate site-source
                        # conversion factor (energy costs are based on
                        # primary energy use numbers)
                        if opts is not None and opts.site_energy is True:
                            cost_energy_base, cost_energy_meas = [{
                                yr: self.handyvars.ecosts[
                                    "residential"][mskeys[3]][yr] *
                                self.handyvars.ss_conv[mskeys[3]][yr] for
                                yr in self.handyvars.aeo_years} for
                                n in range(2)]
                        else:
                            cost_energy_base, cost_energy_meas = (
                                self.handyvars.ecosts[
                                    "residential"][mskeys[3]] for
                                n in range(2))
                    else:
                        # If user flagged site energy use outputs, multiply
                        # energy costs by the appropriate site-source
                        # conversion factor (energy costs are based on
                        # primary energy use numbers)
                        if opts is not None and opts.site_energy is True:
                            cost_energy_base = {
                                yr: self.handyvars.ecosts[
                                    "residential"][mskeys[3]][yr] *
                                self.handyvars.ss_conv[mskeys[3]][yr] for
                                yr in self.handyvars.aeo_years}
                            cost_energy_meas = {
                                yr: self.handyvars.ecosts[
                                    "residential"][self.fuel_switch_to][yr] *
                                self.handyvars.ss_conv[
                                    self.fuel_switch_to][yr] for
                                yr in self.handyvars.aeo_years}
                        else:
                            cost_energy_base = self.handyvars.ecosts[
                                "residential"][mskeys[3]]
                            cost_energy_meas = self.handyvars.ecosts[
                                "residential"][self.fuel_switch_to]

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
                        except (ValueError, TypeError):
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
                    # Update commercial baseline and measure energy cost
                    # information, accounting for any fuel switching from
                    # baseline technology to measure technology
                    if self.fuel_switch_to is None:
                        # If user flagged site energy use outputs, multiply
                        # energy costs by the appropriate site-source
                        # conversion factor (energy costs are based on
                        # primary energy use numbers)
                        if opts is not None and opts.site_energy is True:
                            cost_energy_base, cost_energy_meas = [{
                                yr: self.handyvars.ecosts[
                                    "commercial"][mskeys[3]][yr] *
                                self.handyvars.ss_conv[mskeys[3]][yr] for
                                yr in self.handyvars.aeo_years} for
                                n in range(2)]
                        else:
                            cost_energy_base, cost_energy_meas = (
                                self.handyvars.ecosts[
                                    "commercial"][mskeys[3]] for
                                n in range(2))
                    else:
                        # If user flagged site energy use outputs, multiply
                        # energy costs by the appropriate site-source
                        # conversion factor (energy costs are based on
                        # primary energy use numbers)
                        if opts is not None and opts.site_energy is True:
                            cost_energy_base = {
                                yr: self.handyvars.ecosts[
                                    "commercial"][mskeys[3]][yr] *
                                self.handyvars.ss_conv[mskeys[3]][yr] for
                                yr in self.handyvars.aeo_years}
                            cost_energy_meas = {
                                yr: self.handyvars.ecosts[
                                    "commercial"][self.fuel_switch_to][yr] *
                                self.handyvars.ss_conv[
                                    self.fuel_switch_to][yr] for
                                yr in self.handyvars.aeo_years}
                        else:
                            cost_energy_base = self.handyvars.ecosts[
                                "commercial"][mskeys[3]]
                            cost_energy_meas = self.handyvars.ecosts[
                                "commercial"][self.fuel_switch_to]

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
                    # com_timeprefs info. may eventually be integrated into the
                    # baseline technology cost, performance, and lifetime JSON
                    # as for residential)
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
                        new_constr["total new"][yr] = \
                            new_constr["annual new"][yr] + \
                            new_constr["total new"][str(int(yr) - 1)]
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

                # Check for a time-sensitive efficiency valuation flag; if this
                # type of valuation is necessary, develop the factors needed to
                # reweight energy/cost/carbon data to reflect time-varying
                # energy load, energy price, and marginal carbon emissions
                if self.time_sensitive_valuation is not None and (
                    mskeys[0] == "secondary" or (mskeys[0] == "primary" and
                                                 mskeys[3] == "electricity")):
                    tsv_scale_fracs, rel_perf = self.gen_tsv_facts(
                        tsv_data, mskeys, bldg_sect, rel_perf)
                else:
                    tsv_scale_fracs = {
                        "energy": {"efficient": {
                            yr: 1 for yr in self.handyvars.aeo_years}},
                        "cost": {"baseline": 1, "efficient": {
                            yr: 1 for yr in self.handyvars.aeo_years}},
                        "carbon": {"baseline": 1, "efficient": {
                            yr: 1 for yr in self.handyvars.aeo_years}}}

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
                     add_carb_cost_compete_eff] = \
                        self.partition_microsegment(
                            adopt_scheme, diffuse_params, mskeys,
                            mkt_scale_frac, new_constr, add_stock,
                            add_energy, add_carb, cost_base, cost_meas,
                            cost_energy_base, cost_energy_meas, rel_perf,
                            life_base, life_meas, site_source_conv_base,
                            site_source_conv_meas, intensity_carb_base,
                            intensity_carb_meas, energy_total_scnd,
                            tsv_scale_fracs)

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
                        # the 'Envelope' end use, with the exception of
                        # 'demand' side heating/cooling microsegments that
                        # represent waste heat from lights - these are
                        # categorized as part of the 'Lighting' end use
                        if mskeys[4] == "other":
                            if mskeys[5] == "freezers":
                                out_eu = "Refrigeration"
                            else:
                                out_eu = "Other"
                        elif mskeys[4] in eu[1]:
                            if (eu[0] in ["Heating (Equip.)",
                                          "Cooling (Equip.)"] and
                                mskeys[5] == "supply") or (
                                eu[0] == "Envelope" and
                                mskeys[5] == "demand" and
                                mskeys[0] == "primary") or (
                                eu[0] not in ["Heating (Equip.)",
                                              "Cooling (Equip.)", "Envelope"]):
                                out_eu = eu[0]
                        elif "lighting gain" in mskeys:
                            out_eu = "Lighting"

                    # Given the contributing microsegment's applicable climate
                    # zone, building type, and end use categories, add the
                    # microsegment's baseline energy use value to the
                    # appropriate leaf node of the dictionary used to store
                    # measure output breakout information. * Note: the values
                    # in this dictionary will eventually be normalized by the
                    # measure's total baseline energy use to yield the
                    # fractions of measure energy and carbon markets/savings
                    # that are attributable to each climate zone, building
                    # type, and end use the measure applies to
                    try:
                        # If this is the first time the output breakout
                        # dictionary is being updated, replace appropriate
                        # terminal leaf node value with the absolute baseline
                        # energy use values of the current contributing
                        # microsegment
                        if len(self.markets[adopt_scheme]["mseg_out_break"][
                                out_cz][out_bldg][out_eu].keys()) == 0:
                            self.markets[adopt_scheme]["mseg_out_break"][
                                out_cz][out_bldg][out_eu] = {
                                    yr: abs(add_energy[yr]) for
                                    yr in self.handyvars.aeo_years}

                        # If the output breakout dictionary has already been
                        # updated for a previous microsegment, add the absolute
                        # baseline energy values of the current contributing
                        # microsegment to the dictionary's existing terminal
                        # leaf node values
                        else:
                            for yr in self.handyvars.aeo_years:
                                self.markets[adopt_scheme]["mseg_out_break"][
                                    out_cz][out_bldg][
                                    out_eu][yr] += abs(add_energy[yr])

                        # Add to the total absolute energy value used to
                        # normalize savings values summed by climate zone,
                        # building type, and end use
                        for yr in self.out_break_norm[adopt_scheme].keys():
                            self.out_break_norm[
                                adopt_scheme][yr] += abs(add_energy[yr])

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

                # Normalize baseline energy use values for each category in the
                # measure's output breakout dictionary by the total baseline
                # energy use for the measure across all contributing
                # microsegments; this yields partitioning fractions that will
                # eventually be used to breakout measure energy and carbon
                # markets/savings by climate zone, building type, and end use
                self.div_keyvals(
                    self.markets[adopt_scheme]["mseg_out_break"],
                    self.out_break_norm[adopt_scheme])
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
            print(" Success" + bstk_msg + bcpl_msg + bcc_msg + cc_msg)

    def gen_tsv_facts(self, tsv_data, mskeys, bldg_sect, rel_perf):
        """Set re-weighting factors for time-sensitive efficiency valuation.

        Args:
            tsv_data (data): Time-resolved load/energy cost/emissions data.
            mskeys (tuple): Microsegment information needed to key load shapes.
            bldg_sect (string): Building sector of the current microsegment.
            rel_perf (dict): Annual relative energy performance of the measure.

        Returns:
            Dict of microsegment-specific energy, cost, and emissions re-
            weighting factors that reflect time-sensitive evaluation of energy
            efficiency and associated energy costs/marginal carbon emissions.
        """

        # Set energy load shapes for given climate, building type, and end use

        # Primary microsegment case: find the load shape associated with the
        # primary end use
        if mskeys[0] == "primary":
            try:
                load_fact = tsv_data["load"][mskeys[1]][bldg_sect][mskeys[4]]
            except KeyError:
                if mskeys[4] == "secondary heating":
                    load_fact = \
                        tsv_data["load"][mskeys[1]][bldg_sect]["heating"]
                else:
                    load_fact = tsv_data[
                        "load"][mskeys[1]][bldg_sect]["electronics"]
        # Commercial secondary lighting microsegment case: find the load shape
        # associated with the secondary end use (a combination of the lighting
        # and heating or cooling load shapes)
        else:
            # Pull load shape for cooling energy use associated with waste
            # heat from lights
            if mskeys[4] == "cooling":
                load_fact = tsv_data["load"][mskeys[1]][bldg_sect][
                    "secondary lighting (cooling)"]
            # Pull load shape for heating energy use associated with waste
            # heat from lights
            elif mskeys[4] == "heating":
                load_fact = tsv_data["load"][mskeys[1]][bldg_sect][
                    "secondary lighting (heating)"]
            # Throw error if any end uses other than heating or cooling
            # are included in secondary microsegments
            else:
                raise ValueError(
                    "Invalid secondary microsegment type for " +
                    "measure: " + self.name)
        # Set time-based electricity price scaling factors for given climate
        # zone and building type
        cost_fact = tsv_data["price"][mskeys[1]][bldg_sect]
        # Set time-based marginal emissions scaling factors for given climate
        emissions_fact = tsv_data["emissions"][mskeys[1]]

        # Initialize overall factors to use in scaling initial baseline and
        # efficient-case energy cost and emissions data
        cost_scale_base, carb_scale_base = (0 for n in range(2))
        energy_scale_eff, cost_scale_eff, carb_scale_eff = ({
            yr: 0 for yr in self.handyvars.aeo_years} for n in range(3))

        # Finalize overall scaling factors by looping through all times of
        # year and times of week and multiplying/summing the appropriate
        # scaling factors for those time windows
        for toy in ["winter", "intermediate", "summer"]:
            for tow in ["weekday", "weekend"]:
                # Restrict load shape, energy cost, and emissions data to
                # current time of year and week
                base_load, cost, emissions = [
                    load_fact[toy]["fractions"][tow],
                    cost_fact[toy]["rates"][tow],
                    emissions_fact[toy]["factors"]]

                # Modify base load shape with time sensitive valuation
                # parameters to arrive at efficient load shape

                # Guard against special time sensitive valuation cases
                # where relative performance is set to zero - as a user
                # might do when investigating how much total energy use
                # is associated with a particulate peak definition, for
                # example. Without special handling, such cases may
                # yield an error due to the division by the relative
                # performance variable in 'apply_tsv'. To avoid this issue
                # set any relative performances of zero to a number that
                # is close to zero.
                rel_perf = {
                    yr: (0.0001 if rel_perf[yr] == 0 else rel_perf[yr])
                    for yr in self.handyvars.aeo_years}
                eff_load = self.apply_tsv(base_load, mskeys, rel_perf)

                # Update baseline price and emissions scaling factors
                cost_scale_base += numpy.sum([x * y for x, y in zip(
                    base_load, cost)])
                carb_scale_base += numpy.sum([x * y for x, y in zip(
                    base_load, emissions)])
                # Update efficient price and emissions scaling factors
                energy_scale_eff = {
                    yr: val + numpy.sum(eff_load[yr]) for yr, val in
                    energy_scale_eff.items()}
                cost_scale_eff = {
                    yr: val + numpy.sum([
                        x * y for x, y in zip(eff_load[yr], cost)]) for
                    yr, val in cost_scale_eff.items()}
                carb_scale_eff = {
                    yr: val + numpy.sum([
                        x * y for x, y in zip(eff_load[yr], emissions)]) for
                    yr, val in carb_scale_eff.items()}

        # Set a dict of scaling fractions for time sensitive valuation
        updated_tsv_fracs = {
            "energy": {
                "efficient": energy_scale_eff},
            "cost": {
                "baseline": cost_scale_base,
                "efficient": cost_scale_eff
            },
            "carbon": {
                "baseline": carb_scale_base,
                "efficient": carb_scale_eff
            }}

        return [updated_tsv_fracs, rel_perf]

    def apply_tsv(self, base_load, mskeys, rel_perf):
        """Apply time varying efficiency levels to base load profile.

        Args:
            base_load (dict): Base load profile to apply time-varying eff. to.
            rel_perf (dict): Annual perf. of efficiency measure vs. baseline.
            mskeys (string): Baseline energy use microsegment information.

        Returns:
            Time-varying efficient load profile.
        """
        # Initialize efficient load as equal to base load
        eff_load = {yr: base_load for yr in self.handyvars.aeo_years}

        # Set the user-specified time-sensitive valuation parameters for the
        # current ECM; handle cases where this parameter is broken by end use
        try:
            tsv_adjustments = self.time_sensitive_valuation[mskeys[4]]
        except KeyError:
            tsv_adjustments = self.time_sensitive_valuation

        # Loop through all time-varying efficiency impacts, applying each
        # successively to the base load shape
        for a in [x for x in self.handyvars.tsv_order if
                  x in tsv_adjustments.keys() and
                  tsv_adjustments[x] not in [{}, None]]:
            # Set the applicable hours in which to apply the time-varying
            # efficiency impact; if no start and stop information is specified
            # by the user, assume the impact applies across all 24 hours
            try:
                # Set the starting and stopping hours for the impact
                start_stop = [
                    tsv_adjustments[a][x] for x in ["start", "stop"]]
                # Generate a list of all hours in which the time-varying
                # efficiency impact applies
                try:
                    # Handle case where user specifies an overnight start/stop
                    # time (e.g., 11AM to 5AM the next morning)
                    if start_stop[0] <= start_stop[1]:
                        applicable_hrs = list(
                            range(start_stop[0] - 1, start_stop[1]))
                    else:
                        applicable_hrs = list(range(0, start_stop[1])) + \
                            list(range(start_stop[0], 24))
                except TypeError:
                    applicable_hrs = list(range(0, 24))
            except (TypeError, KeyError):
                applicable_hrs = list(range(0, 24))

            # Apply time-varying impacts based on type of time-varying
            # efficiency measure

            # Conventional time-varying efficiency measures apply a %
            # hourly load reduction across the user-specified hour range
            if a == "conventional":
                # Reflect conventional efficiency in efficient load shape;
                # note that the efficient load shape equals the base load
                # shape in cases where conventional efficiency applies across
                # all 24 hours
                eff_load = {
                    yr: [eff_load[yr][x] if x in applicable_hrs else
                         (eff_load[yr][x] / rel_perf[yr])
                         for x in range(0, 24)] for
                    yr in self.handyvars.aeo_years}
            # Peak shaving or valley filling time-varying efficiency measures
            # either shed load or fill load to a given % of peak load across
            # the user-specified hour range
            elif a == "shave" or a == "fill":
                # Set peak load
                peak_load = {
                    yr: max(eff_load[yr]) for yr in self.handyvars.aeo_years}
                # Set peak load fraction for shave/fill measure
                peak_frac = tsv_adjustments[a]["peak_fraction"]
                # Reflect peak shaving/valley filling in efficient load shape;
                # in the peak shaving case, reduce all loads in the user-
                # specified hour range that are greater than the peak load *
                # peak fraction to that value; in the valley filling case,
                # increase all loads in the user-specified hour range that are
                # less than the peak load * peak fraction to that value
                eff_load = {
                    yr: [peak_load[yr] * peak_frac if (
                         x in applicable_hrs and (
                             (a == "shave" and eff_load[yr][x] >
                              peak_load[yr] * peak_frac) or
                             (a == "fill" and eff_load[yr][x] <
                              peak_load[yr] * peak_frac))) else eff_load[yr][x]
                         for x in range(0, 24)] for
                    yr in self.handyvars.aeo_years}
            # Load shifting time-varying efficiency measures either move the
            # entire baseline load shape earlier by a user-specified number
            # of hours, or move a certain % of hourly load across the
            # user-specified hour range earlier in the day by the
            # user-specified number of hours
            elif a == "shift":
                # Set the number of hours earlier to shift the load
                offset_hrs = tsv_adjustments[a]["offset_hrs_earlier"]
                # If the user has not specified a time range for the load
                # shifting, assume the measure shifts the entire load shape
                # earlier by the number of hours set above
                if len(applicable_hrs) == 24:
                    # Reflect load shifting in efficient load shape; the
                    # initial efficient load in hour X is now the load in hour
                    # X minus the user-specified hour offset
                    eff_load = {yr: [
                        eff_load[yr][x + offset_hrs] if
                        (x + offset_hrs) < 24 else
                        eff_load[yr][0 + (
                            (x + offset_hrs) - 24)] for
                        x in range(0, 24)] for
                        yr in self.handyvars.aeo_years}
                else:
                    # Determine the total amount of load that occurs during
                    # a user-specified hour range
                    load_to_shift = {
                        yr: numpy.sum([
                            eff_load[yr][x] * (1 - rel_perf[yr]) for
                            x in range(0, 24) if
                            x in applicable_hrs])
                        for yr in self.handyvars.aeo_years}
                    # Determine the hour range to shift the load to (take
                    # the user-specified hour range and shift it forward by
                    # the user-specified number of hours)
                    new_start, new_end = [
                        (x - offset_hrs) if (
                            x - offset_hrs) >= 0 else
                        ((x - offset_hrs) + 24) for x in [
                            min(applicable_hrs), max(applicable_hrs)]]
                    # Handle case where load is shifted to an overnight start/
                    # stop time (e.g., 11AM to 5AM the next morning)
                    if new_start <= new_end:
                        hrs_to_shift_to = list(
                            range(new_start, new_end + 1))
                    else:
                        hrs_to_shift_to = list(range(0, new_end + 1)) + \
                            list(range(new_start, 24))

                    # Reflect load shifting in efficient load shape; remove
                    # the user-specified % of load across the user-specified
                    # hour range and distribute it evenly across the earlier
                    # hour range determined by the user offset parameter
                    eff_load = {
                        yr: [((eff_load[yr][x] + (load_to_shift[yr] / len(
                            applicable_hrs)) / rel_perf[yr]) if (
                            x in hrs_to_shift_to and x in applicable_hrs) else
                            (((eff_load[yr][x] + (
                                load_to_shift[yr] / len(applicable_hrs))) /
                              rel_perf[yr]) if (x in hrs_to_shift_to and
                                                x not in applicable_hrs) else (
                                eff_load[yr][x] if x in applicable_hrs else
                                (eff_load[yr][x] / rel_perf[yr]))))
                            for x in range(0, 24)] for
                        yr in self.handyvars.aeo_years}

            # Load reshaping time-varying efficiency measures either impose
            # an entirely new, user-defined load shape or load savings shape
            # across all 24 hours or flatten the existing base load shape
            # across a user-specified hour range
            elif a == "shape":
                # If the user has provided custom load shape or savings
                # shape information, use that information to reshape and/or
                # scale down the efficient load; otherwise flatten the input
                # load across a user-specified hour range
                if "custom_load" in tsv_adjustments[a].keys() and \
                        tsv_adjustments[a]["custom_load"] is not None:
                    # Set the custom load shape (each element of the list
                    # represents an hourly fraction of peak load from 0 to 1)
                    custom_load_shape = tsv_adjustments[a]["custom_load"]
                    # Set the peak load for the efficient load shape
                    peak_load = {
                        yr: max(eff_load[yr]) for
                        yr in self.handyvars.aeo_years}
                    # Determine what fraction of peak each hourly load
                    # represents in the initial efficient load shape
                    eff_load_frac_peak = {yr: [
                        eff_load[yr][x] / peak_load[yr] for x in range(24)] for
                        yr in self.handyvars.aeo_years}
                    # Determine what fractions must be applied to the initial
                    # efficient load shape to arrive at the custom load shape
                    eff_load_adj_fracs = {yr: [x / y for x, y in zip(
                        custom_load_shape, eff_load_frac_peak[yr])] for
                        yr in self.handyvars.aeo_years}
                    # Reflect custom load reshaping in efficient load shape;
                    # apply the custom reshaping fractions to the initial
                    # efficient load shape
                    eff_load = {
                        yr: [eff_load[yr][x] * eff_load_adj_fracs[yr][x] for
                             x in range(24)] for
                        yr in self.handyvars.aeo_years}
                elif "custom_savings" in tsv_adjustments[a].keys() and \
                        tsv_adjustments[a]["custom_savings"] is not None:
                    # Set the custom savings shape (each element of the list
                    # represents an hourly savings fraction)
                    custom_save_shape = tsv_adjustments[a]["custom_savings"]
                    # Reflect custom load savings in efficient load shape;
                    # apply the custom savings fractions to the initial
                    # efficient load shape
                    eff_load = {
                        yr: [eff_load[yr][x] * (1 - custom_save_shape[x]) for
                             x in range(24)] for
                        yr in self.handyvars.aeo_years}
                elif "flatten_fraction" in tsv_adjustments[a].keys():
                    # Set the load flattening fraction
                    flatten_frac = tsv_adjustments[a]["flatten_fraction"]
                    # Determine the average load to use in implementing the
                    # load flattening fraction
                    avg_load = {yr: numpy.mean(eff_load[yr]) for
                                yr in self.handyvars.aeo_years}
                    # Reflect load flatting across a user specified hour
                    # range; the delta between each initial efficient hourly
                    # load and the average load is reduced by the flattening
                    # fraction
                    eff_load = {yr: [
                        eff_load[yr][x] + (
                            avg_load[yr] - eff_load[yr][x]) * flatten_frac if (
                            x in applicable_hrs and
                            avg_load[yr] > eff_load[yr][x]) else (
                            eff_load[yr][x] - (
                                eff_load[yr][x] - avg_load[yr]) *
                            flatten_frac if x in applicable_hrs else
                            eff_load[yr][x])
                        for x in range(0, 24)] for
                        yr in self.handyvars.aeo_years}
                else:
                    # Throw an error if the load reshaping operation name
                    # is invalid
                    raise KeyError(
                        "Invalid load reshaping operation name for measure: " +
                        self.name)

        return eff_load

    def convert_costs(self, convert_data, bldg_sect, mskeys, cost_meas,
                      cost_meas_units, cost_base_units, verbose):
        """Convert measure cost to comparable baseline cost units.

        Args:
            convert_data (dict): Measure cost unit conversions.
            bldg_sect (string): Applicable building sector for measure cost.
            mskeys (tuple): Full applicable market microsegment information for
                measure cost (mseg type->czone->bldg->fuel->end use->technology
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
            intensity_carb_meas, energy_total_scnd, tsv_adj):
        """Find total, competed, and efficient portions of a mkt. microsegment.

        Args:
            adopt_scheme (string): Assumed consumer adoption scenario.
            diffuse_params (NoneType): Parameters relating to the 'adjusted
                adoption' consumer choice model (currently a placeholder).
            mskeys (tuple): Dictionary key information for the currently
                partitioned market microsegment (mseg type->czone->bldg->
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

        Returns:
            Total, total-efficient, competed, and competed-efficient
            stock, energy, carbon, and cost market microsegments.
        """
        # Initialize stock, energy, and carbon mseg partition dicts, where the
        # dict keys will be years in the modeling time horizon
        stock_total, energy_total, carb_total, stock_total_meas, \
            energy_total_eff, carb_total_eff, stock_compete, \
            energy_compete, carb_compete, stock_compete_meas, \
            energy_compete_eff, carb_compete_eff, stock_total_cost, \
            energy_total_cost, carb_total_cost, stock_total_cost_eff, \
            energy_total_eff_cost, carb_total_eff_cost, \
            stock_compete_cost, energy_compete_cost, carb_compete_cost, \
            stock_compete_cost_eff, energy_compete_cost_eff, \
            carb_compete_cost_eff = ({} for n in range(24))

        # Initialize the portion of microsegment already captured by the
        # efficient measure as 0, and the portion baseline stock as 1.
        captured_eff_frac = 0
        captured_base_frac = 1

        # Set the relative energy performance of the current year's
        # competed and uncompeted stock that goes uncaptured
        rel_perf_uncapt = 1
        # Set time sensitive scaling factors for all uncaptured stock
        tsv_ecost_base, tsv_carb_base = [
            tsv_adj[x]["baseline"] for x in ["cost", "carbon"]]

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

        # Loop through and update stock, energy, and carbon mseg partitions for
        # each year in the modeling time horizon
        for yr in self.handyvars.aeo_years:

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
            energy_total[yr] = energy_total_init[yr] * mkt_scale_frac
            carb_total[yr] = carb_total_init[yr] * mkt_scale_frac * \
                tsv_carb_base

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
                # homes in year 1 of the modeling time horizon to begin
                # replacing that baseline stock; if so, the baseline
                # replacement fraction is the fraction of new construction
                # stock from previous years that has already been
                # captured by the baseline technology * (1 / baseline
                # lifetime + retrofit rate); if not, the baseline replacement
                # fraction is 0
                if mskeys[-1] == "new":
                    # Determine the fraction of total new stock in the given
                    # year that was previously captured by the baseline
                    # technology; screen for cases where the total new stock
                    # in the given year is zero
                    if stock_total_init[yr] != 0:
                        # Use try and except to handle cases where the market
                        # entry year occurs in the first year of the modeling
                        # time horizon (in this case, there were no previous
                        # years in which new stock could be captured by the
                        # baseline technology)
                        try:
                            new_stock_base_frac = stock_total_init[str(
                                self.market_entry_year - 1)] / \
                                stock_total_init[yr]
                        except KeyError:
                            new_stock_base_frac = 0
                    else:
                        new_stock_base_frac = 0

                    # If some of the total new stock was previously captured
                    # by the baseline technology, determine the annual baseline
                    # replacement fraction
                    if new_stock_base_frac != 0:
                        # Set maximum annual baseline replacement rate
                        base_repl_rt_max = (
                            (1 / life_base[yr]) + self.retro_rate) * \
                            new_stock_base_frac
                        # Set an indicator for when the previously captured
                        # base stock begins to turnover, using the baseline
                        # lifetime (zero or negative value indicates turnover)
                        turnover_base = life_base[yr] - (
                            int(yr) - int(sorted(self.handyvars.aeo_years)[0]))
                        # Handle case without life or retro. rate distributions
                        if type(base_repl_rt_max) != numpy.ndarray:
                            # If the previously captured baseline stock has
                            # begun to turnover, the turnover rate equals the
                            # max annual baseline replacement rate above
                            if turnover_base <= 0:
                                captured_base_replace_frac = base_repl_rt_max
                            # Otherwise, the turnover rate is zero
                            else:
                                captured_base_replace_frac = 0
                        # Handle case with life or retro. rate distributions
                        else:
                            # Ensure that all variables involved in the
                            # calculation are set to lists with the same length
                            # (and that list elements are of the float type)
                            turnover_base, base_repl_rt_max, \
                                captured_base_frac, captured_eff_frac = [
                                    numpy.repeat(float(x),
                                                 self.handyvars.nsamples) if
                                    type(x) in (int, float) else x for x in [
                                        turnover_base, base_repl_rt_max,
                                        captured_base_frac, captured_eff_frac]]
                            # Initialize the final base replacement fraction
                            # output as a list of zeros with the appropriate
                            # length
                            captured_base_replace_frac = numpy.zeros(
                                self.handyvars.nsamples)
                            # Using a for loop, complete the set of operations
                            # used above (under 'try') for each list element
                            for ind in range(self.handyvars.nsamples):
                                # If the previously captured baseline stock has
                                # begun to turnover, the turnover rate equals
                                # the max annual base replacement rate above
                                if turnover_base[ind] <= 0:
                                    captured_base_replace_frac[ind] = \
                                        base_repl_rt_max[ind]
                                # Otherwise, the turnover rate is zero
                                else:
                                    captured_base_replace_frac[ind] = 0
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
                        new_stock_add_frac = (stock_total[yr] - stock_total[
                            str(int(yr) - 1)]) / stock_total[yr]
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
                    secnd_mseg_adjkey][yr] += energy_total[yr]
                # Total stock
                secnd_adj_stk[
                    "original energy (total)"][secnd_mseg_adjkey][yr] += \
                    energy_total[yr]
                # Previously captured stock
                secnd_adj_stk["adjusted energy (previously captured)"][
                    secnd_mseg_adjkey][yr] += \
                    captured_eff_frac * energy_total[yr]
                # Competed stock
                secnd_adj_stk["adjusted energy (competed)"][
                    secnd_mseg_adjkey][yr] += competed_frac * energy_total[yr]
                # Competed and captured stock
                secnd_adj_stk["adjusted energy (competed and captured)"][
                    secnd_mseg_adjkey][yr] += \
                    competed_captured_eff_frac * energy_total[yr]

            # Update competed stock, energy, and carbon
            stock_compete[yr] = stock_total[yr] * competed_frac
            energy_compete[yr] = energy_total[yr] * competed_frac
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
                # Update time-sensitive efficiency scaling factors
                tsv_energy_eff, tsv_ecost_eff, tsv_carb_eff = [
                    tsv_adj[x]["efficient"][yr] for x in [
                        "energy", "cost", "carbon"]]
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
                # Update time-sensitive efficiency scaling factors
                tsv_energy_eff, tsv_ecost_eff, tsv_carb_eff = [
                    tsv_adj[x]["efficient"][yr] * base_turnover_wt +
                    y * (1 - base_turnover_wt) for x, y in zip([
                        "energy", "cost", "carbon"], [
                        tsv_energy_eff, tsv_ecost_eff, tsv_carb_eff])]

            # Update total-efficient and competed-efficient energy and
            # carbon, where "efficient" signifies the total and competed
            # energy/carbon remaining after measure implementation plus
            # non-competed energy/carbon. * Note: Efficient energy and
            # carbon is dependent upon whether the measure is on the market
            # for the given year (if not, use baseline energy and carbon)

            # Competed-efficient energy
            energy_compete_eff[yr] = energy_total[yr] * \
                competed_captured_eff_frac * rel_perf_capt * \
                tsv_energy_eff * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) + \
                energy_total[yr] * (
                    competed_frac - competed_captured_eff_frac) * \
                rel_perf_uncapt
            # Total-efficient energy
            energy_total_eff[yr] = energy_compete_eff[yr] + \
                (energy_total[yr] - energy_compete[yr]) * \
                captured_eff_frac * rel_perf_capt * \
                tsv_energy_eff * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) + \
                (energy_total[yr] - energy_compete[yr]) * \
                (1 - captured_eff_frac) * rel_perf_uncapt
            # Competed-efficient carbon
            carb_compete_eff[yr] = (carb_total_init[yr] * mkt_scale_frac) * \
                competed_captured_eff_frac * rel_perf_capt * \
                tsv_carb_eff * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                (intensity_carb_meas[yr] / intensity_carb_base[yr]) + \
                (carb_total_init[yr] * mkt_scale_frac) * (
                    competed_frac - competed_captured_eff_frac) * \
                rel_perf_uncapt * tsv_carb_base
            # Total-efficient carbon
            carb_total_eff[yr] = carb_compete_eff[yr] + \
                ((carb_total_init[yr] * mkt_scale_frac) -
                 (carb_total_init[yr] * mkt_scale_frac * competed_frac)) * \
                captured_eff_frac * rel_perf_capt * tsv_carb_eff * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                (intensity_carb_meas[yr] / intensity_carb_base[yr]) + \
                ((carb_total_init[yr] * mkt_scale_frac) -
                 (carb_total_init[yr] * mkt_scale_frac * competed_frac)) * (
                    1 - captured_eff_frac) * rel_perf_uncapt * tsv_carb_base

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
                    stock_compete_meas[yr] * (cost_meas + cost_base[yr]) + (
                        stock_compete[yr] - stock_compete_meas[yr]) * \
                    cost_base[yr]
                # Total-efficient stock cost (add-on measure)
                stock_total_cost_eff[yr] = stock_total_meas[yr] * (
                    cost_meas + cost_base[yr]) + (
                    stock_total[yr] - stock_total_meas[yr]) * cost_base[yr]
            else:
                # Competed-efficient stock cost (full service measure)
                stock_compete_cost_eff[yr] = \
                    stock_compete_meas[yr] * cost_meas + (
                        stock_compete[yr] - stock_compete_meas[yr]) * \
                    cost_base[yr]
                # Total-efficient stock cost (full service measure)
                stock_total_cost_eff[yr] = stock_total_meas[yr] * cost_meas \
                    + (stock_total[yr] - stock_total_meas[yr]) * cost_base[yr]

            # Competed baseline energy cost
            energy_compete_cost[yr] = \
                energy_compete[yr] * cost_energy_base[yr] * tsv_ecost_base
            # Competed energy-efficient cost
            energy_compete_cost_eff[yr] = energy_total[yr] * \
                competed_captured_eff_frac * rel_perf_capt * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                cost_energy_meas[yr] * tsv_ecost_eff + energy_total[yr] * (
                    competed_frac - competed_captured_eff_frac) * \
                cost_energy_base[yr] * rel_perf_uncapt * tsv_ecost_base
            # Total baseline energy cost
            energy_total_cost[yr] = energy_total[yr] * cost_energy_base[yr] * \
                tsv_ecost_base
            # Total energy-efficient cost
            energy_total_eff_cost[yr] = energy_compete_cost_eff[yr] + \
                (energy_total[yr] - energy_compete[yr]) * captured_eff_frac * \
                rel_perf_capt * (
                    site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                cost_energy_meas[yr] * tsv_ecost_eff + (
                    energy_total[yr] - energy_compete[yr]) * (
                    1 - captured_eff_frac) * rel_perf_uncapt * \
                cost_energy_base[yr] * tsv_ecost_base

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
                energy_compete_cost_eff, carb_compete_cost_eff]

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
                        'all ' not in t]
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
                                 (map_tech_orig == "all" or any([
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
        name (string): Package name.
        benefits (dict): Percent improvements in energy savings and/or cost
            reductions from packaging measures.
        remove (boolean): Determines whether package should be removed from
            analysis engine due to insufficient market source data.
        energy_outputs (dict): Indicates whether site energy or captured
            energy site-source conversions were used in measure preparation.
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
        out_break_norm (dict): Total energy use data to normalize
            savings values summed by climate zone, building class, and end use.
    """

    def __init__(self, measure_list_package, p, bens, handyvars):
        self.handyvars = handyvars
        self.contributing_ECMs = copy.deepcopy(measure_list_package)
        self.name = p
        # Check to ensure that measure name is proper length for plotting
        if len(self.name) > 40:
            raise ValueError(
                "ECM '" + self.name + "' name must be <= 40 characters")
        self.benefits = bens
        self.remove = False
        self.energy_outputs = {
            "site_energy": False, "captured_energy_ss": False}
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
        self.markets, self.out_break_norm = ({} for n in range(2))
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
                "mseg_out_break": copy.deepcopy(self.handyvars.out_break_in)}
            self.out_break_norm[adopt_scheme] = {
                yr: 0 for yr in self.handyvars.aeo_years}

    def merge_measures(self):
        """Merge the markets information of multiple individual measures.

        Note:
            Combines the 'markets' attributes of each individual measure into
            a packaged 'markets' attribute.

        Returns:
            Updated 'markets' attribute for a packaged measure that combines
            the 'markets' attributes of multiple individual measures.
        """
        # Loop through each measure and add its attributes to the merged
        # measure definition
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

            # Generate a dictionary with data about all the
            # microsegments that contribute to the packaged measure's
            # master microsegment
            for adopt_scheme in self.handyvars.adopt_schemes:
                # Set contributing microsegment data for individual measure
                msegs_meas = m.markets[adopt_scheme]["mseg_adjust"]
                # Set total energy use for individual measure (used to
                # break out results by climate, building class, and end use)
                mseg_out_break_adj = m.out_break_norm[adopt_scheme]
                # Set contributing microsegment data to update for package
                msegs_pkg = self.markets[adopt_scheme]["mseg_adjust"]
                # Loop through all measures in package and add contributing
                # microsegment data for measure
                for k in msegs_meas.keys():
                    # Add the measure's contributing microsegment markets;
                    # in cases where a measure's markets overlap with those of
                    # other measures in the package, remove these overlaps and
                    # adjust the measure's total energy use accordingly for
                    # the purpose of accurate output breakout calculations
                    if k == "contributing mseg keys and values":
                        for cm in msegs_meas[k].keys():
                            msegs_pkg[k], msegs_meas[k][cm], \
                                mseg_out_break_adj = \
                                self.merge_contrib_msegs(
                                    msegs_pkg[k], msegs_meas[k][cm],
                                    cm, m.measure_type, adopt_scheme,
                                    mseg_out_break_adj)
                    # Add all other contributing microsegment data for
                    # the measure
                    elif k in ["competed choice parameters",
                               "secondary mseg adjustments"]:
                        self.update_dict(msegs_pkg[k], msegs_meas[k])

                # Generate a dictionary including data on how much of the
                # packaged measure's baseline energy use is attributed to
                # each of the output climate zones, building types, and end
                # uses it applies to (normalized by the measure's total
                # baseline energy use below to yield output partitioning
                # fractions)
                self.merge_out_break(self.markets[adopt_scheme][
                    "mseg_out_break"], m.markets[adopt_scheme][
                    "mseg_out_break"], mseg_out_break_adj)

                # Add adjusted total energy use for the individual measure
                # to the total energy use for the packaged measure
                for yr in self.handyvars.aeo_years:
                    self.out_break_norm[adopt_scheme][yr] += \
                        mseg_out_break_adj[yr]

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
                if self.markets[adopt_scheme][
                        "master_mseg"]["stock"]["total"]["all"][yr] != 0:
                    self.markets[adopt_scheme]["master_mseg"][
                        "lifetime"]["baseline"][yr] = \
                        self.markets[adopt_scheme]["master_mseg"][
                        "lifetime"]["baseline"][yr] / \
                        self.markets[adopt_scheme][
                            "master_mseg"]["stock"]["total"]["all"][yr]
            self.markets[adopt_scheme]["master_mseg"]["lifetime"][
                "measure"] = self.markets[adopt_scheme][
                "master_mseg"]["lifetime"]["measure"] / key_chain_ct_package

            # Normalize baseline energy use values for each category in the
            # packaged measure's output breakout dictionary by the total
            # baseline energy use for the packaged measure across all its
            # contributing measures; this yields partitioning fractions that
            # will eventually be used to breakout the packaged measure's
            # energy and carbon markets/savings by climate zone, building
            # class, and end use
            self.div_keyvals(self.markets[adopt_scheme]["mseg_out_break"],
                             self.out_break_norm[adopt_scheme])

    def merge_contrib_msegs(
            self, msegs_pkg, msegs_meas, cm_key, meas_typ, adopt_scheme,
            mseg_out_break_adj):
        """Add a measure's contributing microsegment data to packaged measure.

        Args:
            msegs_pkg (dict): Existing contributing microsegment data for the
                packaged measure.
            msegs_meas (dict): Data for the contributing microsegment of an
                individual measure that is being merged into the package.
            cm_key (tuple): Microsegment key describing the contributing
                microsegment currently being added (e.g. czone->bldg, etc.)
            meas_typ (string): Individual measure type (full service / add-on).
            adopt_scheme (string): Assumed consumer adoption scenario.
            mseg_out_break_adj (dict): Total energy use data for the
                individual measure, used to breakout results by climate zone,
                building class, and end use.

        Returns:
            Updated contributing microsegment information for the package that
            incorporates the measure's contributing microsegment data.
        """
        # Determine what other measures in the package share the current
        # contributing microsegment for the individual measure
        overlap_meas = [
            x for x in self.contributing_ECMs if cm_key in x.markets[
                adopt_scheme]["mseg_adjust"][
                "contributing mseg keys and values"].keys()]

        # Update the contributing microsegment data for the individual measure
        # if the microsegment is shared with other measures in the package
        if len(overlap_meas) > 1:
            # Scale contributing microsegment energy, carbon and associated
            # cost data, as well as lifetime and sub-market fraction data,
            # by total number of overlapping measures in the package
            for k in ["stock", "energy", "carbon", "lifetime"]:
                # Scale down contributing microsegment energy data and
                # adjust total energy use for the measure accordingly, where
                # total energy is used in breaking out measure results
                # by climate zone, building class, and end use
                if k == "energy":
                    # Set total pre-scaled contributing microsegment energy
                    total_energy_orig = copy.deepcopy(
                        msegs_meas[k]["total"]["baseline"])
                    # Scale down contributing microsegment energy based on
                    # number of overlapping measures
                    self.div_keyvals_float(
                        msegs_meas[k], len(overlap_meas))
                    # Adjust the measure's total energy use to reflect
                    # the scaled down contributing microsegment energy use
                    mseg_out_break_adj = {yr: mseg_out_break_adj[yr] - (
                        total_energy_orig[yr] - msegs_meas[k]["total"][
                            "baseline"][yr]) for yr in
                        self.handyvars.aeo_years}
                # Scale down carbon and lifetime data
                else:
                    # Scale down contributing microsegment data based on
                    # number of overlapping measures
                    self.div_keyvals_float(
                        msegs_meas[k], len(overlap_meas))
                # Scale down cost data
                if k in ["stock", "energy", "carbon"]:
                    msegs_meas["cost"][k] = self.div_keyvals_float(
                        msegs_meas["cost"][k], len(overlap_meas))
            # Scale down sub-market fraction
            msegs_meas["sub-market scaling"] /= len(overlap_meas)

        # Check for additional energy savings and/or installed cost benefits
        # from packaging and apply these benefits if applicable
        self.apply_pkg_benefits(msegs_meas)

        # Add updated contributing microsegment information for individual
        # measure to the packaged measure, creating a new contributing
        # microsegment key if one does not already exist for the package
        if cm_key not in msegs_pkg.keys():
            msegs_pkg[cm_key] = msegs_meas
        else:
            msegs_pkg[cm_key] = self.add_keyvals(msegs_pkg[cm_key], msegs_meas)

        return msegs_pkg, msegs_meas, mseg_out_break_adj

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

    def apply_pkg_benefits(self, msegs_meas):
        """Apply additional energy savings or cost benefits from packaging.

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
        # If additional installed cost benefits are not None and are non-zero,
        # apply them to the measure's stock cost
        if cost_ben not in [None, 0]:
            for cs in ["competed", "total"]:
                msegs_meas["cost"]["stock"][cs]["efficient"] = {
                    key: msegs_meas["cost"]["stock"][cs]["efficient"][key] *
                    (1 - cost_ben) for key in self.handyvars.aeo_years}

        return msegs_meas

    def merge_out_break(self, pkg_brk, meas_brk, meas_brk_unnorm):
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
            meas_brk_unnorm (dict): Total energy use market for the
                individual measure, used to derive unnormalized energy use
                sub-markets for the individual measure to add to the package.

        Returns:
            Updated output breakout information for the packaged measure
            that incorporates the individual measure's breakout information.
        """
        for (k, i), (k2, i2) in zip(
                sorted(pkg_brk.items()), sorted(meas_brk.items())):
            if isinstance(i2, dict) and (
                    sorted(list(i2.keys())) != self.handyvars.aeo_years):
                self.merge_out_break(i, i2, meas_brk_unnorm)
            else:
                if k == k2 and (isinstance(i, dict) == isinstance(i2, dict)):
                    # If individual measure output breakout data is
                    # available to add to the current terminal leaf
                    # node for the package, either set the leaf node value
                    # to the unnormalized breakout data if no data already
                    # exist, or otherwise add the unnormalized breakout data
                    # for the individual measure to that of the package
                    if len(i.keys()) == 0:
                        pkg_brk[k] = {yr: i2[yr] * meas_brk_unnorm[yr] for
                                      yr in self.handyvars.aeo_years}
                    else:
                        pkg_brk[k] = {yr: pkg_brk[k][yr] +
                                      i2[yr] * meas_brk_unnorm[yr] for
                                      yr in self.handyvars.aeo_years}
                else:
                    raise KeyError(
                        "Output data dicts to merge for ECM '" + self.name +
                        " are not identically structured")
        return pkg_brk


def prepare_measures(measures, convert_data, msegs, msegs_cpl, handyvars,
                     cbecs_sf_byvint, tsv_data, base_dir, opts):
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
        cbecs_sf_byvint (dict): Commercial square footage by vintage data.
        tsv_data (dict): Data needed for time sensitive efficiency valuation.
        base_dir (string): Base directory.
        opts (object): Stores user-specified execution options.

    Returns:
        A list of dicts, each including a set of measure attributes that has
        been prepared for subsequent use in the analysis engine.

    Raises:
        ValueError: If more than one Measure object matches the name of a
            given input efficiency measure.
    """
    # Initialize Measure() objects based on 'measures_update' list
    meas_update_objs = [Measure(
        handyvars, opts.site_energy, opts.captured_energy, **m) for
        m in measures]

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
    [m.fill_mkts(msegs, msegs_cpl, convert_data, tsv_data, opts) for
     m in meas_update_objs]

    return meas_update_objs


def prepare_packages(packages, meas_update_objs, meas_summary,
                     handyvars, handyfiles, base_dir, opts):
    """Combine multiple measures into a single packaged measure.

    Args:
        packages (dict): Names of packages and measures that comprise them.
        measures (dict): Attributes of individual efficiency measures.
        opts (object): Stores user-specified execution options.

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
                    handyvars, opts.site_energy, opts.captured_energy,
                    **meas_summary_data[0])
                # Reset measure technology type and total energy (used to
                # normalize output breakout fractions) to their values in the
                # high level summary data (reformatted during initialization)
                meas_obj.technology_type = meas_summary_data[0][
                    "technology_type"]
                meas_obj.out_break_norm = meas_summary_data[0][
                    "out_break_norm"]
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
                measure_list_package, p["name"], p["benefits"], handyvars)
            # Merge measures in the package object
            packaged_measure.merge_measures()
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
        # For measure packages, replace 'contributing_ECMs'
        # objects list with a list of these measures' names
        if isinstance(m, MeasurePackage):
            m.contributing_ECMs = [
                x.name for x in m.contributing_ECMs]
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

    # Custom format all warning messages (ignore everything but
    # message itself) *** Note: sometimes yields error; investigate ***
    # warnings.formatwarning = custom_formatwarning
    # Instantiate useful input files object
    handyfiles = UsefulInputFiles(opts.captured_energy)

    # UNCOMMENT WITH ISSUE 188
    # # Ensure that all AEO-based JSON data are drawn from the same AEO version
    # if len(numpy.unique([splitext(x)[0][-4:] for x in [
    #         handyfiles.msegs_in, handyfiles.msegs_cpl_in,
    #         handyfiles.metadata]])) > 1:
    #     raise ValueError("Inconsistent AEO version used across input files")

    # Instantiate useful variables object
    handyvars = UsefulVars(base_dir, handyfiles)

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
                # removed either the "site_energy" or "captured_energy" cmd
                # line arguments and the measure definition was not already
                # prepared using these settings
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
                         meas_dict["name"]])) or\
                   (opts is None or opts.site_energy is False and
                    all([y["energy_outputs"]["site_energy"] is True for
                         y in meas_summary if y["name"] ==
                         meas_dict["name"]])) or \
                   (opts is None or opts.captured_energy is False and
                    all([y["energy_outputs"]["captured_energy_ss"] is True
                         for y in meas_summary if y["name"] ==
                         meas_dict["name"]])):
                    # Append measure dict to list of measure definitions
                    # to update if it meets the above criteria
                    meas_toprep_indiv.append(meas_dict)
            except ValueError as e:
                raise ValueError(
                    "Error reading in ECM '" + mi + "': " +
                    str(e)) from None

    # Find package measure definitions that are new or were edited since
    # the last time 'ecm_prep.py' routine was run, or are comprised of
    # individual measures that are new or were edited since the last time
    # 'ecm_prep.py' routine was run

    # Import packages JSON
    with open(path.join(base_dir, *handyfiles.ecm_packages), 'r') as mpk:
        try:
            meas_toprep_package_init = json.load(mpk)
        except ValueError as e:
            raise ValueError(
                "Error reading in ECM package '" + handyfiles.ecm_packages +
                "': " + str(e)) from None
    # Initialize list of measure package dicts to prepare
    meas_toprep_package = []
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
                *handyfiles.ecm_compete_data))]) or (
                len(m_exist) == 1 and any([m[x] != m_exist[0][x] for x in [
                    "contributing_ECMs", "benefits"]])):
            meas_toprep_package.append(m)
        # Raise an error if the current package matches the name of
        # multiple previously prepared packages
        elif len(m_exist) > 1:
            raise ValueError(
                "Multiple existing ECM names match '" + m["name"] + "'")

    # If one or more measure definition is new or has been edited, proceed
    # further with 'ecm_prep.py' routine; otherwise end the routine
    if len(meas_toprep_indiv) > 0 or len(meas_toprep_package) > 0:

        # Import baseline microsegments
        with open(path.join(base_dir, *handyfiles.msegs_in), 'r') as msi:
            try:
                msegs = json.load(msi)
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.msegs_in + "': " + str(e)) from None
        # Import baseline cost, performance, and lifetime data
        with open(path.join(base_dir, *handyfiles.msegs_cpl_in), 'r') as bjs:
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
        # Import load shape, price, and marginal emissions data needed for
        # time sensitive analysis of measure energy efficiency impacts
        with open(path.join(
                base_dir, *handyfiles.tsv_data), 'r') as tsv:
            try:
                tsv_data = json.load(tsv)
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.tsv_data + "': " + str(e)) from None
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

        # Prepare new or edited measures for use in analysis engine
        meas_prepped_objs = prepare_measures(
            meas_toprep_indiv, convert_data, msegs, msegs_cpl, handyvars,
            cbecs_sf_byvint, tsv_data, base_dir, opts)

        # Prepare measure packages for use in analysis engine (if needed)
        if meas_toprep_package:
            meas_prepped_objs = prepare_packages(
                meas_toprep_package, meas_prepped_objs, meas_summary,
                handyvars, handyfiles, base_dir, opts)

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
            # Measure not already in active measures list (add name to list)
            if m["name"] not in run_setup["active"]:
                run_setup["active"].append(m["name"])
            # Measure in inactive measures list (remove name from list)
            if m["name"] in run_setup["inactive"]:
                run_setup["inactive"] = [x for x in run_setup[
                    "inactive"] if x != m["name"]]

        # Notify user that all measure preparations are completed
        print('All ECM updates complete; writing output data...')

        # Write prepared measure competition data to zipped JSONs
        for ind, m in enumerate(meas_prepped_objs):
            # Assemble folder path for measure competition data
            meas_folder_name = path.join(*handyfiles.ecm_compete_data)
            # Assemble file name for measure competition data
            meas_file_name = m.name + ".pkl.gz"
            with gzip.open(path.join(
                    base_dir, meas_folder_name, meas_file_name), 'w') as zp:
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
    # Optional flag to print all warning messages to stdout
    parser.add_argument("--verbose", action="store_true",
                        help="Print all warnings to stdout")
    # Object to store all user-specified execution arguments
    opts = parser.parse_args()

    # Set current working directory
    base_dir = getcwd()
    main(base_dir)
    hours, rem = divmod(time.time() - start_time, 3600)
    minutes, seconds = divmod(rem, 60)
    print("--- Runtime: %s (HH:MM:SS.mm) ---" %
          "{:0>2}:{:0>2}:{:05.2f}".format(int(hours), int(minutes), seconds))
