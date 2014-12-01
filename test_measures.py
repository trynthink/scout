#!/usr/bin/env python3

"""Test JSON measures for validity prior to importing them"""

# Import needed packages
import json
from pprint import pprint # for testing


# Open the database of measures for reading
json_file = open('measures.json') # need to generalize this to find the json file??

# run a json syntax validator first?

# Read JSON file
measures = json.load(json_file)
pprint(measures) # temporary

# Close JSON file
json_file.close()

# confirm microsegment data
######
###### not entirely sure how this checking should be tiered, since most categories depend on at least one other
######
	# confirm valid end use
		# confirm valid equipment class(es) given end use
	# confirm valid fuel type (for end use)
	# confirm 

# confirm presence of needed support fields for each category
	# sources
	# units