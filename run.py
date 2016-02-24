#!/usr/bin/env python3
import json
import csv
import itertools
import numpy
import copy
import re
from numpy.linalg import LinAlgError
from collections import OrderedDict

# Define measures/microsegments files
measures_file = "measures_test.json"
microsegments_file = "microsegments_out.json"
mseg_base_costperflife_info = "base_costperflife.json"
measure_packages_file = 'measure_packages_test.json'

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
adopt_scheme = 'Max adoption potential'
adjust_savings = True

# Define a summary CSV file. For now, yield separate output files for a
# competed and non-competed case and technical potential and non-technical
# potential case to help organize test plotting efforts
if adopt_scheme is 'Technical potential' and adjust_savings is True:
    csv_output_file = "output_summary_competed.csv"
elif adopt_scheme is 'Technical potential' and adjust_savings is False:
    csv_output_file = "output_summary_noncompeted.csv"
elif adopt_scheme is not'Technical potential' and adjust_savings is True:
    csv_output_file = "output_summary_competed_nontp.csv"
else:
    csv_output_file = "output_summary_noncompeted_nontp.csv"

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
        # heating/cooling measure cases where the microsegment overlaps with
        # other active measure microsegments across the supply-side and the
        # demand-side (e.g., an ASHP microsegment that overlaps with a windows
        # (conduction) microsegment). Together, this information will be used
        # in the 'adjust_savings' function below to ensure there is no double-
        # counting of energy/carbon impacts across multiple competing measures
        mseg_adjust = {
            "contributing mseg keys and values": {},
            "competed choice parameters": {},
            "supply-demand adjustment": {
                "savings": {},
                "total": {}},
            "savings updated": False}

        # If multiple runs are required to handle probability distributions on
        # measure inputs, set a number to seed each random draw of cost,
        # performance, and or lifetime with for consistency across all
        # microsegments that contribute to the measure's master microsegment
        if nsamples is not None:
            rnd_sd = numpy.random.randint(10000)

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
                # Set baseline and measure site-source conversions and
                # CO2 intensities, accounting for any fuel switching from
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
                   ["primary", "secondary", "new", "retrofit", None]:
                    # Skip over "primary" or "secondary" key in updating
                    # cost and lifetime information (not relevant)
                    if mskeys[i] not in [
                            "primary", "secondary", "new", "retrofit", None]:

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
                        # Adjust the resultant total overlapping energy values
                        # by appropriate site-source conversion factor and
                        # record as part of the 'mseg_adjust' measure
                        # attribute
                        mseg_adjust["supply-demand adjustment"]["total"][
                            str(mskeys)] = {key: val * site_source_conv_base[
                                key] for key, val in adj_vals.items()}
                        # Set overlapping energy savings values to zero in
                        # 'mseg_adjust' for now (updated as necessary in the
                        # 'adjust_savings' function below)
                        mseg_adjust["supply-demand adjustment"]["savings"][
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
                                        perf_meas = perf_meas_orig * (
                                            perf_base[str(perf_units[1])] /
                                            perf_base[yr])
                                    else:
                                        perf_meas = perf_meas_orig * (
                                            perf_base[yr] /
                                            perf_base[str(perf_units[1])])
                                    # Ensure that none of the adjusted relative
                                    # savings fractions exceed 1
                                    if type(perf_meas) == numpy.array and \
                                            any(perf_meas > 0):
                                        perf_meas[
                                            numpy.where(perf_meas > 1)] = 1
                                    elif type(perf_meas) != numpy.array and \
                                            perf_meas > 1:
                                        perf_meas = 1
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
                    if mskeys[4] in com_timeprefs["distributions"].keys():
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
                # structures or retrofit structures)
                if mskeys[-1] == "new":
                    new_retrofit_frac = {key: val for key, val in
                                         new_bldg_frac["total"].items()}
                else:
                    new_retrofit_frac = {key: (1 - val) for key, val in
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
                    add_stock = {
                        key: val * new_retrofit_frac[key] for key, val in
                        mseg_sqft_stock["square footage"].items()}
                else:
                    add_stock = {
                        key: val * new_retrofit_frac[key] for key, val in
                        mseg["stock"].items()}
                # Total energy use (primary)
                add_energy = {
                    key: val * site_source_conv_base[key] *
                    new_retrofit_frac[key]
                    for key, val in mseg["energy"].items()}
                # Total carbon emissions
                add_carb = {key: val * intensity_carb_base[key]
                            for key, val in add_energy.items()}

                # Update total, competed, and efficient stock, energy, carbon
                # and baseline/measure cost info. based on adoption scheme
                [add_stock_total_meas, add_energy_total_eff,
                 add_carb_total_eff, add_stock_compete, add_energy_compete,
                 add_carb_compete, add_stock_compete_meas,
                 add_energy_compete_eff, add_carb_compete_eff,
                 add_stock_cost, add_energy_cost, add_carb_cost,
                 add_stock_cost_meas, add_energy_cost_eff, add_carb_cost_eff,
                 add_stock_cost_compete, add_energy_cost_compete,
                 add_carb_cost_compete, add_stock_cost_compete_meas,
                 add_energy_cost_compete_eff, add_carb_cost_compete_eff] = \
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
                                                life_meas, mskeys)

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
                mseg_adjust["contributing mseg keys and values"][str(mskeys)] = \
                    add_dict

                # Register choice parameters associated with contributing
                # microsegment for later use in apportioning out various
                # technology options across competed stock
                mseg_adjust["competed choice parameters"][str(mskeys)] = \
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
            # valid key chains / (# czones * # bldg types * # structure
            # types)), where the numerator refers to the number of full dict
            # key chains that contributed to the mseg stock, energy, and cost
            # calcs, and the denominator reflects the breakdown of square
            # footage by climate zone, building type, and the structure type
            # that the measure applies to.
            if sqft_subst == 1:
                # Determine number of structure types the measure applies to
                # (could be just new, just retrofit, or both)
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
        else:
                raise KeyError('No valid key chains discovered for lifetime \
                                and stock and cost division operations!')

        # Return the final master microsegment
        return [mseg_master, mseg_adjust]

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
        # of each key chain and the applicable structure type (new or retrofit)
        # to the end of each key chain

        # Case where measure applies to both new and retrofit structures
        # (final ms_iterable list length is double that of ms_iterable_init)
        if len(self.structure_type) > 1:
            ms_iterable1, ms_iterable2 = ([] for n in range(2))
            for i in range(0, len(ms_iterable_init)):
                ms_iterable1.append((mseg_type,) + ms_iterable_init[i] +
                                    (self.structure_type[0], ))
                ms_iterable2.append((mseg_type,) + ms_iterable_init[i] +
                                    (self.structure_type[1], ))
            ms_iterable = ms_iterable1 + ms_iterable2
        # Case where measure applies to only new or retrofit structures
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

    def partition_microsegment(self, stock_total, energy_total, carb_total,
                               rel_perf, cost_base, cost_meas,
                               cost_energy_base, cost_energy_meas, cost_carb,
                               site_source_conv_base, site_source_conv_meas,
                               intensity_carb_base, intensity_carb_meas,
                               new_bldg_frac, diffuse_params,
                               adopt_scheme, life_base, life_meas, mskeys):
        """ Partition microsegment to find "competed" stock and energy/carbon
        consumption as well as "efficient" energy consumption (representing
        consumption under the measure).  Also find the cost of the baseline
        and measure stock, energy, and carbon """

        # Initialize stock, energy, and carbon mseg partition dicts, where the
        # dict keys will be years in the modeling time horizon
        stock_total_meas, energy_total_eff, carb_total_eff, stock_compete, \
            energy_compete, carb_compete, stock_compete_meas, energy_compete_eff, \
            carb_compete_eff, stock_total_cost, energy_total_cost, carb_total_cost, \
            stock_total_cost_eff, energy_total_eff_cost, carb_total_eff_cost, \
            stock_compete_cost, energy_compete_cost, carb_compete_cost, \
            stock_compete_cost_eff, energy_compete_cost_eff, \
            carb_compete_cost_eff = ({} for n in range(21))

        # Initialize the portion of microsegment already captured by the
        # efficient measure as 0, and the portion baseline stock as 1.
        # For non-technical potential cases where measure lifetime is a
        # distribution of values, initialize the existing measure portion
        # as a numpy array of zeros
        captured_eff_frac = 0
        captured_base_frac = 1

        # Loop through and update stock, energy, and carbon mseg partitions for
        # each year in the modeling time horizon
        for yr in sorted(stock_total.keys()):

            # For non-technical potential scenarios, calculate the diffusion
            # fraction for the efficient measure (CURRENTLY PLACEDHOLDER OF 1)
            # and replacement fractions for the baseline and efficient stock.
            # * NOTE: THIS PART OF THE ROUTINE CURRENTLY ONLY APPLIES TO
            # 'PRIMARY' MICROSEGMENTS; 'SECONDARY' MICROSEGMENTS REQUIRE
            # SPECIAL HANDLING, TO BE FILLED OUT IN A FUTURE COMMIT
            if adopt_scheme != "Technical potential" and \
               mskeys[0] == "primary":

                # For the adjusted adoption potential case, determine the
                # portion of "competed" (new/replacement) technologies
                # that remain with the baseline technology or change to the
                # efficient alternative technology; otherwise, for all other
                # scenarios, set both fractions to 1
                if adopt_scheme == "Adjusted adoption potential":
                    # PLACEHOLDER
                    diffuse_eff_frac = 999
                else:
                    diffuse_eff_frac = 1

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
                # retrofit structures, the baseline replacement fraction
                # is the lesser of (1 / baseline lifetime) and the fraction
                # of retrofit stock from previous years that has already been
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
            else:  # PLACEHOLDER FOR HANDLING SECONDARY MICROSEGMENTS
                diffuse_eff_frac, captured_base_replace_frac = \
                    (1 for n in range(2))
                captured_eff_replace_frac = 0

            # Determine the fraction of total stock, energy, and carbon
            # in a given year that the measure will compete for under the
            # given technology adoption scenario

            # Calculate the competed fraction for a year where the measure is
            # on the market
            if (self.market_entry_year is None or int(yr) >=
                self.market_entry_year) and (self.market_exit_year is None or
               int(yr) < self.market_exit_year):
                # Current microsegment applies to new structure type
                if mskeys[-1] == "new":
                    if adopt_scheme == "Technical potential":
                        competed_frac = 1
                    else:
                        if new_bldg_frac["total"][yr] != 0:
                            new_bldg_add_frac = new_bldg_frac["added"][yr] / \
                                new_bldg_frac["total"][yr]
                            competed_frac = new_bldg_add_frac + \
                                (1 - new_bldg_add_frac) * \
                                (captured_eff_replace_frac +
                                 captured_base_replace_frac)
                        else:
                            competed_frac = 0
                # Current microsegment applies to retrofit structure type
                else:
                    if adopt_scheme == "Technical potential":
                        competed_frac = 1
                    else:
                        competed_frac = captured_base_replace_frac + \
                            captured_eff_replace_frac
            # The competed fraction for year where measure is not on market is
            # zero
            else:
                competed_frac = 0

            # Set the relative performance levels of the competed stock and
            # stock that has already been captured by the measure

            # If first year in the modeling time horizon, initialize the
            # relative performance level of previously captured stock as
            # identical to that of the competed stock (e.g., initialize
            # to the the relative performance from baseline -> measure
            # for that year only)
            if yr == sorted(stock_total.keys())[0]:
                rel_perf_captured = rel_perf[yr]
            # Set the relative performance level of the competed stock
            if adopt_scheme == 'Technical potential' and \
                    mskeys[0] == "primary":
                rel_perf_competed = (1 / life_meas) * rel_perf[yr] + \
                    (1 - (1 / life_meas)) * rel_perf_captured
            else:
                rel_perf_competed = rel_perf[yr]

            # Update competed stock, energy, and carbon
            stock_compete[yr] = stock_total[yr] * competed_frac
            energy_compete[yr] = energy_total[yr] * competed_frac
            carb_compete[yr] = carb_total[yr] * competed_frac

            # Determine the competed stock that is captured by the measure
            stock_compete_meas[yr] = stock_compete[yr] * diffuse_eff_frac

            # Determine the portion of existing stock that has already
            # been captured by the measure up until the current year;
            # subsequently, update the number of total and competed stock units
            # captured by the measure to reflect additions from the current
            # year. * Note: captured competed stock numbers are used in the
            # cost_metric_update function below to normalize measure cost
            # metrics to a per unit basis.  The captured stock will be less
            # than the competed stock in cases where the measure captures less
            # than 100% of the competed market share (determined in the
            # adjust_savings function below).

            # First year in the modeling time horizon
            if yr == list(sorted(stock_total.keys()))[0]:
                stock_total_meas[yr] = stock_compete_meas[yr]
            # Subsequent year in modeling time horizon
            else:
                # Update total number of stock units captured by the measure
                # (reflects all previously captured stock + captured competed
                # stock from the current year)
                stock_total_meas[yr] = stock_total_meas[str(int(yr) - 1)] + \
                    stock_compete_meas[yr]

                # Ensure stock captured by measure never exceeds total stock

                # Handle case where stock captured by measure is a numpy array
                if type(stock_total_meas[yr]) == numpy.ndarray and \
                   any(stock_total_meas[yr] > stock_total[yr]) \
                        is True:
                    stock_total_meas[yr][
                        numpy.where(
                            stock_total_meas[yr] > stock_total[yr])] = \
                        stock_total[yr]
                # Handle case where stock captured by measure is a point value
                elif type(stock_total_meas[yr]) != numpy.ndarray and \
                        stock_total_meas[yr] > stock_total[yr]:
                    stock_total_meas[yr] = stock_total[yr]

            # Update total-efficient and competed-efficient energy and
            # carbon, where "efficient" signifies the total and competed
            # energy/carbon remaining after measure implementation plus
            # non-competed energy/carbon. * Note: Efficient energy and
            # carbon is dependent upon whether the measure is on the market
            # for the given year (if not, use baseline energy and carbon)

            # Competed-efficient energy
            energy_compete_eff[yr] = energy_compete[yr] * diffuse_eff_frac * \
                rel_perf_competed * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr])
            # Total-efficient energy
            energy_total_eff[yr] = energy_compete_eff[yr] + \
                (energy_total[yr] - energy_compete[yr]) * \
                captured_eff_frac * rel_perf_captured * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) + \
                (energy_total[yr] - energy_compete[yr]) * \
                (1 - captured_eff_frac)
            # Competed-efficient carbon
            carb_compete_eff[yr] = carb_compete[yr] * diffuse_eff_frac * \
                rel_perf_competed * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                (intensity_carb_meas[yr] / intensity_carb_base[yr])
            # Total-efficient carbon
            carb_total_eff[yr] = carb_compete_eff[yr] + \
                (carb_total[yr] - carb_compete[yr]) * \
                captured_eff_frac * rel_perf_captured * \
                (site_source_conv_meas[yr] / site_source_conv_base[yr]) * \
                (intensity_carb_meas[yr] / intensity_carb_base[yr]) + \
                (carb_total[yr] - carb_compete[yr]) * (1 - captured_eff_frac)

            # Update total and competed stock, energy, and carbon
            # costs. * Note: total-efficient and competed-efficient stock
            # cost for the measure are dependent upon whether that measure is
            # on the market for the given year (if not, use baseline technology
            # cost)

            # Baseline cost of the total stock
            stock_total_cost[yr] = stock_total[yr] * cost_base[yr]
            # Baseline cost of the competed stock
            stock_compete_cost[yr] = stock_compete[yr] * cost_base[yr]
            # Competed-efficient stock cost
            stock_compete_cost_eff[yr] = stock_compete[yr] * cost_meas
            # Total-efficient stock cost
            stock_total_cost_eff[yr] = stock_total_meas[yr] * cost_meas \
                + (stock_total[yr] - stock_total_meas[yr]) * cost_base[yr]

            # Total baseline energy cost
            energy_total_cost[yr] = energy_total[yr] * cost_energy_base[yr]
            # Total energy-efficient cost
            energy_total_eff_cost[yr] = energy_total_eff[yr] * \
                cost_energy_meas[yr]
            # Competed baseline energy cost
            energy_compete_cost[yr] = energy_compete[yr] * cost_energy_base[yr]
            # Competed energy-efficient cost
            energy_compete_cost_eff[yr] = energy_compete_eff[yr] * \
                cost_energy_meas[yr]

            # Total baseline carbon cost
            carb_total_cost[yr] = carb_total[yr] * cost_carb[yr]
            # Total carbon-efficient cost
            carb_total_eff_cost[yr] = carb_total_eff[yr] * cost_carb[yr]
            # Competed baseline carbon cost
            carb_compete_cost[yr] = carb_compete[yr] * cost_carb[yr]
            # Competed carbon-efficient cost
            carb_compete_cost_eff[yr] = carb_compete_eff[yr] * cost_carb[yr]

            # Update portion of microsegment already captured by efficient
            # measure to reflect additions from the current modeling year. If
            # this portion is already 1, keep at 1; if we are updating a
            # secondary microsegment, set efficient stock portion to 1
            # (* FOR NOW *); if the total stock for the year is 0, set
            # efficient stock portion to 0

            # Handle case where stock captured by measure is a numpy array
            if type(stock_total_meas[yr]) == numpy.ndarray:
                for i in range(0, len(stock_total_meas[yr])):
                    if stock_total[yr] != 0 and captured_eff_frac[i] != 1 and \
                            mskeys[0] == "primary":
                        captured_eff_frac[i] = stock_total_meas[yr][i] / \
                            stock_total[yr]
                    elif mskeys[0] == "secondary":
                        captured_eff_frac[i] = 1
                    elif stock_total[yr] == 0:
                        captured_eff_frac[i] = 0
            # Handle case where stock captured by measure is a point value
            else:
                if stock_total[yr] != 0 and captured_eff_frac != 1 and \
                   mskeys[0] == "primary":
                    captured_eff_frac = stock_total_meas[yr] / stock_total[yr]
                elif mskeys[0] == "secondary":
                    captured_eff_frac = 1
                elif stock_total[yr] == 0:
                    captured_eff_frac = 0

            # Update portion of existing stock remaining with the baseline
            # technology
            captured_base_frac = 1 - captured_eff_frac

            # Update relative performance level of the captured stock by
            # adding the weighted relative performance of the competed
            # stock for the current year
            if stock_total_meas[yr] != 0:
                rel_perf_captured = rel_perf_competed * competed_frac + \
                    rel_perf_captured * (1 - competed_frac)

        # Return partitioned stock, energy, and cost mseg information
        return [stock_total_meas, energy_total_eff, carb_total_eff,
                stock_compete, energy_compete,
                carb_compete, stock_compete_meas, energy_compete_eff,
                carb_compete_eff, stock_total_cost, energy_total_cost,
                carb_total_cost, stock_total_cost_eff, energy_total_eff_cost,
                carb_total_eff_cost, stock_compete_cost, energy_compete_cost,
                carb_compete_cost, stock_compete_cost_eff,
                energy_compete_cost_eff, carb_compete_cost_eff]

    def calc_metric_update(self, rate, adjust_savings, com_timeprefs):
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

            # Set the lifetime of the baseline technology for comparison
            # with measure lifetime
            life_base = self.master_mseg["lifetime"]["baseline"][yr]
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
                # Check number of units captured by the measure
                if type(num_units) != numpy.ndarray:
                    num_units = numpy.repeat(num_units, length_array)

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
                                rate, scost_base, life_base,
                                scostsave_add_temp[x], esave_add_temp[x],
                                ecostsave_add_temp[x], csave_add_temp[x],
                                ccostsave_add_temp[x],
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
        try:
            irr_e = numpy.irr(cashflows_s + cashflows_e)
            payback_e = self.payback(cashflows_s + cashflows_e)
        except (ValueError, LinAlgError):
            pass

        # Calculate irr and simple payback for capital + energy + carbon cash
        # flows.  Check to ensure thar irr/payback can be calculated for the
        # given cash flows
        try:
            irr_ec = numpy.irr(cashflows_s + cashflows_e + cashflows_c)
            payback_ec = self.payback(cashflows_s + cashflows_e + cashflows_c)
        except (ValueError, LinAlgError):
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
                          measure_packages):
        """ Run initialization scheme on active measures only """
        for m in self.measures:
            # Find master microsegment and partitions, as well as measure
            # savings overlap information
            m.master_mseg, m.mseg_adjust = m.mseg_find_partition(
                mseg_in, base_costperflife_in, adopt_scheme)
            # Update savings outcomes and economic metrics
            # based on master microsegment
            m.master_savings = m.calc_metric_update(rate, adjust_savings,
                                                    com_timeprefs)

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
                packaged_measure = Measure_Package(measure_list_package, p)
                # Remove overlapping markets/savings between individual
                # measures in the package object
                packaged_measure.adjust_savings(
                    com_timeprefs, 'Packaged Measures')
                # Merge measures in the package object
                packaged_measure.merge_measures()
                # Update the savings outcomes and economic metrics for the
                # new packaged measure
                packaged_measure.master_savings = \
                    packaged_measure.calc_metric_update(rate, adjust_savings,
                                                        com_timeprefs)
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
        # Establish list of unique key chains in mseg_keys list above
        msegs = numpy.unique(mseg_keys)

        # Run through all unique contributing microsegments in above list,
        # determining how the measure savings associated with each should be
        # adjusted to reflect measure competition/market shares and, if
        # applicable, the removal of overlapping heating/cooling supply-side
        # and demand-side savings
        for msu in msegs:
            # Determine the subset of measures that compete for the given
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

            # If multiple measures are competing for the microsegment,
            # determine the market shares of the competing measures and adjust
            # measure master microsegments accordingly, using separate market
            # share modeling routines for residential and commercial sectors.
            if adjust_type == "Competing Measures" and \
                len(measures_adj) > 1 and \
                any(x in msu for x in (
                    'single family home', 'multi family home', 'mobile home')):
                self.res_compete(measures_adj, msu)
            elif adjust_type == "Competing Measures" and \
                len(measures_adj) > 1 and \
                all(x not in msu for x in (
                    'single family home', 'multi family home', 'mobile home')):
                self.com_compete(measures_adj, msu)
            elif adjust_type == "Packaged Measures" and \
                    len(measures_adj) > 1:
                self.package_merge(measures_adj, msu)
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
                    rate, adjust_savings, com_timeprefs)

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
                    mkt_fracs_tot[yr] = mkt_fracs_tot[yr] + mkt_fracs[ind][yr]

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
            for yr in m.master_savings[
                    "metrics"]["anpv"]["stock cost"].keys():
                # Ensure measure has captured stock to adjust in given year
                if (type(m.master_mseg["stock"]["competed"][
                    "measure"][yr]) == numpy.ndarray and all(
                    m.master_mseg["stock"]["competed"]["measure"][yr]) != 0) \
                    or (type(m.master_mseg["stock"]["competed"][
                        "measure"][yr]) != numpy.ndarray and m.master_mseg[
                        "stock"]["competed"]["measure"][yr] != 0):
                    mkt_fracs[ind][yr] = mkt_fracs[ind][yr] / mkt_fracs_tot[yr]
                    # Make the adjustment to the measure's master microsegment
                    # based on its updated market share
                    self.compete_adjustment(
                        mkt_fracs[ind], base, adj, base_list_eff, adj_list_eff,
                        adj_list_base, yr, mseg_key, m)

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
                            mkt_fracs[ind][yr][l] = sum(mkt_fracs[ind][yr][l])
                        # Convert market fractions list to numpy array for
                        # use in compete_adjustment function below
                        mkt_fracs[ind][yr] = numpy.array(mkt_fracs[ind][yr])
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
                        mkt_fracs[ind], base, adj, base_list_eff, adj_list_eff,
                        adj_list_base, yr, mseg_key, m)

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
            base["cost"]["stock"]["competed"]["efficient"],
            base["cost"]["energy"]["total"]["efficient"],
            base["cost"]["carbon"]["total"]["efficient"],
            base["cost"]["energy"]["competed"]["efficient"],
            base["cost"]["carbon"]["competed"]["efficient"],
            base["energy"]["total"]["efficient"],
            base["carbon"]["total"]["efficient"],
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
            adj["cost"]["stock"]["competed"]["baseline"],
            adj["cost"]["energy"]["total"]["baseline"],
            adj["cost"]["carbon"]["total"]["baseline"],
            adj["cost"]["energy"]["competed"]["baseline"],
            adj["cost"]["carbon"]["competed"]["baseline"],
            adj["energy"]["total"]["baseline"],
            adj["carbon"]["total"]["baseline"],
            adj["energy"]["competed"]["baseline"],
            adj["carbon"]["competed"]["baseline"]]
        # Total and competed energy, carbon, and cost for contributing
        # microsegment under full efficient measure adoption
        adj_list_eff = [
            adj["cost"]["stock"]["total"]["efficient"],
            adj["cost"]["stock"]["competed"]["efficient"],
            adj["cost"]["energy"]["total"]["efficient"],
            adj["cost"]["carbon"]["total"]["efficient"],
            adj["cost"]["energy"]["competed"]["efficient"],
            adj["cost"]["carbon"]["competed"]["efficient"],
            adj["energy"]["total"]["efficient"],
            adj["carbon"]["total"]["efficient"],
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
        # Adjust the total and competed stock captured by the measure by
        # the updated measure market share for the master microsegment and
        # current contributing microsegment
        base["stock"]["total"]["measure"][yr], \
            base["stock"]["competed"]["measure"][yr] = [
            x[yr] - y[yr] * (1 - adj_fracs[yr]) for x, y in
            zip([base["stock"]["total"]["measure"], base["stock"]["competed"][
                "measure"]], [adj["stock"]["total"]["measure"], adj["stock"][
                    "competed"]["measure"]])]
        adj["stock"]["total"]["measure"][yr], \
            adj["stock"]["competed"]["measure"][yr] = [
            x[yr] - y[yr] * (1 - adj_fracs[yr]) for x, y in
            zip([adj["stock"]["total"]["measure"], adj["stock"]["competed"][
                "measure"]], [adj["stock"]["total"]["measure"], adj["stock"][
                    "competed"]["measure"]])]

        # Adjust the total and competed energy, carbon, and associated cost
        # savings by the updated measure market share for the master
        # microsegment and current contributing microsegment
        base["cost"]["stock"]["total"]["efficient"][yr], \
            base["cost"]["stock"]["competed"]["efficient"][yr], \
            base["cost"]["energy"]["total"]["efficient"][yr], \
            base["cost"]["carbon"]["total"]["efficient"][yr], \
            base["cost"]["energy"]["competed"]["efficient"][yr], \
            base["cost"]["carbon"]["competed"]["efficient"][yr], \
            base["energy"]["total"]["efficient"][yr], \
            base["carbon"]["total"]["efficient"][yr], \
            base["energy"]["competed"]["efficient"][yr], \
            base["carbon"]["competed"]["efficient"][yr] = [
                x[yr] + ((z[yr] - y[yr]) * (1 - adj_fracs[yr])) for x, y, z in
                zip(base_list_eff, adj_list_eff, adj_list_base)]
        adj["cost"]["stock"]["total"]["efficient"][yr], \
            adj["cost"]["stock"]["competed"]["efficient"][yr], \
            adj["cost"]["energy"]["total"]["efficient"][yr], \
            adj["cost"]["carbon"]["total"]["efficient"][yr], \
            adj["cost"]["energy"]["competed"]["efficient"][yr], \
            adj["cost"]["carbon"]["competed"]["efficient"][yr], \
            adj["energy"]["total"]["efficient"][yr], \
            adj["carbon"]["total"]["efficient"][yr],\
            adj["energy"]["competed"]["efficient"][yr], \
            adj["carbon"]["competed"]["efficient"][yr] = [
                x[yr] + ((y[yr] - x[yr]) * (1 - adj_fracs[yr])) for x, y in
                zip(adj_list_eff, adj_list_base)]

        # Register the measure's savings adjustments if not already registered
        if measure.mseg_adjust["savings updated"] is not True:
            measure.mseg_adjust["savings updated"] = True

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
                            "supply-demand adjustment"]["savings"][mseg][yr] / \
                            m.mseg_adjust["supply-demand adjustment"][
                            "total"][mseg][yr]
                    # Adjust savings by supply-demand adjustment fraction
                    base["cost"]["energy"]["total"]["efficient"][yr], \
                        base["cost"]["carbon"]["total"]["efficient"][yr], \
                        base["cost"]["energy"]["competed"]["efficient"][yr], \
                        base["cost"]["carbon"]["competed"]["efficient"][yr], \
                        base["energy"]["total"]["efficient"][yr],\
                        base["carbon"]["total"]["efficient"][yr], \
                        base["energy"]["competed"]["efficient"][yr],\
                        base["carbon"]["competed"]["efficient"][yr] = \
                            [x[yr] + ((z[yr] - y[yr]) * overlap_adj_frac)
                             for x, y, z in zip(
                                base_list_eff[2:], adj_list_eff[2:],
                                adj_list_base[2:])]
                    # Register the measure's savings adjustments if not already
                    # registered
                    if m.mseg_adjust["savings updated"] is not True:
                        m.mseg_adjust["savings updated"] = True

    def write_outputs(self, csv_output_file):
        """ Write selected measure outputs to a summary CSV file """

        # Initialize a list to be populated with measure summary outputs
        measure_summary_list = []

        # Loop through all measures and append a dict of summary outputs to
        # the measure summary list above
        for m in self.measures:
            for yr in sorted(m.master_mseg["stock"]["total"]["all"].keys()):
                # Create list of output variables
                summary_mat = [
                    m.master_mseg["energy"]["total"]["efficient"][yr],
                    m.master_savings["energy"]["savings (total)"][yr],
                    m.master_savings["energy"]["cost savings (total)"][yr],
                    m.master_mseg["carbon"]["total"]["efficient"][yr],
                    m.master_savings["carbon"]["savings (total)"][yr],
                    m.master_savings["carbon"]["cost savings (total)"][yr],
                    m.master_savings["metrics"]["irr (w/ energy $)"][yr],
                    m.master_savings["metrics"][
                        "irr (w/ energy and carbon $)"][yr],
                    m.master_savings["metrics"]["payback (w/ energy $)"][yr],
                    m.master_savings["metrics"][
                        "payback (w/ energy and carbon $)"][yr],
                    m.master_savings["metrics"]["cce"][yr],
                    m.master_savings["metrics"][
                        "cce (w/ carbon $ benefits)"][yr],
                    m.master_savings["metrics"]["ccc"][yr],
                    m.master_savings["metrics"][
                        "ccc (w/ energy $ benefits)"][yr]]

                # Check if the current measure's efficent energy/carbon
                # markets, energy/carbon savings, and associated cost outputs
                # are arrays of values.  If so, find the average and 5th/95th
                # percentile values of each output array and report out.
                # Otherwise, report the point values for each output
                if type(m.master_mseg["energy"]["total"]["efficient"][yr]) == \
                   numpy.ndarray:
                    # Average values for outputs
                    energy_eff_avg, energy_save_avg, energy_costsave_avg, \
                        carb_eff_avg, carb_save_avg, carb_costsave_avg, \
                        irr_e_avg, irr_ec_avg, payback_e_avg, payback_ec_avg, \
                        cce_avg, cce_c_avg, ccc_avg, ccc_e_avg = \
                        [numpy.mean(x) for x in summary_mat]
                    # 5th percentile values for outputs
                    energy_eff_low, energy_save_low, energy_costsave_low, \
                        carb_eff_low, carb_save_low, carb_costsave_low,\
                        irr_e_low, irr_ec_low, payback_e_low, payback_ec_low, \
                        cce_low, cce_c_low, ccc_low, ccc_e_low = \
                        [numpy.percentile(x, 5) for x in summary_mat]
                    # 95th percentile values for outputs
                    energy_eff_high, energy_save_high, energy_costsave_high, \
                        carb_eff_high, carb_save_high, carb_costsave_high, \
                        irr_e_high, irr_ec_high, payback_e_high, payback_ec_high, \
                        cce_high, cce_c_high, ccc_high, ccc_e_high = \
                        [numpy.percentile(x, 95) for x in summary_mat]
                else:
                    energy_eff_avg, energy_save_avg, energy_costsave_avg, \
                        carb_eff_avg, carb_save_avg, carb_costsave_avg, \
                        irr_e_avg, irr_ec_avg, payback_e_avg, payback_ec_avg, \
                        cce_avg, cce_c_avg, ccc_avg, ccc_e_avg,\
                        energy_eff_low, energy_save_low, energy_costsave_low, \
                        carb_eff_low, carb_save_low, carb_costsave_low, \
                        irr_e_low, irr_ec_low, payback_e_low, payback_ec_low, \
                        cce_low, cce_c_low, ccc_low, ccc_e_low, \
                        energy_eff_high, energy_save_high, energy_costsave_high, \
                        carb_eff_high, carb_save_high, carb_costsave_high, \
                        irr_e_high, irr_ec_high, payback_e_high, payback_ec_high, \
                        cce_high, cce_c_high, ccc_high, ccc_e_high = \
                        [x for x in summary_mat] * 3

                # Set up subscript translator for CO2 variable strings
                sub = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")

                # Define a dict of summary output keys and values for the
                # current measure
                measure_summary_dict_yr = OrderedDict([
                    ("Year", yr), ("Measure Name", m.name),
                    ("Measure Climate Zone", m.climate_zone),
                    ("Measure Building Type", m.bldg_type),
                    ("Measure Structure Type", m.structure_type),
                    ("Measure Fuel Type", m.fuel_type["primary"]),
                    ("Measure End Use", m.end_use["primary"]),
                    ("Baseline Energy Use (MMBtu)", m.master_mseg[
                        "energy"]["total"]["baseline"][yr]),
                    ("Competed Energy Use (MMBtu)", m.master_mseg[
                        "energy"]["competed"]["baseline"][yr]),
                    ("Efficient Energy Use (MMBtu)", energy_eff_avg),
                    ("Efficient Energy Use (low) (MMBtu)", energy_eff_low),
                    ("Efficient Energy Use (high) (MMBtu)", energy_eff_high),
                    ("Energy Savings (MMBtu)", energy_save_avg),
                    ("Energy Savings (low) (MMBtu)", energy_save_low),
                    ("Energy Savings (high) (MMBtu)", energy_save_high),
                    ("Energy Cost Savings (USD)", energy_costsave_avg),
                    ("Energy Cost Savings (low) (USD)", energy_costsave_low),
                    ("Energy Cost Savings (high) (USD)", energy_costsave_high),
                    ("Baseline CO2 Emissions  (MMTons)".translate(sub),
                        m.master_mseg["carbon"]["total"]["baseline"][yr]),
                    ("Competed CO2 Emissions (MMTons)".translate(sub),
                        m.master_mseg[
                        "carbon"]["competed"]["baseline"][yr]),
                    ("Efficient CO2 Emissions (MMTons)".translate(sub),
                        carb_eff_avg),
                    ("Efficient CO2 Emissions (low) (MMTons)".translate(sub),
                        carb_eff_low),
                    ("Efficient CO2 Emissions (high) (MMTons)".translate(sub),
                        carb_eff_high),
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
                        carb_costsave_high),
                    ("IRR (%)", irr_e_avg * 100),
                    ("IRR (low) (%)", irr_e_low * 100),
                    ("IRR (high) (%)", irr_e_high * 100),
                    ("IRR (w/ CO2 cost savings) (%)".translate(sub),
                        irr_ec_avg * 100),
                    ("IRR (w/ CO2 cost savings) (low) (%)".translate(sub),
                        irr_ec_low * 100),
                    ("IRR (w/ CO2 cost savings) (high) (%)".translate(sub),
                        irr_ec_high * 100),
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
                    (("Cost of Conserved Energy (w/ CO2 cost savings benefit) "
                      "($/MMBtu saved)").translate(sub), cce_c_avg),
                    (("Cost of Conserved Energy (w/ CO2 cost savings benefit) "
                      "(low) ($/MMBtu saved)").translate(sub), cce_c_low),
                    (("Cost of Conserved Energy (w/ CO2 cost savings benefit) "
                      "(high) ($/MMBtu saved)").translate(sub), cce_c_high),
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
                      "($/MMTon CO2 avoided)").translate(sub), ccc_e_high)])

                # Append the dict of summary outputs for the current measure to
                # the summary list of outputs across all active measures
                measure_summary_list.append(measure_summary_dict_yr)

        # Write the summary outputs list to a CSV
        with open(csv_output_file, 'w', newline="") as f:
            dict_writer = csv.DictWriter(
                f, fieldnames=measure_summary_list[0].keys())
            dict_writer.writeheader()
            dict_writer.writerows(measure_summary_list)


# Define class for measure package objects
class Measure_Package(Measure, Engine):

    def __init__(self, measure_list_package, p):
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
                        # Combine overlapping microsegments
                        for cm in m.mseg_adjust[k].keys():
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
                            else:
                                self.mseg_adjust[k][cm] = m.mseg_adjust[k][cm]

                    # Add measure's contributing microsegment consumer choice
                    # parameters
                    elif k == "competed choice parameters":
                        self.mseg_adjust[k].update(m.mseg_adjust[k])
                    # Add information about supply-demand overlaps for the
                    # measure's contributing microsegments (relevant for HVAC
                    # measures)
                    elif k == "supply-demand adjustment":
                        self.mseg_adjust[k]["savings"].update(
                            m.mseg_adjust[k]["savings"])
                        self.mseg_adjust[k]["total"].update(
                            m.mseg_adjust[k]["total"])

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


def main():

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
                            com_timeprefs, measure_packages)
    # Compete active measures if user has specified this option
    if adjust_savings is True:
        a_run.adjust_savings(com_timeprefs, 'Competing Measures')

    # Write selected outputs to a summary CSV file for post-processing
    a_run.write_outputs(csv_output_file)

if __name__ == '__main__':
    import time
    start_time = time.time()
    main()
    print("--- Runtime: %s seconds ---" % round((time.time() - start_time), 2))
