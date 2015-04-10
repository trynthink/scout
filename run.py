#!/usr/bin/env python3
import json
import itertools
import copy

# Define measures/microsegments files
measures_file = "measures.json"
microsegments_file = "microsegments_out_test.json"

# User-specified inputs (draw from GUI?)
active_measures = []  # For now
adopt_scheme = 'Technical potential'
decision_rule = 'NA'


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
        self.mseg_units = None  # Units (whole mseg)
        self.mseg_energy_unit = None  # Energy/unit (whole mseg)
        self.compete_energy = None  # Energy (competed mseg)
        self.compete_units = None  # Units (competed mseg)
        self.compete_energy_unit = None  # Energy/unit (competed mseg)
        # Initialize relative improvement attributes
        self.esavings = None  # Total energy savings
        self.esavings_unit = None  # Energy savings/unit
        self.carbsavings = None  # Total CO2 savings
        self.carbsavings_unit = None  # CO2 savings/unit
        # Initialize decision making attributes
        self.irr = None  # Internal rate of return
        self.payback = None  # Simple payback
        self.initexpend_pct = None  # Initial expenditure as % of budget
        self.cce = None  # Cost of Conserved Energy
        self.ccc = None  # Cost of Conserved Carbon
        # Other attributes to be added as needed

    def find_master_microsegment(self, mseg_in):
        """ Given an input measure with microsegment selection information and a
        microsegments dict with AEO stock/energy consumption information, find
        the master microsegment for the measure (maximum possible stock &
        energy markets for the measure) """

        # Initialize master microsegment dict and a variable that will indicate
        # the first addition to this dict (special handling)
        mseg_total = {"stock": None, "energy": None}
        key_init = 0
        # Create a variable that will indicate the use of square footage for
        # master microsegment stock
        sqft_subst = 0
        # Create a list of lists where each list has key information for
        # one of the microsegment levels. Use this list to find all possible
        # microsegment key chains and store each in a tuple (i.e. ("new
        # england", "single family home", "natural gas", "water heating")).
        # Add in "demand" and "supply keys where needed (heating, secondary
        # heating, cooling end uses)
        htcl_enduse_ct = 0
        if isinstance(self.end_use, list) is False:
            self.end_use = [self.end_use]
        for eu in self.end_use:
            if eu == "heating" or eu == "secondary heating" or eu == "cooling":
                htcl_enduse_ct += 1
        if (htcl_enduse_ct > 0):
            ms_lists = [self.climate_zone, self.bldg_type, self.fuel_type,
                        self.end_use, self.technology_type, self.technology]
        else:
            ms_lists = [self.climate_zone, self.bldg_type, self.fuel_type,
                        self.end_use, self.technology]
        # Ensure that every "ms_lists" element is itself a list
        for x in range(0, len(ms_lists)):
            if isinstance(ms_lists[x], list) is False:
                ms_lists[x] = [ms_lists[x]]
        # Find all possible microsegment key chains
        ms_iterable = list(itertools.product(*ms_lists))

        # Loop through the discovered key chains to find stock/energy
        # information in "mseg_in" for each microsegment that contributes to
        # the master microsegment
        for mskeys in ms_iterable:
            # Make a new copy of "mseg_in" for use in each loop through the
            # discovered key chains (otherwise the initial dict is reduced with
            # each loop, yielding errors).  Here, we also initialize a separate
            # dict for use in grabbing sqft. info., which will serve as the
            # "stock" for microsegments with no number of units information
            mseg_dict = copy.deepcopy(mseg_in)
            mseg_dict_sqft = copy.deepcopy(mseg_in)
            # Loop recursively through input dict copy, moving down key chain
            for i in range(0, len(mskeys)):  # Check for key in dict level
                if mskeys[i] in mseg_dict.keys():
                    mseg_dict = mseg_dict[mskeys[i]]
                else:  # If no key match, break the loop
                    break
                # For sq.ft. info., only move two levels down the dict
                # (sq.ft. is only broken out by census division and bldg. type)
                if i < 2:
                    mseg_dict_sqft = mseg_dict_sqft[mskeys[i]]
            # If the current loop didn't make it down to the "stock" and
            # "energy" key level (because of mismatch somewhere along the key
            # chain), move to the next loop
            if "stock" not in list(mseg_dict.keys()):
                pass
            # If the loop did make it to the "stock" and "energy" key level,
            # add this information to existing master microsegment dict. If
            # this is the first addition, append the full set of {"year": val}
            # pairs; otherwise, add to existing values for each year.
            else:
                # If number of units stock info. is unavailable, use sq.
                # footage info. from "mseg_dict_sqft" as stock.
                if mseg_dict["stock"] == "NA":
                    sqft_subst = 1
                    add_stock = mseg_dict_sqft["square footage"]
                else:
                    add_stock = mseg_dict["stock"]
                add_energy = mseg_dict["energy"]

                if key_init == 0:
                    key_init = 1
                    mseg_total["stock"] = add_stock
                    mseg_total["energy"] = add_energy
                else:
                    for (key1, key2) in zip(mseg_total["stock"].keys(),
                                            mseg_total["energy"].keys()):
                        mseg_total["stock"][key1] = mseg_total["stock"][key1] + \
                            add_stock[key1]
                        mseg_total["energy"][key2] = mseg_total["energy"][key2] + \
                            add_energy[key2]

        # In microsegments where square footage must be used as stock, the
        # square footages cannot be summed to calculate the master microsegment
        # stock values (as is the case when using no. of units).  For example,
        # 1000 Btu of cooling and heating in the same 1000 square foot building
        # should not yield 2000 total square feet of stock in the master
        # microsegment even though there are two contributing microsegments in
        # this case (heating and cooling). This is remedied by dividing summed
        # sq. footage values by (# technologies * # end uses), including only
        # technologies/end uses that contribute to the square footage sums.
        if sqft_subst == 1:
            for x in mseg_total["stock"].keys():
                mseg_total["stock"][str(x)] = (mseg_total["stock"][str(x)] /
                                               (len(ms_lists[-1]) *
                                                htcl_enduse_ct))

        # Return the master microsegment
        return mseg_total

    def partition_microsegment(self, adopt_scheme):
        """ Partition microsegment to find "competed" and "non-competed"
        stock """
        pass

    def calc_metrics(self):
        """ Calculate measure decision making metrics using competed
        microsegment """
        pass


# Engine runs active measure adoption
class Engine(object):

    def __init__(self, measure_objects):
        self.measure_objs = measure_objects

    def adopt_active(self, adopt_scheme, decision_rule, mseg_in):
        """ Run adoption scheme on active measures only """
        for m in self.measure_objs:
            if m.active == 1:
                # Find microsegment
                m.find_master_microsegment(mseg_in)
                # Find competed microsegment
                m.partition_microsegment(adopt_scheme)
                # Update cost/savings outcomes based on competed microsegment
                m.calc_metrics()
        # Eventually adopt measures here using updated measure decision info.


def main():

    # Import measures/microsegments files
    with open(measures_file, 'r') as mjs:
        measures_input = json.load(mjs)

    with open(microsegments_file, 'r') as msjs:
        microsegments_input = json.load(msjs)

    # Create measures objects list from input measures JSON
    measures_objlist = []

    for mi in measures_input:
        measures_objlist.append(Measure(**mi))

    a_run = Engine(measures_objlist)
    a_run.adopt_active(adopt_scheme, decision_rule, microsegments_input)

if __name__ == '__main__':
    main()
