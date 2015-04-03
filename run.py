#!/usr/bin/env python3
import json

# Define measures/microsegments files
measures_file = "measures.json"
microsegments_file = "microsegments_out.json"

# Import measures/microsegments files
with open(measures_file, 'r') as mjs:
        measures_input = json.load(mjs)

with open(microsegments_file, 'r') as msjs:
        microsegments_input = json.load(msjs)


# Define class for measure objects
class Measure(object):

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    # Find appropriate measure microsegment
    def find_microsegment(self):
        pass

    # Partition microsegment to find "competed" and "non-competed"
    # stock
    def partition_microsegment(self):
        pass


# Engine runs active measure adoption
class Engine(object):

    def __init__(self, active_measure):
        pass

    # Adopt active measure using input rule
    def adopt_measures(self, adopt_rule):
        pass

# Create measures objects list from input measures JSON
measures_objlist = []

for mi in measures_input:
    measures_objlist.append(Measure(**mi))
