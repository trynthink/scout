#!/usr/bin/env python3
import json
import csv
import itertools
import numpy
import copy
import re

# Define measures/microsegments files
measures_file = "measures_test.json"
microsegments_file = "microsegments_out.json"
mseg_base_costperflife_info = "base_costperflife.json"

# Define and import site-source conversions and CO2 emissions data
cost_sitesource_co2 = "Cost_S-S_CO2.txt"
cost_ss_co2 = numpy.genfromtxt(cost_sitesource_co2,
                               names=True, delimiter='\t',
                               dtype=None)

# Set fuel type site-source conversion factors dict
ss_conv = {"electricity (grid)": cost_ss_co2[7],
           "natural gas": cost_ss_co2[8],
           "distillate": cost_ss_co2[9], "other fuel": cost_ss_co2[9]}

# Set fuel type carbon intensity dict
carb_int = {"electricity (grid)": cost_ss_co2[10],
            "natural gas": cost_ss_co2[11],
            "distillate": cost_ss_co2[12], "other fuel": cost_ss_co2[12]}

# Set energy costs dict
ecosts = {"residential": {"electricity (grid)": cost_ss_co2[0],
                          "natural gas": cost_ss_co2[1],
                          "distillate": cost_ss_co2[2],
                          "other fuel": cost_ss_co2[2]},
          "commercial": {"electricity (grid)": cost_ss_co2[3],
                         "natural gas": cost_ss_co2[4],
                         "distillate": cost_ss_co2[5],
                         "other fuel": cost_ss_co2[5]}}
# Set carbon costs dict
ccosts = cost_ss_co2[6]

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

# User-specified inputs (placeholders for now, eventually draw from GUI?)
adopt_scheme = 'Technical potential'
compete_measures = True

# Define a summary CSV file. For now, yield separate output files for a
# competed and non-competed case to help organize test plotting efforts
if compete_measures is True:
    csv_output_file = "output_summary_competed.csv"
else:
    csv_output_file = "output_summary_noncompeted.csv"

# Set default number of input samples for Monte Carlo runs
nsamples = 50

# Define end use cases where relative performance calculation should be
# inverted (i.e., a lower air change rate is an improvement)
inverted_relperf_list = ["ACH50", "CFM/sf", "kWh/yr", "kWh/day", "SHGC",
                         "HP/CFM"]


# Define class for measure objects
class Measure(object):

    def __init__(self, **kwargs):
        # Initialize master microsegment and savings attributes
        self.master_mseg = None
        self.master_savings = None

        # Initialize other mseg-related attributes
        self.total_energy_norm = {}  # Energy/stock (whole mseg)
        self.compete_energy_norm = {}  # Energy/stock (competed mseg)
        self.efficient_energy_norm = {}  # Energy/stock (efficient)
        self.total_carb_norm = {}  # Carbon/stock (whole mseg)
        self.compete_carb_norm = {}  # Carbon/stock (competed mseg)
        self.efficient_carb_norm = {}  # Carbon/stock (efficient)

        # Initialize attributes from JSON
        for key, value in kwargs.items():
            setattr(self, key, value)

    def mseg_find_partition(self, mseg_in, base_costperflife_in, adopt_scheme):
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
        # to the current measure's master microsegment, the consumer choice
        # information associated with these contributing microsegments, and
        # information needed to adjust the microsegments' values in
        # supply-side measure cases where overlapping demand-side measures
        # are also included in the analysis. Together, this information will be
        # used in the 'compete_measures' function below to ensure there is no
        # double-counting of energy/carbon impacts across multiple competing
        # measures
        mseg_compete = {
            "competed mseg keys and values": {},
            "competed choice parameters": {},
            "demand-side adjustment": {
                "savings": {},
                "total": {}},
            "already competed": False}

        # Initialize a counter of valid key chains
        key_chain_ct = 0

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
            self.bldg_type not in \
            ["single family home", "multi family home", "mobile home"] and \
                self.end_use["secondary"] is None:
                    # Set secondary lighting microsegment flag to True
                    lighting_secondary = True
                    # Set secondary energy efficiency value to "Missing"
                    # (used below as a flag)
                    self.energy_efficiency["secondary"] = \
                        "Missing (secondary lighting)"
                    # Set secondary energy efficiency units to "relative
                    # savings"
                    self.energy_efficiency_units["secondary"] = \
                        "relative savings"
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

            # Initialize performance/cost/lifetime and units if:
            # a) For loop through all measure mseg key chains is in first
            # iteration, b) A switch has been made from updating "primary"
            # microsegment info. to updating "secondary" microsegment info.
            # (relevant to cost/lifetime units only), or c) Any of
            # performance/cost/lifetime/units is a dict which must be parsed
            # further to reach the final value. * Note: cost/lifetime
            # information is not updated for "secondary" microsegments,
            # which do not affect these variables; lifetime units are assumed
            # to be years
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
            else:
                if mskeys == ms_iterable[0] or isinstance(
                        self.installed_cost, dict):
                        cost_meas = self.installed_cost
                if mskeys == ms_iterable[0] or isinstance(
                        self.cost_units, dict):
                        cost_units = self.cost_units
                if mskeys == ms_iterable[0] or isinstance(
                        self.product_lifetime, dict):
                        life_meas = self.product_lifetime

            # Set appropriate site-source conversion factor, energy cost, and
            # CO2 intensity for given key chain
            if mskeys[3] in ss_conv.keys():
                site_source_conv = ss_conv[mskeys[3]]
                intensity_carb = carb_int[mskeys[3]]

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
            new_bldg_frac = {}

            # Initialize a dict for relative performance (broken out by year in
            # modeling time horizon)
            rel_perf = {}

            # Loop recursively through the above dicts, moving down key chain
            for i in range(0, len(mskeys)):
                # Check for key in dict level
                if mskeys[i] in base_costperflife.keys() or mskeys[i] in \
                   ["primary", "secondary"]:

                    # Skip over "primary" or "secondary" key in updating
                    # cost and lifetime information (not relevant)
                    if mskeys[i] not in ["primary", "secondary"]:
                        # Restrict base cost/performance/lifetime dict to key
                        # chain info.
                        base_costperflife = base_costperflife[mskeys[i]]

                        # Restrict stock/energy dict to key chain info.
                        mseg = mseg[mskeys[i]]

                        # Restrict sq.ft. dict to key chain info.
                        if i < 3:  # Note: sq.ft. broken out 2 levels
                            mseg_sqft_stock = mseg_sqft_stock[mskeys[i]]

                        # Restrict any measure cost/performance/lifetime info.
                        # that is a dict type to key chain info.
                        if isinstance(cost_meas, dict) and mskeys[i] in \
                           cost_meas.keys():
                            cost_meas = cost_meas[mskeys[i]]
                        if isinstance(cost_units, dict) and mskeys[i] in \
                           cost_units.keys():
                            cost_units = cost_units[mskeys[i]]
                        if isinstance(life_meas, dict) and mskeys[i] in \
                           life_meas.keys():
                            life_meas = life_meas[mskeys[i]]

                    if isinstance(perf_meas, dict) and mskeys[i] in \
                       perf_meas.keys():
                            perf_meas = perf_meas[mskeys[i]]
                    if isinstance(perf_units, dict) and mskeys[i] in \
                       perf_units.keys():
                            perf_units = perf_units[mskeys[i]]

                    # If updating a supply-side measure microsegment, record
                    # the total amount of demand-side energy that is associated
                    # with this microsegment. For example, given a supply-side
                    # measure microsegment key chain of ['AIA_CZ1',
                    # 'single family home', 'electricity (grid)', 'cooling',
                    # 'supply', 'ASHP'], the associated total demand-side
                    # energy is that attributed to the key chain
                    # ['AIA_CZ1', 'single family home',
                    # 'electricity (grid)', 'cooling']. This information will
                    # be used in the 'compete_measures' function below to
                    # adjust supply-side measure microsegments by the fraction
                    # of total associated demand-side energy that is being
                    # saved by demand-side measures.
                    if mskeys[i] == "supply" and mskeys[i + 1] in mseg.keys():
                        # Find the total demand-side energy by summing together
                        # the energy for all microsegments under the current
                        # 'supply' level of the key chain (e.g. could be
                        # 'ASHP', 'GSHP', 'boiler', etc.). Note that for a
                        # given climate zone, building type, and fuel type,
                        # heating/cooling supply and demand energy should be
                        # equal.
                        for ind, ks in enumerate(mseg.keys()):
                            if ind == 0:
                                adj_vals = copy.deepcopy(mseg[ks]["energy"])
                            else:
                                adj_vals = self.add_keyvals(
                                    adj_vals, mseg[ks]["energy"])
                        # Adjust the resultant total demand-side energy values
                        # by appropriate site-source conversion factor and
                        # record as part of the 'mseg_compete' measure
                        # attribute
                        mseg_compete["demand-side adjustment"]["total"][
                            str(mskeys)] = {key: val * site_source_conv[key]
                                            for key, val in adj_vals.items()}
                        # Set demand-side energy savings values to zero in
                        # 'mseg_compete' for now (updated as necessary in the
                        # 'compete_measures' function below)
                        mseg_compete["demand-side adjustment"]["savings"][
                            str(mskeys)] = dict.fromkeys(adj_vals.keys(), 0)

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

                # If the measure performance/cost variable is list with
                # distribution information, sample values from distribution
                if isinstance(perf_meas, list) and isinstance(perf_meas[0],
                                                              str):
                    perf_meas = self.rand_list_gen(perf_meas, nsamples)
                if isinstance(cost_meas, list) and isinstance(cost_meas[0],
                                                              str):
                    cost_meas = self.rand_list_gen(cost_meas, nsamples)
                if isinstance(life_meas, list) and isinstance(life_meas[0],
                                                              str):
                    life_meas = self.rand_list_gen(life_meas, nsamples)

                # Determine relative measure performance after checking for
                # consistent baseline/measure performance and cost units;
                # make an exception for cases where performance is specified
                # in 'relative savings' units (no explicit check
                # of baseline units needed in this case)
                if perf_units == 'relative savings' or \
                    (base_costperflife["performance"]["units"] == perf_units
                     and base_costperflife["installed cost"]["units"] ==
                     cost_units):

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
                    if perf_units == "relative savings":
                        # In a commercial lighting case where the relative
                        # savings impact of the lighting change on a secondary
                        # end use (heating/cooling) has not been user-
                        # specified, draw from the "lighting_secondary"
                        # variable to determine relative performance for this
                        # secondary microsegment; in all other cases where
                        # relative savings are directly user-specified in the
                        # measure definition, calculate relative performance
                        # based on the relative savings value
                        if perf_meas == "Missing (secondary lighting)":
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
                            for yr in perf_base.keys():
                                rel_perf[yr] = 1 - perf_meas
                    elif perf_units not in inverted_relperf_list:
                        if isinstance(perf_meas, list):  # Perf. distrib. case
                            for yr in perf_base.keys():
                                rel_perf[yr] = [(x ** -1 * perf_base[yr])
                                                for x in perf_meas]
                        else:
                            for yr in perf_base.keys():
                                rel_perf[yr] = (perf_base[yr] / perf_meas)
                    else:
                        if isinstance(perf_meas, list):  # Perf. distrib. case
                            for yr in perf_base.keys():
                                rel_perf[yr] = [
                                    (x / perf_base) for x in perf_meas]
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

                # Reduce energy costs and stock turnover info. to appropriate
                # building type and - for energy costs - fuel, before
                # entering into "partition_microsegment"
                if mskeys[2] in ["single family home", "mobile home",
                                 "multi family home"]:
                    # Update energy cost information
                    cost_energy = ecosts["residential"][mskeys[3]]
                    # Update new buildings fraction information
                    for yr in mseg["energy"].keys():
                        new_bldg_frac[yr] = mseg_sqft_stock["new homes"][yr] / \
                            mseg_sqft_stock["total homes"][yr]
                    # Update technology choice parameters needed to choose
                    # between multiple efficient technology options that
                    # access this baseline microsegment. For the residential
                    # sector, these parameters are found in the baseline
                    # technology cost, performance, and lifetime JSON
                    choice_params = base_costperflife["consumer choice"][
                        "competed market share"]["parameters"]
                else:
                    # Update energy cost information
                    cost_energy = ecosts["commercial"][mskeys[3]]
                    # Update new buildings fraction information
                    for yr in mseg["energy"].keys():
                        new_bldg_frac[yr] = 0  # *** Placeholder ***
                    # Update technology choice parameters needed to choose
                    # between multiple efficient technology options that
                    # access this baseline microsegment. For the commercial
                    # sector, these parameters are specified at the
                    # beginning of run.py in com_timeprefs (* Note:
                    # com_timeprefs info. may eventually be integrated into the
                    # baseline technology cost, performance, and lifetime JSON
                    # as for residential)
                    if mskeys[4] in com_timeprefs["distributions"].keys():
                        choice_params = {"rate distribution": com_timeprefs[
                            "distributions"][mskeys[4]]}
                    # For uncovered end uses, default to choice parameters for
                    # the heating end use
                    else:
                        choice_params = {"rate distribution": com_timeprefs[
                            "distributions"]["heating"]}

                # Update bass diffusion parameters needed to determine the
                # fraction of the baseline microegment that will be captured
                # by efficient alternatives to the baseline technology
                # (* BLANK FOR NOW, WILL CHANGE IN FUTURE *)
                diffuse_params = base_costperflife["consumer choice"][
                    "competed market"]["parameters"]

                # Update total stock and energy information. Note that
                # secondary microsegments make no contribution to the stock
                # calculation, as they only affect energy/carbon and associated
                # costs.
                if mskeys[0] == 'secondary':
                    add_stock = dict.fromkeys(mseg["energy"].keys(), 0)
                elif mseg["stock"] == "NA":  # Use sq.ft. in absence of # units
                    sqft_subst = 1
                    add_stock = mseg_sqft_stock["square footage"]
                else:
                    add_stock = mseg["stock"]
                add_energy_site = mseg["energy"]  # Site energy information

                # Update total, competed, and efficient stock, energy, CO2
                # and baseline/measure cost info. based on adoption scheme
                [add_stock, add_energy, add_carb,
                 add_stock_total_meas, add_energy_total_eff, add_carb_total_eff,
                 add_stock_compete, add_energy_compete, add_carb_compete,
                 add_stock_compete_meas, add_energy_compete_eff,
                 add_carb_compete_eff,
                 add_stock_cost, add_energy_cost, add_carb_cost,
                 add_stock_cost_meas, add_energy_cost_eff, add_carb_cost_eff,
                 add_stock_cost_compete, add_energy_cost_compete,
                 add_carb_cost_compete,
                 add_stock_cost_compete_meas, add_energy_cost_compete_eff,
                 add_carb_cost_compete_eff] = \
                    self.partition_microsegment(add_stock, add_energy_site,
                                                rel_perf, cost_base,
                                                cost_meas, cost_energy,
                                                ccosts, site_source_conv,
                                                intensity_carb,
                                                new_bldg_frac, diffuse_params,
                                                adopt_scheme)

                # Combine stock/energy/carbon/cost/lifetime updating info. into
                # a dict
                add_dict = {
                    "stock": {
                        "total": {
                            "all": add_stock,
                            "measure": add_stock_total_meas},
                        "competed": {
                            "all": add_stock_compete,
                            "measure": add_stock_compete_meas}},
                    "energy": {
                        "total": {
                            "baseline": add_energy,
                            "efficient": add_energy_total_eff},
                        "competed": {
                            "baseline": add_energy_compete,
                            "efficient": add_energy_compete_eff}},
                    "carbon": {
                        "total": {
                            "baseline": add_carb,
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

                # Register contributing microsegment for later use
                # in determining savings overlaps for measures that apply
                # to this microsegment
                mseg_compete["competed mseg keys and values"][str(mskeys)] = \
                    add_dict

                # Register choice parameters associated with contributing
                # microsegment for later use in portioning out various
                # technology options across competed stock
                mseg_compete["competed choice parameters"][str(mskeys)] = \
                    choice_params

                # Add all updated info. to existing master mseg dict and
                # move to next iteration of the loop through key chains
                mseg_master = self.add_keyvals(mseg_master, add_dict)

        if key_chain_ct != 0:

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
            # valid key chains / (# czones * # bldg types)), where the
            # numerator refers to the number of full dict key chains that
            # contributed to the mseg stock, energy, and cost calcs, and the
            # denominator reflects the breakdown of square footage by climate
            # zone and building type. Note that cost information is based
            # on competed stock and must be divided in the same manner (see
            # reduce_sqft_stock function).
            if sqft_subst == 1:
                # Create a factor for reduction of msegs with sq.ft. stock
                reduce_factor = key_chain_ct / (len(ms_lists[0]) *
                                                len(ms_lists[1]))
                mseg_master = self.reduce_sqft(mseg_master, reduce_factor)
                mseg_compete["competed mseg keys and values"] = \
                    self.reduce_sqft(copy.deepcopy(
                        mseg_compete["competed mseg keys and values"]),
                    reduce_factor)
            else:
                reduce_factor = 1
        else:
                raise KeyError('No valid key chains discovered for lifetime \
                                and stock and cost division operations!')

        # Return the final master microsegment
        return [mseg_master, mseg_compete]

    def create_keychain(self, mseg_type, htcl_enduse_ct=0):
        """ Given input microsegment information, create a list of keys that
        represents associated branch on the microsegment tree """

        # Determine end use case, first ensuring end use is input as a list
        if isinstance(self.end_use[mseg_type], list) is False:
            self.end_use[mseg_type] = [self.end_use[mseg_type]]
        for eu in self.end_use[mseg_type]:
            if eu == "heating" or eu == "secondary heating" or eu == "cooling":
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
        ms_iterable = list(itertools.product(*ms_lists))

        # Add "primary" or "secondary" microsegment type
        # indicator to beginning of each key chain
        for i in range(0, len(ms_iterable)):
            ms_iterable[i] = (mseg_type,) + ms_iterable[i]

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

    def partition_microsegment(self, mseg_stock, mseg_energy_site,
                               rel_perf, cost_base, cost_meas, cost_energy,
                               cost_carb, site_source_conv, intensity_carb,
                               new_bldg_frac, diffuse_params, adopt_scheme):
        """ Partition microsegment to find "competed" stock and energy/carbon
        consumption as well as "efficient" energy consumption (representing
        consumption under the measure).  Also find the cost of the baseline
        and measure stock, energy, and carbon """

        # Initialize stock, energy, and carbon mseg partition dicts, where the
        # dict keys will be years in the modeling time horizon
        stock_total, energy_total, carb_total, stock_total_meas, energy_total_eff, \
            carb_total_eff, stock_compete, energy_compete, carb_compete, \
            stock_compete_meas, energy_compete_eff, carb_compete_eff, \
            stock_total_cost, energy_total_cost, carb_total_cost, \
            stock_total_cost_eff, energy_total_eff_cost, carb_total_eff_cost, \
            stock_compete_cost, energy_compete_cost, carb_compete_cost, \
            stock_compete_cost_eff, energy_compete_cost_eff, \
            carb_compete_cost_eff = ({} for n in range(24))

        # Loop through and update stock, energy, and carbon mseg partitions for
        # each year in the modeling time horizon
        for yr in mseg_stock.keys():

            # Calculate the fractions of new and existing buildings
            # in the stock for the given year
            new_frac = new_bldg_frac[yr]
            exist_frac = 1 - new_frac

            # Calculate the fractions of existing buildings that have
            # baseline (e.g., conventional) and efficient technologies
            # installed * PLACEHOLDER
            exist_base_frac = 1
            exist_eff_frac = 1 - exist_base_frac

            # Calculate the fractions of baseline and efficient technologies
            # in existing buildings that are up for replacement or survive
            # * PLACEHOLDER
            exist_base_replace_frac = 1
            exist_eff_replace_frac = 1
            exist_base_survive_frac = 1 - exist_base_replace_frac
            exist_eff_survive_frac = 1 - exist_eff_replace_frac

            # For the adjusted adoption potential case, calculate the
            # fractions of "competed" (new/replacement) technologies
            # that remain with the baseline technology or change to the
            # efficient alternative technology; otherwise, for all other
            # scenarios, set both fractions to 1
            if adopt_scheme == "Adjusted adoption potential":
                # PLACEHOLDER
                diffuse_base_frac = 1
                diffuse_eff_frac = 1 - diffuse_base_frac
            else:
                diffuse_base_frac = 0
                diffuse_eff_frac = 1

            # Construct all possible mseg partitions from the above fractions

            # New stock/energy, baseline and efficient partitions
            new_base = new_frac * diffuse_base_frac
            new_eff = new_frac * diffuse_eff_frac

            # Replacement stock/energy, baseline, and efficient partitions
            replace_b2b = exist_frac * exist_base_frac * \
                exist_base_replace_frac * diffuse_base_frac
            replace_b2e = exist_frac * exist_base_frac * \
                exist_base_replace_frac * diffuse_eff_frac
            replace_e2e = exist_frac * exist_eff_frac * \
                exist_eff_replace_frac

            # Surviving stock/energy, baseline and efficient partitions
            survive_base = exist_frac * exist_base_frac * \
                exist_base_survive_frac
            survive_eff = exist_frac * exist_eff_frac * \
                exist_eff_survive_frac

            # Wrap the above partitions up into total and competed
            # stock/energy partitions for given technology adoption scenario

            # Check if measure only applies to new or existing buildings
            if type(self.structure_type) != list:
                # Measure only applies to new buildings
                if self.structure_type == "new":
                    # Calculate total and competed stock fractions
                    total_frac = new_base + new_eff
                    if adopt_scheme == "Technical potential":
                        compete_frac = total_frac
                    else:
                        compete_frac = total_frac - new_base
                # Measure only applies to existing buildings
                else:
                    # Calculate total and competed stock fractions
                    total_frac = replace_b2b + replace_b2e + \
                        replace_e2e
                    if adopt_scheme == "Technical potential":
                        compete_frac = total_frac
                    else:
                        compete_frac = total_frac - replace_b2b
            # Otherwise, measure applies to all buildings
            else:
                # Calculate total and competed stock fractions
                total_frac = 1
                if adopt_scheme == "Technical potential":
                    compete_frac = total_frac
                else:
                    compete_frac = total_frac - new_base - replace_b2b

            # Apply total and competed partition fractions to input stock
            # and energy data to arrive at final partitioned mseg outputs

            # Update total stock, energy, and carbon
            stock_total[yr] = mseg_stock[yr] * total_frac
            energy_total[yr] = mseg_energy_site[yr] * total_frac * \
                site_source_conv[yr]
            carb_total[yr] = energy_total[yr] * intensity_carb[yr]

            # Update competed stock, energy, and carbon
            stock_compete[yr] = mseg_stock[yr] * compete_frac
            energy_compete[yr] = mseg_energy_site[yr] * compete_frac * \
                site_source_conv[yr]
            carb_compete[yr] = energy_compete[yr] * intensity_carb[yr]

            # Update the number of total and competed stock units captured by
            # the measure as initially being equal to the total and competed
            # baseline stock (e.g., all units are assumed to be captured by the
            # measure). * Note: captured competed stock numbers are used in
            # the cost_metric_update function below to normalize measure cost
            # metrics to a per unit basis.  The captured stock will be less
            # than the competed stock in cases where the measure captures less
            # than 100% of the competed market share (determined in the
            # compete_measures function below).
            stock_total_meas[yr] = stock_total[yr]
            stock_compete_meas[yr] = stock_compete[yr]

            # Update total-efficient and competed-efficient energy and
            # carbon, where "efficient" signifies the portion of total and
            # competed energy/carbon remaining after measure implementation
            # plus non-competed energy/carbon. * Note: Efficient energy and
            # carbon is dependent upon whether the measure is on the market
            # for the given year (if not, use total-baseline energy and carbon)
            if (self.market_entry_year is None or int(yr) >= self.market_entry_year) \
               and (self.market_exit_year is None or
                    int(yr) < self.market_exit_year):
                energy_compete_eff[yr] = energy_compete[yr] * rel_perf[yr]
                energy_total_eff[yr] = energy_compete_eff[yr] + \
                    (energy_total[yr] - energy_compete[yr])
                carb_compete_eff[yr] = carb_compete[yr] * rel_perf[yr]
                carb_total_eff[yr] = carb_compete_eff[yr] + \
                    (carb_total[yr] - carb_compete[yr])
            else:
                energy_compete_eff[yr] = energy_compete[yr]
                energy_total_eff[yr] = energy_total[yr]
                carb_compete_eff[yr] = carb_compete[yr]
                carb_total_eff[yr] = carb_total[yr]

            # Update total and competed stock, energy, and carbon
            # costs. * Note: total-efficient and competed-efficient stock
            # cost for the measure are dependent upon whether that measure is
            # on the market for the given year (if not, use total-baseline
            # technology cost)

            # Update stock costs
            stock_total_cost[yr] = stock_total[yr] * cost_base[yr]
            stock_compete_cost[yr] = stock_compete[yr] * cost_base[yr]
            if (self.market_entry_year is None or
                int(yr) >= self.market_entry_year) and \
               (self.market_exit_year is None or
               int(yr) < self.market_exit_year):
                stock_compete_cost_eff[yr] = stock_compete[yr] * cost_meas
                stock_total_cost_eff[yr] = stock_compete_cost_eff[yr] + \
                    (stock_total_cost[yr] - stock_compete_cost[yr])
            else:
                stock_compete_cost_eff[yr] = stock_compete_cost[yr]
                stock_total_cost_eff[yr] = stock_total_cost[yr]
            # Update energy costs
            energy_total_cost[yr] = energy_total[yr] * cost_energy[yr]
            energy_total_eff_cost[yr] = energy_total_eff[yr] * cost_energy[yr]
            energy_compete_cost[yr] = energy_compete[yr] * cost_energy[yr]
            energy_compete_cost_eff[yr] = energy_compete_eff[yr] * \
                cost_energy[yr]
            # Update carbon costs
            carb_total_cost[yr] = carb_total[yr] * cost_carb[yr]
            carb_total_eff_cost[yr] = carb_total_eff[yr] * cost_carb[yr]
            carb_compete_cost[yr] = carb_compete[yr] * cost_carb[yr]
            carb_compete_cost_eff[yr] = carb_compete_eff[yr] * cost_carb[yr]

        # Return partitioned stock, energy, and cost mseg information
        return [
            stock_total, energy_total, carb_total, stock_total_meas,
            energy_total_eff, carb_total_eff, stock_compete, energy_compete,
            carb_compete, stock_compete_meas, energy_compete_eff,
            carb_compete_eff, stock_total_cost, energy_total_cost,
            carb_total_cost, stock_total_cost_eff, energy_total_eff_cost,
            carb_total_eff_cost, stock_compete_cost, energy_compete_cost,
            carb_compete_cost, stock_compete_cost_eff,
            energy_compete_cost_eff, carb_compete_cost_eff]

    def calc_metric_update(self, rate, compete_measures, com_timeprefs):
        """ Given information on a measure's master microsegment for
        each projection year and a discount rate, determine capital ("stock"),
        energy, and carbon cost savings; energy and carbon savings; and the
        internal rate of return, simple payback, cost of conserved energy, and
        cost of conserved carbon for the measure. """

        # Initialize capital cost, energy/energy cost savings, carbon/carbon
        # cost savings, and economic metrics as dicts with years as keys
        scostsave_tot, scostsave_add, esave_tot, esave_add, ecostsave_tot, \
            ecostsave_add, csave_tot, csave_add, ccostsave_tot, ccostsave_add, \
            stock_anpv, energy_anpv, carbon_anpv, irr_e, irr_ec, \
            payback_e, payback_ec, cce, cce_bens, ccc, ccc_bens = \
            ({} for d in range(21))

        # Calculate capital cost savings, energy/carbon savings, and
        # energy/carbon cost savings for each projection year
        for ind, yr in enumerate(
                sorted(self.master_mseg["stock"][
                    "total"]["measure"].keys())):

            # Set the number of competed stock units that are captured by the
            # measure for the given year; this number is used for normalizing
            # stock, energy and carbon cash flows to a per unit basis in the
            # "metric_update" function below
            num_units = self.master_mseg["stock"]["competed"]["measure"][yr]
            # Set the total (not unit) capital cost of the baseline
            # technology for comparison with measure capital cost
            scost_base = self.master_mseg[
                "cost"]["stock"]["total"]["baseline"][yr]

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
                scost_base - \
                self.master_mseg["cost"]["stock"]["total"]["efficient"][yr]
            ecostsave_tot[yr] = \
                self.master_mseg["cost"]["energy"]["total"]["baseline"][yr] - \
                self.master_mseg["cost"]["energy"]["total"]["efficient"][yr]
            ccostsave_tot[yr] = \
                self.master_mseg["cost"]["carbon"]["total"]["baseline"][yr] - \
                self.master_mseg["cost"]["carbon"]["total"]["efficient"][yr]

            # Calculate the added annual energy/carbon and stock/energy/carbon
            # cost savings for the measure vs. baseline.  Added savings reflect
            # the impact of only the measure adoptions simulated in the current
            # year of the modeling time horizon.
            esave_add[yr] = \
                self.master_mseg["energy"]["competed"]["baseline"][yr] - \
                self.master_mseg["energy"]["competed"]["efficient"][yr]
            csave_add[yr] = \
                self.master_mseg["carbon"]["competed"]["baseline"][yr] - \
                self.master_mseg["carbon"]["competed"]["efficient"][yr]
            scostsave_add[yr] = \
                self.master_mseg["cost"]["stock"]["competed"]["baseline"][yr] - \
                self.master_mseg["cost"]["stock"]["competed"]["efficient"][yr]
            ecostsave_add[yr] = \
                self.master_mseg["cost"]["energy"]["competed"]["baseline"][yr] - \
                self.master_mseg["cost"]["energy"]["competed"]["efficient"][yr]
            ccostsave_add[yr] = \
                self.master_mseg["cost"]["carbon"]["competed"]["baseline"][yr] - \
                self.master_mseg["cost"]["carbon"]["competed"]["efficient"][yr]

            # Only run remaining economic calculations if measure is being
            # competed, in which case these calculations will be necessary
            if compete_measures is True:

                # Set the lifetime of the baseline technology for comparison
                # with measure lifetime
                life_base = self.master_mseg["lifetime"]["baseline"][yr]
                if life_base == 0:  # Temporary - need wind./env. tech info.
                    life_base = 999
                # Set life of the measure
                life_meas = self.master_mseg["lifetime"]["measure"]
                # Define ratio of measure lifetime to baseline lifetime.  This
                # will be used below in determining capital cashflows over the
                # measure lifetime
                life_ratio = life_meas / life_base

                # Make copies of the above stock, energy, carbon, and cost
                # variables for possible further manipulation below before
                # as inputs to the "metric update" function
                scostsave_add_temp = scostsave_add[yr]
                esave_add_temp = esave_add[yr]
                ecostsave_add_temp = ecostsave_add[yr]
                csave_add_temp = csave_add[yr]
                ccostsave_add_temp = ccostsave_add[yr]
                life_meas_temp = life_meas
                life_ratio_temp = life_ratio

                # Calculate economic metrics using "metric_update" function

                # Check whether number of adopted units for a measure is zero,
                # in which case all economic outputs are set to 999
                if num_units == 0:
                    stock_anpv[yr], energy_anpv[yr], carbon_anpv[yr], irr_e[yr], \
                        irr_ec[yr], payback_e[yr], payback_ec[yr], cce[yr],\
                        cce_bens[yr], ccc[yr], ccc_bens[yr] = [
                            999 for n in range(11)]
                # Check whether any "metric_update" inputs that can be arrays
                # are in fact arrays
                elif any(type(x) == numpy.ndarray for x in
                         [scostsave_add_temp, esave_add_temp, life_meas_temp]):

                    # Ensure consistency in length of all "metric_update"
                    # inputs that can be arrays

                    # Determine the length that any array inputs to
                    # "metric_update" should consistently have
                    length_array = next(
                        (len(item) for item in [scostsave_add[yr],
                         esave_add[yr], life_ratio] if type(item) ==
                         numpy.ndarray), None)

                    # Ensure all array inputs to "metric_update" are of the
                    # above length

                    # Check incremental capital cost input
                    if type(scostsave_add_temp) != numpy.ndarray:
                        scostsave_add_temp = numpy.repeat(
                            scostsave_add_temp, length_array)
                    # Check energy/energy cost and carbon/cost savings inputs
                    if type(esave_add_temp) != numpy.ndarray:
                        esave_add_temp = numpy.repeat(
                            esave_add_temp, length_array)
                        ecostsave_add_temp = numpy.repeat(
                            ecostsave_add_temp, length_array)
                        csave_add_temp = numpy.repeat(
                            csave_add_temp, length_array)
                        ccostsave_add_temp = numpy.repeat(
                            ccostsave_add_temp, length_array)
                    # Check measure lifetime and lifetime ratio inputs
                    if type(life_meas_temp) != numpy.ndarray:
                        life_meas_temp = numpy.repeat(
                            life_meas_temp, length_array)
                        life_ratio_temp = numpy.repeat(
                            life_ratio_temp, length_array)

                    # Initialize numpy arrays for economic metric outputs

                    # First three arrays will be populated by dicts
                    # containing residential and commercial Annualized
                    # Net Present Values (ANPVs)
                    stock_anpv[yr], energy_anpv[yr], carbon_anpv[yr] = \
                        (numpy.repeat({}, len(scostsave_add_temp))
                            for v in range(3))
                    # Remaining eight arrays will be populated by floating
                    # point values
                    irr_e[yr], irr_ec[yr], payback_e[yr], payback_ec[yr], \
                        cce[yr], cce_bens[yr], ccc[yr], ccc_bens[yr] = \
                        (numpy.zeros(len(scostsave_add_temp))
                            for v in range(8))

                    # Run measure energy/carbon/cost savings and lifetime
                    # inputs through "metric_update" function to yield economic
                    # metric outputs. To handle inputs that are arrays, use a
                    # for loop to generate an output for each input array
                    # element one-by-one and append it to the appropriate
                    # output list.
                    for x in range(0, len(scostsave_add_temp)):
                        stock_anpv[yr][x], energy_anpv[yr][x],\
                            carbon_anpv[yr][x], irr_e[yr][x], irr_ec[yr][x],\
                            payback_e[yr][x], payback_ec[yr][x], cce[yr][x], \
                            cce_bens[yr][x], ccc[yr][x], ccc_bens[yr][x] = \
                            self.metric_update(
                                rate, scost_base, life_base,
                                scostsave_add_temp[x], esave_add_temp[x],
                                ecostsave_add_temp[x], csave_add_temp[x],
                                ccostsave_add_temp[x], int(life_ratio_temp[x]),
                                int(life_meas_temp[x]), num_units,
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
                            rate, scost_base, life_base, scostsave_add_temp,
                            esave_add_temp, ecostsave_add_temp, csave_add_temp,
                            ccostsave_add_temp, int(life_ratio_temp),
                            int(life_meas_temp), num_units, com_timeprefs)

        # Record final measure savings figures and economic metrics
        # in a dict that is returned by the function
        mseg_save = {"stock": {"cost savings (total)": scostsave_tot,
                               "cost savings (added)": scostsave_add},
                     "energy": {"savings (total)": esave_tot,
                                "savings (added)": esave_add,
                                "cost savings (total)": ecostsave_tot,
                                "cost savings (added)": ecostsave_add},
                     "carbon": {"savings (total)": csave_tot,
                                "savings (added)": csave_add,
                                "cost savings (total)": ccostsave_tot,
                                "cost savings (added)": ccostsave_add},
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

    def metric_update(self, rate, scost_base, life_base, scostsave_add, esave,
                      ecostsave, csave, ccostsave, life_ratio, life_meas,
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
        cashflows_s = numpy.array(scostsave_add)

        for life_yr in range(0, life_meas):
            # Check whether an avoided cost of the baseline technology should
            # be added for given year; if not, set this term to zero
            if life_yr in added_stockcost_gain_yrs:
                scost_life = scost_base
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
        if (type(self.bldg_type) == list and
            any([x in self.bldg_type for x in [
                "single family home", "multi family home", "mobile home"]])) or \
            (type(self.bldg_type) != list and self.bldg_type in [
             "single family home", "multi family home", "mobile home"]):
            # Set ANPV values under general discount rate
            res_anpv_s, res_anpv_e, res_anpv_c = [
                numpy.pmt(rate, life_meas, x) for x in [npv_s, npv_e, npv_c]]
        # If measure does not apply to residential sector, set residential
        # ANPVs to 'None'
        else:
            res_anpv_s, res_anpv_e, res_anpv_c = (None for n in range(3))

        # Populate ANPVs for commercial sector
        # Check whether measure applies to commercial sector
        if (type(self.bldg_type) == list and
            any([x not in self.bldg_type for x in [
                "single family home", "multi family home", "mobile home"]])) or \
            (type(self.bldg_type) != list and self.bldg_type not in [
             "single family home", "multi family home", "mobile home"]):
            com_anpv_s, com_anpv_e, com_anpv_c = ({} for n in range(3))
            # Set ANPV values under 7 discount rate categories
            for ind, tps in enumerate(com_timeprefs["rates"]):
                com_anpv_s["rate " + str(ind + 1)],\
                    com_anpv_e["rate " + str(ind + 1)],\
                    com_anpv_c["rate " + str(ind + 1)] = \
                    [numpy.pmt(tps, life_meas, numpy.npv(tps, x))
                     for x in [cashflows_s, cashflows_e, cashflows_c]]
        # If measure does not apply to commercial sector, set commercial
        # ANPVs to 'None'
        else:
            com_anpv_s, com_anpv_e, com_anpv_c = (None for n in range(3))

        # Set overall ANPV dicts based on above updating of residential
        # and commercial sector ANPV values
        anpv_s = {"residential": res_anpv_s, "commercial": com_anpv_s}
        anpv_e = {"residential": res_anpv_e, "commercial": com_anpv_e}
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
        try:
            irr_e = numpy.irr(cashflows_s + cashflows_e)
            payback_e = self.payback(cashflows_s + cashflows_e)
        except ValueError:
            pass

        # Calculate irr and simple payback for capital + energy + carbon cash
        # flows.  Check to ensure thar irr/payback can be calculated for the
        # given cash flows
        try:
            irr_ec = numpy.irr(cashflows_s + cashflows_e + cashflows_c)
            payback_ec = self.payback(cashflows_s + cashflows_e + cashflows_c)
        except ValueError:
            pass

        # Calculate cost of conserved energy w/ and w/o carbon cost savings
        # benefits.  Check to ensure energy savings NPV in the denominator is
        # not zero
        if any(esave_array) != 0:
            cce = (-npv_s / npv_esave)
            cce_bens = (-(npv_s + npv_c) / npv_esave)

        # Calculate cost of conserved carbon w/ and w/o energy cost savings
        # benefits.  Check to ensure carbon savings NPV in the denominator is
        # not zero.
        if any(csave_array) != 0:
            ccc = (-npv_s / npv_csave)
            ccc_bens = (-(npv_s + npv_e) / npv_csave)

        # Return all updated economic metrics
        return anpv_s, anpv_e, anpv_c, irr_e, irr_ec, payback_e, \
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
                          rate, compete_measures, com_timeprefs):
        """ Run initialization scheme on active measures only """
        for m in self.measures:
            # Find master microsegment and partitions, as well as measure
            # competition information
            m.master_mseg, m.mseg_compete = m.mseg_find_partition(
                mseg_in, base_costperflife_in, adopt_scheme)
            # Update savings outcomes and economic metrics
            # based on master microsegment
            m.master_savings = m.calc_metric_update(rate, compete_measures,
                                                    com_timeprefs)

    def compete_measures(self, com_timeprefs):
        """ Compete active measures to address overlapping microsegments and
        avoid double counting energy/carbon/cost savings """
        # Establish list of key chains for all microsegments that contribute to
        # measure master microsegments, across all active measures
        mseg_keys = []
        for x in self.measures:
            mseg_keys.extend(
                x.mseg_compete["competed mseg keys and values"].keys())
        # Establish list of unique key chains in mseg_keys list above
        msegs_init = numpy.unique(mseg_keys)
        # Reorder list of key chains such that the master microsegments for
        # measures that affect heating/cooling demand are updated first;s
        # updates to these microsegments will affect 'supply' microsegments
        # (e.g., reduced heating demand via highly insulating windows also
        # reduces the heating savings possible from more efficient HVAC
        # equipment)
        msegs = [x for x in msegs_init if 'demand' in x]
        msegs.extend([x for x in msegs_init if 'demand' not in x])

        # Run through all unique contributing microsegments in above list,
        # determining how each is apportioned across multiple efficiency
        # measures that are competing for it
        for msu in msegs:
            # Determine the subset of measures that compete for the given
            # microsegment
            measures_compete = [
                x for x in self.measures if msu in x.mseg_compete[
                    "competed mseg keys and values"].keys()]
            # Determine the subset of measures that need demand-side
            # adjustments for the given microsegment
            supply_demand_adj = [
                x for x in self.measures if msu in x.mseg_compete[
                    "demand-side adjustment"]["savings"].keys()]

            # For a demand-side microsegment update, find all supply-side
            # measures/microsegments that would be affected by changes
            # to the demand-side microsegment
            measures_secondary = {"measures": [], "keys": []}
            msu_split = None
            if 'demand' in msu:
                # Search for supply-side measures with contributing
                # microsegment key chains that match that of the demand-side
                # microsegment up until the 'demand' element of the chain
                # (e.g., ['AIA_CZ1', 'single family home',
                # 'electricity (grid)', 'cooling'])
                msu_split = re.search('(.*)(\,.*demand.*)', msu).group(1)
                for m in self.measures:
                    # Register the matching key chains
                    keys = [x for x in m.mseg_compete[
                            "competed mseg keys and values"].keys() if
                            msu_split in x and 'supply' in x]
                    # Record the matched key chains and associated supply-side
                    # measures in a 'measures_secondary' dict to be used
                    # further in the residential and commercial measure
                    # competition sub-routines below
                    if len(keys) > 0:
                        measures_secondary["measures"].append(m)
                        measures_secondary["keys"].append(keys)

            # If multiple measures are competing for the microsegment,
            # determine the market shares of the competing measures and adjust
            # measure master microsegments accordingly, using separate market
            # share modeling routines for residential and commercial sectors.
            # Also use these routines to adjust for any secondary effects a
            # demand-side measure microsegment has on a supply-side measure
            # microsegment (or microsegments)
            if (len(measures_compete) > 1 or len(supply_demand_adj) > 0 or
                len(measures_secondary["measures"]) > 0) and \
                any(x in msu for x in (
                    'single family home', 'multi family home', 'mobile home')):
                self.res_compete(measures_compete, measures_secondary, msu,
                                 supply_demand_adj)
            elif (len(measures_compete) > 1 or len(supply_demand_adj) > 0 or
                  len(measures_secondary["measures"]) > 0) and \
                all(x not in msu for x in (
                    'single family home', 'multi family home', 'mobile home')):
                self.com_compete(measures_compete, msu, measures_secondary,
                                 supply_demand_adj)

        # For each measure that has been competed against other measures and
        # had its master microsegment updated accordingly, also update the
        # savings outcomes and economic metrics for that measure
        for m in self.measures:
            if m.mseg_compete["already competed"] is True:
                m.master_savings = m.calc_metric_update(
                    rate, compete_measures, com_timeprefs)

    def res_compete(self, measures_compete, measures_secondary, mseg_key,
                    supply_demand_adj):
        """ Determine the shares of a given market microsegment that are
        captured by a series of residential efficiency measures that compete
        for this market microsegment; account for the secondary effects that
        any demand-side measures have on supply-side measures """
        # Initialize list of dicts that each store the annual market fractions
        # captured by competing measures; also initialize a dict that sums
        # market fractions by year across competing measures (used to normalize
        # the measure market fractions such that they all sum to 1)
        mkt_fracs = [{} for l in range(0, len(measures_compete))]
        mkt_fracs_tot = dict.fromkeys(
            measures_compete[0].master_mseg["stock"]["total"]["all"].keys(), 0)

        # Loop through competing measures and calculate market shares for each
        # based on their annualized capital and operating costs.
        if len(measures_compete) > 1:
            for ind, m in enumerate(measures_compete):
                # Register that this measure has been competed with others (for
                # use at the end of the 'compete_measures' function in
                # determining whether to update the measure's savings/cost
                # metric outputs)
                m.mseg_compete["already competed"] = True
                # Loop through all years in modeling time horizon
                for yr in m.master_savings[
                        "metrics"]["anpv"]["stock cost"].keys():
                    # Set measure capital and operating cost inputs. * Note:
                    # operating cost is set to just energy costs (for now), but
                    # could be expanded to include maintenance and carbon costs
                    cap_cost = m.master_savings["metrics"]["anpv"][
                        "stock cost"][yr]["residential"]
                    op_cost = m.master_savings["metrics"]["anpv"][
                        "energy cost"][yr]["residential"]
                    # Calculate measure market fraction using log-linear
                    # regression equation that takes capital/operating costs as
                    # inputs
                    mkt_fracs[ind][yr] = numpy.exp(cap_cost * m.mseg_compete[
                        "competed choice parameters"][str(mseg_key)]["b1"][yr]
                        + op_cost *
                        m.mseg_compete["competed choice parameters"][
                        str(mseg_key)]["b2"][yr])
                    # Add calculated market fraction to market fractions sum
                    mkt_fracs_tot[yr] += mkt_fracs[ind][yr]

        # Loop through competing measures to normalize their calculated market
        # shares to the total market share sum; use normalized market shares to
        # make adjustments to each measure's master microsegment values
        for ind, m in enumerate(measures_compete):
            # Establish the starting master microsegment and contributing
            # microsegment information necessary to adjust the master
            # microsegment to reflect the updated measure market fraction
            base, base_list_tot, base_list_comp, adj, adj_list_base, adj_list_eff = \
                self.compete_adjustment_dicts(m, mseg_key)
            # Calculate annual market share fraction for the measure and adjust
            # measure's master microsegment values accordingly
            for yr in m.master_savings["metrics"]["anpv"]["stock cost"].keys():
                # Normalize measure market share if more than one measure is
                # competing; otherwise, market share remains 1
                if len(measures_compete) > 1:
                    mkt_fracs[ind][yr] = mkt_fracs[ind][yr] / mkt_fracs_tot[yr]
                else:
                    mkt_fracs[ind][yr] = 1
                # Make the adjustment to the measure's master microsegment
                # based on its updated market share; if a supply-side measure,
                # also account for any secondary effects of demand-side
                # measures on the measure master microsegment
                self.compete_adjustment(
                    mkt_fracs, base, base_list_tot, base_list_comp, adj,
                    adj_list_base, adj_list_eff, ind, yr, mseg_key,
                    measures_secondary, m)

    def com_compete(self, measures_compete, measures_secondary, mseg_key,
                    com_timeprefs, supply_demand_adj):
        """ Determine market shares captured by competing commercial efficiency
        measures; account for the secondary effects that any demand-side
        measures have on supply-side measures """
        # Initialize list of dicts that each store the annual market fractions
        # captured by competing measures; also initialize a dict that records
        # the total annualized capital + operating costs for each measure
        # and discount rate level (used to choose which measure is adopted
        # under each discount rate level)
        mkt_fracs = [{} for l in range(0, len(measures_compete))]
        tot_cost = [{} for l in range(0, len(measures_compete))]

        # Loop through competing measures and calculate market shares for each
        # based on their annualized capital and operating costs
        if len(measures_compete) > 1:
            for ind, m in enumerate(measures_compete):
                # Register that this measure has been competed with others (for
                # use at the end of the 'compete_measures' function in
                # determining whether to update the measure's savings/cost
                # metric outputs)
                m.mseg_compete["already competed"] = True
                # Loop through all years in modeling time horizon
                for yr in m.master_savings["metrics"]["anpv"][
                        "stock cost"].keys():
                    # Set measure capital and operating cost inputs. * Note:
                    # operating cost is set to just energy costs (for now), but
                    # could be expanded to include maintenance and carbon costs
                    cap_cost = m.master_savings["metrics"]["anpv"][
                        "stock cost"][yr]["commercial"]
                    op_cost = m.master_savings["metrics"]["anpv"][
                        "energy cost"][yr]["commercial"]
                    # Sum capital and operating costs and add to the total cost
                    # dict entry for the given measure
                    tot_cost[ind][yr] = []
                    for dr in sorted(cap_cost.keys()):
                        tot_cost[ind][yr].append(cap_cost[dr] + op_cost[dr])

        # Loop through competing measures and use total annualized capital
        # + operating costs to determine the overall share of the market
        # that is captured by each measure; use market shares to make
        # adjustments to each measure's master microsegment values
        for ind, m in enumerate(measures_compete):
            # Establish the starting master microsegment and contributing
            # microsegment information necessary to adjust the master
            # microsegment to reflect the updated measure market fraction
            base, base_list_tot, base_list_comp, adj, adj_list_base, adj_list_eff = \
                self.compete_adjustment_dicts(m, mseg_key)
            # Calculate annual market share fraction for the measure and adjust
            # measure's master microsegment values accordingly
            for yr in m.master_savings["metrics"]["anpv"]["stock cost"].keys():
                # Update market share based on annualized measure cost if more
                # than one measure is competing; otherwise, market share
                # remains 1
                if len(measures_compete) > 1:
                    # Set the fractions of commericial adopters who fall into
                    # each discount rate category for this particular
                    # microsegment
                    mkt_dists = m.mseg_compete[
                        "competed choice parameters"][str(mseg_key)][
                        "rate distribution"][yr]
                    # For each discount rate category, find which measure has
                    # the lowest annualized cost and assign that measure the
                    # share of commercial market adopters defined for that
                    # category above
                    mkt_fracs[ind][yr] = []
                    for ind2, dr in enumerate(tot_cost[ind][yr]):
                        # If the measure has the lowest annualized cost, assign
                        # it the appropriate market share for the current
                        # discount rate category being looped through;
                        # otherwise, set its market fraction for that category
                        # to zero
                        if tot_cost[ind][yr][ind2] == \
                           min([tot_cost[x][yr][ind2] for x in range(
                                0, len(measures_compete))]):  # * Equals ? *
                            mkt_fracs[ind][yr].append(mkt_dists[ind2])
                        else:
                            mkt_fracs[ind][yr].append(0)
                    mkt_fracs[ind][yr] = sum(mkt_fracs[ind][yr])
                else:
                    mkt_fracs[ind][yr] = 1
                # Make the adjustment to the measure's master microsegment
                # based on its updated market share; if a supply-side measure,
                # also account for any secondary effects of demand-side
                # measures on the measure master microsegment
                self.compete_adjustment(
                    mkt_fracs, base, base_list_tot, base_list_comp, adj,
                    adj_list_base, adj_list_eff, ind, yr, mseg_key,
                    measures_secondary, m)

    def compete_adjustment_dicts(self, m, mseg_key):
        """ Establish a measure's starting master microsegment and the
        contributing microsegment information needed to adjust the
        master microsegment values following measure competition """
        # Organize relevant starting master microsegment values into a list
        base = m.master_mseg
        # Set total-efficient master microsegment values to be updated in the
        # compete_adjustment function below
        base_list_tot = [base["energy"]["total"]["efficient"],
                         base["carbon"]["total"]["efficient"],
                         base["cost"]["energy"]["total"]["efficient"],
                         base["cost"]["carbon"]["total"]["efficient"]]
        # Set competed-efficient master microsegment values to be updated in
        # the compete_adjustment function below
        base_list_comp = [base["energy"]["competed"]["efficient"],
                          base["carbon"]["competed"]["efficient"],
                          base["cost"]["energy"]["competed"]["efficient"],
                          base["cost"]["carbon"]["competed"]["efficient"]]
        # Set up lists that will be used to determine the energy, carbon,
        # and cost savings associated with the competed microsegment that
        # must be adjusted according to a measure's calculated market share
        adj = m.mseg_compete["competed mseg keys and values"][mseg_key]

        # Competed baseline energy, carbon, and cost for contributing
        # microsegment
        adj_list_base = [
            adj["energy"]["competed"]["baseline"],
            adj["carbon"]["competed"]["baseline"],
            adj["cost"]["energy"]["competed"]["baseline"],
            adj["cost"]["carbon"]["competed"]["baseline"]]
        # Competed energy, carbon, and cost for contributing microsegment under
        # full efficient measure adoption
        adj_list_eff = [
            adj["energy"]["competed"]["efficient"],
            adj["carbon"]["competed"]["efficient"],
            adj["cost"]["energy"]["competed"]["efficient"],
            adj["cost"]["carbon"]["competed"]["efficient"]]

        # Return baseline master microsegment and adjustment microsegments
        return base, base_list_tot, base_list_comp, adj, adj_list_base, \
            adj_list_eff

    def compete_adjustment(
        self, mkt_fracs, base, base_list_tot, base_list_comp, adj,
        adj_list_base, adj_list_eff, ind, yr, mseg_key, measures_secondary,
            measure):
        """ Adjust the measure's master microsegment values by applying
        its competed market share and demand-side adjustment (if applicable)
        to the measure's captured stock and energy, carbon, and associated cost
        savings that are attributed to the current competed microsegment """
        # Determine adjustment fraction needed to reflect any previously
        # captured demand-side measure savings; if not applicable, this
        # fraction is set to 1.
        if mseg_key in measure.mseg_compete[
           "demand-side adjustment"]["savings"].keys():
            # Find the fraction of the total applicable demand-side
            # energy that is saved by demand-side measures; adjust
            # supply-side savings by the fraction of energy that
            # has not already been saved by these demand-side
            # measures
            dem_adj_frac = 1 - (
                measure.mseg_compete["demand-side adjustment"][
                    "savings"][mseg_key][yr] /
                measure.mseg_compete["demand-side adjustment"][
                    "total"][mseg_key][yr])
        else:
            dem_adj_frac = 1

        # Scale down the competed stock captured by the measure by the updated
        # measure market share
        base["stock"]["competed"]["measure"][yr] = \
            base["stock"]["competed"]["measure"][yr] * \
            mkt_fracs[ind][yr]
        # Adjust the total stock captured by the measure to reflect the above
        # adjustment to the captured competed stock
        base["stock"]["total"]["measure"][yr] = \
            base["stock"]["total"]["measure"][yr] - \
            (base["stock"]["competed"]["all"][yr] -
             base["stock"]["competed"]["measure"][yr])

        # Adjust the total and competed efficient vs. baseline stock cost
        # difference for the contributing microsegment by the updated measure
        # market share; add the updated difference to the measure's starting
        # 'efficient' master microsegment values
        base["cost"]["stock"]["total"]["efficient"][yr] = \
            base["cost"]["stock"]["total"]["efficient"][yr] + (
                (adj["cost"]["stock"]["competed"]["baseline"][yr] -
                 adj["cost"]["stock"]["competed"]["efficient"][yr]) *
                (1 - mkt_fracs[ind][yr]))
        base["cost"]["stock"]["competed"]["efficient"][yr] = \
            base["cost"]["stock"]["competed"]["efficient"][yr] + (
                (adj["cost"]["stock"]["competed"]["baseline"][yr] -
                 adj["cost"]["stock"]["competed"]["efficient"][yr]) *
                (1 - mkt_fracs[ind][yr]))

        # Adjust the total and competed energy, carbon, and associated cost
        # savings for the contributing microsegment by the updated measure
        # market share and - if a supply-side measure - by any savings already
        # captured on the demand-side, to arrive at an uncaptured savings
        # value; add the uncaptured savings to the measure's starting
        # 'efficient' master microsegment values
        base["energy"]["total"]["efficient"][yr],\
            base["carbon"]["total"]["efficient"][yr], \
            base["cost"]["energy"]["total"]["efficient"][yr], \
            base["cost"]["carbon"]["total"]["efficient"][yr], = [
                x[yr] + ((y[yr] - z[yr]) * (
                    1 - (mkt_fracs[ind][yr] * dem_adj_frac))) for x, y, z in
                zip(base_list_tot, adj_list_base, adj_list_eff)]
        base["energy"]["competed"]["efficient"][yr],\
            base["carbon"]["competed"]["efficient"][yr], \
            base["cost"]["energy"]["competed"]["efficient"][yr], \
            base["cost"]["carbon"]["competed"]["efficient"][yr], = [
                x[yr] + ((y[yr] - z[yr]) * (
                    1 - (mkt_fracs[ind][yr] * dem_adj_frac))) for x, y, z in
                zip(base_list_comp, adj_list_base, adj_list_eff)]

        # If updating a demand-side measure that has secondary effects on
        # supply-side measures, register any captured demand-side savings for
        # later use in adjusting the supply-side measures' energy, carbon,
        # and associated cost savings
        if 'demand' in mseg_key and len(measures_secondary["measures"]) > 0:
            # For each of the affected supply-side measures, establish
            # the affected contributing microsegments and record the
            # demand-side savings adjustment that must be made for each
            for ind2, ms in enumerate(measures_secondary["measures"]):
                # Record the appropriate demand-side savings adjustment
                # for each of the supply-side measure's contributing
                # microsegments
                keys = measures_secondary["keys"][ind2]
                for k in keys:
                    dem_save = (adj_list_base[0][yr] - adj_list_eff[0][yr]) * \
                        mkt_fracs[ind][yr]
                    ms.mseg_compete["demand-side adjustment"][
                        "savings"][k][yr] += dem_save

    def write_outputs(self, csv_output_file):
        """ Write selected measure outputs to a summary CSV file """

        # Initialize a list to be populated with measure summary outputs
        measure_summary_list = []

        # Loop through all measures and append a dict of summary outputs to
        # the measure summary list above
        for m in self.measures:
            for yr in m.master_mseg["stock"]["total"]["all"].keys():
                # Create list of output variables
                summary_mat = [
                    m.master_mseg["energy"]["total"]["efficient"][yr],
                    m.master_savings["energy"]["savings (total)"][yr],
                    m.master_savings["energy"]["cost savings (total)"][yr],
                    m.master_mseg["carbon"]["total"]["efficient"][yr],
                    m.master_savings["carbon"]["savings (total)"][yr],
                    m.master_savings["carbon"]["cost savings (total)"][yr]]

                # Check if the current measure's efficent energy/carbon
                # markets, energy/carbon savings, and associated cost outputs
                # are arrays of values.  If so, find the average and 5th/95th
                # percentile values of each output array and report out.
                # Otherwise, report the point values for each output
                if type(m.master_mseg["energy"]["total"]["efficient"][yr]) == \
                   numpy.ndarray:
                    # Average values for outputs
                    energy_eff_avg, energy_save_avg, energy_costsave_avg, \
                        carb_eff_avg, carb_save_avg, carb_costsave_avg = \
                        [numpy.mean(x) for x in summary_mat]
                    # 5th percentile values for outputs
                    energy_eff_low, energy_save_low, energy_costsave_low, \
                        carb_eff_low, carb_save_low, carb_costsave_low = \
                        [numpy.percentile(x, 5) for x in summary_mat]
                    # 95th percentile values for outputs
                    energy_eff_high, energy_save_high, energy_costsave_high, \
                        carb_eff_high, carb_save_high, carb_costsave_high = \
                        [numpy.percentile(x, 95) for x in summary_mat]
                else:
                    energy_eff_avg, energy_save_avg, energy_costsave_avg, \
                        carb_eff_avg, carb_save_avg, carb_costsave_avg, \
                        energy_eff_low, energy_save_low, energy_costsave_low, \
                        carb_eff_low, carb_save_low, carb_costsave_low, \
                        energy_eff_high, energy_save_high, energy_costsave_high, \
                        carb_eff_high, carb_save_high, carb_costsave_high = \
                        [x for x in summary_mat] * 3

                # Define a dict of summary output keys and values for the
                # current measure
                measure_summary_dict_yr = {
                    "year": yr, "measure name": m.name,
                    "total energy": m.master_mseg[
                        "energy"]["total"]["baseline"][yr],
                    "competed energy": m.master_mseg[
                        "energy"]["competed"]["baseline"][yr],
                    "efficient energy": energy_eff_avg,
                    "efficient energy (low)": energy_eff_low,
                    "efficient energy (high)": energy_eff_high,
                    "energy savings": energy_save_avg,
                    "energy savings (low)": energy_save_low,
                    "energy savings (high)": energy_save_high,
                    "energy cost savings": energy_costsave_avg,
                    "energy cost savings (low)": energy_costsave_low,
                    "energy cost savings (high)": energy_costsave_high,
                    "total carbon": m.master_mseg[
                        "carbon"]["total"]["baseline"][yr],
                    "competed carbon": m.master_mseg[
                        "carbon"]["competed"]["baseline"][yr],
                    "efficient carbon": carb_eff_avg,
                    "efficient carbon (low)": carb_eff_low,
                    "efficient carbon (high)": carb_eff_high,
                    "carbon savings": carb_save_avg,
                    "carbon savings (low)": carb_save_low,
                    "carbon savings (high)": carb_save_high,
                    "carbon cost savings": carb_costsave_avg,
                    "carbon cost savings (low)": carb_costsave_low,
                    "carbon cost savings (high)": carb_costsave_high,
                }
                # Append the dict of summary outputs for the current measure to
                # the summary list of outputs across all active measures
                measure_summary_list.append(measure_summary_dict_yr)

        # Write the summary outputs list to a CSV
        with open(csv_output_file, 'w', newline="") as f:
            dict_writer = csv.DictWriter(
                f, fieldnames=measure_summary_list[0].keys())
            dict_writer.writeheader()
            dict_writer.writerows(measure_summary_list)


def main():

    # Import measures/microsegments files
    with open(measures_file, 'r') as mjs:
        measures_input = json.load(mjs)

    with open(microsegments_file, 'r') as msjs:
        microsegments_input = json.load(msjs)

    with open(mseg_base_costperflife_info, 'r') as bjs:
        base_costperflife_info_input = json.load(bjs)

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
                            adopt_scheme, rate, compete_measures,
                            com_timeprefs)
    # Compete active measures if user has specified this option
    if compete_measures is True:
        a_run.compete_measures(com_timeprefs)

    # Write selected outputs to a summary CSV file for post-processing
    a_run.write_outputs(csv_output_file)

if __name__ == '__main__':
    import time
    start_time = time.time()
    main()
    print("--- Runtime: %s seconds ---" % round((time.time() - start_time), 2))
