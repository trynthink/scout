#!/usr/bin/env python3

"""Python script to automate the baseline calculator of Scout."""

#import json

"""Read in the test JSON"""
#with open('test_json_traverse.json', 'r') as f:
    #test_file = json.load(f)

#Computes sum of energy values for electric heating 
def sum_electric_heating(tech_energy1, tech_energy2, tech_energy3):
	# Calculate electric heating sum for energy values
	electric_sum = tech_energy1 + tech_energy2 + tech_energy3

	return electric_sum

# Computes sum of energy values for electric refrigeration 
def sum_refrig(refrig_energy1, refrig_energy2):
	""" Each refrig_energy represents the different refrigeration values from 
	test_json_traverse.json for AIA_CZ1 and AIA_CZ2 for a one year""" 

	refrig_sum = refrig_energy1 + refrig_energy2 
	return refrig_sum

# Aggregates electric refrigeration based on year
def aggregate_refrig(energy_2015_val1, energy_2015_val2, energy_2015_val3
	,energy_2015_val4,energy_2015_val5,energy_2015_val6):
		
	refrig_tot_sum_2015 = (energy_2015_val1 + energy_2015_val2  + energy_2015_val3 + energy_2015_val4 + energy_2015_val5 + energy_2015_val6)
	
	return refrig_tot_sum_2015

# Aggregates electric heating based on year
def aggregate_heating(resist_energy, ASHP_energy, GSHP_energy):
	heating_tot_sum_2015 = (resist_energy + ASHP_energy  + GSHP_energy)
	
	return heating_tot_sum_2015

# Read in EIA data


# Functions needed
# To traverse the test json structure 

# To pull out given values

# To replicate json structure and recursively works to reach file endpoint i.e. = end uses, year, value

# Once grab endpoint, then acts on file location = use previous sum functiona

# Runs on the command line
#if __name__ == '__main__':
  #  main()