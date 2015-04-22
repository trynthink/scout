#!/usr/bin/env python3
import json
import itertools
import copy
import re

# Define measures/microsegments files
measures_file = "measures.json"
microsegments_file = "microsegments_out_test.json"
mseg_base_costperf_info = "microsegments_base_costperf.json"  # To be developed

# User-specified inputs (placeholders for now, eventually draw from GUI?)
active_measures = []
adopt_scheme = 'Technical potential'
decision_rule = 'NA'

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

        # Initialize master stock, energy, and cost information dict
        mseg_master = {"stock": {"total": None, "competed": None},
                       "energy": {"total": None, "competed": None,
                                  "efficient": None},
                       "cost": {"baseline": None, "measure": None}}

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
            # Initialize performance/cost and units (* could each be dict)
            perf_meas = self.energy_efficiency
            cost_meas = self.installed_cost
            perf_units = self.energy_efficiency_units
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
                # Determine relative measure performance after checking for
                # consistent baseline/measure performance and cost units
                if base_costperf["performance"]["units"] == perf_units and \
                   base_costperf["cost"]["units"] == cost_units:
                    # Relative performance calculation depends on tech. case
                    # (i.e. COP  of 4 is higher rel. performance than COP 3,
                    # (but 1 ACH50 is higher rel. performance than 13 ACH50)
                    if perf_units not in inverted_relperf_list:
                        rel_perf = (base_costperf["performance"]["value"] /
                                    perf_meas)
                    else:
                        rel_perf = (perf_meas /
                                    base_costperf["performance"]["value"])
                    base_cost = base_costperf["cost"]["value"]
                else:
                    raise(KeyError('Inconsistent performance or cost units!'))

                # Update total stock and energy information
                if mseg["stock"] == "NA":  # Use sq.ft. in absence of no. units
                    sqft_subst = 1
                    add_stock = mseg_sqft["square footage"]
                else:
                    add_stock = mseg["stock"]
                add_energy = mseg["energy"]

                # Update competed and efficient stock and energy info.
                # and competed cost info. based on adoption scheme
                [add_compete_stock, add_compete_energy, add_efficient, add_cost] = \
                    self.partition_microsegment(add_stock, add_energy,
                                                rel_perf, base_cost,
                                                cost_meas, adopt_scheme)

                # Combine stock/energy/cost updating info. into a dict
                add_dict = {"stock": {"total": add_stock, "competed":
                            add_compete_stock}, "energy": {"total": add_energy,
                            "competed": add_compete_energy, "efficient":
                                                            add_efficient},
                            "cost": {"baseline": add_cost["baseline"],
                                     "measure": add_cost["measure"]}}

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

        # Return the final master microsegment
        return mseg_master

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
                        dict1[k] = dict1[k] + dict2[k2]
            else:
                raise(KeyError('Add dict keys do not match!'))
        return dict1

    def reduce_sqft_stock_cost(self, dict1, reduce_factor, loop=0):
        """ Divide "stock" and "cost" information by a given factor to
        handle special case when sq.ft. is used as stock """

        if loop == 0 and sorted(dict1.keys()) == ['cost', 'energy', 'stock'] or \
           loop > 0:
            loop += 1
            for (k, i) in dict1.items():
                if k == "energy":
                    continue
                else:
                    if isinstance(i, dict):
                            self.reduce_sqft_stock_cost(i, reduce_factor, loop)
                    else:
                        dict1[k] = dict1[k] / reduce_factor
        else:
            raise(KeyError('Incorrect keys found in mseg_master dict!'))

        return dict1

    def partition_microsegment(self, mseg_stock, mseg_energy, rel_perf,
                               base_cost, cost_meas, adopt_scheme):
        """ Partition microsegment to find "competed" stock and energy
        consumption as well as "efficient" energy consumption (representing
        consumption under the measure).  Also find the total cost of the
        competed stock for baseline and measure cost levels """

        # Initialize efficient dict
        mseg_efficient = dict.fromkeys(mseg_energy)

        # Determine whether this is a technical potential calculation
        tp = re.search('Technical potential', adopt_scheme, re.IGNORECASE)

        # If a technical potential calculation, "competed" = "total" mseg
        if tp:
            mseg_competed_stock = mseg_stock
            mseg_competed_energy = mseg_energy
            for yr in mseg_competed_energy.keys():
                mseg_efficient[yr] = mseg_competed_energy[yr] * (rel_perf)
        else:  # The below few lines are temporary
            mseg_competed_stock = None
            mseg_competed_energy = None
            mseg_efficient = None

        # Find base and measure cost of competed stock (cost/stock * stock).
        # Initialize these as simply the competed stock, then multiply by
        # by either the baseline or measure cost/stock to finalize.
        if mseg_competed_stock is not None:  # If statement is temporary
            mseg_competed_cost = {"baseline":
                                  dict.fromkeys(mseg_competed_stock.keys()),
                                  "measure":
                                  dict.fromkeys(mseg_competed_stock.keys())}
            for ctype in mseg_competed_cost.keys():
                if ctype == "baseline":
                    multiplier = base_cost
                else:
                    multiplier = cost_meas
                for yr in mseg_competed_cost[ctype].keys():
                    mseg_competed_cost[ctype][yr] = mseg_competed_stock[yr] * \
                        multiplier
        else:
            mseg_competed_cost = None

        # Return updated stock, energy, and cost information
        return [mseg_competed_stock, mseg_competed_energy, mseg_efficient,
                mseg_competed_cost]

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
