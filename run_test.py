#!/usr/bin/env python3

""" Tests for running the engine """

# Import code to be tested
import run

# Import needed packages
import unittest
import numpy
import copy
import itertools


class CommonTestMeasures(object):
    """Class of common sample measures for tests.

    Attributes:
        sample_measure (dict): Sample residential measure #1.
        sample_measure2 (dict): Sample residential measure #2.
        sample_measure3 (dict): Sample commercial measure #1.
    """

    def __init__(self):
        self.sample_measure = {
            "name": "sample measure 1",
            "active": 1,
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "bldg_type": ["single family home"],
            "fuel_type": {"primary": ["electricity (grid)"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["heating", "cooling"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": ["boiler (electric)",
                           "ASHP", "GSHP", "room AC"],
                           "secondary": None},
            "markets": {
                "Technical potential": {
                    "master_mseg": {},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {},
                        "competed choice parameters": {},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}
                    },
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {},
                        "competed choice parameters": {},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}},
                    "mseg_out_break": {}}}}
        self.sample_measure2 = {
            "name": "sample measure 2",
            "active": 1,
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "bldg_type": ["single family home"],
            "fuel_type": {"primary": ["electricity (grid)"],
                          "secondary": ["electricity (grid)"]},
            "fuel_switch_to": None,
            "end_use": {"primary": ["heating", "cooling"],
                        "secondary": ["lighting"]},
            "technology_type": {"primary": "supply",
                                "secondary": "supply"},
            "technology": {"primary": ["boiler (electric)",
                           "ASHP", "GSHP", "room AC"],
                           "secondary": ["general service (LED)"]},
            "markets": {
                "Technical potential": {
                    "master_mseg": {},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {},
                        "competed choice parameters": {},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}},
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {},
                        "competed choice parameters": {},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}},
                    "mseg_out_break": {}}}}
        self.sample_measure3 = {
            "name": "sample measure 3 (commercial)",
            "active": 1,
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "bldg_type": ["assembly"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["heating", "cooling"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": ["boiler (electric)",
                           "ASHP", "GSHP", "room AC"],
                           "secondary": None},
            "markets": {
                "Technical potential": {
                    "master_mseg": {},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {},
                        "competed choice parameters": {},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}},
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {},
                        "competed choice parameters": {},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}},
                    "mseg_out_break": {}}}}


class CommonMethods(object):
    """Define common methods for use in all tests below."""

    def dict_check(self, dict1, dict2):
        """Check the equality of two dicts.

        Args:
            dict1 (dict): First dictionary to be compared
            dict2 (dict): Second dictionary to be compared

        Raises:
            AssertionError: If dictionaries are not equal.
        """
        # zip() and zip_longest() produce tuples for the items
        # identified, where in the case of a dict, the first item
        # in the tuple is the key and the second item is the value;
        # in the case where the dicts are not of identical size,
        # zip_longest() will use the fill value created below as a
        # substitute in the dict that has missing content; this
        # value is given as a tuple to be of comparable structure
        # to the normal output from zip_longest()
        fill_val = ('substituted entry', 5.2)

        # In this structure, k and k2 are the keys that correspond to
        # the dicts or unitary values that are found in i and i2,
        # respectively, at the current level of the recursive
        # exploration of dict1 and dict2, respectively
        for (k, i), (k2, i2) in itertools.zip_longest(sorted(dict1.items()),
                                                      sorted(dict2.items()),
                                                      fillvalue=fill_val):

            # Confirm that at the current location in the dict structure,
            # the keys are equal; this should fail if one of the dicts
            # is empty, is missing section(s), or has different key names
            self.assertEqual(k, k2)

            # If the recursion has not yet reached the terminal/leaf node
            if isinstance(i, dict):
                # Test that the dicts from the current keys are equal
                self.assertCountEqual(i, i2)
                # Continue to recursively traverse the dict
                self.dict_check(i, i2)

            # At the terminal/leaf node, formatted as a numpy array
            # (for input uncertainty test cases)
            elif isinstance(i, numpy.ndarray):
                self.assertTrue(type(i) == type(i2))
                numpy.testing.assert_array_almost_equal(
                    i, i2, decimal=2)

            # At the terminal/leaf node, formatted as a point value
            else:
                self.assertAlmostEqual(i, i2, places=2)


class TestMeasureInit(unittest.TestCase):
    """Ensure that measure attributes are correctly initiated.

    Attributes:
        sample_measure (object): Residential sample measure object.
        attribute_dict (dict): Dict of sample measure attributes.
    """

    @classmethod
    def setUpClass(cls):
        """Define objects/variables for use across all class functions."""
        handyvars = run.UsefulVars()
        cls.sample_measure = CommonTestMeasures().sample_measure
        measure_instance = run.Measure(handyvars, **cls.sample_measure)
        cls.attribute_dict = measure_instance.__dict__

    def test_attributes(self):
        """Compare object attributes to keys from input dict."""
        for key in self.sample_measure.keys():
            self.assertEqual(
                self.attribute_dict[key], self.sample_measure[key])


class OutputBreakoutDictWalkTest(unittest.TestCase, CommonMethods):
    """Test operation of 'out_break_walk' function.

    Verify that function properly applies a climate zone/building
    type/end use partition to a total energy or carbon
    market/savings value.

    Attributes:
        a_run (object): Sample analysis engine object.
        ok_total (dict): Sample unpartitioned measure results data.
        ok_partitions (dict): Sample results partitioning fraction.
        ok_out (dict): Sample partitioned measure results data.
    """

    @classmethod
    def setUpClass(cls):
        """Define objects/variables for use across all class functions."""
        handyvars = run.UsefulVars()
        sample_measure = CommonTestMeasures().sample_measure
        measure_list = [run.Measure(handyvars, **sample_measure)]
        cls.a_run = run.Engine(handyvars, measure_list)
        cls.ok_total = {"2009": 100, "2010": 100}
        cls.ok_partitions = {
            "AIA CZ1": {
                "Residential": {
                    "Heating": {"2009": .10, "2010": .10},
                    "Cooling": {"2009": .15, "2010": .15}},
                "Commercial": {
                    "Heating": {"2009": .20, "2010": .20},
                    "Cooling": {"2009": .25, "2010": .25}}},
            "AIA CZ2": {
                "Residential": {
                    "Heating": {"2009": .30, "2010": .30},
                    "Cooling": {"2009": .35, "2010": .35}},
                "Commercial": {
                    "Heating": {"2009": .40, "2010": .40},
                    "Cooling": {"2009": .45, "2010": .45}}}}
        cls.ok_out = {
            "AIA CZ1": {
                "Residential": {
                    "Heating": {"2009": 10, "2010": 10},
                    "Cooling": {"2009": 15, "2010": 15}},
                "Commercial": {
                    "Heating": {"2009": 20, "2010": 20},
                    "Cooling": {"2009": 25, "2010": 25}}},
            "AIA CZ2": {
                "Residential": {
                    "Heating": {"2009": 30, "2010": 30},
                    "Cooling": {"2009": 35, "2010": 35}},
                "Commercial": {
                    "Heating": {"2009": 40, "2010": 40},
                    "Cooling": {"2009": 45, "2010": 45}}}}

    def test_ok(self):
        """Test for correct function output given valid inputs."""
        dict1 = self.a_run.out_break_walk(
            self.ok_partitions, self.ok_total)
        dict2 = self.ok_out
        self.dict_check(dict1, dict2)


class PrioritizationMetricsTest(unittest.TestCase, CommonMethods):
    """Test the operation of the 'calc_savings_metrics' function.

    Verify that measure master microsegment inputs yield expected savings
    and financial metrics outputs.

    Attributes:
        handyvars (object): Useful variables across the class.
        sample_measure_res (object): Sample residential measure data.
        sample_measure_com (object): Sample commercial measure data.
        test_adopt_scheme (string): Sample consumer adoption scheme.
        ok_rate (float): Sample discount rate.
        ok_master_mseg_point (dict): Sample measure master microsegment
            including all point values at terminal leaf nodes.
        ok_master_mseg_dist1 (dict): Sample measure master microsegment
            including energy, carbon, and energy/carbon cost arrays.
        ok_master_mseg_dist2 (dict): Sample measure master microsegment
            including stock cost array.
        ok_master_mseg_dist3 (dict): Sample measure master microsegment
            including measure lifetime array.
        ok_master_mseg_dist4 (dict): Sample measure master microsegment
            including stock cost and measure lifetime array.
        ok_out_point_res (dict): Measure attribute update status, savings,
            and portfolio/consumer-level financial metrics that should be
            generated given 'ok_master_mseg_point' with a residential sample
            measure.
        ok_out_point_com (dict): Measure attribute update status, savings,
            and portfolio/consumer-level financial metrics that should be
            generated given 'ok_master_mseg_point' with a residential sample
            measure.
        ok_out_dist1 (dict): Measure attribute update status, savings,
            and portfolio/consumer-level financial metrics that should be
            generated given 'ok_master_mseg_dist1' with a residential sample
            measure.
        ok_out_dist2 (dict): Measure attribute update status, savings,
            and portfolio/consumer-level financial metrics that should be
            generated given 'ok_master_mseg_dist2' with a residential sample
            measure.
        ok_out_dist3 (dict): Measure attribute update status, savings,
            and portfolio/consumer-level financial metrics that should be
            generated given 'ok_master_mseg_dist3' with a residential sample
            measure.
        ok_out_dist4 (dict): Measure attribute update status, savings,
            and portfolio/consumer-level financial metrics that should be
            generated given 'ok_master_mseg_dist4' with a residential sample
            measure.
    """

    @classmethod
    def setUpClass(cls):
        """Define objects/variables for use across all class functions."""
        cls.handyvars = run.UsefulVars()
        # Reset aeo_years
        cls.handyvars.aeo_years = ["2009", "2010"]
        cls.sample_measure_res = CommonTestMeasures().sample_measure
        cls.sample_measure_com = CommonTestMeasures().sample_measure3
        cls.test_adopt_scheme = 'Max adoption potential'
        cls.ok_rate = 0.07
        cls.ok_master_mseg_point = {
            "stock": {
                "total": {
                    "all": {"2009": 10, "2010": 20},
                    "measure": {"2009": 15, "2010": 25}},
                "competed": {
                    "all": {"2009": 5, "2010": 10},
                    "measure": {"2009": 5, "2010": 10}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 200, "2010": 300},
                    "efficient": {"2009": 50, "2010": 100}},
                "competed": {
                    "baseline": {"2009": 100, "2010": 150},
                    "efficient": {"2009": 0, "2010": 50}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 200, "2010": 300},
                    "efficient": {"2009": 50, "2010": 100}},
                "competed": {
                    "baseline": {"2009": 100, "2010": 150},
                    "efficient": {"2009": 50, "2010": 100}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 10, "2010": 15},
                        "efficient": {"2009": 15, "2010": 25}},
                    "competed": {
                        "baseline": {"2009": 10, "2010": 15},
                        "efficient": {"2009": 15, "2010": 25}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 20, "2010": 35},
                        "efficient": {"2009": 10, "2010": 20}},
                    "competed": {
                        "baseline": {"2009": 20, "2010": 35},
                        "efficient": {"2009": 10, "2010": 20}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 30, "2010": 40},
                        "efficient": {"2009": 25, "2010": 25}},
                    "competed": {
                        "baseline": {"2009": 30, "2010": 40},
                        "efficient": {"2009": 25, "2010": 25}}}},
            "lifetime": {
                "baseline": {"2009": 1, "2010": 1},
                "measure": 2}}
        cls.ok_master_mseg_dist1 = {
            "stock": {
                "total": {
                    "all": {"2009": 10, "2010": 20},
                    "measure": {"2009": 15, "2010": 25}},
                "competed": {
                    "all": {"2009": 5, "2010": 10},
                    "measure": {"2009": 5, "2010": 10}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 200, "2010": 300},
                    "efficient": {
                        "2009": numpy.array([16, 27, 31, 6, 51]),
                        "2010": numpy.array([106, 95, 81, 11, 124])}},
                "competed": {
                    "baseline": {"2009": 100, "2010": 150},
                    "efficient": {
                        "2009": numpy.array([6, 7, 1, 16, 1]),
                        "2010": numpy.array([36, 45, 61, 5, 54])}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 200, "2010": 300},
                    "efficient": {
                        "2009": numpy.array([50.6, 57.7, 58.1, 50, 51.1]),
                        "2010": numpy.array(
                            [100.6, 108.7, 105.1, 105, 106.1])}},
                "competed": {
                    "baseline": {"2009": 100, "2010": 150},
                    "efficient": {
                        "2009": numpy.array([50.6, 57.7, 58.1, 50, 51.1]),
                        "2010": numpy.array(
                            [100.6, 108.7, 105.1, 105, 106.1])}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 10, "2010": 15},
                        "efficient": {"2009": 15, "2010": 25}},
                    "competed": {
                        "baseline": {"2009": 10, "2010": 15},
                        "efficient": {"2009": 15, "2010": 25}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 20, "2010": 35},
                        "efficient": {
                            "2009": numpy.array([9.1, 8.7, 7.7, 11.2, 12.5]),
                            "2010": numpy.array(
                                [20.1, 18.7, 21.7, 21.2, 22.5])}},
                    "competed": {
                        "baseline": {"2009": 20, "2010": 35},
                        "efficient": {
                            "2009": numpy.array([9.1, 8.7, 7.7, 11.2, 12.5]),
                            "2010": numpy.array(
                                [20.1, 18.7, 21.7, 21.2, 22.5])}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 30, "2010": 40},
                        "efficient": {
                            "2009": numpy.array(
                                [25.1, 24.7, 23.7, 31.2, 18.5]),
                            "2010": numpy.array(
                                [20.1, 18.7, 21.7, 21.2, 22.5])}},
                    "competed": {
                        "baseline": {"2009": 30, "2010": 40},
                        "efficient": {
                            "2009": numpy.array(
                                [25.1, 24.7, 23.7, 31.2, 18.5]),
                            "2010": numpy.array(
                                [20.1, 18.7, 21.7, 21.2, 22.5])}}}},
            "lifetime": {
                "baseline": {"2009": 1, "2010": 1},
                "measure": 2}}
        cls.ok_master_mseg_dist2 = {
            "stock": {
                "total": {
                    "all": {"2009": 10, "2010": 20},
                    "measure": {"2009": 15, "2010": 25}},
                "competed": {
                    "all": {"2009": 5, "2010": 10},
                    "measure": {"2009": 5, "2010": 10}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 200, "2010": 300},
                    "efficient": {"2009": 50, "2010": 100}},
                "competed": {
                    "baseline": {"2009": 100, "2010": 150},
                    "efficient": {"2009": 0, "2010": 50}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 200, "2010": 300},
                    "efficient": {"2009": 50, "2010": 100}},
                "competed": {
                    "baseline": {"2009": 100, "2010": 150},
                    "efficient": {"2009": 50, "2010": 100}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 10, "2010": 15},
                        "efficient": {
                            "2009": numpy.array(
                                [15.1, 12.7, 14.1, 14.2, 15.5]),
                            "2010": numpy.array([20.1, 18.7, 21.7, 19.2, 20.5])
                        }},
                    "competed": {
                        "baseline": {"2009": 10, "2010": 15},
                        "efficient": {
                            "2009": numpy.array(
                                [15.1, 12.7, 14.1, 14.2, 15.5]),
                            "2010": numpy.array([20.1, 18.7, 21.7, 19.2, 20.5])
                        }}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 20, "2010": 35},
                        "efficient": {"2009": 10, "2010": 20}},
                    "competed": {
                        "baseline": {"2009": 20, "2010": 35},
                        "efficient": {"2009": 10, "2010": 20}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 30, "2010": 40},
                        "efficient": {"2009": 25, "2010": 25}},
                    "competed": {
                        "baseline": {"2009": 30, "2010": 40},
                        "efficient": {"2009": 25, "2010": 25}}}},
            "lifetime": {
                "baseline": {"2009": 1, "2010": 1},
                "measure": 2}}
        cls.ok_master_mseg_dist3 = {
            "stock": {
                "total": {
                    "all": {"2009": 10, "2010": 20},
                    "measure": {"2009": 15, "2010": 25}},
                "competed": {
                    "all": {"2009": 5, "2010": 10},
                    "measure": {"2009": 5, "2010": 10}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 200, "2010": 300},
                    "efficient": {"2009": 50, "2010": 100}},
                "competed": {
                    "baseline": {"2009": 100, "2010": 150},
                    "efficient": {"2009": 0, "2010": 50}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 200, "2010": 300},
                    "efficient": {"2009": 50, "2010": 100}},
                "competed": {
                    "baseline": {"2009": 100, "2010": 150},
                    "efficient": {"2009": 50, "2010": 100}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 10, "2010": 15},
                        "efficient": {"2009": 15, "2010": 25}},
                    "competed": {
                        "baseline": {"2009": 10, "2010": 15},
                        "efficient": {"2009": 15, "2010": 25}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 20, "2010": 35},
                        "efficient": {"2009": 10, "2010": 20}},
                    "competed": {
                        "baseline": {"2009": 20, "2010": 35},
                        "efficient": {"2009": 10, "2010": 20}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 30, "2010": 40},
                        "efficient": {"2009": 25, "2010": 25}},
                    "competed": {
                        "baseline": {"2009": 30, "2010": 40},
                        "efficient": {"2009": 25, "2010": 25}}}},
            "lifetime": {"baseline": {"2009": 1, "2010": 1},
                         "measure": numpy.array([0.5, 1.2, 2.1, 2.2, 5.6])}}
        cls.ok_master_mseg_dist4 = {
            "stock": {
                "total": {
                    "all": {"2009": 10, "2010": 20},
                    "measure": {"2009": 15, "2010": 25}},
                "competed": {
                    "all": {"2009": 5, "2010": 10},
                    "measure": {"2009": 5, "2010": 10}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 200, "2010": 300},
                    "efficient": {"2009": 50, "2010": 100}},
                "competed": {
                    "baseline": {"2009": 100, "2010": 150},
                    "efficient": {"2009": 0, "2010": 50}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 200, "2010": 300},
                    "efficient": {"2009": 50, "2010": 100}},
                "competed": {
                    "baseline": {"2009": 100, "2010": 150},
                    "efficient": {"2009": 50, "2010": 100}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 10, "2010": 15},
                        "efficient": {
                            "2009": numpy.array(
                                [15.1, 12.7, 14.1, 14.2, 15.5]),
                            "2010": numpy.array([20.1, 18.7, 21.7, 19.2, 20.5])
                        }},
                    "competed": {
                        "baseline": {"2009": 10, "2010": 15},
                        "efficient": {
                            "2009": numpy.array(
                                [15.1, 12.7, 14.1, 14.2, 15.5]),
                            "2010": numpy.array([20.1, 18.7, 21.7, 19.2, 20.5])
                        }}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 20, "2010": 35},
                        "efficient": {"2009": 10, "2010": 20}},
                    "competed": {
                        "baseline": {"2009": 20, "2010": 35},
                        "efficient": {"2009": 10, "2010": 20}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 30, "2010": 40},
                        "efficient": {"2009": 25, "2010": 25}},
                    "competed": {
                        "baseline": {"2009": 30, "2010": 40},
                        "efficient": {"2009": 25, "2010": 25}}}},
            "lifetime": {"baseline": {"2009": 1, "2010": 1},
                         "measure": numpy.array([0.5, 1.2, 2.1, 2.2, 5.6])}}
        cls.ok_out_point_res = [{
            "savings and portfolio metrics": {
                "Technical potential": {
                    "uncompeted": True, "competed": True},
                "Max adoption potential": {
                    "uncompeted": False, "competed": True}},
            "consumer metrics": False},
            {
            "stock": {
                "cost savings (total)": {"2009": -5, "2010": -10},
                "cost savings (annual)": {"2009": -5, "2010": -10}},
            "energy": {
                "savings (total)": {"2009": 150, "2010": 200},
                "savings (annual)": {"2009": 100, "2010": 100},
                "cost savings (total)": {"2009": 10, "2010": 15},
                "cost savings (annual)": {"2009": 10, "2010": 15}},
            "carbon": {
                "savings (total)": {"2009": 150, "2010": 200},
                "savings (annual)": {"2009": 50, "2010": 50},
                "cost savings (total)": {"2009": 5, "2010": 15},
                "cost savings (annual)": {"2009": 5, "2010": 15}}},
            {
            "cce": {"2009": -0.02, "2010": -0.02},
            "cce (w/ carbon cost benefits)": {
                "2009": -0.07, "2010": -0.17},
            "ccc": {"2009": -4.81e-08, "2010": -4.45e-08},
            "ccc (w/ energy cost benefits)": {
                "2009": -2.48e-07, "2010": -3.44e-07}},
            {
            "anpv": {
                "stock cost": {
                    "residential": {
                        "2009": numpy.pmt(0.07, 2, 0.8691589),
                        "2010": numpy.pmt(0.07, 2, 0.4018692)},
                    "commercial": {"2009": None, "2010": None}},
                "energy cost": {
                    "residential": {
                        "2009": numpy.pmt(0.07, 2, 3.616036),
                        "2010": numpy.pmt(0.07, 2, 2.712027)},
                    "commercial": {"2009": None, "2010": None}},
                "carbon cost": {
                    "residential": {
                        "2009": numpy.pmt(0.07, 2, 1.808018),
                        "2010": numpy.pmt(0.07, 2, 2.712027)},
                    "commercial": {"2009": None, "2010": None}}},
            "irr (w/ energy costs)": {
                "2009": 3.45, "2010": 2.44},
            "irr (w/ energy and carbon costs)": {
                "2009": 4.54, "2010": 4.09},
            "payback (w/ energy costs)": {
                "2009": 0.25, "2010": 0.33},
            "payback (w/ energy and carbon costs)": {
                "2009": 0.2, "2010": 0.22}}]
        cls.ok_out_point_com = [{
            "savings and portfolio metrics": {
                "Technical potential": {
                    "uncompeted": True, "competed": True},
                "Max adoption potential": {
                    "uncompeted": False, "competed": True}},
            "consumer metrics": False},
            {
            "stock": {
                "cost savings (total)": {"2009": -5, "2010": -10},
                "cost savings (annual)": {"2009": -5, "2010": -10}},
            "energy": {
                "savings (total)": {"2009": 150, "2010": 200},
                "savings (annual)": {"2009": 100, "2010": 100},
                "cost savings (total)": {"2009": 10, "2010": 15},
                "cost savings (annual)": {"2009": 10, "2010": 15}},
            "carbon": {
                "savings (total)": {"2009": 150, "2010": 200},
                "savings (annual)": {"2009": 50, "2010": 50},
                "cost savings (total)": {"2009": 5, "2010": 15},
                "cost savings (annual)": {"2009": 5, "2010": 15}}},
            {
            "cce": {"2009": -0.02, "2010": -0.02},
            "cce (w/ carbon cost benefits)": {
                "2009": -0.07, "2010": -0.17},
            "ccc": {"2009": -4.81e-08, "2010": -4.45e-08},
            "ccc (w/ energy cost benefits)": {
                "2009": -2.48e-07, "2010": -3.44e-07}},
            {
            "anpv": {
                "stock cost": {
                    "residential": {"2009": None, "2010": None},
                    "commercial": {
                        "2009": {
                            "rate 1": numpy.pmt(10.0, 2, -0.8181818),
                            "rate 2": numpy.pmt(1.0, 2, 0),
                            "rate 3": numpy.pmt(0.45, 2, 0.3793103),
                            "rate 4": numpy.pmt(0.25, 2, 0.6),
                            "rate 5": numpy.pmt(0.15, 2, 0.7391304),
                            "rate 6": numpy.pmt(0.065, 2, 0.8779343),
                            "rate 7": -0.5},
                        "2010": {
                            "rate 1": numpy.pmt(10.0, 2, -0.8636364),
                            "rate 2": numpy.pmt(1.0, 2, -0.25),
                            "rate 3": numpy.pmt(0.45, 2, 0.03448276),
                            "rate 4": numpy.pmt(0.25, 2, 0.2),
                            "rate 5": numpy.pmt(0.15, 2, 0.3043478),
                            "rate 6": numpy.pmt(0.065, 2, 0.4084507),
                            "rate 7": -0.25}}},
                "energy cost": {
                    "residential": {"2009": None, "2010": None},
                    "commercial": {
                        "2009": {
                            "rate 1": numpy.pmt(10.0, 2, 0.1983471),
                            "rate 2": numpy.pmt(1.0, 2, 1.5),
                            "rate 3": numpy.pmt(0.45, 2, 2.330559),
                            "rate 4": numpy.pmt(0.25, 2, 2.88),
                            "rate 5": numpy.pmt(0.15, 2, 3.251418),
                            "rate 6": numpy.pmt(0.065, 2, 3.641253),
                            "rate 7": -2},
                        "2010": {
                            "rate 1": numpy.pmt(10.0, 2, 0.1487603),
                            "rate 2": numpy.pmt(1.0, 2, 1.125),
                            "rate 3": numpy.pmt(0.45, 2, 1.747919),
                            "rate 4": numpy.pmt(0.25, 2, 2.16),
                            "rate 5": numpy.pmt(0.15, 2, 2.438563),
                            "rate 6": numpy.pmt(0.065, 2, 2.73094),
                            "rate 7": -1.5}}},
                "carbon cost": {
                    "residential": {"2009": None, "2010": None},
                    "commercial": {
                        "2009": {
                            "rate 1": numpy.pmt(10.0, 2, 0.09917355),
                            "rate 2": numpy.pmt(1.0, 2, 0.75),
                            "rate 3": numpy.pmt(0.45, 2, 1.165279),
                            "rate 4": numpy.pmt(0.25, 2, 1.44),
                            "rate 5": numpy.pmt(0.15, 2, 1.625709),
                            "rate 6": numpy.pmt(0.065, 2, 1.820626),
                            "rate 7": -1},
                        "2010": {
                            "rate 1": numpy.pmt(10.0, 2, 0.1487603),
                            "rate 2": numpy.pmt(1.0, 2, 1.125),
                            "rate 3": numpy.pmt(0.45, 2, 1.747919),
                            "rate 4": numpy.pmt(0.25, 2, 2.16),
                            "rate 5": numpy.pmt(0.15, 2, 2.438563),
                            "rate 6": numpy.pmt(0.065, 2, 2.73094),
                            "rate 7": -1.5}}}},
                "irr (w/ energy costs)": {
                    "2009": 3.45, "2010": 2.44},
                "irr (w/ energy and carbon costs)": {
                    "2009": 4.54, "2010": 4.09},
                "payback (w/ energy costs)": {
                    "2009": 0.25, "2010": 0.33},
                "payback (w/ energy and carbon costs)": {
                    "2009": 0.2, "2010": 0.22}}]
        cls.ok_out_dist1 = [{
            "savings and portfolio metrics": {
                "Technical potential": {
                    "uncompeted": True, "competed": True},
                "Max adoption potential": {
                    "uncompeted": False, "competed": True}},
            "consumer metrics": False},
            {
            "stock": {
                "cost savings (total)": {"2009": -5, "2010": -10},
                "cost savings (annual)": {"2009": -5, "2010": -10}},
            "energy": {
                "savings (total)": {
                    "2009": numpy.array([184, 173, 169, 194, 149]),
                    "2010": numpy.array([194, 205, 219, 289, 176])},
                "savings (annual)": {
                    "2009": numpy.array([94, 93, 99, 84, 99]),
                    "2010": numpy.array([114, 105, 89, 145, 96])},
                "cost savings (total)": {
                    "2009": numpy.array([10.9, 11.3, 12.3, 8.8, 7.5]),
                    "2010": numpy.array([14.9, 16.3, 13.3, 13.8, 12.5])},
                "cost savings (annual)": {
                    "2009": numpy.array([10.9, 11.3, 12.3, 8.8, 7.5]),
                    "2010": numpy.array([14.9, 16.3, 13.3, 13.8, 12.5])}},
            "carbon": {
                "savings (total)": {
                    "2009": numpy.array([149.4, 142.3, 141.9, 150.0, 148.9]),
                    "2010": numpy.array([199.4, 191.3, 194.9, 195.0, 193.9])},
                "savings (annual)": {
                    "2009": numpy.array([49.4, 42.3, 41.9, 50.0, 48.9]),
                    "2010": numpy.array([49.4, 41.3, 44.9, 45.0, 43.9])},
                "cost savings (total)": {
                    "2009": numpy.array([4.9, 5.3, 6.3, -1.2, 11.5]),
                    "2010": numpy.array([19.9, 21.3, 18.3, 18.8, 17.5])},
                "cost savings (annual)": {
                    "2009": numpy.array([4.9, 5.3, 6.3, -1.2, 11.5]),
                    "2010": numpy.array([19.9, 21.3, 18.3, 18.8, 17.5])}}},
            {
            "cce": {
                "2009": numpy.array([
                    -0.02557046, -0.02584541, -0.02427902,
                    -0.02861456, -0.02427902]),
                "2010": numpy.array([
                    -0.01949742, -0.02116862, -0.02497422,
                    -0.01532900, -0.02315318])},
            "cce (w/ carbon cost benefits)": {
                "2009": numpy.array([
                    -0.07769812, -0.08283466, -0.08791539,
                    -0.01432885, -0.1404406]),
                "2010": numpy.array([
                    -0.19405882, -0.22402576, -0.23059219,
                    -0.14498417, -0.2054448])},
            "ccc": {
                "2009": numpy.array([
                    -4.87e-08, -5.68e-08, -5.74e-08, -4.81e-08, -4.92e-08]),
                "2010": numpy.array([
                    -4.50e-08, -5.38e-08, -4.95e-08, -4.94e-08, -5.06e-08])},
            "ccc (w/ energy cost benefits)": {
                "2009": numpy.array([
                    -2.69e-07, -3.24e-07, -3.51e-07, -2.24e-07, -2.03e-07]),
                "2010": numpy.array([
                    -3.47e-07, -4.48e-07, -3.46e-07, -3.56e-07, -3.35e-07])}},
            {
            "anpv": {
                "stock cost": {
                    "residential": {
                        "2009": numpy.array([
                            numpy.pmt(0.07, 2, 0.8691589),
                            numpy.pmt(0.07, 2, 0.8691589),
                            numpy.pmt(0.07, 2, 0.8691589),
                            numpy.pmt(0.07, 2, 0.8691589),
                            numpy.pmt(0.07, 2, 0.8691589)]),
                        "2010": numpy.array([
                            numpy.pmt(0.07, 2, 0.4018692),
                            numpy.pmt(0.07, 2, 0.4018692),
                            numpy.pmt(0.07, 2, 0.4018692),
                            numpy.pmt(0.07, 2, 0.4018692),
                            numpy.pmt(0.07, 2, 0.4018692)])
                    },
                    "commercial": {
                        "2009": numpy.repeat(numpy.nan, 5),
                        "2010": numpy.repeat(numpy.nan, 5)
                    }},
                "energy cost": {
                    "residential": {
                        "2009": numpy.array([
                            numpy.pmt(0.07, 2, 3.94148),
                            numpy.pmt(0.07, 2, 4.086121),
                            numpy.pmt(0.07, 2, 4.447725),
                            numpy.pmt(0.07, 2, 3.182112),
                            numpy.pmt(0.07, 2, 2.712027)]),
                        "2010": numpy.array([
                            numpy.pmt(0.07, 2, 2.693947),
                            numpy.pmt(0.07, 2, 2.94707),
                            numpy.pmt(0.07, 2, 2.404664),
                            numpy.pmt(0.07, 2, 2.495065),
                            numpy.pmt(0.07, 2, 2.260023)])
                    },
                    "commercial": {
                        "2009": numpy.repeat(numpy.nan, 5),
                        "2010": numpy.repeat(numpy.nan, 5)
                    }},
                "carbon cost": {
                    "residential": {
                        "2009": numpy.array([
                            numpy.pmt(0.07, 2, 1.7718578),
                            numpy.pmt(0.07, 2, 1.9164993),
                            numpy.pmt(0.07, 2, 2.2781029),
                            numpy.pmt(0.07, 2, -0.4339244),
                            numpy.pmt(0.07, 2, 4.1584418)]),
                        "2010": numpy.array([
                            numpy.pmt(0.07, 2, 3.597956),
                            numpy.pmt(0.07, 2, 3.851079),
                            numpy.pmt(0.07, 2, 3.308673),
                            numpy.pmt(0.07, 2, 3.399074),
                            numpy.pmt(0.07, 2, 3.164032)])
                    },
                    "commercial": {
                        "2009": numpy.repeat(numpy.nan, 5),
                        "2010": numpy.repeat(numpy.nan, 5)
                    }}},
                "irr (w/ energy costs)": {
                    "2009": numpy.array([3.65, 3.74, 3.96, 3.18, 2.89]),
                    "2010": numpy.array([2.42, 2.58, 2.24, 2.30, 2.15])},
                "irr (w/ energy and carbon costs)": {
                    "2009": numpy.array([4.71, 4.88, 5.31, 2.91, 5.39]),
                    "2010": numpy.array([4.60, 4.90, 4.26, 4.37, 4.09])},
                "payback (w/ energy costs)": {
                    "2009": numpy.array([0.24, 0.23, 0.22, 0.27, 0.29]),
                    "2010": numpy.array([0.33, 0.32, 0.35, 0.35, 0.36])},
                "payback (w/ energy and carbon costs)": {
                    "2009": numpy.array([0.19, 0.19, 0.17, 0.28, 0.17]),
                    "2010": numpy.array([0.20, 0.19, 0.21, 0.21, 0.22])}}]
        cls.ok_out_dist2 = [{
            "savings and portfolio metrics": {
                "Technical potential": {
                    "uncompeted": True, "competed": True},
                "Max adoption potential": {
                    "uncompeted": False, "competed": True}},
            "consumer metrics": False},
            {
            "stock": {
                "cost savings (total)": {
                    "2009": numpy.array([-5.1, -2.7, -4.1, -4.2, -5.5]),
                    "2010": numpy.array([-5.1, -3.7, -6.7, -4.2, -5.5])},
                "cost savings (annual)": {
                    "2009": numpy.array([-5.1, -2.7, -4.1, -4.2, -5.5]),
                    "2010": numpy.array([-5.1, -3.7, -6.7, -4.2, -5.5])}},
            "energy": {
                "savings (total)": {"2009": 150, "2010": 200},
                "savings (annual)": {"2009": 100, "2010": 100},
                "cost savings (total)": {"2009": 10, "2010": 15},
                "cost savings (annual)": {"2009": 10, "2010": 15}},
            "carbon": {
                "savings (total)": {"2009": 150, "2010": 200},
                "savings (annual)": {"2009": 50, "2010": 50},
                "cost savings (total)": {"2009": 5, "2010": 15},
                "cost savings (annual)": {"2009": 5, "2010": 15}}},
            {
            "cce": {
                "2009": numpy.array([
                    -0.02348314, -0.03675734, -0.02901406,
                    -0.02846097, -0.02127077]),
                "2010": numpy.array([
                    -0.04932855, -0.05707184, -0.04047908,
                    -0.05430638, -0.04711618])},
            "cce (w/ carbon cost benefits)": {
                "2009": numpy.array([
                    -0.07348314, -0.08675734, -0.07901406,
                    -0.07846097, -0.07127077]),
                "2010": numpy.array([
                    -0.19932855, -0.20707184, -0.19047908,
                    -0.20430638, -0.19711618])},
            "ccc": {
                "2009": numpy.array([
                    -4.70e-08, -7.35e-08, -5.8e-08, -5.69e-08, -4.25e-08]),
                "2010": numpy.array([
                    -9.87e-08, -1.14e-07, -8.1e-08, -1.09e-07, -9.42e-08])},
            "ccc (w/ energy cost benefits)": {
                "2009": numpy.array([
                    -2.47e-07, -2.74e-07, -2.58e-07, -2.57e-07, -2.43e-07]),
                "2010": numpy.array([
                    -3.99e-07, -4.14e-07, -3.81e-07, -4.09e-07, -3.94e-07])}},
            {
            "anpv": {
                "stock cost": {
                    "residential": {
                        "2009": numpy.array([
                            numpy.pmt(0.07, 2, 0.8491589),
                            numpy.pmt(0.07, 2, 1.329159),
                            numpy.pmt(0.07, 2, 1.049159),
                            numpy.pmt(0.07, 2, 1.029159),
                            numpy.pmt(0.07, 2, 0.7691589)]),
                        "2010": numpy.array([
                            numpy.pmt(0.07, 2, 0.8918692),
                            numpy.pmt(0.07, 2, 1.031869),
                            numpy.pmt(0.07, 2, 0.7318692),
                            numpy.pmt(0.07, 2, 0.9818692),
                            numpy.pmt(0.07, 2, 0.8518692)])},
                    "commercial": {
                        "2009": numpy.repeat(numpy.nan, 5),
                        "2010": numpy.repeat(numpy.nan, 5)}},

                "energy cost": {
                    "residential": {
                        "2009": numpy.array([
                            numpy.pmt(0.07, 2, 3.616036),
                            numpy.pmt(0.07, 2, 3.616036),
                            numpy.pmt(0.07, 2, 3.616036),
                            numpy.pmt(0.07, 2, 3.616036),
                            numpy.pmt(0.07, 2, 3.616036)]),
                        "2010": numpy.array([
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 2, 2.712027)])},
                    "commercial": {
                        "2009": numpy.repeat(numpy.nan, 5),
                        "2010": numpy.repeat(numpy.nan, 5)}},
                "carbon cost": {
                    "residential": {
                        "2009": numpy.array([
                            numpy.pmt(0.07, 2, 1.808018),
                            numpy.pmt(0.07, 2, 1.808018),
                            numpy.pmt(0.07, 2, 1.808018),
                            numpy.pmt(0.07, 2, 1.808018),
                            numpy.pmt(0.07, 2, 1.808018)]),
                        "2010": numpy.array([
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 2, 2.712027)])},
                    "commercial": {
                        "2009": numpy.repeat(numpy.nan, 5),
                        "2010": numpy.repeat(numpy.nan, 5)}}},
            "irr (w/ energy costs)":
                {"2009": numpy.array([3.37, 6.88, 4.34, 4.22, 3.08]),
                 "2010": numpy.array([5.35, 7.58, 3.93, 6.61, 4.92])},
            "irr (w/ energy and carbon costs)":
                {"2009": numpy.array([4.44, 8.82, 5.65, 5.50, 4.08]),
                 "2010": numpy.array([8.45, 11.80, 6.33, 10.34, 7.80])},
            "payback (w/ energy costs)":
                {"2009": numpy.array([0.26, 0.14, 0.21, 0.21, 0.28]),
                 "2010": numpy.array([0.17, 0.12, 0.22, 0.14, 0.18])},
            "payback (w/ energy and carbon costs)":
                {"2009": numpy.array([0.20, 0.11, 0.16, 0.17, 0.22]),
                 "2010": numpy.array([0.11, 0.08, 0.15, 0.09, 0.12])}}]
        cls.ok_out_dist3 = [{
            "savings and portfolio metrics": {
                "Technical potential": {
                    "uncompeted": True, "competed": True},
                "Max adoption potential": {
                    "uncompeted": False, "competed": True}},
            "consumer metrics": False},
            {
            "stock": {
                "cost savings (total)": {"2009": -5, "2010": -10},
                "cost savings (annual)": {"2009": -5, "2010": -10}},
            "energy": {
                "savings (total)": {"2009": 150, "2010": 200},
                "savings (annual)": {"2009": 100, "2010": 100},
                "cost savings (total)": {"2009": 10, "2010": 15},
                "cost savings (annual)": {"2009": 10, "2010": 15}},
            "carbon": {
                "savings (total)": {"2009": 150, "2010": 200},
                "savings (annual)": {"2009": 50, "2010": 50},
                "cost savings (total)": {"2009": 5, "2010": 15},
                "cost savings (annual)": {"2009": 5, "2010": 15}}},
            {
            "cce": {
                "2009": numpy.array([
                    0.0535, 0.0535, -0.02403623,
                    -0.02403623, -0.07041640]),
                "2010": numpy.array([
                    0.1070, 0.1070, -0.02222705,
                    -0.02222705, -0.09952733])},
            "cce (w/ carbon cost benefits)": {
                "2009": numpy.array([
                    0.0035, 0.0035, -0.07403623,
                    -0.07403623, -0.1204164]),
                "2010": numpy.array([
                    -0.0430, -0.0430, -0.17222705,
                    -0.17222705, -0.2495273])},
            "ccc": {
                "2009": numpy.array([
                    1.07e-07, 1.07e-07, -4.81e-08, -4.81e-08, -1.41e-07]),
                "2010": numpy.array([
                    2.14e-07, 2.14e-07, -4.45e-08, -4.45e-08, -1.99e-07])},
            "ccc (w/ energy cost benefits)": {
                "2009": numpy.array([
                    -9.3e-08, -9.3e-08, -2.48e-07, -2.48e-07, -3.41e-07]),
                "2010": numpy.array([
                    -8.6e-08, -8.6e-08, -3.44e-07, -3.44e-07, -4.99e-07])}},
            {
            "anpv": {
                "stock cost": {
                    "residential": {
                        "2009": numpy.array([
                            numpy.pmt(0.07, 1, -1),
                            numpy.pmt(0.07, 1, -1),
                            numpy.pmt(0.07, 2, 0.8691589),
                            numpy.pmt(0.07, 2, 0.8691589),
                            numpy.pmt(0.07, 5, 5.7744225)]),
                        "2010": numpy.array([
                            numpy.pmt(0.07, 1, -1),
                            numpy.pmt(0.07, 1, -1),
                            numpy.pmt(0.07, 2, 0.4018692),
                            numpy.pmt(0.07, 2, 0.4018692),
                            numpy.pmt(0.07, 5, 4.080817)])},
                    "commercial": {
                        "2009": numpy.repeat(numpy.nan, 5),
                        "2010": numpy.repeat(numpy.nan, 5)}},
                "energy cost": {
                    "residential": {
                        "2009": numpy.array([
                            numpy.pmt(0.07, 1, 1.869159),
                            numpy.pmt(0.07, 1, 1.869159),
                            numpy.pmt(0.07, 2, 3.616036),
                            numpy.pmt(0.07, 2, 3.616036),
                            numpy.pmt(0.07, 5, 8.200395)]),
                        "2010": numpy.array([
                            numpy.pmt(0.07, 1, 1.401869),
                            numpy.pmt(0.07, 1, 1.401869),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 5, 6.150296)])},
                    "commercial": {
                        "2009": numpy.repeat(numpy.nan, 5),
                        "2010": numpy.repeat(numpy.nan, 5)}},
                "carbon cost": {
                    "residential": {
                        "2009": numpy.array([
                            numpy.pmt(0.07, 1, 0.9345794),
                            numpy.pmt(0.07, 1, 0.9345794),
                            numpy.pmt(0.07, 2, 1.808018),
                            numpy.pmt(0.07, 2, 1.808018),
                            numpy.pmt(0.07, 5, 4.1001974)]),
                        "2010": numpy.array([
                            numpy.pmt(0.07, 1, 1.401869),
                            numpy.pmt(0.07, 1, 1.401869),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 5, 6.150296)])},
                    "commercial": {
                        "2009": numpy.repeat(numpy.nan, 5),
                        "2010": numpy.repeat(numpy.nan, 5)}}},
            "irr (w/ energy costs)":
                {"2009": numpy.array([1.00, 1.00, 3.45, 3.45, 4.00]),
                 "2010": numpy.array([0.50, 0.50, 2.44, 2.44, 2.99])},
            "irr (w/ energy and carbon costs)":
                {"2009": numpy.array([2.00, 2.00, 4.54, 4.54, 5.00]),
                 "2010": numpy.array([2.00, 2.00, 4.09, 4.09, 4.50])},
            "payback (w/ energy costs)":
                {"2009": numpy.array([0.50, 0.50, 0.25, 0.25, 0.25]),
                 "2010": numpy.array([0.67, 0.67, 0.33, 0.33, 0.33])},
            "payback (w/ energy and carbon costs)":
                {"2009": numpy.array([0.33, 0.33, 0.20, 0.20, 0.20]),
                 "2010": numpy.array([0.33, 0.33, 0.22, 0.22, 0.22])}}]
        cls.ok_out_dist4 = [{
            "savings and portfolio metrics": {
                "Technical potential": {
                    "uncompeted": True, "competed": True},
                "Max adoption potential": {
                    "uncompeted": False, "competed": True}},
            "consumer metrics": False},
            {
            "stock": {
                "cost savings (total)": {
                    "2009": numpy.array([-5.1, -2.7, -4.1, -4.2, -5.5]),
                    "2010": numpy.array([-5.1, -3.7, -6.7, -4.2, -5.5])},
                "cost savings (annual)": {
                    "2009": numpy.array([-5.1, -2.7, -4.1, -4.2, -5.5]),
                    "2010": numpy.array([-5.1, -3.7, -6.7, -4.2, -5.5])}},
            "energy": {
                "savings (total)": {"2009": 150, "2010": 200},
                "savings (annual)": {"2009": 100, "2010": 100},
                "cost savings (total)": {"2009": 10, "2010": 15},
                "cost savings (annual)": {"2009": 10, "2010": 15}},
            "carbon": {
                "savings (total)": {"2009": 150, "2010": 200},
                "savings (annual)": {"2009": 50, "2010": 50},
                "cost savings (total)": {"2009": 5, "2010": 15},
                "cost savings (annual)": {"2009": 5, "2010": 15}}},
            {
            "cce": {
                "2009": numpy.array([
                    0.05457, 0.02889, -0.02901406,
                    -0.02846097, -0.06919694]),
                "2010": numpy.array([
                    0.05457, 0.03959, -0.04047908,
                    -0.05430638, -0.11050241])},
            "cce (w/ carbon cost benefits)": {
                "2009": numpy.array([
                    0.00457, -0.02111, -0.07901406,
                    -0.07846097, -0.1191969]),
                "2010": numpy.array([
                    -0.09543, -0.11041, -0.19047908,
                    -0.20430638, -0.2605024])},
            "ccc": {
                "2009": numpy.array([
                    1.09e-07, 5.78e-08, -5.8e-08, -5.69e-08, -1.38e-07]),
                "2010": numpy.array([
                    1.09e-07, 7.92e-08, -8.1e-08, -1.09e-07, -2.21e-07])},
            "ccc (w/ energy cost benefits)": {
                "2009": numpy.array([
                    -9.09e-08, -1.42e-07, -2.58e-07, -2.57e-07, -3.38e-07]),
                "2010": numpy.array([
                    -1.91e-07, -2.21e-07, -3.81e-07, -4.09e-07, -5.21e-07])}},
            {
            "anpv": {
                "stock cost": {
                    "residential": {
                        "2009": numpy.array([
                            numpy.pmt(0.07, 1, -1.02),
                            numpy.pmt(0.07, 1, -0.54),
                            numpy.pmt(0.07, 2, 1.049159),
                            numpy.pmt(0.07, 2, 1.029159),
                            numpy.pmt(0.07, 5, 5.674423)]),
                        "2010": numpy.array([
                            numpy.pmt(0.07, 1, -0.51),
                            numpy.pmt(0.07, 1, -0.37),
                            numpy.pmt(0.07, 2, 0.7318692),
                            numpy.pmt(0.07, 2, 0.9818692),
                            numpy.pmt(0.07, 5, 4.530817)])},
                    "commercial": {
                        "2009": numpy.repeat(numpy.nan, 5),
                        "2010": numpy.repeat(numpy.nan, 5)}},
                "energy cost": {
                    "residential": {
                        "2009": numpy.array([
                            numpy.pmt(0.07, 1, 1.869159),
                            numpy.pmt(0.07, 1, 1.869159),
                            numpy.pmt(0.07, 2, 3.616036),
                            numpy.pmt(0.07, 2, 3.616036),
                            numpy.pmt(0.07, 5, 8.200395)]),
                        "2010": numpy.array([
                            numpy.pmt(0.07, 1, 1.401869),
                            numpy.pmt(0.07, 1, 1.401869),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 5, 6.150296)])},
                    "commercial": {
                        "2009": numpy.repeat(numpy.nan, 5),
                        "2010": numpy.repeat(numpy.nan, 5)}},
                "carbon cost": {
                    "residential": {
                        "2009": numpy.array([
                            numpy.pmt(0.07, 1, 0.9345794),
                            numpy.pmt(0.07, 1, 0.9345794),
                            numpy.pmt(0.07, 2, 1.808018),
                            numpy.pmt(0.07, 2, 1.808018),
                            numpy.pmt(0.07, 5, 4.1001974)]),
                        "2010": numpy.array([
                            numpy.pmt(0.07, 1, 1.401869),
                            numpy.pmt(0.07, 1, 1.401869),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 2, 2.712027),
                            numpy.pmt(0.07, 5, 6.150296)])},
                    "commercial": {
                        "2009": numpy.repeat(numpy.nan, 5),
                        "2010": numpy.repeat(numpy.nan, 5)}}},
            "irr (w/ energy costs)":
                {"2009": numpy.array([0.96, 2.70, 4.34, 4.22, 3.63]),
                 "2010": numpy.array([1.94, 3.05, 3.93, 6.61, 5.45])},
            "irr (w/ energy and carbon costs)":
                {"2009": numpy.array([1.94, 4.56, 5.65, 5.50, 4.54]),
                 "2010": numpy.array([4.88, 7.11, 6.33, 10.34, 8.18])},
            "payback (w/ energy costs)":
                {"2009": numpy.array([0.51, 0.27, 0.21, 0.21, 0.28]),
                 "2010": numpy.array([0.34, 0.25, 0.22, 0.14, 0.18])},
            "payback (w/ energy and carbon costs)":
                {"2009": numpy.array([0.34, 0.18, 0.16, 0.17, 0.22]),
                 "2010": numpy.array([0.17, 0.12, 0.15, 0.09, 0.12])}}]
        cls.ok_savings_mkts_comp_schemes = ["competed", "uncompeted"]

    def test_metrics_ok_point_res(self):
        """Test output given residential measure with point value inputs."""
        # Initialize test measure and assign it a sample 'uncompeted'
        # market ('ok_master_mseg_point'), the focus of this test suite
        test_meas = run.Measure(self.handyvars, **self.sample_measure_res)
        test_meas.markets[self.test_adopt_scheme]["uncompeted"][
            "master_mseg"] = self.ok_master_mseg_point
        # Create Engine instance using test measure, run function on it
        engine_instance = run.Engine(self.handyvars, [test_meas])
        engine_instance.calc_savings_metrics(
            self.test_adopt_scheme, "uncompeted")
        # For first test case, verify correct adoption/competition scenario
        # keys for measure markets/savings/portfolio metrics
        for adopt_scheme in self.handyvars.adopt_schemes:
            # Markets
            self.assertEqual(list(sorted(
                engine_instance.measures[0].markets[adopt_scheme].keys())),
                self.ok_savings_mkts_comp_schemes)
            # Savings
            self.assertEqual(list(sorted(
                engine_instance.measures[0].savings[adopt_scheme].keys())),
                self.ok_savings_mkts_comp_schemes)
            # Portfolio metrics
            self.assertEqual(list(sorted(engine_instance.measures[
                0].portfolio_metrics[adopt_scheme].keys())),
                self.ok_savings_mkts_comp_schemes)
        # Verify test measure results update status
        self.dict_check(engine_instance.measures[
            0].update_results, self.ok_out_point_res[0])
        # Verify test measure savings
        self.dict_check(engine_instance.measures[0].savings[
            self.test_adopt_scheme]["uncompeted"], self.ok_out_point_res[1])
        # Verify test measure portfolio-level financial metrics
        self.dict_check(engine_instance.measures[0].portfolio_metrics[
            self.test_adopt_scheme]["uncompeted"], self.ok_out_point_res[2])
        # Verify test measure consumer-level metrics
        self.dict_check(engine_instance.measures[
            0].consumer_metrics, self.ok_out_point_res[3])

    def test_metrics_ok_point_com(self):
        """Test output given commercial measure with point value inputs."""
        # Initialize test measure and assign it a sample 'uncompeted'
        # market ('ok_master_mseg_point'), the focus of this test suite
        test_meas = run.Measure(self.handyvars, **self.sample_measure_com)
        test_meas.markets[self.test_adopt_scheme]["uncompeted"][
            "master_mseg"] = self.ok_master_mseg_point
        # Create Engine instance using test measure, run function on it
        engine_instance = run.Engine(self.handyvars, [test_meas])
        engine_instance.calc_savings_metrics(
            self.test_adopt_scheme, "uncompeted")
        # Verify test measure results update status
        self.dict_check(engine_instance.measures[
            0].update_results, self.ok_out_point_com[0])
        # Verify test measure savings
        self.dict_check(engine_instance.measures[0].savings[
            self.test_adopt_scheme]["uncompeted"], self.ok_out_point_com[1])
        # Verify test measure portfolio-level financial metrics
        self.dict_check(engine_instance.measures[0].portfolio_metrics[
            self.test_adopt_scheme]["uncompeted"], self.ok_out_point_com[2])
        # Verify test measure consumer-level metrics
        self.dict_check(engine_instance.measures[
            0].consumer_metrics, self.ok_out_point_com[3])

    def test_metrics_ok_distrib1(self):
        """Test output given residential measure with array inputs."""
        # Initialize test measure and assign it a sample 'uncompeted'
        # market ('ok_master_mseg_dist1'), the focus of this test suite
        test_meas = run.Measure(self.handyvars, **self.sample_measure_res)
        test_meas.markets[self.test_adopt_scheme]["uncompeted"][
            "master_mseg"] = self.ok_master_mseg_dist1
        # Create Engine instance using test measure, run function on it
        engine_instance = run.Engine(self.handyvars, [test_meas])
        engine_instance.calc_savings_metrics(
            self.test_adopt_scheme, "uncompeted")
        # Verify test measure results update status
        self.dict_check(engine_instance.measures[
            0].update_results, self.ok_out_dist1[0])
        # Verify test measure savings
        self.dict_check(engine_instance.measures[0].savings[
            self.test_adopt_scheme]["uncompeted"], self.ok_out_dist1[1])
        # Verify test measure portfolio-level financial metrics
        self.dict_check(engine_instance.measures[0].portfolio_metrics[
            self.test_adopt_scheme]["uncompeted"], self.ok_out_dist1[2])
        # Verify test measure consumer-level metrics
        self.dict_check(engine_instance.measures[
            0].consumer_metrics, self.ok_out_dist1[3])

    def test_metrics_ok_distrib2(self):
        """Test output given residential measure with array inputs."""
        # Initialize test measure and assign it a sample 'uncompeted'
        # market ('ok_master_mseg_dist2'), the focus of this test suite
        test_meas = run.Measure(self.handyvars, **self.sample_measure_res)
        test_meas.markets[self.test_adopt_scheme]["uncompeted"][
            "master_mseg"] = self.ok_master_mseg_dist2
        # Create Engine instance using test measure, run function on it
        engine_instance = run.Engine(self.handyvars, [test_meas])
        engine_instance.calc_savings_metrics(
            self.test_adopt_scheme, "uncompeted")
        # Verify test measure results update status
        self.dict_check(engine_instance.measures[
            0].update_results, self.ok_out_dist2[0])
        # Verify test measure savings
        self.dict_check(engine_instance.measures[0].savings[
            self.test_adopt_scheme]["uncompeted"], self.ok_out_dist2[1])
        # Verify test measure portfolio-level financial metrics
        self.dict_check(engine_instance.measures[0].portfolio_metrics[
            self.test_adopt_scheme]["uncompeted"], self.ok_out_dist2[2])
        # Verify test measure consumer-level metrics
        self.dict_check(engine_instance.measures[
            0].consumer_metrics, self.ok_out_dist2[3])

    def test_metrics_ok_distrib3(self):
        """Test output given residential measure with array inputs."""
        # Initialize test measure and assign it a sample 'uncompeted'
        # market ('ok_master_mseg_dist3'), the focus of this test suite
        test_meas = run.Measure(self.handyvars, **self.sample_measure_res)
        test_meas.markets[self.test_adopt_scheme]["uncompeted"][
            "master_mseg"] = self.ok_master_mseg_dist3
        # Create Engine instance using test measure, run function on it
        engine_instance = run.Engine(self.handyvars, [test_meas])
        engine_instance.calc_savings_metrics(
            self.test_adopt_scheme, "uncompeted")
        # Verify test measure results update status
        self.dict_check(engine_instance.measures[
            0].update_results, self.ok_out_dist3[0])
        # Verify test measure savings
        self.dict_check(engine_instance.measures[0].savings[
            self.test_adopt_scheme]["uncompeted"], self.ok_out_dist3[1])
        # Verify test measure portfolio-level financial metrics
        self.dict_check(engine_instance.measures[0].portfolio_metrics[
            self.test_adopt_scheme]["uncompeted"], self.ok_out_dist3[2])
        # Verify test measure consumer-level metrics
        self.dict_check(engine_instance.measures[
            0].consumer_metrics, self.ok_out_dist3[3])

    def test_metrics_ok_distrib4(self):
        """Test output given residential measure with array inputs."""
        # Initialize test measure and assign it a sample 'uncompeted'
        # market ('ok_master_mseg_dist4'), the focus of this test suite
        test_meas = run.Measure(self.handyvars, **self.sample_measure_res)
        test_meas.markets[self.test_adopt_scheme]["uncompeted"][
            "master_mseg"] = self.ok_master_mseg_dist4
        # Create Engine instance using test measure, run function on it
        engine_instance = run.Engine(self.handyvars, [test_meas])
        engine_instance.calc_savings_metrics(
            self.test_adopt_scheme, "uncompeted")
        # Verify test measure results update status
        self.dict_check(engine_instance.measures[
            0].update_results, self.ok_out_dist4[0])
        # Verify test measure savings
        self.dict_check(engine_instance.measures[0].savings[
            self.test_adopt_scheme]["uncompeted"], self.ok_out_dist4[1])
        # Verify test measure portfolio-level financial metrics
        self.dict_check(engine_instance.measures[0].portfolio_metrics[
            self.test_adopt_scheme]["uncompeted"], self.ok_out_dist4[2])
        # Verify test measure consumer-level metrics
        self.dict_check(engine_instance.measures[
            0].consumer_metrics, self.ok_out_dist4[3])


class MetricUpdateTest(unittest.TestCase, CommonMethods):
    """Test the operation of the 'metrics_update' function.

    Verify that cashflow inputs generate expected prioritization metric
    outputs.

    Attributes:
        handyvars (object): Useful variables across the class.
        measure_list (list): List for Engine including one sample
            residential measure.
        ok_num_units (int): Sample number of competed units.
        ok_base_life (int): Sample baseline technology lifetime.
        ok_product_lifetime (float): Sample measure lifetime.
        ok_life_ratio (int): Sample measure->baseline lifetime ratio.
        ok_base_scost (int): Sample baseline stock cost.
        ok_scostsave (int): Sample baseline->measure stock cost delta.
        ok_esave (int): Sample measure energy savings.
        ok_ecostsave (int): Sample measure energy cost savings.
        ok_csave (int): Sample measure avoided carbon emissions.
        ok_ccostsave (int): Sample measure avoided carbon costs.
        ok_out_dicts (list): Output annuity equivalent Net Present Value
            dicts that should be generated given valid sample inputs.
        ok_out_array (list): Other financial metric values that should
            be generated given valid sample inputs.
    """

    @classmethod
    def setUpClass(cls):
        """Define objects/variables for use across all class functions."""
        cls.handyvars = run.UsefulVars()
        sample_measure = CommonTestMeasures().sample_measure
        cls.measure_list = [run.Measure(cls.handyvars, **sample_measure)]
        cls.ok_base_life = 3
        cls.ok_product_lifetime = 6.2
        cls.ok_life_ratio = 2
        cls.ok_base_scost = 1
        cls.ok_meas_sdelt = -1
        cls.ok_esave = 7.5
        cls.ok_ecostsave = 0.5
        cls.ok_csave = 50
        cls.ok_ccostsave = 1
        cls.ok_out_array = [
            numpy.pmt(0.07, 6, -0.1837021),
            numpy.pmt(0.07, 6, 2.38327), numpy.pmt(0.07, 6, 4.76654),
            None, None, None, 0.62, 1.59, 2, 0.67, 0.005,
            -0.13, 7.7e-10, -9.2e-9]

    def test_metric_updates(self):
        """Test for correct outputs given valid inputs."""
        # Create an Engine instance using sample_measure list
        engine_instance = run.Engine(self.handyvars, self.measure_list)
        # Record the output for the test run of the 'metric_update'
        # function
        function_output = engine_instance.metric_update(
            self.measure_list[0], self.ok_base_life,
            int(self.ok_product_lifetime), self.ok_base_scost,
            self.ok_meas_sdelt, self.ok_esave, self.ok_ecostsave,
            self.ok_csave, self.ok_ccostsave)
        # Test that valid inputs yield correct anpv, irr, payback, and
        # cost of conserved energy/carbon outputs
        for ind, x in enumerate(self.ok_out_array):
            if x is not None:
                self.assertAlmostEqual(function_output[ind], x, places=2)
            else:
                self.assertEqual(function_output[ind], x)


class PaybackTest(unittest.TestCase):
    """Test the operation of the 'payback' function.

    Verify cashflow input generates expected payback output.

    Attributes:
        handyvars (object): Useful variables across the class.
        measure_list (list): List for Engine including one sample
            residential measure.
        ok_cashflows (list): Set of sample input cash flows.
        ok_out (list): Outputs that should be generated for each
            set of sample cash flows.
    """

    @classmethod
    def setUpClass(cls):
        """Define objects/variables for use across all class functions."""
        cls.handyvars = run.UsefulVars()
        sample_measure = CommonTestMeasures().sample_measure
        cls.measure_list = [run.Measure(cls.handyvars, **sample_measure)]
        cls.ok_cashflows = [[-10, 1, 1, 1, 1, 5, 7, 8], [-10, 14, 2, 3, 4],
                            [-10, 0, 1, 2], [10, 4, 7, 8, 10]]
        cls.ok_out = [5.14, 0.71, 999, 0]

    def test_cashflow_paybacks(self):
        """Test for correct outputs given valid inputs."""
        # Create an Engine instance using sample_measure list
        engine_instance = run.Engine(self.handyvars, self.measure_list)
        # Test that valid input cashflows yield correct output payback values
        for idx, cf in enumerate(self.ok_cashflows):
            self.assertAlmostEqual(engine_instance.payback(cf),
                                   self.ok_out[idx], places=2)


class ResCompeteTest(unittest.TestCase, CommonMethods):
    """Test 'compete_res_primary,' and 'htcl_adj'.

    Verify that 'compete_res_primary' correctly calculates primary market
    shares and updates master microsegments for a series of competing
    residential measures; and that 'htcl_adj' properly accounts for
    heating and cooling supply-demand overlaps.

    Attributes:
        handyvars (object): Useful variables across the class.
        test_adopt_scheme (string): Sample consumer adoption scheme.
        adjust_key1 (string): First sample string for competed demand-side and
            supply-side market microsegment key chain being tested.
        adjust_key2 (string): Second sample string for competed demand-side and
            supply-side market microsegment key chain being tested.
        compete_meas1 (dict): Sample residential demand-side cooling measure 1.
        compete_meas1_dist (dict): Alternative version of sample residential
            demand-side cooling measure 1 including lists of energy/carbon and
            associated cost input values instead of point values.
        compete_meas2 (dict): Sample residential demand-side cooling measure 2.
        compete_meas3 (dict): Sample residential supply-side cooling measure 1.
        compete_meas3_dist (dict): Alternative version of sample residential
            supply-side cooling measure 1 including lists of stock cost input
            values instead of point values.
        compete_meas4 (dict): Sample residential supply-side cooling measure 2.
        compete_meas5 (dict): Sample residential supply-side cooling measure 3.
        measures_all (list): List of all competing/interacting sample Measure
            objects with point value inputs.
        measures_demand (list): Demand-side subset of 'measures_all'.
        measures_supply (list): Supply-side subset of 'measures_all'.
        measures_overlap1 (dict): List of supply-side Measure objects and
            associated contributing microsegment keys that overlap with
            'measures_demand' Measure objects.
        measures_overlap2 (dict): List of demand-side Measure objects and
            associated contributing microsegment keys that overlap with
            'measures_supply' Measure objects.
        a_run (object): Analysis engine object incorporating all
            'measures_all' objects.
        measures_all_dist (list): List including competing/interacting sample
            Measure objects with array inputs.
        measures_demand_dist (list): Demand-side subset of 'measures_all_dist'.
        measures_supply_dist (list): Supply-side subset of 'measures_all_dist'.
        measures_overlap1_dist (dict): List of supply-side Measure objects and
            associated contributing microsegment keys that overlap with
            'measures_demand_dist' Measure objects.
        measures_overlap2_dist (dict): List of demand-side Measure objects and
            associated contributing microsegment keys that overlap with
            'measures_supply_dist' Measure objects.
        a_run_dist (object): Engine object incorporating all
            'measures_all_dist' objects.
        measure_master_msegs_out (dict): Master market microsegments
            that should be generated for each Measure object in 'measures_all'
            following competition and supply-demand overlap adjustments.
        measure_master_msegs_out_dist (dict): Master market microsegments
            that should be generated for each Measure object in
            'measures_all_dist' following competition and supply-demand overlap
            adjustments.
    """

    @classmethod
    def setUpClass(cls):
        """Define objects/variables for use across all class functions."""
        cls.handyvars = run.UsefulVars()
        cls.handyvars.aeo_years = ["2009", "2010"]
        cls.test_adopt_scheme = "Max adoption potential"
        cls.adjust_key1 = str(
            ('primary', 'AIA_CZ1', 'single family home', 'electricity (grid)',
             'cooling', 'demand', 'windows', 'existing'))
        cls.adjust_key2 = str(
            ('primary', 'AIA_CZ1', 'single family home', 'electricity (grid)',
             'cooling', 'supply', 'ASHP', 'existing'))
        cls.compete_meas1 = {
            "name": "sample compete measure r1",
            "climate_zone": ["AIA_CZ1"],
            "bldg_type": ["single family home"],
            "end_use": {"primary": ["cooling"], "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "yrs_on_mkt": ["2009", "2010"],
            "markets": {
                "Technical potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 10, "2010": 10},
                                "measure": {"2009": 10, "2010": 10}},
                            "competed": {
                                "all": {"2009": 5, "2010": 5},
                                "measure": {"2009": 5, "2010": 5}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 20, "2010": 20},
                                "efficient": {"2009": 15, "2010": 15}},
                            "competed": {
                                "baseline": {"2009": 10, "2010": 10},
                                "efficient": {"2009": 5, "2010": 5}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 20, "2010": 20}},
                            "competed": {
                                "baseline": {"2009": 15, "2010": 15},
                                "efficient": {"2009": 5, "2010": 5}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 15, "2010": 15}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 20, "2010": 20}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 5, "2010": 5}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.adjust_key1: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                        "competed choice parameters": {
                            cls.adjust_key1: {
                                "b1": {"2009": -0.95, "2010": -0.95},
                                "b2": {"2009": -0.10, "2010": -0.10}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}
                                },
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 10, "2010": 10},
                                "measure": {"2009": 10, "2010": 10}},
                            "competed": {
                                "all": {"2009": 5, "2010": 5},
                                "measure": {"2009": 5, "2010": 5}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 20, "2010": 20},
                                "efficient": {"2009": 15, "2010": 15}},
                            "competed": {
                                "baseline": {"2009": 10, "2010": 10},
                                "efficient": {"2009": 5, "2010": 5}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 20, "2010": 20}},
                            "competed": {
                                "baseline": {"2009": 15, "2010": 15},
                                "efficient": {"2009": 5, "2010": 5}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 15, "2010": 15}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 20, "2010": 20}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 5, "2010": 5}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.adjust_key1: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {"2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                        "competed choice parameters": {
                            cls.adjust_key1: {
                                "b1": {"2009": -0.95, "2010": -0.95},
                                "b2": {"2009": -0.10, "2010": -0.10}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}
                                },
                    "mseg_out_break": {}}}}
        # cls.compete_meas1_dist = {
        #     "name": "sample compete measure r1 dist",
        #     "climate_zone": ["AIA_CZ1"],
        #     "bldg_type": ["single family home"],
        #     "end_use": {"primary": ["cooling"], "secondary": None},
        #     "market_entry_year": None,
        #     "market_exit_year": None,
        #     "yrs_on_mkt": ["2009", "2010"],
        #     "markets": {
        #         "Technical potential": {
        #             "master_mseg": {
        #                 "stock": {
        #                     "total": {
        #                         "all": {"2009": 10, "2010": 10},
        #                         "measure": {"2009": 10, "2010": 10}},
        #                     "competed": {
        #                         "all": {"2009": 5, "2010": 5},
        #                         "measure": {"2009": 5, "2010": 5}}},
        #                 "energy": {
        #                     "total": {
        #                         "baseline": {"2009": 20, "2010": 20},
        #                         "efficient": {
        #                             "2009": numpy.array([15, 16, 17]),
        #                             "2010": numpy.array([15, 16, 17])}},
        #                     "competed": {
        #                         "baseline": {"2009": 10, "2010": 10},
        #                         "efficient": {
        #                             "2009": numpy.array([5, 6, 7]),
        #                             "2010": numpy.array([5, 6, 7])}}},
        #                 "carbon": {
        #                     "total": {
        #                         "baseline": {"2009": 30, "2010": 30},
        #                         "efficient": {
        #                             "2009": numpy.array([20, 21, 22]),
        #                             "2010": numpy.array([20, 21, 22])}},
        #                     "competed": {
        #                         "baseline": {"2009": 15, "2010": 15},
        #                         "efficient": {
        #                             "2009": numpy.array([5, 6, 7]),
        #                             "2010": numpy.array([5, 6, 7])}}},
        #                 "cost": {
        #                     "stock": {
        #                         "total": {
        #                             "baseline": {"2009": 10, "2010": 10},
        #                             "efficient": {"2009": 5, "2010": 5}},
        #                         "competed": {
        #                             "baseline": {"2009": 5, "2010": 5},
        #                             "efficient": {"2009": 0, "2010": 0}}},
        #                     "energy": {
        #                         "total": {
        #                             "baseline": {"2009": 20, "2010": 20},
        #                             "efficient": {
        #                                 "2009": numpy.array([15, 16, 17]),
        #                                 "2010": numpy.array([15, 16, 17])}},
        #                         "competed": {
        #                             "baseline": {"2009": 10, "2010": 10},
        #                             "efficient": {
        #                                 "2009": numpy.array([5, 6, 7]),
        #                                 "2010": numpy.array([5, 6, 7])}}},
        #                     "carbon": {
        #                         "total": {
        #                             "baseline": {"2009": 30, "2010": 30},
        #                             "efficient": {
        #                                 "2009": numpy.array([20, 21, 22]),
        #                                 "2010": numpy.array([20, 21, 22])}},
        #                         "competed": {
        #                             "baseline": {"2009": 15, "2010": 15},
        #                             "efficient": {
        #                                 "2009": numpy.array([5, 6, 7]),
        #                                 "2010": numpy.array([5, 6, 7])}}}},
        #                 "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                              "measure": {"2009": 1, "2010": 1}}},
        #             "mseg_adjust": {
        #                 "contributing mseg keys and values": {
        #                     cls.adjust_key1: {
        #                         "stock": {
        #                             "total": {
        #                                 "all": {"2009": 10, "2010": 10},
        #                                 "measure": {"2009": 10, "2010": 10}},
        #                             "competed": {
        #                                 "all": {"2009": 5, "2010": 5},
        #                                 "measure": {"2009": 5, "2010": 5}}},
        #                         "energy": {
        #                             "total": {
        #                                 "baseline": {"2009": 20, "2010": 20},
        #                                 "efficient": {
        #                                     "2009": numpy.array([15, 16, 17]),
        #                                     "2010": numpy.array(
        #                                         [15, 16, 17])}},
        #                             "competed": {
        #                                 "baseline": {"2009": 10, "2010": 10},
        #                                 "efficient": {
        #                                     "2009": numpy.array([5, 6, 7]),
        #                                     "2010": numpy.array([5, 6, 7])}}},
        #                         "carbon": {
        #                             "total": {
        #                                 "baseline": {"2009": 30, "2010": 30},
        #                                 "efficient": {
        #                                     "2009": numpy.array([20, 21, 22]),
        #                                     "2010": numpy.array(
        #                                         [20, 21, 22])}},
        #                             "competed": {
        #                                 "baseline": {"2009": 15, "2010": 15},
        #                                 "efficient": {
        #                                     "2009": numpy.array([5, 6, 7]),
        #                                     "2010": numpy.array([5, 6, 7])}}},
        #                         "cost": {
        #                             "stock": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": 5, "2010": 5}},
        #                                 "competed": {
        #                                     "baseline": {"2009": 5, "2010": 5},
        #                                     "efficient": {
        #                                         "2009": 0, "2010": 0}}},
        #                             "energy": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 20, "2010": 20},
        #                                     "efficient": {
        #                                         "2009": numpy.array(
        #                                             [15, 16, 17]),
        #                                         "2010": numpy.array(
        #                                             [15, 16, 17])}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": numpy.array([5, 6, 7]),
        #                                         "2010": numpy.array(
        #                                             [5, 6, 7])}}},
        #                             "carbon": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 30, "2010": 30},
        #                                     "efficient": {
        #                                         "2009": numpy.array(
        #                                             [20, 21, 22]),
        #                                         "2010": numpy.array(
        #                                             [20, 21, 22])}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 15, "2010": 15},
        #                                     "efficient": {
        #                                         "2009": numpy.array([5, 6, 7]),
        #                                         "2010": numpy.array(
        #                                             [5, 6, 7])}}}},
        #                         "lifetime": {
        #                             "baseline": {"2009": 1, "2010": 1},
        #                             "measure": {"2009": 1, "2010": 1}}}},
        #                 "competed choice parameters": {
        #                     cls.adjust_key1: {
        #                         "b1": {"2009": -0.95, "2010": -0.95},
        #                         "b2": {"2009": -0.10, "2010": -0.10}}},
        #                 "secondary mseg adjustments": {
        #                     "market share": {
        #                         "original energy (total captured)": {},
        #                         "original energy (competed and captured)": {},
        #                         "adjusted energy (total captured)": {},
        #                         "adjusted energy (competed and captured)": {}}},
        #                 "supply-demand adjustment": {
        #                     "savings": {
        #                         cls.adjust_key1: {
        #                             "2009": 0, "2010": 0}},
        #                     "total": {
        #                         cls.adjust_key1: {
        #                             "2009": 100, "2010": 100}}}},
        #             "mseg_out_break": {}},
        #         "Max adoption potential": {
        #             "master_mseg": {
        #                 "stock": {
        #                     "total": {
        #                         "all": {"2009": 10, "2010": 10},
        #                         "measure": {"2009": 10, "2010": 10}},
        #                     "competed": {
        #                         "all": {"2009": 5, "2010": 5},
        #                         "measure": {"2009": 5, "2010": 5}}},
        #                 "energy": {
        #                     "total": {
        #                         "baseline": {"2009": 20, "2010": 20},
        #                         "efficient": {
        #                             "2009": numpy.array([15, 16, 17]),
        #                             "2010": numpy.array([15, 16, 17])}},
        #                     "competed": {
        #                         "baseline": {"2009": 10, "2010": 10},
        #                         "efficient": {
        #                             "2009": numpy.array([5, 6, 7]),
        #                             "2010": numpy.array([5, 6, 7])}}},
        #                 "carbon": {
        #                     "total": {
        #                         "baseline": {"2009": 30, "2010": 30},
        #                         "efficient": {
        #                             "2009": numpy.array([20, 21, 22]),
        #                             "2010": numpy.array([20, 21, 22])}},
        #                     "competed": {
        #                         "baseline": {"2009": 15, "2010": 15},
        #                         "efficient": {
        #                             "2009": numpy.array([5, 6, 7]),
        #                             "2010": numpy.array([5, 6, 7])}}},
        #                 "cost": {
        #                     "stock": {
        #                         "total": {
        #                             "baseline": {"2009": 10, "2010": 10},
        #                             "efficient": {"2009": 5, "2010": 5}},
        #                         "competed": {
        #                             "baseline": {"2009": 5, "2010": 5},
        #                             "efficient": {"2009": 0, "2010": 0}}},
        #                     "energy": {
        #                         "total": {
        #                             "baseline": {"2009": 20, "2010": 20},
        #                             "efficient": {
        #                                 "2009": numpy.array([15, 16, 17]),
        #                                 "2010": numpy.array([15, 16, 17])}},
        #                         "competed": {
        #                             "baseline": {"2009": 10, "2010": 10},
        #                             "efficient": {
        #                                 "2009": numpy.array([5, 6, 7]),
        #                                 "2010": numpy.array([5, 6, 7])}}},
        #                     "carbon": {
        #                         "total": {
        #                             "baseline": {"2009": 30, "2010": 30},
        #                             "efficient": {
        #                                 "2009": numpy.array([20, 21, 22]),
        #                                 "2010": numpy.array([20, 21, 22])}},
        #                         "competed": {
        #                             "baseline": {"2009": 15, "2010": 15},
        #                             "efficient": {
        #                                 "2009": numpy.array([5, 6, 7]),
        #                                 "2010": numpy.array([5, 6, 7])}}}},
        #                 "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                              "measure": {"2009": 1, "2010": 1}}},
        #             "mseg_adjust": {
        #                 "contributing mseg keys and values": {
        #                     cls.adjust_key1: {
        #                         "stock": {
        #                             "total": {
        #                                 "all": {"2009": 10, "2010": 10},
        #                                 "measure": {"2009": 10, "2010": 10}},
        #                             "competed": {
        #                                 "all": {"2009": 5, "2010": 5},
        #                                 "measure": {"2009": 5, "2010": 5}}},
        #                         "energy": {
        #                             "total": {
        #                                 "baseline": {"2009": 20, "2010": 20},
        #                                 "efficient": {
        #                                     "2009": numpy.array([15, 16, 17]),
        #                                     "2010": numpy.array(
        #                                         [15, 16, 17])}},
        #                             "competed": {
        #                                 "baseline": {"2009": 10, "2010": 10},
        #                                 "efficient": {
        #                                     "2009": numpy.array([5, 6, 7]),
        #                                     "2010": numpy.array([5, 6, 7])}}},
        #                         "carbon": {
        #                             "total": {
        #                                 "baseline": {"2009": 30, "2010": 30},
        #                                 "efficient": {
        #                                     "2009": numpy.array([20, 21, 22]),
        #                                     "2010": numpy.array(
        #                                         [20, 21, 22])}},
        #                             "competed": {
        #                                 "baseline": {"2009": 15, "2010": 15},
        #                                 "efficient": {
        #                                     "2009": numpy.array([5, 6, 7]),
        #                                     "2010": numpy.array([5, 6, 7])}}},
        #                         "cost": {
        #                             "stock": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": 5, "2010": 5}},
        #                                 "competed": {
        #                                     "baseline": {"2009": 5, "2010": 5},
        #                                     "efficient": {
        #                                         "2009": 0, "2010": 0}}},
        #                             "energy": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 20, "2010": 20},
        #                                     "efficient": {
        #                                         "2009": numpy.array(
        #                                             [15, 16, 17]),
        #                                         "2010": numpy.array(
        #                                             [15, 16, 17])}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": numpy.array([5, 6, 7]),
        #                                         "2010": numpy.array(
        #                                             [5, 6, 7])}}},
        #                             "carbon": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 30, "2010": 30},
        #                                     "efficient": {
        #                                         "2009": numpy.array(
        #                                             [20, 21, 22]),
        #                                         "2010": numpy.array(
        #                                             [20, 21, 22])}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 15, "2010": 15},
        #                                     "efficient": {
        #                                         "2009": numpy.array([5, 6, 7]),
        #                                         "2010": numpy.array(
        #                                             [5, 6, 7])}}}},
        #                         "lifetime": {
        #                             "baseline": {"2009": 1, "2010": 1},
        #                             "measure": {"2009": 1, "2010": 1}}}},
        #                 "competed choice parameters": {
        #                     cls.adjust_key1: {
        #                         "b1": {"2009": -0.95, "2010": -0.95},
        #                         "b2": {"2009": -0.10, "2010": -0.10}}},
        #                 "secondary mseg adjustments": {
        #                     "market share": {
        #                         "original energy (total captured)": {},
        #                         "original energy (competed and captured)": {},
        #                         "adjusted energy (total captured)": {},
        #                         "adjusted energy (competed and captured)": {}}},
        #                 "supply-demand adjustment": {
        #                     "savings": {
        #                         cls.adjust_key1: {
        #                             "2009": 0, "2010": 0}},
        #                     "total": {
        #                         cls.adjust_key1: {
        #                             "2009": 100, "2010": 100}}}},
        #             "mseg_out_break": {}}}}
        cls.compete_meas2 = {
            "name": "sample compete measure r2",
            "climate_zone": ["AIA_CZ1"],
            "bldg_type": ["single family home"],
            "end_use": {"primary": ["cooling"], "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "yrs_on_mkt": ["2009", "2010"],
            "markets": {
                "Technical potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 20, "2010": 20},
                                "measure": {"2009": 20, "2010": 20}},
                            "competed": {
                                "all": {"2009": 10, "2010": 10},
                                "measure": {"2009": 10, "2010": 10}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 40, "2010": 40},
                                "efficient": {"2009": 30, "2010": 30}},
                            "competed": {
                                "baseline": {"2009": 20, "2010": 20},
                                "efficient": {"2009": 10, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 40, "2010": 40}},
                            "competed": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 10, "2010": 10}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 30, "2010": 30}},
                                "competed": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 10, "2010": 10}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 40, "2010": 40}},
                                "competed": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 10, "2010": 10}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.adjust_key1: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                            str(('primary', 'AIA_CZ2', 'single family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                        "competed choice parameters": {
                            cls.adjust_key1: {
                                "b1": {"2009": -0.95, "2010": -0.95},
                                "b2": {"2009": -0.10, "2010": -0.10}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}
                                },
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 20, "2010": 20},
                                "measure": {"2009": 20, "2010": 20}},
                            "competed": {
                                "all": {"2009": 10, "2010": 10},
                                "measure": {"2009": 10, "2010": 10}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 40, "2010": 40},
                                "efficient": {"2009": 30, "2010": 30}},
                            "competed": {
                                "baseline": {"2009": 20, "2010": 20},
                                "efficient": {"2009": 10, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 40, "2010": 40}},
                            "competed": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 10, "2010": 10}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 30, "2010": 30}},
                                "competed": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 10, "2010": 10}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 40, "2010": 40}},
                                "competed": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 10, "2010": 10}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.adjust_key1: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                            str(('primary', 'AIA_CZ2', 'single family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                        "competed choice parameters": {
                            cls.adjust_key1: {
                                "b1": {"2009": -0.95, "2010": -0.95},
                                "b2": {"2009": -0.10, "2010": -0.10}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}
                        },
                    "mseg_out_break": {}}}}
        cls.compete_meas3 = {
            "name": "sample compete measure r3",
            "climate_zone": ["AIA_CZ1"],
            "bldg_type": ["single family home"],
            "end_use": {"primary": ["cooling"], "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "yrs_on_mkt": ["2009", "2010"],
            "markets": {
                "Technical potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 10, "2010": 10},
                                "measure": {"2009": 10, "2010": 10}},
                            "competed": {
                                "all": {"2009": 5, "2010": 5},
                                "measure": {"2009": 5, "2010": 5}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 20, "2010": 20},
                                "efficient": {"2009": 15, "2010": 15}},
                            "competed": {
                                "baseline": {"2009": 10, "2010": 10},
                                "efficient": {"2009": 5, "2010": 5}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 20, "2010": 20}},
                            "competed": {
                                "baseline": {"2009": 15, "2010": 15},
                                "efficient": {"2009": 5, "2010": 5}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 15, "2010": 15}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 20, "2010": 20}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 5, "2010": 5}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.adjust_key2: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                        "competed choice parameters": {
                            cls.adjust_key2: {
                                "b1": {"2009": -0.95, "2010": -0.95},
                                "b2": {"2009": -0.10, "2010": -0.10}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}
                                },
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 10, "2010": 10},
                                "measure": {"2009": 10, "2010": 10}},
                            "competed": {
                                "all": {"2009": 5, "2010": 5},
                                "measure": {"2009": 5, "2010": 5}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 20, "2010": 20},
                                "efficient": {"2009": 15, "2010": 15}},
                            "competed": {
                                "baseline": {"2009": 10, "2010": 10},
                                "efficient": {"2009": 5, "2010": 5}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 20, "2010": 20}},
                            "competed": {
                                "baseline": {"2009": 15, "2010": 15},
                                "efficient": {"2009": 5, "2010": 5}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 5, "2010": 5}},
                                "competed": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 15, "2010": 15}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 5, "2010": 5}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 20, "2010": 20}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 5, "2010": 5}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.adjust_key2: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                        "competed choice parameters": {
                            cls.adjust_key2: {
                                "b1": {"2009": -0.95, "2010": -0.95},
                                "b2": {"2009": -0.10, "2010": -0.10}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}
                                },
                    "mseg_out_break": {}}}}
        # cls.compete_meas3_dist = {
        #     "name": "sample compete measure r3 dist",
        #     "climate_zone": ["AIA_CZ1"],
        #     "bldg_type": ["single family home"],
        #     "end_use": {"primary": ["cooling"], "secondary": None},
        #     "market_entry_year": None,
        #     "market_exit_year": None,
        #     "yrs_on_mkt": ["2009", "2010"],
        #     "markets": {
        #         "Technical potential": {
        #             "master_mseg": {
        #                 "stock": {
        #                     "total": {
        #                         "all": {"2009": 10, "2010": 10},
        #                         "measure": {"2009": 10, "2010": 10}},
        #                     "competed": {
        #                         "all": {"2009": 5, "2010": 5},
        #                         "measure": {"2009": 5, "2010": 5}}},
        #                 "energy": {
        #                     "total": {
        #                         "baseline": {"2009": 20, "2010": 20},
        #                         "efficient": {"2009": 15, "2010": 15}},
        #                     "competed": {
        #                         "baseline": {"2009": 10, "2010": 10},
        #                         "efficient": {"2009": 5, "2010": 5}}},
        #                 "carbon": {
        #                     "total": {
        #                         "baseline": {"2009": 30, "2010": 30},
        #                         "efficient": {"2009": 20, "2010": 20}},
        #                     "competed": {
        #                         "baseline": {"2009": 15, "2010": 15},
        #                         "efficient": {"2009": 5, "2010": 5}}},
        #                 "cost": {
        #                     "stock": {
        #                         "total": {
        #                             "baseline": {"2009": 10, "2010": 10},
        #                             "efficient": {
        #                                 "2009": numpy.array([5, 6, 7]),
        #                                 "2010": numpy.array([5, 6, 7])}},
        #                         "competed": {
        #                             "baseline": {"2009": 5, "2010": 5},
        #                             "efficient": {
        #                                 "2009": numpy.array([0, 1, 2]),
        #                                 "2010": numpy.array([0, 1, 2])}}},
        #                     "energy": {
        #                         "total": {
        #                             "baseline": {"2009": 20, "2010": 20},
        #                             "efficient": {"2009": 15, "2010": 15}},
        #                         "competed": {
        #                             "baseline": {"2009": 10, "2010": 10},
        #                             "efficient": {"2009": 5, "2010": 5}}},
        #                     "carbon": {
        #                         "total": {
        #                             "baseline": {"2009": 30, "2010": 30},
        #                             "efficient": {"2009": 20, "2010": 20}},
        #                         "competed": {
        #                             "baseline": {"2009": 15, "2010": 15},
        #                             "efficient": {"2009": 5, "2010": 5}}}},
        #                 "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                              "measure": {"2009": 1, "2010": 1}}},
        #             "mseg_adjust": {
        #                 "contributing mseg keys and values": {
        #                     cls.adjust_key2: {
        #                         "stock": {
        #                             "total": {
        #                                 "all": {"2009": 10, "2010": 10},
        #                                 "measure": {"2009": 10, "2010": 10}},
        #                             "competed": {
        #                                 "all": {"2009": 5, "2010": 5},
        #                                 "measure": {"2009": 5, "2010": 5}}},
        #                         "energy": {
        #                             "total": {
        #                                 "baseline": {"2009": 20, "2010": 20},
        #                                 "efficient": {"2009": 15, "2010": 15}},
        #                             "competed": {
        #                                 "baseline": {"2009": 10, "2010": 10},
        #                                 "efficient": {"2009": 5, "2010": 5}}},
        #                         "carbon": {
        #                             "total": {
        #                                 "baseline": {"2009": 30, "2010": 30},
        #                                 "efficient": {"2009": 20, "2010": 20}},
        #                             "competed": {
        #                                 "baseline": {"2009": 15, "2010": 15},
        #                                 "efficient": {"2009": 5, "2010": 5}}},
        #                             "cost": {
        #                                 "stock": {
        #                                     "total": {
        #                                         "baseline": {
        #                                             "2009": 10, "2010": 10},
        #                                         "efficient": {
        #                                             "2009": numpy.array(
        #                                                 [5, 6, 7]),
        #                                             "2010": numpy.array(
        #                                                 [5, 6, 7])}},
        #                                     "competed": {
        #                                         "baseline": {
        #                                             "2009": 5, "2010": 5},
        #                                         "efficient": {
        #                                             "2009": numpy.array(
        #                                                 [0, 1, 2]),
        #                                             "2010": numpy.array(
        #                                                 [0, 1, 2])}}},
        #                             "energy": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 20, "2010": 20},
        #                                     "efficient": {
        #                                         "2009": 15, "2010": 15}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": 5, "2010": 5}}},
        #                             "carbon": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 30, "2010": 30},
        #                                     "efficient": {
        #                                         "2009": 20, "2010": 20}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 15, "2010": 15},
        #                                     "efficient": {
        #                                         "2009": 5, "2010": 5}}}},
        #                         "lifetime": {
        #                             "baseline": {"2009": 1, "2010": 1},
        #                             "measure": {"2009": 1, "2010": 1}}}},
        #                 "competed choice parameters": {
        #                     cls.adjust_key2: {
        #                         "b1": {"2009": -0.95, "2010": -0.95},
        #                         "b2": {"2009": -0.10, "2010": -0.10}}},
        #                 "secondary mseg adjustments": {
        #                     "market share": {
        #                         "original energy (total captured)": {},
        #                         "original energy (competed and captured)": {},
        #                         "adjusted energy (total captured)": {},
        #                         "adjusted energy (competed and captured)": {}}},
        #                 "supply-demand adjustment": {
        #                     "savings": {
        #                         cls.adjust_key2: {
        #                             "2009": 0, "2010": 0}},
        #                     "total": {
        #                         cls.adjust_key2: {
        #                             "2009": 100, "2010": 100}}}},
        #             "mseg_out_break": {}},
        #         "Max adoption potential": {
        #             "master_mseg": {
        #                 "stock": {
        #                     "total": {
        #                         "all": {"2009": 10, "2010": 10},
        #                         "measure": {"2009": 10, "2010": 10}},
        #                     "competed": {
        #                         "all": {"2009": 5, "2010": 5},
        #                         "measure": {"2009": 5, "2010": 5}}},
        #                 "energy": {
        #                     "total": {
        #                         "baseline": {"2009": 20, "2010": 20},
        #                         "efficient": {"2009": 15, "2010": 15}},
        #                     "competed": {
        #                         "baseline": {"2009": 10, "2010": 10},
        #                         "efficient": {"2009": 5, "2010": 5}}},
        #                 "carbon": {
        #                     "total": {
        #                         "baseline": {"2009": 30, "2010": 30},
        #                         "efficient": {"2009": 20, "2010": 20}},
        #                     "competed": {
        #                         "baseline": {"2009": 15, "2010": 15},
        #                         "efficient": {"2009": 5, "2010": 5}}},
        #                 "cost": {
        #                     "stock": {
        #                         "total": {
        #                             "baseline": {"2009": 10, "2010": 10},
        #                             "efficient": {
        #                                 "2009": numpy.array([5, 6, 7]),
        #                                 "2010": numpy.array([5, 6, 7])}},
        #                         "competed": {
        #                             "baseline": {"2009": 5, "2010": 5},
        #                             "efficient": {
        #                                 "2009": numpy.array([0, 1, 2]),
        #                                 "2010": numpy.array([0, 1, 2])}}},
        #                     "energy": {
        #                         "total": {
        #                             "baseline": {"2009": 20, "2010": 20},
        #                             "efficient": {"2009": 15, "2010": 15}},
        #                         "competed": {
        #                             "baseline": {"2009": 10, "2010": 10},
        #                             "efficient": {"2009": 5, "2010": 5}}},
        #                     "carbon": {
        #                         "total": {
        #                             "baseline": {"2009": 30, "2010": 30},
        #                             "efficient": {"2009": 20, "2010": 20}},
        #                         "competed": {
        #                             "baseline": {"2009": 15, "2010": 15},
        #                             "efficient": {"2009": 5, "2010": 5}}}},
        #                 "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                              "measure": {"2009": 1, "2010": 1}}},
        #             "mseg_adjust": {
        #                 "contributing mseg keys and values": {
        #                     cls.adjust_key2: {
        #                         "stock": {
        #                             "total": {
        #                                 "all": {"2009": 10, "2010": 10},
        #                                 "measure": {"2009": 10, "2010": 10}},
        #                             "competed": {
        #                                 "all": {"2009": 5, "2010": 5},
        #                                 "measure": {"2009": 5, "2010": 5}}},
        #                         "energy": {
        #                             "total": {
        #                                 "baseline": {"2009": 20, "2010": 20},
        #                                 "efficient": {"2009": 15, "2010": 15}},
        #                             "competed": {
        #                                 "baseline": {"2009": 10, "2010": 10},
        #                                 "efficient": {"2009": 5, "2010": 5}}},
        #                         "carbon": {
        #                             "total": {
        #                                 "baseline": {"2009": 30, "2010": 30},
        #                                 "efficient": {"2009": 20, "2010": 20}},
        #                             "competed": {
        #                                 "baseline": {"2009": 15, "2010": 15},
        #                                 "efficient": {"2009": 5, "2010": 5}}},
        #                             "cost": {
        #                                 "stock": {
        #                                     "total": {
        #                                         "baseline": {
        #                                             "2009": 10, "2010": 10},
        #                                         "efficient": {
        #                                             "2009": numpy.array(
        #                                                 [5, 6, 7]),
        #                                             "2010": numpy.array(
        #                                                 [5, 6, 7])}},
        #                                     "competed": {
        #                                         "baseline": {
        #                                             "2009": 5, "2010": 5},
        #                                         "efficient": {
        #                                             "2009": numpy.array(
        #                                                 [0, 1, 2]),
        #                                             "2010": numpy.array(
        #                                                 [0, 1, 2])}}},
        #                             "energy": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 20, "2010": 20},
        #                                     "efficient": {
        #                                         "2009": 15, "2010": 15}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": 5, "2010": 5}}},
        #                             "carbon": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 30, "2010": 30},
        #                                     "efficient": {
        #                                         "2009": 20, "2010": 20}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 15, "2010": 15},
        #                                     "efficient": {
        #                                         "2009": 5, "2010": 5}}}},
        #                         "lifetime": {
        #                             "baseline": {"2009": 1, "2010": 1},
        #                             "measure": {"2009": 1, "2010": 1}}}},
        #                 "competed choice parameters": {
        #                     cls.adjust_key2: {
        #                         "b1": {"2009": -0.95, "2010": -0.95},
        #                         "b2": {"2009": -0.10, "2010": -0.10}}},
        #                 "secondary mseg adjustments": {
        #                     "market share": {
        #                         "original energy (total captured)": {},
        #                         "original energy (competed and captured)": {},
        #                         "adjusted energy (total captured)": {},
        #                         "adjusted energy (competed and captured)": {}}},
        #                 "supply-demand adjustment": {
        #                     "savings": {
        #                         cls.adjust_key2: {
        #                             "2009": 0, "2010": 0}},
        #                     "total": {
        #                         cls.adjust_key2: {
        #                             "2009": 100, "2010": 100}}}},
        #             "mseg_out_break": {}}}}
        cls.compete_meas4 = {
            "name": "sample compete measure r4",
            "climate_zone": ["AIA_CZ1"],
            "bldg_type": ["single family home"],
            "end_use": {"primary": ["cooling"], "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "yrs_on_mkt": ["2009", "2010"],
            "markets": {
                "Technical potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 20, "2010": 20},
                                "measure": {"2009": 20, "2010": 20}},
                            "competed": {
                                "all": {"2009": 10, "2010": 10},
                                "measure": {"2009": 10, "2010": 10}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 40, "2010": 40},
                                "efficient": {"2009": 30, "2010": 30}},
                            "competed": {
                                "baseline": {"2009": 20, "2010": 20},
                                "efficient": {"2009": 10, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 40, "2010": 40}},
                            "competed": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 10, "2010": 10}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 30, "2010": 30}},
                                "competed": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 10, "2010": 10}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 40, "2010": 40}},
                                "competed": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 10, "2010": 10}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.adjust_key2: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                            str(('primary', 'AIA_CZ2', 'single family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                        "competed choice parameters": {
                            cls.adjust_key2: {
                                "b1": {"2009": -0.95, "2010": -0.95},
                                "b2": {"2009": -0.10, "2010": -0.10}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}},
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 20, "2010": 20},
                                "measure": {"2009": 20, "2010": 20}},
                            "competed": {
                                "all": {"2009": 10, "2010": 10},
                                "measure": {"2009": 10, "2010": 10}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 40, "2010": 40},
                                "efficient": {"2009": 30, "2010": 30}},
                            "competed": {
                                "baseline": {"2009": 20, "2010": 20},
                                "efficient": {"2009": 10, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 40, "2010": 40}},
                            "competed": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 10, "2010": 10}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 30, "2010": 30}},
                                "competed": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 10, "2010": 10}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 40, "2010": 40}},
                                "competed": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 10, "2010": 10}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.adjust_key2: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                            str(('primary', 'AIA_CZ2', 'single family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                        "competed choice parameters": {
                            cls.adjust_key2: {
                                "b1": {"2009": -0.95, "2010": -0.95},
                                "b2": {"2009": -0.10, "2010": -0.10}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}},
                    "mseg_out_break": {}}}}
        cls.compete_meas5 = {
            "name": "sample compete measure r5",
            "climate_zone": ["AIA_CZ1"],
            "bldg_type": ["single family home"],
            "end_use": {"primary": ["cooling"], "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "yrs_on_mkt": ["2009", "2010"],
            "markets": {
                "Technical potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 30, "2010": 30},
                                "measure": {"2009": 30, "2010": 30}},
                            "competed": {
                                "all": {"2009": 15, "2010": 15},
                                "measure": {"2009": 15, "2010": 15}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 45, "2010": 45}},
                            "competed": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 15, "2010": 15}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 90, "2010": 90},
                                "efficient": {"2009": 60, "2010": 60}},
                            "competed": {
                                "baseline": {"2009": 45, "2010": 45},
                                "efficient": {"2009": 15, "2010": 15}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 15, "2010": 15}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 45, "2010": 45}},
                                "competed": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 15, "2010": 15}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 90, "2010": 90},
                                    "efficient": {"2009": 60, "2010": 60}},
                                "competed": {
                                    "baseline": {"2009": 45, "2010": 45},
                                    "efficient": {"2009": 15, "2010": 15}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.adjust_key2: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                            str(('primary', 'AIA_CZ2', 'single family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                            str(('primary', 'AIA_CZ2', 'multi family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                        "competed choice parameters": {
                            cls.adjust_key2: {
                                "b1": {"2009": -0.95, "2010": -0.95},
                                "b2": {"2009": -0.10, "2010": -0.10}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}},
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 30, "2010": 30},
                                "measure": {"2009": 30, "2010": 30}},
                            "competed": {
                                "all": {"2009": 15, "2010": 15},
                                "measure": {"2009": 15, "2010": 15}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 45, "2010": 45}},
                            "competed": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 15, "2010": 15}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 90, "2010": 90},
                                "efficient": {"2009": 60, "2010": 60}},
                            "competed": {
                                "baseline": {"2009": 45, "2010": 45},
                                "efficient": {"2009": 15, "2010": 15}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 15, "2010": 15}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 45, "2010": 45}},
                                "competed": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 15, "2010": 15}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 90, "2010": 90},
                                    "efficient": {"2009": 60, "2010": 60}},
                                "competed": {
                                    "baseline": {"2009": 45, "2010": 45},
                                    "efficient": {"2009": 15, "2010": 15}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.adjust_key2: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                            str(('primary', 'AIA_CZ2', 'single family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                            str(('primary', 'AIA_CZ2', 'multi family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                        "competed choice parameters": {
                            cls.adjust_key2: {
                                "b1": {"2009": -0.95, "2010": -0.95},
                                "b2": {"2009": -0.10, "2010": -0.10}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {},
                                "original energy (competed and captured)": {},
                                "adjusted energy (total captured)": {},
                                "adjusted energy (competed and captured)": {}}}},
                    "mseg_out_break": {}}}}
        cls.measures_all = [run.Measure(cls.handyvars, **x) for x in [
            cls.compete_meas1, copy.deepcopy(cls.compete_meas2),
            cls.compete_meas3, copy.deepcopy(cls.compete_meas4),
            copy.deepcopy(cls.compete_meas5)]]
        cls.measures_demand = cls.measures_all[0:2]
        cls.measures_supply = cls.measures_all[2:5]
        cls.measures_overlap1 = {
            "measures": cls.measures_all[2:5],
            "keys": [[str(('primary', 'AIA_CZ1', 'single family home',
                           'electricity (grid)',
                           'cooling', 'supply', 'ASHP', 'existing'))],
                     [str(('primary', 'AIA_CZ1', 'single family home',
                           'electricity (grid)',
                           'cooling', 'supply', 'ASHP', 'existing'))],
                     [str(('primary', 'AIA_CZ1', 'single family home',
                           'electricity (grid)',
                           'cooling', 'supply', 'ASHP', 'existing'))]]}
        cls.measures_overlap2 = {
            "measures": cls.measures_all[0:2],
            "keys": [[str(('primary', 'AIA_CZ1', 'single family home',
                           'electricity (grid)',
                           'cooling', 'demand', 'windows', 'existing'))],
                     [str(('primary', 'AIA_CZ1', 'single family home',
                           'electricity (grid)',
                           'cooling', 'demand', 'windows', 'existing'))]]}
        cls.a_run = run.Engine(cls.handyvars, cls.measures_all)
        # Set information needed to finalize point value test measure
        # consumer metrics
        consumer_metrics_final = [{
            "stock cost": {
                "residential": {
                    "2009": 95,
                    "2010": 95},
                "commercial": {
                    "2009": None,
                    "2010": None}},
            "energy cost": {
                "residential": {
                    "2009": -150,
                    "2010": -150},
                "commercial": {
                    "2009": None,
                    "2010": None}},
            "carbon cost": {
                "residential": {
                    "2009": -150,
                    "2010": -50},
                "commercial": {
                    "2009": None,
                    "2010": None}}},
            {
            "stock cost": {
                "residential": {
                    "2009": 120,
                    "2010": 120},
                "commercial": {
                    "2009": None,
                    "2010": None}},
            "energy cost": {
                "residential": {
                    "2009": -400,
                    "2010": -400},
                "commercial": {
                    "2009": None,
                    "2010": None}},
            "carbon cost": {
                "residential": {
                    "2009": -50,
                    "2010": -50},
                "commercial": {
                    "2009": None,
                    "2010": None}}},
            {
            "stock cost": {
                "residential": {
                    "2009": 95,
                    "2010": 95},
                "commercial": {
                    "2009": None,
                    "2010": None}},
            "energy cost": {
                "residential": {
                    "2009": -150,
                    "2010": -150},
                "commercial": {
                    "2009": None,
                    "2010": None}},
            "carbon cost": {
                "residential": {
                    "2009": -150,
                    "2010": -50},
                "commercial": {
                    "2009": None,
                    "2010": None}}},
            {
            "stock cost": {
                "residential": {
                    "2009": 120,
                    "2010": 120},
                "commercial": {
                    "2009": None,
                    "2010": None}},
            "energy cost": {
                "residential": {
                    "2009": -400,
                    "2010": -400},
                "commercial": {
                    "2009": None,
                    "2010": None}},
            "carbon cost": {
                "residential": {
                    "2009": -50,
                    "2010": -50},
                "commercial": {
                    "2009": None,
                    "2010": None}}},
            {
            "stock cost": {
                "residential": {
                    "2009": 100,
                    "2010": 100},
                "commercial": {
                    "2009": None,
                    "2010": None}},
            "energy cost": {
                "residential": {
                    "2009": -200,
                    "2010": -200},
                "commercial": {
                    "2009": None,
                    "2010": None}},
            "carbon cost": {
                "residential": {
                    "2009": -100,
                    "2010": -100},
                "commercial": {
                    "2009": None,
                    "2010": None}}}]
        # Adjust/finalize point value test measure consumer metrics
        for ind, m in enumerate(cls.a_run.measures):
            m.consumer_metrics['anpv'] = consumer_metrics_final[ind]
        # cls.measures_all_dist = [run.Measure(cls.handyvars, **x) for x in [
        #     cls.compete_meas1_dist, copy.deepcopy(cls.compete_meas2),
        #     cls.compete_meas3_dist, copy.deepcopy(cls.compete_meas4),
        #     copy.deepcopy(cls.compete_meas5)]]
        # cls.measures_demand_dist = cls.measures_all_dist[0:2]
        # cls.measures_supply_dist = cls.measures_all_dist[2:5]
        # cls.supply_demand_adjust1_dist = cls.measures_all_dist[0:2]
        # cls.supply_demand_adjust2_dist = cls.measures_all_dist[2:5]
        # cls.measures_overlap1_dist = {
        #     "measures": cls.measures_all_dist[2:5],
        #     "keys": [[str(('primary', 'AIA_CZ1', 'single family home',
        #                    'electricity (grid)',
        #                    'cooling', 'supply', 'ASHP', 'existing'))],
        #              [str(('primary', 'AIA_CZ1', 'single family home',
        #                    'electricity (grid)',
        #                    'cooling', 'supply', 'ASHP', 'existing'))],
        #              [str(('primary', 'AIA_CZ1', 'single family home',
        #                    'electricity (grid)',
        #                    'cooling', 'supply', 'ASHP', 'existing'))]]}
        # cls.measures_overlap2_dist = {
        #     "measures": cls.measures_all_dist[0:2],
        #     "keys": [[str(('primary', 'AIA_CZ1', 'single family home',
        #                    'electricity (grid)',
        #                    'cooling', 'demand', 'windows', 'existing'))],
        #              [str(('primary', 'AIA_CZ1', 'single family home',
        #                    'electricity (grid)',
        #                    'cooling', 'demand', 'windows', 'existing'))]]}
        # cls.a_run_dist = run.Engine(cls.handyvars, cls.measures_all_dist)
        # Set information needed to finalize array test measure consumer
        # metrics
        # consumer_metrics_final_dist = [{
        #     "stock cost": {
        #         "2009": {"residential": 95, "commercial": None},
        #         "2010": {"residential": 95, "commercial": None}},
        #     "energy cost": {
        #         "2009": numpy.array([
        #             {"residential": -150,
        #              "commercial": None},
        #             {"residential": -200,
        #              "commercial": None},
        #             {"residential": -100,
        #              "commercial": None}]),
        #         "2010": numpy.array([
        #             {"residential": -150,
        #              "commercial": None},
        #             {"residential": -200,
        #              "commercial": None},
        #             {"residential": -100,
        #              "commercial": None}])},
        #     "carbon cost": {
        #         "2009": numpy.array([
        #             {"residential": -150,
        #              "commercial": None},
        #             {"residential": -200,
        #              "commercial": None},
        #             {"residential": -100,
        #              "commercial": None}]),
        #         "2010": numpy.array([
        #             {"residential": -50,
        #              "commercial": None},
        #             {"residential": -100,
        #              "commercial": None},
        #             {"residential": -10,
        #              "commercial": None}])}},
        #     {
        #     "stock cost": {
        #         "2009": {"residential": 120, "commercial": None},
        #         "2010": {"residential": 120, "commercial": None}},
        #     "energy cost": {
        #         "2009": {"residential": -400, "commercial": None},
        #         "2010": {"residential": -400, "commercial": None}},
        #     "carbon cost": {
        #         "2009": {"residential": -50, "commercial": None},
        #         "2010": {"residential": -50, "commercial": None}}},
        #     {
        #     "stock cost": {
        #         "2009": numpy.array([
        #             {"residential": 95,
        #              "commercial": None},
        #             {"residential": 100,
        #              "commercial": None},
        #             {"residential": 90,
        #              "commercial": None}]),
        #         "2010": numpy.array([
        #             {"residential": 95,
        #              "commercial": None},
        #             {"residential": 100,
        #              "commercial": None},
        #             {"residential": 90,
        #              "commercial": None}])},
        #     "energy cost": {
        #         "2009": {"residential": -150, "commercial": None},
        #         "2010": {"residential": -150, "commercial": None}},
        #     "carbon cost": {
        #         "2009": {"residential": -150, "commercial": None},
        #         "2010": {"residential": -50, "commercial": None}}},
        #     {
        #     "stock cost": {
        #         "2009": {"residential": 120, "commercial": None},
        #         "2010": {"residential": 120, "commercial": None}},
        #     "energy cost": {
        #         "2009": {"residential": -400, "commercial": None},
        #         "2010": {"residential": -400, "commercial": None}},
        #     "carbon cost": {
        #         "2009": {"residential": -50, "commercial": None},
        #         "2010": {"residential": -50, "commercial": None}}},
        #     {
        #     "stock cost": {
        #         "2009": {"residential": 100, "commercial": None},
        #         "2010": {"residential": 100, "commercial": None}},
        #     "energy cost": {
        #         "2009": {"residential": -200, "commercial": None},
        #         "2010": {"residential": -200, "commercial": None}},
        #     "carbon cost": {
        #         "2009": {"residential": -100, "commercial": None},
        #         "2010": {"residential": -100, "commercial": None}}}]
        # Adjust/finalize point value test measure consumer metrics
        # for ind, m in enumerate(cls.a_run_dist.measures):
        #     m.consumer_metrics['anpv'] = consumer_metrics_final_dist[ind]
        cls.measures_master_msegs_out = [{
            "stock": {
                "total": {
                    "all": {"2009": 10, "2010": 10},
                    "measure": {"2009": 2.23, "2010": 2.23}},
                "competed": {
                    "all": {"2009": 5, "2010": 5},
                    "measure": {"2009": 1.11, "2010": 1.11}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 2.227001, "2010": 2.227001},
                    "efficient": {"2009": 1.670251, "2010": 1.670251}},
                "competed": {
                    "baseline": {"2009": 1.113501, "2010": 1.113501},
                    "efficient": {"2009": 0.5567503, "2010": 0.5567503}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 3.340502, "2010": 3.340502},
                    "efficient": {"2009": 2.227001, "2010": 2.227001}},
                "competed": {
                    "baseline": {"2009": 1.670251, "2010": 1.670251},
                    "efficient": {"2009": 0.5567503, "2010": 0.5567503}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 2.227001, "2010": 2.227001},
                        "efficient": {"2009": 1.113501, "2010": 1.113501}},
                    "competed": {
                        "baseline": {"2009": 1.113501, "2010": 1.113501},
                        "efficient": {"2009": 0, "2010": 0}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 2.227001, "2010": 2.227001},
                        "efficient": {"2009": 1.670251, "2010": 1.670251}},
                    "competed": {
                        "baseline": {"2009": 1.113501, "2010": 1.113501},
                        "efficient": {"2009": 0.5567503, "2010": 0.5567503}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 3.340502, "2010": 3.340502},
                        "efficient": {"2009": 2.227001, "2010": 2.227001}},
                    "competed": {
                        "baseline": {"2009": 1.670251, "2010": 1.670251},
                        "efficient": {"2009": 0.5567503, "2010": 0.5567503}}}},
            "lifetime": {"baseline": {"2009": 1, "2010": 1},
                         "measure": {"2009": 1, "2010": 1}}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 20, "2010": 20},
                    "measure": {"2009": 17.77, "2010": 17.77}},
                "competed": {
                    "all": {"2009": 10, "2010": 10},
                    "measure": {"2009": 8.89, "2010": 8.89}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 27.77300, "2010": 27.77300},
                    "efficient": {"2009": 20.82975, "2010": 20.82975}},
                "competed": {
                    "baseline": {"2009": 13.88650, "2010": 13.88650},
                    "efficient": {"2009": 6.943250, "2010": 6.943250}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 41.65950, "2010": 41.65950},
                    "efficient": {"2009": 27.77300, "2010": 27.77300}},
                "competed": {
                    "baseline": {"2009": 20.82975, "2010": 20.82975},
                    "efficient": {"2009": 6.943250, "2010": 6.943250}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 17.77300, "2010": 17.77300},
                        "efficient": {"2009": 8.886499, "2010": 8.886499}},
                    "competed": {
                        "baseline": {"2009": 8.886499, "2010": 8.886499},
                        "efficient": {"2009": 0, "2010": 0}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 27.77300, "2010": 27.77300},
                        "efficient": {"2009": 20.82975, "2010": 20.82975}},
                    "competed": {
                        "baseline": {"2009": 13.88650, "2010": 13.88650},
                        "efficient": {"2009": 6.943250, "2010": 6.943250}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 41.65950, "2010": 41.65950},
                        "efficient": {"2009": 27.77300, "2010": 27.77300}},
                    "competed": {
                        "baseline": {"2009": 20.82975, "2010": 20.82975},
                        "efficient": {"2009": 6.943250, "2010": 6.943250}}}},
            "lifetime": {"baseline": {"2009": 1, "2010": 1},
                         "measure": {"2009": 1, "2010": 1}}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 10, "2010": 10},
                    "measure": {"2009": 1.73, "2010": 1.73}},
                "competed": {
                    "all": {"2009": 5, "2010": 5},
                    "measure": {"2009": 0.87, "2010": 0.87}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 1.73179114, "2010": 1.73179114},
                    "efficient": {"2009": 1.29884336, "2010": 1.29884336}},
                "competed": {
                    "baseline": {"2009": 0.865895571, "2010": 0.865895571},
                    "efficient": {"2009": 0.432947785, "2010": 0.432947785}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 2.59768671, "2010": 2.59768671},
                    "efficient": {"2009": 1.73179114, "2010": 1.73179114}},
                "competed": {
                    "baseline": {"2009": 1.29884336, "2010": 1.29884336},
                    "efficient": {"2009": 0.432947785, "2010": 0.432947785}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {
                            "2009": 1.73179114, "2010": 1.73179114},
                        "efficient": {
                            "2009": 0.865895571, "2010": 0.865895571}},
                    "competed": {
                        "baseline": {"2009": 0.865895571, "2010": 0.865895571},
                        "efficient": {"2009": 0, "2010": 0}}},
                "energy": {
                    "total": {
                        "baseline": {
                            "2009": 1.73179114, "2010": 1.73179114},
                        "efficient": {
                            "2009": 1.29884336, "2010": 1.29884336}},
                    "competed": {
                        "baseline": {
                            "2009": 0.865895571, "2010": 0.865895571},
                        "efficient": {
                            "2009": 0.432947785, "2010": 0.432947785}}},
                "carbon": {
                    "total": {
                        "baseline": {
                            "2009": 2.59768671, "2010": 2.59768671},
                        "efficient": {
                            "2009": 1.73179114, "2010": 1.73179114}},
                    "competed": {
                        "baseline": {
                            "2009": 1.29884336, "2010": 1.29884336},
                        "efficient": {
                            "2009": 0.432947785, "2010": 0.432947785}}}},
            "lifetime": {"baseline": {"2009": 1, "2010": 1},
                         "measure": {"2009": 1, "2010": 1}}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 20, "2010": 20},
                    "measure": {"2009": 16.04, "2010": 16.04}},
                "competed": {
                    "all": {"2009": 10, "2010": 10},
                    "measure": {"2009": 8.02, "2010": 8.02}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 26.04455, "2010": 26.04455},
                    "efficient": {"2009": 19.53341, "2010": 19.53341}},
                "competed": {
                    "baseline": {"2009": 13.02227, "2010": 13.02227},
                    "efficient": {"2009": 6.511136, "2010": 6.511136}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 39.06682, "2010": 39.06682},
                    "efficient": {"2009": 26.04455, "2010": 26.04455}},
                "competed": {
                    "baseline": {"2009": 19.53341, "2010": 19.53341},
                    "efficient": {"2009": 6.511136, "2010": 6.511136}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 16.04455, "2010": 16.04455},
                        "efficient": {"2009": 8.022273, "2010": 8.022273}},
                    "competed": {
                        "baseline": {"2009": 8.022273, "2010": 8.022273},
                        "efficient": {"2009": 0, "2010": 0}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 26.04455, "2010": 26.04455},
                        "efficient": {"2009": 19.53341, "2010": 19.53341}},
                    "competed": {
                        "baseline": {"2009": 13.02227, "2010": 13.02227},
                        "efficient": {"2009": 6.511136, "2010": 6.511136}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 39.06682, "2010": 39.06682},
                        "efficient": {"2009": 26.04455, "2010": 26.04455}},
                    "competed": {
                        "baseline": {"2009": 19.53341, "2010": 19.53341},
                        "efficient": {"2009": 6.511136, "2010": 6.511136}}}},
            "lifetime": {"baseline": {"2009": 1, "2010": 1},
                         "measure": {"2009": 1, "2010": 1}}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 30, "2010": 30},
                    "measure": {"2009": 22.22, "2010": 22.22}},
                "competed": {
                    "all": {"2009": 15, "2010": 15},
                    "measure": {"2009": 11.11, "2010": 11.11}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 42.22366, "2010": 42.22366},
                    "efficient": {"2009": 31.66775, "2010": 31.66775}},
                "competed": {
                    "baseline": {"2009": 21.11183, "2010": 21.11183},
                    "efficient": {"2009": 10.55592, "2010": 10.55592}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 63.33550, "2010": 63.33550},
                    "efficient": {"2009": 42.22366, "2010": 42.22366}},
                "competed": {
                    "baseline": {"2009": 31.66775, "2010": 31.66775},
                    "efficient": {"2009": 10.55592, "2010": 10.55592}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 22.22366, "2010": 22.22366},
                        "efficient": {"2009": 11.11183, "2010": 11.11183}},
                    "competed": {
                        "baseline": {"2009": 11.11183, "2010": 11.11183},
                        "efficient": {"2009": 0, "2010": 0}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 42.22366, "2010": 42.22366},
                        "efficient": {"2009": 31.66775, "2010": 31.66775}},
                    "competed": {
                        "baseline": {"2009": 21.11183, "2010": 21.11183},
                        "efficient": {"2009": 10.55592, "2010": 10.55592}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 63.33550, "2010": 63.33550},
                        "efficient": {"2009": 42.22366, "2010": 42.22366}},
                    "competed": {
                        "baseline": {"2009": 31.66775, "2010": 31.66775},
                        "efficient": {"2009": 10.55592, "2010": 10.55592}}}},
            "lifetime": {"baseline": {"2009": 1, "2010": 1},
                         "measure": {"2009": 1, "2010": 1}}}]
        # cls.measures_master_msegs_out_dist = [{
        #     "stock": {
        #         "total": {
        #             "all": {"2009": 10, "2010": 10},
        #             "measure": {
        #                 "2009": numpy.array([2.23, 9.77, 0.02]),
        #                 "2010": numpy.array([2.23, 9.77, 0.02])}},
        #         "competed": {
        #             "all": {"2009": 5, "2010": 5},
        #             "measure": {
        #                 "2009": numpy.array([1.11, 4.89, 0.01]),
        #                 "2010": numpy.array([1.11, 4.89, 0.01])}}},
        #     "energy": {
        #         "total": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     4.231303, 18.56343, 0.03660796]),
        #                 "2010": numpy.array([
        #                     4.231303, 18.56343, 0.03660796])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     3.173477, 14.85074, 0.03111676]),
        #                 "2010": numpy.array([
        #                     3.173477, 14.85074, 0.03111676])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     2.115651, 9.281715, 0.01830398]),
        #                 "2010": numpy.array([
        #                     2.115651, 9.281715, 0.01830398])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     1.057826, 5.569029, 0.01281279]),
        #                 "2010": numpy.array([
        #                     1.057826, 5.569029, 0.01281279])}}},
        #     "carbon": {
        #         "total": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     6.346954, 27.84514, 0.05491194]),
        #                 "2010": numpy.array([
        #                     6.346954, 27.84514, 0.05491194])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     4.231303, 19.4916, 0.04026875]),
        #                 "2010": numpy.array([
        #                     4.231303, 19.4916, 0.04026875])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     3.173477, 13.92257, 0.02745597]),
        #                 "2010": numpy.array([
        #                     3.173477, 13.92257, 0.02745597])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     1.057826, 5.569029, 0.01281279]),
        #                 "2010": numpy.array([
        #                     1.057826, 5.569029, 0.01281279])}}},
        #     "cost": {
        #         "stock": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         2.227001, 9.770226, 0.01926735]),
        #                     "2010": numpy.array([
        #                         2.227001, 9.770226, 0.01926735])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         1.113501, 4.885113, 0.009633673]),
        #                     "2010": numpy.array([
        #                         1.113501, 4.885113, 0.009633673])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         1.113501, 4.885113, 0.009633673]),
        #                     "2010": numpy.array([
        #                         1.113501, 4.885113, 0.009633673])},
        #                 "efficient": {
        #                     "2009": numpy.array([0, 0, 0]),
        #                     "2010": numpy.array([0, 0, 0])}}},
        #         "energy": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         4.231303, 18.56343, 0.03660796]),
        #                     "2010": numpy.array([
        #                         4.231303, 18.56343, 0.03660796])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         3.173477, 14.85074, 0.03111676]),
        #                     "2010": numpy.array([
        #                         3.173477, 14.85074, 0.03111676])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         2.115651, 9.281715, 0.01830398]),
        #                     "2010": numpy.array([
        #                         2.115651, 9.281715, 0.01830398])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         1.057826, 5.569029, 0.01281279]),
        #                     "2010": numpy.array([
        #                         1.057826, 5.569029, 0.01281279])}}},
        #         "carbon": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         6.346954, 27.84514, 0.05491194]),
        #                     "2010": numpy.array([
        #                         6.346954, 27.84514, 0.05491194])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         4.231303, 19.4916, 0.04026875]),
        #                     "2010": numpy.array([
        #                         4.231303, 19.4916, 0.04026875])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         3.173477, 13.92257, 0.02745597]),
        #                     "2010": numpy.array([
        #                         3.173477, 13.92257, 0.02745597])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         1.057826, 5.569029, 0.01281279]),
        #                     "2010": numpy.array([
        #                         1.057826, 5.569029, 0.01281279])}}}},
        #     "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                  "measure": {"2009": 1, "2010": 1}}},
        #     {
        #     "stock": {
        #         "total": {
        #             "all": {"2009": 20, "2010": 20},
        #             "measure": {
        #                 "2009": numpy.array([17.77, 10.23, 19.98]),
        #                 "2010": numpy.array([17.77, 10.23, 19.98])}},
        #         "competed": {
        #             "all": {"2009": 10, "2010": 10},
        #             "measure": {
        #                 "2009": numpy.array([8.89, 5.11, 9.99]),
        #                 "2010": numpy.array([8.89, 5.11, 9.99])}}},
        #     "energy": {
        #         "total": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     34.76870, 20.43657, 38.96339]),
        #                 "2010": numpy.array([
        #                     34.76870, 20.43657, 38.96339])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     26.07652, 15.32743, 29.22254]),
        #                 "2010": numpy.array([
        #                     26.07652, 15.32743, 29.22254])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     17.38435, 10.21829, 19.48170]),
        #                 "2010": numpy.array([
        #                     17.38435, 10.21829, 19.48170])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     8.692174, 5.109143, 9.740848]),
        #                 "2010": numpy.array([
        #                     8.692174, 5.109143, 9.740848])}}},
        #     "carbon": {
        #         "total": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     52.15305, 30.65486, 58.44509]),
        #                 "2010": numpy.array([
        #                     52.15305, 30.65486, 58.44509])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     34.76870, 20.43657, 38.96339]),
        #                 "2010": numpy.array([
        #                     34.76870, 20.43657, 38.96339])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     26.07652, 15.32743, 29.22254]),
        #                 "2010": numpy.array([
        #                     26.07652, 15.32743, 29.22254])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     8.692174, 5.109143, 9.740848]),
        #                 "2010": numpy.array([
        #                     8.692174, 5.109143, 9.740848])}}},
        #     "cost": {
        #         "stock": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         17.77300, 10.22977, 19.98073]),
        #                     "2010": numpy.array([
        #                         17.77300, 10.22977, 19.98073])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         8.886499, 5.114887, 9.990366]),
        #                     "2010": numpy.array([
        #                         8.886499, 5.114887, 9.990366])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         8.886499, 5.114887, 9.990366]),
        #                     "2010": numpy.array([
        #                         8.886499, 5.114887, 9.990366])},
        #                 "efficient": {
        #                     "2009": numpy.array([0, 0, 0]),
        #                     "2010": numpy.array([0, 0, 0])}}},
        #         "energy": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         34.76870, 20.43657, 38.96339]),
        #                     "2010": numpy.array([
        #                         34.76870, 20.43657, 38.96339])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         26.07652, 15.32743, 29.22254]),
        #                     "2010": numpy.array([
        #                         26.07652, 15.32743, 29.22254])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         17.38435, 10.21829, 19.48170]),
        #                     "2010": numpy.array([
        #                         17.38435, 10.21829, 19.48170])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         8.692174, 5.109143, 9.740848]),
        #                     "2010": numpy.array([
        #                         8.692174, 5.109143, 9.740848])}}},
        #         "carbon": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         52.15305, 30.65486, 58.44509]),
        #                     "2010": numpy.array([
        #                         52.15305, 30.65486, 58.44509])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         34.76870, 20.43657, 38.96339]),
        #                     "2010": numpy.array([
        #                         34.76870, 20.43657, 38.96339])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         26.07652, 15.32743, 29.22254]),
        #                     "2010": numpy.array([
        #                         26.07652, 15.32743, 29.22254])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         8.692174, 5.109143, 9.740848]),
        #                     "2010": numpy.array([
        #                         8.692174, 5.109143, 9.740848])}}}},
        #     "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                  "measure": {"2009": 1, "2010": 1}}},
        #     {
        #     "stock": {
        #         "total": {
        #             "all": {"2009": 10, "2010": 10},
        #             "measure": {
        #                 "2009": numpy.array([1.73, 0.02, 9.60]),
        #                 "2010": numpy.array([1.73, 0.02, 9.60])}},
        #         "competed": {
        #             "all": {"2009": 5, "2010": 5},
        #             "measure": {
        #                 "2009": numpy.array([0.87, 0.01, 4.80]),
        #                 "2010": numpy.array([0.87, 0.01, 4.80])}}},
        #     "energy": {
        #         "total": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     3.29040317, 0.03472132, 18.24705107]),
        #                 "2010": numpy.array([
        #                     3.29040317, 0.03472132, 18.24705107])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     2.46780238, 0.02604099, 13.68528830]),
        #                 "2010": numpy.array([
        #                     2.46780238, 0.02604099, 13.68528830])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     1.64520158, 0.01736066, 9.12352553]),
        #                 "2010": numpy.array([
        #                     1.64520158, 0.01736066, 9.12352553])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     0.822600792, 0.008680331, 4.561762767]),
        #                 "2010": numpy.array([
        #                     0.822600792, 0.008680331, 4.561762767])}}},
        #     "carbon": {
        #         "total": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     4.93560475, 0.05208199, 27.37057660]),
        #                 "2010": numpy.array([
        #                     4.93560475, 0.05208199, 27.37057660])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     3.29040317, 0.03472132, 18.24705107]),
        #                 "2010": numpy.array([
        #                     3.29040317, 0.03472132, 18.24705107])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     2.46780238, 0.02604099, 13.68528830]),
        #                 "2010": numpy.array([
        #                     2.46780238, 0.02604099, 13.68528830])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     0.822600792, 0.008680331, 4.561762767]),
        #                 "2010": numpy.array([
        #                     0.822600792, 0.008680331, 4.561762767])}}},
        #     "cost": {
        #         "stock": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         1.73179114, 0.01808835, 9.60332155]),
        #                     "2010": numpy.array([
        #                         1.73179114, 0.01808835, 9.60332155])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         0.865895571, 0.01085301, 6.722325]),
        #                     "2010": numpy.array([
        #                         0.865895571, 0.01085301, 6.722325])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         0.865895571, 0.009044176, 4.801660776]),
        #                     "2010": numpy.array([
        #                         0.865895571, 0.009044176, 4.801660776])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         0, 0.001808835, 1.920664]),
        #                     "2010": numpy.array([
        #                         0, 0.001808835, 1.920664])}}},
        #         "energy": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         3.29040317, 0.03472132, 18.24705107]),
        #                     "2010": numpy.array([
        #                         3.29040317, 0.03472132, 18.24705107])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         2.46780238, 0.02604099, 13.68528830]),
        #                     "2010": numpy.array([
        #                         2.46780238, 0.02604099, 13.68528830])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         1.64520158, 0.01736066, 9.12352553]),
        #                     "2010": numpy.array([
        #                         1.64520158, 0.01736066, 9.12352553])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         0.822600792, 0.008680331, 4.561762767]),
        #                     "2010": numpy.array([
        #                         0.822600792, 0.008680331, 4.561762767])}}},
        #         "carbon": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         4.93560475, 0.05208199, 27.37057660]),
        #                     "2010": numpy.array([
        #                         4.93560475, 0.05208199, 27.37057660])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         3.29040317, 0.03472132, 18.24705107]),
        #                     "2010": numpy.array([
        #                         3.29040317, 0.03472132, 18.24705107])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         2.46780238, 0.02604099, 13.68528830]),
        #                     "2010": numpy.array([
        #                         2.46780238, 0.02604099, 13.68528830])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         0.822600792, 0.008680331, 4.561762767]),
        #                     "2010": numpy.array([
        #                         0.822600792, 0.008680331, 4.561762767])}}}},
        #     "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                  "measure": {"2009": 1, "2010": 1}}},
        #     {
        #     "stock": {
        #         "total": {
        #             "all": {"2009": 20, "2010": 20},
        #             "measure": {
        #                 "2009": numpy.array([16.04, 17.30, 10.29]),
        #                 "2010": numpy.array([16.04, 17.30, 10.29])}},
        #         "competed": {
        #             "all": {"2009": 10, "2010": 10},
        #             "measure": {
        #                 "2009": numpy.array([8.02, 8.65, 5.14]),
        #                 "2010": numpy.array([8.02, 8.65, 5.14])}}},
        #     "energy": {
        #         "total": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     31.48464, 34.00758, 20.55101]),
        #                 "2010": numpy.array([
        #                     31.48464, 34.00758, 20.55101])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     23.61348, 25.50569, 15.41326]),
        #                 "2010": numpy.array([
        #                     23.61348, 25.50569, 15.41326])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     15.74232, 17.00379, 10.27551]),
        #                 "2010": numpy.array([
        #                     15.74232, 17.00379, 10.27551])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     7.871159, 8.501895, 5.137753]),
        #                 "2010": numpy.array([
        #                     7.871159, 8.501895, 5.137753])}}},
        #     "carbon": {
        #         "total": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     47.22695, 51.01137, 30.82652]),
        #                 "2010": numpy.array([
        #                     47.22695, 51.01137, 30.82652])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     31.48464, 34.00758, 20.55101]),
        #                 "2010": numpy.array([
        #                     31.48464, 34.00758, 20.55101])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     23.61348, 25.50569, 15.41326]),
        #                 "2010": numpy.array([
        #                     23.61348, 25.50569, 15.41326])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     7.871159, 8.501895, 5.137753]),
        #                 "2010": numpy.array([
        #                     7.871159, 8.501895, 5.137753])}}},
        #     "cost": {
        #         "stock": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         16.04455, 17.29736, 10.29000]),
        #                     "2010": numpy.array([
        #                         16.04455, 17.29736, 10.29000])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         8.022273, 8.648681, 5.144998]),
        #                     "2010": numpy.array([
        #                         8.022273, 8.648681, 5.144998])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         8.022273, 8.648681, 5.144998]),
        #                     "2010": numpy.array([
        #                         8.022273, 8.648681, 5.144998])},
        #                 "efficient": {
        #                     "2009": numpy.array([0, 0, 0]),
        #                     "2010": numpy.array([0, 0, 0])}}},
        #         "energy": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         31.48464, 34.00758, 20.55101]),
        #                     "2010": numpy.array([
        #                         31.48464, 34.00758, 20.55101])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         23.61348, 25.50569, 15.41326]),
        #                     "2010": numpy.array([
        #                         23.61348, 25.50569, 15.41326])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         15.74232, 17.00379, 10.27551]),
        #                     "2010": numpy.array([
        #                         15.74232, 17.00379, 10.27551])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         7.871159, 8.501895, 5.137753]),
        #                     "2010": numpy.array([
        #                         7.871159, 8.501895, 5.137753])}}},
        #         "carbon": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         47.22695, 51.01137, 30.82652]),
        #                     "2010": numpy.array([
        #                         47.22695, 51.01137, 30.82652])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         31.48464, 34.00758, 20.55101]),
        #                     "2010": numpy.array([
        #                         31.48464, 34.00758, 20.55101])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         23.61348, 25.50569, 15.41326]),
        #                     "2010": numpy.array([
        #                         23.61348, 25.50569, 15.41326])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         7.871159, 8.501895, 5.137753]),
        #                     "2010": numpy.array([
        #                         7.871159, 8.501895, 5.137753])}}}},
        #     "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                  "measure": {"2009": 1, "2010": 1}}},
        #     {
        #     "stock": {
        #         "total": {
        #             "all": {"2009": 30, "2010": 30},
        #             "measure": {
        #                 "2009": numpy.array([22.22, 22.68, 20.11]),
        #                 "2010": numpy.array([22.22, 22.68, 20.11])}},
        #         "competed": {
        #             "all": {"2009": 15, "2010": 15},
        #             "measure": {
        #                 "2009": numpy.array([11.11, 11.34, 10.05]),
        #                 "2010": numpy.array([11.11, 11.34, 10.05])}}},
        #     "energy": {
        #         "total": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     44.22496, 45.15310, 40.20271]),
        #                 "2010": numpy.array([
        #                     44.22496, 45.15310, 40.20271])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     33.16872, 33.86483, 30.15203]),
        #                 "2010": numpy.array([
        #                     33.16872, 33.86483, 30.15203])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     22.11248, 22.57655, 20.10135]),
        #                 "2010": numpy.array([
        #                     22.11248, 22.57655, 20.10135])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     11.05624, 11.28828, 10.05068]),
        #                 "2010": numpy.array([
        #                     11.05624, 11.28828, 10.05068])}}},
        #     "carbon": {
        #         "total": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     66.33744, 67.72965, 60.30406]),
        #                 "2010": numpy.array([
        #                     66.33744, 67.72965, 60.30406])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     44.22496, 45.15310, 40.20271]),
        #                 "2010": numpy.array([
        #                     44.22496, 45.15310, 40.20271])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": numpy.array([
        #                     33.16872, 33.86483, 30.15203]),
        #                 "2010": numpy.array([
        #                     33.16872, 33.86483, 30.15203])},
        #             "efficient": {
        #                 "2009": numpy.array([
        #                     11.05624, 11.28828, 10.05068]),
        #                 "2010": numpy.array([
        #                     11.05624, 11.28828, 10.05068])}}},
        #     "cost": {
        #         "stock": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         22.22366, 22.68455, 20.10668]),
        #                     "2010": numpy.array([
        #                         22.22366, 22.68455, 20.10668])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         11.11183, 11.34227, 10.05334]),
        #                     "2010": numpy.array([
        #                         11.11183, 11.34227, 10.05334])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         11.11183, 11.34227, 10.05334]),
        #                     "2010": numpy.array([
        #                         11.11183, 11.34227, 10.05334])},
        #                 "efficient": {
        #                     "2009": numpy.array([0, 0, 0]),
        #                     "2010": numpy.array([0, 0, 0])}}},
        #         "energy": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         44.22496, 45.15310, 40.20271]),
        #                     "2010": numpy.array([
        #                         44.22496, 45.15310, 40.20271])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         33.16872, 33.86483, 30.15203]),
        #                     "2010": numpy.array([
        #                         33.16872, 33.86483, 30.15203])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         22.11248, 22.57655, 20.10135]),
        #                     "2010": numpy.array([
        #                         22.11248, 22.57655, 20.10135])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         11.05624, 11.28828, 10.05068]),
        #                     "2010": numpy.array([
        #                         11.05624, 11.28828, 10.05068])}}},
        #         "carbon": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         66.33744, 67.72965, 60.30406]),
        #                     "2010": numpy.array([
        #                         66.33744, 67.72965, 60.30406])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         44.22496, 45.15310, 40.20271]),
        #                     "2010": numpy.array([
        #                         44.22496, 45.15310, 40.20271])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": numpy.array([
        #                         33.16872, 33.86483, 30.15203]),
        #                     "2010": numpy.array([
        #                         33.16872, 33.86483, 30.15203])},
        #                 "efficient": {
        #                     "2009": numpy.array([
        #                         11.05624, 11.28828, 10.05068]),
        #                     "2010": numpy.array([
        #                         11.05624, 11.28828, 10.05068])}}}},
        #     "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                  "measure": {"2009": 1, "2010": 1}}}]

    def test_compete_res(self):
        """Test outcomes given valid sample measures w/ point value inputs."""
        # Run the measure competition routine on sample demand-side measures
        self.a_run.compete_res_primary(
            self.measures_demand, self.adjust_key1, self.test_adopt_scheme)
        # Remove any market overlaps across the supply and demand sides of
        # heating and cooling
        self.a_run.htcl_adj(
            self.measures_demand, self.adjust_key1, self.test_adopt_scheme)
        # Run the measure competition routine on sample supply-side measures
        self.a_run.compete_res_primary(
            self.measures_supply, self.adjust_key2, self.test_adopt_scheme)
        # Remove any market overlaps across the supply and demand sides of
        # heating and cooling
        self.a_run.htcl_adj(
            self.measures_supply, self.adjust_key2, self.test_adopt_scheme)

        # Check updated competed master microsegments for each sample measure
        # following competition/supply-demand overlap adjustments
        for ind, d in enumerate(self.a_run.measures):
            self.dict_check(
                self.measures_master_msegs_out[ind],
                self.a_run.measures[ind].markets[self.test_adopt_scheme][
                    "competed"]["master_mseg"])

    # def test_compete_res_dist(self):
    #     """Test outcomes given valid sample measures w/ some array inputs."""
    #     # Run the measure competition routine on sample demand-side measures
    #     self.a_run_dist.compete_res_primary(
    #         self.measures_demand_dist, self.adjust_key1, self.test_adopt_scheme)
    #     # Record any demand-side savings overlaps with sample supply-side
    #     # measures
    #     self.a_run.htcl_adj_rec(
    #         self.measures_demand_dist, self.measures_overlap1_dist,
    #         self.adjust_key1, self.test_adopt_scheme)
    #     # Run the measure competition routine on sample supply-side measures
    #     self.a_run_dist.compete_res_primary(
    #         self.measures_supply_dist, self.adjust_key2, self.test_adopt_scheme)
    #     # Record any supply-side savings overlaps with sample demand-side
    #     # measures
    #     self.a_run.htcl_adj_rec(
    #         self.measures_supply_dist, self.measures_overlap2_dist,
    #         self.adjust_key2, self.test_adopt_scheme)
    #     # Remove any market overlaps across the supply and demand sides of
    #     # heating and cooling
    #     meas_overlap_adj = [x for x in self.a_run_dist.measures if len(
    #         x.markets[self.test_adopt_scheme]["competed"]["mseg_adjust"][
    #             "supply-demand adjustment"]["savings"].keys()) > 0]
    #     self.a_run_dist.htcl_adj(
    #         meas_overlap_adj, self.test_adopt_scheme)
    #     # Check updated competed master microsegments for each sample measure
    #     # following competition/supply-demand overlap adjustments
    #     for ind, d in enumerate(self.a_run_dist.measures):
    #         self.dict_check(
    #             self.measures_master_msegs_out_dist[ind],
    #             self.a_run_dist.measures[ind].markets[self.test_adopt_scheme][
    #                 "competed"]["master_mseg"])


class ComCompeteTest(unittest.TestCase, CommonMethods):
    """Test 'compete_com_primary' and 'secondary_adj' functions.

    Verify that 'compete_com_primary' correctly calculates primary market
    shares and updates master microsegments for a series of competing
    commercial measures; and that 'secondary_adj' correctly adjusts any
    secondary markets associated with these primary market microsegments.


    Attributes:
        handyvars (object): Useful variables across the class.
        test_adopt_scheme (string): Sample consumer adoption scheme.
        overlap_key (string): First sample string for competed primary market
            microsegment key chain being tested.
        overlap_key_scnd (string): Second sample string for secondary market
            microsegment key chain being tested.
        secnd_adj_key (string): Key used to link primary and secondary market
            microsegments (by climate, building type, structure type).
        compete_meas1 (dict): Sample commercial supply-side lighting measure 1.
        compete_meas2 (dict): Sample commercial supply-side lighting measure 2.
        compete_meas3 (dict): Sample commercial supply-side lighting measure 3.
        compete_meas_dist (dict): Alternative version of sample commercial
            supply-side lighting measure 1 including lists stock cost input
            values instead of point values.
        measures_all (list): List of all competing measures with point
            value inputs.
        measures_secondary (list): Subset of 'measures_all' with secondary
            microsegments to adjust.
        a_run (object): Analysis engine object incorporating all
            'measures_primary' objects.
        measures_all_dist (list): List of competing measures including
            some measures with array inputs.
        measures_secondary_dist (list): Subset of 'measures_all_dist' with
            secondary microsegments to adjust.
        a_run_dist (object): Analysis engine object incorporating all
            'measures_primary_dist' objects.
        measures_overlap (dict): List of supply-side Measure objects and
            associated contributing microsegment keys that overlap with
            'measures_demand' Measure objects.
        measure_master_msegs_out (dict): Master market microsegments
            that should be generated for each Measure object in 'measures_all'
            following competition and supply-demand overlap adjustments.
        measure_master_msegs_out_dist (dict): Master market microsegments
            that should be generated for each Measure object in
            'measures_all_dist' following competition and supply-demand overlap
            adjustments.
    """

    @classmethod
    def setUpClass(cls):
        """Define objects/variables for use across all class functions."""
        cls.handyvars = run.UsefulVars()
        cls.handyvars.aeo_years = ["2009", "2010"]
        cls.test_adopt_scheme = "Max adoption potential"
        cls.overlap_key = str(
            ('primary', 'AIA_CZ1', 'assembly', 'electricity (grid)',
             'lighting', 'reflector (LED)', 'existing'))
        cls.overlap_key_scnd = str(
            ('secondary', 'AIA_CZ1', 'assembly', 'electricity (grid)',
             'cooling', 'demand', 'lighting gain', 'existing'))
        cls.secnd_adj_key = str(('AIA_CZ1', 'assembly', 'existing'))
        cls.compete_meas1 = {
            "name": "sample compete measure c1",
            "climate_zone": ["AIA_CZ1"],
            "bldg_type": ["assembly"],
            "end_use": {
                "primary": ["lighting"],
                "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "yrs_on_mkt": ["2009", "2010"],
            "markets": {
                "Technical potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 20, "2010": 20},
                                "measure": {"2009": 20, "2010": 20}},
                            "competed": {
                                "all": {"2009": 10, "2010": 10},
                                "measure": {"2009": 10, "2010": 10}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 40, "2010": 40},
                                "efficient": {"2009": 30, "2010": 30}},
                            "competed": {
                                "baseline": {"2009": 20, "2010": 20},
                                "efficient": {"2009": 10, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 40, "2010": 40}},
                            "competed": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 10, "2010": 10}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 30, "2010": 30}},
                                "competed": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 10, "2010": 10}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 40, "2010": 40}},
                                "competed": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 10, "2010": 10}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.overlap_key: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                            str(('primary', 'AIA_CZ2', 'single family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                        "competed choice parameters": {
                            cls.overlap_key: {
                                "rate distribution": {
                                    "2009": [
                                        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4],
                                    "2010": [
                                        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4]}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "original energy (competed and captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "adjusted energy (total captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "adjusted energy (competed and captured)": {
                                    cls.secnd_adj_key: {
                                        "2009": 0, "2010": 0}}}}},
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 20, "2010": 20},
                                "measure": {"2009": 20, "2010": 20}},
                            "competed": {
                                "all": {"2009": 10, "2010": 10},
                                "measure": {"2009": 10, "2010": 10}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 40, "2010": 40},
                                "efficient": {"2009": 30, "2010": 30}},
                            "competed": {
                                "baseline": {"2009": 20, "2010": 20},
                                "efficient": {"2009": 10, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 40, "2010": 40}},
                            "competed": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 10, "2010": 10}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 10, "2010": 10}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 30, "2010": 30}},
                                "competed": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 10, "2010": 10}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 40, "2010": 40}},
                                "competed": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 10, "2010": 10}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.overlap_key: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                            str(('primary', 'AIA_CZ2', 'single family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                        "competed choice parameters": {
                            cls.overlap_key: {
                                "rate distribution": {
                                    "2009": [
                                        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4],
                                    "2010": [
                                        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4]}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "original energy (competed and captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "adjusted energy (total captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "adjusted energy (competed and captured)": {
                                    cls.secnd_adj_key: {
                                        "2009": 0, "2010": 0}}}}},
                    "mseg_out_break": {}}}}
        cls.compete_meas2 = {
            "name": "sample compete measure c2",
            "climate_zone": ["AIA_CZ1"],
            "bldg_type": ["assembly"],
            "end_use": {
                "primary": ["lighting"],
                "secondary": ["heating", "secondary heating", "cooling"]},
            "market_entry_year": 2010,
            "market_exit_year": None,
            "yrs_on_mkt": ["2010"],
            "markets": {
                "Technical potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 20, "2010": 20},
                                "measure": {"2009": 0, "2010": 20}},
                            "competed": {
                                "all": {"2009": 10, "2010": 10},
                                "measure": {"2009": 0, "2010": 10}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 40, "2010": 40},
                                "efficient": {"2009": 40, "2010": 30}},
                            "competed": {
                                "baseline": {"2009": 20, "2010": 20},
                                "efficient": {"2009": 20, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 60, "2010": 40}},
                            "competed": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 30, "2010": 10}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 20, "2010": 10}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 10, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 40, "2010": 30}},
                                "competed": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 20, "2010": 10}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 60, "2010": 40}},
                                "competed": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 30, "2010": 10}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.overlap_key: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 0, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 0, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 20, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 10, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 30, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 15, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 0, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 20, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 10, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 30, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 15, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                            cls.overlap_key_scnd: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 20, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 10, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 30, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 15, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 10, "2010": 10}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 20, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 10, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 30, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 15, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                        "competed choice parameters": {
                            cls.overlap_key: {
                                "rate distribution": {
                                    "2009": [
                                        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4],
                                    "2010": [
                                        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4]}},
                            cls.overlap_key_scnd: {
                                "rate distribution": {}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "original energy (competed and captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "adjusted energy (total captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "adjusted energy (competed and captured)": {
                                    cls.secnd_adj_key: {
                                        "2009": 0, "2010": 0}}}}},
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 20, "2010": 20},
                                "measure": {"2009": 0, "2010": 20}},
                            "competed": {
                                "all": {"2009": 10, "2010": 10},
                                "measure": {"2009": 0, "2010": 10}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 40, "2010": 40},
                                "efficient": {"2009": 40, "2010": 30}},
                            "competed": {
                                "baseline": {"2009": 20, "2010": 20},
                                "efficient": {"2009": 20, "2010": 10}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 60, "2010": 40}},
                            "competed": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 30, "2010": 10}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 20, "2010": 10}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 10, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 40, "2010": 30}},
                                "competed": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 20, "2010": 10}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 60, "2010": 40}},
                                "competed": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 30, "2010": 10}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.overlap_key: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 0, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 0, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 20, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 10, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 30, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 15, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 0, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 20, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 10, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 30, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 15, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                            cls.overlap_key_scnd: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 20, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 10, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 30, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 15, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 10, "2010": 10}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 20, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 10, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 30, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 15, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                        "competed choice parameters": {
                            cls.overlap_key: {
                                "rate distribution": {
                                    "2009": [
                                        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4],
                                    "2010": [
                                        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4]}},
                            cls.overlap_key_scnd: {
                                "rate distribution": {}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "original energy (competed and captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "adjusted energy (total captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "adjusted energy (competed and captured)": {
                                    cls.secnd_adj_key: {
                                        "2009": 0, "2010": 0}}}}},
                    "mseg_out_break": {}}}}
        # cls.compete_meas2_dist = {
        #     "name": "sample compete measure c2 dist",
        #     "climate_zone": ["AIA_CZ1"],
        #     "bldg_type": ["assembly"],
        #     "end_use": {
        #         "primary": ["lighting"],
        #         "secondary": ["heating", "secondary heating", "cooling"]},
        #     "market_entry_year": 2010,
        #     "market_exit_year": None,
        #     "yrs_on_mkt": ["2010"],
        #     "markets": {
        #         "Technical potential": {
        #             "master_mseg": {
        #                 "stock": {
        #                     "total": {
        #                         "all": {"2009": 20, "2010": 20},
        #                         "measure": {"2009": 0, "2010": 20}},
        #                     "competed": {
        #                         "all": {"2009": 10, "2010": 10},
        #                         "measure": {"2009": 0, "2010": 10}}},
        #                 "energy": {
        #                     "total": {
        #                         "baseline": {"2009": 40, "2010": 40},
        #                         "efficient": {"2009": 40, "2010": 30}},
        #                     "competed": {
        #                         "baseline": {"2009": 20, "2010": 20},
        #                         "efficient": {"2009": 20, "2010": 10}}},
        #                 "carbon": {
        #                     "total": {
        #                         "baseline": {"2009": 60, "2010": 60},
        #                         "efficient": {"2009": 60, "2010": 40}},
        #                     "competed": {
        #                         "baseline": {"2009": 30, "2010": 30},
        #                         "efficient": {"2009": 30, "2010": 10}}},
        #                 "cost": {
        #                     "stock": {
        #                         "total": {
        #                             "baseline": {"2009": 20, "2010": 20},
        #                             "efficient": {
        #                                 "2009": 20,
        #                                 "2010": numpy.array([10, 12, 14])}},
        #                         "competed": {
        #                             "baseline": {"2009": 10, "2010": 10},
        #                             "efficient": {
        #                                 "2009": 10,
        #                                 "2010": numpy.array([0, 2, 4])}}},
        #                     "energy": {
        #                         "total": {
        #                             "baseline": {"2009": 40, "2010": 40},
        #                             "efficient": {"2009": 40, "2010": 30}},
        #                         "competed": {
        #                             "baseline": {"2009": 20, "2010": 20},
        #                             "efficient": {"2009": 20, "2010": 10}}},
        #                     "carbon": {
        #                         "total": {
        #                             "baseline": {"2009": 60, "2010": 60},
        #                             "efficient": {"2009": 60, "2010": 40}},
        #                         "competed": {
        #                             "baseline": {"2009": 30, "2010": 30},
        #                             "efficient": {"2009": 30, "2010": 10}}}},
        #                 "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                              "measure": {"2009": 1, "2010": 1}}},
        #             "mseg_adjust": {
        #                 "contributing mseg keys and values": {
        #                     cls.overlap_key: {
        #                         "stock": {
        #                             "total": {
        #                                 "all": {"2009": 10, "2010": 10},
        #                                 "measure": {"2009": 0, "2010": 10}},
        #                             "competed": {
        #                                 "all": {"2009": 5, "2010": 5},
        #                                 "measure": {"2009": 0, "2010": 5}}},
        #                         "energy": {
        #                             "total": {
        #                                 "baseline": {"2009": 20, "2010": 20},
        #                                 "efficient": {"2009": 20, "2010": 15}},
        #                             "competed": {
        #                                 "baseline": {"2009": 10, "2010": 10},
        #                                 "efficient": {"2009": 10, "2010": 5}}},
        #                         "carbon": {
        #                             "total": {
        #                                 "baseline": {"2009": 30, "2010": 30},
        #                                 "efficient": {"2009": 30, "2010": 20}},
        #                             "competed": {
        #                                 "baseline": {"2009": 15, "2010": 15},
        #                                 "efficient": {"2009": 15, "2010": 5}}},
        #                         "cost": {
        #                             "stock": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": 0,
        #                                         "2010": numpy.array(
        #                                             [5, 6, 7])}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 5, "2010": 5},
        #                                     "efficient": {
        #                                         "2009": 0,
        #                                         "2010": numpy.array(
        #                                             [0, 1, 2])}}},
        #                             "energy": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 20, "2010": 20},
        #                                     "efficient": {
        #                                         "2009": 20, "2010": 15}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": 10, "2010": 5}}},
        #                             "carbon": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 30, "2010": 30},
        #                                     "efficient": {
        #                                         "2009": 30, "2010": 20}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 15, "2010": 15},
        #                                     "efficient": {
        #                                         "2009": 15, "2010": 5}}}},
        #                         "lifetime": {
        #                             "baseline": {"2009": 1, "2010": 1},
        #                             "measure": {"2009": 1, "2010": 1}}},
        #                     cls.overlap_key_scnd: {
        #                         "stock": {
        #                             "total": {
        #                                 "all": {"2009": 10, "2010": 10},
        #                                 "measure": {"2009": 0, "2010": 10}},
        #                             "competed": {
        #                                 "all": {"2009": 5, "2010": 5},
        #                                 "measure": {"2009": 0, "2010": 5}}},
        #                         "energy": {
        #                             "total": {
        #                                 "baseline": {"2009": 20, "2010": 20},
        #                                 "efficient": {"2009": 20, "2010": 15}},
        #                             "competed": {
        #                                 "baseline": {"2009": 10, "2010": 10},
        #                                 "efficient": {"2009": 10, "2010": 5}}},
        #                         "carbon": {
        #                             "total": {
        #                                 "baseline": {"2009": 30, "2010": 30},
        #                                 "efficient": {"2009": 30, "2010": 20}},
        #                             "competed": {
        #                                 "baseline": {"2009": 15, "2010": 15},
        #                                 "efficient": {"2009": 15, "2010": 5}}},
        #                         "cost": {
        #                             "stock": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": 10,
        #                                         "2010": numpy.array(
        #                                             [5, 6, 7])}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 5, "2010": 5},
        #                                     "efficient": {
        #                                         "2009": 5,
        #                                         "2010": numpy.array([
        #                                             0, 1, 2])}}},
        #                             "energy": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 20, "2010": 20},
        #                                     "efficient": {
        #                                         "2009": 20, "2010": 15}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": 10, "2010": 5}}},
        #                             "carbon": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 30, "2010": 30},
        #                                     "efficient": {
        #                                         "2009": 30, "2010": 20}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 15, "2010": 15},
        #                                     "efficient": {
        #                                         "2009": 15, "2010": 5}}}},
        #                         "lifetime": {
        #                             "baseline": {"2009": 1, "2010": 1},
        #                             "measure": {"2009": 1, "2010": 1}}}},
        #                 "competed choice parameters": {
        #                     cls.overlap_key: {
        #                         "rate distribution": {
        #                             "2009": [
        #                                 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4],
        #                             "2010": [
        #                                 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4]}},
        #                     cls.overlap_key_scnd: {
        #                         "rate distribution": {}}},
        #                 "secondary mseg adjustments": {
        #                     "market share": {
        #                         "original energy (total captured)": {
        #                             cls.secnd_adj_key: {"2009": 0, "2010": 0}},
        #                         "original energy (competed and captured)": {
        #                             cls.secnd_adj_key: {"2009": 0, "2010": 0}},
        #                         "adjusted energy (total captured)": {
        #                             cls.secnd_adj_key: {"2009": 0, "2010": 0}},
        #                         "adjusted energy (competed and captured)": {
        #                             cls.secnd_adj_key: {
        #                                 "2009": 0, "2010": 0}}}},
        #                 "supply-demand adjustment": {
        #                     "savings": {},
        #                     "total": {}}},
        #             "mseg_out_break": {}},
        #         "Max adoption potential": {
        #             "master_mseg": {
        #                 "stock": {
        #                     "total": {
        #                         "all": {"2009": 20, "2010": 20},
        #                         "measure": {"2009": 0, "2010": 20}},
        #                     "competed": {
        #                         "all": {"2009": 10, "2010": 10},
        #                         "measure": {"2009": 0, "2010": 10}}},
        #                 "energy": {
        #                     "total": {
        #                         "baseline": {"2009": 40, "2010": 40},
        #                         "efficient": {"2009": 40, "2010": 30}},
        #                     "competed": {
        #                         "baseline": {"2009": 20, "2010": 20},
        #                         "efficient": {"2009": 20, "2010": 10}}},
        #                 "carbon": {
        #                     "total": {
        #                         "baseline": {"2009": 60, "2010": 60},
        #                         "efficient": {"2009": 60, "2010": 40}},
        #                     "competed": {
        #                         "baseline": {"2009": 30, "2010": 30},
        #                         "efficient": {"2009": 30, "2010": 10}}},
        #                 "cost": {
        #                     "stock": {
        #                         "total": {
        #                             "baseline": {"2009": 20, "2010": 20},
        #                             "efficient": {
        #                                 "2009": 20,
        #                                 "2010": numpy.array([10, 12, 14])}},
        #                         "competed": {
        #                             "baseline": {"2009": 10, "2010": 10},
        #                             "efficient": {
        #                                 "2009": 10,
        #                                 "2010": numpy.array([0, 2, 4])}}},
        #                     "energy": {
        #                         "total": {
        #                             "baseline": {"2009": 40, "2010": 40},
        #                             "efficient": {"2009": 40, "2010": 30}},
        #                         "competed": {
        #                             "baseline": {"2009": 20, "2010": 20},
        #                             "efficient": {"2009": 20, "2010": 10}}},
        #                     "carbon": {
        #                         "total": {
        #                             "baseline": {"2009": 60, "2010": 60},
        #                             "efficient": {"2009": 60, "2010": 40}},
        #                         "competed": {
        #                             "baseline": {"2009": 30, "2010": 30},
        #                             "efficient": {"2009": 30, "2010": 10}}}},
        #                 "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                              "measure": {"2009": 1, "2010": 1}}},
        #             "mseg_adjust": {
        #                 "contributing mseg keys and values": {
        #                     cls.overlap_key: {
        #                         "stock": {
        #                             "total": {
        #                                 "all": {"2009": 10, "2010": 10},
        #                                 "measure": {"2009": 0, "2010": 10}},
        #                             "competed": {
        #                                 "all": {"2009": 5, "2010": 5},
        #                                 "measure": {"2009": 0, "2010": 5}}},
        #                         "energy": {
        #                             "total": {
        #                                 "baseline": {"2009": 20, "2010": 20},
        #                                 "efficient": {"2009": 20, "2010": 15}},
        #                             "competed": {
        #                                 "baseline": {"2009": 10, "2010": 10},
        #                                 "efficient": {"2009": 10, "2010": 5}}},
        #                         "carbon": {
        #                             "total": {
        #                                 "baseline": {"2009": 30, "2010": 30},
        #                                 "efficient": {"2009": 30, "2010": 20}},
        #                             "competed": {
        #                                 "baseline": {"2009": 15, "2010": 15},
        #                                 "efficient": {"2009": 15, "2010": 5}}},
        #                         "cost": {
        #                             "stock": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": 0,
        #                                         "2010": numpy.array(
        #                                             [5, 6, 7])}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 5, "2010": 5},
        #                                     "efficient": {
        #                                         "2009": 0,
        #                                         "2010": numpy.array(
        #                                             [0, 1, 2])}}},
        #                             "energy": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 20, "2010": 20},
        #                                     "efficient": {
        #                                         "2009": 20, "2010": 15}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": 10, "2010": 5}}},
        #                             "carbon": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 30, "2010": 30},
        #                                     "efficient": {
        #                                         "2009": 30, "2010": 20}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 15, "2010": 15},
        #                                     "efficient": {
        #                                         "2009": 15, "2010": 5}}}},
        #                         "lifetime": {
        #                             "baseline": {"2009": 1, "2010": 1},
        #                             "measure": {"2009": 1, "2010": 1}}},
        #                     cls.overlap_key_scnd: {
        #                         "stock": {
        #                             "total": {
        #                                 "all": {"2009": 10, "2010": 10},
        #                                 "measure": {"2009": 0, "2010": 10}},
        #                             "competed": {
        #                                 "all": {"2009": 5, "2010": 5},
        #                                 "measure": {"2009": 0, "2010": 5}}},
        #                         "energy": {
        #                             "total": {
        #                                 "baseline": {"2009": 20, "2010": 20},
        #                                 "efficient": {"2009": 20, "2010": 15}},
        #                             "competed": {
        #                                 "baseline": {"2009": 10, "2010": 10},
        #                                 "efficient": {"2009": 10, "2010": 5}}},
        #                         "carbon": {
        #                             "total": {
        #                                 "baseline": {"2009": 30, "2010": 30},
        #                                 "efficient": {"2009": 30, "2010": 20}},
        #                             "competed": {
        #                                 "baseline": {"2009": 15, "2010": 15},
        #                                 "efficient": {"2009": 15, "2010": 5}}},
        #                         "cost": {
        #                             "stock": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": 10,
        #                                         "2010": numpy.array(
        #                                             [5, 6, 7])}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 5, "2010": 5},
        #                                     "efficient": {
        #                                         "2009": 5,
        #                                         "2010": numpy.array([
        #                                             0, 1, 2])}}},
        #                             "energy": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 20, "2010": 20},
        #                                     "efficient": {
        #                                         "2009": 20, "2010": 15}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 10, "2010": 10},
        #                                     "efficient": {
        #                                         "2009": 10, "2010": 5}}},
        #                             "carbon": {
        #                                 "total": {
        #                                     "baseline": {
        #                                         "2009": 30, "2010": 30},
        #                                     "efficient": {
        #                                         "2009": 30, "2010": 20}},
        #                                 "competed": {
        #                                     "baseline": {
        #                                         "2009": 15, "2010": 15},
        #                                     "efficient": {
        #                                         "2009": 15, "2010": 5}}}},
        #                         "lifetime": {
        #                             "baseline": {"2009": 1, "2010": 1},
        #                             "measure": {"2009": 1, "2010": 1}}}},
        #                 "competed choice parameters": {
        #                     cls.overlap_key: {
        #                         "rate distribution": {
        #                             "2009": [
        #                                 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4],
        #                             "2010": [
        #                                 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4]}},
        #                     cls.overlap_key_scnd: {
        #                         "rate distribution": {}}},
        #                 "secondary mseg adjustments": {
        #                     "market share": {
        #                         "original energy (total captured)": {
        #                             cls.secnd_adj_key: {"2009": 0, "2010": 0}},
        #                         "original energy (competed and captured)": {
        #                             cls.secnd_adj_key: {"2009": 0, "2010": 0}},
        #                         "adjusted energy (total captured)": {
        #                             cls.secnd_adj_key: {"2009": 0, "2010": 0}},
        #                         "adjusted energy (competed and captured)": {
        #                             cls.secnd_adj_key: {
        #                                 "2009": 0, "2010": 0}}}},
        #                 "supply-demand adjustment": {
        #                     "savings": {},
        #                     "total": {}}},
        #             "mseg_out_break": {}}}}
        cls.compete_meas3 = {
            "name": "sample compete measure c3",
            "climate_zone": ["AIA_CZ1"],
            "bldg_type": ["assembly"],
            "end_use": {
                "primary": ["lighting"],
                "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "yrs_on_mkt": ["2009", "2010"],
            "markets": {
                "Technical potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 30, "2010": 30},
                                "measure": {"2009": 30, "2010": 30}},
                            "competed": {
                                "all": {"2009": 15, "2010": 15},
                                "measure": {"2009": 15, "2010": 15}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 45, "2010": 45}},
                            "competed": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 15, "2010": 15}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 90, "2010": 90},
                                "efficient": {"2009": 60, "2010": 60}},
                            "competed": {
                                "baseline": {"2009": 45, "2010": 45},
                                "efficient": {"2009": 15, "2010": 15}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 15, "2010": 15}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 45, "2010": 45}},
                                "competed": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 15, "2010": 15}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 90, "2010": 90},
                                    "efficient": {"2009": 60, "2010": 60}},
                                "competed": {
                                    "baseline": {"2009": 45, "2010": 45},
                                    "efficient": {"2009": 15, "2010": 15}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.overlap_key: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                            str(('primary', 'AIA_CZ2', 'single family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                            str(('primary', 'AIA_CZ2', 'multi family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                        "competed choice parameters": {
                            cls.overlap_key: {
                                "rate distribution": {
                                    "2009": [
                                        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4],
                                    "2010": [
                                        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4]}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "original energy (competed and captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "adjusted energy (total captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "adjusted energy (competed and captured)": {
                                    cls.secnd_adj_key: {
                                        "2009": 0, "2010": 0}}}}},
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 30, "2010": 30},
                                "measure": {"2009": 30, "2010": 30}},
                            "competed": {
                                "all": {"2009": 15, "2010": 15},
                                "measure": {"2009": 15, "2010": 15}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 45, "2010": 45}},
                            "competed": {
                                "baseline": {"2009": 30, "2010": 30},
                                "efficient": {"2009": 15, "2010": 15}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 90, "2010": 90},
                                "efficient": {"2009": 60, "2010": 60}},
                            "competed": {
                                "baseline": {"2009": 45, "2010": 45},
                                "efficient": {"2009": 15, "2010": 15}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 15, "2010": 15}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 0, "2010": 0}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 45, "2010": 45}},
                                "competed": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 15, "2010": 15}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 90, "2010": 90},
                                    "efficient": {"2009": 60, "2010": 60}},
                                "competed": {
                                    "baseline": {"2009": 45, "2010": 45},
                                    "efficient": {"2009": 15, "2010": 15}}}},
                        "lifetime": {"baseline": {"2009": 1, "2010": 1},
                                     "measure": {"2009": 1, "2010": 1}}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            cls.overlap_key: {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}}},
                            str(('primary', 'AIA_CZ2', 'single family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                            str(('primary', 'AIA_CZ2', 'multi family home',
                                 'electricity (grid)', 'lighting',
                                 'reflector (LED)')): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 10, "2010": 10}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 5, "2010": 5}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 15, "2010": 15}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 20, "2010": 20}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 5, "2010": 5}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 5, "2010": 5},
                                            "efficient": {
                                                "2009": 0, "2010": 0}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 15, "2010": 15}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 20, "2010": 20}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 5, "2010": 5}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": {"2009": 1, "2010": 1}}},
                        "competed choice parameters": {
                            cls.overlap_key: {
                                "rate distribution": {
                                    "2009": [
                                        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4],
                                    "2010": [
                                        0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.4]}}},
                        "secondary mseg adjustments": {
                            "market share": {
                                "original energy (total captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "original energy (competed and captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "adjusted energy (total captured)": {
                                    cls.secnd_adj_key: {"2009": 0, "2010": 0}},
                                "adjusted energy (competed and captured)": {
                                    cls.secnd_adj_key: {
                                        "2009": 0, "2010": 0}}}}},
                    "mseg_out_break": {}}}}
        cls.measures_all = [run.Measure(
            cls.handyvars, **x) for x in [
            copy.deepcopy(cls.compete_meas1), cls.compete_meas2,
            copy.deepcopy(cls.compete_meas3)]]
        cls.measures_secondary = [cls.measures_all[1]]
        # Instantiate engine object based on above measures
        cls.a_run = run.Engine(cls.handyvars, cls.measures_all)
        # Set information needed to finalize array test measure consumer
        # metrics
        consumer_metrics = [{
            "stock cost": {
                "residential": {
                    "2009": None, "2010": None},
                "commercial": {
                    "2009": {
                        "rate 1": 100, "rate 2": 110,
                        "rate 3": 120, "rate 4": 130,
                        "rate 5": 140, "rate 6": 150,
                        "rate 7": 160},
                    "2010": {
                        "rate 1": 100, "rate 2": 110,
                        "rate 3": 120, "rate 4": 130,
                        "rate 5": 140, "rate 6": 150,
                        "rate 7": 160}}},
            "energy cost": {
                "residential": {
                    "2009": None, "2010": None},
                "commercial": {
                    "2009": {
                        "rate 1": -350, "rate 2": -60,
                        "rate 3": -70, "rate 4": -380,
                        "rate 5": -390, "rate 6": -150,
                        "rate 7": -400},
                    "2010": {
                        "rate 1": -350, "rate 2": -60,
                        "rate 3": -70, "rate 4": -380,
                        "rate 5": -390, "rate 6": -150,
                        "rate 7": -400}}},
            "carbon cost": {
                "residential": {
                    "2009": None, "2010": None},
                "commercial": {
                    "2009": {
                        "rate 1": -40, "rate 2": -50,
                        "rate 3": -55, "rate 4": -60,
                        "rate 5": -65, "rate 6": -70,
                        "rate 7": -75},
                    "2010": {
                        "rate 1": -40, "rate 2": -50,
                        "rate 3": -55, "rate 4": -60,
                        "rate 5": -65, "rate 6": -70,
                        "rate 7": -75}}}},
            {
            "stock cost": {
                "residential": {
                    "2009": None, "2010": None},
                "commercial": {
                    "2009": {
                        "rate 1": 85, "rate 2": 90, "rate 3": 95,
                        "rate 4": 100, "rate 5": 105,
                        "rate 6": 110, "rate 7": 115},
                    "2010": {
                        "rate 1": 85, "rate 2": 90, "rate 3": 95,
                        "rate 4": 100, "rate 5": 105,
                        "rate 6": 110, "rate 7": 115}}},
            "energy cost": {
                "residential": {
                    "2009": None, "2010": None},
                "commercial": {
                    "2009": {
                        "rate 1": -435, "rate 2": -440,
                        "rate 3": -145,
                        "rate 4": -150, "rate 5": -155,
                        "rate 6": -160,
                        "rate 7": -370},
                    "2010": {
                        "rate 1": -435, "rate 2": -440,
                        "rate 3": -145,
                        "rate 4": -150, "rate 5": -155,
                        "rate 6": -160,
                        "rate 7": -370}}},
            "carbon cost": {
                "residential": {
                    "2009": None, "2010": None},
                "commercial": {
                    "2009": {
                        "rate 1": -135, "rate 2": -140,
                        "rate 3": -145,
                        "rate 4": -150, "rate 5": -155,
                        "rate 6": -160,
                        "rate 7": -170},
                    "2010": {
                        "rate 1": -135, "rate 2": -140,
                        "rate 3": -145,
                        "rate 4": -150, "rate 5": -155,
                        "rate 6": -160,
                        "rate 7": -170}}}},
            {
            "stock cost": {
                "residential": {
                    "2009": None, "2010": None},
                "commercial": {
                    "2009": {
                        "rate 1": 50, "rate 2": 60, "rate 3": 70,
                        "rate 4": 80, "rate 5": 90, "rate 6": 100,
                        "rate 7": 110},
                    "2010": {
                        "rate 1": 50, "rate 2": 60, "rate 3": 70,
                        "rate 4": 80, "rate 5": 90, "rate 6": 100,
                        "rate 7": 110}}},
            "energy cost": {
                "residential": {
                    "2009": None, "2010": None},
                "commercial": {
                    "2009": {
                        "rate 1": -190, "rate 2": -195,
                        "rate 3": -190,
                        "rate 4": -205, "rate 5": -180,
                        "rate 6": -230,
                        "rate 7": -200},
                    "2010": {
                        "rate 1": -190, "rate 2": -195,
                        "rate 3": -190,
                        "rate 4": -205, "rate 5": -180,
                        "rate 6": -230,
                        "rate 7": -200}}},
            "carbon cost":
                {
                "residential": {
                    "2009": None, "2010": None},
                "commercial": {
                    "2009": {
                        "rate 1": -90, "rate 2": -95,
                        "rate 3": -100,
                        "rate 4": -105, "rate 5": -110,
                        "rate 6": -115,
                        "rate 7": -120},
                    "2010": {
                        "rate 1": -90, "rate 2": -95,
                        "rate 3": -100,
                        "rate 4": -105, "rate 5": -110,
                        "rate 6": -115,
                        "rate 7": -120}}}}]
        # Adjust/finalize point value test measure consumer metrics
        for ind, m in enumerate(cls.a_run.measures):
            m.consumer_metrics['anpv'] = consumer_metrics[ind]
        # cls.measures_all_dist = [run.Measure(
        #     cls.handyvars, **x) for x in [
        #     copy.deepcopy(cls.compete_meas1),
        #     cls.compete_meas2_dist,
        #     copy.deepcopy(cls.compete_meas3)]]
        # cls.measures_secondary_dist = [cls.measures_all_dist[1]]
        # cls.a_run_dist = run.Engine(cls.handyvars, cls.measures_all_dist)
        # Set information needed to finalize array test measure consumer
        # metrics
        # consumer_metrics_dist = [{
        #     "stock cost": {
        #         "2009": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": 100, "rate 2": 110,
        #                 "rate 3": 120, "rate 4": 130,
        #                 "rate 5": 140, "rate 6": 150,
        #                 "rate 7": 160}},
        #         "2010": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": 100, "rate 2": 110,
        #                 "rate 3": 120, "rate 4": 130,
        #                 "rate 5": 140, "rate 6": 150,
        #                 "rate 7": 160}}},
        #     "energy cost": {
        #         "2009": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": -350, "rate 2": -60,
        #                 "rate 3": -70, "rate 4": -380,
        #                 "rate 5": -390, "rate 6": -150,
        #                 "rate 7": -400}},
        #         "2010": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": -350, "rate 2": -60,
        #                 "rate 3": -70, "rate 4": -380,
        #                 "rate 5": -390, "rate 6": -150,
        #                 "rate 7": -400}}},
        #     "carbon cost": {
        #         "2009": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": -40, "rate 2": -50,
        #                 "rate 3": -55, "rate 4": -60,
        #                 "rate 5": -65, "rate 6": -70,
        #                 "rate 7": -75}},
        #         "2010": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": -40, "rate 2": -50,
        #                 "rate 3": -55, "rate 4": -60,
        #                 "rate 5": -65, "rate 6": -70,
        #                 "rate 7": -75}}}},
        #     {
        #     "stock cost": {
        #         "2009": {
        #             "residential": 999,
        #             "commercial": 999},
        #         "2010": numpy.array(
        #             [{"residential": None,
        #               "commercial": {
        #                   "rate 1": 85, "rate 2": 90, "rate 3": 95,
        #                   "rate 4": 100, "rate 5": 105,
        #                   "rate 6": 110, "rate 7": 115}},
        #              {"residential": None,
        #               "commercial": {
        #                   "rate 1": 205, "rate 2": 100, "rate 3": 105,
        #                   "rate 4": 110, "rate 5": 115,
        #                   "rate 6": 120, "rate 7": 125}},
        #              {"residential": None,
        #               "commercial": {
        #                   "rate 1": 105, "rate 2": 110, "rate 3": 115,
        #                   "rate 4": 120, "rate 5": 125,
        #                   "rate 6": 10, "rate 7": 135}}])},
        #     "energy cost": {
        #         "2009": {
        #             "residential": 999,
        #             "commercial": 999},
        #         "2010": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": -435, "rate 2": -440,
        #                 "rate 3": -145,
        #                 "rate 4": -150, "rate 5": -155,
        #                 "rate 6": -160,
        #                 "rate 7": -370}}},
        #     "carbon cost": {
        #         "2009": {
        #             "residential": 999,
        #             "commercial": 999},
        #         "2010": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": -135, "rate 2": -140,
        #                 "rate 3": -145,
        #                 "rate 4": -150, "rate 5": -155,
        #                 "rate 6": -160,
        #                 "rate 7": -170}}}},
        #     {
        #     "stock cost": {
        #         "2009": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": 50, "rate 2": 60, "rate 3": 70,
        #                 "rate 4": 80, "rate 5": 90, "rate 6": 100,
        #                 "rate 7": 110}},
        #         "2010": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": 50, "rate 2": 60, "rate 3": 70,
        #                 "rate 4": 80, "rate 5": 90, "rate 6": 100,
        #                 "rate 7": 110}}},
        #     "energy cost": {
        #         "2009": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": -190, "rate 2": -195,
        #                 "rate 3": -190,
        #                 "rate 4": -205, "rate 5": -180,
        #                 "rate 6": -230,
        #                 "rate 7": -200}},
        #         "2010": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": -190, "rate 2": -195,
        #                 "rate 3": -190,
        #                 "rate 4": -205, "rate 5": -180,
        #                 "rate 6": -230,
        #                 "rate 7": -200}}},
        #     "carbon cost": {
        #         "2009": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": -90, "rate 2": -95,
        #                 "rate 3": -100,
        #                 "rate 4": -105, "rate 5": -110,
        #                 "rate 6": -115,
        #                 "rate 7": -120}},
        #         "2009": {
        #             "residential": None,
        #             "commercial": {
        #                 "rate 1": -90, "rate 2": -95,
        #                 "rate 3": -100,
        #                 "rate 4": -105, "rate 5": -110,
        #                 "rate 6": -115,
        #                 "rate 7": -120}}}}]
        # Adjust/finalize point value test measure consumer metrics
        # for ind, m in enumerate(cls.a_run_dist.measures):
        #     m.consumer_metrics['anpv'] = consumer_metrics_dist[ind]
        cls.measures_master_msegs_out = [{
            "stock": {
                "total": {
                    "all": {"2009": 20, "2010": 20},
                    "measure": {"2009": 17, "2010": 14.5}},
                "competed": {
                    "all": {"2009": 10, "2010": 10},
                    "measure": {"2009": 8.5, "2010": 6}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 34, "2010": 29},
                    "efficient": {"2009": 25.5, "2010": 21.75}},
                "competed": {
                    "baseline": {"2009": 17, "2010": 12},
                    "efficient": {"2009": 8.5, "2010": 6}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 51, "2010": 43.5},
                    "efficient": {"2009": 34, "2010": 29}},
                "competed": {
                    "baseline": {"2009": 25.5, "2010": 18},
                    "efficient": {"2009": 8.5, "2010": 6}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 17, "2010": 14.5},
                        "efficient": {"2009": 8.5, "2010": 7.25}},
                    "competed": {
                        "baseline": {"2009": 8.5, "2010": 6},
                        "efficient": {"2009": 0, "2010": 0}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 34, "2010": 29},
                        "efficient": {"2009": 25.5, "2010": 21.75}},
                    "competed": {
                        "baseline": {"2009": 17, "2010": 12},
                        "efficient": {"2009": 8.5, "2010": 6}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 51, "2010": 43.5},
                        "efficient": {"2009": 34, "2010": 29}},
                    "competed": {
                        "baseline": {"2009": 25.5, "2010": 18},
                        "efficient": {"2009": 8.5, "2010": 6}}}},
            "lifetime": {"baseline": {"2009": 1, "2010": 1},
                         "measure": {"2009": 1, "2010": 1}}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 20, "2010": 20},
                    "measure": {"2009": 0, "2010": 13}},
                "competed": {
                    "all": {"2009": 10, "2010": 10},
                    "measure": {"2009": 0, "2010": 8}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 0, "2010": 12},
                    "efficient": {"2009": 0, "2010": 9}},
                "competed": {
                    "baseline": {"2009": 0, "2010": 12},
                    "efficient": {"2009": 0, "2010": 6}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 0, "2010": 18},
                    "efficient": {"2009": 0, "2010": 12}},
                "competed": {
                    "baseline": {"2009": 0, "2010": 18},
                    "efficient": {"2009": 0, "2010": 6}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 10, "2010": 13},
                        "efficient": {"2009": 20, "2010": 6.5}},
                    "competed": {
                        "baseline": {"2009": 5, "2010": 8},
                        "efficient": {"2009": 10, "2010": 0}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 0, "2010": 12},
                        "efficient": {"2009": 0, "2010": 9}},
                    "competed": {
                        "baseline": {"2009": 0, "2010": 12},
                        "efficient": {"2009": 0, "2010": 6}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 0, "2010": 18},
                        "efficient": {"2009": 0, "2010": 12}},
                    "competed": {
                        "baseline": {"2009": 0, "2010": 18},
                        "efficient": {"2009": 0, "2010": 6}}}},
            "lifetime": {"baseline": {"2009": 1, "2010": 1},
                         "measure": {"2009": 1, "2010": 1}}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 30, "2010": 30},
                    "measure": {"2009": 23, "2010": 22.5}},
                "competed": {
                    "all": {"2009": 15, "2010": 15},
                    "measure": {"2009": 11.5, "2010": 11}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 46, "2010": 45},
                    "efficient": {"2009": 34.5, "2010": 33.75}},
                "competed": {
                    "baseline": {"2009": 23, "2010": 22},
                    "efficient": {"2009": 11.5, "2010": 11}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 69, "2010": 67.5},
                    "efficient": {"2009": 46, "2010": 45}},
                "competed": {
                    "baseline": {"2009": 34.5, "2010": 33},
                    "efficient": {"2009": 11.5, "2010": 11}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 23, "2010": 22.5},
                        "efficient": {"2009": 11.5, "2010": 11.25}},
                    "competed": {
                        "baseline": {"2009": 11.5, "2010": 11},
                        "efficient": {"2009": 0, "2010": 0}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 46, "2010": 45},
                        "efficient": {"2009": 34.5, "2010": 33.75}},
                    "competed": {
                        "baseline": {"2009": 23, "2010": 22},
                        "efficient": {"2009": 11.5, "2010": 11}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 69, "2010": 67.5},
                        "efficient": {"2009": 46, "2010": 45}},
                    "competed": {
                        "baseline": {"2009": 34.5, "2010": 33},
                        "efficient": {"2009": 11.5, "2010": 11}}}},
                "lifetime": {"baseline": {"2009": 1, "2010": 1},
                             "measure": {"2009": 1, "2010": 1}}}]
        # cls.measures_master_msegs_out_dist = [{
        #     "stock": {
        #         "total": {
        #             "all": {"2009": 20, "2010": 20},
        #             "measure": {
        #                 "2009": 17,
        #                 "2010": numpy.array([14.5, 15.0, 16.5])}},
        #         "competed": {
        #             "all": {"2009": 10, "2010": 10},
        #             "measure": {
        #                 "2009": 8.5,
        #                 "2010": numpy.array([6.0, 6.5, 8.0])}}},
        #     "energy": {
        #         "total": {
        #             "baseline": {
        #                 "2009": 34,
        #                 "2010": numpy.array([29, 30, 33])},
        #             "efficient": {
        #                 "2009": 25.5,
        #                 "2010": numpy.array([21.75, 22.50, 24.75])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": 17,
        #                 "2010": numpy.array([12, 13, 16])},
        #             "efficient": {
        #                 "2009": 8.5,
        #                 "2010": numpy.array([6.0, 6.5, 8.0])}}},
        #     "carbon": {
        #         "total": {
        #             "baseline": {
        #                 "2009": 51,
        #                 "2010": numpy.array([43.5, 45.0, 49.5])},
        #             "efficient": {
        #                 "2009": 34,
        #                 "2010": numpy.array([29, 30, 33])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": 25.5,
        #                 "2010": numpy.array([18.0, 19.5, 24.0])},
        #             "efficient": {
        #                 "2009": 8.5,
        #                 "2010": numpy.array([6.0, 6.5, 8.0])}}},
        #     "cost": {
        #         "stock": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": 17,
        #                     "2010": numpy.array([14.5, 15.0, 16.5])},
        #                 "efficient": {
        #                     "2009": 8.5,
        #                     "2010": numpy.array([7.25, 7.50, 8.25])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": 8.5,
        #                     "2010": numpy.array([6.0, 6.5, 8.0])},
        #                 "efficient": {
        #                     "2009": 0,
        #                     "2010": numpy.array([0, 0, 0])}}},
        #         "energy": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": 34,
        #                     "2010": numpy.array([29, 30, 33])},
        #                 "efficient": {
        #                     "2009": 25.5,
        #                     "2010": numpy.array([21.75, 22.50, 24.75])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": 17,
        #                     "2010": numpy.array([12, 13, 16])},
        #                 "efficient": {
        #                     "2009": 8.5,
        #                     "2010": numpy.array([6.0, 6.5, 8.0])}}},
        #         "carbon": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": 51,
        #                     "2010": numpy.array([43.5, 45.0, 49.5])},
        #                 "efficient": {
        #                     "2009": 34,
        #                     "2010": numpy.array([29, 30, 33])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": 25.5,
        #                     "2010": numpy.array([18.0, 19.5, 24.0])},
        #                 "efficient": {
        #                     "2009": 8.5,
        #                     "2010": numpy.array([6.0, 6.5, 8.0])}}}},
        #     "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                  "measure": {"2009": 1, "2010": 1}}},
        #     {
        #     "stock": {
        #         "total": {
        #             "all": {"2009": 20, "2010": 20},
        #             "measure": {
        #                 "2009": 0,
        #                 "2010": numpy.array([13.0, 12.5, 11.5])}},
        #         "competed": {
        #             "all": {"2009": 10, "2010": 10},
        #             "measure": {
        #                 "2009": 0,
        #                 "2010": numpy.array([8.0, 7.5, 6.5])}}},
        #     "energy": {
        #         "total": {
        #             "baseline": {
        #                 "2009": 0,
        #                 "2010": numpy.array([12, 10, 6])},
        #             "efficient": {
        #                 "2009": 0,
        #                 "2010": numpy.array([9.0, 7.5, 4.5])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": 0,
        #                 "2010": numpy.array([12, 10, 6])},
        #             "efficient": {
        #                 "2009": 0,
        #                 "2010": numpy.array([6, 5, 3])}}},
        #     "carbon": {
        #         "total": {
        #             "baseline": {
        #                 "2009": 0,
        #                 "2010": numpy.array([18, 15, 9])},
        #             "efficient": {
        #                 "2009": 0,
        #                 "2010": numpy.array([12, 10, 6])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": 0,
        #                 "2010": numpy.array([18, 15, 9])},
        #             "efficient": {
        #                 "2009": 0,
        #                 "2010": numpy.array([6, 5, 3])}}},
        #     "cost": {
        #         "stock": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": 10,
        #                     "2010": numpy.array([13.0, 12.5, 11.5])},
        #                 "efficient": {
        #                     "2009": 20,
        #                     "2010": numpy.array([6.50, 7.5, 8.05])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": 5,
        #                     "2010": numpy.array([8.0, 7.5, 6.5])},
        #                 "efficient": {
        #                     "2009": 10,
        #                     "2010": numpy.array([0, 1.5, 2.6])}}},
        #         "energy": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": 0,
        #                     "2010": numpy.array([12, 10, 6])},
        #                 "efficient": {
        #                     "2009": 0,
        #                     "2010": numpy.array([9.0, 7.5, 4.5])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": 0,
        #                     "2010": numpy.array([12, 10, 6])},
        #                 "efficient": {
        #                     "2009": 0,
        #                     "2010": numpy.array([6, 5, 3])}}},
        #         "carbon": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": 0,
        #                     "2010": numpy.array([18, 15, 9])},
        #                 "efficient": {
        #                     "2009": 0,
        #                     "2010": numpy.array([12, 10, 6])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": 0,
        #                     "2010": numpy.array([18, 15, 9])},
        #                 "efficient": {
        #                     "2009": 0,
        #                     "2010": numpy.array([6, 5, 3])}}}},
        #     "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                  "measure": {"2009": 1, "2010": 1}}},
        #     {
        #     "stock": {
        #         "total": {
        #             "all": {
        #                 "2009": 30, "2010": 30},
        #             "measure": {
        #                 "2009": 23,
        #                 "2010": numpy.array([22.5, 22.5, 22.0])}},
        #         "competed": {
        #             "all": {"2009": 15, "2010": 15},
        #             "measure": {
        #                 "2009": 11.5,
        #                 "2010": numpy.array([11.0, 11.0, 10.5])}}},
        #     "energy": {
        #         "total": {
        #             "baseline": {
        #                 "2009": 46,
        #                 "2010": numpy.array([45, 45, 44])},
        #             "efficient": {
        #                 "2009": 34.5,
        #                 "2010": numpy.array([33.75, 33.75, 33.00])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": 23,
        #                 "2010": numpy.array([22, 22, 21])},
        #             "efficient": {
        #                 "2009": 11.5,
        #                 "2010": numpy.array([11.0, 11.0, 10.5])}}},
        #     "carbon": {
        #         "total": {
        #             "baseline": {
        #                 "2009": 69,
        #                 "2010": numpy.array([67.5, 67.5, 66.0])},
        #             "efficient": {
        #                 "2009": 46,
        #                 "2010": numpy.array([45, 45, 44])}},
        #         "competed": {
        #             "baseline": {
        #                 "2009": 34.5,
        #                 "2010": numpy.array([33.0, 33.0, 31.5])},
        #             "efficient": {
        #                 "2009": 11.5,
        #                 "2010": numpy.array([11.0, 11.0, 10.5])}}},
        #     "cost": {
        #         "stock": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": 23,
        #                     "2010": numpy.array([22.5, 22.5, 22.0])},
        #                 "efficient": {
        #                     "2009": 11.5,
        #                     "2010": numpy.array([11.25, 11.25, 11.00])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": 11.5,
        #                     "2010": numpy.array([11.0, 11.0, 10.5])},
        #                 "efficient": {
        #                     "2009": 0,
        #                     "2010": numpy.array([0, 0, 0])}}},
        #         "energy": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": 46,
        #                     "2010": numpy.array([45, 45, 44])},
        #                 "efficient": {
        #                     "2009": 34.5,
        #                     "2010": numpy.array([33.75, 33.75, 33.00])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": 23,
        #                     "2010": numpy.array([22, 22, 21])},
        #                 "efficient": {
        #                     "2009": 11.5,
        #                     "2010": numpy.array([11.0, 11.0, 10.5])}}},
        #         "carbon": {
        #             "total": {
        #                 "baseline": {
        #                     "2009": 69,
        #                     "2010": numpy.array([67.5, 67.5, 66.0])},
        #                 "efficient": {
        #                     "2009": 46,
        #                     "2010": numpy.array([45, 45, 44])}},
        #             "competed": {
        #                 "baseline": {
        #                     "2009": 34.5,
        #                     "2010": numpy.array([33.0, 33.0, 31.5])},
        #                 "efficient": {
        #                     "2009": 11.5,
        #                     "2010": numpy.array([11.0, 11.0, 10.5])}}}},
        #     "lifetime": {"baseline": {"2009": 1, "2010": 1},
        #                  "measure": {"2009": 1, "2010": 1}}}]

    def test_compete_com(self):
        """Test outcomes given sample measures w/ point value inputs."""
        # Run measure competition routine on sample measures
        self.a_run.compete_com_primary(
            self.measures_all, self.overlap_key, self.test_adopt_scheme)
        # Run secondary microsegment adjustments on sample measure
        self.a_run.secondary_adj(
            self.measures_secondary, self.overlap_key_scnd,
            self.secnd_adj_key, self.test_adopt_scheme)
        # Check updated competed master microsegments for each sample measure
        # following competition/secondary microsegment adjustments
        for ind, d in enumerate(self.a_run.measures):
            self.dict_check(
                self.measures_master_msegs_out[ind],
                self.a_run.measures[ind].markets[self.test_adopt_scheme][
                    "competed"]["master_mseg"])

    # def test_compete_com_dist(self):
    #     """Test outcomes given valid sample measures w/ some array inputs."""
    #     # Run measure competition routine on sample measures
    #     self.a_run_dist.compete_com_primary(
    #         self.measures_all_dist, self.overlap_key, self.test_adopt_scheme)
    #     # Run secondary microsegment adjustments on sample measure
    #     self.a_run_dist.secondary_adj(
    #         self.measures_secondary_dist, self.overlap_key_scnd,
    #         self.secnd_adj_key, self.test_adopt_scheme)
    #     # Check updated competed master microsegments for each sample measure
    #     # following competition/secondary microsegment adjustments
    #     for ind, d in enumerate(self.a_run_dist.measures):
    #         self.dict_check(
    #             self.measures_master_msegs_out_dist[ind],
    #             self.a_run_dist.measures[ind].markets[self.test_adopt_scheme][
    #                 "competed"]["master_mseg"])


class NumpyConversionTest(unittest.TestCase, CommonMethods):
    """Test the operation of the 'convert_to_numpy' function.

    Verify that the function converts terminal/leaf node lists in a dict to
    numpy arrays.

    Attributes:
        handyvars (object): Useful variables across the class.
        sample_measure (object): Sample measure data with lists to convert.
    """

    @classmethod
    def setUpClass(cls):
        """Define objects/variables for use across all class functions."""
        cls.handyvars = run.UsefulVars()
        cls.sample_measure = {
            "market_entry_year": None,
            "market_exit_year": None,
            "markets": {
                "Technical potential": {
                    "key 1": {
                        "nested key 1":
                            [1, 2, 3, 4, 5],
                        "nested key 2": 5},
                    "key 2": 10.8},
                "Max adoption potential": {
                    "key 1": {
                        "nested key 1":
                            [0.5, 0.2, 0.3, 0.4, 0.5],
                        "nested key 2": 2},
                    "key 2": 5.8}}}

    def test_numpy_convert(self):
        """Test for correct function output given valid input."""
        # Instantiate measure
        measure_instance = run.Measure(self.handyvars, **self.sample_measure)
        # Test for correct data types in measure markets attribute
        for adopt_scheme in self.handyvars.adopt_schemes:
            for comp_scheme in ["uncompeted", "competed"]:
                tested_data = \
                    measure_instance.markets[adopt_scheme][comp_scheme]
                self.assertTrue(
                    all([isinstance(x, y) for x, y in zip([
                        tested_data["key 1"]["nested key 1"],
                        tested_data["key 1"]["nested key 2"],
                        tested_data["key 2"]], [numpy.ndarray, int, float])]))


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    """Trigger default behavior of running all test fixtures in the file."""
    unittest.main()

if __name__ == "__main__":
    main()
