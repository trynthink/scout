#!/usr/bin/env python3
import json
import itertools
import numpy
import copy
import re

# Define measures/microsegments files
measures_file = "measures.json"
microsegments_file = "microsegments_out_test.json"
mseg_base_costperflife_info = "microsegments_base_costperflife.json"

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

# Set discount rate for cost calculations
rate = 0.07

# User-specified inputs (placeholders for now, eventually draw from GUI?)
active_measures = []
adopt_scheme = 'Technical potential'
decision_rule = 'NA'

# Set default number of input samples for Monte Carlo runs
nsamples = 50

# Define end use cases where relative performance calculation should be
# inverted (i.e., a lower air change rate is an improvement)
inverted_relperf_list = ["ACH50", "CFM/sf", "kWh/yr", "kWh/day", "SHGC",
                         "HP/CFM"]


# Define class for measure objects
class Measure(object):

    def __init__(self, **kwargs):
        # Initialize attributes from JSON
        for key, value in kwargs.items():
            setattr(self, key, value)
        # Initialize measure inclusion state attribute
        if self.name in active_measures:
            self.active = 1
        else:
            self.active = 0

        # Initialize master microsegment attribute
        self.master_mseg = None
        self.master_savings = None

        # Initialize other mseg-related attributes
        self.total_energy_norm = {}  # Energy/stock (whole mseg)
        self.compete_energy_norm = {}  # Energy/stock (competed mseg)
        self.efficient_energy_norm = {}  # Energy/stock (efficient)
        self.total_carb_norm = {}  # Carbon/stock (whole mseg)
        self.compete_carb_norm = {}  # Carbon/stock (competed mseg)
        self.efficient_carb_norm = {}  # Carbon/stock (efficient)

        # Initialize relative change attributes (meas vs. base)
        self.esavings_norm = {}  # Energy savings/stock
        self.ecostsavings_norm = {}  # Total energy cost savings/stock
        self.carbsavings_norm = {}  # CO2 savings/stock
        self.carbcostsavings_norm = {}  # CO2 cost savings/stock

    def mseg_find_partition(self, mseg_in, base_costperflife_in, adopt_scheme):
        """ Given an input measure with microsegment selection information and two
        input dicts with AEO microsegment cost and performance and stock and
        energy consumption information, find: 1) total and competed stock,
        2) total, competed, and energy efficient consumption and 3)
        associated cost of the competed stock """

        # Initialize master microsegment stock, energy, carbon, cost, and
        # lifetime information dict
        mseg_master = {"stock": {"total": None, "competed": None},
                       "energy": {"total": None, "competed": None,
                                  "efficient": None},
                       "carbon": {"total": None, "competed": None,
                                  "efficient": None},
                       "cost": {"baseline": {"stock": None, "energy": None,
                                             "carbon": None},
                                "measure": {"stock": None, "energy": None,
                                            "carbon": None}},
                       "lifetime": None}

        # Initialize a dict to register contributing microsegments for
        # later use in determining overlapping measure microsegments in staging
        overlap_dict = {}

        # Initialize a counter of valid key chains
        key_chain_ct = 0

        # Initialize variable indicating use of sq.ft. as microsegment stock
        sqft_subst = 0

        # Initialize variable flagging heating, 2nd heat, and cooling end uses
        htcl_enduse_ct = 0
        # Determine end use case, first ensuring end use is input as a list
        if isinstance(self.end_use, list) is False:
            self.end_use = [self.end_use]
        for eu in self.end_use:
            if eu == "heating" or eu == "secondary heating" or eu == "cooling":
                htcl_enduse_ct += 1

        # Create a list of lists where each list has key information for
        # one of the microsegment levels. Use list to find all possible
        # microsegment key chains (i.e. ("new england", "single family home",
        # "natural gas", "water heating")). Add in "demand" and "supply keys
        # where needed (heating, secondary heating, cooling end uses)
        if (htcl_enduse_ct > 0):
            ms_lists = [self.climate_zone, self.bldg_type, self.fuel_type,
                        self.end_use, self.technology_type, self.technology]
        else:
            ms_lists = [self.climate_zone, self.bldg_type, self.fuel_type,
                        self.end_use, self.technology]

        # Ensure that every list element is itself a list
        for x in range(0, len(ms_lists)):
            if isinstance(ms_lists[x], list) is False:
                ms_lists[x] = [ms_lists[x]]
        # Find all possible microsegment key chains
        ms_iterable = list(itertools.product(*ms_lists))

        # Loop through discovered key chains to find needed performance/cost
        # and stock/energy information for measure
        for mskeys in ms_iterable:
            # Initialize (or re-initialize) performance/cost/lifetime and
            # performance/cost units if dicts (lifetime assumed to be in years)
            if mskeys == ms_iterable[0] or isinstance(
                    self.energy_efficiency, dict):
                perf_meas = self.energy_efficiency
            if mskeys == ms_iterable[0] or isinstance(
                    self.installed_cost, dict):
                cost_meas = self.installed_cost
            if mskeys == ms_iterable[0] or isinstance(
                    self.energy_efficiency_units, dict):
                perf_units = self.energy_efficiency_units
            if mskeys == ms_iterable[0] or isinstance(self.cost_units, dict):
                cost_units = self.cost_units
            if mskeys == ms_iterable[0] or isinstance(
                    self.product_lifetime, dict):
                life_meas = self.product_lifetime

            # Initialize dicts of microsegment information specific to this run
            # of for loop; also initialize dict for mining sq.ft. information
            # to be used as stock for microsegments without no. units info.
            base_costperflife = base_costperflife_in
            mseg = mseg_in
            mseg_sqft = mseg_in

            # Initialize a dict for relative performance (broken out by year in
            # modeling time horizon)
            rel_perf = {}

            # Loop recursively through the above dicts, moving down key chain
            for i in range(0, len(mskeys)):
                # Check for key in dict level
                if mskeys[i] in base_costperflife.keys():
                    # Restrict base cost/performance/lifetime dict to key chain
                    # info.
                    base_costperflife = base_costperflife[mskeys[i]]
                    # Restrict stock/energy dict to key chain info.
                    mseg = mseg[mskeys[i]]
                    # Restrict any measure cost/performance/lifetime info. that
                    # is a dict type to key chain info.
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
                    # Restrict sq.ft. dict to key chain info.
                    if i < 2:  # Note: sq.ft. broken out 2 levels (cdiv, bldg)
                        mseg_sqft = mseg_sqft[mskeys[i]]
                # If no key match, break the loop
                else:
                    break

            # If mseg dict isn't defined to "stock" info. level, go no further
            if "stock" not in list(mseg.keys()):
                continue
            # Otherwise update all stock/energy/cost information for each year
            else:
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
                # consistent baseline/measure performance and cost units
                if base_costperflife["performance"]["units"] == perf_units and \
                   base_costperflife["installed cost"]["units"] == cost_units:
                    # Set base performance dict
                    perf_base = base_costperflife["performance"]["typical"]

                    # Relative performance calculation depends on tech. case
                    # (i.e. COP  of 4 is higher rel. performance than COP 3,
                    # (but 1 ACH50 is higher rel. performance than 13 ACH50).
                    # Note that relative performance values are stored in a
                    # dict with keys for each year in the modeling time horizon
                    if perf_units not in inverted_relperf_list:
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

                    # Set base cost
                    cost_base = base_costperflife["installed cost"]["typical"]
                else:
                    raise KeyError('Inconsistent performance or cost units!')

                # Set base lifetime
                life_base = base_costperflife["lifetime"]["average"]

                # Set appropriate site-source factor, energy cost, and CO2
                # intensity for given key chain
                site_source_conv = ss_conv[mskeys[2]]
                intensity_carb = carb_int[mskeys[2]]
                # Reduce energy costs info. to appropriate building type and
                # fuel before entering into "partition_microsegment"
                if mskeys[1] in ["single family home", "mobile home",
                                 "multi family home"]:
                    cost_energy = ecosts["residential"][mskeys[2]]
                else:
                    cost_energy = ecosts["commercial"][mskeys[2]]

                # Update total stock and energy information
                if mseg["stock"] == "NA":  # Use sq.ft. in absence of no. units
                    sqft_subst = 1
                    add_stock = mseg_sqft["square footage"]
                else:
                    add_stock = mseg["stock"]
                add_energy_site = mseg["energy"]  # Site energy information
                add_energy = {}  # Source energy dict
                add_carb = {}  # Carbon emissions dict
                for yr in add_energy_site:  # Site-source & CO2 calc.
                    add_energy[yr] = add_energy_site[yr] * site_source_conv[yr]
                    add_carb[yr] = add_energy[yr] * intensity_carb[yr]

                # Update competed and efficient stock, energy, CO2
                # and baseline/measure cost info. based on adoption scheme
                [add_compete_stock, add_compete_energy, add_compete_carb,
                 add_efficient_energy, add_efficient_carb, add_cost_stock_base,
                 add_cost_energy_base, add_cost_carb_base, add_cost_stock_meas,
                 add_cost_energy_meas, add_cost_carb_meas] = \
                    self.partition_microsegment(add_stock, add_energy,
                                                add_carb, rel_perf, cost_base,
                                                cost_meas, cost_energy,
                                                ccosts, adopt_scheme)

                # Combine stock/energy/carbon/cost/lifetime updating info. into
                # a dict
                add_dict = {"stock": {"total": add_stock,
                                      "competed": add_compete_stock},
                            "energy": {"total": add_energy,
                                       "competed": add_compete_energy,
                                       "efficient": add_efficient_energy},
                            "carbon": {"total": add_carb,
                                       "competed": add_compete_carb,
                                       "efficient": add_efficient_carb},
                            "cost": {"baseline": {
                                     "stock": add_cost_stock_base,
                                     "energy": add_cost_energy_base,
                                     "carbon": add_cost_carb_base
                                     },
                                     "measure": {
                                     "stock": add_cost_stock_meas,
                                     "energy": add_cost_energy_meas,
                                     "carbon": add_cost_carb_meas}},
                            "lifetime": life_base}

                # Register contributing microsegment for later use
                # in determining staging overlaps
                overlap_dict[str(mskeys)] = add_dict

                # Add all updated info. to existing master mseg dict and
                # move to next iteration of the loop through key chains
                mseg_master = self.add_keyvals(mseg_master, add_dict)

        if key_chain_ct != 0:

            # Reduce summed lifetimes by number of microsegments that
            # contributed to the sum
            for yr in mseg_master["lifetime"].keys():
                mseg_master["lifetime"][yr] = mseg_master["lifetime"][yr] / \
                    key_chain_ct

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
                mseg_master = self.reduce_sqft_stock_cost(mseg_master,
                                                          reduce_factor)
            else:
                reduce_factor = 1
        else:
                raise KeyError('No valid key chains discovered for lifetime and sq.ft. \
                                  stock and cost division operation!')

        # Register contributing microsegment for later use
        # in determining staging overlaps
        overlap_dict["reduce factor"] = reduce_factor

        # Return the final master microsegment
        return [mseg_master, overlap_dict]

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

    def partition_microsegment(self, mseg_stock, mseg_energy, mseg_carb,
                               rel_perf, cost_base, cost_meas, cost_energy,
                               cost_carb, adopt_scheme):
        """ Partition microsegment to find "competed" stock and energy
        consumption as well as "efficient" energy consumption (representing
        consumption under the measure).  Also find the cost of the baseline
        and measure stock, energy, and carbon """

        # Initialize stock, energy, and carbon information addition dicts
        stock_compete_cost_base = {}
        stock_compete_cost_meas = {}
        energy_compete_cost = {}
        carb_compete_cost = {}
        energy_eff = {}
        energy_eff_cost = {}
        carb_eff = {}
        carb_eff_cost = {}

        # Determine whether this is a technical potential calculation
        tp = re.search('Technical potential', adopt_scheme, re.IGNORECASE)

        if tp:
            # If a technical potential calculation, "competed" stock, energy
            # and carbon = "total" stock, energy and carbon
            stock_compete = mseg_stock
            energy_compete = mseg_energy
            carb_compete = mseg_carb

            # Loop through all projection years to update remaining energy,
            # carbon, and cost information
            for yr in stock_compete.keys():
                # Update "competed" stock cost (baseline)
                stock_compete_cost_base[yr] = stock_compete[yr] * cost_base[yr]
                stock_compete_cost_meas[yr] = stock_compete[yr] * cost_meas

                # Update "competed" energy and carbon costs (baseline)
                energy_compete_cost[yr] = energy_compete[yr] * cost_energy[yr]
                carb_compete_cost[yr] = carb_compete[yr] * cost_carb[yr]

                # Update "efficient" energy and carbon and associated costs
                energy_eff[yr] = energy_compete[yr] * rel_perf[yr]
                energy_eff_cost[yr] = energy_eff[yr] * cost_energy[yr]
                carb_eff[yr] = carb_compete[yr] * rel_perf[yr]
                carb_eff_cost[yr] = carb_eff[yr] * cost_carb[yr]

        else:  # The below few lines are temporary
            stock_compete = None
            energy_compete = None
            carb_compete = None
            stock_compete_cost_base = None
            stock_compete_cost_meas = None
            energy_compete_cost = None
            carb_compete_cost = None
            energy_eff = None
            energy_eff_cost = None
            carb_eff = None
            carb_eff_cost = None

        # Return updated stock, energy, and cost information
        return [stock_compete, energy_compete, carb_compete, energy_eff,
                carb_eff, stock_compete_cost_base, energy_compete_cost,
                carb_compete_cost, stock_compete_cost_meas, energy_eff_cost,
                carb_eff_cost]

    def calc_metric_update(self, rate):
        """ Given information on a measure's master microsegment for
        each projection year and a discount rate, determine capital ("stock"),
        energy, and carbon cost savings; energy and carbon savings; and the
        internal rate of return, simple payback, cost of conserved energy, and
        cost of conserved carbon for the measure. """

        # Initialize a set of dicts including information on capital
        # cost savings; energy and energy costs savings; carbon and carbon cost
        # savings; and a series of possible measure prioritization metrics
        # (internal rate of return, simple payback, cost of conserved energy,
        # cost of conserved carbon)
        scostsave_list, esave_list, ecostsave_list, csave_list, ccostsave_list, \
            irr_e, irr_ec, payback_e, payback_ec, cce, cce_bens, ccc, ccc_bens = \
            ({} for d in range(13))

        # Calculate capital cost savings, energy/carbon savings, and
        # energy/carbon cost savings for each projection year
        for yr in self.master_mseg["stock"]["competed"].keys():

            # Define ratio of measure lifetime to baseline lifetime.  This will
            # be used below in determining capital cashflows over the measure
            # lifetime
            life_ratio = int(self.life_meas / self.master_mseg["lifetime"][yr])

            # Determine the initial incremental capital cost of the
            # measure over the baseline
            stock_costsave_init = \
                self.master_mseg["cost"]["baseline"]["stock"][yr] - \
                self.master_mseg["cost"]["measure"]["stock"][yr]

            # Determine subsequent capital cost gains (if any) of the measure
            # over the baseline due to a comparatively longer lifetime (i.e, if
            # a measure has twice the lifetime of a baseline technology it
            # will take two purchases of the baseline technology to
            # equal one purchase of the measure technology).
            if life_ratio != 1:
                # Determine the cost gain (= capital cost of baseline tech.)
                stock_costsave_life = \
                    self.master_mseg["cost"]["baseline"]["stock"][yr]
                # Determine when over the course of the measure lifetime
                # this cost gain is realized; store this information in
                # a list of year indicators for subsequent use below
                added_stockcost_gain_yrs = []
                for i in range(0, life_ratio - 1):
                    added_stockcost_gain_yrs.append(
                        2 * i + self.master_mseg["lifetime"][yr])

            # Calculate annual energy savings for the measure vs. baseline
            esave = \
                self.master_mseg["energy"]["competed"][yr] - \
                self.master_mseg["energy"]["efficient"][yr]
            # Calculate annual energy cost savings for the measure vs. baseline
            ecostsave = \
                self.master_mseg["cost"]["baseline"]["energy"][yr] - \
                self.master_mseg["cost"]["measure"]["energy"][yr]
            # Calculate annual carbon savings for the measure vs. baseline
            csave = \
                self.master_mseg["carbon"]["competed"][yr] - \
                self.master_mseg["carbon"]["efficient"][yr]
            # Calculate annual carbon cost savings for the measure vs. baseline
            ccostsave = \
                self.master_mseg["cost"]["baseline"]["carbon"][yr] - \
                self.master_mseg["cost"]["measure"]["carbon"][yr]

            # Combine each of the above capital/energy/carbon savings variables
            # into a single list for use in determining consistency of
            # formatting.  For example, if a user specifies a distribution on
            # the measure capital cost but not the performance, energy/carbon
            # cost savings information will be in a list format, while
            # energy/carbon savings will be point values.  The few lines
            # below ensure formatting of all variables as lists of length N,
            # where N is the maximum length of "check_format" elements
            check_format = [stock_costsave_init, esave, ecostsave,
                            csave, ccostsave]
            # First, ensure that all variables in "check_format" are formatted
            # as lists
            for c in range(0, len(check_format)):
                if type(check_format[c]) != list:
                    check_format[c] = [check_format[c]]
            # Then, find "check_format" element lengths and ensure they are
            # consistent; if there are differences in the element lengths, find
            # the maximum element length and extend all elements to this length
            # to simplify later operations
            if all(len(n) == 1 for n in check_format):  # All point values
                list_length = 1
            elif all(len(n) > 1 for n in check_format):  # All lists
                list_length = len(check_format[0])
            else:  # Mix of point values and lists
                list_length = \
                    len(next(x for x in check_format if type(x) == list))
                for elem in check_format:
                    if type(elem) != list:
                        elem = [elem] * list_length

            # Develop a list of zeros consistent with maximum element
            # length, to be added to initial capital cost savings list below
            # for all years > 0; and to initial energy/energy cost and carbon/
            # carbon cost savings lists below for year == 0
            zeros_add = [0] * list_length

            # Develop initial list of capital cost savings across measure life
            scostsave_list[yr] = numpy.array(check_format[0] + zeros_add *
                                             self.life_meas)
            # Develop initial list of energy savings across measure life
            esave_list[yr] = numpy.array(zeros_add + check_format[1] *
                                         self.life_meas)
            # Develop initial list of energy cost savings across measure life
            ecostsave_list[yr] = numpy.array(zeros_add + check_format[2] *
                                             self.life_meas)
            # Develop initial list of carbon savings across measure life
            csave_list[yr] = numpy.array(zeros_add + check_format[3] *
                                         self.life_meas)
            # Develop initial list of carbon cost savings across measure life
            ccostsave_list[yr] = numpy.array(zeros_add + check_format[4] *
                                             self.life_meas)

            # Develop three initial cash flow scenarios over the measure life:
            # 1) Cash flows considering capital costs and energy costs
            # 2) Cash flows considering capital costs and carbon costs
            # 3) Cash flows considering capital, energy, and carbon costs
            cashflows_se = scostsave_list[yr] + ecostsave_list[yr]
            cashflows_sc = scostsave_list[yr] + ccostsave_list[yr]
            cashflows_sec = scostsave_list[yr] + ecostsave_list[yr] + \
                ccostsave_list[yr]

            # If measure has longer life than baseline, update all cash flows
            # to reflect capital cost gains from longer life in the appropriate
            # years (indicated by "added_stockcost_gain_yrs" list)
            if stock_costsave_life:
                for elem in range(0, len(scostsave_list[yr]) + 1):
                    if any(added_stockcost_gain_yrs) == elem:
                        # Reflect additional capital gains in
                        # appropriate years of capital cost
                        # savings list
                        scostsave_list[yr][elem] = stock_costsave_life + \
                            scostsave_list[yr][elem]
                        # Reflect additional capital gains in
                        # appropriate years of cash flows
                        cashflows_se[elem] = stock_costsave_life + \
                            cashflows_se[elem]
                        cashflows_sc[elem] = stock_costsave_life + \
                            cashflows_sc[elem]
                        cashflows_sec[elem] = stock_costsave_life + \
                            cashflows_sec[elem]

            # Using the above lifetime capital costs, cash flows, and energy
            # and carbon savings, calculate desired prioritization metrics

            # If the inputs are each lists, expect metric outputs that are also
            # lists of the same length; otherwise, expect point value outputs
            if list_length > 1:
                # Initialize output lists
                irr_e[yr], irr_ec[yr], payback_e[yr], payback_ec[yr], cce[yr], \
                    cce_bens[yr], ccc[yr], ccc_bens[yr] = \
                    ([None] * list_length for i in range(8))
                # Loop through each output list element and update with
                # appropriate metric calculation
                for x in range(0, list_length):
                    irr_e[yr][x], irr_ec[yr][x], payback_e[yr][x], \
                        payback_ec[yr][x], cce[yr][x], cce_bens[yr][x], \
                        ccc[yr][x], ccc_bens[yr][x] = self.metric_update(
                            rate, scostsave_list[yr][x], cashflows_se[yr][x],
                            cashflows_sc[x], cashflows_sec[x],
                            esave_list[yr][x], csave_list[yr][x])
            else:
                # Update each output value with appropriate metric calculation
                irr_e[yr], irr_ec[yr], payback_e[yr], payback_ec[yr], cce[yr],\
                    cce_bens[yr], ccc[yr], ccc_bens[yr] = self.metric_update(
                        rate, scostsave_list[yr], cashflows_se,
                        cashflows_sc, cashflows_sec, esave_list[yr],
                        csave_list[yr])

        # Record final measure savings figures and prioritization metrics
        # in a dict that is returned by the function
        mseg_save = {"stock": {"cost savings": scostsave_list},
                     "energy": {"savings": esave_list,
                                "cost savings": ecostsave_list},
                     "carbon": {"savings": csave_list,
                                "cost savings": ccostsave_list},
                     "metrics": {"irr (w/ energy $)": irr_e,
                                 "irr (w/ energy and carbon $)": irr_ec,
                                 "payback (w/ energy $)": payback_e,
                                 "payback (w/ energy and carbon $)":
                                 payback_ec,
                                 "cce": cce,
                                 "cce (w/ carbon $ benefits)": cce_bens,
                                 "ccc": ccc,
                                 "ccc (w/ energy $ benefits)": ccc_bens}}

        # Return final savings figures and prioritization metrics
        return mseg_save

    def reduce_sqft_stock_cost(self, dict1, reduce_factor):
        """ Divide "stock" and "stock cost" information by a given factor to
        handle special case when sq.ft. is used as stock """
        for (k, i) in dict1.items():
            # Do not divide any energy or carbon information
            if (k == "energy" or k == "carbon" or k == "lifetime"):
                    continue
            else:
                    if isinstance(i, dict):
                        self.reduce_sqft_stock_cost(i, reduce_factor)
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

    def metric_update(self, rate, scostsave_list, cashflows_se, cashflows_sc,
                      cashflows_sec, esave_list, csave_list):
        """ Calculate internal rate of return, simple payback, and cost of
        conserved energy/carbon given input cash flows and energy/carbon
        savings across the measure lifetime """

        # Calculate irr for capital + energy and capital + energy + carbon
        # cash flows
        irr_e = numpy.irr(cashflows_se)
        irr_ec = numpy.irr(cashflows_sec)
        # Calculate simple payback for capital + energy and capital + energy +
        # carbon cash flows
        payback_e = self.payback(cashflows_se)
        payback_ec = self.payback(cashflows_sec)
        # Calculate cost of conserved energy w/o carbon cost savings benefits
        cce = numpy.npv(rate, scostsave_list) / numpy.npv(rate, esave_list)
        # Calculate cost of conserved energy w/ carbon cost savings benefits
        cce_bens = numpy.npv(rate, cashflows_sc) / numpy.npv(rate, esave_list)
        # Calculate cost of conserved carbon w/o energy cost savings benefits
        ccc = numpy.npv(rate, scostsave_list) / numpy.npv(rate, csave_list)
        # Calculate cost of conserved carbon w/ energy cost savings benefits
        ccc_bens = numpy.npv(rate, cashflows_se) / numpy.npv(rate, csave_list)

        # Return all updated prioritization metrics
        return irr_e, irr_ec, payback_e, payback_ec, \
            cce, cce_bens, ccc, ccc_bens

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
        self.measure_objs = measure_objects

    def adopt_active(self, mseg_in, base_costperflife_in, adopt_scheme,
                     decision_rule, rate):
        """ Run adoption scheme on active measures only """
        for m in self.measure_objs:
            if m.active == 1:
                # Find master microsegment and partitions
                m.master_mseg = m.mseg_find_partition(
                    mseg_in, base_costperflife_in, adopt_scheme)
                # Update cost/savings outcomes based on master microsegment
                m.master_savings = m.calc_metric_update(rate)
        # Eventually adopt measures here using updated measure decision info.


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

    for mi in measures_input:
        measures_objlist.append(Measure(**mi))

    a_run = Engine(measures_objlist)
    a_run.adopt_active(microsegments_input, base_costperflife_info_input,
                       adopt_scheme, decision_rule, rate)

if __name__ == '__main__':
    main()
