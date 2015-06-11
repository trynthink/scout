#!/usr/bin/env python3

""" Tests for running the engine """

# Import code to be tested
import run

# Import needed packages
import unittest
import numpy
import scipy.stats as ss
import copy
import math


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
                 "carbon":
                 {"total":
                     {"2009": 500, "2010": 600},
                  "competed":
                     {"2009": 700, "2010": 800},
                  "efficient":
                     {"2009": 700, "2010": 800}},
                 "cost":
                 {"baseline": {
                     "stock": {"2009": 900, "2010": 1000},
                     "energy": {"2009": 900, "2010": 1000},
                     "carbon": {"2009": 900, "2010": 1000}},
                  "measure": {
                     "stock": {"2009": 1100, "2010": 1200},
                     "energy": {"2009": 1100, "2010": 1200},
                     "carbon": {"2009": 1100, "2010": 1200}}}}

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
              "carbon":
              {"total":
                   {"2009": 500, "2010": 600},
               "competed":
                   {"2009": 700, "2010": 800},
               "efficient":
                   {"2009": 700, "2010": 800}},
              "cost":
              {"baseline": {
                  "stock": {"2009": 225, "2010": 250},
                  "energy": {"2009": 900, "2010": 1000},
                  "carbon": {"2009": 900, "2010": 1000}},
               "measure": {
                  "stock": {"2009": 275, "2010": 300},
                  "energy": {"2009": 1100, "2010": 1200},
                  "carbon": {"2009": 1100, "2010": 1200}}}}

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


class RandomSampleTest(unittest.TestCase):
    """ Test that the "rand_list_gen" yields an output
    list of sampled values that are correctly distributed """

    # Sample measure for use in testing attributes
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

    # Set test sampling number
    test_sample_n = 100

    # Set of input distribution information that should
    # yield valid outputs
    test_ok_in = [["normal", 10, 2], ["weibull", 5, 8],
                  ["triangular", 3, 7, 10]]

    # Set of input distribution information that should
    # yield value errors
    test_fail_in = [[1, 10, 2], ["triangle", 5, 8, 10],
                    ["triangular", 3, 7]]

    # Calls to the scipy fit function that will be used
    # to check for correct fitted distribution parameters
    # for sampled values
    test_fit_calls = ['ss.norm.fit(sample)',
                      'ss.weibull_min.fit(sample, floc = 0)',
                      'ss.triang.fit(sample)']

    # Correct set of outputs for given random sampling seed
    test_outputs = [numpy.array([10.06, 2.03]),
                    numpy.array([4.93, 0, 8.02]),
                    numpy.array([0.51, 3.01, 7.25])]

    # Test for correct output from "ok" input distribution info.
    def test_distrib_ok(self):
        # Seed random number generator to yield repeatable results
        numpy.random.seed(5423)
        for idx in range(0, len(self.test_ok_in)):
            # Sample values based on distribution input info.
            sample = self.measure_instance.rand_list_gen(self.test_ok_in[idx],
                                                         self.test_sample_n)
            # Fit parameters for sampled values and check against
            # known correct parameter values in "test_outputs" * NOTE:
            # this adds ~ 0.15 s to test computation
            for elem in range(0, len(self.test_outputs[idx])):
                with numpy.errstate(divide='ignore'):  # Warning for triang
                    self.assertAlmostEqual(
                        list(eval(self.test_fit_calls[idx]))[elem],
                        self.test_outputs[idx][elem], 2)

    # Test for correct output from "fail" input distribution info.
    def test_distrib_fail(self):
        for idx in range(0, len(self.test_fail_in)):
            with self.assertRaises(ValueError):
                self.measure_instance.rand_list_gen(
                    self.test_fail_in[idx], self.test_sample_n)


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
    test_carbon = [{"2009": 30, "2010": 60, "2011": 90},
                   {"2025": 120, "2028": 150, "2035": 180},
                   {"2020": 210, "2021": 240, "2022": 270}]

    # Set sample base and measure costs to use in the testing
    test_base_cost = [{"2009": 10, "2010": 10, "2011": 10},
                      {"2025": 20, "2028": 20, "2035": 20},
                      {"2020": 30, "2021": 30, "2022": 30}]
    test_cost_meas = [20, 30, 40]

    # Set sample energy and carbon costs to use in the testing
    cost_energy = numpy.array((b'Test', 1, 2, 2, 2, 2, 2, 2, 2, 2),
                              dtype=[('Category', 'S11'), ('2009', '<f8'),
                                     ('2010', '<f8'), ('2011', '<f8'),
                                     ('2020', '<f8'), ('2021', '<f8'),
                                     ('2022', '<f8'), ('2025', '<f8'),
                                     ('2028', '<f8'), ('2035', '<f8')])
    cost_carbon = numpy.array((b'Test', 1, 4, 1, 1, 1, 1, 1, 1, 3),
                              dtype=[('Category', 'S11'), ('2009', '<f8'),
                                     ('2010', '<f8'), ('2011', '<f8'),
                                     ('2020', '<f8'), ('2021', '<f8'),
                                     ('2022', '<f8'), ('2025', '<f8'),
                                     ('2028', '<f8'), ('2035', '<f8')])

    # Set two alternative schemes to use in the testing,
    # where the first should yield a full list of outputs
    # and the second should yield a list with blank elements
    test_schemes = ['Technical potential', 'Undefined']

    # Set a relative performance list that should yield a
    # full list of valid outputs
    ok_relperf = [{"2009": 0.30, "2010": 0.30, "2011": 0.30},
                  {"2025": 0.15, "2028": 0.15, "2035": 0.15},
                  {"2020": 0.75, "2021": 0.75, "2022": 0.75}]

    # Correct output of the "ok" function test
    ok_out = [[{"2009": 100, "2010": 200, "2011": 300},
               {"2009": 10, "2010": 20, "2011": 30},
               {"2009": 30, "2010": 60, "2011": 90},
               {"2009": 3, "2010": 6, "2011": 9},
               {"2009": 9, "2010": 18, "2011": 27},
               {"2009": 1000, "2010": 2000, "2011": 3000},
               {"2009": 10, "2010": 40, "2011": 60},
               {"2009": 30, "2010": 240, "2011": 90},
               {"2009": 2000, "2010": 4000, "2011": 6000},
               {"2009": 3, "2010": 12, "2011": 18},
               {"2009": 9, "2010": 72, "2011": 27}],
              [{"2025": 400, "2028": 500, "2035": 600},
               {"2025": 40, "2028": 50, "2035": 60},
               {"2025": 120, "2028": 150, "2035": 180},
               {"2025": 6, "2028": 7.5, "2035": 9},
               {"2025": 18, "2028": 22.5, "2035": 27},
               {"2025": 8000, "2028": 10000, "2035": 12000},
               {"2025": 80, "2028": 100, "2035": 120},
               {"2025": 120, "2028": 150, "2035": 540},
               {"2025": 12000, "2028": 15000, "2035": 18000},
               {"2025": 12, "2028": 15, "2035": 18},
               {"2025": 18, "2028": 22.5, "2035": 81}],
              [{"2020": 700, "2021": 800, "2022": 900},
               {"2020": 70, "2021": 80, "2022": 90},
               {"2020": 210, "2021": 240, "2022": 270},
               {"2020": 52.5, "2021": 60, "2022": 67.5},
               {"2020": 157.5, "2021": 180, "2022": 202.5},
               {"2020": 21000, "2021": 24000, "2022": 27000},
               {"2020": 140, "2021": 160, "2022": 180},
               {"2020": 210, "2021": 240, "2022": 270},
               {"2020": 28000, "2021": 32000, "2022": 36000},
               {"2020": 105, "2021": 120, "2022": 135},
               {"2020": 157.5, "2021": 180, "2022": 202.5}]]

    blank_out = [None, None, None, None, None, None,
                 None, None, None, None, None]

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
                self.test_carbon[elem],
                self.ok_relperf[elem],
                self.test_base_cost[elem],
                self.test_cost_meas[elem],
                self.cost_energy,
                self.cost_carbon,
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
                self.test_carbon[elem],
                self.ok_relperf[elem],
                self.test_base_cost[elem],
                self.test_cost_meas[elem],
                self.cost_energy,
                self.cost_carbon,
                self.test_schemes[1])

            lists2 = self.blank_out

            self.assertEqual(lists1, lists2)


class FindPartitionMasterMicrosegmentTest(unittest.TestCase):
    """ Test the operation of the mseg_find_partition function to
    verify measure microsegment-related attribute inputs yield expected master
    microsegment output """

    # Set cost, site-source, and carbon intensity info. from "run.py"
    ccosts = run.ccosts
    ss_conv = run.ss_conv
    carb_int = run.carb_int

    # Sample input dict of microsegment performance/cost info. to reference in
    # generating and partitioning master microsegments for a measure
    sample_basein = {
        "AIA_CZ1": {
            "single family home": {
                "electricity (grid)": {
                    "heating": {
                        "demand": {
                            "windows conduction": {
                                "performance": {
                                    "typical": {"2009": 1, "2010": 1},
                                    "best": {"2009": 1, "2010": 1},
                                    "units": "R Value",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 1, "2010": 1},
                                    "best": {"2009": 1, "2010": 1},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 10, "2010": 10},
                                    "range": {"2009": 1, "2010": 1},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "windows solar": {
                                "performance": {
                                    "typical": {"2009": 2, "2010": 2},
                                    "best": {"2009": 2, "2010": 2},
                                    "units": "SHGC",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 2, "2010": 2},
                                    "best": {"2009": 2, "2010": 2},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 20, "2010": 20},
                                    "range": {"2009": 2, "2010": 2},
                                    "units": "years",
                                    "source": "EIA AEO"}}},
                        "supply": {
                            "boiler (electric)": {
                                "performance": {
                                    "typical": {"2009": 2, "2010": 2},
                                    "best": {"2009": 2, "2010": 2},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 2, "2010": 2},
                                    "best": {"2009": 2, "2010": 2},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 20, "2010": 20},
                                    "range": {"2009": 2, "2010": 2},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "ASHP": {
                                "performance": {
                                    "typical": {"2009": 3, "2010": 3},
                                    "best": {"2009": 3, "2010": 3},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 3, "2010": 3},
                                    "best": {"2009": 3, "2010": 3},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 30, "2010": 30},
                                    "range": {"2009": 3, "2010": 3},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "GSHP": {
                                "performance": {
                                    "typical": {"2009": 4, "2010": 4},
                                    "best": {"2009": 4, "2010": 4},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 4, "2010": 4},
                                    "best": {"2009": 4, "2010": 4},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 40, "2010": 40},
                                    "range": {"2009": 4, "2010": 4},
                                    "units": "years",
                                    "source": "EIA AEO"}}}},
                    "secondary heating": {
                        "demand": {
                            "windows conduction": {
                                "performance": {
                                    "typical": {"2009": 5, "2010": 5},
                                    "best": {"2009": 5, "2010": 5},
                                    "units": "R Value",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 5, "2010": 5},
                                    "best": {"2009": 5, "2010": 5},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 50, "2010": 50},
                                    "range": {"2009": 5, "2010": 5},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "windows solar": {
                                "performance": {
                                    "typical": {"2009": 6, "2010": 6},
                                    "best": {"2009": 6, "2010": 6},
                                    "units": "SHGC",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 6, "2010": 6},
                                    "best": {"2009": 6, "2010": 6},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 60, "2010": 60},
                                    "range": {"2009": 6, "2010": 6},
                                    "units": "years",
                                    "source": "EIA AEO"}}},
                        "supply": {
                            "non-specific": {
                                "performance": {
                                    "typical": {"2009": 7, "2010": 7},
                                    "best": {"2009": 7, "2010": 7},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 7, "2010": 7},
                                    "best": {"2009": 7, "2010": 7},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 70, "2010": 70},
                                    "range": {"2009": 7, "2010": 7},
                                    "units": "years",
                                    "source": "EIA AEO"}}}},
                    "cooling": {
                        "demand": {
                            "windows conduction": {
                                "performance": {
                                    "typical": {"2009": 8, "2010": 8},
                                    "best": {"2009": 8, "2010": 8},
                                    "units": "R Value",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 8, "2010": 8},
                                    "best": {"2009": 8, "2010": 8},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 80, "2010": 80},
                                    "range": {"2009": 8, "2010": 8},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "windows solar": {
                                "performance": {
                                    "typical": {"2009": 9, "2010": 9},
                                    "best": {"2009": 9, "2010": 9},
                                    "units": "SHGC",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 9, "2010": 9},
                                    "best": {"2009": 9, "2010": 9},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 90, "2010": 90},
                                    "range": {"2009": 9, "2010": 9},
                                    "units": "years",
                                    "source": "EIA AEO"}}},
                        "supply": {
                            "central AC": {
                                "performance": {
                                    "typical": {"2009": 10, "2010": 10},
                                    "best": {"2009": 10, "2010": 10},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 10, "2010": 10},
                                    "best": {"2009": 10, "2010": 10},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 100, "2010": 100},
                                    "range": {"2009": 10, "2010": 10},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "room AC": {
                                "performance": {
                                    "typical": {"2009": 11, "2010": 11},
                                    "best": {"2009": 11, "2010": 11},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 11, "2010": 11},
                                    "best": {"2009": 11, "2010": 11},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 110, "2010": 110},
                                    "range": {"2009": 11, "2010": 11},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "ASHP": {
                                "performance": {
                                    "typical": {"2009": 12, "2010": 12},
                                    "best": {"2009": 12, "2010": 12},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 12, "2010": 12},
                                    "best": {"2009": 12, "2010": 12},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 120, "2010": 120},
                                    "range": {"2009": 12, "2010": 12},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "GSHP": {
                                "performance": {
                                    "typical": {"2009": 13, "2010": 13},
                                    "best": {"2009": 13, "2010": 13},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 13, "2010": 13},
                                    "best": {"2009": 13, "2010": 13},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 130, "2010": 130},
                                    "range": {"2009": 13, "2010": 13},
                                    "units": "years",
                                    "source": "EIA AEO"}}}},
                    "lighting": {
                        "linear fluorescent (LED)": {
                                "performance": {
                                    "typical": {"2009": 14, "2010": 14},
                                    "best": {"2009": 14, "2010": 14},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 14, "2010": 14},
                                    "best": {"2009": 14, "2010": 14},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 140, "2010": 140},
                                    "range": {"2009": 14, "2010": 14},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "general service (LED)": {
                                "performance": {
                                    "typical": {"2009": 15, "2010": 15},
                                    "best": {"2009": 15, "2010": 15},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 15, "2010": 15},
                                    "best": {"2009": 15, "2010": 15},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 150, "2010": 150},
                                    "range": {"2009": 15, "2010": 15},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "reflector (LED)": {
                                "performance": {
                                    "typical": {"2009": 16, "2010": 16},
                                    "best": {"2009": 16, "2010": 16},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 16, "2010": 16},
                                    "best": {"2009": 16, "2010": 16},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 160, "2010": 160},
                                    "range": {"2009": 16, "2010": 16},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "external (LED)": {
                                "performance": {
                                    "typical": {"2009": 17, "2010": 17},
                                    "best": {"2009": 17, "2010": 17},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 17, "2010": 17},
                                    "best": {"2009": 17, "2010": 17},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 170, "2010": 170},
                                    "range": {"2009": 17, "2010": 17},
                                    "units": "years",
                                    "source": "EIA AEO"}}}},
                    "natural gas": {
                        "water heating": {
                                "performance": {
                                    "typical": {"2009": 18, "2010": 18},
                                    "best": {"2009": 18, "2010": 18},
                                    "units": "EF",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 18, "2010": 18},
                                    "best": {"2009": 18, "2010": 18},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 180, "2010": 180},
                                    "range": {"2009": 18, "2010": 18},
                                    "units": "years",
                                    "source": "EIA AEO"}}}},
            "multi family home": {
                "electricity (grid)": {
                    "heating": {
                        "demand": {
                            "windows conduction": {
                                "performance": {
                                    "typical": {"2009": 19, "2010": 19},
                                    "best": {"2009": 19, "2010": 19},
                                    "units": "R Value",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 19, "2010": 19},
                                    "best": {"2009": 19, "2010": 19},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 190, "2010": 190},
                                    "range": {"2009": 19, "2010": 19},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "windows solar": {
                                "performance": {
                                    "typical": {"2009": 20, "2010": 20},
                                    "best": {"2009": 20, "2010": 20},
                                    "units": "SHGC",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 20, "2010": 20},
                                    "best": {"2009": 20, "2010": 20},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 200, "2010": 200},
                                    "range": {"2009": 20, "2010": 20},
                                    "units": "years",
                                    "source": "EIA AEO"}}},
                        "supply": {
                            "boiler (electric)": {
                                "performance": {
                                    "typical": {"2009": 21, "2010": 21},
                                    "best": {"2009": 21, "2010": 21},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 21, "2010": 21},
                                    "best": {"2009": 21, "2010": 21},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 210, "2010": 210},
                                    "range": {"2009": 21, "2010": 21},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "ASHP": {
                                "performance": {
                                    "typical": {"2009": 22, "2010": 22},
                                    "best": {"2009": 22, "2010": 22},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 22, "2010": 22},
                                    "best": {"2009": 22, "2010": 22},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 220, "2010": 220},
                                    "range": {"2009": 22, "2010": 22},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "GSHP": {
                                "performance": {
                                    "typical": {"2009": 23, "2010": 23},
                                    "best": {"2009": 23, "2010": 23},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 23, "2010": 23},
                                    "best": {"2009": 23, "2010": 23},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 230, "2010": 230},
                                    "range": {"2009": 23, "2010": 23},
                                    "units": "years",
                                    "source": "EIA AEO"}}}},
                    "lighting": {
                        "linear fluorescent (LED)": {
                                "performance": {
                                    "typical": {"2009": 24, "2010": 24},
                                    "best": {"2009": 24, "2010": 24},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 24, "2010": 24},
                                    "best": {"2009": 24, "2010": 24},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 240, "2010": 240},
                                    "range": {"2009": 24, "2010": 24},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "general service (LED)": {
                                "performance": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 250, "2010": 250},
                                    "range": {"2009": 25, "2010": 25},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "reflector (LED)": {
                                "performance": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 250, "2010": 250},
                                    "range": {"2009": 25, "2010": 25},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "external (LED)": {
                                "performance": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 250, "2010": 250},
                                    "range": {"2009": 25, "2010": 25},
                                    "units": "years",
                                    "source": "EIA AEO"}}}}}},
        "AIA_CZ2": {
            "single family home": {
                "electricity (grid)": {
                    "heating": {
                        "demand": {
                            "windows conduction": {
                                "performance": {
                                    "typical": {"2009": 1, "2010": 1},
                                    "best": {"2009": 1, "2010": 1},
                                    "units": "R Value",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 1, "2010": 1},
                                    "best": {"2009": 1, "2010": 1},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 10, "2010": 10},
                                    "range": {"2009": 1, "2010": 1},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "windows solar": {
                                "performance": {
                                    "typical": {"2009": 2, "2010": 2},
                                    "best": {"2009": 2, "2010": 2},
                                    "units": "SHGC",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 2, "2010": 2},
                                    "best": {"2009": 2, "2010": 2},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 20, "2010": 20},
                                    "range": {"2009": 2, "2010": 2},
                                    "units": "years",
                                    "source": "EIA AEO"}}},
                        "supply": {
                            "boiler (electric)": {
                                "performance": {
                                    "typical": {"2009": 2, "2010": 2},
                                    "best": {"2009": 2, "2010": 2},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 2, "2010": 2},
                                    "best": {"2009": 2, "2010": 2},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 20, "2010": 20},
                                    "range": {"2009": 2, "2010": 2},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "ASHP": {
                                "performance": {
                                    "typical": {"2009": 3, "2010": 3},
                                    "best": {"2009": 3, "2010": 3},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 3, "2010": 3},
                                    "best": {"2009": 3, "2010": 3},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 30, "2010": 30},
                                    "range": {"2009": 3, "2010": 3},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "GSHP": {
                                "performance": {
                                    "typical": {"2009": 4, "2010": 4},
                                    "best": {"2009": 4, "2010": 4},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 4, "2010": 4},
                                    "best": {"2009": 4, "2010": 4},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 40, "2010": 40},
                                    "range": {"2009": 4, "2010": 4},
                                    "units": "years",
                                    "source": "EIA AEO"}}}},
                    "secondary heating": {
                        "demand": {
                            "windows conduction": {
                                "performance": {
                                    "typical": {"2009": 5, "2010": 5},
                                    "best": {"2009": 5, "2010": 5},
                                    "units": "R Value",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 5, "2010": 5},
                                    "best": {"2009": 5, "2010": 5},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 50, "2010": 50},
                                    "range": {"2009": 5, "2010": 5},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "windows solar": {
                                "performance": {
                                    "typical": {"2009": 6, "2010": 6},
                                    "best": {"2009": 6, "2010": 6},
                                    "units": "SHGC",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 6, "2010": 6},
                                    "best": {"2009": 6, "2010": 6},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 60, "2010": 60},
                                    "range": {"2009": 6, "2010": 6},
                                    "units": "years",
                                    "source": "EIA AEO"}}},
                        "supply": {
                            "non-specific": {
                                "performance": {
                                    "typical": {"2009": 7, "2010": 7},
                                    "best": {"2009": 7, "2010": 7},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 7, "2010": 7},
                                    "best": {"2009": 7, "2010": 7},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 70, "2010": 70},
                                    "range": {"2009": 7, "2010": 7},
                                    "units": "years",
                                    "source": "EIA AEO"}}}},
                    "cooling": {
                        "demand": {
                            "windows conduction": {
                                "performance": {
                                    "typical": {"2009": 8, "2010": 8},
                                    "best": {"2009": 8, "2010": 8},
                                    "units": "R Value",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 8, "2010": 8},
                                    "best": {"2009": 8, "2010": 8},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 80, "2010": 80},
                                    "range": {"2009": 8, "2010": 8},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "windows solar": {
                                "performance": {
                                    "typical": {"2009": 9, "2010": 9},
                                    "best": {"2009": 9, "2010": 9},
                                    "units": "SHGC",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 9, "2010": 9},
                                    "best": {"2009": 9, "2010": 9},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 90, "2010": 90},
                                    "range": {"2009": 9, "2010": 9},
                                    "units": "years",
                                    "source": "EIA AEO"}}},
                        "supply": {
                            "central AC": {
                                "performance": {
                                    "typical": {"2009": 10, "2010": 10},
                                    "best": {"2009": 10, "2010": 10},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 10, "2010": 10},
                                    "best": {"2009": 10, "2010": 10},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 100, "2010": 100},
                                    "range": {"2009": 10, "2010": 10},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "room AC": {
                                "performance": {
                                    "typical": {"2009": 11, "2010": 11},
                                    "best": {"2009": 11, "2010": 11},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 11, "2010": 11},
                                    "best": {"2009": 11, "2010": 11},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 110, "2010": 110},
                                    "range": {"2009": 11, "2010": 11},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "ASHP": {
                                "performance": {
                                    "typical": {"2009": 12, "2010": 12},
                                    "best": {"2009": 12, "2010": 12},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 12, "2010": 12},
                                    "best": {"2009": 12, "2010": 12},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 120, "2010": 120},
                                    "range": {"2009": 12, "2010": 12},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "GSHP": {
                                "performance": {
                                    "typical": {"2009": 13, "2010": 13},
                                    "best": {"2009": 13, "2010": 13},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 13, "2010": 13},
                                    "best": {"2009": 13, "2010": 13},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 130, "2010": 130},
                                    "range": {"2009": 13, "2010": 13},
                                    "units": "years",
                                    "source": "EIA AEO"}}}},
                    "lighting": {
                        "linear fluorescent (LED)": {
                                "performance": {
                                    "typical": {"2009": 14, "2010": 14},
                                    "best": {"2009": 14, "2010": 14},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 14, "2010": 14},
                                    "best": {"2009": 14, "2010": 14},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 140, "2010": 140},
                                    "range": {"2009": 14, "2010": 14},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "general service (LED)": {
                                "performance": {
                                    "typical": {"2009": 15, "2010": 15},
                                    "best": {"2009": 15, "2010": 15},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 15, "2010": 15},
                                    "best": {"2009": 15, "2010": 15},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 150, "2010": 150},
                                    "range": {"2009": 15, "2010": 15},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "reflector (LED)": {
                                "performance": {
                                    "typical": {"2009": 16, "2010": 16},
                                    "best": {"2009": 16, "2010": 16},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 16, "2010": 16},
                                    "best": {"2009": 16, "2010": 16},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 160, "2010": 160},
                                    "range": {"2009": 16, "2010": 16},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "external (LED)": {
                                "performance": {
                                    "typical": {"2009": 17, "2010": 17},
                                    "best": {"2009": 17, "2010": 17},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 17, "2010": 17},
                                    "best": {"2009": 17, "2010": 17},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 170, "2010": 170},
                                    "range": {"2009": 17, "2010": 17},
                                    "units": "years",
                                    "source": "EIA AEO"}}}},
                    "natural gas": {
                        "water heating": {
                                "performance": {
                                    "typical": {"2009": 18, "2010": 18},
                                    "best": {"2009": 18, "2010": 18},
                                    "units": "EF",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 18, "2010": 18},
                                    "best": {"2009": 18, "2010": 18},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 180, "2010": 180},
                                    "range": {"2009": 18, "2010": 18},
                                    "units": "years",
                                    "source": "EIA AEO"}}}},
            "multi family home": {
                "electricity (grid)": {
                    "heating": {
                        "demand": {
                            "windows conduction": {
                                "performance": {
                                    "typical": {"2009": 19, "2010": 19},
                                    "best": {"2009": 19, "2010": 19},
                                    "units": "R Value",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 19, "2010": 19},
                                    "best": {"2009": 19, "2010": 19},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 190, "2010": 190},
                                    "range": {"2009": 19, "2010": 19},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "windows solar": {
                                "performance": {
                                    "typical": {"2009": 20, "2010": 20},
                                    "best": {"2009": 20, "2010": 20},
                                    "units": "SHGC",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 20, "2010": 20},
                                    "best": {"2009": 20, "2010": 20},
                                    "units": "2014$/sf",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 200, "2010": 200},
                                    "range": {"2009": 20, "2010": 20},
                                    "units": "years",
                                    "source": "EIA AEO"}}},
                        "supply": {
                            "boiler (electric)": {
                                "performance": {
                                    "typical": {"2009": 21, "2010": 21},
                                    "best": {"2009": 21, "2010": 21},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 21, "2010": 21},
                                    "best": {"2009": 21, "2010": 21},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 210, "2010": 210},
                                    "range": {"2009": 21, "2010": 21},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "ASHP": {
                                "performance": {
                                    "typical": {"2009": 22, "2010": 22},
                                    "best": {"2009": 22, "2010": 22},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 22, "2010": 22},
                                    "best": {"2009": 22, "2010": 22},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 220, "2010": 220},
                                    "range": {"2009": 22, "2010": 22},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                            "GSHP": {
                                "performance": {
                                    "typical": {"2009": 23, "2010": 23},
                                    "best": {"2009": 23, "2010": 23},
                                    "units": "COP",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 23, "2010": 23},
                                    "best": {"2009": 23, "2010": 23},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 230, "2010": 230},
                                    "range": {"2009": 23, "2010": 23},
                                    "units": "years",
                                    "source": "EIA AEO"}}}},
                    "lighting": {
                        "linear fluorescent (LED)": {
                                "performance": {
                                    "typical": {"2009": 24, "2010": 24},
                                    "best": {"2009": 24, "2010": 24},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 24, "2010": 24},
                                    "best": {"2009": 24, "2010": 24},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 240, "2010": 240},
                                    "range": {"2009": 24, "2010": 24},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "general service (LED)": {
                                "performance": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 250, "2010": 250},
                                    "range": {"2009": 25, "2010": 25},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "reflector (LED)": {
                                "performance": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 250, "2010": 250},
                                    "range": {"2009": 25, "2010": 25},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "external (LED)": {
                                "performance": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 250, "2010": 250},
                                    "range": {"2009": 25, "2010": 25},
                                    "units": "years",
                                    "source": "EIA AEO"}}}}}},
        "AIA_CZ4": {
            "multi family home": {
                "electricity (grid)": {
                    "lighting": {
                        "linear fluorescent (LED)": {
                                "performance": {
                                    "typical": {"2009": 24, "2010": 24},
                                    "best": {"2009": 24, "2010": 24},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 24, "2010": 24},
                                    "best": {"2009": 24, "2010": 24},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 240, "2010": 240},
                                    "range": {"2009": 24, "2010": 24},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "general service (LED)": {
                                "performance": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 25, "2010": 25},
                                    "best": {"2009": 25, "2010": 25},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 250, "2010": 250},
                                    "range": {"2009": 25, "2010": 25},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "reflector (LED)": {
                                "performance": {
                                    "typical": {"2009": 26, "2010": 26},
                                    "best": {"2009": 26, "2010": 26},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 26, "2010": 26},
                                    "best": {"2009": 26, "2010": 26},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 260, "2010": 260},
                                    "range": {"2009": 26, "2010": 26},
                                    "units": "years",
                                    "source": "EIA AEO"}},
                        "external (LED)": {
                                "performance": {
                                    "typical": {"2009": 27, "2010": 27},
                                    "best": {"2009": 27, "2010": 27},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 27, "2010": 27},
                                    "best": {"2009": 27, "2010": 27},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 270, "2010": 270},
                                    "range": {"2009": 27, "2010": 27},
                                    "units": "years",
                                    "source": "EIA AEO"}}}}}}}

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
                    "lighting": {"linear fluorescent (LED)": {
                                 "stock": {"2009": 11, "2010": 11},
                                 "energy": {"2009": 11, "2010": 11}},
                                 "general service (LED)": {
                                 "stock": {"2009": 12, "2010": 12},
                                 "energy": {"2009": 12, "2010": 12}},
                                 "reflector (LED)": {
                                 "stock": {"2009": 13, "2010": 13},
                                 "energy": {"2009": 13, "2010": 13}},
                                 "external (LED)": {
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
                    "lighting": {"linear fluorescent (LED)": {
                                 "stock": {"2009": 11, "2010": 11},
                                 "energy": {"2009": 11, "2010": 11}},
                                 "general service (LED)": {
                                 "stock": {"2009": 12, "2010": 12},
                                 "energy": {"2009": 12, "2010": 12}},
                                 "reflector (LED)": {
                                 "stock": {"2009": 13, "2010": 13},
                                 "energy": {"2009": 13, "2010": 13}},
                                 "external (LED)": {
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
                    "lighting": {"linear fluorescent (LED)": {
                                 "stock": {"2009": 11, "2010": 11},
                                 "energy": {"2009": 11, "2010": 11}},
                                 "general service (LED)": {
                                 "stock": {"2009": 12, "2010": 12},
                                 "energy": {"2009": 12, "2010": 12}},
                                 "reflector (LED)": {
                                 "stock": {"2009": 13, "2010": 13},
                                 "energy": {"2009": 13, "2010": 13}},
                                 "external (LED)": {
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
                    "lighting": {"linear fluorescent (LED)": {
                                 "stock": {"2009": 11, "2010": 11},
                                 "energy": {"2009": 11, "2010": 11}},
                                 "general service (LED)": {
                                 "stock": {"2009": 12, "2010": 12},
                                 "energy": {"2009": 12, "2010": 12}},
                                 "reflector (LED)": {
                                 "stock": {"2009": 13, "2010": 13},
                                 "energy": {"2009": 13, "2010": 13}},
                                 "external (LED)": {
                                 "stock": {"2009": 14, "2010": 14},
                                 "energy": {"2009": 14, "2010": 14}}}}}},
        "AIA_CZ4": {
            "multi family home": {
                "square footage": {"2009": 900, "2010": 1000},
                "electricity (grid)": {
                    "lighting": {"linear fluorescent (LED)": {
                                 "stock": {"2009": 11, "2010": 11},
                                 "energy": {"2009": 11, "2010": 11}},
                                 "general service (LED)": {
                                 "stock": {"2009": 12, "2010": 12},
                                 "energy": {"2009": 12, "2010": 12}},
                                 "reflector (LED)": {
                                 "stock": {"2009": 13, "2010": 13},
                                 "energy": {"2009": 13, "2010": 13}},
                                 "external (LED)": {
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
                    "product_lifetime": 10,
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
                    "energy_efficiency_units": "EF",
                    "product_lifetime": 10,
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
                    "product_lifetime": 10,
                    "end_use": "lighting",
                    "fuel_type": "electricity (grid)",
                    "technology_type": "supply",
                    "technology": ["linear fluorescent (LED)",
                                   "general service (LED)",
                                   "external (LED)"],
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
                    "product_lifetime": 10,
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
                    "product_lifetime": 10,
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
                    "product_lifetime": 10,
                    "end_use": ["heating", "secondary heating", "cooling"],
                    "fuel_type": "electricity (grid)",
                    "technology_type": "demand",
                    "technology": ["windows conduction", "windows solar"],
                    "bldg_type": "single family home",
                    "climate_zone": ["AIA_CZ1", "AIA_CZ2"]}]

    # List of selected "ok" measures above with certain inputs now specified
    # as probability distributions
    ok_measures_dist = [{"name": "distrib measure 1",
                         "installed_cost": ["normal", 25, 5],
                         "cost_units": "2014$/unit",
                         "energy_efficiency": {"AIA_CZ1": {"heating":
                                                           ["normal", 30, 1],
                                                           "cooling":
                                                           ["normal", 25, 2]},
                                               "AIA_CZ2": {"heating": 30,
                                                           "cooling":
                                                           ["normal", 15, 4]}},
                         "energy_efficiency_units": "COP",
                         "product_lifetime": 10,
                         "end_use": ["heating", "cooling"],
                         "fuel_type": "electricity (grid)",
                         "technology_type": "supply",
                         "technology": ["boiler (electric)",
                                        "ASHP", "GSHP", "room AC"],
                         "bldg_type": "single family home",
                         "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                        {"name": "distrib measure 2",
                         "installed_cost": ["lognormal", 3.22, 0.06],
                         "cost_units": "2014$/unit",
                         "energy_efficiency": ["normal", 25, 5],
                         "energy_efficiency_units": "EF",
                         "product_lifetime": 10,
                         "end_use": "water heating",
                         "fuel_type": "natural gas",
                         "technology_type": "supply",
                         "technology": None,
                         "bldg_type": "single family home",
                         "climate_zone": "AIA_CZ1"},
                        {"name": "distrib measure 2",
                         "installed_cost": ["normal", 10, 5],
                         "cost_units": "2014$/sf",
                         "energy_efficiency": {"windows conduction":
                                               ["lognormal", 2.29, 0.14],
                                               "windows solar":
                                               ["normal", 1, 0.1]},
                         "energy_efficiency_units": {"windows conduction":
                                                     "R Value",
                                                     "windows solar": "SHGC"},
                         "product_lifetime": 10,
                         "end_use": ["heating", "secondary heating",
                                     "cooling"],
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
                         "product_lifetime": 10,
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
                         "product_lifetime": 10,
                         "energy_efficiency_units": "COP",
                         "end_use": ["heating", "cooling"],
                         "fuel_type": "electricity (grid)",
                         "technology_type": "supply",
                         "technology": ["linear fluorescent (LED)",
                                        "general service (LED)",
                                        "external (LED)", "GSHP", "ASHP"],
                         "bldg_type": "single family home",
                         "climate_zone": ["AIA_CZ1", "AIA_CZ2"]}]

    # List of measures with attribute combinations that should not match any
    # of the key chains in the "sample_msegin" dict above
    blank_measures = [{"name": "blank measure 1",
                       "installed_cost": 10,
                       "cost_units": "2014$/unit",
                       "energy_efficiency": 10,
                       "energy_efficiency_units": "COP",
                       "product_lifetime": 10,
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
                       "product_lifetime": 10,
                       "end_use": ["heating", "cooling"],
                       "fuel_type": "electricity (grid)",
                       "technology_type": "supply",
                       "technology": ["linear fluorescent (LED)",
                                      "general service (LED)",
                                      "external (LED)"],
                       "bldg_type": "single family home",
                       "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                      {"name": "blank measure 3",
                       "installed_cost": 25,
                       "cost_units": "2014$/unit",
                       "energy_efficiency": 25,
                       "product_lifetime": 10,
                       "energy_efficiency_units": "lm/W",
                       "end_use": "lighting",
                       "fuel_type": "natural gas",
                       "technology_type": "supply",
                       "technology": ["linear fluorescent (LED)",
                                      "general service (LED)",
                                      "external (LED)"],
                       "bldg_type": "single family home",
                       "climate_zone": ["AIA_CZ1", "AIA_CZ2"]},
                      {"name": "blank measure 4",
                       "installed_cost": 25,
                       "cost_units": "2014$/unit",
                       "energy_efficiency": 25,
                       "product_lifetime": 10,
                       "energy_efficiency_units": "lm/W",
                       "end_use": "lighting",
                       "fuel_type": "solar",
                       "technology_type": "supply",
                       "technology": ["linear fluorescent (LED)",
                                      "general service (LED)",
                                      "external (LED)"],
                       "bldg_type": "single family home",
                       "climate_zone": "AIA_CZ1"}]

    # Master stock, energy, and cost information that should be generated by
    # "ok_measures" above using the "sample_msegin" dict
    ok_out = [{"stock": {"total": {"2009": 72, "2010": 72},
                         "competed": {"2009": 72, "2010": 72}},
               "energy": {"total": {"2009": 229.68, "2010": 230.4},
                          "competed": {"2009": 229.68, "2010": 230.4},
                          "efficient": {"2009": 117.0943, "2010": 117.4613}},
               "carbon": {"total": {"2009": 13056.63, "2010": 12941.16},
                          "competed": {"2009": 13056.63, "2010": 12941.16},
                          "efficient": {"2009": 6656.461, "2010": 6597.595}},
               "cost": {"baseline": {"stock": {"2009": 710,
                                               "2010": 710},
                                     "energy": {"2009": 2328.955,
                                                "2010": 2227.968},
                                     "carbon": {"2009": 430868.6,
                                                "2010": 427058.3},
                                     },
                        "measure": {"stock": {"2009": 1800,
                                              "2010": 1800},
                                    "energy": {"2009": 1187.336,
                                               "2010": 1135.851},
                                    "carbon": {"2009": 219663.2,
                                               "2010": 217720.6}}},
               "lifetime": {"2009": 75, "2010": 75}},
              {"stock": {"total": {"2009": 15, "2010": 15},
                         "competed": {"2009": 15, "2010": 15}},
               "energy": {"total": {"2009": 15.15, "2010": 15.15},
                          "competed": {"2009": 15.15, "2010": 15.15},
                          "efficient": {"2009": 10.908, "2010": 10.908}},
               "carbon": {"total": {"2009": 856.2139, "2010": 832.0021},
                          "competed": {"2009": 856.2139, "2010": 832.0021},
                          "efficient": {"2009": 616.474, "2010": 599.0415}},
               "cost": {"baseline": {"stock": {"2009": 270,
                                               "2010": 270},
                                     "energy": {"2009": 170.892,
                                                "2010": 163.317},
                                     "carbon": {"2009": 28255.06,
                                                "2010": 27456.07},
                                     },
                        "measure": {"stock": {"2009": 375,
                                              "2010": 375},
                                    "energy": {"2009": 123.0422,
                                               "2010": 117.5882},
                                    "carbon": {"2009": 20343.64,
                                               "2010": 19768.37}}},
               "lifetime": {"2009": 180, "2010": 180}},
              {"stock": {"total": {"2009": 148, "2010": 148},
                         "competed": {"2009": 148, "2010": 148}},
               "energy": {"total": {"2009": 472.12, "2010": 473.6},
                          "competed": {"2009": 472.12, "2010": 473.6},
                          "efficient": {"2009": 379.2272, "2010": 380.416}},
               "carbon": {"total": {"2009": 26838.62, "2010": 26601.27},
                          "competed": {"2009": 26838.62, "2010": 26601.27},
                          "efficient": {"2009": 21557.94, "2010": 21367.29}},
               "cost": {"baseline": {"stock": {"2009": 2972,
                                               "2010": 2972},
                                     "energy": {"2009": 4787.297,
                                                "2010": 4579.712},
                                     "carbon": {"2009": 885674.4,
                                                "2010": 877842.1},
                                     },
                        "measure": {"stock": {"2009": 3700,
                                              "2010": 3700},
                                    "energy": {"2009": 3845.364,
                                               "2010": 3678.623},
                                    "carbon": {"2009": 711412,
                                               "2010": 705120.7}}},
               "lifetime": {"2009": 200, "2010": 200}},
              {"stock": {"total": {"2009": 1600, "2010": 2000},
                         "competed": {"2009": 1600, "2010": 2000}},
               "energy": {"total": {"2009": 12.76, "2010": 12.8},
                          "competed": {"2009": 12.76, "2010": 12.8},
                          "efficient": {"2009": 3.509, "2010": 3.52}},
               "carbon": {"total": {"2009": 725.3681, "2010": 718.9534},
                          "competed": {"2009": 725.3681, "2010": 718.9534},
                          "efficient": {"2009": 199.4762, "2010": 197.7122}},
               "cost": {"baseline": {"stock": {"2009": 20400,
                                               "2010": 24600},
                                     "energy": {"2009": 129.3864,
                                                "2010": 123.776},
                                     "carbon": {"2009": 23937.15,
                                                "2010": 23725.46},
                                     },
                        "measure": {"stock": {"2009": 16000,
                                              "2010": 20000},
                                    "energy": {"2009": 35.58126,
                                               "2010": 34.0384},
                                    "carbon": {"2009": 6582.715,
                                               "2010": 6524.502}}},
               "lifetime": {"2009": 105, "2010": 105}},
              {"stock": {"total": {"2009": 600, "2010": 800},
                         "competed": {"2009": 600, "2010": 800}},
               "energy": {"total": {"2009": 6.38, "2010": 6.4},
                          "competed": {"2009": 6.38, "2010": 6.4},
                          "efficient": {"2009": 3.19, "2010": 3.2}},
               "carbon": {"total": {"2009": 362.684, "2010": 359.4767},
                          "competed": {"2009": 362.684, "2010": 359.4767},
                          "efficient": {"2009": 181.342, "2010": 179.7383}},
               "cost": {"baseline": {"stock": {"2009": 1200,
                                               "2010": 1600},
                                     "energy": {"2009": 64.6932,
                                                "2010": 61.888},
                                     "carbon": {"2009": 11968.57,
                                                "2010": 11862.73},
                                     },
                        "measure": {"stock": {"2009": 6000,
                                              "2010": 8000},
                                    "energy": {"2009": 32.3466,
                                               "2010": 30.944},
                                    "carbon": {"2009": 5984.287,
                                               "2010": 5931.365}}},
               "lifetime": {"2009": 20, "2010": 20}},
              {"stock": {"total": {"2009": 600, "2010": 800},
                         "competed": {"2009": 600, "2010": 800}},
               "energy": {"total": {"2009": 146.74, "2010": 147.2},
                          "competed": {"2009": 146.74, "2010": 147.2},
                          "efficient": {"2009": 55.29333, "2010": 55.46667}},
               "carbon": {"total": {"2009": 8341.733, "2010": 8267.964},
                          "competed": {"2009": 8341.733, "2010": 8267.964},
                          "efficient": {"2009": 3143.262, "2010": 3115.465}},
               "cost": {"baseline": {"stock": {"2009": 3100,
                                               "2010": 4133.33},
                                     "energy": {"2009": 1487.944,
                                                "2010": 1423.424},
                                     "carbon": {"2009": 275277.2,
                                                "2010": 272842.8},
                                     },
                        "measure": {"stock": {"2009": 6000,
                                              "2010": 8000},
                                    "energy": {"2009": 560.6744,
                                               "2010": 536.3627},
                                    "carbon": {"2009": 103727.6,
                                               "2010": 102810.3}}},
               "lifetime": {"2009": 51.67, "2010": 51.67}}]

    # Means and sampling Ns for energy and cost that should be generated by
    # "ok_measures_dist" above using the "sample_msegin" dict
    ok_out_dist = [[124.07, 50, 1860.93, 50], [11.96, 50, 375.32, 50],
                   [56.29, 50, 6448.37, 50]]

    # Master stock, energy, and cost information that should be generated by
    # "partial_measures" above using the "sample_msegin" dict
    partial_out = [{"stock": {"total": {"2009": 18, "2010": 18},
                              "competed": {"2009": 18, "2010": 18}},
                    "energy": {"total": {"2009": 57.42, "2010": 57.6},
                               "competed": {"2009": 57.42, "2010": 57.6},
                               "efficient": {"2009": 27.5616, "2010": 27.648}},
                    "carbon": {"total": {"2009": 3264.156, "2010": 3235.29},
                               "competed": {"2009": 3264.156, "2010": 3235.29},
                               "efficient": {"2009": 1566.795,
                                             "2010": 1552.939}},
                    "cost": {"baseline": {"stock": {"2009": 216,
                                                    "2010": 216},
                                          "energy": {"2009": 582.2388,
                                                     "2010": 556.992},
                                          "carbon": {"2009": 107717.2,
                                                     "2010": 106764.6},
                                          },
                             "measure": {"stock": {"2009": 450,
                                                   "2010": 450},
                                         "energy": {"2009": 279.4746,
                                                    "2010": 267.3562},
                                         "carbon": {"2009": 51704.24,
                                                    "2010": 51247}}},
                    "lifetime": {"2009": 120, "2010": 120}},
                   {"stock": {"total": {"2009": 52, "2010": 52},
                              "competed": {"2009": 52, "2010": 52}},
                    "energy": {"total": {"2009": 165.88, "2010": 166.4},
                               "competed": {"2009": 165.88, "2010": 166.4},
                               "efficient": {"2009": 67.1176, "2010": 67.328}},
                    "carbon": {"total": {"2009": 9429.785, "2010": 9346.394},
                               "competed": {"2009": 9429.785,
                                            "2010": 9346.394},
                               "efficient": {"2009": 3815.436,
                                             "2010": 3781.695}},
                    "cost": {"baseline": {"stock": {"2009": 526,
                                                    "2010": 526},
                                          "energy": {"2009": 1682.023,
                                                     "2010": 1609.088},
                                          "carbon": {"2009": 311182.9,
                                                     "2010": 308431},
                                          },
                             "measure": {"stock": {"2009": 1300,
                                                   "2010": 1300},
                                         "energy": {"2009": 680.5725,
                                                    "2010": 651.0618},
                                         "carbon": {"2009": 125909.4,
                                                    "2010": 124795.9}}},
                    "lifetime": {"2009": 80, "2010": 80}}]

    # Create a routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                self.assertAlmostEqual(dict1[k], dict2[k2], places=1)

    # Test for correct output from "ok_measures" input
    def test_mseg_ok(self):
        for idx, measure in enumerate(self.ok_measures):
            # Create an instance of the object based on ok measure info
            measure_instance = run.Measure(**measure)
            # Assert output dict is correct
            dict1 = measure_instance.mseg_find_partition(
                self.sample_msegin,
                self.sample_basein,
                "Technical potential")[0]
            dict2 = self.ok_out[idx]
            self.dict_check(dict1, dict2)

    # Test for correct output from "ok_measures_dist" input
    def test_mseg_ok_distrib(self):
        # Seed random number generator to yield repeatable results
        numpy.random.seed(1234)
        for idx, measure in enumerate(self.ok_measures_dist):
            # Create an instance of the object based on ok_dist measure info
            measure_instance = run.Measure(**measure)
            # Generate lists of energy and cost output values
            test_e = measure_instance.mseg_find_partition(
                self.sample_msegin, self.sample_basein,
                "Technical potential")[0]["energy"]["efficient"]["2009"]
            test_c = measure_instance.mseg_find_partition(
                self.sample_msegin, self.sample_basein,
                "Technical potential")[0]["cost"]["measure"]["stock"]["2009"]
            # Calculate mean values from output lists for testing
            param_e = round(sum(test_e) / len(test_e), 2)
            param_c = round(sum(test_c) / len(test_c), 2)
            # Check mean values and length of output lists to ensure correct
            self.assertEqual([param_e, len(test_e), param_c, len(test_c)],
                             self.ok_out_dist[idx])

    # Test for correct output from "partial_measures" input
    def test_mseg_partial(self):
        for idx, measure in enumerate(self.partial_measures):
            # Create an instance of the object based on partial measure info
            measure_instance = run.Measure(**measure)
            # Assert output dict is correct
            dict1 = measure_instance.mseg_find_partition(
                self.sample_msegin,
                self.sample_basein,
                "Technical potential")[0]
            dict2 = self.partial_out[idx]
            self.dict_check(dict1, dict2)

    # Test for correct output from "blank_measures" input
    def test_mseg_blank(self):
        for idx, measure in enumerate(self.blank_measures):
            # Create an instance of the object based on blank measure info
            measure_instance = run.Measure(**measure)
            # Assert output dict is correct
            with self.assertRaises(KeyError):
                measure_instance.mseg_find_partition(
                    self.sample_msegin,
                    self.sample_basein,
                    "Technical potential")


class PrioritizationMetricsTest(unittest.TestCase):
    """ Test the operation of the calc_metric_update function to
    verify measure master microsegment inputs yield expected savings
    and prioritization metrics outputs """

    # Sample measure for use in testing
    sample_measure = {"name": "sample measure 1",
                      "product_lifetime": 2,
                      "end_use": ["heating", "cooling"],
                      "fuel_type": "electricity (grid)",
                      "technology_type": "supply",
                      "technology": ["boiler (electric)",
                                     "ASHP", "GSHP", "room AC"],
                      "bldg_type": "single family home",
                      "climate_zone": ["AIA_CZ1", "AIA_CZ2"]}

    # Discount rate used for testing
    ok_rate = 0.07

    # Create an "ok" master microsegment input dict to use in calculating
    # savings and prioritization metrics outputs to be tested
    ok_master_mseg = {"stock": {"total": {"2009": 10, "2010": 20},
                                "competed": {"2009": 5, "2010": 10}},
                      "energy": {"total": {"2009": 20, "2010": 30},
                                 "competed": {"2009": 10, "2010": 15},
                                 "efficient": {"2009": 5, "2010": 10}},
                      "carbon": {"total": {"2009": 200, "2010": 300},
                                 "competed": {"2009": 100, "2010": 150},
                                 "efficient": {"2009": 50, "2010": 100}},
                      "cost": {"baseline": {"stock": {"2009": 10,
                                                      "2010": 15},
                                            "energy": {"2009": 20,
                                                       "2010": 25},
                                            "carbon": {"2009": 30,
                                                       "2010": 35}},
                               "measure": {"stock": {"2009": 15,
                                                     "2010": 20},
                                           "energy": {"2009": 10,
                                                      "2010": 20},
                                           "carbon": {"2009": 25,
                                                      "2010": 25}}},
                      "lifetime": {"2009": 1, "2010": 1}}

    # Savings/prioritization metrics dict keys and values that should be
    # yielded by above master microsegment dict input
    ok_out = {"stock": {"cost savings": {"2009": numpy.array([-5, 10, 0]),
                                         "2010": numpy.array([-5, 15, 0])}},
              "energy": {"savings": {"2009": numpy.array([0, 5, 5]),
                                     "2010": numpy.array([0, 5, 5])},
                         "cost savings": {"2009": numpy.array([0, 10, 10]),
                                          "2010": numpy.array([0, 5, 5])}},
              "carbon": {"savings": {"2009": numpy.array([0, 50, 50]),
                                     "2010": numpy.array([0, 50, 50])},
                         "cost savings": {"2009": numpy.array([0, 5, 5]),
                                          "2010": numpy.array([0, 10, 10])}},
              "metrics": {"irr (w/ energy $)":
                          {"2009": 3.45, "2010": 3.24},
                          "irr (w/ energy and carbon $)":
                          {"2009": 4.54, "2010": 5.46},
                          "payback (w/ energy $)":
                          {"2009": 0.25, "2010": 0.25},
                          "payback (w/ energy and carbon $)":
                          {"2009": 0.2, "2010": 0.17},
                          "cce": {"2009": 0.48, "2010": 1.00},
                          "cce (w/ carbon $ benefits)":
                          {"2009": 1.48, "2010": 3.00},
                          "ccc": {"2009": 0.05, "2010": 0.10},
                          "ccc (w/ energy $ benefits)":
                          {"2009": 0.25, "2010": 0.20}}}

    # Create a routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                # Expect numpy arrays and/or point values
                if type(i) != int and type(i) != float:
                    numpy.testing.assert_almost_equal(
                        i, i2, decimal=2)
                else:
                    self.assertAlmostEqual(dict1[k], dict2[k2],
                                           places=2)

    # Test for correct output from "ok_master_mseg" input
    def test_metrics_ok(self):
        # Create a measure instance to use in the test
        measure_instance = run.Measure(**self.sample_measure)
        # Set the master microsegment for the measure instance
        # to the "ok_master_mseg" dict defined above
        measure_instance.master_mseg = self.ok_master_mseg
        # Set measure "life_meas" parameter based on the sample
        # "product_lifetime" attribute (* Note: this is necessary because
        # "life_meas" is set in the "mseg_find_partition" function, which is
        # not being executed here)
        measure_instance.life_meas = measure_instance.product_lifetime
        # Set measure "life_base" parameter using the measure "master_mseg"
        # information (* Note: this is necessary because "life_base" is set
        # in the "mseg_find_partition" function, which is not being excuted
        # here)
        measure_instance.life_base = measure_instance.master_mseg["lifetime"]
        # Assert that output dict is correct
        dict1 = measure_instance.calc_metric_update(self.ok_rate)
        dict2 = self.ok_out
        self.dict_check(dict1, dict2)


class MetricUpdateTest(unittest.TestCase):
    """ Test the operation of the metrics_update function to
    verify cashflow inputs generate expected prioritization metric outputs """

    # Sample measure for use in testing
    sample_measure = {"name": "sample measure 1",
                      "end_use": ["heating", "cooling"],
                      "fuel_type": "electricity (grid)",
                      "technology_type": "supply",
                      "technology": ["boiler (electric)",
                                     "ASHP", "GSHP", "room AC"],
                      "bldg_type": "single family home",
                      "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
                      "life_base": 1,
                      "life_meas": 2}

    # Define ok test inputs

    # Test discount rate
    ok_rate = 0.07
    # Test stock cashflow input
    ok_s_list = numpy.array([-10, 0, 0, 10, 0, 0, 0])
    # Test stock + energy cashflow input
    ok_se_list = numpy.array([-10, 5, 5, 15, 5, 5, 5])
    # Test stock + carbon cashflow input
    ok_sc_list = numpy.array([-10, 10, 10, 20, 10, 10, 10])
    # Test stock + energy + carbon cashflow input
    ok_sec_list = numpy.array([-10, 15, 15, 25, 15, 15, 15])
    # Test energy savings input
    ok_esave_list = numpy.array([0, 25, 25, 25, 25, 25, 25])
    # Test carbon savings input
    ok_csave_list = numpy.array([0, 50, 50, 50, 50, 50, 50])

    # Correct metric output values that should be yielded by using "ok"
    # inputs above
    ok_out = numpy.array([0.62, 1.59, 2, 0.67, -0.02, 0.38, -0.01, 0.09])

    # Test for correct outputs given "ok" inputs above
    def test_metric_updates(self):
        # Create a sample measure instance using sample_measure
        measure_instance = run.Measure(**self.sample_measure)
        # Test that "ok" inputs yield correct output metric values
        # (* Note: outputs should be formatted as numpy arrays)
        numpy.testing.assert_almost_equal(
            measure_instance.metric_update(self.ok_rate, self.ok_s_list,
                                           self.ok_se_list, self.ok_sc_list,
                                           self.ok_sec_list,
                                           self.ok_esave_list,
                                           self.ok_csave_list), self.ok_out,
            decimal=2)


class PaybackTest(unittest.TestCase):
    """ Test the operation of the payback function to
    verify cashflow input generates expected payback output """

    # Sample measure for use in testing
    sample_measure = {"name": "sample measure 1",
                      "end_use": ["heating", "cooling"],
                      "fuel_type": "electricity (grid)",
                      "technology_type": "supply",
                      "technology": ["boiler (electric)",
                                     "ASHP", "GSHP", "room AC"],
                      "bldg_type": "single family home",
                      "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
                      "life_base": 1,
                      "life_meas": 2}

    # Define ok test cashflow inputs
    ok_cashflows = [[-10, 1, 1, 1, 1, 5, 7, 8],
                    [-10, 14, 2, 3, 4],
                    [-10, 0, 1, 2],
                    [10, 4, 7, 8, 10]]

    # Correct outputs that should be yielded by above "ok" cashflow inputs
    ok_out = [5.14, 0.71, 999, 0]

    # Test for correct outputs given "ok" input cashflows above
    def test_cashflow_paybacks(self):
        # Create a sample measure instance using sample_measure
        measure_instance = run.Measure(**self.sample_measure)
        # Test that "ok" input cashflows yield correct output payback values
        for idx, cf in enumerate(self.ok_cashflows):
            self.assertAlmostEqual(measure_instance.payback(cf),
                                   self.ok_out[idx], places=2)


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == "__main__":
    main()
