#!/usr/bin/env python3
import json

# Define measures/microsegments files
measures_file = "measures.json"
microsegments_file = "microsegments_out_test.json"

# Import measures/microsegments files
with open(measures_file, 'r') as mjs:
        measures_input = json.load(mjs)

with open(microsegments_file, 'r') as msjs:
        microsegments_input = json.load(msjs)

# User-specified inputs (draw from GUI?)
active_measures = ['Demonstrate and deploy minisplit heat pumps in homes']
adopt_scheme = 'Technical potential'
decision_rule = 'Economic'  # Just one possible example


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

    # Find appropriate measure microsegment
    def find_microsegment(self, microsegments_input):
        pass

    # Partition microsegment to find "competed" and "non-competed"
    # stock
    def partition_microsegment(self, adopt_scheme):
        pass

    # Calculate measure decision making metrics using competed microsegment
    def calc_metrics(self):
        pass


# Engine runs active measure adoption
class Engine(object):

    def __init__(self, measure_objects):
        self.measure_objs = measure_objects

    # Run adoption scheme on active measures only
    def adopt_active(self, adopt_scheme, decision_rule):
        for m in self.measure_objs:
            if m.active == 1:
                # Find microsegment
                m.find_microsegment(microsegments_input)
                # Find competed microsegment
                m.partition_microsegment(adopt_scheme)
                # Update cost/savings outcomes based on competed microsegment
                m.calc_metrics()
        # Eventually adopt measures here using updated measure decision info.


def main():

    # Create measures objects list from input measures JSON
    measures_objlist = []

    for mi in measures_input:
        measures_objlist.append(Measure(**mi))

    a_run = Engine(measures_objlist)
    a_run.adopt_active(adopt_scheme, decision_rule)

if __name__ == '__main__':
    main()
