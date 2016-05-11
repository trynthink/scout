#!/usr/bin/env python3
import json
import itertools
import numpy
import copy
import re
from numpy.linalg import LinAlgError
from collections import OrderedDict
import warnings
from urllib.parse import urlparse
# User-specified inputs (placeholders for now, eventually draw from GUI?)
adopt_scheme = 'Technical potential'  # Determines measure adoption scenario
adjust_savings = True  # Determines whether measures are competed or not
retro_rate = 0.02  # Fraction of building stock retrofitted each year
# Note: set retrofit rate to zero to compare against P-Tool results, where
# no retrofits are considered in the calculations
nsamples = 50  # Number of samples in cases with input distributions

# Define measures/microsegments files
measures_file = "measures_test.json"
microsegments_file = "microsegments_out.json"
mseg_base_costperflife_info = "base_costperflife.json"
measure_packages_file = 'measure_packages_test.json'

# Define and import site-source conversions and carbon emissions data
cost_sitesource_carb = "Cost_S-S_CO2.txt"
cost_ss_carb = numpy.genfromtxt(cost_sitesource_carb,
                                names=True, delimiter='\t',
                                dtype=None)

# Set fuel type site-source conversion factors dict
ss_conv = {"electricity (grid)": cost_ss_carb[7],
           "natural gas": cost_ss_carb[8],
           "distillate": cost_ss_carb[9], "other fuel": cost_ss_carb[9]}

# Set fuel type carbon intensity dict
carb_int = {"electricity (grid)": cost_ss_carb[10],
            "natural gas": cost_ss_carb[11],
            "distillate": cost_ss_carb[12], "other fuel": cost_ss_carb[12]}

# Set energy costs dict
ecosts = {"residential": {"electricity (grid)": cost_ss_carb[0],
                          "natural gas": cost_ss_carb[1],
                          "distillate": cost_ss_carb[2],
                          "other fuel": cost_ss_carb[2]},
          "commercial": {"electricity (grid)": cost_ss_carb[3],
                         "natural gas": cost_ss_carb[4],
                         "distillate": cost_ss_carb[5],
                         "other fuel": cost_ss_carb[5]}}
# Set carbon costs dict
ccosts = cost_ss_carb[6]

# Set a general discount rate for cost calculations
rate = 0.07

# Set end use-specific discount rate distributions for use in commercial
# sector measure competition.  For now, specify this manually using Table
# E-1 of the commercial demand module documentation.  * Note: in the future,
# a routine will be added that imports this information from the most recent
# AEO kprem.txt raw data file
com_timeprefs = {
    "rates": [10.0, 1.0, 0.45, 0.25, 0.15, 0.065, 0.0],
    "distributions": {
        "heating": [0.265, 0.226, 0.196, 0.192, 0.105, 0.013, 0.003],
        "cooling": [0.264, 0.225, 0.193, 0.192, 0.106, 0.016, 0.004],
        "water heating": [0.263, 0.249, 0.212, 0.169, 0.097, 0.006, 0.004],
        "ventilation": [0.265, 0.226, 0.196, 0.192, 0.105, 0.013, 0.003],
        "cooking": [0.261, 0.248, 0.214, 0.171, 0.097, 0.005, 0.004],
        "lighting": [0.264, 0.225, 0.193, 0.193, 0.085, 0.013, 0.027],
        "refrigeration": [0.262, 0.248, 0.213, 0.170, 0.097, 0.006, 0.004]}}

# Define a summary JSON file. For now, yield separate output files for a
# competed and non-competed case and technical potential and non-technical
# potential case to help organize test plotting efforts
if adopt_scheme is 'Technical potential' and adjust_savings is True:
    json_output_file = "output_summary_competed.json"
elif adopt_scheme is 'Technical potential' and adjust_savings is False:
    json_output_file = "output_summary_noncompeted.json"
elif adopt_scheme is not'Technical potential' and adjust_savings is True:
    json_output_file = "output_summary_competed_nontp.json"
else:
    json_output_file = "output_summary_noncompeted_nontp.json"

# Define end use cases where relative performance calculation should be
# inverted (i.e., a lower air change rate is an improvement)
inverted_relperf_list = ["ACH50", "CFM/sf", "kWh/yr", "kWh/day", "SHGC",
                         "HP/CFM"]

# Initialize a dictionary that will store energy and carbon market/savings
# output breakouts for each measure. Breakouts are by climate zone,
# building type ('Residential' or 'Commercial'), and end use

# First, establish a series of dicts that map the climate zone, building
# type, and end use breakouts used in measure microsegment definitions to
# the higher-level breakouts desired for measure outputs

# Climate zone breakout mapping
out_break_czones = OrderedDict([
    ('AIA CZ1', 'AIA_CZ1'), ('AIA CZ2', 'AIA_CZ2'),
    ('AIA CZ3', 'AIA_CZ3'), ('AIA CZ4', 'AIA_CZ4'),
    ('AIA CZ5', 'AIA_CZ5')])
# Building type breakout mapping
out_break_bldgtypes = OrderedDict([
    ('Residential', [
        'single family home', 'multi family home', 'mobile home']),
    ('Commercial', [
        'assembly', 'education', 'food sales', 'food service',
        'health care', 'mercantile/service', 'lodging', 'large office',
        'small office', 'warehouse', 'other'])])
# End use breakout mapping
out_break_enduses = OrderedDict([
    ('Heating', ["heating", "secondary heating"]),
    ('Cooling', ["cooling"]),
    ('Ventilation', ["ventilation"]),
    ('Lighting', ["lighting"]),
    ('Water Heating', ["water heating"]),
    ('Refrigeration', ["refrigeration", "other (grid electric)"]),
    ('Computers and Electronics', [
        "PCs", "non-PC office equipment",
        "TVs", "computers"]),
    ('Other', ["cooking", "drying", "MELs", "other (grid electric)"])])

# Use the above output categories to establish a dictionary with blank
# values at terminal leaf nodes; this dict will eventually store
# partitioning fractions needed to breakout the measure results

# Determine all possible outcome category combinations
out_levels = [out_break_czones.keys(), out_break_bldgtypes.keys(),
              out_break_enduses.keys()]
out_levels_keys = list(itertools.product(*out_levels))
# Create dictionary using outcome category combinations as key chains
out_break_in = OrderedDict()
for kc in out_levels_keys:
    current_level = out_break_in
    for ind, elem in enumerate(kc):
        if elem not in current_level:
            current_level[elem] = OrderedDict()
        current_level = current_level[elem]

# Establish an initial approved list of websites for sub-market scaling data
valid_submkt_urls = [
    '.eia.gov', '.doe.gov', '.energy.gov', '.data.gov', '.energystar.gov',
    '.epa.gov', '.census.gov', '.pnnl.gov', '.lbl.gov',
    '.nrel.gov', 'www.sciencedirect.com', 'www.costar.com',
    'www.navigantresearch.com']


# Define class for measure objects
class Measure(object):

    def __init__(self, **kwargs):
        # Initialize master market microsegment, master savings,
        # contributing microsegment information, and market/savings
        # breakout attributes as dicts
        self.master_mseg = {}
        self.master_savings = {}
        self.mseg_adjust = {}
        self.mseg_out_break = {}

        # Initialize attributes from JSON
        for key, value in kwargs.items():
            setattr(self, key, value)

    def mseg_find_partition(self, mseg_in, base_costperflife_in, adopt_scheme,
                            out_break_in, retro_rate):
        """ Given an input measure with microsegment selection information and two
        input dicts with AEO microsegment cost and performance and stock and
        energy consumption information, find: 1) total and competed stock,
        2) total, competed, and energy efficient consumption and 3)
        associated cost of the competed stock """

        # Initialize master microsegment stock, energy, carbon, cost, and
        # lifetime information dict
        mseg_master = {
            "stock": {
                "total": {"all": None, "measure": None},
                "competed": {"all": None, "measure": None}},
            "energy": {
                "total": {"baseline": None, "efficient": None},
                "competed": {"baseline": None, "efficient": None}},
            "carbon": {
                "total": {"baseline": None, "efficient": None},
                "competed": {"baseline": None, "efficient": None}},
            "cost": {
                "stock": {
                    "total": {"baseline": None, "efficient": None},
                    "competed": {"baseline": None, "efficient": None}},
                "energy": {
                    "total": {"baseline": None, "efficient": None},
                    "competed": {"baseline": None, "efficient": None}},
                "carbon": {
                    "total": {"baseline": None, "efficient": None},
                    "competed": {"baseline": None, "efficient": None}}},
            "lifetime": {"baseline": None, "measure": None}}

        # Initialize a dict that registers all microsegments that contribute
        # to the current measure's master microsegment; the consumer choice
        # information associated with these contributing microsegments;
        # information needed to scale down secondary heating/cooling
        # microsegments in accordance with user-defined sub-markets,
        # baseline stocks-and-flows, and competed market share adjustments for
        # associated primary lighting microsegments; and information needed to
        # adjust the microsegments' values in heating/cooling measure cases
        # where the microsegment overlaps with other active measure
        # microsegments across the supply-side and the demand-side (e.g., an
        # ASHP microsegment that overlaps with a windows (conduction)
        # microsegment). Together, this information will be used in the
        # 'adjust_savings' function below to ensure there is no overestimation
        # of energy/carbon impacts across multiple competing measures
        mseg_adjust = {
            "contributing mseg keys and values": {},
            "competed choice parameters": {},
            "secondary mseg adjustments": {
                "sub-market": {
                    "original stock (total)": {},
                    "adjusted stock (sub-market)": {}},
                "stock-and-flow": {
                    "original stock (total)": {},
                    "adjusted stock (previously captured)": {},
                    "adjusted stock (competed)": {},
                    "adjusted stock (competed and captured)": {}},
                "market share": {
                    "original stock (total captured)": {},
                    "original stock (competed and captured)": {},
                    "adjusted stock (total captured)": {},
                    "adjusted stock (competed and captured)": {}}},
            "supply-demand adjustment": {
                "savings": {},
                "total": {}},
            "savings updated": False}

        # Initialize a dict that stores the partitioning fractions used to
        # breakout all measure energy and carbon market/savings outputs by
        # climate zone, building type, and end use
        mseg_out_break = copy.deepcopy(out_break_in)

        # If multiple runs are required to handle probability distributions on
        # measure inputs, set a number to seed each random draw of cost,
        # performance, and or lifetime with for consistency across all
        # microsegments that contribute to the measure's master microsegment
        if nsamples is not None:
            rnd_sd = numpy.random.randint(10000)

        # Initialize a counter of valid key chains
        key_chain_ct = 0

        # Initialize flags for invalid information about sub-market fraction
        # source, URL, and derivation
        sbmkt_source_invalid, sbmkt_URL_invalid, sbmkt_derive_invalid = (
            0 for n in range(3))

        # Initialize variable indicating use of sq.ft. as microsegment stock
        sqft_subst = 0

        # Establish a flag for a commercial lighting case where the user has
        # not specified secondary end use effects on heating and cooling.  In
        # this case, secondary effects are added automatically by adjusting
        # the "lights" thermal load component in accordance with the lighting
        # efficiency change (e.g., a 40% relative savings from efficient
        # lighting equipment translates to a 40% increase in heating loads and
        # 40% decrease in cooling load)
        lighting_secondary = False

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

        # Determine "secondary" microsegment key chains and add to the
        # "primary" microsegment key chain list, if needed. In a commercial
        # lighting measure case where no secondary microsegment is specified,
        # use the "lights" thermal load component microsegments to represent
        # secondary end use effects of the lighting measure
        if self.end_use["secondary"] is not None:
            ms_iterable_second, ms_lists_second = self.create_keychain(
                "secondary")
            ms_iterable.extend(ms_iterable_second)
        elif "lighting" in self.end_use["primary"] and \
            any([x not in ["single family home", "multi family home",
                           "mobile home"] for x in self.bldg_type]):
                    # Set secondary lighting microsegment flag to True
                    lighting_secondary = True
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
                    self.fuel_type["secondary"] = ["electricity (grid)",
                                                   "natural gas",
                                                   "other"]
                    # Set relevant secondary end uses
                    self.end_use["secondary"] = ["heating",
                                                 "secondary heating",
                                                 "cooling"]
                    # Set secondary technology type ("demand" as the lighting
                    # measure affects heating/cooling loads)
                    self.technology_type["secondary"] = "demand"
                    # Set secondary technology class to "lights", which will
                    # access the portion of commercial heating/cooling demand
                    # that is attributable to waste heat from lights
                    self.technology["secondary"] = "lights"

                    # Determine secondary microsegment key chains and add to
                    # the primary microsegment key chain list
                    ms_iterable_second, ms_lists_second = self.create_keychain(
                        "secondary")
                    ms_iterable.extend(ms_iterable_second)

        # Loop through discovered key chains to find needed performance/cost
        # and stock/energy information for measure
        for ind, mskeys in enumerate(ms_iterable):

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
            # lifetime units only), or c) Any of performance/cost/lifetime/
            # units is a dict which must be parsed further to reach the final
            # value. * Note: cost/lifetime/sub-market information is not
            # updated for "secondary" microsegments, which do not pertain to
            # these variables; lifetime units are assumed to be years
            if ind == 0 or (ms_iterable[ind][0] != ms_iterable[ind - 1][0]) \
               or isinstance(self.energy_efficiency, dict):
                perf_meas = self.energy_efficiency
            if ind == 0 or (ms_iterable[ind][0] != ms_iterable[ind - 1][0]) \
               or isinstance(self.energy_efficiency_units, dict):
                perf_units = self.energy_efficiency_units
            if mskeys[0] == "secondary":
                cost_meas = 0
                cost_units = "NA"
                life_meas = 0
                # * Note: no unique sub-market scaling fractions for secondary
                # microsegments; secondary microsegments are only scaled down
                # by the sub-market fraction for their associated primary
                # microsegments
                mkt_scale_frac, mkt_scale_frac_source = (
                    None for n in range(2))
            else:
                if ind == 0 or isinstance(
                        self.installed_cost, dict):
                    cost_meas = self.installed_cost
                if ind == 0 or isinstance(
                        self.cost_units, dict):
                    cost_units = self.cost_units
                if ind == 0 or isinstance(
                        self.product_lifetime, dict):
                    life_meas = self.product_lifetime
                if ind == 0 or isinstance(
                        self.market_scaling_fractions, dict):
                    mkt_scale_frac = self.market_scaling_fractions
                if ind == 0 or isinstance(
                        self.market_scaling_fractions_source, dict):
                    mkt_scale_frac_source = self.market_scaling_fractions_source

            # Set appropriate site-source conversion factor, energy cost, and
            # carbon intensity for given key chain
            if mskeys[3] in ss_conv.keys():
                # Set baseline and measure site-source conversions and
                # carbon intensities, accounting for any fuel switching from
                # baseline technology to measure technology
                if self.fuel_switch_to is None:
                    site_source_conv_base, site_source_conv_meas = (
                        ss_conv[mskeys[3]] for n in range(2))
                    intensity_carb_base, intensity_carb_meas = (
                        carb_int[mskeys[3]] for n in range(2))
                else:
                    site_source_conv_base = ss_conv[mskeys[3]]
                    site_source_conv_meas = ss_conv[self.fuel_switch_to]
                    intensity_carb_base = carb_int[mskeys[3]]
                    intensity_carb_meas = carb_int[self.fuel_switch_to]

            # Initialize dicts of microsegment information specific to this run
            # of for loop; also initialize dict for mining sq.ft. information
            # to be used as stock for microsegments without no. units info.;
            # finally, initialize a dict to store information about the portion
            # of this microsegment's stock and energy that is attributable to
            # new buildings. The new buildings fraction will be used in the
            # partitition_microsegment function below
            base_costperflife = base_costperflife_in
            mseg = mseg_in
            mseg_sqft_stock = mseg_in
            new_bldg_frac = {"added": {}, "total": {}}

            # Initialize a dict for relative performance (broken out by year in
            # modeling time horizon)
            rel_perf = {}

            # Loop recursively through the above dicts, moving down key chain
            for i in range(0, len(mskeys)):
                # Check for key in dict level
                if mskeys[i] in base_costperflife.keys() or mskeys[i] in \
                   ["primary", "secondary", "new", "existing", None]:
                    # Skip over "primary" or "secondary" key in updating
                    # cost and lifetime information (not relevant)
                    if mskeys[i] not in [
                            "primary", "secondary", "new", "existing", None]:

                        # Restrict base cost/performance/lifetime dict to key
                        # chain info.
                        base_costperflife = base_costperflife[mskeys[i]]

                        # Restrict stock/energy dict to key chain info.
                        mseg = mseg[mskeys[i]]

                        # Restrict sq.ft. dict to key chain info.
                        if i < 3:  # Note: sq.ft. broken out 2 levels
                            mseg_sqft_stock = mseg_sqft_stock[mskeys[i]]

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

                    # If updating heating/cooling measure microsegment,
                    # record the total amount of overlapping supply and
                    # demand-side energy. For example, given a supply-side
                    # cooling measure microsegment key chain of ['AIA_CZ1',
                    # 'single family home', 'electricity (grid)', 'cooling',
                    # 'supply', 'ASHP'], the total cooling energy that overlaps
                    # with demand-side measures (e.g. highly insulating window)
                    # is defined by the key ['AIA_CZ1', 'single family home',
                    # 'electricity (grid)', 'cooling']. This information will
                    # be used in the 'adjust_savings' function below to
                    # adjust supply-side measure savings by the fraction
                    # of overlapping demand-side savings, and vice versa.
                    if (mskeys[i] == "supply" or mskeys[i] == "demand") \
                       and mskeys[i + 1] in mseg.keys():
                        # Find the total overlapping heating/cooling energy
                        # by summing together the energy for all microsegments
                        # under the current 'supply' or 'demand' levels of the
                        # key chain (e.g. could be 'ASHP', 'GSHP', 'boiler',
                        # 'windows (conduction)', 'infiltration', etc.).
                        # Note that for a given climate zone, building type,
                        # and fuel type, heating/cooling supply and demand
                        # energy should be equal.
                        for ind, ks in enumerate(mseg.keys()):
                            if ind == 0:
                                adj_vals = copy.deepcopy(mseg[ks]["energy"])
                            else:
                                adj_vals = self.add_keyvals(
                                    adj_vals, mseg[ks]["energy"])

                        # Case with no existing 'windows' contributing
                        # microsegment for the current climate zone,
                        # building type, fuel type, and end use (create new
                        # 'supply-demand adjustment' information)
                        if contrib_mseg_key not in mseg_adjust[
                                "supply-demand adjustment"]["total"].keys():
                            # Adjust the resultant total overlapping energy
                            # values by appropriate site-source conversion
                            # factor and record as the measure's 'supply-demand
                            # adjustment' information
                            mseg_adjust["supply-demand adjustment"]["total"][
                                str(contrib_mseg_key)] = {
                                    key: val * site_source_conv_base[
                                        key] for key, val in adj_vals.items()}
                            # Set overlapping energy savings values to zero in
                            # the measure's 'supply-demand adjustment'
                            # information for now (updated as necessary in the
                            # 'adjust_savings' function below)
                            mseg_adjust["supply-demand adjustment"]["savings"][
                                str(contrib_mseg_key)] = dict.fromkeys(
                                    adj_vals.keys(), 0)
                        # Case with existing 'windows' contributing
                        # microsegment for the current climate zone, building
                        # type, fuel type, and end use (add to existing
                        # 'supply-demand adjustment' information)
                        else:
                            # Adjust the resultant total overlapping energy
                            # values by appropriate site-source conversion
                            # factor and add to existing 'supply-demand
                            # adjustment' information for the current windows
                            # microsegment
                            add_adjust = {
                                key: val * site_source_conv_base[
                                    key] for key, val in adj_vals.items()}
                            mseg_adjust["supply-demand adjustment"]["total"][
                                str(contrib_mseg_key)] = self.add_key_vals(
                                    mseg_adjust["supply-demand adjustment"][
                                        "total"][str(contrib_mseg_key)],
                                    add_adjust)

                # If no key match, break the loop
                else:
                    if mskeys[i] is not None:
                        mseg = {}
                    break

            # If mseg dict isn't defined to "stock" info. level, go no further
            if "stock" not in list(mseg.keys()):
                continue
            # Otherwise update all stock/energy/cost information for each year
            else:
                # Restrict valid key chain count to "primary" microsegment
                # key chains only, as the key chain count is used later in
                # stock and stock cost calculations, which secondary
                # microsegments do not contribute to
                if mskeys[0] == "primary":
                    key_chain_ct += 1

                # If a sub-market scaling fraction is to be applied to the
                # current baseline microsegment, check that the source
                # information for the fraction is sufficient; if not, remove
                # the measure from further analysis
                if mkt_scale_frac_source is not None:
                    # Establish sub-market fraction general source, URL, and
                    # derivation information

                    # Set general source info. for the sub-market fraction
                    source_info = [
                        mkt_scale_frac_source['title'],
                        mkt_scale_frac_source['author'],
                        mkt_scale_frac_source['organization'],
                        mkt_scale_frac_source['year']]
                    # Set URL for the sub-market fraction
                    URL = mkt_scale_frac_source['URL']
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
                        warnings.warn((
                            "WARNING: " + self.name + " has invalid "
                            "sub-market scaling fraction source title, author,"
                            " organization, and/or year information"))
                        # Set invalid source information flag to 1
                        sbmkt_source_invalid = 1
                    # Check sub-market fraction URL, yield warning if URL is
                    # invalid and invalid URL flag hasn't already been raised
                    # for this measure
                    if sbmkt_URL_invalid != 1:
                        # Parse the URL into components (addressing scheme,
                        # network location, etc.)
                        url_check = urlparse(URL)
                        # Check for valid URL address scheme and network
                        # location components
                        if (any([len(url_check.scheme),
                                 len(url_check.netloc)]) == 0 or
                            all([x not in url_check.netloc for x in
                                 valid_submkt_urls])):
                            # Print invalid URL warning
                            warnings.warn((
                                "WARNING: " + self.name + " has invalid "
                                "sub-market scaling fraction source URL "
                                "information"))
                            # Set invalid URL flag to 1
                            sbmkt_URL_invalid = 1
                    # Check sub-market fraction derivation information, yield
                    # warning if invalid
                    if not isinstance(frac_derive, str):
                        # Print invalid derivation warning
                        warnings.warn((
                            "WARNING: " + self.name + " has invalid "
                            "sub-market scaling fraction derivation "
                            "information"))
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
                            sbmkt_URL_invalid == 1):
                        # Print measure removal warning
                        warnings.warn((
                            "WARNING (CRITICAL): " + self.name + " has "
                            "insufficient sub-market source information and "
                            "will be removed from analysis"))
                        # Reset valid key chain count to 999 flag
                        key_chain_ct = 999
                        # Reset measure 'active' attribute to zero
                        self.active = 0
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
                    perf_meas = self.rand_list_gen(perf_meas, nsamples)
                    # Set any measure performance values less than zero to
                    # zero, for cases where performance isn't relative
                    if perf_units != 'relative savings (constant)' and \
                        type(perf_units) is not list and any(
                            perf_meas < 0) is True:
                        perf_meas[numpy.where(perf_meas < 0)] == 0

                if isinstance(cost_meas, list) and isinstance(cost_meas[0],
                                                              str):
                    # Sample measure cost values
                    cost_meas = self.rand_list_gen(cost_meas, nsamples)
                    # Set any measure cost values less than zero to zero
                    if any(cost_meas < 0) is True:
                        cost_meas[numpy.where(cost_meas < 0)] == 0
                if isinstance(life_meas, list) and isinstance(life_meas[0],
                                                              str):
                    # Sample measure lifetime values
                    life_meas = self.rand_list_gen(life_meas, nsamples)
                    # Set any measure lifetime values in list less than zero
                    # to 1
                    if any(life_meas < 0) is True:
                        life_meas[numpy.where(life_meas < 0)] == 1
                elif isinstance(life_meas, float) or \
                        isinstance(life_meas, int) and mskeys[0] == "primary":
                    # Set measure lifetime point values less than zero to 1
                    # (minimum lifetime)
                    if life_meas < 1:
                        life_meas = 1

                # Determine relative measure performance after checking for
                # consistent baseline/measure performance and cost units;
                # make an exception for cases where performance is specified
                # in 'relative savings' units (no explicit check
                # of baseline units needed in this case)
                if perf_units == 'relative savings (constant)' or \
                   (isinstance(perf_units, list) and
                    perf_units[0] == 'relative savings (dynamic)') or \
                    (base_costperflife["performance"]["units"] ==
                        perf_units and base_costperflife[
                        "installed cost"]["units"] == cost_units):

                    # Set base performance dict
                    perf_base = base_costperflife["performance"]["typical"]

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
                        # specified, draw from the "lighting_secondary"
                        # variable to determine relative performance for this
                        # secondary microsegment; in all other cases where
                        # relative savings are directly user-specified in the
                        # measure definition, calculate relative performance
                        # based on the relative savings value
                        if type(perf_meas) != numpy.ndarray and \
                           perf_meas == "Missing (secondary lighting)":
                            # If relevant secondary lighting performance
                            # information doesn't exist, throw an error
                            if type(lighting_secondary) == dict:
                                # Relative performance for heating end uses
                                if mskeys[4] in ["heating",
                                                 "secondary heating"]:
                                    rel_perf = lighting_secondary["heat"]
                                # Relative performance for cooling end uses
                                else:
                                    rel_perf = lighting_secondary["cool"]
                            else:
                                raise ValueError("No performance value available for \
                                                 secondary lighting end use \
                                                 effect calculation!")
                        else:
                            # Set the original measure relative savings value
                            # (potentially adjusted via re-baselining)
                            perf_meas_orig = copy.deepcopy(perf_meas)
                            # Loop through all years in modeling time horizon
                            # and calculate relative measure performance
                            for yr in perf_base.keys():
                                # If relative savings must be adjusted to
                                # account for changes in baseline performance,
                                # scale the relative savings value by the
                                # ratio of current year baseline to that of
                                # an anchor year specified with the measure
                                # performance units
                                if isinstance(perf_units, list):
                                    if base_costperflife[
                                        "performance"]["units"] \
                                            not in inverted_relperf_list:
                                        perf_meas = 1 - (perf_base[yr] / (
                                            perf_base[str(perf_units[1])] /
                                            (1 - perf_meas_orig)))
                                    else:
                                        perf_meas = 1 - (
                                            (perf_base[str(perf_units[1])] *
                                             (1 - perf_meas_orig)) /
                                            perf_base[yr])
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
                    elif perf_units not in inverted_relperf_list:
                        for yr in perf_base.keys():
                            rel_perf[yr] = (perf_base[yr] / perf_meas)
                    else:
                        for yr in perf_base.keys():
                            rel_perf[yr] = (perf_meas / perf_base[yr])

                    # If looping through a commercial lighting microsegment
                    # where secondary end use effects (heating/cooling) are not
                    # specified by the user and must be added, store the
                    # relative performance of the efficient lighting equipment
                    # for later use in updating these secondary microsegments
                    if mskeys[4] == "lighting" and mskeys[0] == "primary" and\
                            lighting_secondary is True:

                        # The impact of a lighting efficiency change on heating
                        # is the negative of that on cooling, as improved
                        # lighting efficiency reduces waste heat from lights,
                        # increasing heating load and decreasing cooling load
                        secondary_perf_cool = rel_perf
                        secondary_perf_heat = copy.deepcopy(rel_perf)
                        secondary_perf_heat.update((x, (2 - y)) for x, y in
                                                   secondary_perf_heat.items())

                        # Store the secondary microsegment performance
                        # information for later use in updating these secondary
                        # microsegments
                        lighting_secondary = {"heat": secondary_perf_heat,
                                              "cool": secondary_perf_cool}

                    # Set base stock cost. Note that secondary microsegments
                    # make no contribution to the stock cost calculation, as
                    # they only affect energy/carbon and associated costs
                    if mskeys[0] == "secondary":
                        cost_base = dict.fromkeys(mseg["energy"].keys(), 0)
                    else:
                        cost_base = base_costperflife[
                            "installed cost"]["typical"]
                else:
                    raise KeyError('Inconsistent performance or cost units!')

                # Set base lifetime.  Note that secondary microsegments make
                # no contribution to the lifetime calculation, as they only
                # affect energy/carbon and associated costs
                if mskeys[0] == "secondary":
                    life_base = dict.fromkeys(mseg["energy"].keys(), 0)
                else:
                    life_base = base_costperflife["lifetime"]["average"]
                    # Set any base lifetime values less than 1 to 1
                    # (minimum lifetime)
                    for yr in life_base.keys():
                        if life_base[yr] < 1:
                            life_base[yr] = 1

                # Reduce energy costs and stock turnover info. to appropriate
                # building type and - for energy costs - fuel, before
                # entering into "partition_microsegment"
                if mskeys[2] in ["single family home", "mobile home",
                                 "multi family home"]:
                    # Update residential baseline and measure energy cost
                    # information, accounting for any fuel switching from
                    # baseline technology to measure technology
                    if self.fuel_switch_to is None:
                        cost_energy_base, cost_energy_meas = (
                            ecosts["residential"][mskeys[3]] for n in range(2))
                    else:
                        cost_energy_base = ecosts["residential"][mskeys[3]]
                        cost_energy_meas = ecosts["residential"][
                            self.fuel_switch_to]

                    # Update new buildings fraction information
                    for yr in sorted(mseg["energy"].keys()):
                        # Find fraction of total buildings that are
                        # newly constructed in the current year
                        new_bldg_frac["added"][yr] = \
                            mseg_sqft_stock["new homes"][yr] / \
                            mseg_sqft_stock["total homes"][yr]

                        # Find fraction of total buildings that are newly
                        # constructed in all years up through the current
                        # modeling year. These data are used to determine total
                        # cumulative new structure markets for a measure
                        if yr == list(sorted(mseg["energy"].keys()))[0]:
                            new_bldg_frac["total"][yr] = \
                                new_bldg_frac["added"][yr]
                        else:
                            new_bldg_frac["total"][yr] = \
                                new_bldg_frac["added"][yr] + new_bldg_frac[
                                "total"][str(int(yr) - 1)]

                        # Ensure that cumulative new building fraction is <= 1
                        if new_bldg_frac["total"][yr] > 1:
                            new_bldg_frac["total"][yr] = 1

                    # Update technology choice parameters needed to choose
                    # between multiple efficient technology options that
                    # access this baseline microsegment. For the residential
                    # sector, these parameters are found in the baseline
                    # technology cost, performance, and lifetime JSON
                    if mskeys[0] == "secondary":
                        choice_params = {}  # No choice params for 2nd msegs
                    else:
                        choice_params = base_costperflife["consumer choice"][
                            "competed market share"]["parameters"]
                else:
                    # Update commercial baseline and measure energy cost
                    # information, accounting for any fuel switching from
                    # baseline technology to measure technology
                    if self.fuel_switch_to is None:
                        cost_energy_base, cost_energy_meas = (
                            ecosts["commercial"][mskeys[3]] for n in range(2))
                    else:
                        cost_energy_base = ecosts["commercial"][mskeys[3]]
                        cost_energy_meas = ecosts["commercial"][
                            self.fuel_switch_to]

                    # Update new buildings fraction information
                    for yr in mseg["energy"].keys():
                        # *** Placeholders for new commercial information ***
                        new_bldg_frac["added"][yr] = 0
                        new_bldg_frac["total"][yr] = 0
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
                    elif mskeys[4] in com_timeprefs["distributions"].keys():
                        choice_params = {"rate distribution": com_timeprefs[
                            "distributions"][mskeys[4]]}
                    # For uncovered end uses, default to choice parameters for
                    # the heating end use
                    else:
                        choice_params = {"rate distribution": com_timeprefs[
                            "distributions"]["heating"]}

                # Determine the fraction to use in scaling down the stock,
                # energy, and carbon microsegments to the applicable structure
                # type indicated in the microsegment key chain (e.g., new
                # structures or existing structures)
                if mskeys[-1] == "new":
                    new_existing_frac = {key: val for key, val in
                                         new_bldg_frac["total"].items()}
                else:
                    new_existing_frac = {key: (1 - val) for key, val in
                                         new_bldg_frac["total"].items()}

                # Update bass diffusion parameters needed to determine the
                # fraction of the baseline microegment that will be captured
                # by efficient alternatives to the baseline technology
                # (* BLANK FOR NOW, WILL CHANGE IN FUTURE *)
                diffuse_params = base_costperflife["consumer choice"][
                    "competed market"]["parameters"]

                # Update total stock, energy use, and carbon emissions for the
                # current contributing microsegment. Note that secondary
                # microsegments make no contribution to the stock calculation,
                # as they only affect energy/carbon and associated costs.

                # Total stock
                if mskeys[0] == 'secondary':
                    add_stock = dict.fromkeys(mseg["energy"].keys(), 0)
                elif mseg["stock"] == "NA":  # Use sq.ft. in absence of # units
                    sqft_subst = 1
                    # * Note: multiply AEO square footages by 1 million (AEO
                    # reports in million square feet)
                    add_stock = {
                        key: val * new_existing_frac[key] * 1000000 for key,
                        val in mseg_sqft_stock["square footage"].items()}
                else:
                    add_stock = {
                        key: val * new_existing_frac[key] for key, val in
                        mseg["stock"].items()}
                # Total energy use (primary)
                add_energy = {
                    key: val * site_source_conv_base[key] *
                    new_existing_frac[key]
                    for key, val in mseg["energy"].items()}
                # Total carbon emissions
                add_carb = {key: val * intensity_carb_base[key]
                            for key, val in add_energy.items()}

                # Update total, competed, and efficient stock, energy, carbon
                # and baseline/measure cost info. based on adoption scheme
                [add_stock_total, add_energy_total, add_carb_total,
                 add_stock_total_meas, add_energy_total_eff,
                 add_carb_total_eff, add_stock_compete, add_energy_compete,
                 add_carb_compete, add_stock_compete_meas,
                 add_energy_compete_eff, add_carb_compete_eff,
                 add_stock_cost, add_energy_cost, add_carb_cost,
                 add_stock_cost_meas, add_energy_cost_eff, add_carb_cost_eff,
                 add_stock_cost_compete, add_energy_cost_compete,
                 add_carb_cost_compete, add_stock_cost_compete_meas,
                 add_energy_cost_compete_eff, add_carb_cost_compete_eff,
                 mseg_adjust] = \
                    self.partition_microsegment(add_stock, add_energy,
                                                add_carb, rel_perf, cost_base,
                                                cost_meas, cost_energy_base,
                                                cost_energy_meas,
                                                ccosts, site_source_conv_base,
                                                site_source_conv_meas,
                                                intensity_carb_base,
                                                intensity_carb_meas,
                                                new_bldg_frac, diffuse_params,
                                                adopt_scheme, life_base,
                                                life_meas, mskeys, mseg_adjust,
                                                retro_rate, mkt_scale_frac)

                # Combine stock/energy/carbon/cost/lifetime updating info. into
                # a dict
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
                        "baseline": life_base, "measure": life_meas}}

                # Using the key chain for the current microsegment, determine
                # the output climate zone, building type, and end use breakout
                # categories to which the current microsegment applies

                # Establish applicable climate zone breakout
                for cz in out_break_czones.items():
                    if mskeys[1] in cz[1]:
                        out_cz = cz[0]
                # Establish applicable building type breakout
                for bldg in out_break_bldgtypes.items():
                    if mskeys[2] in bldg[1]:
                        out_bldg = bldg[0]
                # Establish applicable end use breakout
                for eu in out_break_enduses.items():
                    # * Note: The 'other (grid electric)' microsegment end
                    # use may map to either the 'Refrigeration' output
                    # breakout or the 'Other' output breakout, depending on
                    # the technology type specified in the measure definition
                    if mskeys[4] == "other (grid electric)":
                        if mskeys[5] == "freezers":
                            out_eu = "Refrigeration"
                        else:
                            out_eu = "Other"
                    elif mskeys[4] in eu[1]:
                        out_eu = eu[0]

                # Given the contributing microsegment's applicable climate
                # zone, building type, and end use categories, add the
                # microsegment's baseline energy use value to the appropriate
                # leaf node of the dictionary used to store measure output
                # breakout information. * Note: the values in this dictionary
                # will eventually be normalized by the measure's total baseline
                # energy use to yield the fractions of measure energy and
                # carbon markets/savings that are attributable to each climate
                # zone, building type, and end use the measure applies to
                if out_cz and out_bldg and out_eu:
                    # If this is the first time the output breakout dictionary
                    # is being updated, replace appropriate terminal leaf node
                    # value with the baseline energy use values of the current
                    # contributing microsegment
                    if len(mseg_out_break[out_cz][
                            out_bldg][out_eu].keys()) == 0:
                        mseg_out_break[out_cz][out_bldg][out_eu] = \
                            OrderedDict(sorted(add_energy.items()))

                    # If the output breakout dictionary has already been
                    # updated for a previous microsegment, add the baseline
                    # energy values of the current contributing microsegment
                    # to the dictionary's existing terminal leaf node values
                    else:
                        for yr in mseg_out_break[out_cz][
                                out_bldg][out_eu].keys():
                            mseg_out_break[out_cz][out_bldg][
                                out_eu][yr] += add_energy[yr]
                # Yield error if current contributing microsegment cannot be
                # mapped to an output breakout category
                else:
                    raise ValueError(
                        'Microsegment not found in output categories!')

                # Case with no existing 'windows' contributing microsegment
                # for the current climate zone, building type, fuel type, and
                # end use (create new 'contributing mseg keys and values'
                # and 'competed choice parameters' microsegment information)
                if contrib_mseg_key not in mseg_adjust[
                        "contributing mseg keys and values"].keys():
                    # Register contributing microsegment information for later
                    # use in determining savings overlaps for measures that
                    # apply to this microsegment
                    mseg_adjust["contributing mseg keys and values"][
                        str(contrib_mseg_key)] = add_dict
                    # Register choice parameters associated with contributing
                    # microsegment for later use in apportioning out various
                    # technology options across competed stock
                    mseg_adjust["competed choice parameters"][
                        str(contrib_mseg_key)] = choice_params
                # Case with no existing 'windows' contributing microsegment
                # for the current climate zone, building type, fuel type, and
                # end use (add to existing 'contributing mseg keys and values'
                # information)
                else:
                    mseg_adjust["contributing mseg keys and values"][
                        str(contrib_mseg_key)] = self.add_keyvals_restrict(
                            mseg_adjust["contributing mseg keys and values"][
                                str(contrib_mseg_key)], add_dict)

                # Add all updated information to existing master mseg dict and
                # move to next iteration of the loop through key chains
                mseg_master = self.add_keyvals(mseg_master, add_dict)

        # Further normalize a measure's lifetime and stock information (where
        # the latter is based on square footage) to the number of valid
        # microsegments that contribute to the measure's overall master
        # microsegment. Before proceeeding with this calculation, ensure the
        # number of valid contributing microsegments is non-zero, and that the
        # measure has not been flagged for removal from the analysis due to
        # insufficient sub-market scaling source information (key_chain_ct =
        # 999 in this case)
        if key_chain_ct != 0 and key_chain_ct != 999:

            # Reduce summed lifetimes by number of microsegments that
            # contributed to the sums
            for yr in mseg_master["lifetime"]["baseline"].keys():
                mseg_master["lifetime"]["baseline"][yr] = mseg_master[
                    "lifetime"]["baseline"][yr] / key_chain_ct
            mseg_master["lifetime"]["measure"] = mseg_master[
                "lifetime"]["measure"] / key_chain_ct

            # In microsegments where square footage must be used as stock, the
            # square footages cannot be summed to calculate the master
            # microsegment stock values (as is the case when using no. of
            # units).  For example, 1000 Btu of cooling and heating in the same
            # 1000 square foot building should not yield 2000 total square feet
            # of stock in the master microsegment even though there are two
            # contributing microsegments in this case (heating and cooling).
            # This is remedied by dividing summed square footage values by (#
            # valid key chains / (# czones * # bldg types * # structure
            # types)), where the numerator refers to the number of full dict
            # key chains that contributed to the mseg stock, energy, and cost
            # calcs, and the denominator reflects the breakdown of square
            # footage by climate zone, building type, and the structure type
            # that the measure applies to.
            if sqft_subst == 1:
                # Determine number of structure types the measure applies to
                # (could be just new, just existing, or both)
                if isinstance(self.structure_type, list):
                    structure_types = 2
                else:
                    structure_types = 1
                # Create a factor for reduction of msegs with sq.ft. stock
                reduce_factor = key_chain_ct / (len(ms_lists[0]) *
                                                len(ms_lists[1]) *
                                                structure_types)
                # Adjust master microsegment by above factor
                mseg_master = self.reduce_sqft(mseg_master, reduce_factor)
                # Adjust all recorded microsegments that contributed to the
                # master microsegment by above factor
                mseg_adjust["contributing mseg keys and values"] = \
                    self.reduce_sqft(copy.deepcopy(
                        mseg_adjust["contributing mseg keys and values"]),
                    reduce_factor)
            else:
                reduce_factor = 1

            # Normalize baseline energy use values for each category in the
            # measure's output breakout dictionary by the total baseline
            # energy use for the measure across all contributing
            # microsegments; this yields partitioning fractions that will
            # eventually be used to breakout measure energy and carbon
            # markets/savings by climate zone, building type, and end use
            mseg_out_break = self.out_break_norm(
                mseg_out_break, mseg_master['energy']['total']['baseline'])
        # Generate an error message when no valid contributing microsegments
        # have been found for the measure's master microsegment
        elif key_chain_ct == 0:
            raise KeyError((
                "No valid key chains discovered for lifetime "
                "and stock and cost division operations!"))

        # Return the final master microsegment as well as contributing
        # microsegment and markets/savings output breakout information
        return [mseg_master, mseg_adjust, mseg_out_break]

    def create_keychain(self, mseg_type, htcl_enduse_ct=0):
        """ Given input microsegment information, create a list of keys that
        represents associated branch on the microsegment tree """

        # Flag a heating/cooling end use case; here, an extra 'supply' or
        # 'demand' key is required in the key chain, which flags the
        # supply-side and demand-side variants of heating/cooling technologies
        # (e.g., ASHP for the former, envelope air sealing for the latter).

        # Case where there is only one end use listed for the measure
        if isinstance(self.end_use[mseg_type], list) is False:
            if self.end_use[mseg_type] in [
                    "heating", "secondary heating", "cooling"]:
                htcl_enduse_ct = 1
        # Case where there is more than one end use listed for the measure
        else:
            for eu in self.end_use[mseg_type]:
                if eu in ["heating", "secondary heating", "cooling"]:
                    htcl_enduse_ct += 1

        # Create a list of lists where each list has key information for
        # one of the microsegment levels. Use list to find all possible
        # microsegment key chains (i.e. ("new england", "single family home",
        # "natural gas", "water heating")). Add in "demand" and "supply keys
        # where needed (heating, secondary heating, cooling end uses)
        if (htcl_enduse_ct > 0):
            ms_lists = [self.climate_zone, self.bldg_type,
                        self.fuel_type[mseg_type],
                        self.end_use[mseg_type],
                        self.technology_type[mseg_type],
                        self.technology[mseg_type]]
        else:
            ms_lists = [self.climate_zone, self.bldg_type,
                        self.fuel_type[mseg_type], self.end_use[mseg_type],
                        self.technology[mseg_type]]

        # Ensure that every list element is itself a list
        for x in range(0, len(ms_lists)):
            if isinstance(ms_lists[x], list) is False:
                ms_lists[x] = [ms_lists[x]]

        # Find all possible microsegment key chains
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

    def add_keyvals(self, dict1, dict2):
        """ Add key values of two identically structured dicts together """

        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if k == k2:
                if isinstance(i, dict):
                    self.add_keyvals(i, i2)
                else:
                    if dict1[k] is None:
                        dict1[k] = copy.deepcopy(dict2[k2])
                    else:
                        dict1[k] = dict1[k] + dict2[k]
            else:
                raise KeyError('Add dict keys do not match!')
        return dict1

    def add_keyvals_restrict(self, dict1, dict2):
        """ Add key values of two identically structured dicts together,
        with the exception of any keys that indicate measure lifetime
        values """

        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
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
                raise KeyError('Add dict keys do not match!')
        return dict1

    def partition_microsegment(self, stock_total_init, energy_total_init,
                               carb_total_init, rel_perf, cost_base, cost_meas,
                               cost_energy_base, cost_energy_meas, cost_carb,
                               site_source_conv_base, site_source_conv_meas,
                               intensity_carb_base, intensity_carb_meas,
                               new_bldg_frac, diffuse_params,
                               adopt_scheme, life_base, life_meas, mskeys,
                               mseg_adjust, retro_rate, mkt_scale_frac):
        """ Partition microsegment to find "competed" stock and energy/carbon
        consumption as well as "efficient" energy consumption (representing
        consumption under the measure).  Also find the cost of the baseline
        and measure stock, energy, and carbon """

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

        # Set measure market entry year
        if self.market_entry_year is None:
            mkt_entry_yr = int(list(sorted(stock_total_init.keys()))[0])
        else:
            mkt_entry_yr = self.market_entry_year
        # Set measure market exit year
        if self.market_exit_year is None:
            mkt_exit_yr = int(list(sorted(stock_total_init.keys()))[-1]) + 1
        else:
            mkt_exit_yr = self.market_exit_year

        # Initialize the portion of microsegment already captured by the
        # efficient measure as 0, and the portion baseline stock as 1.
        captured_eff_frac = 0
        captured_base_frac = 1

        # In cases where secondary heating/cooling microsegments are present
        # for a lighting efficiency measure, initialize a dict of year-by-year
        # secondary microsegment adjustment information that will be used
        # to scale down the secondary heating/cooling microsegment(s) in
        # accordance with the portion of the total applicable lighting stock
        # that is captured by the measure in each year
        if self.end_use["secondary"] is not None and mskeys[4] in ["lighting",
           "heating", "secondary heating", "cooling"]:
            # Set short names for secondary adjustment information dicts
            secnd_adj_sbmkt = mseg_adjust[
                "secondary mseg adjustments"]["sub-market"]
            secnd_adj_stk = mseg_adjust[
                "secondary mseg adjustments"]["stock-and-flow"]
            secnd_adj_mktshr = mseg_adjust[
                "secondary mseg adjustments"]["market share"]
            # Determine a dictionary key indicating the climate zone, building
            # type, and structure type that is shared by the primary lighting
            # microsegment and secondary heating/cooling microsegment
            secnd_mseg_adjkey = (mskeys[1], mskeys[2], mskeys[-1])
            # If no year-by-year secondary microsegment adjustment information
            # exists for the given climate zone, building type, and structure
            # type, initialize all year-by-year adjustment values as 0
            if secnd_mseg_adjkey not in secnd_adj_stk[
                    "original stock (total)"].keys():
                # Initialize sub-market secondary adjustment information

                # Initialize original primary microsegment stock information
                secnd_adj_sbmkt["original stock (total)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        stock_total_init.keys(), 0)
                # Initialize sub-market adjusted microsegment stock information
                secnd_adj_sbmkt["adjusted stock (sub-market)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        stock_total_init.keys(), 0)

                # Initialize stock-and-flow secondary adjustment information

                # Initialize original primary microsegment stock information
                secnd_adj_stk["original stock (total)"][secnd_mseg_adjkey] = \
                    dict.fromkeys(
                        stock_total_init.keys(), 0)
                # Initialize previously captured primary microsegment stock
                # information
                secnd_adj_stk["adjusted stock (previously captured)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        stock_total_init.keys(), 0)
                # Initialize competed primary microsegment stock information
                secnd_adj_stk["adjusted stock (competed)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        stock_total_init.keys(), 0)
                # Initialize competed and captured primary microsegment stock
                # information
                secnd_adj_stk["adjusted stock (competed and captured)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        stock_total_init.keys(), 0)

                # Initialize market share secondary adjustment information
                # (used in 'adjust_savings' function below)

                # Initialize original total captured stock information
                secnd_adj_mktshr["original stock (total captured)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        stock_total_init.keys(), 0)
                # Initialize original competed and captured stock information
                secnd_adj_mktshr["original stock (competed and captured)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        stock_total_init.keys(), 0)
                # Initialize adjusted total captured stock information
                secnd_adj_mktshr["adjusted stock (total captured)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        stock_total_init.keys(), 0)
                # Initialize adjusted competed and captured stock information
                secnd_adj_mktshr["adjusted stock (competed and captured)"][
                    secnd_mseg_adjkey] = dict.fromkeys(
                        stock_total_init.keys(), 0)

        # In cases where no secondary heating/cooling microsegment is present,
        # set secondary microsegment adjustment key to None
        else:
            secnd_mseg_adjkey = None

        # Loop through and update stock, energy, and carbon mseg partitions for
        # each year in the modeling time horizon
        for yr in sorted(stock_total_init.keys()):

            # For secondary microsegments only, update: a) sub-market scaling
            # fraction, based on any sub-market scaling in the associated
            # primary microsegment, and b) the portion of associated primary
            # microsegment stock that has been captured by the measure in
            # previous years
            if mskeys[0] == "secondary" and secnd_mseg_adjkey is not None:
                # Adjust sub-market scaling fraction
                if secnd_adj_sbmkt["original stock (total)"][
                        secnd_mseg_adjkey][yr] != 0:
                    mkt_scale_frac = secnd_adj_sbmkt[
                        "adjusted stock (sub-market)"][
                        secnd_mseg_adjkey][yr] / \
                        secnd_adj_sbmkt["original stock (total)"][
                        secnd_mseg_adjkey][yr]
                # Adjust previously captured efficient fraction
                if secnd_adj_stk["original stock (total)"][
                        secnd_mseg_adjkey][yr] != 0:
                    captured_eff_frac = secnd_adj_stk[
                        "adjusted stock (previously captured)"][
                        secnd_mseg_adjkey][yr] / secnd_adj_stk[
                        "original stock (total)"][secnd_mseg_adjkey][yr]
                else:
                    captured_eff_frac = 0
                # Update portion of existing primary stock remaining with the
                # baseline technology
                captured_base_frac = 1 - captured_eff_frac

            # If sub-market scaling fraction is None, set to 1
            if mkt_scale_frac is None:
                mkt_scale_frac = 1

            # Stock, energy, and carbon adjustments
            stock_total[yr] = stock_total_init[yr] * mkt_scale_frac
            energy_total[yr] = energy_total_init[yr] * mkt_scale_frac
            carb_total[yr] = carb_total_init[yr] * mkt_scale_frac

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
                # replacement fraction equals the fraction of stock in new
                # homes already captured by baseline technology multiplied
                # by (1 / baseline lifetime); if not, the baseline replacement
                # fraction is 0
                if mskeys[-1] == "new":
                    turnover_base = life_base[yr] - (
                        int(yr) - int(list(sorted(stock_total.keys()))[0]))
                    if turnover_base <= 0:
                        captured_base_replace_frac = captured_base_frac * \
                            (1 / life_base[yr])
                    else:
                        captured_base_replace_frac = 0
                # For a case where the current microsegment applies to
                # existing structures, the baseline replacement fraction
                # is the lesser of (1 / baseline lifetime) and the fraction
                # of existing stock from previous years that has already been
                # captured by the baseline technology
                else:
                    if (1 / life_base[yr]) <= captured_base_frac:
                        captured_base_replace_frac = (1 / life_base[yr])
                    else:
                        captured_base_replace_frac = captured_base_frac

                # Update efficient replacement fraction

                # Determine whether enough years have passed since the
                # efficient measure was first adopted in new homes in its
                # market entry year to begin replacing that efficient stock;
                # if so, the efficient replacement fraction is the fraction of
                # stock in new homes already captured by the efficient
                # technology multiplied by (1 / efficient lifetime); if not,
                # the efficient replacement fraction is 0
                if self.market_entry_year is None:
                    turnover_meas = life_meas - (
                        int(yr) - int(list(sorted(stock_total.keys()))[0]))
                else:
                    turnover_meas = life_meas - (
                        int(yr) - self.market_entry_year)
                # Handle case where efficient measure lifetime is a numpy array
                if type(life_meas) == numpy.ndarray:
                    for ind, l in enumerate(life_meas):
                        if turnover_meas[ind] <= 0:
                            captured_eff_replace_frac = \
                                captured_eff_frac * (1 / l)
                        else:
                            captured_eff_replace_frac = 0
                # Handle case where efficient measure lifetime is a point value
                else:
                    if turnover_meas <= 0:
                        captured_eff_replace_frac = captured_eff_frac * \
                            (1 / life_meas)
                    else:
                        captured_eff_replace_frac = 0
            else:
                captured_eff_replace_frac, captured_base_replace_frac = \
                    (0 for n in range(2))

            # Determine the fraction of total stock, energy, and carbon
            # in a given year that the measure will compete for given the
            # microsegment type and technology adoption scenario

            # Secondary microsegment (competed fraction tied to the associated
            # primary microsegment)
            if mskeys[0] == "secondary" and secnd_mseg_adjkey is not None and \
               secnd_adj_stk["original stock (total)"][
                    secnd_mseg_adjkey][yr] != 0:
                    competed_frac = secnd_adj_stk["adjusted stock (competed)"][
                        secnd_mseg_adjkey][yr] / secnd_adj_stk[
                            "original stock (total)"][secnd_mseg_adjkey][yr]
            # Primary microsegment in the first year of a technical potential
            # scenario (all stock competed)
            elif mskeys[0] == "primary" and int(yr) == mkt_entry_yr and \
                    adopt_scheme == "Technical potential":
                competed_frac = 1
            # Primary microsegment not in the first year where current
            # microsegment applies to new structure type
            elif mskeys[0] == "primary" and mskeys[-1] == "new":
                if new_bldg_frac["total"][yr] != 0:
                    new_bldg_add_frac = new_bldg_frac["added"][yr] / \
                        new_bldg_frac["total"][yr]
                    competed_frac = new_bldg_add_frac + \
                        (1 - new_bldg_add_frac) * \
                        (captured_eff_replace_frac +
                         captured_base_replace_frac)
                else:
                    competed_frac = 0
            # Primary microsegment not in the first year where current
            # microsegment applies to existing structure type
            elif mskeys[0] == "primary" and mskeys[-1] == "existing":
                # Ensure that replacement plus retrofit fraction does not
                # exceed 1
                if captured_base_replace_frac + captured_eff_replace_frac + \
                   retro_rate <= 1:
                    competed_frac = captured_base_replace_frac + \
                        captured_eff_replace_frac + retro_rate
                else:
                    competed_frac = 1
            # For all other cases, set competed fraction to 0
            else:
                competed_frac = 0

            # Determine the fraction of total stock, energy, and carbon
            # in a given year that is competed and captured by the measure

            # Secondary microsegment (competed and captured fraction tied
            # to the associated primary microsegment)
            if mskeys[0] == "secondary" and secnd_mseg_adjkey is not None \
               and secnd_adj_stk[
                    "original stock (total)"][secnd_mseg_adjkey][yr] != 0:
                    competed_captured_eff_frac = secnd_adj_stk[
                        "adjusted stock (competed and captured)"][
                        secnd_mseg_adjkey][yr] / secnd_adj_stk[
                        "original stock (total)"][secnd_mseg_adjkey][yr]
            # Primary microsegment and year when measure is on the market
            elif mskeys[0] == "primary" and (
                    int(yr) >= mkt_entry_yr) and (int(yr) < mkt_exit_yr):
                competed_captured_eff_frac = competed_frac * diffuse_eff_frac
            # For all other cases, set competed and captured fraction to 0
            else:
                competed_captured_eff_frac = 0

            # In the case of a primary microsegment with secondary effects,
            # update the information needed to scale down the secondary
            # microsegment(s) by a sub-market fraction and previously captured,
            # competed, and competed and captured stock fractions for the
            # primary microsegment
            if mskeys[0] == "primary" and secnd_mseg_adjkey is not None:
                # Total stock
                secnd_adj_sbmkt["original stock (total)"][
                    secnd_mseg_adjkey][yr] += stock_total_init[yr]
                # Sub-market stock
                secnd_adj_sbmkt["adjusted stock (sub-market)"][
                    secnd_mseg_adjkey][yr] += stock_total[yr]
                # Total stock
                secnd_adj_stk[
                    "original stock (total)"][secnd_mseg_adjkey][yr] += \
                    stock_total[yr]
                # Previously captured stock
                secnd_adj_stk["adjusted stock (previously captured)"][
                    secnd_mseg_adjkey][yr] += \
                    captured_eff_frac * stock_total[yr]
                # Competed stock
                secnd_adj_stk["adjusted stock (competed)"][
                    secnd_mseg_adjkey][yr] += competed_frac * stock_total[yr]
                # Competed and captured stock
                secnd_adj_stk["adjusted stock (competed and captured)"][
                    secnd_mseg_adjkey][yr] += \
                    competed_captured_eff_frac * stock_total[yr]

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
            # year. * Note: captured stock numbers are used in the
            # cost_metric_update function below to normalize measure cost
            # metrics to a per unit basis.

            # First year in the modeling time horizon
            if yr == list(sorted(stock_total.keys()))[0]:
                stock_total_meas[yr] = stock_compete_meas[yr]
            # Subsequent year in modeling time horizon
            else:
                # Technical potential case where the measure is on the
                # market: the stock captured by the measure should equal the
                # total stock (measure captures all stock)
                if adopt_scheme == "Technical potential" and \
                        (int(yr) >= mkt_entry_yr) and (int(yr) < mkt_exit_yr):
                    stock_total_meas[yr] = stock_total[yr]
                # All other cases
                else:
                    # Update total number of stock units captured by the
                    # measure (reflects all previously captured stock +
                    # captured competed stock from the current year)
                    stock_total_meas[yr] = \
                        (stock_total_meas[str(int(yr) - 1)]) * (
                            1 - captured_eff_replace_frac) + \
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

            # Set a relative performance level for all stock captured by the
            # measure by weighting the relative performance of competed
            # stock captured by the measure in the current year and the
            # relative performance of all stock captured by the measure in
            # previous years

            # Set the relative performance of the current year's competed stock
            rel_perf_competed = rel_perf[yr]

            # If first year in the modeling time horizon, initialize the
            # weighted relative performance level as identical to that of the
            # competed stock (e.g., initialize to the the relative performance
            # from baseline -> measure for that year only)
            if yr == sorted(stock_total.keys())[0]:
                rel_perf_weighted = rel_perf[yr]
            # For a subsequent year in the modeling time horizon, calculate
            # a weighted sum of the relative performances of the competed stock
            # captured in the current year and the stock captured in all
            # previous years
            else:
                total_capture = competed_captured_eff_frac + (
                    1 - competed_frac) * captured_eff_frac
                if total_capture != 0:
                    rel_perf_weighted = (
                        rel_perf_competed * competed_captured_eff_frac +
                        rel_perf_weighted * (
                            total_capture - competed_captured_eff_frac)) / \
                        total_capture

            # Update total-efficient and competed-efficient energy and
            # carbon, where "efficient" signifies the total and competed
            # energy/carbon remaining after measure implementation plus
            # non-competed energy/carbon. * Note: Efficient energy and
            # carbon is dependent upon whether the measure is on the market
            # for the given year (if not, use baseline energy and carbon)

            # Competed-efficient energy
            energy_compete_eff[yr] = energy_total[yr] * \
                competed_captured_eff_frac * rel_perf_weighted * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) + \
                energy_total[yr] * (competed_frac - competed_captured_eff_frac)
            # Total-efficient energy
            energy_total_eff[yr] = energy_compete_eff[yr] + \
                (energy_total[yr] - energy_compete[yr]) * \
                captured_eff_frac * rel_perf_weighted * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) + \
                (energy_total[yr] - energy_compete[yr]) * \
                (1 - captured_eff_frac)
            # Competed-efficient carbon
            carb_compete_eff[yr] = carb_total[yr] * \
                competed_captured_eff_frac * rel_perf_weighted * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                (intensity_carb_meas[yr] / intensity_carb_base[yr]) + \
                carb_total[yr] * (competed_frac - competed_captured_eff_frac)
            # Total-efficient carbon
            carb_total_eff[yr] = carb_compete_eff[yr] + \
                (carb_total[yr] - carb_compete[yr]) * \
                captured_eff_frac * rel_perf_weighted * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                (intensity_carb_meas[yr] / intensity_carb_base[yr]) + \
                (carb_total[yr] - carb_compete[yr]) * (1 - captured_eff_frac)

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
            energy_compete_cost[yr] = energy_compete[yr] * cost_energy_base[yr]
            # Competed energy-efficient cost
            energy_compete_cost_eff[yr] = energy_total[yr] * \
                competed_captured_eff_frac * rel_perf_weighted * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                cost_energy_meas[yr] + energy_total[yr] * (
                    competed_frac - competed_captured_eff_frac) * \
                cost_energy_base[yr]
            # Total baseline energy cost
            energy_total_cost[yr] = energy_total[yr] * cost_energy_base[yr]
            # Total energy-efficient cost
            energy_total_eff_cost[yr] = energy_compete_cost_eff[yr] + \
                (energy_total[yr] - energy_compete[yr]) * captured_eff_frac * \
                rel_perf_weighted * (
                    site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                cost_energy_meas[yr] + (
                    energy_total[yr] - energy_compete[yr]) * (
                    1 - captured_eff_frac) * cost_energy_base[yr]

            # Competed baseline carbon cost
            carb_compete_cost[yr] = carb_compete[yr] * cost_carb[yr]
            # Competed carbon-efficient cost
            carb_compete_cost_eff[yr] = carb_compete_eff[yr] * cost_carb[yr]
            # Total baseline carbon cost
            carb_total_cost[yr] = carb_total[yr] * cost_carb[yr]
            # Total carbon-efficient cost
            carb_total_eff_cost[yr] = carb_total_eff[yr] * cost_carb[yr]

            # For primary microsegments only, update portion of stock captured
            # by efficient measure in previous years to reflect gains from the
            # current modeling year. If this portion is already 1 or the total
            # stock for the year is 0, do not update the captured portion from
            # the previous year
            if mskeys[0] == "primary":
                # Handle case where stock captured by measure is a numpy array
                if type(stock_total_meas[yr]) == numpy.ndarray:
                    for i in range(0, len(stock_total_meas[yr])):
                        if stock_total[yr] != 0 and captured_eff_frac[i] != 1:
                            captured_eff_frac[i] = stock_total_meas[yr][i] / \
                                stock_total[yr]
                # Handle case where stock captured by measure is a point value
                else:
                    if stock_total[yr] != 0 and captured_eff_frac != 1:
                        captured_eff_frac = \
                            stock_total_meas[yr] / stock_total[yr]
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
                energy_compete_cost_eff, carb_compete_cost_eff, mseg_adjust]

    def calc_metric_update(
            self, rate, adjust_savings, com_timeprefs, adopt_scheme):
        """ Given information on a measure's master microsegment for
        each projection year and a discount rate, determine capital ("stock"),
        energy, and carbon cost savings; energy and carbon savings; and the
        internal rate of return, simple payback, cost of conserved energy, and
        cost of conserved carbon for the measure. """

        # Initialize capital cost, energy/energy cost savings, carbon/carbon
        # cost savings, and economic metrics as dicts with years as keys
        scostsave_tot, scostsave_annual, esave_tot, esave_annual, \
            ecostsave_tot, ecostsave_annual, csave_tot, csave_annual, \
            ccostsave_tot, ccostsave_annual, stock_anpv, energy_anpv, \
            carbon_anpv, irr_e, irr_ec, payback_e, payback_ec, cce, cce_bens, \
            ccc, ccc_bens = ({} for d in range(21))

        # Calculate capital cost savings, energy/carbon savings, and
        # energy/carbon cost savings for each projection year
        for ind, yr in enumerate(
                sorted(self.master_mseg["stock"][
                    "total"]["measure"].keys())):

            # Set the number of competed stock units that are captured by the
            # measure for the given year; this number is used for normalizing
            # stock, energy and carbon cash flows to a per unit basis in the
            # "metric_update" function below. * Note: for a technical
            # potential scenario, all stock units are captured in each year
            if adopt_scheme != "Technical potential":
                num_units = self.master_mseg[
                    "stock"]["competed"]["measure"][yr]
            else:
                num_units = self.master_mseg["stock"]["total"]["measure"][yr]
            # Set the total (not unit) capital cost of the baseline
            # technology for comparison with measure capital cost
            scost_base_tot = self.master_mseg[
                "cost"]["stock"]["total"]["baseline"][yr]
            scost_base_add = self.master_mseg[
                "cost"]["stock"]["competed"]["baseline"][yr]

            # Calculate total annual energy/carbon and stock/energy/carbon cost
            # savings for the measure vs. baseline. Total savings reflect the
            # impact of all measure adoptions simulated up until and including
            # the current year of the modeling time horizon.
            esave_tot[yr] = \
                self.master_mseg["energy"]["total"]["baseline"][yr] - \
                self.master_mseg["energy"]["total"]["efficient"][yr]
            csave_tot[yr] = \
                self.master_mseg["carbon"]["total"]["baseline"][yr] - \
                self.master_mseg["carbon"]["total"]["efficient"][yr]
            scostsave_tot[yr] = \
                scost_base_tot - \
                self.master_mseg["cost"]["stock"]["total"]["efficient"][yr]
            ecostsave_tot[yr] = \
                self.master_mseg["cost"]["energy"]["total"]["baseline"][yr] - \
                self.master_mseg["cost"]["energy"]["total"]["efficient"][yr]
            ccostsave_tot[yr] = \
                self.master_mseg["cost"]["carbon"]["total"]["baseline"][yr] - \
                self.master_mseg["cost"]["carbon"]["total"]["efficient"][yr]

            # Calculate the annual energy/carbon and stock/energy/carbon
            # cost savings for the measure vs. baseline. Annual savings
            # will later be used in measure competition routines. In non-
            # technical potential scenarios, annual savings reflect the impact
            # of only the measure adoptions that are new in the current year of
            # the modeling time horizon. In a technical potential scenario,
            # where we are simulating an 'overnight' adoption of the measure
            # across the entire applicable stock in each year, annual savings
            # are set to the total savings from all current/previous adoptions
            # of the measure
            if adopt_scheme != "Technical potential":
                esave_annual[yr] = \
                    self.master_mseg["energy"][
                    "competed"]["baseline"][yr] - \
                    self.master_mseg["energy"][
                    "competed"]["efficient"][yr]
                csave_annual[yr] = \
                    self.master_mseg["carbon"][
                    "competed"]["baseline"][yr] - \
                    self.master_mseg["carbon"][
                    "competed"]["efficient"][yr]
                scostsave_annual[yr] = \
                    scost_base_add - \
                    self.master_mseg["cost"]["stock"][
                    "competed"]["efficient"][yr]
                ecostsave_annual[yr] = \
                    self.master_mseg["cost"]["energy"][
                    "competed"]["baseline"][yr] - \
                    self.master_mseg["cost"]["energy"][
                    "competed"]["efficient"][yr]
                ccostsave_annual[yr] = \
                    self.master_mseg["cost"]["carbon"][
                    "competed"]["baseline"][yr] - \
                    self.master_mseg["cost"]["carbon"][
                    "competed"]["efficient"][yr]
            else:
                esave_annual[yr], csave_annual[yr], scostsave_annual[yr], \
                    ecostsave_annual[yr], ccostsave_annual[yr] = [
                    esave_tot[yr], csave_tot[yr], scostsave_tot[yr],
                    ecostsave_tot[yr], ccostsave_tot[yr]]

            # Set the lifetime of the baseline technology for comparison
            # with measure lifetime
            life_base = self.master_mseg["lifetime"]["baseline"][yr]
            # Ensure that baseline lifetime is at least 1 year
            if type(life_base) == numpy.ndarray and any(life_base) < 1:
                life_base[numpy.where(life_base) < 1] = 1
            elif type(life_base) != numpy.ndarray and life_base < 1:
                life_base = 1

            # Set lifetime of the measure
            life_meas = self.master_mseg["lifetime"]["measure"]
            # Ensure that measure lifetime is at least 1 year
            if type(life_meas) == numpy.ndarray and any(life_meas) < 1:
                life_meas[numpy.where(life_meas) < 1] = 1
            elif type(life_meas) != numpy.ndarray and life_meas < 1:
                life_meas = 1

            # Define ratio of measure lifetime to baseline lifetime.  This
            # will be used below in determining capital cashflows over the
            # measure lifetime
            life_ratio = life_meas / life_base

            # Make copies of the above stock, energy, carbon, and cost
            # variables for possible further manipulation below before
            # as inputs to the "metric update" function
            scostsave_annual_temp = scostsave_annual[yr]
            esave_annual_temp = esave_annual[yr]
            ecostsave_annual_temp = ecostsave_annual[yr]
            csave_annual_temp = csave_annual[yr]
            ccostsave_annual_temp = ccostsave_annual[yr]
            life_meas_temp = life_meas
            life_ratio_temp = life_ratio

            # Calculate economic metrics using "metric_update" function

            # Check whether number of adopted units for a measure is zero,
            # in which case all economic outputs are set to 999
            if type(num_units) != numpy.ndarray and num_units == 0 or \
               type(num_units) == numpy.ndarray and all(num_units) == 0:
                stock_anpv[yr], energy_anpv[yr], carbon_anpv[yr] = [
                    {"residential": 999, "commercial": 999} for n in
                    range(3)]
                irr_e[yr], irr_ec[yr], payback_e[yr], payback_ec[yr], cce[yr],\
                    cce_bens[yr], ccc[yr], ccc_bens[yr] = [
                        999 for n in range(8)]
            # Check whether any "metric_update" inputs that can be arrays
            # are in fact arrays
            elif any(type(x) == numpy.ndarray for x in
                     [scostsave_annual_temp, esave_annual_temp,
                      life_meas_temp]):

                # Ensure consistency in length of all "metric_update"
                # inputs that can be arrays

                # Determine the length that any array inputs to
                # "metric_update" should consistently have
                length_array = next(
                    (len(item) for item in [scostsave_annual[yr],
                     esave_annual[yr], life_ratio] if type(item) ==
                     numpy.ndarray), None)

                # Ensure all array inputs to "metric_update" are of the
                # above length

                # Check incremental capital cost input
                if type(scostsave_annual_temp) != numpy.ndarray:
                    scostsave_annual_temp = numpy.repeat(
                        scostsave_annual_temp, length_array)
                # Check energy/energy cost and carbon/cost savings inputs
                if type(esave_annual_temp) != numpy.ndarray:
                    esave_annual_temp = numpy.repeat(
                        esave_annual_temp, length_array)
                    ecostsave_annual_temp = numpy.repeat(
                        ecostsave_annual_temp, length_array)
                    csave_annual_temp = numpy.repeat(
                        csave_annual_temp, length_array)
                    ccostsave_annual_temp = numpy.repeat(
                        ccostsave_annual_temp, length_array)
                # Check measure lifetime and lifetime ratio inputs
                if type(life_meas_temp) != numpy.ndarray:
                    life_meas_temp = numpy.repeat(
                        life_meas_temp, length_array)
                    life_ratio_temp = numpy.repeat(
                        life_ratio_temp, length_array)
                # Check number of units captured by the measure
                if type(num_units) != numpy.ndarray:
                    num_units = numpy.repeat(num_units, length_array)

                # Initialize numpy arrays for economic metric outputs

                # First three arrays will be populated by dicts
                # containing residential and commercial Annualized
                # Net Present Values (ANPVs)
                stock_anpv[yr], energy_anpv[yr], carbon_anpv[yr] = \
                    (numpy.repeat({}, len(scostsave_annual_temp))
                        for v in range(3))
                # Remaining eight arrays will be populated by floating
                # point values
                irr_e[yr], irr_ec[yr], payback_e[yr], payback_ec[yr], \
                    cce[yr], cce_bens[yr], ccc[yr], ccc_bens[yr] = \
                    (numpy.zeros(len(scostsave_annual_temp))
                        for v in range(8))

                # Run measure energy/carbon/cost savings and lifetime
                # inputs through "metric_update" function to yield economic
                # metric outputs. To handle inputs that are arrays, use a
                # for loop to generate an output for each input array
                # element one-by-one and append it to the appropriate
                # output list.
                for x in range(0, len(scostsave_annual_temp)):
                    # Check whether number of adopted units for a measure
                    # is zero, in which case all economic outputs are set
                    # to 999
                    if num_units[x] == 0:
                        stock_anpv[yr][x], energy_anpv[yr][x],\
                            carbon_anpv[yr][x] = [{
                                "residential": 999, "commercial": 999} for
                                n in range(3)]
                        irr_e[yr][x], \
                            irr_ec[yr][x], payback_e[yr][x], \
                            payback_ec[yr][x], cce[yr][x], cce_bens[yr][x], \
                            ccc[yr][x], ccc_bens[yr][x] = [
                                999 for n in range(8)]
                    else:
                        stock_anpv[yr][x], energy_anpv[yr][x],\
                            carbon_anpv[yr][x], irr_e[yr][x], irr_ec[yr][x],\
                            payback_e[yr][x], payback_ec[yr][x], cce[yr][x], \
                            cce_bens[yr][x], ccc[yr][x], ccc_bens[yr][x] = \
                            self.metric_update(
                                rate, scost_base_add, life_base,
                                scostsave_annual_temp[x], esave_annual_temp[x],
                                ecostsave_annual_temp[x], csave_annual_temp[x],
                                ccostsave_annual_temp[x],
                                int(life_ratio_temp[x]),
                                int(life_meas_temp[x]), num_units[x],
                                com_timeprefs)
            else:
                # Run measure energy/carbon/cost savings and lifetime
                # inputs through "metric_update" function to yield economic
                # metric outputs
                stock_anpv[yr], energy_anpv[yr],\
                    carbon_anpv[yr], irr_e[yr], irr_ec[yr],\
                    payback_e[yr], payback_ec[yr], cce[yr],\
                    cce_bens[yr], ccc[yr], ccc_bens[yr] = \
                    self.metric_update(
                        rate, scost_base_add, life_base, scostsave_annual_temp,
                        esave_annual_temp, ecostsave_annual_temp,
                        csave_annual_temp, ccostsave_annual_temp,
                        int(life_ratio_temp), int(life_meas_temp),
                        num_units, com_timeprefs)

        # Record final measure savings figures and economic metrics
        # in a dict that is returned by the function
        mseg_save = {"stock": {"cost savings (total)": scostsave_tot,
                               "cost savings (annual)": scostsave_annual},
                     "energy": {"savings (total)": esave_tot,
                                "savings (annual)": esave_annual,
                                "cost savings (total)": ecostsave_tot,
                                "cost savings (annual)": ecostsave_annual},
                     "carbon": {"savings (total)": csave_tot,
                                "savings (annual)": csave_annual,
                                "cost savings (total)": ccostsave_tot,
                                "cost savings (annual)": ccostsave_annual},
                     "metrics": {"anpv": {
                                 "stock cost": stock_anpv,
                                 "energy cost": energy_anpv,
                                 "carbon cost": carbon_anpv},
                                 "irr (w/ energy $)": irr_e,
                                 "irr (w/ energy and carbon $)": irr_ec,
                                 "payback (w/ energy $)": payback_e,
                                 "payback (w/ energy and carbon $)":
                                 payback_ec,
                                 "cce": cce,
                                 "cce (w/ carbon $ benefits)": cce_bens,
                                 "ccc": ccc,
                                 "ccc (w/ energy $ benefits)": ccc_bens}}

        # Return final savings figures and economic metrics
        return mseg_save

    def reduce_sqft(self, dict1, reduce_factor):
        """ Divide "stock" and "stock cost" information by a given factor to
        handle special case when sq.ft. is used as stock """
        for (k, i) in dict1.items():
            # Do not divide any energy, carbon, or lifetime information
            if (k == "energy" or k == "carbon" or k == "lifetime"):
                continue
            else:
                if isinstance(i, dict):
                    self.reduce_sqft(i, reduce_factor)
                else:
                    dict1[k] = dict1[k] / reduce_factor
        return dict1

    def out_break_norm(self, dict1, reduce_factor):
        """ Divide a measure's climate, building, and end use-specific baseline
        energy use by its total baseline energy use, yielding climate,
        building, and end use partitioning fractions used in output plot
        breakdowns """
        for (k, i) in dict1.items():
            if isinstance(i, dict):
                self.out_break_norm(i, reduce_factor)
            else:
                if reduce_factor[k] != 0:  # Handle total energy use of zero
                    dict1[k] = dict1[k] / reduce_factor[k]
                else:
                    dict1[k] = 0
        return dict1

    def rand_list_gen(self, distrib_info, nsamples):
        """ Generate list of N randomly sampled values given input
        information on distribution name, parameters, and sample N """

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
        else:  # Raise error if unsupported distribution is entered
            raise ValueError("Unsupported input distribution specification!")

        # Return the randomly sampled list of values
        return rand_list

    def metric_update(self, rate, scost_base_add, life_base, scostsave_annual,
                      esave, ecostsave, csave, ccostsave, life_ratio, life_meas,
                      num_units, com_timeprefs):
        """ Calculate internal rate of return, simple payback, and cost of
        conserved energy/carbon from cash flows and energy/carbon
        savings across the measure lifetime """

        # Develop four initial cash flow scenarios over the measure life:
        # 1) Cash flows considering capital costs only
        # 2) Cash flows considering capital costs and energy costs
        # 3) Cash flows considering capital costs and carbon costs
        # 4) Cash flows considering capital, energy, and carbon costs

        # Determine when over the course of the measure lifetime (if at all)
        # a cost gain is realized from an avoided purchase of the baseline
        # technology due to longer measure lifetime; store this information in
        # a list of year indicators for subsequent use below.  Example: an LED
        # bulb lasts 30 years compared to a baseline bulb's 10 years, meaning
        # 3 purchases of the baseline bulb would have occured by the time the
        # LED bulb has reached the end of its life.
        added_stockcost_gain_yrs = []
        if life_ratio > 1:
            for i in range(0, life_ratio - 1):
                added_stockcost_gain_yrs.append(
                    (life_base - 1) + (life_base * i))
        # If the measure lifetime is less than 1 year, set it to 1 year
        # (a minimum for measure lifetime to work in below calculations)
        if life_meas < 1:
            life_meas = 1

        # Construct complete stock cash flows across measure lifetime
        # (normalized by number of captured stock units)

        # Initialize stock cash flows with incremental capital cost
        cashflows_s = numpy.array(scostsave_annual)

        for life_yr in range(0, life_meas):
            # Check whether an avoided cost of the baseline technology should
            # be added for given year; if not, set this term to zero
            if life_yr in added_stockcost_gain_yrs:
                scost_life = scost_base_add
            else:
                scost_life = 0

            # Add avoided capital costs and saved energy and carbon costs
            # as appropriate
            cashflows_s = numpy.append(cashflows_s, scost_life)

        cashflows_s = cashflows_s / num_units

        # Construct complete energy and carbon cash flows across measure
        # lifetime (normalized by number of captured stock units). First
        # term (reserved for initial investment figure) is zero.
        cashflows_e, cashflows_c = [numpy.append(0, [x] * life_meas) /
                                    num_units for x in [ecostsave, ccostsave]]

        # Calculate Net Present Value (NPVs) using the above cashflows
        npv_s, npv_e, npv_c = [numpy.npv(rate, x) for x in [
            cashflows_s, cashflows_e, cashflows_c]]

        # Calculate Annualized Net Present Value (ANPV) using the above
        # cashflows for later use in measure competition calculations. For
        # residential sector measures, ANPV is calculated using the
        # above NPVs, with a general discount rate applied.  For commerical
        # sector measures, ANPV is calculated using multiple discount rate
        # levels that reflect various degrees of risk tolerance observed
        # amongst commercial adopters.  These discount rate levels are imported
        # from the commercial AEO demand module data.

        # Populate ANPVs for residential sector
        # Check whether measure applies to residential sector
        if any([x in ["single family home", "multi family home",
                      "mobile home"] for x in self.bldg_type]):
            # Set ANPV values under general discount rate
            res_anpv_s_in, res_anpv_e_in, res_anpv_c = [
                numpy.pmt(rate, life_meas, x) for x in [npv_s, npv_e, npv_c]]
        # If measure does not apply to residential sector, set residential
        # ANPVs to 'None'
        else:
            res_anpv_s_in, res_anpv_e_in, res_anpv_c = (None for n in range(3))

        # Populate ANPVs for commercial sector
        # Check whether measure applies to commercial sector
        if any([x not in ["single family home", "multi family home",
                          "mobile home"] for x in self.bldg_type]):
            com_anpv_s_in, com_anpv_e_in, com_anpv_c = ({} for n in range(3))
            # Set ANPV values under 7 discount rate categories
            for ind, tps in enumerate(com_timeprefs["rates"]):
                com_anpv_s_in["rate " + str(ind + 1)],\
                    com_anpv_e_in["rate " + str(ind + 1)],\
                    com_anpv_c["rate " + str(ind + 1)] = \
                    [numpy.pmt(tps, life_meas, numpy.npv(tps, x))
                     for x in [cashflows_s, cashflows_e, cashflows_c]]
        # If measure does not apply to commercial sector, set commercial
        # ANPVs to 'None'
        else:
            com_anpv_s_in, com_anpv_e_in, com_anpv_c = (None for n in range(3))

        # Set overall ANPV dicts based on above updating of residential
        # and commercial sector ANPV values
        anpv_s_in = {"residential": res_anpv_s_in, "commercial": com_anpv_s_in}
        anpv_e_in = {"residential": res_anpv_e_in, "commercial": com_anpv_e_in}
        anpv_c = {"residential": res_anpv_c, "commercial": com_anpv_c}

        # Develop arrays of energy and carbon savings across measure
        # lifetime (for use in cost of conserved energy and carbon calcs).
        # First term (reserved for initial investment figure) is zero, and
        # each array is normalized by number of captured stock units
        esave_array = numpy.append(0, [esave] * life_meas) / num_units
        csave_array = numpy.append(0, [csave] * life_meas) / num_units

        # Calculate Net Present Value and Annualized Net Present Value (anpv)
        # of the above energy and carbon savings
        npv_esave = numpy.npv(rate, esave_array)
        npv_csave = numpy.npv(rate, csave_array)

        # Initially set economic metrics to 999 for cases where the
        # metric cannot be computed (e.g., zeros in 'cce' denominator due to
        # no energy savings)
        irr_e, irr_ec, payback_e, payback_ec, cce, cce_bens, ccc, ccc_bens = \
            (999 for n in range(8))

        # Calculate irr and simple payback for capital + energy cash flows.
        # Check to ensure thar irr/payback can be calculated for the
        # given cash flows
        if any(numpy.isclose(esave_array[1:], 0)) is False:
            try:
                irr_e = numpy.irr(cashflows_s + cashflows_e)
                payback_e = self.payback(cashflows_s + cashflows_e)
            except (ValueError, LinAlgError):
                pass

        # Calculate irr and simple payback for capital + energy + carbon cash
        # flows.  Check to ensure thar irr/payback can be calculated for the
        # given cash flows
        if any(numpy.isclose(esave_array[1:], 0)) is False or \
           any(numpy.isclose(csave_array[1:], 0)) is False:
            try:
                irr_ec = numpy.irr(cashflows_s + cashflows_e + cashflows_c)
                payback_ec = \
                    self.payback(cashflows_s + cashflows_e + cashflows_c)
            except (ValueError, LinAlgError):
                pass

        # Calculate cost of conserved energy w/ and w/o carbon cost savings
        # benefits.  Check to ensure energy savings NPV in the denominator is
        # not zero
        if any(numpy.isclose(esave_array[1:], 0)) is False:
            cce = (-npv_s / npv_esave)
            cce_bens = (-(npv_s + npv_c) / npv_esave)

        # Calculate cost of conserved carbon w/ and w/o energy cost savings
        # benefits.  Check to ensure carbon savings NPV in the denominator is
        # not zero.
        if any(numpy.isclose(csave_array[1:], 0)) is False:
            ccc = (-npv_s / npv_csave)
            ccc_bens = (-(npv_s + npv_e) / npv_csave)

        # Return all updated economic metrics
        return anpv_s_in, anpv_e_in, anpv_c, irr_e, irr_ec, payback_e, \
            payback_ec, cce, cce_bens, ccc, ccc_bens

    def payback(self, cashflows):
        """ Calculate the simple payback period given an input list of
        cash flows, which may be uneven """

        # Separate initial investment and subsequent cash flows
        # from "cashflows" input
        investment, cashflows = cashflows[0], cashflows[1:]
        # If initial investment is positive, payback = 0
        if investment >= 0:
            payback_val = 0
        else:
            # Find absolute value of initial investment to compare
            # subsequent cash flows against
            investment = abs(investment)
            # Initialize cumulative cashflow and # years tracking
            total, years, cumulative = 0, 0, []
            # Add to years and cumulative cashflow trackers while cumulative
            # cashflow < investment
            for cashflow in cashflows:
                total += cashflow
                if total < investment:
                    years += 1
                cumulative.append(total)
            # If investment pays back within the measure lifetime,
            # calculate this payback period in years
            if years < len(cashflows):
                a = years
                # Case where payback period < 1 year
                if (years - 1) < 0:
                    b = investment
                    c = cumulative[0]
                # Case where payback period >= 1 year
                else:
                    b = investment - cumulative[years - 1]
                    c = cumulative[years] - cumulative[years - 1]
                payback_val = a + (b / c)
            # If investment does not pay back within measure lifetime,
            # set payback period to artifically high number
            else:
                payback_val = 999

        # Return updated payback period value in years
        return payback_val


# Engine runs active measure adoption
class Engine(object):

    def __init__(self, measure_objects):
        self.measures = measure_objects

    @property
    def energy_savings_sum(self):
        return sum([x.master_savings["energy"]["savings (total)"] for x in
                    self._measures])

    @property
    def carbon_savings_sum(self):
        return sum([x.master_savings["carbon"]["savings (total)"] for x in
                    self._measures])

    def initialize_active(self, mseg_in, base_costperflife_in, adopt_scheme,
                          rate, adjust_savings, com_timeprefs,
                          measure_packages, out_break_in):
        """ Run initialization scheme on active measures only """
        for m in self.measures:
            # Find master microsegment and partitions, as well as measure
            # savings overlaps and markets/savings output breakout information
            m.master_mseg, m.mseg_adjust, m.mseg_out_break = \
                m.mseg_find_partition(
                    mseg_in, base_costperflife_in, adopt_scheme,
                    out_break_in, retro_rate)
            # Screen measure from further savings/metrics calculations if it
            # has sub-market scaling information with insufficient source
            # attribution
            if m.active == 1:
                # Update savings outcomes and economic metrics
                # based on master microsegment
                m.master_savings = m.calc_metric_update(
                    rate, adjust_savings, com_timeprefs, adopt_scheme)

        # Permanently remove any measures with insufficiently sourced
        # sub-market scaling information
        self.measures = [x for x in self.measures if x.active == 1]

        # If packaged measures are present, merge the individual measures that
        # contribute to the package and append to the overall measures list
        if measure_packages:
            # Run through each unique measure package and merge the
            # measures that contribute to this package
            for p in measure_packages.keys():
                # Establish a list of names for measures that contribute to the
                # package
                package_measures = measure_packages[p]
                # Determine the subset of all active measures that belong
                # to the current package
                measure_list_package = [copy.deepcopy(x) for x in self.measures
                                        if x.name in package_measures]
                # Instantiate measure package object based on packaged measure
                # subset above
                packaged_measure = Measure_Package(
                    measure_list_package, p, out_break_in)
                # Remove overlapping markets/savings between individual
                # measures in the package object
                packaged_measure.adjust_savings(
                    com_timeprefs, 'Packaged Measures')
                # Merge measures in the package object
                packaged_measure.merge_measures()
                # Update the savings outcomes and economic metrics for the
                # new packaged measure
                packaged_measure.master_savings = \
                    packaged_measure.calc_metric_update(
                        rate, adjust_savings, com_timeprefs, adopt_scheme)
                # Add the new packaged measure to the measure list for
                # further evaluation like any other regular measure
                self.measures.append(packaged_measure)

    def adjust_savings(self, com_timeprefs, adjust_type):
        """ Adjust active measure savings to reflect overlapping microsegments
        and avoid double counting energy/carbon/cost savings """
        # Establish list of key chains for all microsegments that contribute to
        # measure master microsegments, across all active measures
        mseg_keys = []

        if adjust_type == "Competing Measures":
            measure_list = self.measures
        elif adjust_type == "Packaged Measures":
            measure_list = self.measures_to_package
        else:
            raise ValueError('Invalid savings adjustment type!')

        for x in measure_list:
            mseg_keys.extend(x.mseg_adjust[
                "contributing mseg keys and values"].keys())

        # Establish list of unique key chains in mseg_keys list above,
        # ensuring that all primary microsegments are ordered (and thus
        # updated) before secondary microsegments that depend upon them
        msegs = sorted(numpy.unique(mseg_keys))

        # Run through all unique contributing microsegments in above list,
        # determining how the measure savings associated with each should be
        # adjusted to reflect measure competition/market shares and, if
        # applicable, the removal of overlapping heating/cooling supply-side
        # and demand-side savings
        for msu in msegs:
            # Determine the subset of measures that pertain to the given
            # microsegment
            measures_adj = [
                x for x in measure_list if msu in x.mseg_adjust[
                    "contributing mseg keys and values"].keys()]

            # For a heating/cooling microsegment update, find all microsegments
            # that overlap with the current contributing microsegment across
            # the supply-side and demand-side (e.g., if the current
            # microsegment key is ['AIA_CZ1', 'single family home',
            # 'electricity (grid)', 'cooling', 'supply', 'ASHP'], find all
            # demand-side microsegments with ['AIA_CZ1', 'single family home',
            # 'electricity (grid)', 'cooling'] in their key chains.
            measures_overlap = {"measures": [], "keys": []}
            msu_split = None
            if 'supply' in msu or 'demand' in msu:
                # Search for microsegment key chains that match that of the
                # current microsegment up until the 'supply' or 'demand'
                # element of the chain

                # Establish key matching criteria
                if 'supply' in msu:
                    msu_split = re.search('(.*)(\,.*supply.*)', msu).group(1)
                else:
                    msu_split = re.search('(.*)(\,.*demand.*)', msu).group(1)
                # Loop through all measures to find key chain matches
                for m in measure_list:
                    # Register the matching key chains
                    if 'supply' in msu:
                        keys = [x for x in m.mseg_adjust[
                                "contributing mseg keys and values"].keys() if
                                msu_split in x and 'demand' in x]
                    else:
                        keys = [x for x in m.mseg_adjust[
                                "contributing mseg keys and values"].keys() if
                                msu_split in x and 'supply' in x]
                    # Record the matched key chains and associated overlapping
                    # measure objects in a 'measures_overlap' dict to
                    # be used further in the 'overlap_recording' routine below
                    if len(keys) > 0:
                        measures_overlap["measures"].append(m)
                        measures_overlap["keys"].append(keys)

            # Adjust a measure's primary savings based on the share of the
            # current market microsegment it captures when directly competed
            # against other measures that apply to the same microsegment
            if "primary" in msu:
                # If multiple measures are competing for a primary
                # microsegment, determine the market shares of the
                # competing measures and adjust measure master microsegments
                # accordingly, using separate market share modeling routines
                # for residential and commercial sectors.
                if adjust_type == "Competing Measures" and \
                    len(measures_adj) > 1 and \
                    any(x in msu for x in (
                        'single family home', 'multi family home',
                        'mobile home')):
                    self.res_compete(measures_adj, msu)
                elif adjust_type == "Competing Measures" and \
                    len(measures_adj) > 1 and \
                    all(x not in msu for x in (
                        'single family home', 'multi family home',
                        'mobile home')):
                    self.com_compete(measures_adj, msu)
                elif adjust_type == "Packaged Measures" and \
                        len(measures_adj) > 1:
                    self.package_merge(measures_adj, msu)
            # Adjust a measure's secondary savings based on the market share
            # previously calculated for the primary microsegment these
            # secondary savings are associated with
            elif "secondary" in msu:
                self.secondary_mktshare_adjust(measures_adj, msu)
            # Microsegments not tagged as 'primary' or 'secondary' are
            # flagged as invalid
            else:
                raise ValueError(
                    'Microsegment type must be primary or secondary!')

            # If the microsegment applies to heating/cooling and overlaps with
            # other active microsegments across the heating/cooling supply-side
            # and demand-side, record any associated savings; these will be
            # removed from overlapping microsegments in the
            # 'overlap_adjustment' function below
            if len(measures_overlap["measures"]) > 0:
                self.overlap_recording(measures_adj, measures_overlap, msu)

        # Determine measures that require further savings adjustments to
        # reflect overlapping heating/cooling supply-side and demand-side
        # energy savings; remove these overlapping savings
        measures_overlap_adj = [
            x for x in measure_list if len(x.mseg_adjust[
                "supply-demand adjustment"]["savings"].keys()) > 0]
        self.overlap_adjustment(measures_overlap_adj)

        if adjust_type == "Competing Measures":
            # Determine measures with updated energy/carbon/cost savings and
            # update the savings outcomes and economic metrics for measures
            measures_recalc = [x for x in measure_list if x.mseg_adjust[
                "savings updated"] is True]
            for m in measures_recalc:
                m.master_savings = m.calc_metric_update(
                    rate, adjust_savings, com_timeprefs, adopt_scheme)

    def res_compete(self, measures_adj, mseg_key):
        """ Determine the shares of a given market microsegment that are
        captured by a series of residential efficiency measures that compete
        for this market microsegment; account for the secondary effects that
        any demand-side measures have on supply-side measures """
        # Initialize list of dicts that each store the annual market fractions
        # captured by competing measures; also initialize a dict that sums
        # market fractions by year across competing measures (used to normalize
        # the measure market fractions such that they all sum to 1)
        mkt_fracs = [{} for l in range(0, len(measures_adj))]
        mkt_fracs_tot = dict.fromkeys(
            measures_adj[0].master_mseg["stock"]["total"]["all"].keys(), 0)

        # Loop through competing measures and calculate market shares for each
        # based on their annualized capital and operating costs.

        # Set abbreviated names for the dictionaries containing measure
        # capital and operating cost values, accessed further below

        # Annualized capital cost dictionary
        anpv_s_in = [m.master_savings["metrics"]["anpv"]["stock cost"] for
                     m in measures_adj]
        # Annualized operating cost dictionary
        anpv_e_in = [m.master_savings["metrics"]["anpv"]["energy cost"] for
                     m in measures_adj]

        # Loop through competing measures and calculate market shares for
        # each based on their annualized capital and operating costs
        for ind, m in enumerate(measures_adj):
            # # Loop through all years in modeling time horizon
            for yr in anpv_s_in[ind].keys():
                # Ensure measure has captured stock to adjust in given year
                if (type(m.master_mseg["stock"]["competed"][
                    "measure"][yr]) == numpy.ndarray and all(
                    m.master_mseg["stock"]["competed"]["measure"][yr]) != 0) \
                    or (type(m.master_mseg["stock"]["competed"][
                        "measure"][yr]) != numpy.ndarray and m.master_mseg[
                        "stock"]["competed"]["measure"][yr] != 0):
                    # Set measure capital and operating cost inputs. * Note:
                    # operating cost is set to just energy costs (for now), but
                    # could be expanded to include maintenance and carbon costs

                    # Set capital cost (handle as numpy array or point value)
                    if type(anpv_s_in[ind][yr]) == numpy.ndarray:
                        cap_cost = numpy.zeros(len(anpv_s_in[ind][yr]))
                        for i in range(0, len(anpv_s_in[ind][yr])):
                            cap_cost[i] = anpv_s_in[ind][yr][i][
                                "residential"]
                    else:
                        cap_cost = anpv_s_in[ind][yr]["residential"]
                    # Set operating cost (handle as numpy array or point value)
                    if type(anpv_e_in[ind][yr]) == numpy.ndarray:
                        op_cost = numpy.zeros(len(anpv_e_in[ind][yr]))
                        for i in range(0, len(anpv_e_in[ind][yr])):
                            op_cost[i] = anpv_e_in[ind][yr][i][
                                "residential"]
                    else:
                        op_cost = anpv_e_in[ind][yr]["residential"]

                    # Calculate measure market fraction using log-linear
                    # regression equation that takes capital/operating
                    # costs as inputs
                    mkt_fracs[ind][yr] = numpy.exp(
                        cap_cost * m.mseg_adjust[
                            "competed choice parameters"][
                                str(mseg_key)]["b1"][yr] + op_cost *
                        m.mseg_adjust["competed choice parameters"][
                            str(mseg_key)]["b2"][yr])
                    # Add calculated market fraction to mkt fraction sum
                    mkt_fracs_tot[yr] = \
                        mkt_fracs_tot[yr] + mkt_fracs[ind][yr]

        # Loop through competing measures to normalize their calculated
        # market shares to the total market share sum; use normalized
        # market shares to make adjustments to each measure's master
        # microsegment values
        for ind, m in enumerate(measures_adj):
            # Establish starting master microsegment and contributing
            # microsegment information
            base, adj, base_list_eff, adj_list_eff, adj_list_base = \
                self.savings_adjustment_dicts(m, mseg_key)
            # Calculate annual market share fraction for the measure and
            # adjust measure's master microsegment values accordingly
            for yr in sorted(m.master_savings[
                    "metrics"]["anpv"]["stock cost"].keys()):
                # Ensure measure has captured stock to adjust in given year
                if (type(m.master_mseg["stock"]["competed"][
                    "measure"][yr]) == numpy.ndarray and all(
                    m.master_mseg["stock"]["competed"]["measure"][yr]) != 0) \
                    or (type(m.master_mseg["stock"]["competed"][
                        "measure"][yr]) != numpy.ndarray and m.master_mseg[
                        "stock"]["competed"]["measure"][yr] != 0):
                    mkt_fracs[ind][yr] = \
                        mkt_fracs[ind][yr] / mkt_fracs_tot[yr]
                    # Make the adjustment to the measure's master microsegment
                    # based on its updated market share
                    self.compete_adjustment(
                        mkt_fracs[ind], base, adj, base_list_eff,
                        adj_list_eff, adj_list_base, yr, mseg_key, m)

    def com_compete(self, measures_adj, mseg_key):
        """ Determine market shares captured by competing commercial efficiency
        measures; account for the secondary effects that any demand-side
        measures have on supply-side measures """
        # Initialize list of dicts that each store the annual market fractions
        # captured by competing measures; also initialize a dict that records
        # the total annualized capital + operating costs for each measure
        # and discount rate level (used to choose which measure is adopted
        # under each discount rate level)
        mkt_fracs = [{} for l in range(0, len(measures_adj))]
        tot_cost = [{} for l in range(0, len(measures_adj))]

        # Calculate the total annualized cost (capital + operating) needed to
        # determine market shares below

        # Initialize a flag that indicates whether any competing measures
        # have arrays of annualized capital and/or operating costs rather
        # than point values (resultant of distributions on measure inputs)
        length_array = 0
        # Set abbreviated names for the dictionaries containing measure
        # capital and operating cost values, accessed further below

        # Annualized capital cost dictionary
        anpv_s_in = [m.master_savings["metrics"]["anpv"]["stock cost"] for
                     m in measures_adj]
        # Annualized operating cost dictionary
        anpv_e_in = [m.master_savings["metrics"]["anpv"]["energy cost"] for
                     m in measures_adj]

        # Loop through competing measures and calculate market shares for
        # each based on their annualized capital and operating costs
        for ind, m in enumerate(measures_adj):
            # Loop through all years in modeling time horizon
            for yr in anpv_s_in[ind].keys():
                # Ensure measure has captured stock to adjust in given year
                if (type(m.master_mseg["stock"]["competed"][
                    "measure"][yr]) == numpy.ndarray and all(
                    m.master_mseg["stock"]["competed"]["measure"][yr]) != 0) \
                    or (type(m.master_mseg["stock"]["competed"][
                        "measure"][yr]) != numpy.ndarray and m.master_mseg[
                        "stock"]["competed"]["measure"][yr] != 0):
                    # Set measure capital and operating cost inputs. * Note:
                    # operating cost is set to just energy costs (for now), but
                    # could be expanded to include maintenance and carbon costs

                    # Determine whether any of the competing measures have
                    # arrays of annualized capital and/or operating costs; if
                    # so, find the array length. * Note: all array lengths
                    # should be equal to the 'nsamples' variable defined above
                    if length_array > 0 or \
                        any([type(x[yr]) == numpy.ndarray or
                             type(y[yr]) == numpy.ndarray for
                            x, y in zip(anpv_s_in, anpv_e_in)]) is True:
                        length_array = next(
                            (len(x[yr]) or len(y[yr]) for x, y in
                             zip(anpv_s_in, anpv_e_in) if type(x[yr]) ==
                             numpy.ndarray or type(y[yr]) == numpy.ndarray),
                            length_array)

                    # Handle cases where capital and/or operating cost inputs
                    # are specified as arrays for at least one of the competing
                    # measures. In this case, the capital and operating costs
                    # for all measures must be formatted consistently as arrays
                    # of the same length
                    if length_array > 0:
                        cap_cost, op_cost = ([
                            {} for n in range(length_array)] for n in range(2))
                        for i in range(length_array):
                            # Set capital cost input array
                            if type(anpv_s_in[ind][yr]) == numpy.ndarray:
                                cap_cost[i] = anpv_s_in[ind][yr][i][
                                    "commercial"]
                            else:
                                cap_cost[i] = anpv_s_in[ind][yr]["commercial"]
                            # Set operating cost input array
                            if type(anpv_e_in[ind][yr]) == numpy.ndarray:
                                op_cost[i] = anpv_e_in[ind][yr][i][
                                    "commercial"]
                            else:
                                op_cost[i] = anpv_e_in[ind][yr]["commercial"]
                        # Sum capital and operating cost arrays and add to the
                        # total cost dict entry for the given measure
                        tot_cost[ind][yr] = [
                            [] for n in range(length_array)]
                        for l in range(0, len(tot_cost[ind][yr])):
                            for dr in sorted(cap_cost[l].keys()):
                                tot_cost[ind][yr][l].append(
                                    cap_cost[l][dr] + op_cost[l][dr])
                    # Handle cases where capital and/or operating cost inputs
                    # are specified as point values for all competing measures
                    else:
                        # Set capital cost point value
                        cap_cost = anpv_s_in[ind][yr]["commercial"]
                        # Set operating cost point value
                        op_cost = anpv_e_in[ind][yr]["commercial"]
                        # Sum capital and opearting cost point values and add
                        # to the total cost dict entry for the given measure
                        tot_cost[ind][yr] = []
                        for dr in sorted(cap_cost.keys()):
                            tot_cost[ind][yr].append(
                                cap_cost[dr] + op_cost[dr])

        # Loop through competing measures and use total annualized capital
        # + operating costs to determine the overall share of the market
        # that is captured by each measure; use market shares to make
        # adjustments to each measure's master microsegment values
        for ind, m in enumerate(measures_adj):
            # Establish starting master microsegment and contributing
            # microsegment information
            base, adj, base_list_eff, adj_list_eff, adj_list_base = \
                self.savings_adjustment_dicts(m, mseg_key)
            # Calculate annual market share fraction for the measure and
            # adjust measure's master microsegment values accordingly
            for yr in m.master_savings[
                    "metrics"]["anpv"]["stock cost"].keys():
                # Ensure measure has captured stock to adjust in given year
                if (type(m.master_mseg["stock"]["competed"][
                    "measure"][yr]) == numpy.ndarray and all(
                    m.master_mseg["stock"]["competed"]["measure"][yr]) != 0) \
                    or (type(m.master_mseg["stock"]["competed"][
                        "measure"][yr]) != numpy.ndarray and m.master_mseg[
                        "stock"]["competed"]["measure"][yr] != 0):
                    # Set the fractions of commericial adopters who fall into
                    # each discount rate category for this particular
                    # microsegment
                    mkt_dists = m.mseg_adjust[
                        "competed choice parameters"][str(mseg_key)][
                        "rate distribution"][yr]
                    # For each discount rate category, find which measure has
                    # the lowest annualized cost and assign that measure the
                    # share of commercial market adopters defined for that
                    # category above

                    # Handle cases where capital and/or operating cost inputs
                    # are specified as lists for at least one of the competing
                    # measures.
                    if length_array > 0:
                        mkt_fracs[ind][yr] = [
                            [] for n in range(length_array)]
                        for l in range(length_array):
                            for ind2, dr in enumerate(tot_cost[ind][yr][l]):
                                # If the measure has the lowest annualized
                                # cost, assign it the appropriate market share
                                # for the current discount rate category being
                                # looped through; otherwise, set its market
                                # fraction for that category to zero
                                if tot_cost[ind][yr][l][ind2] == \
                                   min([tot_cost[x][yr][l][ind2] for x in
                                        range(0, len(measures_adj))]):
                                    mkt_fracs[ind][yr][l].append(
                                        mkt_dists[ind2])  # * EQUALS? *
                                else:
                                    mkt_fracs[ind][yr][l].append(0)
                            mkt_fracs[ind][yr][l] = sum(
                                mkt_fracs[ind][yr][l])
                        # Convert market fractions list to numpy array for
                        # use in compete_adjustment function below
                        mkt_fracs[ind][yr] = numpy.array(
                            mkt_fracs[ind][yr])
                    # Handle cases where capital and/or operating cost inputs
                    # are specified as point values for all competing measures
                    else:
                        mkt_fracs[ind][yr] = []
                        for ind2, dr in enumerate(tot_cost[ind][yr]):
                            if tot_cost[ind][yr][ind2] == \
                               min([tot_cost[x][yr][ind2] for x in range(
                                    0, len(measures_adj))]):
                                mkt_fracs[ind][yr].append(mkt_dists[ind2])
                            else:
                                mkt_fracs[ind][yr].append(0)
                        mkt_fracs[ind][yr] = sum(mkt_fracs[ind][yr])

                    # Make the adjustment to the measure's master microsegment
                    # based on its updated market share
                    self.compete_adjustment(
                        mkt_fracs[ind], base, adj, base_list_eff,
                        adj_list_eff, adj_list_base, yr, mseg_key, m)

    def package_merge(self, measures_adj, mseg_key):
        # Initialize list of dicts that each store the share of an adopting
        # building's energy use that is assigned to each of multiple
        # measures with overlapping baseline microsegments that contribute
        # to a measure package
        package_fracs = [{} for l in range(0, len(measures_adj))]

        # Loop through individual measures to be packaged and adjust
        # the master microsegment values for each by the share of
        # building energy use assigned to that measure
        for ind, m in enumerate(measures_adj):
            # Establish starting master microsegment and contributing
            # microsegment information
            base, adj, base_list_eff, adj_list_eff, adj_list_base = \
                self.savings_adjustment_dicts(m, mseg_key)
            # Assign building energy use share for the measure to be packaged
            # and adjust measure's master microsegment values accordingly
            for yr in m.master_mseg["stock"]["total"]["all"].keys():
                package_fracs[ind][yr] = 1 / len(measures_adj)
                # Make the adjustment to the measure's master microsegment
                # based on its assigned building energy use share
                self.compete_adjustment(
                    package_fracs[ind], base, adj, base_list_eff, adj_list_eff,
                    adj_list_base, yr, mseg_key, m)

    def savings_adjustment_dicts(self, m, mseg_key):
        """ Establish a measure's starting master microsegment and the
        contributing microsegment information needed to adjust the
        master microsegment values following measure competition and/or
        heating/cooling supply and demand-side savings overlap adjustments"""
        # Organize relevant starting master microsegment values into a list
        base = m.master_mseg
        # Set total-efficient and competed-efficient master microsegment
        # values to be updated in the compete_adjustment or overlap_adjustment
        # functions below
        base_list_eff = [
            base["cost"]["stock"]["total"]["efficient"],
            base["cost"]["energy"]["total"]["efficient"],
            base["cost"]["carbon"]["total"]["efficient"],
            base["energy"]["total"]["efficient"],
            base["carbon"]["total"]["efficient"],
            base["cost"]["stock"]["competed"]["efficient"],
            base["cost"]["energy"]["competed"]["efficient"],
            base["cost"]["carbon"]["competed"]["efficient"],
            base["energy"]["competed"]["efficient"],
            base["carbon"]["competed"]["efficient"]]
        # Set up lists that will be used to determine the energy, carbon,
        # and cost savings associated with the contributing microsegment that
        # must be adjusted according to a measure's calculated market share
        # and/or heating/cooling supply-side and demand-side savings overlaps
        adj = m.mseg_adjust["contributing mseg keys and values"][mseg_key]
        # Total and competed baseline energy, carbon, and cost for contributing
        # microsegment
        adj_list_base = [
            adj["cost"]["stock"]["total"]["baseline"],
            adj["cost"]["energy"]["total"]["baseline"],
            adj["cost"]["carbon"]["total"]["baseline"],
            adj["energy"]["total"]["baseline"],
            adj["carbon"]["total"]["baseline"],
            adj["cost"]["stock"]["competed"]["baseline"],
            adj["cost"]["energy"]["competed"]["baseline"],
            adj["cost"]["carbon"]["competed"]["baseline"],
            adj["energy"]["competed"]["baseline"],
            adj["carbon"]["competed"]["baseline"]]
        # Total and competed energy, carbon, and cost for contributing
        # microsegment under full efficient measure adoption
        adj_list_eff = [
            adj["cost"]["stock"]["total"]["efficient"],
            adj["cost"]["energy"]["total"]["efficient"],
            adj["cost"]["carbon"]["total"]["efficient"],
            adj["energy"]["total"]["efficient"],
            adj["carbon"]["total"]["efficient"],
            adj["cost"]["stock"]["competed"]["efficient"],
            adj["cost"]["energy"]["competed"]["efficient"],
            adj["cost"]["carbon"]["competed"]["efficient"],
            adj["energy"]["competed"]["efficient"],
            adj["carbon"]["competed"]["efficient"]]

        # Return baseline master microsegment and adjustment microsegments
        return base, adj, base_list_eff, adj_list_eff, adj_list_base

    def compete_adjustment(
            self, adj_fracs, base, adj, base_list_eff, adj_list_eff,
            adj_list_base, yr, mseg_key, measure):
        """ Adjust the measure's master microsegment values by applying
        its competed market share to the measure's captured stock and energy,
        carbon, and associated cost savings that are attributed to the current
        contributing microsegment that is being competed """

        # Set market shares for the competed stock in the current year, and
        # for the weighted combination of the competed stock for the current
        # and all previous years. Handle this calculation differently for
        # primary and secondary microsegment types

        # Set primary microsegment competed and total weighted market shares
        if "primary" in mseg_key:
            # Competed stock market share (represents adjustment for current
            # year)
            adj_frac_comp = copy.deepcopy(adj_fracs[yr])

            # Combine the competed market share adjustment for the stock
            # captured by the measure in the current year with that of the
            # stock captured by the measure in all previous years, yielding a
            # weighted market share adjustment

            # Determine the subset of all years leading up to the current
            # year in the modeling time horizon
            weighting_yrs = sorted([
                x for x in adj_fracs.keys() if int(x) <= int(yr)])
            # Loop through the above set of years, successively updating the
            # weighted market share based on the captured stock in each year
            for ind, wyr in enumerate(weighting_yrs):
                # First year in time horizon; weighted market share equals
                # market share for the captured stock in current year only
                if ind == 0:
                    adj_frac_tot = copy.deepcopy(adj_fracs[yr])
                # Subsequent year; weighted market share combines market share
                # for captured stock in current year and all previous years
                else:
                    # Only update weighted market share if measure captures
                    # stock in the current year
                    if type(adj["stock"]["total"]["measure"][wyr]) == \
                        numpy.ndarray and all(
                            adj["stock"]["total"]["measure"][wyr]) != 0 or \
                       type(adj["stock"]["total"]["measure"][wyr]) != \
                        numpy.ndarray and \
                            adj["stock"]["total"]["measure"][wyr] != 0:
                        # Develop the split between captured stock in the
                        # current year and all previously captured stock
                        wt_comp = adj["stock"]["competed"]["measure"][wyr] / \
                            adj["stock"]["total"]["measure"][wyr]
                        # Calculate weighted combination of market shares for
                        # current and previously captured stock
                        adj_frac_tot = adj_fracs[wyr] * wt_comp + \
                            adj_frac_tot * (1 - wt_comp)
        # Set secondary microsegment competed and total weighted market shares
        # (based on competed/total market shares previously calculated for
        # associated primary microsegment)
        elif "secondary" in mseg_key:
            # Competed stock market share (represents adjustment for current
            # year)
            adj_frac_comp = adj_fracs["competed"]
            # Total weighted stock market share (represents adjustments for
            # current and all previous years)
            adj_frac_tot = adj_fracs["total"]
        # Microsegments not tagged as 'primary' or 'secondary' are flagged
        # as invalid
        else:
            raise ValueError(
                'Microsegment type must be primary or secondary!')

        # For a primary contributing microsegment with secondary effects,
        # record market share information that will subsequently be used
        # to adjust associated secondary microsegments and associated savings
        if "lighting" in mseg_key and len(measure.mseg_adjust[
                "secondary mseg adjustments"]["market share"][
                "original stock (total captured)"].keys()) != 0:
            # Determine the climate zone, building type, and structure
            # type for the current contributing primary microsegment
            cz_bldg_struct = re.search(
                ("'[\w+\s*]+\(*\w+\)*',\s'([\w+\s*]+\(*\w+\)*)',"
                 "\s'([\w+\s*]+\(*\w+\)*)',\s'[\w+\s*]+\(*\w+\)*',"
                 "\s'[\w+\s*]+\(*\w+\)*',\s'[\w+\s*]+\(*\w+\)*',"
                 "\s'([\w+\s*]+\(*\w+\)*)'"), mseg_key)
            # Use climate zone, building type, and structure type as
            # the key for linking the primary and its associated
            # secondary microsegment
            secnd_mseg_adjkey = str(
                (cz_bldg_struct.group(1), cz_bldg_struct.group(2),
                 cz_bldg_struct.group(3)))
            # Record original and adjusted primary stock numbers as part of
            # the measure's 'mseg_adjust' attribute
            secnd_adj_mktshr = measure.mseg_adjust[
                "secondary mseg adjustments"]["market share"]
            # Original total captured stock
            secnd_adj_mktshr["original stock (total captured)"][
                secnd_mseg_adjkey][yr] += \
                adj["stock"]["total"]["measure"][yr]
            # Original competed and captured stock
            secnd_adj_mktshr["original stock (competed and captured)"][
                secnd_mseg_adjkey][yr] += \
                adj["stock"]["competed"]["measure"][yr]
            # Adjusted total captured stock
            secnd_adj_mktshr["adjusted stock (total captured)"][
                secnd_mseg_adjkey][yr] += \
                (adj["stock"]["total"]["measure"][yr] * adj_frac_tot)
            # Adjusted competed and captured stock
            secnd_adj_mktshr["adjusted stock (competed and captured)"][
                secnd_mseg_adjkey][yr] += \
                (adj["stock"]["competed"]["measure"][yr] * adj_frac_comp)

        # Adjust the total and competed stock captured by the measure by
        # the appropriate measure market share for the master microsegment and
        # current contributing microsegment
        base["stock"]["total"]["measure"][yr] = \
            base["stock"]["total"]["measure"][yr] - \
            adj["stock"]["total"]["measure"][yr] * (1 - adj_frac_tot)
        base["stock"]["competed"]["measure"][yr] = \
            base["stock"]["competed"]["measure"][yr] - \
            adj["stock"]["competed"]["measure"][yr] * (1 - adj_frac_comp)
        adj["stock"]["total"]["measure"][yr] = \
            adj["stock"]["total"]["measure"][yr] * adj_frac_tot
        adj["stock"]["competed"]["measure"][yr] = \
            adj["stock"]["competed"]["measure"][yr] * adj_frac_comp

        # Adjust the total and competed energy, carbon, and associated cost
        # savings by the appropriate measure market share for the master
        # microsegment and current contributing microsegment
        base["cost"]["stock"]["total"]["efficient"][yr], \
            base["cost"]["energy"]["total"]["efficient"][yr], \
            base["cost"]["carbon"]["total"]["efficient"][yr], \
            base["energy"]["total"]["efficient"][yr], \
            base["carbon"]["total"]["efficient"][yr] = [
                x[yr] + ((z[yr] - y[yr]) * (1 - adj_frac_tot)) for x, y, z in
                zip(base_list_eff[0:5], adj_list_eff[0:5], adj_list_base[0:5])]
        base["cost"]["stock"]["competed"]["efficient"][yr], \
            base["cost"]["energy"]["competed"]["efficient"][yr], \
            base["cost"]["carbon"]["competed"]["efficient"][yr], \
            base["energy"]["competed"]["efficient"][yr], \
            base["carbon"]["competed"]["efficient"][yr] = [
                x[yr] + ((z[yr] - y[yr]) * (1 - adj_frac_comp)) for x, y, z in
                zip(base_list_eff[5:], adj_list_eff[5:], adj_list_base[5:])]
        adj["cost"]["stock"]["total"]["efficient"][yr], \
            adj["cost"]["energy"]["total"]["efficient"][yr], \
            adj["cost"]["carbon"]["total"]["efficient"][yr], \
            adj["energy"]["total"]["efficient"][yr], \
            adj["carbon"]["total"]["efficient"][yr] = [
                x[yr] + ((y[yr] - x[yr]) * (1 - adj_frac_tot)) for x, y in
                zip(adj_list_eff[0:5], adj_list_base[0:5])]
        adj["cost"]["stock"]["competed"]["efficient"][yr], \
            adj["cost"]["energy"]["competed"]["efficient"][yr], \
            adj["cost"]["carbon"]["competed"]["efficient"][yr], \
            adj["energy"]["competed"]["efficient"][yr], \
            adj["carbon"]["competed"]["efficient"][yr] = [
                x[yr] + ((y[yr] - x[yr]) * (1 - adj_frac_comp)) for x, y in
                zip(adj_list_eff[5:], adj_list_base[5:])]

        # Register the measure's savings adjustments if not already registered
        if measure.mseg_adjust["savings updated"] is not True:
            measure.mseg_adjust["savings updated"] = True

    def secondary_mktshare_adjust(self, measures_adj, mseg_key):
        """ Adjust a measure's secondary microsegment values to reflect the
        the updated market shares calculated for an associated primary
        microsegment """
        # Loop through all measures that apply to the current contributing
        # secondary microsegment
        for ind, m in enumerate(measures_adj):
            # Establish starting master microsegment and current contributing
            # secondary microsegment information for the measure
            base, adj, base_list_eff, adj_list_eff, adj_list_base = \
                self.savings_adjustment_dicts(m, mseg_key)

            # Adjust measure savings for the current contributing
            # secondary microsegment based on the market share calculated
            # for an associated primary contributing microsegment
            for yr in adj["energy"]["total"]["baseline"].keys():
                # Determine the climate zone, building type, and structure
                # type for the current contributing secondary microsegment
                cz_bldg_struct = re.search(
                    ("'[\w+\s*]+\(*\w+\)*',\s'([\w+\s*]+\(*\w+\)*)',"
                     "\s'([\w+\s*]+\(*\w+\)*)',\s'[\w+\s*]+\(*\w+\)*',"
                     "\s'[\w+\s*]+\(*\w+\)*',\s'[\w+\s*]+\(*\w+\)*',"
                     "\s'([\w+\s*]+\(*\w+\)*)'"), mseg_key)
                # Use climate zone, building type, and structure type as
                # the key for linking the secondary and its associated
                # primary microsegment
                secnd_mseg_adjkey = str(
                    (cz_bldg_struct.group(1), cz_bldg_struct.group(2),
                     cz_bldg_struct.group(3)))
                # Find the appropriate market share adjustment information
                # for the given secondary climate zone, building type, and
                # structure type in the measure's 'mseg_adjust' attribute
                # and scale down the secondary and master savings accordingly
                secnd_adj_mktshr = m.mseg_adjust[
                    "secondary mseg adjustments"]["market share"]
                # Check to ensure that market share adjustment information
                # exists for the secondary microsegment climate zone, building
                # type, and structure type
                if secnd_mseg_adjkey in \
                   secnd_adj_mktshr["original stock (total captured)"].keys():
                    # Calculate the market share adjustment factors to apply
                    # to the secondary and master savings, for both the
                    # currently competed secondary stock and the
                    # total current and previously competed secondary stock

                    # Initialize dictionary to store competed and total market
                    # adjustment factors for the secondary microsegments
                    adj_factors = {"total": None, "competed": None}
                    # Calculate and store competed and total adjustment factors
                    adj_factors["competed"] = secnd_adj_mktshr[
                        "adjusted stock (competed and captured)"][
                        secnd_mseg_adjkey][yr] / secnd_adj_mktshr[
                        "original stock (competed and captured)"][
                        secnd_mseg_adjkey][yr]
                    adj_factors["total"] = secnd_adj_mktshr[
                        "adjusted stock (total captured)"][
                        secnd_mseg_adjkey][yr] / secnd_adj_mktshr[
                        "original stock (total captured)"][
                        secnd_mseg_adjkey][yr]
                    # Apply the market share adjustment factors to the
                    # secondary and master savings
                    self.compete_adjustment(
                        adj_factors, base, adj, base_list_eff, adj_list_eff,
                        adj_list_base, yr, mseg_key, m)
                # Raise error if no adjustment information exists
                else:
                    raise KeyError(
                        'Secondary market share adjustment info. missing!')

    def overlap_recording(self, measures_adj, measures_overlap, mseg_key):
        """ For heating/cooling measures, record any savings associated
        with the current contributing microsegment that overlap with savings
        for other active contributing microsegments across the supply-side and
        demand-side """
        # Loop through all heating/cooling measures that apply to the the
        # current contributing microsegment and which have savings overlaps
        # across the supply-side and demand-side
        for ind, m in enumerate(measures_adj):
            # Establish starting master microsegment and current contributing
            # microsegment information for the measure
            base, adj, base_list_eff, adj_list_eff, adj_list_base = \
                self.savings_adjustment_dicts(m, mseg_key)
            # Record any measure savings associated with the current
            # contributing microsegment; these will be removed from
            # overlapping microsegments in the 'overlap_adjustment' function
            for yr in adj["energy"]["total"]["baseline"].keys():
                # Loop through all overlapping measure microsegments and
                # record the overlapping savings associated with the
                # current measure microsegment
                for ind2, ms in enumerate(measures_overlap["measures"]):
                    keys = measures_overlap["keys"][ind2]
                    for k in keys:
                        ms.mseg_adjust["supply-demand adjustment"][
                            "savings"][k][yr] += (
                                adj["energy"]["total"]["baseline"][yr] -
                                adj["energy"]["total"]["efficient"][yr])

    def overlap_adjustment(self, measures_overlap_adj):
        """ For heating/cooling measures, remove any measure savings that
        have been determined to overlap with the savings of other heating/
        cooling measures across the supply-side and demand-side """
        # Loop through all heating/cooling measures with savings overlaps
        # across the supply-side and demand-side
        for m in measures_overlap_adj:
            for mseg in m.mseg_adjust[
                    "supply-demand adjustment"]["savings"].keys():
                # Establish starting master microsegment and contributing
                # microsegment information
                base, adj, base_list_eff, adj_list_eff, adj_list_base = \
                    self.savings_adjustment_dicts(m, mseg)
                # Calculate annual supply-demand overlap adjustment fraction
                # for the measure and adjust measure's master microsegment
                # values accordingly
                for yr in m.mseg_adjust[
                        "supply-demand adjustment"]["savings"][mseg].keys():
                    # Calculate supply-demand adjustment fraction
                    if m.mseg_adjust["supply-demand adjustment"][
                       "total"][mseg][yr] == 0:
                        overlap_adj_frac = 0
                    else:
                        overlap_adj_frac = m.mseg_adjust[
                            "supply-demand adjustment"]["savings"][
                            mseg][yr] / m.mseg_adjust[
                            "supply-demand adjustment"]["total"][mseg][yr]
                    # Adjust total and competed savings by supply-demand
                    # adjustment fraction
                    base["cost"]["energy"]["total"]["efficient"][yr], \
                        base["cost"]["carbon"]["total"]["efficient"][yr], \
                        base["energy"]["total"]["efficient"][yr],\
                        base["carbon"]["total"]["efficient"][yr] = \
                            [x[yr] + ((z[yr] - y[yr]) * overlap_adj_frac)
                             for x, y, z in zip(
                                base_list_eff[1:5], adj_list_eff[1:5],
                                adj_list_base[1:5])]
                    base["cost"]["energy"]["competed"]["efficient"][yr], \
                        base["cost"]["carbon"]["competed"]["efficient"][yr], \
                        base["energy"]["competed"]["efficient"][yr],\
                        base["carbon"]["competed"]["efficient"][yr] = \
                            [x[yr] + ((z[yr] - y[yr]) * overlap_adj_frac)
                             for x, y, z in zip(
                                base_list_eff[6:], adj_list_eff[6:],
                                adj_list_base[6:])]
                    # Register the measure's savings adjustments if not already
                    # registered
                    if m.mseg_adjust["savings updated"] is not True:
                        m.mseg_adjust["savings updated"] = True

    def write_outputs(self, json_output_file):
        """ Write selected measure outputs to a summary JSON file """

        # Initialize a dictionary to be populated with measure summary outputs
        measure_output_dict = {}

        # Loop through all measures and populate above dict of summary outputs
        for m in self.measures:
            # Create list of efficient energy and carbon markets/savings
            eff_summary = [
                m.master_mseg["energy"]["total"]["efficient"],
                m.master_savings["energy"]["savings (total)"],
                m.master_savings["energy"]["cost savings (total)"],
                m.master_mseg["carbon"]["total"]["efficient"],
                m.master_savings["carbon"]["savings (total)"],
                m.master_savings["carbon"]["cost savings (total)"],
                m.master_savings["metrics"]["irr (w/ energy $)"],
                m.master_savings["metrics"][
                    "irr (w/ energy and carbon $)"],
                m.master_savings["metrics"]["payback (w/ energy $)"],
                m.master_savings["metrics"][
                    "payback (w/ energy and carbon $)"],
                m.master_savings["metrics"]["cce"],
                m.master_savings["metrics"][
                    "cce (w/ carbon $ benefits)"],
                m.master_savings["metrics"]["ccc"],
                m.master_savings["metrics"][
                    "ccc (w/ energy $ benefits)"]]
            # Order the year entries of in the above markets/savings outputs
            eff_summary = [
                OrderedDict(sorted(x.items())) for x in eff_summary]

            # Check if the current measure's efficent energy/carbon
            # markets, energy/carbon savings, and associated cost outputs
            # are arrays of values.  If so, find the average and 5th/95th
            # percentile values of each output array and report out.
            # Otherwise, report the point values for each output
            if any([type(x) == numpy.ndarray for x in
                    m.master_mseg["energy"]["total"]["efficient"].values()]):
                # Average values for outputs
                energy_eff_avg, energy_save_avg, energy_costsave_avg, \
                    carb_eff_avg, carb_save_avg, carb_costsave_avg, \
                    irr_e_avg, irr_ec_avg, payback_e_avg, payback_ec_avg, \
                    cce_avg, cce_c_avg, ccc_avg, ccc_e_avg = \
                    [{k: numpy.mean(v) for k, v in z.items()} for
                     z in eff_summary]
                # 5th percentile values for outputs
                energy_eff_low, energy_save_low, energy_costsave_low, \
                    carb_eff_low, carb_save_low, carb_costsave_low,\
                    irr_e_low, irr_ec_low, payback_e_low, payback_ec_low, \
                    cce_low, cce_c_low, ccc_low, ccc_e_low = \
                    [{k: numpy.percentile(v, 5) for k, v in z.items()} for
                     z in eff_summary]
                # 95th percentile values for outputs
                energy_eff_high, energy_save_high, energy_costsave_high, \
                    carb_eff_high, carb_save_high, carb_costsave_high, \
                    irr_e_high, irr_ec_high, payback_e_high, \
                    payback_ec_high, cce_high, cce_c_high, ccc_high, \
                    ccc_e_high = \
                    [{k: numpy.percentile(v, 95) for k, v in z.items()} for
                     z in eff_summary]
            else:
                energy_eff_avg, energy_save_avg, energy_costsave_avg, \
                    carb_eff_avg, carb_save_avg, carb_costsave_avg, \
                    irr_e_avg, irr_ec_avg, payback_e_avg, payback_ec_avg, \
                    cce_avg, cce_c_avg, ccc_avg, ccc_e_avg,\
                    energy_eff_low, energy_save_low, energy_costsave_low, \
                    carb_eff_low, carb_save_low, carb_costsave_low, \
                    irr_e_low, irr_ec_low, payback_e_low, payback_ec_low, \
                    cce_low, cce_c_low, ccc_low, ccc_e_low, \
                    energy_eff_high, energy_save_high, \
                    energy_costsave_high, carb_eff_high, carb_save_high, \
                    carb_costsave_high, irr_e_high, irr_ec_high, \
                    payback_e_high, payback_ec_high, cce_high, \
                    cce_c_high, ccc_high, ccc_e_high = \
                    [x for x in eff_summary] * 3

            # Set up subscript translator for carbon variable strings
            sub = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

            # Update the dict of measure summary outputs, using the
            # measure name as a dictionary key with the summary
            # outputs as its associated value (formatted in an
            # ordered dict)
            measure_output_dict[m.name] = OrderedDict([
                # Update filtering output variables for the measure
                ("Filter Variables", OrderedDict([
                    ("Measure Climate Zone", m.climate_zone),
                    ("Measure Building Type", m.bldg_type),
                    ("Measure Structure Type", m.structure_type),
                    ("Measure Fuel Type", m.fuel_type["primary"]),
                    ("Measure End Use", m.end_use["primary"])])),
                # Update overall markets and savings for the measure
                ("Markets and Savings (Overall)", OrderedDict([
                    # Order year entries of baseline energy market
                    ("Baseline Energy Use (MMBtu)",
                        OrderedDict(sorted(m.master_mseg[
                            "energy"]["total"]["baseline"].items()))),
                    ("Efficient Energy Use (MMBtu)", energy_eff_avg),
                    ("Efficient Energy Use (low) (MMBtu)", energy_eff_low),
                    ("Efficient Energy Use (high) (MMBtu)", energy_eff_high),
                    # Order year entries of baseline carbon market
                    ("Baseline CO2 Emissions  (MMTons)".translate(sub),
                        OrderedDict(sorted(m.master_mseg[
                            "carbon"]["total"]["baseline"].items()))),
                    ("Efficient CO2 Emissions (MMTons)".translate(sub),
                        carb_eff_avg),
                    ("Efficient CO2 Emissions (low) (MMTons)".translate(
                        sub), carb_eff_low),
                    ("Efficient CO2 Emissions (high) (MMTons)".translate(
                        sub), carb_eff_high),
                    ("Energy Savings (MMBtu)", energy_save_avg),
                    ("Energy Savings (low) (MMBtu)", energy_save_low),
                    ("Energy Savings (high) (MMBtu)", energy_save_high),
                    ("Energy Cost Savings (USD)", energy_costsave_avg),
                    ("Energy Cost Savings (low) (USD)", energy_costsave_low),
                    ("Energy Cost Savings (high) (USD)", energy_costsave_high),
                    ("Avoided CO2 Emissions (MMTons)".translate(sub),
                        carb_save_avg),
                    ("Avoided CO2 Emissions (low) (MMTons)".translate(sub),
                        carb_save_low),
                    ("Avoided CO2 Emissions (high) (MMTons)".translate(sub),
                        carb_save_high),
                    ("CO2 Cost Savings (USD)".translate(sub),
                        carb_costsave_avg),
                    ("CO2 Cost Savings (low) (USD)".translate(sub),
                        carb_costsave_low),
                    ("CO2 Cost Savings (high) (USD)".translate(sub),
                        carb_costsave_high)])),
                # Update by-category markets and savings for the measure
                # (initially the same as overall markets/savings, updated by
                # output category partitions below)
                ("Markets and Savings (by Category)", OrderedDict([
                    # Order year entries of baseline energy market
                    ("Baseline Energy Use (MMBtu)",
                        OrderedDict(sorted(m.master_mseg[
                            "energy"]["total"]["baseline"].items()))),
                    ("Efficient Energy Use (MMBtu)", energy_eff_avg),
                    ("Efficient Energy Use (low) (MMBtu)", energy_eff_low),
                    ("Efficient Energy Use (high) (MMBtu)", energy_eff_high),
                    # Order year entries of baseline carbon market
                    ("Baseline CO2 Emissions  (MMTons)".translate(sub),
                        OrderedDict(sorted(m.master_mseg[
                            "carbon"]["total"]["baseline"].items()))),
                    ("Efficient CO2 Emissions (MMTons)".translate(sub),
                        carb_eff_avg),
                    ("Efficient CO2 Emissions (low) (MMTons)".translate(
                        sub), carb_eff_low),
                    ("Efficient CO2 Emissions (high) (MMTons)".translate(
                        sub), carb_eff_high),
                    ("Energy Savings (MMBtu)", energy_save_avg),
                    ("Energy Savings (low) (MMBtu)", energy_save_low),
                    ("Energy Savings (high) (MMBtu)", energy_save_high),
                    ("Energy Cost Savings (USD)", energy_costsave_avg),
                    ("Energy Cost Savings (low) (USD)", energy_costsave_low),
                    ("Energy Cost Savings (high) (USD)", energy_costsave_high),
                    ("Avoided CO2 Emissions (MMTons)".translate(sub),
                        carb_save_avg),
                    ("Avoided CO2 Emissions (low) (MMTons)".translate(sub),
                        carb_save_low),
                    ("Avoided CO2 Emissions (high) (MMTons)".translate(sub),
                        carb_save_high),
                    ("CO2 Cost Savings (USD)".translate(sub),
                        carb_costsave_avg),
                    ("CO2 Cost Savings (low) (USD)".translate(sub),
                        carb_costsave_low),
                    ("CO2 Cost Savings (high) (USD)".translate(sub),
                        carb_costsave_high)])),
                # Update economic metrics for the measure
                ("Economic Metrics", OrderedDict([
                    ("IRR (%)", irr_e_avg),
                    ("IRR (low) (%)", irr_e_low),
                    ("IRR (high) (%)", irr_e_high),
                    ("IRR (w/ CO2 cost savings) (%)".translate(sub),
                        irr_ec_avg),
                    ("IRR (w/ CO2 cost savings) (low) (%)".translate(sub),
                        irr_ec_low),
                    ("IRR (w/ CO2 cost savings) (high) (%)".translate(sub),
                        irr_ec_high),
                    ("Payback (years)", payback_e_avg),
                    ("Payback (low) (years)", payback_e_low),
                    ("Payback (high) (years)", payback_e_high),
                    ("Payback (w/ CO2 cost savings) (years)".translate(sub),
                        payback_ec_avg),
                    (("Payback (w/ CO2 cost savings) "
                      "(low) (years)").translate(sub), payback_ec_low),
                    (("Payback (w/ CO2 cost savings) "
                      "(high) (years)").translate(sub), payback_ec_high),
                    ("Cost of Conserved Energy ($/MMBtu saved)", cce_avg),
                    ("Cost of Conserved Energy (low) ($/MMBtu saved)",
                        cce_low),
                    ("Cost of Conserved Energy (high) ($/MMBtu saved)",
                        cce_high),
                    (("Cost of Conserved Energy (w/ CO2 cost savings "
                      "benefit) ($/MMBtu saved)").translate(sub), cce_c_avg),
                    (("Cost of Conserved Energy (w/ CO2 cost savings "
                      "benefit) (low) ($/MMBtu saved)").translate(sub),
                     cce_c_low),
                    (("Cost of Conserved Energy (w/ CO2 cost savings "
                      "benefit) (high) ($/MMBtu saved)").translate(sub),
                     cce_c_high),
                    (("Cost of Conserved CO2 "
                      "($/MMTon CO2 avoided)").translate(sub), ccc_avg),
                    (("Cost of Conserved CO2 (low) "
                      "($/MMTon CO2 avoided)").translate(sub), ccc_low),
                    (("Cost of Conserved CO2 (high) "
                      "($/MMTon CO2 avoided)").translate(sub), ccc_high),
                    (("Cost of Conserved CO2 "
                      "(w/ energy cost savings benefit) "
                      "($/MMTon CO2 avoided)").translate(sub), ccc_e_avg),
                    (("Cost of Conserved CO2 (low) "
                      "(w/ energy cost savings benefit) "
                      "($/MMTon CO2 avoided)").translate(sub), ccc_e_low),
                    (("Cost of Conserved CO2 (high) "
                      "(w/ energy cost savings benefit) "
                      "($/MMTon CO2 avoided)").translate(sub),
                     ccc_e_high)]))])

            # Scale down the measure's overall energy and carbon markets/
            # savings by the climate zone, building type, and end use
            # partitioning fractions established for the measure in the
            # 'mseg_find_partition' function
            for k in measure_output_dict[m.name][
                    'Markets and Savings (by Category)'].keys():
                measure_output_dict[m.name][
                    'Markets and Savings (by Category)'][k] = \
                    self.out_break_walk(
                        copy.deepcopy(m.mseg_out_break), measure_output_dict[
                            m.name]['Markets and Savings (by Category)'][k])

        # Write summary outputs for all measures to a JSON
        with open(json_output_file, "w") as jso:
            json.dump(measure_output_dict, jso, indent=4)

    def out_break_walk(self, adjust_dict, adjust_val):
        """ Break out overall measure energy and carbon markets/savings by
        climate zone, building type, and end use """
        for (k, i) in sorted(adjust_dict.items()):
            if isinstance(i, dict):
                self.out_break_walk(i, adjust_val)
            else:
                # Apply appropriate climate zone/building type/end use
                # partitioning fraction to the overall market/savings
                # value
                adjust_dict[k] = adjust_dict[k] * adjust_val[k]
        # Return broken out markets/savings values
        return adjust_dict


# Define class for measure package objects
class Measure_Package(Measure, Engine):

    def __init__(self, measure_list_package, p, out_break_in):
        # Set the list of measures to package
        self.measures_to_package = measure_list_package
        # Set the name of the measure package
        self.name = "Package: " + p
        # Set output filtering variables for the measure
        # package (climate, building, structure, fuel, end use)
        self.climate_zone = []
        self.bldg_type = []
        self.structure_type = []
        self.fuel_type = {"primary": []}
        self.end_use = {"primary": []}
        # Set contributing microsegment information attribute
        # (used for measure competition)
        self.mseg_adjust = {}
        # Set master microsegment and savings attributes
        self.master_mseg = {
            "stock": {
                "total": {"all": None, "measure": None},
                "competed": {"all": None, "measure": None}},
            "energy": {
                "total": {"baseline": None, "efficient": None},
                "competed": {"baseline": None, "efficient": None}},
            "carbon": {
                "total": {"baseline": None, "efficient": None},
                "competed": {"baseline": None, "efficient": None}},
            "cost": {
                "stock": {
                    "total": {"baseline": None, "efficient": None},
                    "competed": {"baseline": None, "efficient": None}},
                "energy": {
                    "total": {"baseline": None, "efficient": None},
                    "competed": {"baseline": None, "efficient": None}},
                "carbon": {
                    "total": {"baseline": None, "efficient": None},
                    "competed": {"baseline": None, "efficient": None}}},
            "lifetime": {"baseline": None, "measure": None}}
        self.master_savings = {}
        self.mseg_out_break = copy.deepcopy(out_break_in)

    def merge_measures(self):
        """ Merge a list of input measures into a single measure that combines
        all measure attributes and accounts for any overlaps in the baseline
        market microsegments of the merged measures """

        # Loop through each measure and add its attributes to the merged
        # measure definition
        for ind, m in enumerate(self.measures_to_package):
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
            self.fuel_type["primary"].extend(
                list(set(m.fuel_type["primary"]) -
                     set(self.fuel_type["primary"])))
            # Add measure end uses
            self.end_use["primary"].extend(
                list(set(m.end_use["primary"]) -
                     set(self.end_use["primary"])))

            # Generate a dictionary with information about all the
            # microsegments that contribute to the packaged measure's
            # master microsegment
            for k in m.mseg_adjust.keys():
                # Case where we are adding the first of the measures
                # that contribute to the package
                if ind == 0:
                    self.mseg_adjust[k] = m.mseg_adjust[k]
                # Case where we are adding subsequent measures that
                # contribute to the package
                else:
                    # Add measure's contributing microsegments
                    if k == "contributing mseg keys and values":
                        for cm in m.mseg_adjust[k].keys():
                            # Account for overlaps between the current
                            # contributing microsegment and existing
                            # contributing microsegments for the package
                            if cm in self.mseg_adjust[k].keys():
                                # Add in measure captured stock
                                self.mseg_adjust[k][cm]["stock"]["measure"] \
                                    += m.mseg_adjust[k][cm]["stock"]["measure"]
                                # Add in measure energy/carbon savings
                                for kt in ["energy", "carbon"]:
                                    self.mseg_adjust[k][cm][kt]["efficient"] \
                                        -= (
                                        m.mseg_adjust[k][cm][kt]["baseline"] -
                                        m.mseg_adjust[k][cm][kt]["efficient"])
                                # Add in measure stock, energy, and carbon cost
                                # savings
                                for kt in ["stock", "energy", "carbon"]:
                                    self.mseg_adjust[k][cm]["cost"][kt][
                                        "efficient"] -= (
                                            m.mseg_adjust[k][cm]["cost"][kt][
                                                "baseline"] -
                                            m.mseg_adjust[k][cm]["cost"][kt][
                                                "efficient"])
                            # If there is no overlap between the current
                            # contributing microsegment and existing
                            # contributing microsegments for the package, add
                            # in the current microsegment as is
                            else:
                                self.mseg_adjust[k][cm] = m.mseg_adjust[k][cm]

                    # Add measure's contributing microsegment consumer choice
                    # parameters
                    elif k in ["competed choice parameters",
                               "secondary mseg adjustments",
                               "supply-demand adjustment"]:
                        self.mseg_adjust[k].update(m.mseg_adjust[k])

            # Generate a dictionary including information about how
            # much of the packaged measure's baseline energy use is attributed
            # to each of the output climate zones, building types, and end uses
            # it applies to (normalized by the measure's total baseline
            # energy use below to yield output partitioning fractions)
            self.mseg_out_break = self.out_break_merge(
                self.mseg_out_break, m.mseg_out_break, m.master_mseg[
                    'energy']['total']['baseline'])

        # Generate a packaged master microsegment based on the contributing
        # microsegment information defined above

        # Determine contributing microsegment key chain count for use in
        # calculating an average baseline and measure lifetime below
        key_chain_ct_package = len(self.mseg_adjust[
            "contributing mseg keys and values"].keys())

        # Loop through all contributing microsegments for the packaged
        # measure and add to the packaged master microsegment
        for k in (self.mseg_adjust[
                "contributing mseg keys and values"].keys()):
            self.master_mseg = self.add_keyvals(
                self.master_mseg,
                self.mseg_adjust["contributing mseg keys and values"][k])

        # Reduce summed lifetimes across all microsegments that contribute
        # to the packaged master microsegment by the number of
        # microsegments that contributed to the sums, to arrive at an
        # average baseline/measure lifetime for the packaged measure
        for yr in self.master_mseg["lifetime"]["baseline"].keys():
            self.master_mseg["lifetime"]["baseline"][yr] = \
                self.master_mseg["lifetime"]["baseline"][yr] / \
                key_chain_ct_package
        self.master_mseg["lifetime"]["measure"] = self.master_mseg[
            "lifetime"]["measure"] / key_chain_ct_package

        # Normalize baseline energy use values for each category in the
        # packaged measure's output breakout dictionary by the total
        # baseline energy use for the packaged measure across all its
        # contributing measures; this yields partitioning fractions that
        # will eventually be used to breakout the packaged measure's
        # energy and carbon markets/savings by climate zone, building
        # type, and end use
        self.mseg_out_break = self.out_break_norm(
            self.mseg_out_break, self.master_mseg[
                'energy']['total']['baseline'])

    def out_break_merge(self, init_dict, update_dict, update_multiplier):
        """ Merge the output breakout dictionary for a measure that
        contributes to a packaged measure into the packaged measure's
        existing output breakout dictionary """

        for (k, i), (k2, i2) in zip(sorted(init_dict.items()),
                                    sorted(update_dict.items())):
            if isinstance(i, dict) and len(i.keys()) > 0:
                self.out_break_merge(i, i2, update_multiplier)
            else:
                # If this is the first time the packaged measure's output
                # breakout dictionary is being updated, replace appropriate
                # terminal leaf node value with terminal leaf node values
                # of the current contributing measure
                if len(update_dict[k2].keys()) > 0 and \
                   len(init_dict[k].keys()) == 0:
                    for yr in update_dict[k2].keys():
                        init_dict[k][yr] = \
                            update_dict[k2][yr] * update_multiplier[yr]
                # If the packaged measure's output breakout dictionary has
                # already been updated for a previous contributing measure,
                # add the appropriate terminal leaf node values of the current
                # contributing measure to the dictionary's existing terminal
                # leaf node values
                elif len(update_dict[k2].keys()) > 0 and \
                        len(init_dict[k].keys()) > 0:
                    for yr in update_dict[k2].keys():
                        init_dict[k][yr] += \
                            update_dict[k2][yr] * update_multiplier[yr]

        # Return the updated output breakout dict for the packaged measure
        return init_dict


def custom_formatwarning(msg, *a):
    """ Given a warning object, return only the warning message """
    return str(msg) + '\n'


def main():

    # Custom format all warning messages (ignore everything but message itself)
    warnings.formatwarning = custom_formatwarning

    # Import measures/microsegments files
    with open(measures_file, 'r') as mjs:
        measures_input = json.load(mjs)

    with open(microsegments_file, 'r') as msjs:
        microsegments_input = json.load(msjs)

    with open(mseg_base_costperflife_info, 'r') as bjs:
        base_costperflife_info_input = json.load(bjs)

    with open(measure_packages_file, 'r') as mpk:
        measure_packages = json.load(mpk)

    # Create measures objects list from input measures JSON
    measures_objlist = []

    # Loop through measures in JSON to initialize measure objects,
    # and run methods on these objects
    for mi in measures_input:
        measures_objlist.append(Measure(**mi))

    # Remove all measure objects that are not specified as "active" for
    # the current analysis run
    measures_objlist_fin = [x for x in measures_objlist if x.active == 1]

    # Instantiate an Engine object with input measures as attribute
    a_run = Engine(measures_objlist_fin)
    # Find master microsegment information for each active measure
    a_run.initialize_active(microsegments_input, base_costperflife_info_input,
                            adopt_scheme, rate, adjust_savings,
                            com_timeprefs, measure_packages, out_break_in)
    # Compete active measures if user has specified this option
    if adjust_savings is True:
        a_run.adjust_savings(com_timeprefs, 'Competing Measures')

    # Write selected outputs to a summary CSV file for post-processing
    a_run.write_outputs(json_output_file)

if __name__ == '__main__':
    import time
    start_time = time.time()
    main()
    print("--- Runtime: %s seconds ---" % round((time.time() - start_time), 2))
