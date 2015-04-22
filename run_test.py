#!/usr/bin/env python3

""" Tests for running the engine """

# Import code to be tested
import run

# Import needed packages
import unittest
import numpy
import copy


class TestMeasureInit(unittest.TestCase):
    """ Ensure that measure attributes are correctly initiated """

    # Sample measure for use in testing attributes * NOTE:
    # this is duplicated later in another test, look into how to combine?
    sample_measure = {"name": "sample measure 1",
                      "end_use": ["heating", "cooling"],
                      "fuel_type": "electricity (grid)",
                      "technology_type": "supply",
                      "technology": ["boiler (electric)",
                                     "ASHP", "GSHP", "room AC"],
                      "bldg_type": "single family home",
                      "climate_zone": ["AIA_CZ1", "AIA_CZ2"]}

    def test_attributes(self):
        # Create an instance of the object using sample_measure
        measure_instance = run.Measure(**self.sample_measure)
        # Put object attributes into a dict
        attribute_dict = measure_instance.__dict__
        # Loop through sample measure keys and compare key values
        # to those from the "attribute_dict"
        for key in self.sample_measure.keys():
            self.assertEqual(attribute_dict[key],
                             self.sample_measure[key])
        # Check to see that sample measure is correctly identified
        # as inactive
        self.assertEqual(measure_instance.active, 0)


class AddKeyValsTest(unittest.TestCase):
    """ Test the operation of the add_keyvals function to verify it
    adds together dict items correctly """

    # Sample measure for use in testing add_keyvals
    sample_measure = {"name": "sample measure 1",
                      "end_use": ["heating", "cooling"],
                      "fuel_type": "electricity (grid)",
                      "technology_type": "supply",
                      "technology": ["boiler (electric)",
                                     "ASHP", "GSHP", "room AC"],
                      "bldg_type": "single family home",
                      "climate_zone": ["AIA_CZ1", "AIA_CZ2"]}

    # Create a measure instance to use in the testing
    measure_instance = run.Measure(**sample_measure)

    # 1st dict to be entered into the "ok" test of the function
    base_dict1 = {"level 1a":
                  {"level 2aa":
                      {"2009": 2, "2010": 3},
                   "level2ab":
                      {"2009": 4, "2010": 5}},
                  "level 1b":
                  {"level 2ba":
                      {"2009": 6, "2010": 7},
                   "level2bb":
                      {"2009": 8, "2010": 9}}}

    # 1st dict to be entered into the "fail" test of the function
    base_dict2 = copy.deepcopy(base_dict1)

    # 2nd dict to be added to "base_dict1" in the "ok" test of the function
    ok_add_dict2 = {"level 1a":
                    {"level 2aa":
                        {"2009": 2, "2010": 3},
                     "level2ab":
                        {"2009": 4, "2010": 5}},
                    "level 1b":
                    {"level 2ba":
                        {"2009": 6, "2010": 7},
                     "level2bb":
                        {"2009": 8, "2010": 9}}}

    # 2nd dict to be added to "base_dict2" in the "fail" test of the function
    fail_add_dict2 = {"level 1a":
                      {"level 2aa":
                          {"2009": 2, "2010": 3},
                       "level2ab":
                          {"2009": 4, "2010": 5}},
                      "level 1b":
                      {"level 2ba":
                          {"2009": 6, "2010": 7},
                       "level2bb":
                          {"2009": 8, "2011": 9}}}

    # Correct output of the "ok" test to check against
    ok_out = {"level 1a":
              {"level 2aa":
                  {"2009": 4, "2010": 6},
               "level2ab":
                  {"2009": 8, "2010": 10}},
              "level 1b":
              {"level 2ba":
                  {"2009": 12, "2010": 14},
               "level2bb":
                  {"2009": 16, "2010": 18}}}

    # Create a routine for checking equality of a dict * NOTE:
    # this is duplicated later in another test, look into how to combine?
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                self.assertAlmostEqual(dict1[k], dict2[k2], places=2)

    # Test the "ok" function output
    def test_ok_add(self):
        dict1 = self.measure_instance.add_keyvals(self.base_dict1,
                                                  self.ok_add_dict2)
        dict2 = self.ok_out
        self.dict_check(dict1, dict2)

    # Test the "fail" function output
    def test_fail_add(self):
        with self.assertRaises(KeyError):
            self.measure_instance.add_keyvals(self.base_dict2,
                                              self.fail_add_dict2)


class ReduceSqftStockCostTest(unittest.TestCase):
    """ Test the operation of the reduce_sqft_stock_cost function to verify
    that it properly divides dict key values by a given factor (used in special
    case where square footage is used as the microsegment stock) """

    # Sample measure for use in testing add_keyvals
    sample_measure = {"name": "sample measure 1",
                      "end_use": ["heating", "cooling"],
                      "fuel_type": "electricity (grid)",
                      "technology_type": "supply",
                      "technology": ["boiler (electric)",
                                     "ASHP", "GSHP", "room AC"],
                      "bldg_type": "single family home",
                      "climate_zone": ["AIA_CZ1", "AIA_CZ2"]}

    # Create a measure instance to use in the testing
    measure_instance = run.Measure(**sample_measure)

    # Initialize a factor to divide input dict key values by
    test_factor = 4

    # Base input dict to be divided by test_factor in "ok" test
    base_dict = {"stock":
                 {"total":
                     {"2009": 100, "2010": 200},
                  "competed":
                      {"2009": 300, "2010": 400}},
                 "energy":
                 {"total":
                     {"2009": 500, "2010": 600},
                  "competed":
                     {"2009": 700, "2010": 800},
                  "efficient":
                     {"2009": 700, "2010": 800}},
                 "cost":
                 {"baseline":
                     {"2009": 900, "2010": 1000},
                  "measure":
                     {"2009": 1100, "2010": 1200}}}

    # Base input dict that should yield KeyError in "fail" test (one of the top
    # level keys ("energetics") is incorrect)
    fail_dict = {"stock":
                 {"total":
                     {"2009": 100, "2010": 200},
                  "competed":
                      {"2009": 300, "2010": 400}},
                 "energetics":
                 {"total":
                     {"2009": 500, "2010": 600},
                  "competed":
                     {"2009": 700, "2010": 800},
                  "efficient":
                     {"2009": 700, "2010": 800}},
                 "cost":
                 {"baseline":
                     {"2009": 900, "2010": 1000},
                  "measure":
                     {"2009": 1100, "2010": 1200}}}

    # Correct output of the "ok" test to check against
    ok_out = {"stock":
              {"total":
                  {"2009": 25, "2010": 50},
               "competed":
                   {"2009": 75, "2010": 100}},
              "energy":
              {"total":
                  {"2009": 500, "2010": 600},
               "competed":
                  {"2009": 700, "2010": 800},
               "efficient":
                  {"2009": 700, "2010": 800}},
              "cost":
              {"baseline":
                  {"2009": 225, "2010": 250},
               "measure":
                  {"2009": 275, "2010": 300}}}

    # Create a routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                self.assertAlmostEqual(dict1[k], dict2[k2], places=2)

    # Test the "ok" function output
    def test_ok_add(self):
        dict1 = self.measure_instance.reduce_sqft_stock_cost(self.base_dict,
                                                             self.test_factor)
        dict2 = self.ok_out
        self.dict_check(dict1, dict2)

    # Test the "fail" function output
    def test_fail_add(self):
        with self.assertRaises(KeyError):
            self.measure_instance.reduce_sqft_stock_cost(self.fail_dict,
                                                         self.test_factor)


class PartitionMicrosegmentTest(unittest.TestCase):
    """ Test the operation of the partition_microsegment function to verify
    that it properly partitions an input microsegment to yield the required
    competed stock/energy/cost and energy efficient consumption information """

    # Sample measure for use in testing add_keyvals
    sample_measure = {"name": "sample measure 1",
                      "end_use": ["heating", "cooling"],
                      "fuel_type": "electricity (grid)",
                      "technology_type": "supply",
                      "technology": ["boiler (electric)",
                                     "ASHP", "GSHP", "room AC"],
                      "bldg_type": "single family home",
                      "climate_zone": ["AIA_CZ1", "AIA_CZ2"]}

    # Create a measure instance to use in the testing
    measure_instance = run.Measure(**sample_measure)

    # Set sample stock and energy inputs for testing
    test_stock = [{"2009": 100, "2010": 200, "2011": 300},
                  {"2025": 400, "2028": 500, "2035": 600},
                  {"2020": 700, "2021": 800, "2022": 900}]
    test_energy = [{"2009": 10, "2010": 20, "2011": 30},
                   {"2025": 40, "2028": 50, "2035": 60},
                   {"2020": 70, "2021": 80, "2022": 90}]

    # Set sample base and measure costs to use in the testing
    test_base_cost = [10, 20, 30]
    test_cost_meas = [20, 30, 40]

    # Set two alternative schemes to use in the testing,
    # where the first should yield a full list of outputs
    # and the second should yield a list with blank elements
    test_schemes = ['Technical potential', 'Undefined']

    # Set a relative performance list that should yield a
    # full list of valid outputs
    ok_relperf = [0.30, 0.15, 0.75]

    # Correct output of the "ok" function test
    ok_out = [[{"2009": 100, "2010": 200, "2011": 300},
               {"2009": 10, "2010": 20, "2011": 30},
               {"2009": 3, "2010": 6, "2011": 9},
               {"baseline":
                {"2009": 1000, "2010": 2000, "2011": 3000},
                "measure":
                {"2009": 2000, "2010": 4000, "2011": 6000}}],
              [{"2025": 400, "2028": 500, "2035": 600},
               {"2025": 40, "2028": 50, "2035": 60},
               {"2025": 6, "2028": 7.5, "2035": 9},
               {"baseline":
                {"2025": 8000, "2028": 10000, "2035": 12000},
                "measure":
                {"2025": 12000, "2028": 15000, "2035": 18000}}],
              [{"2020": 700, "2021": 800, "2022": 900},
               {"2020": 70, "2021": 80, "2022": 90},
               {"2020": 52.5, "2021": 60, "2022": 67.5},
               {"baseline":
               {"2020": 21000, "2021": 24000, "2022": 27000},
                "measure":
                {"2020": 28000, "2021": 32000, "2022": 36000}}]]

    # Correct output of the "blank" function test
    blank_out = [None, None, None, None]  # For now (pass)

    # Create a routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                self.assertAlmostEqual(dict1[k], dict2[k2], places=2)

    # Test the "ok" function output
    def test_ok(self):
        for elem in range(0, len(self.test_stock)):
            lists1 = self.measure_instance.partition_microsegment(
                self.test_stock[elem],
                self.test_energy[elem],
                self.ok_relperf[elem],
                self.test_base_cost[elem],
                self.test_cost_meas[elem],
                self.test_schemes[0])

            lists2 = self.ok_out[elem]

            for elem2 in range(0, len(lists1)):
                self.dict_check(lists1[elem2], lists2[elem2])

    # Test the "blank" function output
    def test_blank(self):
        for elem in range(0, len(self.test_stock)):
            lists1 = self.measure_instance.partition_microsegment(
                self.test_stock[elem],
                self.test_energy[elem],
                self.ok_relperf[elem],
                self.test_base_cost[elem],
                self.test_cost_meas[elem],
                self.test_schemes[1])

            lists2 = self.blank_out

            self.assertEqual(lists1, lists2)


class FindPartitionMasterMicrosegmentTest(unittest.TestCase):
    """ Test the operation of the mseg_find_partition function to
    verify measure microsegment-related attribute inputs yield expected master
    microsegment output """

    # Sample input dict of microsegment performance/cost info. to reference in
    # generating and partitioning master microsegments for a measure
    sample_basein = {
        "AIA_CZ1": {
            "single family home": {
                "electricity (grid)": {
                    "heating": {"demand": {"windows conduction": {
                                           "performance": {"value": 1,
                                                           "units": "R Value"},
                                           "cost": {"value": 1,
                                                    "units": "2014$/sf"}},
                                           "windows solar": {
                                           "performance": {"value": 2,
                                                           "units": "SHGC"},
                                           "cost": {"value": 2,
                                                    "units": "2014$/sf"}}},
                                "supply": {"boiler (electric)": {
                                           "performance": {"value": 2,
                                                           "units": "COP"},
                                           "cost": {"value": 2,
                                                    "units": "2014$/unit"}},
                                           "ASHP": {
                                           "performance": {"value": 3,
                                                           "units": "COP"},
                                           "cost": {"value": 3,
                                                    "units": "2014$/unit"}},
                                           "GSHP": {
                                           "performance": {"value": 4,
                                                           "units": "COP"},
                                           "cost": {"value": 4,
                                                    "units": "2014$/unit"}}}},
                    "secondary heating": {"demand":
                                          {"windows conduction": {
                                           "performance": {"value": 5,
                                                           "units": "R Value"},
                                           "cost": {"value": 5,
                                                    "units": "2014$/sf"}},
                                           "windows solar": {
                                           "performance": {"value": 6,
                                                           "units": "SHGC"},
                                           "cost": {"value": 6,
                                                    "units": "2014$/sf"}}},
                                          "supply": {"performance":
                                                     {"value": 7,
                                                      "units": "COP"},
                                                     "cost":
                                                     {"value": 7,
                                                      "units": "2014$/unit"}}},
                    "cooling": {"demand": {"windows conduction": {
                                           "performance": {"value": 8,
                                                           "units": "R Value"},
                                           "cost": {"value": 8,
                                                    "units": "2014$/sf"}},
                                           "windows solar": {
                                           "performance": {"value": 9,
                                                           "units": "SHGC"},
                                           "cost": {"value": 9,
                                                    "units": "2014$/sf"}}},
                                "supply": {"central AC": {
                                           "performance": {"value": 10,
                                                           "units": "COP"},
                                           "cost": {"value": 10,
                                                    "units": "2014$/unit"}},
                                           "room AC": {
                                           "performance": {"value": 11,
                                                           "units": "COP"},
                                           "cost": {"value": 11,
                                                    "units": "2014$/unit"}},
                                           "ASHP": {
                                           "performance": {"value": 12,
                                                           "units": "COP"},
                                           "cost": {"value": 12,
                                                    "units": "2014$/unit"}},
                                           "GSHP": {
                                           "performance": {"value": 13,
                                                           "units": "COP"},
                                           "cost": {"value": 13,
                                                    "units": "2014$/unit"}}}},
                    "lighting": {"linear fluorescent": {
                                 "performance": {"value": 14,
                                                 "units": "lm/W"},
                                 "cost": {"value": 14,
                                          "units": "2014$/unit"}},
                                 "general service": {
                                 "performance": {"value": 15,
                                                 "units": "lm/W"},
                                 "cost": {"value": 15,
                                          "units": "2014$/unit"}},
                                 "reflector": {
                                 "performance": {"value": 16,
                                                 "units": "lm/W"},
                                 "cost": {"value": 16,
                                          "units": "2014$/unit"}},
                                 "external": {
                                 "performance": {"value": 17,
                                                 "units": "lm/W"},
                                 "cost": {"value": 17,
                                          "units": "2014$/unit"}}}},
                    "natural gas": {"water heating": {
                                    "performance": {"value": 18,
                                                    "units": "Energy Factor"},
                                    "cost": {"value": 18,
                                             "units": "2014$/unit"}}}},
            "multi family home": {
                "electricity (grid)": {
                    "heating": {"demand": {"windows conduction": {
                                           "performance": {"value": 19,
                                                           "units": "R Value"},
                                           "cost": {"value": 19,
                                                    "units": "2014$/sf"}},
                                           "windows solar": {
                                           "performance": {"value": 20,
                                                           "units": "SHGC"},
                                           "cost": {"value": 20,
                                                    "units": "2014$/sf"}}},
                                "supply": {"boiler (electric)": {
                                           "performance": {"value": 21,
                                                           "units": "COP"},
                                           "cost": {"value": 21,
                                                    "units": "2014$/unit"}},
                                           "ASHP": {
                                           "performance": {"value": 22,
                                                           "units": "COP"},
                                           "cost": {"value": 22,
                                                    "units": "2014$/unit"}},
                                           "GSHP": {
                                           "performance": {"value": 23,
                                                           "units": "COP"},
                                           "cost": {"value": 23,
                                                    "units": "2014$/unit"}}}},
                    "lighting": {"linear fluorescent": {
                                 "performance": {"value": 24,
                                                 "units": "lm/W"},
                                 "cost": {"value": 24,
                                          "units": "2014$/unit"}},
                                 "general service": {
                                 "performance": {"value": 25,
                                                 "units": "lm/W"},
                                 "cost": {"value": 25,
                                          "units": "2014$/unit"}},
                                 "reflector": {
                                 "performance": {"value": 25,
                                                 "units": "lm/W"},
                                 "cost": {"value": 25,
                                          "units": "2014$/unit"}},
                                 "external": {
                                 "performance": {"value": 25,
                                                 "units": "lm/W"},
                                 "cost": {"value": 25,
                                          "units": "2014$/unit"}}}}}},
        "AIA_CZ2": {
            "single family home": {
                "electricity (grid)": {
                    "heating": {"demand": {"windows conduction": {
                                           "performance": {"value": 1,
                                                           "units": "R Value"},
                                           "cost": {"value": 1,
                                                    "units": "2014$/sf"}},
                                           "windows solar": {
                                           "performance": {"value": 2,
                                                           "units": "SHGC"},
                                           "cost": {"value": 2,
                                                    "units": "2014$/sf"}}},
                                "supply": {"boiler (electric)": {
                                           "performance": {"value": 2,
                                                           "units": "COP"},
                                           "cost": {"value": 2,
                                                    "units": "2014$/unit"}},
                                           "ASHP": {
                                           "performance": {"value": 3,
                                                           "units": "COP"},
                                           "cost": {"value": 3,
                                                    "units": "2014$/unit"}},
                                           "GSHP": {
                                           "performance": {"value": 4,
                                                           "units": "COP"},
                                           "cost": {"value": 4,
                                                    "units": "2014$/unit"}}}},
                    "secondary heating": {"demand":
                                          {"windows conduction": {
                                           "performance": {"value": 5,
                                                           "units": "R Value"},
                                           "cost": {"value": 5,
                                                    "units": "2014$/sf"}},
                                           "windows solar": {
                                           "performance": {"value": 6,
                                                           "units": "SHGC"},
                                           "cost": {"value": 6,
                                                    "units": "2014$/sf"}}},
                                          "supply": {"performance":
                                                     {"value": 7,
                                                      "units": "COP"},
                                                     "cost":
                                                     {"value": 7,
                                                      "units": "2014$/unit"}}},
                    "cooling": {"demand": {"windows conduction": {
                                           "performance": {"value": 8,
                                                           "units": "R Value"},
                                           "cost": {"value": 8,
                                                    "units": "2014$/sf"}},
                                           "windows solar": {
                                           "performance": {"value": 9,
                                                           "units": "SHGC"},
                                           "cost": {"value": 9,
                                                    "units": "2014$/sf"}}},
                                "supply": {"central AC": {
                                           "performance": {"value": 10,
                                                           "units": "COP"},
                                           "cost": {"value": 10,
                                                    "units": "2014$/unit"}},
                                           "room AC": {
                                           "performance": {"value": 11,
                                                           "units": "COP"},
                                           "cost": {"value": 11,
                                                    "units": "2014$/unit"}},
                                           "ASHP": {
                                           "performance": {"value": 12,
                                                           "units": "COP"},
                                           "cost": {"value": 12,
                                                    "units": "2014$/unit"}},
                                           "GSHP": {
                                           "performance": {"value": 13,
                                                           "units": "COP"},
                                           "cost": {"value": 13,
                                                    "units": "2014$/unit"}}}},
                    "lighting": {"linear fluorescent": {
                                 "performance": {"value": 14,
                                                 "units": "lm/W"},
                                 "cost": {"value": 14,
                                          "units": "2014$/unit"}},
                                 "general service": {
                                 "performance": {"value": 15,
                                                 "units": "lm/W"},
                                 "cost": {"value": 15,
                                          "units": "2014$/unit"}},
                                 "reflector": {
                                 "performance": {"value": 16,
                                                 "units": "lm/W"},
                                 "cost": {"value": 16,
                                          "units": "2014$/unit"}},
                                 "external": {
                                 "performance": {"value": 17,
                                                 "units": "lm/W"},
                                 "cost": {"value": 17,
                                          "units": "2014$/unit"}}}},
                    "natural gas": {"water heating": {
                                    "performance": {"value": 18,
                                                    "units": "Energy Factor"},
                                    "cost": {"value": 18,
                                             "units": "2014$/unit"}}}},
            "multi family home": {
                "electricity (grid)": {
                    "heating": {"demand": {"windows conduction": {
                                           "performance": {"value": 19,
                                                           "units": "R Value"},
                                           "cost": {"value": 19,
                                                    "units": "2014$/sf"}},
                                           "windows solar": {
                                           "performance": {"value": 20,
                                                           "units": "SHGC"},
                                           "cost": {"value": 20,
                                                    "units": "2014$/sf"}}},
                                "supply": {"boiler (electric)": {
                                           "performance": {"value": 21,
                                                           "units": "COP"},
                                           "cost": {"value": 21,
                                                    "units": "2014$/unit"}},
                                           "ASHP": {
                                           "performance": {"value": 22,
                                                           "units": "COP"},
                                           "cost": {"value": 22,
                                                    "units": "2014$/unit"}},
                                           "GSHP": {
                                           "performance": {"value": 23,
                                                           "units": "COP"},
                                           "cost": {"value": 23,
                                                    "units": "2014$/unit"}}}},
                    "lighting": {"linear fluorescent": {
                                 "performance": {"value": 24,
                                                 "units": "lm/W"},
                                 "cost": {"value": 24,
                                          "units": "2014$/unit"}},
                                 "general service": {
                                 "performance": {"value": 25,
                                                 "units": "lm/W"},
                                 "cost": {"value": 25,
                                          "units": "2014$/unit"}},
                                 "reflector": {
                                 "performance": {"value": 25,
                                                 "units": "lm/W"},
                                 "cost": {"value": 25,
                                          "units": "2014$/unit"}},
                                 "external": {
                                 "performance": {"value": 25,
                                                 "units": "lm/W"},
                                 "cost": {"value": 25,
                                          "units": "2014$/unit"}}}}}},
        "AIA_CZ4": {
            "multi family home": {
                "electricity (grid)": {
                    "lighting": {"linear fluorescent": {
                                 "performance": {"value": 24,
                                                 "units": "lm/W"},
                                 "cost": {"value": 24,
                                          "units": "2014$/unit"}},
                                 "general service": {
                                 "performance": {"value": 25,
                                                 "units": "lm/W"},
                                 "cost": {"value": 25,
                                          "units": "2014$/unit"}},
                                 "reflector": {
                                 "performance": {"value": 26,
                                                 "units": "lm/W"},
                                 "cost": {"value": 26,
                                          "units": "2014$/unit"}},
                                 "external": {
                                 "performance": {"value": 27,
                                                 "units": "lm/W"},
                                 "cost": {"value": 27,
                                          "units": "2014$/unit"}}}}}}}

    # Sample input dict of microsegment stock/energy info. to reference in
    # generating and partitioning master microsegments for a measure
    sample_msegin = {
        "AIA_CZ1": {
            "single family home": {
                "square footage": {"2009": 100, "2010": 200},
                "electricity (grid)": {
                    "heating": {"demand": {"windows conduction": {
                                           "stock": "NA",
                                           "energy": {"2009": 0, "2010": 0}},
                                           "windows solar": {
                                           "stock": "NA",
                                           "energy": {"2009": 1, "2010": 1}}},
                                "supply": {"boiler (electric)": {
                                           "stock": {"2009": 2, "2010": 2},
                                           "energy": {"2009": 2, "2010": 2}},
                                           "ASHP": {
                                           "stock": {"2009": 3, "2010": 3},
                                           "energy": {"2009": 3, "2010": 3}},
                                           "GSHP": {
                                           "stock": {"2009": 4, "2010": 4},
                                           "energy": {"2009": 4, "2010": 4}}}},
                    "secondary heating": {"demand": {"windows conduction": {
                                                     "stock": "NA",
                                                     "energy": {"2009": 5,
                                                                "2010": 5}},
                                                     "windows solar": {
                                                     "stock": "NA",
                                                     "energy": {"2009": 6,
                                                                "2010": 6}}},
                                          "supply": {"non-specific": 7}},
                    "cooling": {"demand": {"windows conduction": {
                                           "stock": "NA",
                                           "energy": {"2009": 5, "2010": 5}},
                                           "windows solar": {
                                           "stock": "NA",
                                           "energy": {"2009": 6, "2010": 6}}},
                                "supply": {"central AC": {
                                           "stock": {"2009": 7, "2010": 7},
                                           "energy": {"2009": 7, "2010": 7}},
                                           "room AC": {
                                           "stock": {"2009": 8, "2010": 8},
                                           "energy": {"2009": 8, "2010": 8}},
                                           "ASHP": {
                                           "stock": {"2009": 9, "2010": 9},
                                           "energy": {"2009": 9, "2010": 9}},
                                           "GSHP": {
                                           "stock": {"2009": 10, "2010": 10},
                                           "energy": {"2009": 10,
                                                      "2010": 10}}}},
                    "lighting": {"linear fluorescent": {
                                 "stock": {"2009": 11, "2010": 11},
                                 "energy": {"2009": 11, "2010": 11}},
                                 "general service": {
                                 "stock": {"2009": 12, "2010": 12},
                                 "energy": {"2009": 12, "2010": 12}},
                                 "reflector": {
                                 "stock": {"2009": 13, "2010": 13},
                                 "energy": {"2009": 13, "2010": 13}},
                                 "external": {
                                 "stock": {"2009": 14, "2010": 14},
                                 "energy": {"2009": 14, "2010": 14}}}},
                    "natural gas": {"water heating": {
                                    "stock": {"2009": 15, "2010": 15},
                                    "energy": {"2009": 15, "2010": 15}}}},
            "multi family home": {
                "square footage": {"2009": 300, "2010": 400},
                "electricity (grid)": {
                    "heating": {"demand": {"windows conduction": {
                                           "stock": "NA",
                                           "energy": {"2009": 0, "2010": 0}},
                                           "windows solar": {
                                           "stock": "NA",
                                           "energy": {"2009": 1, "2010": 1}}},
                                "supply": {"boiler (electric)": {
                                           "stock": {"2009": 2, "2010": 2},
                                           "energy": {"2009": 2, "2010": 2}},
                                           "ASHP": {
                                           "stock": {"2009": 3, "2010": 3},
                                           "energy": {"2009": 3, "2010": 3}},
                                           "GSHP": {
                                           "stock": {"2009": 4, "2010": 4}}}},
                    "lighting": {"linear fluorescent": {
                                 "stock": {"2009": 11, "2010": 11},
                                 "energy": {"2009": 11, "2010": 11}},
                                 "general service": {
                                 "stock": {"2009": 12, "2010": 12},
                                 "energy": {"2009": 12, "2010": 12}},
                                 "reflector": {
                                 "stock": {"2009": 13, "2010": 13},
                                 "energy": {"2009": 13, "2010": 13}},
                                 "external": {
                                 "stock": {"2009": 14, "2010": 14},
                                 "energy": {"2009": 14, "2010": 14}}}}}},
        "AIA_CZ2": {
            "single family home": {
                "square footage": {"2009": 500, "2010": 600},
                "electricity (grid)": {
                    "heating": {"demand": {"windows conduction": {
                                           "stock": "NA",
                                           "energy": {"2009": 0, "2010": 0}},
                                           "windows solar": {
                                           "stock": "NA",
                                           "energy": {"2009": 1, "2010": 1}}},
                                "supply": {"boiler (electric)": {
                                           "stock": {"2009": 2, "2010": 2},
                                           "energy": {"2009": 2, "2010": 2}},
                                           "ASHP": {
                                           "stock": {"2009": 3, "2010": 3},
                                           "energy": {"2009": 3, "2010": 3}},
                                           "GSHP": {
                                           "stock": {"2009": 4, "2010": 4},
                                           "energy": {"2009": 4, "2010": 4}}}},
                    "secondary heating": {"demand": {"windows conduction": {
                                                     "stock": "NA",
                                                     "energy": {"2009": 5,
                                                                "2010": 5}},
                                                     "windows solar": {
                                                     "stock": "NA",
                                                     "energy": {"2009": 6,
                                                                "2010": 6}}},
                                          "supply": {"non-specific": 7}},
                    "cooling": {"demand": {"windows conduction": {
                                           "stock": "NA",
                                           "energy": {"2009": 5, "2010": 5}},
                                           "windows solar": {
                                           "stock": "NA",
                                           "energy": {"2009": 6, "2010": 6}}},
                                "supply": {"central AC": {
                                           "stock": {"2009": 7, "2010": 7},
                                           "energy": {"2009": 7, "2010": 7}},
                                           "room AC": {
                                           "stock": {"2009": 8, "2010": 8},
                                           "energy": {"2009": 8, "2010": 8}},
                                           "ASHP": {
                                           "stock": {"2009": 9, "2010": 9},
                                           "energy": {"2009": 9, "2010": 9}},
                                           "GSHP": {
                                           "stock": {"2009": 10, "2010": 10},
                                           "energy": {"2009": 10,
                                                      "2010": 10}}}},
                    "lighting": {"linear fluorescent": {
                                 "stock": {"2009": 11, "2010": 11},
                                 "energy": {"2009": 11, "2010": 11}},
                                 "general service": {
                                 "stock": {"2009": 12, "2010": 12},
                                 "energy": {"2009": 12, "2010": 12}},
                                 "reflector": {
                                 "stock": {"2009": 13, "2010": 13},
                                 "energy": {"2009": 13, "2010": 13}},
                                 "external": {
                                 "stock": {"2009": 14, "2010": 14},
                                 "energy": {"2009": 14, "2010": 14}}}},
                    "natural gas": {"water heating": {
                                    "stock": {"2009": 15, "2010": 15},
                                    "energy": {"2009": 15, "2010": 15}}}},
            "multi family home": {
                "square footage": {"2009": 700, "2010": 800},
                "electricity (grid)": {
                    "heating": {"demand": {"windows conduction": {
                                           "stock": "NA",
                                           "energy": {"2009": 0, "2010": 0}},
                                           "windows solar": {
                                           "stock": "NA",
                                           "energy": {"2009": 1, "2010": 1}}},
                                "supply": {"boiler (electric)": {
                                           "stock": {"2009": 2, "2010": 2},
                                           "energy": {"2009": 2, "2010": 2}},
                                           "ASHP": {
                                           "stock": {"2009": 3, "2010": 3},
                                           "energy": {"2009": 3, "2010": 3}},
                                           "GSHP": {
                                           "stock": {"2009": 4, "2010": 4}}}},
                    "lighting": {"linear fluorescent": {
                                 "stock": {"2009": 11, "2010": 11},
                                 "energy": {"2009": 11, "2010": 11}},
                                 "general service": {
                                 "stock": {"2009": 12, "2010": 12},
                                 "energy": {"2009": 12, "2010": 12}},
                                 "reflector": {
                                 "stock": {"2009": 13, "2010": 13},
                                 "energy": {"2009": 13, "2010": 13}},
                                 "external": {
                                 "stock": {"2009": 14, "2010": 14},
                                 "energy": {"2009": 14, "2010": 14}}}}}},
        "AIA_CZ4": {
            "multi family home": {
                "square footage": {"2009": 900, "2010": 1000},
                "electricity (grid)": {
                    "lighting": {"linear fluorescent": {
                                 "stock": {"2009": 11, "2010": 11},
                                 "energy": {"2009": 11, "2010": 11}},
                                 "general service": {
                                 "stock": {"2009": 12, "2010": 12},
                                 "energy": {"2009": 12, "2010": 12}},
                                 "reflector": {
                                 "stock": {"2009": 13, "2010": 13},
                                 "energy": {"2009": 13, "2010": 13}},
                                 "external": {
                                 "stock": {"2009": 14, "2010": 14},
                                 "energy": {"2009": 14, "2010": 14}}}}}}}

    # List of measures with attribute combinations that should all be found in
    # the key chains of the "sample_msegin" dict above
    ok_measures = [{"name": "sample measure 1",
                    "installed_cost": 25,
                    "cost_units": "2014$/unit",
                    "energy_efficiency": {"AIA_CZ1": {"heating": 30,
                                                      "cooling": 25},
                                          "AIA_CZ2": {"heating": 30,
                                                      "cooling": 15}},
                    "energy_efficiency_units": "COP",
                    "end_use": ["heating", "cooling"],
                    "fuel_type": "electricity (grid)",
                    "technology_type": "supply",
                    "technology": ["boiler (electric)",
                                   "ASHP", "GSHP", "room AC"],
                    "bldg_type": "single family home",
                    "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                   {"name": "sample measure 2",
                    "installed_cost": 25,
                    "cost_units": "2014$/unit",
                    "energy_efficiency": 25,
                    "energy_efficiency_units": "Energy Factor",
                    "end_use": "water heating",
                    "fuel_type": "natural gas",
                    "technology_type": "supply",
                    "technology": None,
                    "bldg_type": "single family home",
                    "climate_zone": "AIA_CZ1"},
                   {"name": "sample measure 3",  # Add heat/cool end uses later
                    "installed_cost": 25,
                    "cost_units": "2014$/unit",
                    "energy_efficiency": 25,
                    "energy_efficiency_units": "lm/W",
                    "end_use": "lighting",
                    "fuel_type": "electricity (grid)",
                    "technology_type": "supply",
                    "technology": ["linear fluorescent",
                                   "general service",
                                   "external"],
                    "bldg_type": ["single family home",
                                  "multi family home"],
                    "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                   {"name": "sample measure 4",
                    "installed_cost": 10,
                    "cost_units": "2014$/sf",
                    "energy_efficiency": {"windows conduction": 20,
                                          "windows solar": 1},
                    "energy_efficiency_units": {"windows conduction":
                                                "R Value",
                                                "windows solar": "SHGC"},
                    "end_use": "heating",
                    "fuel_type": "electricity (grid)",
                    "technology_type": "demand",
                    "technology": ["windows conduction",
                                   "windows solar"],
                    "bldg_type": ["single family home",
                                  "multi family home"],
                    "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                   {"name": "sample measure 5",
                    "installed_cost": 10,
                    "cost_units": "2014$/sf",
                    "energy_efficiency": 1,
                    "energy_efficiency_units": "SHGC",
                    "end_use": "heating",
                    "fuel_type": "electricity (grid)",
                    "technology_type": "demand",
                    "technology": "windows solar",
                    "bldg_type": "single family home",
                    "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                   {"name": "sample measure 6",
                    "installed_cost": 10,
                    "cost_units": "2014$/sf",
                    "energy_efficiency": {"windows conduction": 10,
                                          "windows solar": 1},
                    "energy_efficiency_units": {"windows conduction":
                                                "R Value",
                                                "windows solar": "SHGC"},
                    "end_use": ["heating", "secondary heating", "cooling"],
                    "fuel_type": "electricity (grid)",
                    "technology_type": "demand",
                    "technology": ["windows conduction", "windows solar"],
                    "bldg_type": "single family home",
                    "climate_zone": ["AIA_CZ1", "AIA_CZ2"]}]

    # List of measures with attribute combinations that should match some of
    # the key chains in the "sample_msegin" dict above (i.e., AIA_CZ1 ->
    # single family home -> electricity (grid) -> cooling -> GSHP is
    # a valid chain, AIA_CZ1 -> single family home -> electricity (grid) ->
    # cooling -> linear fluorescent is not)
    partial_measures = [{"name": "partial measure 1",
                         "installed_cost": 25,
                         "cost_units": "2014$/unit",
                         "energy_efficiency": 25,
                         "energy_efficiency_units": "COP",
                         "end_use": "cooling",
                         "fuel_type": "electricity (grid)",
                         "technology_type": "supply",
                         "technology": ["boiler (electric)", "ASHP"],
                         "bldg_type": "single family home",
                         "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                        {"name": "partial measure 2",
                         "installed_cost": 25,
                         "cost_units": "2014$/unit",
                         "energy_efficiency": 25,
                         "energy_efficiency_units": "COP",
                         "end_use": ["heating", "cooling"],
                         "fuel_type": "electricity (grid)",
                         "technology_type": "supply",
                         "technology": ["linear fluorescent",
                                        "general service",
                                        "external", "GSHP", "ASHP"],
                         "bldg_type": "single family home",
                         "climate_zone": ["AIA_CZ1", "AIA_CZ2"]}]

    # List of measures with attribute combinations that should not match any
    # of the key chains in the "sample_msegin" dict above
    blank_measures = [{"name": "blank measure 1",
                       "installed_cost": 10,
                       "cost_units": "2014$/unit",
                       "energy_efficiency": 10,
                       "energy_efficiency_units": "COP",
                       "end_use": "cooling",
                       "fuel_type": "electricity (grid)",
                       "technology_type": "supply",
                       "technology": "boiler (electric)",
                       "bldg_type": "single family home",
                       "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                      {"name": "blank measure 2",
                       "installed_cost": 10,
                       "cost_units": "2014$/unit",
                       "energy_efficiency": {"AIA_CZ1": {"heating": 30,
                                                         "cooling": 25},
                                             "AIA_CZ2": {"heating": 30,
                                                         "cooling": 15}},
                       "energy_efficiency_units": "COP",
                       "end_use": ["heating", "cooling"],
                       "fuel_type": "electricity (grid)",
                       "technology_type": "supply",
                       "technology": ["linear fluorescent",
                                      "general service",
                                      "external"],
                       "bldg_type": "single family home",
                       "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                      {"name": "blank measure 3",
                       "installed_cost": 25,
                       "cost_units": "2014$/unit",
                       "energy_efficiency": 25,
                       "energy_efficiency_units": "lm/W",
                       "end_use": "lighting",
                       "fuel_type": "natural gas",
                       "technology_type": "supply",
                       "technology": ["linear fluorescent",
                                      "general service",
                                      "external"],
                       "bldg_type": "single family home",
                       "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                      {"name": "blank measure 4",
                       "installed_cost": 25,
                       "cost_units": "2014$/unit",
                       "energy_efficiency": 25,
                       "energy_efficiency_units": "lm/W",
                       "end_use": "lighting",
                       "fuel_type": "solar",
                       "technology_type": "supply",
                       "technology": ["linear fluorescent",
                                      "general service",
                                      "external"],
                       "bldg_type": "single family home",
                       "climate_zone": "AIA_CZ1"}]

    # Master stock, energy, and cost information that should be generated by
    # "ok_measures" above using the "sample_msegin" dict
    ok_out = [{"stock": {"total": {"2009": 72, "2010": 72},
                         "competed": {"2009": 72, "2010": 72}},
               "energy": {"total": {"2009": 72, "2010": 72},
                          "competed": {"2009": 72, "2010": 72},
                          "efficient": {"2009": 36.7067, "2010": 36.7067}},
               "cost": {"baseline": {"2009": 710, "2010": 710},
                        "measure": {"2009": 1800, "2010": 1800}}},
              {"stock": {"total": {"2009": 15, "2010": 15},
                         "competed": {"2009": 15, "2010": 15}},
               "energy": {"total": {"2009": 15, "2010": 15},
                          "competed": {"2009": 15, "2010": 15},
                          "efficient": {"2009": 10.80, "2010": 10.80}},
               "cost": {"baseline": {"2009": 270, "2010": 270},
                        "measure": {"2009": 375, "2010": 375}}},
              {"stock": {"total": {"2009": 148, "2010": 148},
                         "competed": {"2009": 148, "2010": 148}},
               "energy": {"total": {"2009": 148, "2010": 148},
                          "competed": {"2009": 148, "2010": 148},
                          "efficient": {"2009": 118.88, "2010": 118.88}},
               "cost": {"baseline": {"2009": 2972, "2010": 2972},
                        "measure": {"2009": 3700, "2010": 3700}}},
              {"stock": {"total": {"2009": 1600, "2010": 2000},
                         "competed": {"2009": 1600, "2010": 2000}},
               "energy": {"total": {"2009": 4, "2010": 4},
                          "competed": {"2009": 4, "2010": 4},
                          "efficient": {"2009": 1.1, "2010": 1.1}},
               "cost": {"baseline": {"2009": 20400, "2010": 24600},
                        "measure": {"2009": 16000, "2010": 20000}}},
              {"stock": {"total": {"2009": 600, "2010": 800},
                         "competed": {"2009": 600, "2010": 800}},
               "energy": {"total": {"2009": 2, "2010": 2},
                          "competed": {"2009": 2, "2010": 2},
                          "efficient": {"2009": 1, "2010": 1}},
               "cost": {"baseline": {"2009": 1200, "2010": 1600},
                        "measure": {"2009": 6000, "2010": 8000}}},
              {"stock": {"total": {"2009": 600, "2010": 800},
                         "competed": {"2009": 600, "2010": 800}},
               "energy": {"total": {"2009": 46, "2010": 46},
                          "competed": {"2009": 46, "2010": 46},
                          "efficient": {"2009": 17.33, "2010": 17.33}},
               "cost": {"baseline": {"2009": 3100, "2010": 4133.33},
                        "measure": {"2009": 6000, "2010": 8000}}}]

    # Master stock, energy, and cost information that should be generated by
    # "partial_measures" above using the "sample_msegin" dict
    partial_out = [{"stock": {"total": {"2009": 18, "2010": 18},
                              "competed": {"2009": 18, "2010": 18}},
                    "energy": {"total": {"2009": 18, "2010": 18},
                               "competed": {"2009": 18, "2010": 18},
                               "efficient": {"2009": 8.64, "2010": 8.64}},
                    "cost": {"baseline": {"2009": 216, "2010": 216},
                             "measure": {"2009": 450, "2010": 450}}},
                   {"stock": {"total": {"2009": 52, "2010": 52},
                              "competed": {"2009": 52, "2010": 52}},
                    "energy": {"total": {"2009": 52, "2010": 52},
                               "competed": {"2009": 52, "2010": 52},
                               "efficient": {"2009": 21.04, "2010": 21.04}},
                    "cost": {"baseline": {"2009": 526, "2010": 526},
                             "measure": {"2009": 1300, "2010": 1300}}}]

    # Master stock, energy, and cost information that should be generated by
    # "blank_measures" above using the "sample_msegin" dict
    blank_out = list(numpy.repeat({"stock": {"total": None,
                                             "competed": None},
                                   "energy": {"total": None,
                                              "competed": None,
                                              "efficient": None},
                                   "cost": {"baseline": None,
                                            "measure": None}},
                                  len(blank_measures)))

    # Create a routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                self.assertAlmostEqual(dict1[k], dict2[k2], places=2)

    # Test for correct output from "ok_measures" input
    def test_mseg_ok(self):
        for idx, measure in enumerate(self.ok_measures):
            # Create an instance of the object based on ok measure info
            measure_instance = run.Measure(**measure)
            # Assert output dict is correct
            dict1 = measure_instance.mseg_find_partition(self.sample_msegin,
                                                         self.sample_basein,
                                                         "Technical potential")
            dict2 = self.ok_out[idx]
            self.dict_check(dict1, dict2)

    # Test for correct output from "partial_measures" input
    def test_mseg_partial(self):
        for idx, measure in enumerate(self.partial_measures):
            # Create an instance of the object based on partial measure info
            measure_instance = run.Measure(**measure)
            # Assert output dict is correct
            dict1 = measure_instance.mseg_find_partition(self.sample_msegin,
                                                         self.sample_basein,
                                                         "Technical potential")
            dict2 = self.partial_out[idx]
            self.dict_check(dict1, dict2)

    # Test for correct output from "blank_measures" input
    def test_mseg_blank(self):
        for idx, measure in enumerate(self.blank_measures):
            # Create an instance of the object based on blank measure info
            measure_instance = run.Measure(**measure)
            # Assert output dict is correct
            dict1 = measure_instance.mseg_find_partition(self.sample_msegin,
                                                         self.sample_basein,
                                                         "Technical potential")
            dict2 = self.blank_out[idx]
            self.dict_check(dict1, dict2)


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == "__main__":
    main()
