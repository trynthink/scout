#!/usr/bin/env python3

""" Tests for commercial microsegment data processing code """

# There are two files to be handled with the commercial microsegment data
# ksdout and kdbout

# ksdout has seven categories that aren't well defined
# r - census division (probably) - 1,...,9
# b - building type (probably) - 1,...,11
# s - end use "service" - 1,...,6
# f - fuel (1 = electricity, 2 = natural gas, 3 = distillate)
# d - dtype (probably) (new, replacement, surviving)
# t - technology ID number
# v - vintage (probably, no idea what vintage is though)

# kdbout has a bunch of different information in it
# SurvFloorTotal
# CMNewFloorSpace
# EndUseConsump
# MiscElConsump
# FuelPrice(87$)
# HeatingFacExist
# HeatingFacNew
# CoolingFacExist
# CoolingFacNew

# From ksdout, these are v 1 through 7 and each one is d 1 through 3

# "rooftop_ASHP-heat 2003 installed base       "
# "rooftop_ASHP-heat 2003 installed base       "
# "rooftop_ASHP-heat 2003 installed base       "
# "rooftop_ASHP-heat 2007 installed base       "
# "rooftop_ASHP-heat 2007 installed base       "
# "rooftop_ASHP-heat 2007 installed base       "
# "rooftop_ASHP-heat 2010 current standard/ typ"
# "rooftop_ASHP-heat 2010 current standard/ typ"
# "rooftop_ASHP-heat 2010 current standard/ typ"
# "rooftop_ASHP-heat placeholder to reconcile h"
# "rooftop_ASHP-heat placeholder to reconcile h"
# "rooftop_ASHP-heat placeholder to reconcile h"
# "rooftop_ASHP-heat 2010 high                 "
# "rooftop_ASHP-heat 2010 high                 "
# "rooftop_ASHP-heat 2010 high                 "
# "rooftop_ASHP-heat 2020 typical              "
# "rooftop_ASHP-heat 2020 typical              "
# "rooftop_ASHP-heat 2020 typical              "
# "rooftop_ASHP-heat 2020 high                 "
# "rooftop_ASHP-heat 2020 high                 "
# "rooftop_ASHP-heat 2020 high                 "
