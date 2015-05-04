#!/usr/bin/env python3
import json
import itertools
import numpy
import copy
import re

# Define measures/microsegments files
measures_file = "measures.json"
microsegments_file = "microsegments_out_test.json"
mseg_base_costperf_info = "microsegments_base_costperf.json"  # To be developed

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
        # Initialize other mseg-related attributes
        self.mseg_energy = None  # Energy (whole mseg)
        self.mseg_stock = None  # No. units and/or sq.ft. (whole mseg)
        self.mseg_energy_norm = None  # Energy/stock (whole mseg)
        self.compete_energy = None  # Energy (competed mseg)
        self.compete_stock = None  # No. units and/or sq.ft. (competed mseg)
        self.compete_energy_norm = None  # Energy/stock (competed mseg)
        self.efficient_energy = None  # Energy (efficient scenario)
        self.efficient_energy_norm = None  # Energy/stock (efficient)
        # Initialize relative improvement attributes
        self.esavings = None  # Total energy savings
        self.esavings_norm = None  # Energy savings/stock
        self.carbsavings = None  # Total CO2 savings
        self.carbsavings_norm = None  # CO2 savings/stock
        # Initialize decision making attributes
        self.irr = None  # Internal rate of return
        self.payback = None  # Simple payback
        self.initexpend_pct = None  # Initial expenditure as % of budget
        self.cce = None  # Cost of Conserved Energy
        self.ccc = None  # Cost of Conserved Carbon
        # Other attributes to be added as needed

    def mseg_find_partition(self, mseg_in, base_costperf_in, adopt_scheme):
        """ Given an input measure with microsegment selection information and two
        input dicts with AEO microsegment cost and performance and stock and
        energy consumption information, find: 1) total and competed stock,
        2) total, competed, and energy efficient consumption and 3)
        associated cost of the competed stock """

        # Initialize master stock, energy, carbon, and cost information dict
        mseg_master = {"stock": {"total": None, "competed": None},
                       "energy": {"total": None, "competed": None,
                                  "efficient": None},
                       "carbon": {"total": None, "competed": None,
                                  "efficient": None},
                       "cost": {"baseline": {"stock": None, "energy": None,
                                             "carbon": None},
                                "measure": {"stock": None, "energy": None,
                                            "carbon": None}}}

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
            # Initialize (or re-initialize) performance/cost and units if dicts
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

            # Initialize dicts of microsegment information specific to this run
            # of for loop; also initialize dict for mining sq.ft. information
            # to be used as stock for microsegments without no. units info.
            base_costperf = base_costperf_in
            mseg = mseg_in
            mseg_sqft = mseg_in

            # Loop recursively through the above dicts, moving down key chain
            for i in range(0, len(mskeys)):
                # Check for key in dict level
                if mskeys[i] in base_costperf.keys():
                    # Restrict base cost/performance dict to key chain info.
                    base_costperf = base_costperf[mskeys[i]]
                    # Restrict stock/energy dict to key chain info.
                    mseg = mseg[mskeys[i]]
                    # Restrict any measure cost/performance info. that is
                    # a dict type to key chain info.
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
                # Determine relative measure performance after checking for
                # consistent baseline/measure performance and cost units
                if base_costperf["performance"]["units"] == perf_units and \
                   base_costperf["cost"]["units"] == cost_units:
                    # Relative performance calculation depends on tech. case
                    # (i.e. COP  of 4 is higher rel. performance than COP 3,
                    # (but 1 ACH50 is higher rel. performance than 13 ACH50)
                    if perf_units not in inverted_relperf_list:
                        if isinstance(perf_meas, list):  # Perf. distrib. case
                            rel_perf = [(x ** -1 * base_costperf["performance"]
                                        ["value"]) for x in perf_meas]
                        else:
                            rel_perf = (base_costperf["performance"]["value"] /
                                        perf_meas)
                    else:
                        if isinstance(perf_meas, list):  # Perf. distrib. case
                            rel_perf = [(x / base_costperf["performance"]
                                        ["value"]) for x in perf_meas]
                        else:
                            rel_perf = (perf_meas /
                                        base_costperf["performance"]["value"])
                    base_cost = base_costperf["cost"]["value"]
                else:
                    raise(KeyError('Inconsistent performance or cost units!'))

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
                                                add_carb, rel_perf, base_cost,
                                                cost_meas, cost_energy,
                                                ccosts, adopt_scheme)

                # Combine stock/energy/carbon/cost updating info. into a dict
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
                                     "carbon": add_cost_carb_meas}}}

                # Register contributing microsegment for later use
                # in determining staging overlaps
                overlap_dict[str(mskeys)] = add_dict

                # Add all updated info. to existing master mseg dict and
                # move to next iteration of the loop through key chains
                mseg_master = self.add_keyvals(mseg_master, add_dict)

        # In microsegments where square footage must be used as stock, the
        # square footages cannot be summed to calculate the master microsegment
        # stock values (as is the case when using no. of units).  For example,
        # 1000 Btu of cooling and heating in the same 1000 square foot building
        # should not yield 2000 total square feet of stock in the master
        # microsegment even though there are two contributing microsegments in
        # this case (heating and cooling). This is remedied by dividing summed
        # square footage values by (# valid key chains / (# czones * # bldg
        # types)), where the numerator refers to the number of full dict key
        # chains that contributed to the mseg stock, energy, and cost calcs,
        # and the denominator reflects the breakdown of square footage by
        # climate zone and building type. Note that cost information is based
        # on competed stock and must be divided in the same manner (see
        # reduce_sqft_stock function).
        if sqft_subst == 1:
            # Create a factor for reduction of msegs with sq.ft. stock
            if key_chain_ct != 0:
                reduce_factor = key_chain_ct / (len(ms_lists[0]) *
                                                len(ms_lists[1]))
            else:
                raise(ValueError('No valid key chains discovered for sq.ft. \
                                  stock and cost division operation!'))
            mseg_master = self.reduce_sqft_stock_cost(mseg_master,
                                                      reduce_factor)
        else:
            reduce_factor = 1

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
                        # Note: the below lines check to see if one, both, or
                        # neither of the key items being added is a list, and
                        # performs the addition accordingly.  Key values
                        # will be lists in cases where probability distrbutions
                        # were specified for measure cost/performance inputs
                        if type(dict1[k]) != list and type(dict2[k2]) != list:
                                dict1[k] = dict1[k] + dict2[k2]
                        elif isinstance(dict1[k], list) and \
                                isinstance(dict2[k2], list):
                                dict1[k] = [x + y for (x, y)
                                            in zip(dict1[k], dict2[k2])]
                        elif isinstance(dict1[k], list) and \
                                type(dict2[k2]) != list:
                                dict1[k] = [x + dict2[k2] for x
                                            in dict1[k]]
                        elif type(dict1[k]) != list and \
                                isinstance(dict2[k2], list):
                                dict1[k] = [y + dict1[k] for y
                                            in dict2[k2]]
                        else:
                            raise(ValueError(('Key values to be added are not \
                                              of expected types!')))
            else:
                raise(KeyError('Add dict keys do not match!'))
        return dict1

    def reduce_sqft_stock_cost(self, dict1, reduce_factor):
        """ Divide "stock" and "stock cost" information by a given factor to
        handle special case when sq.ft. is used as stock """
        for (k, i) in dict1.items():
            # Do not divide any energy or carbon information
            if (k == "energy" or k == "carbon"):
                    continue
            else:
                    if isinstance(i, dict):
                        self.reduce_sqft_stock_cost(i, reduce_factor)
                    else:
                        if isinstance(dict1[k], list):  # Cost distrib. case
                            dict1[k] = [x / reduce_factor for x in dict1[k]]
                        else:
                            dict1[k] = dict1[k] / reduce_factor
        return dict1

    def rand_list_gen(self, distrib_info, nsamples):
        """ Given input distribution type, parameters, and sample N information,
        generate list of N randomly sampled values from that distribution """

        # Generate string to pair with "numpy.random" call
        if len(distrib_info) == 3 and distrib_info[0] in ["normal",
                                                          "lognormal",
                                                          "uniform",
                                                          "gamma"]:
            vals = str(distrib_info[1]) + ',' + str(distrib_info[2]) + ',' + \
                str(nsamples)
        elif len(distrib_info) == 3 and distrib_info[0] == "weibull":
            vals = str(distrib_info[1]) + ',' + str(nsamples)
        elif len(distrib_info) == 4 and distrib_info[0] == "triangular":
            vals = str(distrib_info[1]) + ',' + str(distrib_info[2]) + ',' + \
                str(distrib_info[3]) + ',' + str(nsamples)
        else:
            raise(ValueError("Unsupported input distribution specification!"))

        # Pair generated string with "numpy.random" call
        rand_string = 'numpy.random.' + distrib_info[0] + '(' + vals + ')'

        # Evaluate "numpy.random" call
        if distrib_info[0] != "weibull":
            rand_list = eval(rand_string)
        else:  # Apply scaling factor here for Weibull distrib. case
            rand_list = distrib_info[2] * eval(rand_string)

        # Remove any sampled values below zero if they exist
        if any(rand_list < 0):
            rand_list = rand_list[rand_list >= 0]

        # Return the randomly sampled values as a list
        return list(rand_list)

    def partition_microsegment(self, mseg_stock, mseg_energy, mseg_carb,
                               rel_perf, base_cost, cost_meas, cost_energy,
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
                stock_compete_cost_base[yr] = stock_compete[yr] * base_cost

                # Update "competed" stock cost (measure)
                if isinstance(cost_meas, list):  # Measure stock cost distrib.
                    stock_compete_cost_meas[yr] = [x * stock_compete[yr]
                                                   for x in cost_meas]
                else:  # Measure stock cost point value
                    stock_compete_cost_meas[yr] = stock_compete[yr] * cost_meas

                # Update "competed" energy and carbon costs (baseline)
                energy_compete_cost[yr] = energy_compete[yr] * cost_energy[yr]
                carb_compete_cost[yr] = carb_compete[yr] * cost_carb[yr]

                # Update "efficient" energy and carbon and associated costs
                if isinstance(rel_perf, list):  # Relative performance distrib.
                    energy_eff[yr] = [x * energy_compete[yr] for x in rel_perf]
                    energy_eff_cost[yr] = [x * cost_energy[yr] for x in
                                           energy_eff[yr]]
                    carb_eff[yr] = [x * carb_compete[yr] for x in rel_perf]
                    carb_eff_cost[yr] = [x * cost_carb[yr] for x in
                                         carb_eff[yr]]
                else:  # Relative performance point value
                    energy_eff[yr] = energy_compete[yr] * (rel_perf)
                    energy_eff_cost[yr] = energy_eff[yr] * cost_energy[yr]
                    carb_eff[yr] = carb_compete[yr] * (rel_perf)
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

    def calc_metrics(self):
        """ Calculate measure decision making metrics using competed
        microsegment """
        pass


# Engine runs active measure adoption
class Engine(object):

    def __init__(self, measure_objects):
        self.measure_objs = measure_objects

    def adopt_active(self, mseg_in, base_costperf_in, adopt_scheme,
                     decision_rule):
        """ Run adoption scheme on active measures only """
        for m in self.measure_objs:
            if m.active == 1:
                # Find master microsegment and partitions
                m.mseg_master_find_partition(mseg_in, base_costperf_in,
                                             adopt_scheme)
                # Update cost/savings outcomes based on competed microsegment
                m.calc_metrics()
        # Eventually adopt measures here using updated measure decision info.


def main():

    # Import measures/microsegments files
    with open(measures_file, 'r') as mjs:
        measures_input = json.load(mjs)

    with open(microsegments_file, 'r') as msjs:
        microsegments_input = json.load(msjs)

    with open(mseg_base_costperf_info, 'r') as bjs:
        base_costperf_info_input = json.load(bjs)

    # Create measures objects list from input measures JSON
    measures_objlist = []

    for mi in measures_input:
        measures_objlist.append(Measure(**mi))

    a_run = Engine(measures_objlist)
    a_run.adopt_active(microsegments_input, base_costperf_info_input,
                       adopt_scheme, decision_rule)

if __name__ == '__main__':
    main()
