#!/usr/bin/env python3

""" Tests for processing microsegment cost, performance, and lifetime data """

# Import code to be tested
import mseg_techdata

# Import needed packages
import unittest
import numpy


class SimpleWalkTest(unittest.TestCase):
    """ Test operation of a simpler version of the walk_techdata function, which
    is used to walk through all the levels of the microsegments dictionary
    structure and update the values at the end of each terminal leaf node """

    # Define a test dict to walk through
    in_dict = {
        "cdiv 1": {"bldg 1": {"fuel 1": {
            "end use 1": {"tech 1": None}}}},
        "cdiv 2": {"bldg 2": {"fuel 2": {
            "end use 2": {"tech 2": None}},
            "fuel 3": {
                "end use 3": {"tech 3": None}}}},
        "cdiv 3": {"bldg 3": {"fuel 3": {
            "end use 3": {"tech 4": None}}},
            "bldg 4": {"fuel 4": {
                "end use 4": {"tech 5": None}}}},
        "cdiv 4": {"bldg 4": {"fuel 5": {
            "end use 5": {"tech 6": {"sub tech 1": None,
                                     "sub tech 2": None}}}}}}

    # Define an output dict that should be yielded via the walk routine. As
    # an additional check, the key chains leading to each terminal leaf node
    # are set to be the values for those leaf nodes.
    out_dict = {
        "cdiv 1": {"bldg 1": {"fuel 1": {"end use 1": {
            "tech 1": ["cdiv 1", "bldg 1", "fuel 1", "end use 1", "tech 1"]
        }}}},
        "cdiv 2": {"bldg 2": {"fuel 2": {"end use 2": {
            "tech 2": ["cdiv 2", "bldg 2", "fuel 2", "end use 2", "tech 2"]
        }}, "fuel 3": {"end use 3": {
            "tech 3": ["cdiv 2", "bldg 2", "fuel 3", "end use 3", "tech 3"]
        }}}},
        "cdiv 3": {"bldg 3": {"fuel 3": {"end use 3": {
            "tech 4": ["cdiv 3", "bldg 3", "fuel 3", "end use 3", "tech 4"]
        }}}, "bldg 4": {"fuel 4": {"end use 4": {
            "tech 5": ["cdiv 3", "bldg 4", "fuel 4", "end use 4", "tech 5"]
        }}}},
        "cdiv 4": {"bldg 4": {"fuel 5": {"end use 5": {"tech 6": {
            "sub tech 1": ["cdiv 4", "bldg 4", "fuel 5", "end use 5", "tech 6",
                           "sub tech 1"],
            "sub tech 2": ["cdiv 4", "bldg 4", "fuel 5", "end use 5", "tech 6",
                           "sub tech 2"]}}}}}}

    def simple_walk(self, in_dict, key_list=[]):
        """ This function represents a simpler verison of the walk_techdata
        function in mseg_techdata_test.py where terminal leaf node values are
        assigned as the key chain that leads to the given leaf node """
        for key, item in sorted(in_dict.items()):
            # If there are additional levels in the dict, call the function
            # again to advance another level deeper into the data structure
            if isinstance(item, dict):
                self.simple_walk(item, key_list + [key])
            # If a leaf node has been reached, finish constructing the key
            # list for the current location and update the data in the dict
            else:
                # Update key chain
                leaf_node_keys = key_list + [key]
                # Update dict key value to the updated key chain
                in_dict[key] = leaf_node_keys
        # Return updated dict
        return in_dict

    # Create a routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                self.assertEqual(dict1[k], dict2[k2])

    # Test that a walk through the in_dict above updates its terminal
    # leaf nodes to the correct values in the out_dict above
    def test_walk_ok(self):
        dict1 = self.simple_walk(self.in_dict)
        dict2 = self.out_dict
        self.dict_check(dict1, dict2)


class ListGeneratorTest(unittest.TestCase):
    """ Test that the list_generator_techdata function correctly updates the
    terminal leaf node values for an input dictionary with input technology
    performance, cost, and lifetime information """

    # Define a test input array in the format of EIA performance and cost
    # data on non-lighting technologies
    eia_nlt_cp = numpy.array([(1, 2005, 2040, 3, 4.5, 3000, b'ELEC_RAD'),
                              (1, 2010, 2011, 1, 2.65, 1200, b'ELEC_HP1'),
                              (1, 2011, 2012, 1, 3.1, 1250, b'ELEC_HP1'),
                              (1, 2012, 2014, 1, 4.5, 1450, b'ELEC_HP1'),
                              (1, 2014, 2040, 1, 5, 2000, b'ELEC_HP1'),
                              (1, 2010, 2011, 2, 3.65, 1200, b'ELEC_HP1'),
                              (1, 2011, 2012, 2, 4.1, 1250, b'ELEC_HP1'),
                              (1, 2012, 2014, 2, 5.5, 1450, b'ELEC_HP1'),
                              (1, 2014, 2040, 2, 6, 2000, b'ELEC_HP1'),
                              (1, 2014, 2040, 2, 5, 2000, b'ELEC_HP1'),
                              (2, 2010, 2013, 3, 4.65, 1400, b'ELEC_HP1'),
                              (2, 2013, 2040, 3, 5.1, 1450, b'ELEC_HP1'),
                              (1, 2005, 2010, 1, 2.75, 1200, b'ELEC_HP2'),
                              (1, 2010, 2011, 1, 2.75, 1250, b'ELEC_HP2'),
                              (1, 2011, 2012, 1, 3.2, 1270, b'ELEC_HP2'),
                              (1, 2012, 2014, 1, 4.6, 1800, b'ELEC_HP2'),
                              (1, 2014, 2040, 1, 5.1, 1900, b'ELEC_HP2'),
                              (1, 2005, 2010, 1, 2.8, 1000, b'ELEC_HP4'),
                              (1, 2010, 2011, 1, 2.9, 1300, b'ELEC_HP4'),
                              (1, 2011, 2012, 1, 3.3, 1400, b'ELEC_HP4'),
                              (1, 2012, 2014, 1, 4.8, 1500, b'ELEC_HP4'),
                              (1, 2014, 2040, 1, 6, 2000, b'ELEC_HP4'),
                              (5, 2007, 2040, 4, 3, 1000, b'ELEC_WH1'),
                              (5, 2005, 2009, 4, 2.8, 1000, b'NG_WH#1'),
                              (5, 2009, 2040, 4, 2.9, 1300, b'NG_WH#1'),
                              (5, 2005, 2009, 4, 2.9, 1000, b'NG_WH#2'),
                              (5, 2009, 2040, 4, 3.2, 1300, b'NG_WH#2'),
                              (5, 2005, 2009, 4, 3.2, 2000, b'NG_WH#4'),
                              (5, 2009, 2040, 4, 3.5, 1500, b'NG_WH#4'),
                              (5, 2005, 2009, 5, 2.8, 1000, b'NG_WH#1'),
                              (5, 2009, 2040, 5, 2.9, 1300, b'NG_WH#1'),
                              (5, 2005, 2009, 5, 2.9, 1000, b'NG_WH#2'),
                              (5, 2009, 2040, 5, 3.2, 1300, b'NG_WH#2'),
                              (5, 2005, 2009, 5, 3.2, 2000, b'NG_WH#4'),
                              (5, 2009, 2040, 5, 3.5, 1500, b'NG_WH#4'),
                              (6, 2010, 2011, 2, 28, 100, b'ELEC_STV1'),
                              (6, 2012, 2040, 2, 29, 130, b'ELEC_STV1'),
                              (6, 2010, 2011, 2, 29, 150, b'NG_STV1'),
                              (6, 2012, 2040, 2, 32, 160, b'NG_STV1'),
                              (6, 2010, 2011, 2, 31, 200, b'NG_STV2'),
                              (6, 2012, 2040, 2, 33, 170, b'NG_STV2'),
                              (6, 2010, 2011, 2, 32, 200, b'LPG_STV2'),
                              (6, 2012, 2040, 2, 35, 175, b'LPG_STV2'),
                              (6, 2010, 2011, 2, 33, 300, b'ELEC_STV2'),
                              (6, 2012, 2040, 2, 36, 250, b'ELEC_STV2'),
                              (7, 2010, 2011, 2, 128, 1010, b'ELEC_DRY1'),
                              (7, 2012, 2040, 2, 129, 1310, b'ELEC_DRY1'),
                              (7, 2010, 2011, 2, 129, 1510, b'NG_DRY1'),
                              (7, 2012, 2040, 2, 132, 1610, b'NG_DRY1'),
                              (7, 2010, 2011, 2, 131, 2010, b'NG_DRY2'),
                              (7, 2012, 2040, 2, 133, 1710, b'NG_DRY2'),
                              (7, 2010, 2011, 2, 133, 3010, b'ELEC_DRY2'),
                              (7, 2012, 2040, 2, 136, 2510, b'ELEC_DRY2'),
                              (3, 2010, 2040, 3, 15, 150, b'CW#1'),
                              (3, 2010, 2040, 3, 12, 175, b'CW#2'),
                              (3, 2010, 2040, 3, 10, 300, b'CW#3'),
                              (8, 2005, 2009, 3, 200, 300, b'RefSF#1'),
                              (8, 2009, 2013, 3, 300, 250, b'RefSF#1'),
                              (8, 2013, 2040, 3, 400, 200, b'RefSF#1'),
                              (8, 2005, 2009, 3, 300, 400, b'RefBF#1'),
                              (8, 2009, 2013, 3, 400, 300, b'RefBF#1'),
                              (8, 2013, 2040, 3, 500, 200, b'RefBF#1'),
                              (8, 2005, 2009, 3, 500, 500, b'RefTF#1'),
                              (8, 2009, 2013, 3, 600, 400, b'RefTF#1'),
                              (8, 2013, 2040, 3, 700, 300, b'RefTF#1'),
                              (8, 2005, 2009, 3, 800, 800, b'RefSF#2'),
                              (8, 2009, 2013, 3, 900, 700, b'RefSF#2'),
                              (8, 2013, 2040, 3, 1000, 600, b'RefSF#2'),
                              (8, 2005, 2009, 3, 900, 200, b'RefBF#2'),
                              (8, 2009, 2013, 3, 1000, 100, b'RefBF#2'),
                              (8, 2013, 2040, 3, 1100, 50, b'RefBF#2'),
                              (8, 2005, 2009, 3, 900, 1400, b'RefTF#2'),
                              (8, 2009, 2013, 3, 950, 1200, b'RefTF#2'),
                              (8, 2013, 2040, 3, 1000, 1100, b'RefTF#2'),
                              (8, 2005, 2009, 3, 1500, 700, b'RefTF#3'),
                              (8, 2009, 2013, 3, 1600, 650, b'RefTF#3'),
                              (8, 2013, 2040, 3, 1700, 550, b'RefTF#3'),
                              (8, 2005, 2009, 1, 1500, 700, b'RefTF#3'),
                              (8, 2009, 2013, 1, 1600, 650, b'RefTF#3'),
                              (8, 2013, 2040, 1, 1700, 550, b'RefTF#3')
                              ],
                             dtype=[('ENDUSE', '<i8'),
                                    ('START_EQUIP_YR', '<i8'),
                                    ('END_EQUIP_YR', '<f8'),
                                    ('CDIV', '<i8'),
                                    ('BASE_EFF', '<f8'),
                                    ('INST_COST', '<f8'),
                                    ('NAME', 'S10')])

    # Define a test input array in the format of EIA lifetime
    # data on non-lighting technologies
    eia_nlt_l = numpy.array([(1, 3.5, 19.5, b'ELEC_RAD'),
                             (1, 15, 20.1, b'ELEC_HP'),
                             (1, 15.6, 20.6, b'NG_FA'),
                             (2, 18.6, 19.1, b'CENT_AIR'),
                             (2, 18, 25, b'ELEC_HP'),
                             (5, 10, 20.5, b'ELEC_WH'),
                             (5, 8.5, 15.0, b'NG_WH'),
                             (6, 10.5, 12.4, b'ELEC_STV'),
                             (6, 17.9, 25, b'NG_STV'),
                             (6, 14.7, 27, b'LPG_STV'),
                             (7, 13.2, 21.6, b'ELEC_DRY'),
                             (7, 10, 17, b'NG_DRY'),
                             (3, 8.9, 16.7, b'CW'),
                             (8, 6.5, 11.1, b'REFR'),
                             (9, 5, 10.1, b'FREZ')],
                            dtype=[('ENDUSE', '<i8'),
                                   ('LIFE_MIN', '<f8'),
                                   ('LIFE_MAX', '<f8'),
                                   ('NAME', 'S10')])

    # Define a test input array in the format of EIA performance, cost, and
    # lifetime data on lighting technologies
    eia_lt = numpy.array([(2008, 2012, 0.33, 10000, 55, b'GSL', b'Inc'),
                          (2012, 2013, 1.03, 20000, 60, b'GSL', b'Inc'),
                          (2013, 2017, 1.53, 35000, 61.2, b'GSL', b'Inc'),
                          (2017, 2020, 2.75, 40000, 80.3, b'GSL', b'Inc'),
                          (2020, 2040, 3.45, 50000, 90, b'GSL', b'Inc'),
                          (2005, 2008, 0.35, 10000, 60, b'GSL', b'LED'),
                          (2008, 2010, 1.13, 30000, 65, b'GSL', b'LED'),
                          (2010, 2012, 1.55, 37000, 63.2, b'GSL', b'LED'),
                          (2012, 2040, 2.78, 42000, 90.3, b'GSL', b'LED'),
                          (2010, 2040, 3.71, 8000, 100.3, b'REF', b'LED')],
                         dtype=[('START_EQUIP_YR', '<i8'),
                                ('END_EQUIP_YR', '<f8'),
                                ('BASE_EFF', '<f8'),
                                ('LIFE_HRS', '<f8'),
                                ('INST_COST', '<f8'),
                                ('NAME', 'S3'),
                                ('BULB_TYPE', 'S3')])

    # Define a test dict in the format of BTO-defined performance, cost
    # and lifetime data on all technologies not covered by EIA data
    tech_non_eia = {'secondary heating (electric)': [[5, 2, 'Source 1'],
                                                     [2, 3, 'Source 2'],
                                                     [50, 70, 'Source 3'],
                                                     'COP'],
                    'secondary heating (natural gas)': [[4, 1, 'Source 4'],
                                                        [87, 92, 'Source 5'],
                                                        [60, 80, 'Source 6'],
                                                        'AFUE'],
                    'secondary heating (kerosene)': [[1.1, 2.2, 'Source 7'],
                                                     [85, 99, 'Source 8'],
                                                     [100, 200, 'Source 9'],
                                                     'AFUE'],
                    'secondary heating (wood)': [[10, 5, 'Source 10'],
                                                 [70, 85, 'Source 11'],
                                                 [45, 50, 'Source 12'],
                                                 'AFUE'],
                    'secondary heating (LPG)': [[5, 5, 'Source 13'],
                                                [90, 95, 'Source 14'],
                                                [150, 175, 'Source 15'],
                                                'AFUE'],
                    'secondary heating (coal)': [[15, 10, 'Source 16'],
                                                 [77, 82, 'Source 17'],
                                                 [35, 55, 'Source 17'],
                                                 'AFUE'],
                    'TV': [[1, 0.5, 'Source 18'], [10.1, 20.4, 'Source 18'],
                           [500, 605, 'Source 19'], 'W'],
                    'set top box': [[25, 2, 'Source 20'],
                                    [100, 50, 'Source 20'],
                                    [60, 43, 'Source 20'], 'W'],
                    'DVD': [[7, 4, 'Source 21'],
                            [70, 60, 'Source 21'], [20, 30, 'Source 21'],
                            'W'],
                    'other MELs': [[0, 0, 'NA'], [0, 0, 'NA'],
                                   [0, 0, 'NA'], 'NA'],
                    'windows conduction': [[25, 5, 'RS Means'],
                                           [7, 10, 'NREL Efficiency DB'],
                                           [20, 30, 'RS Means'], 'R Value'],
                    'windows solar': [[20, 2, 'RS Means'],
                                      [0.4, 0.3, 'NREL Efficiency DB'],
                                      [20, 30, 'RS Means'], 'SHGC'],
                    'wall': [[25, 7, 'RS Means'], [6, 7, 'EnergyStar'],
                             [35, 40, 'RS Means'], 'R Value/sq.in.']}

    # Define the modeling time horizon to test (2009:2013)
    years = [str(i) for i in range(2009, 2013 + 1)]
    project_dict = dict.fromkeys(years)

    # Define a sample list of full dictionary key chains that are defined
    # while running through the microsegments JSON structure and which will
    # be used to determine what performance, cost, and lifetime data to look
    # for
    tech_ok_keys = [['new england', 'single family home',
                     'electricity (grid)', 'heating', 'supply', 'ASHP'],
                    ['east north central', 'multi family home',
                     'electricity (grid)', 'refrigeration'],
                    ['east north central', 'multi family home',
                     'electricity (grid)', 'other (grid electric)',
                     'clothes washing'],
                    ['mid atlantic', 'single family home',
                     'natural gas', 'cooking'],
                    ['mid atlantic', 'single family home',
                     'natural gas', 'drying'],
                    ['west north central', 'mobile home',
                     'natural gas', 'water heating'],
                    ['west north central', 'mobile home',
                     'electricity (grid)', 'lighting',
                     'general service (LED)'],
                    ['mid atlantic', 'single family home',
                     'electricity (grid)', 'secondary heating',
                     'supply', 'non-specific'],
                    ['mid atlantic', 'single family home',
                     'electricity (grid)', 'secondary heating',
                     'demand', 'windows conduction']]

    # Define a sample list of full dictionary key chains as above that should
    # cause the function to fail
    tech_fail_keys = [['nengland', 'single family home',
                       'electricity', 'heating', 'supply', 'ASHP'],
                      ['east north central', 'multi family home',
                       'electric', 'refrigeration'],
                      ['east north central', 'multi family home',
                       'electricity (grid)', 'other (gas electric)',
                       'clothes washing'],
                      ['east north central', 'multi family home',
                       'electricity (grid)', 'other (gas electric)',
                       'washing device']]

    # Define an output dict with leaf node values that should be yielded
    # by the walk_techdata function given the valid inputs above.  Output dict
    # information for a given technology is organized by performance,
    # installed cost, and lifetime.  Within the performance and cost
    # categories, a "typical" and "best" level are provided.  For all three
    # categories, the units and source of the information are provided.
    ok_datadict_out = [[{
        "performance": {
            "typical": {"2009": 2.65, "2010": 2.65, "2011": 3.1, "2012": 4.5,
                        "2013": 4.5},
            "best": {"2009": 2.9, "2010": 2.9, "2011": 3.3, "2012": 4.8,
                     "2013": 4.8},
            "units": "COP",
            "source": "EIA AEO"},
        "installed cost": {
            "typical": {"2009": 1200, "2010": 1200, "2011": 1250, "2012": 1450,
                        "2013": 1450},
            "best": {"2009": 1300, "2010": 1300, "2011": 1400, "2012": 1500,
                     "2013": 1500},
            "units": "2013$/unit",
            "source": "EIA AEO"},
        "lifetime": {
            "average": {"2009": 17.55, "2010": 17.55, "2011": 17.55,
                        "2012": 17.55, "2013": 17.55},
            "range": {"2009": 2.55, "2010": 2.55, "2011": 2.55, "2012": 2.55,
                      "2013": 2.55},
            "units": "years",
            "source": "EIA AEO"}}],
        [{"performance": {
            "typical": {"2009": 433.33, "2010": 433.33, "2011": 433.33,
                        "2012": 433.33, "2013": 533.33},
            "best": {"2009": 1166.67, "2010": 1166.67, "2011": 1166.67,
                     "2012": 1166.67, "2013": 1266.67},
            "units": "kWh/yr",
            "source": "EIA AEO"},
          "installed cost": {
            "typical": {"2009": 316.67, "2010": 316.67, "2011": 316.67,
                        "2012": 316.67, "2013": 233.33},
            "best": {"2009": 483.33, "2010": 483.33, "2011": 483.33,
                     "2012": 483.33, "2013": 400},
            "units": "2013$/unit",
            "source": "EIA AEO"},
          "lifetime": {
            "average": {"2009": 8.8, "2010": 8.8, "2011": 8.8, "2012": 8.8,
                        "2013": 8.8},
            "range": {"2009": 2.3, "2010": 2.3, "2011": 2.3, "2012": 2.3,
                      "2013": 2.3},
            "units": "years",
            "source": "EIA AEO"}}],
        [{"performance": {
            "typical": {"2009": 15, "2010": 15, "2011": 15, "2012": 15,
                        "2013": 15},
            "best": {"2009": 10, "2010": 10, "2011": 10, "2012": 10,
                     "2013": 10},
            "units": "kWh/cycle",
            "source": "EIA AEO"},
          "installed cost": {
            "typical": {"2009": 150, "2010": 150, "2011": 150, "2012": 150,
                        "2013": 150},
            "best": {"2009": 300, "2010": 300, "2011": 300, "2012": 300,
                     "2013": 300},
            "units": "2013$/unit",
            "source": "EIA AEO"},
          "lifetime": {
            "average": {"2009": 12.8, "2010": 12.8, "2011": 12.8, "2012": 12.8,
                        "2013": 12.8},
            "range": {"2009": 3.9, "2010": 3.9, "2011": 3.9, "2012": 3.9,
                      "2013": 3.9},
            "units": "years",
            "source": "EIA AEO"}}],
        [{"performance": {
            "typical": {"2009": 29, "2010": 29, "2011": 29, "2012": 32,
                        "2013": 32},
            "best": {"2009": 31, "2010": 31, "2011": 31, "2012": 33,
                     "2013": 33},
            "units": "TEff",
            "source": "EIA AEO"},
          "installed cost": {
            "typical": {"2009": 150, "2010": 150, "2011": 150, "2012": 160,
                        "2013": 160},
            "best": {"2009": 200, "2010": 200, "2011": 200, "2012": 170,
                     "2013": 170},
            "units": "2013$/unit",
            "source": "EIA AEO"},
          "lifetime": {
            "average": {"2009": 21.45, "2010": 21.45, "2011": 21.45,
                        "2012": 21.45, "2013": 21.45},
            "range": {"2009": 3.55, "2010": 3.55, "2011": 3.55, "2012": 3.55,
                      "2013": 3.55},
            "units": "years",
            "source": "EIA AEO"}}],
        [{"performance": {
            "typical": {"2009": 129, "2010": 129, "2011": 129, "2012": 132,
                        "2013": 132},
            "best": {"2009": 131, "2010": 131, "2011": 131, "2012": 133,
                     "2013": 133},
            "units": "EF",
            "source": "EIA AEO"},
          "installed cost": {
            "typical": {"2009": 1510, "2010": 1510, "2011": 1510, "2012": 1610,
                        "2013": 1610},
            "best": {"2009": 2010, "2010": 2010, "2011": 2010, "2012": 1710,
                     "2013": 1710},
            "units": "2013$/unit",
            "source": "EIA AEO"},
          "lifetime": {
            "average": {"2009": 13.5, "2010": 13.5, "2011": 13.5, "2012": 13.5,
                        "2013": 13.5},
            "range": {"2009": 3.5, "2010": 3.5, "2011": 3.5, "2012": 3.5,
                      "2013": 3.5},
            "units": "years",
            "source": "EIA AEO"}}],
        [{"performance": {
            "typical": {"2009": 2.9, "2010": 2.9, "2011": 2.9, "2012": 2.9,
                        "2013": 2.9},
            "best": {"2009": 3.5, "2010": 3.5, "2011": 3.5, "2012": 3.5,
                     "2013": 3.5},
            "units": "EF",
            "source": "EIA AEO"},
          "installed cost": {
            "typical": {"2009": 1300, "2010": 1300, "2011": 1300, "2012": 1300,
                        "2013": 1300},
            "best": {"2009": 1500, "2010": 1500, "2011": 1500, "2012": 1500,
                     "2013": 1500},
            "units": "2013$/unit",
            "source": "EIA AEO"},
          "lifetime": {
            "average": {"2009": 11.75, "2010": 11.75, "2011": 11.75,
                        "2012": 11.75, "2013": 11.75},
            "range": {"2009": 3.25, "2010": 3.25, "2011": 3.25, "2012": 3.25,
                      "2013": 3.25},
            "units": "years",
            "source": "EIA AEO"}}],
        [{"performance": {
            "typical": {"2009": 1.13, "2010": 1.55, "2011": 1.55, "2012": 2.78,
                        "2013": 2.78},
            "best": {"2009": "NA", "2010": "NA", "2011": "NA", "2012": "NA",
                     "2013": "NA"},
            "units": "lm/W",
            "source": "EIA AEO"},
          "installed cost": {
            "typical": {"2009": 65, "2010": 63.2, "2011": 63.2, "2012": 90.3,
                        "2013": 90.3},
            "best": {"2009": "NA", "2010": "NA", "2011": "NA", "2012": "NA",
                     "2013": "NA"},
            "units": "2013$/unit",
            "source": "EIA AEO"},
          "lifetime": {
            "average": {"2009": 3.42, "2010": 4.22, "2011": 4.22, "2012": 4.79,
                        "2013": 4.79},
            "range": {"2009": "NA", "2010": "NA", "2011": "NA", "2012": "NA",
                      "2013": "NA"},
            "units": "years",
            "source": "EIA AEO"}}],
        [{"performance": {
            "typical": {"2009": 2, "2010": 2, "2011": 2, "2012": 2, "2013": 2},
            "best": {"2009": 3, "2010": 3, "2011": 3, "2012": 3, "2013": 3},
            "units": "COP",
            "source": "Source 2"},
          "installed cost": {
            "typical": {"2009": 50, "2010": 50, "2011": 50, "2012": 50,
                        "2013": 50},
            "best": {"2009": 70, "2010": 70, "2011": 70, "2012": 70,
                     "2013": 70},
            "units": "2013$/unit",
            "source": "Source 3"},
          "lifetime": {
            "average": {"2009": 5, "2010": 5, "2011": 5, "2012": 5,
                        "2013": 5},
            "range": {"2009": 2, "2010": 2, "2011": 2, "2012": 2, "2013": 2},
            "units": "years",
            "source": "Source 1"}}],
        [{"performance": {
            "typical": {"2009": 7, "2010": 7, "2011": 7, "2012": 7, "2013": 7},
            "best": {"2009": 10, "2010": 10, "2011": 10, "2012": 10, 
                     "2013": 10},
            "units": "R Value",
            "source": "NREL Efficiency DB"},
          "installed cost": {
            "typical": {"2009": 20, "2010": 20, "2011": 20, "2012": 20,
                        "2013": 20},
            "best": {"2009": 30, "2010": 30, "2011": 30, "2012": 30,
                     "2013": 30},
            "units": "2013$/sf",
            "source": "RS Means"},
          "lifetime": {
            "average": {"2009": 25, "2010": 25, "2011": 25, "2012": 25,
                        "2013": 25},
            "range": {"2009": 5, "2010": 5, "2011": 5, "2012": 5,
                      "2013": 5},
            "units": "years",
            "source": "RS Means"}}]]

    # The EIA array with cost and performance data on non-lighting
    # technologies is reduced during the walk_techdata routine as rows are
    # matched and removed from it.  The following list elements represent the
    # reduced arrays that should be produced from running each of the dict
    # key chains in tech_ok_keys above through the walk_techdata function
    eia_nlt_cp_reduced = [numpy.hstack([eia_nlt_cp[0:1], eia_nlt_cp[5:17],
                                        eia_nlt_cp[22:]]),
                          numpy.hstack([eia_nlt_cp[0:56], eia_nlt_cp[71:74],
                                        eia_nlt_cp[77:]]),
                          numpy.hstack([eia_nlt_cp[0:53], eia_nlt_cp[54],
                                        eia_nlt_cp[56:]]),
                          numpy.hstack([eia_nlt_cp[0:37], eia_nlt_cp[41:]]),
                          numpy.hstack([eia_nlt_cp[0:47], eia_nlt_cp[51:]]),
                          numpy.hstack([eia_nlt_cp[0:23], eia_nlt_cp[25:27],
                                        eia_nlt_cp[29:]]),
                          eia_nlt_cp, eia_nlt_cp, eia_nlt_cp]

    # Create a routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                # In the use of this function to compare dicts below,
                # certain leaf node values will be strings (the info.
                # units and sources) while others will be float values
                if not isinstance(dict1[k], str):
                    self.assertAlmostEqual(dict1[k], dict2[k2], places=2)
                else:
                    self.assertEqual(dict1[k], dict2[k])

    # Test that the walk_techdata function yields a correct output dict
    # given the valid key chain input along with the other sample inputs
    # defined above
    def test_listgen_ok(self):
        for (idx, tk) in enumerate(self.tech_ok_keys):
            dict1 = mseg_techdata.list_generator_techdata(
                self.eia_nlt_cp, self.eia_nlt_l, self.eia_lt,
                mseg_techdata.tech_eia_nonlt, mseg_techdata.tech_eia_lt,
                self.tech_non_eia, tk, self.project_dict)
            dict2 = self.ok_datadict_out[idx][0]
            self.dict_check(dict1[0], dict2)
            numpy.testing.assert_array_equal(
                dict1[1], self.eia_nlt_cp_reduced[idx])

    # Test that the walk_techdata function yields a KeyError given the
    # invalid key chain input along with the other sample inputs defined above
    def test_listgen_fail(self):
        with self.assertRaises(KeyError):
            for tk_f in self.tech_fail_keys:
                mseg_techdata.list_generator_techdata(
                    self.eia_nlt_cp, self.eia_nlt_l, self.eia_lt,
                    mseg_techdata.tech_eia_nonlt, mseg_techdata.tech_eia_lt,
                    self.tech_non_eia, tk_f, self.project_dict)


class FillYrsTest(unittest.TestCase):
    """ Test that both the fill_years_nlt and fill_years_lt functions yield
    the correct non-lighting and lighting tech. cost, performance, and lifetime
    info. given an input array with these data broken out across various time
    periods. * Note: only the fill_years_lt function accesses lifetime info. as
    lifetime is not broken out by year for non-lighting technologies """

    # Define a list of test input arrays with valid EIA data on the cost and
    # performance of non-lighting technologies to be stitched together
    # into a list of cost and performance output dicts that each cover the
    # modeling time horizon. * Note: the second element in this list tests the
    # special case of a freezer technology, which has data on multiple
    # configurations that must be consolidated into a single 'average'
    # configuration for proper handling by the stitch function.
    in_nonlt = [numpy.array([(2005, 2010, 2.5, 1000, b'ELEC_HP1'),
                            (2010, 2011, 2.65, 1200, b'ELEC_HP1'),
                            (2011, 2012, 3.1, 1250, b'ELEC_HP1'),
                            (2012, 2014, 4.5, 1450, b'ELEC_HP1'),
                            (2014, 2040, 5, 2000, b'ELEC_HP1')],
                            dtype=[('START_EQUIP_YR', '<i8'),
                                   ('END_EQUIP_YR', '<f8'),
                                   ('BASE_EFF', '<f8'),
                                   ('INST_COST', '<f8'),
                                   ('NAME', 'S10')]),
                numpy.array([(2005, 2010, 2.5, 1000, b'FrzrC#1'),
                            (2010, 2011, 2.65, 1200, b'FrzrC#1'),
                            (2011, 2012, 3.1, 1250, b'FrzrC#1'),
                            (2012, 2014, 4.5, 1450, b'FrzrC#1'),
                            (2014, 2040, 5, 2000, b'FrzrC#1'),
                            (2005, 2010, 3, 2000, b'FrzrU#1'),
                            (2010, 2011, 3.1, 1500, b'FrzrU#1'),
                            (2011, 2012, 3.7, 1500, b'FrzrU#1'),
                            (2012, 2014, 3.7, 1600, b'FrzrU#1'),
                            (2014, 2040, 6, 1900, b'FrzrU#1')],
                            dtype=[('START_EQUIP_YR', '<i8'),
                                   ('END_EQUIP_YR', '<f8'),
                                   ('BASE_EFF', '<f8'),
                                   ('INST_COST', '<f8'),
                                   ('NAME', 'S10')])]

    # Define a test input array with valid EIA data on the cost, performance,
    # and lifetime of lighting technologies to be stitched together into
    # a list of cost, performance, and lifetime output dicts that each covers
    # the modeling time horizon
    in_lt = numpy.array([(2008, 2012, 0.33, 10000, 55, b'GSL', b'Inc'),
                         (2012, 2013, 1.03, 20000, 60, b'GSL', b'Inc'),
                         (2013, 2017, 1.53, 35000, 61.2, b'GSL', b'Inc'),
                         (2017, 2020, 2.75, 40000, 80.3, b'GSL', b'Inc'),
                         (2020, 2040, 3.45, 50000, 90, b'GSL', b'Inc')],
                        dtype=[('START_EQUIP_YR', '<i8'),
                               ('END_EQUIP_YR', '<f8'),
                               ('BASE_EFF', '<f8'),
                               ('LIFE_HRS', '<f8'),
                               ('INST_COST', '<f8'),
                               ('NAME', 'S3'),
                               ('BULB_TYPE', 'S3')])

    # Define a test input array with faulty EIA data that should yield an
    # error in the fill_years_nlt and fill_years_lt function executions
    # when paired with the tech_fail_keys below (multiple rows with same
    # starting year and not a special technology case (refrigerators, freezers)
    in_fail = numpy.array([(2005, 2010, 2.5, 1000, b'Fail_Test1'),
                           (2010, 2011, 2.65, 1200, b'Fail_Test1'),
                           (2011, 2012, 3.1, 1250, b'Fail_Test1'),
                           (2012, 2014, 4.5, 1450, b'Fail_Test1'),
                           (2014, 2040, 5, 2000, b'Fail_Test1'),
                           (2005, 2010, 3, 2000, b'Fail_Test1'),
                           (2010, 2011, 3.1, 1500, b'Fail_Test1'),
                           (2011, 2012, 3.7, 1500, b'Fail_Test1'),
                           (2012, 2014, 3.7, 1600, b'Fail_Test1'),
                           (2014, 2040, 6, 1900, b'Fail_Test1')],
                          dtype=[('START_EQUIP_YR', '<i8'),
                                 ('END_EQUIP_YR', '<f8'),
                                 ('BASE_EFF', '<f8'),
                                 ('INST_COST', '<f8'),
                                 ('NAME', 'S3')])

    # Define a sample list of the technology-level keys that are defined while
    # running through the microsegments JSON structure; these keys are used to
    # flag non-lighting technologies that require special handling to update
    # with EIA data because of their unique definitions in these data
    # (i.e. refrigerators, freezers)
    tech_ok_key = ['ASHP', 'freezers']

    # Define a sample list of dictionary keys as above that should cause the
    # fill_years_nonlt function to fail when paired with an input array that
    # includes multiple rows with the same 'START_EQUIP_YR' value (this is
    # only allowed when 'refrigerators' or 'freezers' is in the key list)
    tech_fail_key = ['ASHP']

    # Define the modeling time horizon to test (2009:2015)
    years = [str(i) for i in range(2009, 2015 + 1)]
    project_dict = dict.fromkeys(years)

    # Define a list of output dicts that should be generated by the
    # fill_years_nlt function for each year of the modeling time horizon
    # based on the in_nonlt array input above
    out_nonlt = [[{"2009": 2.65, "2010": 2.65, "2011": 3.1, "2012": 4.5,
                   "2013": 4.5, "2014": 5, "2015": 5},
                  {"2009": 1200, "2010": 1200, "2011": 1250, "2012": 1450,
                   "2013": 1450, "2014": 2000, "2015": 2000}],
                 [{"2009": 2.88, "2010": 2.88, "2011": 3.4, "2012": 4.1,
                   "2013": 4.1, "2014": 5.5, "2015": 5.5},
                  {"2009": 1350, "2010": 1350, "2011": 1375, "2012": 1525,
                   "2013": 1525, "2014": 1950, "2015": 1950}]]

    # Define a list of output dicts that should be generated by the
    # fill_years_lt function for each year of the modeling time horizon
    # based on the in_lt array input above
    out_lt = [{"2009": 0.33, "2010": 0.33, "2011": 0.33, "2012": 1.03,
               "2013": 1.53, "2014": 1.53, "2015": 1.53},
              {"2009": 55, "2010": 55, "2011": 55, "2012": 60,
               "2013": 61.2, "2014": 61.2, "2015": 61.2},
              {"2009": 1.14, "2010": 1.14, "2011": 1.14, "2012": 2.28,
               "2013": 4.00, "2014": 4.00, "2015": 4.00}]

    # Create a routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                self.assertAlmostEqual(dict1[k], dict2[k2], places=2)

    # Test that the fill_years_nlt function yields a correct output list
    # given the in_nlt numpy array, modeling time horizon, and tech_ok_keys
    # inputs defined above
    def test_fill_nlt(self):
        for (idx, tk) in enumerate(self.tech_ok_key):
            list1 = mseg_techdata.fill_years_nlt(
                self.in_nonlt[idx], self.project_dict, tk)
            list2 = self.out_nonlt[idx]

            for (el1, el2) in zip(list1, list2):
                dict1 = el1
                dict2 = el2
                self.dict_check(dict1, dict2)

    # Test that the fill_years_lt function yields a correct output list given
    # the in_lt numpy array and modeling time horizon inputs defined above
    def test_fill_lt(self):
        list1 = mseg_techdata.fill_years_lt(
            self.in_lt, self.project_dict)
        list2 = self.out_lt

        for (el1, el2) in zip(list1, list2):
            dict1 = el1
            dict2 = el2
            self.dict_check(dict1, dict2)

    # Test that both the fill_years nlt and fill_years_lt functions yield a
    # ValueError when provided a numpy array input that has multiple rows
    # with the same 'START_EQUIP_YR' value
    def test_fail(self):
        with self.assertRaises(ValueError):
            mseg_techdata.fill_years_nlt(self.in_fail, self.project_dict,
                                         self.tech_fail_key)
            mseg_techdata.fill_years_lt(self.in_fail, self.project_dict)


class StitchTest(unittest.TestCase):
    """ Test operation of stitch function, which reconstructs EIA performance,
    cost, and lifetime projections for a technology between a series of
    time periods (i.e. 2010-2014, 2014-2020, 2020-2040) in a dict with annual
    keys across a given modeling time horizon (i.e. {"2009": XXX, "2010": XXX,
    ..., "2040": XXX}) """

    # Define a test input array with valid EIA data to stich together
    # across modeling time horizon
    ok_array = numpy.array([(2008, 2012, 0.33, 14.5, 55, b'GSL', b'Inc'),
                            (2012, 2013, 1.03, 20, 60, b'GSL', b'Inc'),
                            (2013, 2017, 1.53, 21, 61.2, b'GSL', b'Inc'),
                            (2017, 2020, 2.75, 22, 80.3, b'GSL', b'Inc'),
                            (2020, 2040, 3.45, 23, 90, b'GSL', b'Inc')],
                           dtype=[('START_EQUIP_YR', '<i8'),
                                  ('END_EQUIP_YR', '<f8'),
                                  ('BASE_EFF', '<f8'),
                                  ('LIFE_HRS', '<f8'),
                                  ('INST_COST', '<f8'),
                                  ('NAME', 'S3'),
                                  ('BULB_TYPE', 'S3')])

    # Define a test input array with faulty EIA data that should yield an
    # error in the function execution (multiple rows with same starting year)
    fail_array = numpy.array([(2008, 2012, 0.33, 14.5, 55, b'GSL', b'Inc'),
                              (2012, 2013, 1.03, 20, 60, b'GSL', b'Inc'),
                              (2013, 2017, 1.53, 21, 61.2, b'GSL', b'Inc'),
                              (2017, 2020, 2.75, 22, 80.3, b'GSL', b'Inc'),
                              (2020, 2040, 3.45, 23, 90, b'GSL', b'Inc'),
                              (2013, 2017, 1.53, 21, 61.2, b'GSL', b'Inc'),
                              (2017, 2020, 2.75, 22, 80.3, b'GSL', b'Inc'),
                              (2020, 2040, 3.45, 23, 90, b'GSL', b'Inc')],
                             dtype=[('START_EQUIP_YR', '<i8'),
                                    ('END_EQUIP_YR', '<f8'),
                                    ('BASE_EFF', '<f8'),
                                    ('LIFE_HRS', '<f8'),
                                    ('INST_COST', '<f8'),
                                    ('NAME', 'S3'),
                                    ('BULB_TYPE', 'S3')])

    # Define the modeling time horizon to test (2009:2015)
    years = [str(i) for i in range(2009, 2015 + 1)]
    project_dict = dict.fromkeys(years)

    # Define the each variable (column) in the input array with the values that
    # will be reconstructed annually across the modeling time horizon, based on
    # each row's 'START_EQUIP_YR' column value
    col_names = ['BASE_EFF', 'INST_COST', 'LIFE_HRS']

    # Define a dict of output values for the above variables in col_names that
    # should be generated by the function for each year of the modeling time
    # horizon based on the ok_array above
    ok_out = [{"2009": 0.33, "2010": 0.33, "2011": 0.33, "2012": 1.03,
               "2013": 1.53, "2014": 1.53, "2015": 1.53},
              {"2009": 55, "2010": 55, "2011": 55, "2012": 60,
               "2013": 61.2, "2014": 61.2, "2015": 61.2},
              {"2009": 14.5, "2010": 14.5, "2011": 14.5, "2012": 20,
               "2013": 21, "2014": 21, "2015": 21}]

    # Create a routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                self.assertAlmostEqual(dict1[k], dict2[k2], places=2)

    # Test that the function yields a correct output dict for each set of
    # variable values to be stitched together across the modeling time
    # horizon, given the ok_array above as an input
    def test_convert_match(self):
        for (idx, col_name) in enumerate(self.col_names):
            dict1 = mseg_techdata.stitch(
                self.ok_array, self.project_dict,
                col_name)
            dict2 = self.ok_out[idx]
            self.dict_check(dict1, dict2)

    # Test that the function yields a ValueError given the fail_array above,
    # which includes multiple rows with the same 'START_EQUIP_YR' column value
    def test_convert_fail(self):
        for (idx, col_name) in enumerate(self.col_names):
            with self.assertRaises(ValueError):
                mseg_techdata.stitch(self.fail_array, self.project_dict,
                                     col_name)


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == '__main__':
    main()
