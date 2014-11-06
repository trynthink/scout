#!/usr/bin/env python3

# Consider the first paragraph of https://docs.python.org/3.4/tutorial/classes.html#random-remarks
# We thus need to establish a common naming convention for data and methods in objects

# Define measure class

class Measure:
	def __init__(self,cost,_cost,energy_eff,_energy_eff,market_entry_year,
		product_lifetime,_product_lifetime, end_use,fuel_type,equip_class,
		bldg_type,climate_zone):

		self.cost = cost
		self.energy_eff = energy_eff
		self.market_entry_year = market_entry_year
		self.product_lifetime = product_lifetime
		#finish this
		#confirm correct approach to data assignment

	# What can be done with/to measures?
