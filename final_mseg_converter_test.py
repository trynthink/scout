#!/usr/bin/env python3

"""Tests for the census division to climate zone conversion script.
"""

# Import code to be tested
import final_mseg_converter as fmc

# Import code with translation dicts
import com_mseg as cm

# Import needed packages
import unittest
import numpy as np
import copy


class CommonUnitTest(unittest.TestCase):
    """ Set up a common unittest.TestCase subclass with data and
    functions common to the tests below """

    # Define routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            elif isinstance(i, list):
                np.testing.assert_almost_equal(dict1[k], dict2[k2], decimal=3)
            else:
                self.assertAlmostEqual(dict1[k], dict2[k2], places=3)

    # Array of census division to climate zone conversion factors for
    # energy, stock, and square footage data for residential buildings
    # Derived from Res_Cdiv_Czone_ConvertTable_Final.txt
    res_cd_cz_array = np.array([
        (1, 0.2196, 0.7273, 0.0532, 0.0, 0.0),
        (2, 0.0599, 0.3407, 0.5994, 0.0, 0.0),
        (3, 0.1554, 0.6739, 0.1707, 0.0, 0.0),
        (4, 0.3621, 0.206, 0.4274, 0.0045, 0.0),
        (5, 0.0, 0.0096, 0.258, 0.3514, 0.3811),
        (6, 0.0, 0.0, 0.287, 0.4393, 0.2736),
        (7, 0.0, 0.0, 0.061, 0.1416, 0.7974),
        (8, 0.1189, 0.3085, 0.1604, 0.0549, 0.3574),
        (9, 0.0202, 0.0204, 0.2157, 0.6996, 0.0442)],
        dtype=[('CDIV', '<i4'), ('AIA_CZ1', '<f8'), ('AIA_CZ2', '<f8'),
               ('AIA_CZ3', '<f8'), ('AIA_CZ4', '<f8'), ('AIA_CZ5', '<f8')])

    # Array of census division to climate zone conversion factors for
    # energy, stock, and square footage data for commercial buildings
    # Derived from Com_Cdiv_Czone_ConvertTable_Final.txt
    com_cd_cz_array = np.array([
        (1, 0.2389, 0.7611, 0.0, 0.0, 0.0),
        (2, 0.1546, 0.3568, 0.4886, 0.0, 0.0),
        (3, 0.2668, 0.7332, 0.0, 0.0, 0.0),
        (4, 0.4769, 0.2417, 0.2815, 0.0, 0.0),
        (5, 0.0, 0.0, 0.2107, 0.515, 0.2743),
        (6, 0.0, 0.0, 0.3102, 0.5726, 0.1172),
        (7, 0.0, 0.0, 0.0616, 0.2638, 0.6746),
        (8, 0.5681, 0.2986, 0.0, 0.0, 0.1332),
        (9, 0.0701, 0.129, 0.0792, 0.708, 0.0137)],
        dtype=[('CDIV', '<i4'), ('AIA_CZ1', '<f8'), ('AIA_CZ2', '<f8'),
               ('AIA_CZ3', '<f8'), ('AIA_CZ4', '<f8'), ('AIA_CZ5', '<f8')])

    # Residential building census division to climate zone conversion
    # factors for cost, performance, and lifetime data
    # Derived from Res_Cdiv_Czone_ConvertTable_Rev_Final.txt
    res_cd_cz_wtavg_array = np.array([
        (1, 0.13296, 0.15477, 0.00997, 0, 0),
        (2, 0.10044, 0.20077, 0.31107, 0, 0),
        (3, 0.30485, 0.46459, 0.10366, 0, 0),
        (4, 0.32086, 0.06415, 0.11721, 0.00146, 0),
        (5, 0, 0.00822, 0.195, 0.31172, 0.35048),
        (6, 0, 0, 0.06916, 0.12423, 0.08022),
        (7, 0, 0, 0.0265, 0.07217, 0.42143),
        (8, 0.10326, 0.09417, 0.04312, 0.01732, 0.11691),
        (9, 0.03763, 0.01332, 0.1243, 0.4731, 0.03096)],
        dtype=[('CDIV', '<i4'), ('AIA_CZ1', '<f8'), ('AIA_CZ2', '<f8'),
               ('AIA_CZ3', '<f8'), ('AIA_CZ4', '<f8'), ('AIA_CZ5', '<f8')])

    # Commercial building census division to climate zone conversion
    # factors for cost, performance, and lifetime data
    # Derived from Com_Cdiv_Czone_ConvertTable_Rev_Final.txt
    com_cd_cz_wtavg_array = np.array([
        (1, 0.07044, 0.13487, 0, 0, 0),
        (2, 0.13854, 0.19219, 0.41823, 0, 0),
        (3, 0.28803, 0.47563, 0, 0, 0),
        (4, 0.24615, 0.07497, 0.13876, 0, 0),
        (5, 0, 0, 0.24293, 0.40379, 0.35346),
        (6, 0, 0, 0.09947, 0.12486, 0.04198),
        (7, 0, 0, 0.04431, 0.12909, 0.54244),
        (8, 0.20464, 0.06465, 0, 0, 0.05122),
        (9, 0.0522, 0.05769, 0.0563, 0.34226, 0.01089)],
        dtype=[('CDIV', '<i4'), ('AIA_CZ1', '<f8'), ('AIA_CZ2', '<f8'),
               ('AIA_CZ3', '<f8'), ('AIA_CZ4', '<f8'), ('AIA_CZ5', '<f8')])


class DataRestructuringFunctionTest(CommonUnitTest):
    """ Test the operation of the function that calculates the
    contribution of each census division to each climate zone """

    # Create a sample dict that takes the form of the data provided
    # within each census division (each climate zone will have the
    # same keys and structure, but different numbers)
    orig_input = {
        'single family home': {
            'new homes': {'2009': 111, '2010': 111, '2011': 111},
            'total homes': {'2009': 222, '2010': 222, '2011': 222},
            'square footage': {'2009': 333, '2010': 333, '2011': 333},
            'electricity (grid)': {
                'lighting': {
                    'linear fluorescent': {
                        'stock': {'2009': 13, '2010': 14, '2011': 15},
                        'energy': {'2009': 16, '2010': 17, '2011': 18}}}}},
        'mercantile/service': {
            'total square footage': {'2009': 19, '2010': 21, '2011': 20},
            'new square footage': {'2009': 6, '2010': 5, '2011': 4},
            'electricity': {
                'lighting': {
                    'F96T8 HO_HB': {'2009': 0.3, '2010': 0.6, '2011': 0.7}}},
            'natural gas': {
                'water heating': {'2009': 20, '2010': 22, '2011': 23}}}}

    # Specify the census divisions to be tested; more than one census
    # divisions is tested here because the mathematical treatment of
    # the first census division (in the order in which it appears in
    # the census division list 'cd_list') to be added to a climate
    # zone is different than subsequent climate zones
    census_divisions = [1, 2]

    # Specify the climate zones to be tested with the census divisions
    # specified by 'census_divisions'
    climate_zones = [1, 1]

    # Create an instance of the CommericalTranslationDicts object from
    # com_mseg, which includes dictionaries for converting between
    # descriptive string keys for e.g., census divisions and the
    # corresponding integer numeric values for those strings
    cd = cm.CommercialTranslationDicts()

    # List of census divisions typically derived from the top-level
    # keys in the input JSON database
    cd_list = ['new england', 'mid atlantic', 'east north central']

    # List the dicts that should be produced from the inputs to the
    # merge_sum function in the order in which they should be tested
    # (i.e., matching the order of 'census_divisions' and 'climate_zones')
    loutput = [
        {'single family home': {
            'new homes': {
                '2009': 117.6489, '2010': 117.6489, '2011': 117.6489},
            'total homes': {
                '2009': 235.2978, '2010': 235.2978, '2011': 235.2978},
            'square footage': {
                '2009': 352.9467, '2010': 352.9467, '2011': 352.9467},
            'electricity (grid)': {
                'lighting': {
                    'linear fluorescent': {
                        'energy': {
                            '2009': 16.9584,
                            '2010': 18.0183,
                            '2011': 19.0782},
                        'stock': {
                            '2009': 13.7787,
                            '2010': 14.8386,
                            '2011': 15.8985}}}}},
         'mercantile/service': {
            'total square footage': {
                '2009': 21.9374, '2010': 24.2466, '2011': 23.092},
            'new square footage': {
                '2009': 6.9276, '2010': 5.773, '2011': 4.6184},
            'electricity': {
                'lighting': {
                    'F96T8 HO_HB': {
                        '2009': 0.3464, '2010': 0.6928, '2011': 0.8082}}},
            'natural gas': {
                'water heating': {
                    '2009': 23.092, '2010': 25.401, '2011': 26.556}}}},
        {'single family home': {
            'new homes': {
                '2009': 128.2494, '2010': 128.2494, '2011': 128.2494},
            'total homes': {
                '2009': 256.4988, '2010': 256.4988, '2011': 256.4988},
            'square footage': {
                '2009': 384.7482, '2010': 384.7482, '2011': 384.7482},
            'electricity (grid)': {
                'lighting': {
                    'linear fluorescent': {
                        'energy': {
                            '2009': 18.4864,
                            '2010': 19.6418,
                            '2011': 20.7972},
                        'stock': {
                            '2009': 15.0202,
                            '2010': 16.1756,
                            '2011': 17.331}}}}},
         'mercantile/service': {
            'natural gas': {
                'water heating': {
                    '2009': 25.336, '2010': 27.8696, '2011': 29.1363}},
            'total square footage': {
                '2009': 24.0692, '2010': 26.6028, '2011': 25.336},
            'new square footage': {
                '2009': 7.6008, '2010': 6.334, '2011': 5.0672},
            'electricity': {
                'lighting': {
                    'F96T8 HO_HB': {
                        '2009': 0.38, '2010': 0.7601, '2011': 0.8866}}}}}]

    def test_conversion_calculation_for_individual_cz_cd_combinations(self):
        for idx, _ in enumerate(self.census_divisions):
            # Since the merge_sum function recursively operates on
            # 'base_input', make the two required copies to serve as
            # the inputs for testing purposes to ensure that all tests
            # start with the same input data
            base_input = copy.deepcopy(self.orig_input)
            add_input = copy.deepcopy(self.orig_input)

            # Call the function to be tested
            result = fmc.merge_sum(base_input,
                                   add_input,
                                   self.census_divisions[idx],
                                   self.climate_zones[idx],
                                   self.cd.cdivdict,
                                   self.cd_list,
                                   self.res_cd_cz_array,
                                   self.com_cd_cz_array)

            self.dict_check(result, self.loutput[idx])


class ToClimateZoneConversionTest(CommonUnitTest):
    """ Test the operation of the full climate conversion function
    operating over multiple census divisions to convert the data to a
    climate zone basis """

    # Create a sample input dict of energy, square footage, and
    # stock data in three census divisions
    test_energy_stock_input = {
        'new england': {
            'single family home': {
                'new homes': {
                    '2009': 1, '2010': 11, '2011': 1},
                'total homes': {
                    '2009': 2, '2010': 22, '2011': 2},
                'square footage': {
                    '2009': 3, '2010': 33, '2011': 3},
                'electricity (grid)': {
                    'lighting': {
                        'linear fluorescent': {
                            'stock': {
                                '2009': 1,
                                '2010': 2,
                                '2011': 3},
                            'energy': {
                                '2009': 4,
                                '2010': 5,
                                '2011': 6}}},
                    'heating': {
                        'demand': {
                            'wall': {
                                'stock': 'NA',
                                'energy': {
                                    '2009': 3.5,
                                    '2010': 4,
                                    '2011': 5}}}}}},
            'mercantile/service': {
                'total square footage': {
                    '2009': 12, '2010': 13, '2011': 14},
                'new square footage': {
                    '2009': 2, '2010': 3, '2011': 4},
                'electricity': {
                    'lighting': {
                        'F96T8 HO_HB': {
                            '2009': 0.1, '2010': 0.2, '2011': 0.3}}},
                'natural gas': {
                    'water heating': {
                        '2009': 5, '2010': 6, '2011': 7}}}},
        'mid atlantic': {
            'single family home': {
                'new homes': {
                    '2009': 11, '2010': 11, '2011': 11},
                'total homes': {
                    '2009': 22, '2010': 22, '2011': 22},
                'square footage': {
                    '2009': 33, '2010': 33, '2011': 33},
                'electricity (grid)': {
                    'lighting': {
                        'linear fluorescent': {
                            'stock': {
                                '2009': 7,
                                '2010': 8,
                                '2011': 9},
                            'energy': {
                                '2009': 10,
                                '2010': 11,
                                '2011': 12}}},
                    'heating': {
                        'demand': {
                            'wall': {
                                'stock': 'NA',
                                'energy': {
                                    '2009': 6,
                                    '2010': 7,
                                    '2011': 8}}}}}},
            'mercantile/service': {
                'total square footage': {
                    '2009': 6, '2010': 7, '2011': 8},
                'new square footage': {
                    '2009': 2, '2010': 0, '2011': 1},
                'electricity': {
                    'lighting': {
                        'F96T8 HO_HB': {
                            '2009': 0.5, '2010': 0.6, '2011': 0.7}}},
                'natural gas': {
                    'water heating': {
                        '2009': 10, '2010': 11, '2011': 9}}}},
        'east north central': {
            'single family home': {
                'new homes': {
                    '2009': 111, '2010': 111, '2011': 111},
                'total homes': {
                    '2009': 222, '2010': 222, '2011': 222},
                'square footage': {
                    '2009': 333, '2010': 333, '2011': 333},
                'electricity (grid)': {
                    'lighting': {
                        'linear fluorescent': {
                            'stock': {
                                '2009': 13,
                                '2010': 14,
                                '2011': 15},
                            'energy': {
                                '2009': 16,
                                '2010': 17,
                                '2011': 18}}},
                    'heating': {
                        'demand': {
                            'wall': {
                                'stock': 'NA',
                                'energy': {
                                    '2009': 2,
                                    '2010': 3,
                                    '2011': 4}}}}}},
            'mercantile/service': {
                'total square footage': {
                    '2009': 19, '2010': 21, '2011': 20},
                'new square footage': {
                    '2009': 6, '2010': 5, '2011': 4},
                'electricity': {
                    'lighting': {
                        'F96T8 HO_HB': {
                            '2009': 0.3, '2010': 0.6, '2011': 0.7}}},
                'natural gas': {
                    'water heating': {
                        '2009': 20, '2010': 22, '2011': 23}}}}}

    # Create a sample input dict of cost, performance, and lifetime
    # data in three census divisions - note that including only a few
    # census divisions is done to reduce the effort to set up these
    # tests but will yield results that seem wrong because the
    # contributions from the other census divisions are missing
    test_cpl_input = {
        'south atlantic': {
            'mobile home': {
                'new homes': 0,
                'total homes': 0,
                'square footage': 0,
                'distillate': {
                    'heating': {
                        'supply': {
                            'boiler (distillate)': {
                                'installed cost': {
                                    'typical': {
                                        '2015': 20,
                                        '2016': 30,
                                        '2017': 40},
                                    'best': {
                                        '2015': 20,
                                        '2016': 30,
                                        '2017': 40},
                                    'source': 'EIA AEO',
                                    'units': '2013$/kBTU out/hr'},
                                'performance': {
                                    'typical': {
                                        '2015': 5,
                                        '2016': 6,
                                        '2017': 7},
                                    'best': {
                                        '2015': 5,
                                        '2016': 6,
                                        '2017': 7},
                                    'source': 'EIA AEO',
                                    'units': 'BTU out/BTU in'},
                                'lifetime': {
                                    'average': {
                                        '2015': 25,
                                        '2016': 25,
                                        '2017': 25},
                                    'range': {
                                        '2015': 25,
                                        '2016': 25,
                                        '2017': 25},
                                    'source': 'EIA AEO',
                                    'units': 'years'}}}}}},
            'assembly': {
                'total square footage': 0,
                'new square footage': 0,
                'electricity': {
                    'refrigeration': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0.1, 0.8, 1.2],
                                '2016': [0.1, 0.8, 1.2],
                                '2017': [0.1, 0.8, 1.2]},
                            'population fraction': {
                                '2015': [0.1, 0.3, 0.5],
                                '2016': [0.1, 0.3, 0.5],
                                '2017': [0.1, 0.3, 0.5]}},
                        'Supermkt_display_case': {
                            'installed cost': {
                                'typical': {
                                    '2015': 3.5,
                                    '2016': 4.5,
                                    '2017': 5.5},
                                'best': {
                                    '2015': 4.5,
                                    '2016': 5.5,
                                    '2017': 6.5},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 15,
                                    '2016': 15,
                                    '2017': 18},
                                'best': {
                                    '2015': 15,
                                    '2016': 15,
                                    '2017': 20},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 16,
                                    '2016': 16,
                                    '2017': 16},
                                'range': {
                                    '2015': 24,
                                    '2016': 24,
                                    '2017': 24},
                                'source': 'EIA AEO',
                                'units': 'years'}}}},
                'natural gas': {
                    'water heating': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0.1, 0.8, 1.2],
                                '2016': [0.1, 0.8, 1.2],
                                '2017': [0.1, 0.8, 1.2]},
                            'population fraction': {
                                '2015': [0.2, 0.4, 0.4],
                                '2016': [0.2, 0.4, 0.4],
                                '2017': [0.2, 0.4, 0.4]}},
                        'gas_water_heater': {
                            'installed cost': {
                                'typical': {
                                    '2015': 6,
                                    '2016': 6,
                                    '2017': 6},
                                'best': {
                                    '2015': 8,
                                    '2016': 8,
                                    '2017': 8},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 3.5,
                                    '2016': 4.5,
                                    '2017': 5.5},
                                'best': {
                                    '2015': 4.5,
                                    '2016': 5.5,
                                    '2017': 6.5},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 20,
                                    '2016': 20,
                                    '2017': 20},
                                'range': {
                                    '2015': 30,
                                    '2016': 30,
                                    '2017': 30},
                                'source': 'EIA AEO',
                                'units': 'years'}}}}}},
        'east south central': {
            'mobile home': {
                'new homes': 0,
                'total homes': 0,
                'square footage': 0,
                'distillate': {
                    'heating': {
                        'supply': {
                            'boiler (distillate)': {
                                'installed cost': {
                                    'typical': {
                                        '2015': 7,
                                        '2016': 8,
                                        '2017': 9},
                                    'best': {
                                        '2015': 10,
                                        '2016': 12,
                                        '2017': 14},
                                    'source': 'EIA AEO',
                                    'units': '2013$/kBTU out/hr'},
                                'performance': {
                                    'typical': {
                                        '2015': 7,
                                        '2016': 8,
                                        '2017': 9},
                                    'best': {
                                        '2015': 10,
                                        '2016': 12,
                                        '2017': 14},
                                    'source': 'EIA AEO',
                                    'units': 'BTU out/BTU in'},
                                'lifetime': {
                                    'average': {
                                        '2015': 25,
                                        '2016': 25,
                                        '2017': 25},
                                    'range': {
                                        '2015': 25,
                                        '2016': 25,
                                        '2017': 25},
                                    'source': 'EIA AEO',
                                    'units': 'years'}}}}}},
            'assembly': {
                'total square footage': 0,
                'new square footage': 0,
                'electricity': {
                    'refrigeration': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0.1, 0.8, 1.2],
                                '2016': [0.1, 0.8, 1.2],
                                '2017': [0.1, 0.8, 1.2]},
                            'population fraction': {
                                '2015': [0.1, 0.3, 0.5],
                                '2016': [0.1, 0.3, 0.5],
                                '2017': [0.1, 0.3, 0.5]}},
                        'Supermkt_display_case': {
                            'installed cost': {
                                'typical': {
                                    '2015': 28,
                                    '2016': 35,
                                    '2017': 57},
                                'best': {
                                    '2015': 36,
                                    '2016': 50,
                                    '2017': 53.3},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 15,
                                    '2016': 18,
                                    '2017': 21},
                                'best': {
                                    '2015': 16,
                                    '2016': 19,
                                    '2017': 22},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 19,
                                    '2016': 19,
                                    '2017': 19},
                                'range': {
                                    '2015': 28,
                                    '2016': 28,
                                    '2017': 28},
                                'source': 'EIA AEO',
                                'units': 'years'}}}},
                'natural gas': {
                    'water heating': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0.1, 0.8, 1.2],
                                '2016': [0.1, 0.8, 1.2],
                                '2017': [0.1, 0.8, 1.2]},
                            'population fraction': {
                                '2015': [0.1, 0.3, 0.5],
                                '2016': [0.1, 0.3, 0.5],
                                '2017': [0.1, 0.3, 0.5]}},
                        'gas_water_heater': {
                            'installed cost': {
                                'typical': {
                                    '2015': 10,
                                    '2016': 15,
                                    '2017': 20},
                                'best': {
                                    '2015': 10,
                                    '2016': 15,
                                    '2017': 20},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 4,
                                    '2016': 5,
                                    '2017': 6},
                                'best': {
                                    '2015': 4,
                                    '2016': 5,
                                    '2017': 6},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 7,
                                    '2016': 8,
                                    '2017': 9},
                                'range': {
                                    '2015': 10,
                                    '2016': 11,
                                    '2017': 12},
                                'source': 'EIA AEO',
                                'units': 'years'}}}}}},
        'west south central': {
            'mobile home': {
                'new homes': 0,
                'total homes': 0,
                'square footage': 0,
                'distillate': {
                    'heating': {
                        'supply': {
                            'boiler (distillate)': {
                                'installed cost': {
                                    'typical': {
                                        '2015': 2,
                                        '2016': 3,
                                        '2017': 4},
                                    'best': {
                                        '2015': 5,
                                        '2016': 6,
                                        '2017': 7},
                                    'source': 'EIA AEO',
                                    'units': '2013$/kBTU out/hr'},
                                'performance': {
                                    'typical': {
                                        '2015': 2,
                                        '2016': 3,
                                        '2017': 4},
                                    'best': {
                                        '2015': 5,
                                        '2016': 6,
                                        '2017': 7},
                                    'source': 'EIA AEO',
                                    'units': 'BTU out/BTU in'},
                                'lifetime': {
                                    'average': {
                                        '2015': 25,
                                        '2016': 25,
                                        '2017': 25},
                                    'range': {
                                        '2015': 25,
                                        '2016': 25,
                                        '2017': 25},
                                    'source': 'EIA AEO',
                                    'units': 'years'}}}}}},
            'assembly': {
                'total square footage': 0,
                'new square footage': 0,
                'electricity': {
                    'refrigeration': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0.1, 0.8, 1.2],
                                '2016': [0.1, 0.8, 1.2],
                                '2017': [0.1, 0.8, 1.2]},
                            'population fraction': {
                                '2015': [0.1, 0.4, 0.5],
                                '2016': [0.1, 0.4, 0.5],
                                '2017': [0.1, 0.4, 0.5]}},
                        'Supermkt_display_case': {
                            'installed cost': {
                                'typical': {
                                    '2015': 11,
                                    '2016': 12,
                                    '2017': 14},
                                'best': {
                                    '2015': 16,
                                    '2016': 18,
                                    '2017': 20},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 23,
                                    '2016': 23,
                                    '2017': 23},
                                'best': {
                                    '2015': 27,
                                    '2016': 27,
                                    '2017': 27},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 7,
                                    '2016': 8,
                                    '2017': 9},
                                'range': {
                                    '2015': 10,
                                    '2016': 11,
                                    '2017': 12},
                                'source': 'EIA AEO',
                                'units': 'years'}}}},
                'natural gas': {
                    'water heating': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0.1, 0.8, 1.2],
                                '2016': [0.1, 0.8, 1.2],
                                '2017': [0.1, 0.8, 1.2]},
                            'population fraction': {
                                '2015': [0.2, 0.3, 0.5],
                                '2016': [0.2, 0.3, 0.5],
                                '2017': [0.2, 0.3, 0.5]}},
                        'gas_water_heater': {
                            'installed cost': {
                                'typical': {
                                    '2015': 3,
                                    '2016': 5,
                                    '2017': 7},
                                'best': {
                                    '2015': 4,
                                    '2016': 6,
                                    '2017': 8},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 1.5,
                                    '2016': 2.5,
                                    '2017': 3.5},
                                'best': {
                                    '2015': 2.5,
                                    '2016': 3.5,
                                    '2017': 4.5},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 6,
                                    '2016': 6,
                                    '2017': 6},
                                'range': {
                                    '2015': 6,
                                    '2016': 6,
                                    '2017': 6},
                                'source': 'EIA AEO',
                                'units': 'years'}}}}}}}

    # Create a sample input dict that will trigger KeyError exceptions
    # because it is not correctly structured
    test_fail_input = {
        'new england': {
            'single family home': {
                'electricity (grid)': {
                    'lighting': {
                        'linear fluorescent': {
                            'stock': {
                                '2009': 1,
                                '2010': 1,
                                '2011': 1},
                            'energy': {
                                '2009': 1,
                                '2010': 1,
                                '2011': 1}}}}}},
        'middle atlantic': {
            'single family home': {
                'electricity (grid)': {
                    'lighting': {
                        'linear fluorescent': {
                            'stock': {
                                '2009': 2,
                                '2010': 2,
                                '2011': 2},
                            'energy': {
                                '2009': 2,
                                '2010': 2,
                                '2011': 2}}}}}},
        'east north central': {
            'single family home': {
                'electricity (grid)': {
                    'lighting': {
                        'linear fluorescent': {
                            'stock': {
                                '2009': 3,
                                '2010': 3,
                                '2011': 3},
                            'energy': {
                                '2009': 3,
                                '2010': 3,
                                '2011': 3}}}}}}}

    # Create an expected output dict of energy, square footage, and
    # stock data structured by climate zone
    test_energy_stock_output = {
        'AIA_CZ1': {
            'single family home': {
                'new homes': {
                    '2009': 18.1279, '2010': 20.3239, '2011': 18.1279},
                'total homes': {
                    '2009': 36.2558, '2010': 40.6478, '2011': 36.2558},
                'square footage': {
                    '2009': 54.3837, '2010': 60.9717, '2011': 54.3837},
                'electricity (grid)': {
                    'lighting': {
                        'linear fluorescent': {
                            "stock": {
                                "2009": 2.6591,
                                "2010": 3.0940,
                                "2011": 3.5289},
                            "energy": {
                                "2009": 3.9638,
                                "2010": 4.3987,
                                "2011": 4.8336}}},
                    'heating': {
                        'demand': {
                            'wall': {
                                'stock': 'NA',
                                'energy': {
                                    '2009': 1.4388,
                                    '2010': 1.7639,
                                    '2011': 2.1988}}}}}},
            'mercantile/service': {
                'total square footage': {
                    '2009': 8.8636, '2010': 9.7907, '2011': 9.9174},
                'new square footage': {
                    '2009': 2.3878, '2010': 2.0507, '2011': 2.1774},
                'electricity': {
                    'lighting': {
                        'F96T8 HO_HB': {
                            '2009': 0.1812, '2010': 0.3006, '2011': 0.3667}}},
                'natural gas': {
                    'water heating': {
                        '2009': 8.0765, '2010': 9.0036, '2011': 9.2001}}}},
        'AIA_CZ2': {
            'single family home': {
                'new homes': {
                    '2009': 79.2779, '2010': 86.5509, '2011': 79.2779},
                'total homes': {
                    '2009': 158.5558, '2010': 173.1018, '2011': 158.5558},
                'square footage': {
                    '2009': 237.8337, '2010': 259.6527, '2011': 237.8337},
                'electricity (grid)': {
                    'lighting': {
                        'linear fluorescent': {
                            "stock": {
                                "2009": 11.8729,
                                "2010": 13.6148,
                                "2011": 15.3567},
                            "energy": {
                                "2009": 17.0986,
                                "2010": 18.8405,
                                "2011": 20.5824}}},
                    'heating': {
                        'demand': {
                            'wall': {
                                'stock': 'NA',
                                'energy': {
                                    '2009': 5.9376,
                                    '2010': 7.3158,
                                    '2011': 9.0578}}}}}},
            'mercantile/service': {
                'total square footage': {
                    '2009': 25.2048, '2010': 27.7891, '2011': 28.1738},
                'new square footage': {
                    '2009': 6.635, '2010': 5.9493, '2011': 6.334},
                'electricity': {
                    'lighting': {
                        'F96T8 HO_HB': {
                            '2009': 0.4745, '2010': 0.8062, '2011': 0.9913}}},
                'natural gas': {
                    'water heating': {
                        '2009': 22.0375, '2010': 24.6218, '2011': 25.4025}}}},
        'AIA_CZ3': {
            'single family home': {
                'new homes': {
                    '2009': 25.5943, '2010': 26.1263, '2011': 25.5943},
                'total homes': {
                    '2009': 51.1886, '2010': 52.2526, '2011': 51.1886},
                'square footage': {
                    '2009': 76.7829, '2010': 78.3789, '2011': 76.7829},
                'electricity (grid)': {
                    'lighting': {
                        'linear fluorescent': {
                            "stock": {
                                "2009": 6.4681,
                                "2010": 7.2914,
                                "2011": 8.1147},
                            "energy": {
                                "2009": 8.9380,
                                "2010": 9.7613,
                                "2011": 10.5846}}},
                    'heating': {
                        'demand': {
                            'wall': {
                                'stock': 'NA',
                                'energy': {
                                    '2009': 4.124,
                                    '2010': 4.9207,
                                    '2011': 5.744}}}}}},
            'mercantile/service': {
                'total square footage': {
                    '2009': 2.9316, '2010': 3.4202, '2011': 3.9088},
                'new square footage': {
                    '2009': 0.9772, '2010': 0, '2011': 0.4886},
                'electricity': {
                    'lighting': {
                        'F96T8 HO_HB': {
                            '2009': 0.2443, '2010': 0.2932, '2011': 0.3420}}},
                'natural gas': {
                    'water heating': {
                        '2009': 4.886, '2010': 5.3746, '2011': 4.3974}}}},
        'AIA_CZ4': {
            'single family home': {
                'new homes': {
                    '2009': 0, '2010': 0, '2011': 0},
                'total homes': {
                    '2009': 0, '2010': 0, '2011': 0},
                'square footage': {
                    '2009': 0, '2010': 0, '2011': 0},
                'electricity (grid)': {
                    'lighting': {
                        'linear fluorescent': {
                            "stock": {
                                "2009": 0,
                                "2010": 0,
                                "2011": 0},
                            "energy": {
                                "2009": 0,
                                "2010": 0,
                                "2011": 0}}},
                    'heating': {
                        'demand': {
                            'wall': {
                                'stock': 'NA',
                                'energy': {
                                    '2009': 0,
                                    '2010': 0,
                                    '2011': 0}}}}}},
            'mercantile/service': {
                'total square footage': {
                    '2009': 0, '2010': 0, '2011': 0},
                'new square footage': {
                    '2009': 0, '2010': 0, '2011': 0},
                'electricity': {
                    'lighting': {
                        'F96T8 HO_HB': {
                            '2009': 0, '2010': 0, '2011': 0}}},
                'natural gas': {
                    'water heating': {
                        '2009': 0, '2010': 0, '2011': 0}}}},
        'AIA_CZ5': {
            'single family home': {
                'new homes': {
                    '2009': 0, '2010': 0, '2011': 0},
                'total homes': {
                    '2009': 0, '2010': 0, '2011': 0},
                'square footage': {
                    '2009': 0, '2010': 0, '2011': 0},
                'electricity (grid)': {
                    'lighting': {
                        'linear fluorescent': {
                            "stock": {
                                "2009": 0,
                                "2010": 0,
                                "2011": 0},
                            "energy": {
                                "2009": 0,
                                "2010": 0,
                                "2011": 0}}},
                    'heating': {
                        'demand': {
                            'wall': {
                                'stock': 'NA',
                                'energy': {
                                    '2009': 0,
                                    '2010': 0,
                                    '2011': 0}}}}}},
            'mercantile/service': {
                'total square footage': {
                    '2009': 0, '2010': 0, '2011': 0},
                'new square footage': {
                    '2009': 0, '2010': 0, '2011': 0},
                'electricity': {
                    'lighting': {
                        'F96T8 HO_HB': {
                            '2009': 0, '2010': 0, '2011': 0}}},
                'natural gas': {
                    'water heating': {
                        '2009': 0, '2010': 0, '2011': 0}}}}}

    # Create an expected output dict of cost, performance, and lifetime
    # data structured by climate zone
    test_cpl_output = {
        'AIA_CZ1': {
            'mobile home': {
                'new homes': 0,
                'total homes': 0,
                'square footage': 0,
                'distillate': {
                    'heating': {
                        'supply': {
                            'boiler (distillate)': {
                                'installed cost': {
                                    'typical': {
                                        '2015': 0,
                                        '2016': 0,
                                        '2017': 0},
                                    'best': {
                                        '2015': 0,
                                        '2016': 0,
                                        '2017': 0},
                                    'source': 'EIA AEO',
                                    'units': '2013$/kBTU out/hr'},
                                'performance': {
                                    'typical': {
                                        '2015': 0,
                                        '2016': 0,
                                        '2017': 0},
                                    'best': {
                                        '2015': 0,
                                        '2016': 0,
                                        '2017': 0},
                                    'source': 'EIA AEO',
                                    'units': 'BTU out/BTU in'},
                                'lifetime': {
                                    'average': {
                                        '2015': 0,
                                        '2016': 0,
                                        '2017': 0},
                                    'range': {
                                        '2015': 0,
                                        '2016': 0,
                                        '2017': 0},
                                    'source': 'EIA AEO',
                                    'units': 'years'}}}}}},
            'assembly': {
                'total square footage': 0,
                'new square footage': 0,
                'electricity': {
                    'refrigeration': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0, 0, 0],
                                '2016': [0, 0, 0],
                                '2017': [0, 0, 0]},
                            'population fraction': {
                                '2015': [0, 0, 0],
                                '2016': [0, 0, 0],
                                '2017': [0, 0, 0]}},
                        'Supermkt_display_case': {
                            'installed cost': {
                                'typical': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'best': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'best': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'range': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'source': 'EIA AEO',
                                'units': 'years'}}}},
                'natural gas': {
                    'water heating': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0, 0, 0],
                                '2016': [0, 0, 0],
                                '2017': [0, 0, 0]},
                            'population fraction': {
                                '2015': [0, 0, 0],
                                '2016': [0, 0, 0],
                                '2017': [0, 0, 0]}},
                        'gas_water_heater': {
                            'installed cost': {
                                'typical': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'best': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'best': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'range': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'source': 'EIA AEO',
                                'units': 'years'}}}}}},
        'AIA_CZ2': {
            'mobile home': {
                'new homes': 0,
                'total homes': 0,
                'square footage': 0,
                'distillate': {
                    'heating': {
                        'supply': {
                            'boiler (distillate)': {
                                'installed cost': {
                                    'typical': {
                                        '2015': 0.1644,
                                        '2016': 0.2466,
                                        '2017': 0.3288},
                                    'best': {
                                        '2015': 0.1644,
                                        '2016': 0.2466,
                                        '2017': 0.3288},
                                    'source': 'EIA AEO',
                                    'units': '2013$/kBTU out/hr'},
                                'performance': {
                                    'typical': {
                                        '2015': 0.0411,
                                        '2016': 0.0493,
                                        '2017': 0.0575},
                                    'best': {
                                        '2015': 0.0411,
                                        '2016': 0.0493,
                                        '2017': 0.0575},
                                    'source': 'EIA AEO',
                                    'units': 'BTU out/BTU in'},
                                'lifetime': {
                                    'average': {
                                        '2015': 0.2055,
                                        '2016': 0.2055,
                                        '2017': 0.2055},
                                    'range': {
                                        '2015': 0.2055,
                                        '2016': 0.2055,
                                        '2017': 0.2055},
                                    'source': 'EIA AEO',
                                    'units': 'years'}}}}}},
            'assembly': {
                'total square footage': 0,
                'new square footage': 0,
                'electricity': {
                    'refrigeration': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0, 0, 0],
                                '2016': [0, 0, 0],
                                '2017': [0, 0, 0]},
                            'population fraction': {
                                '2015': [0, 0, 0],
                                '2016': [0, 0, 0],
                                '2017': [0, 0, 0]}},
                        'Supermkt_display_case': {
                            'installed cost': {
                                'typical': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'best': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'best': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'range': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'source': 'EIA AEO',
                                'units': 'years'}}}},
                'natural gas': {
                    'water heating': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0, 0, 0],
                                '2016': [0, 0, 0],
                                '2017': [0, 0, 0]},
                            'population fraction': {
                                '2015': [0, 0, 0],
                                '2016': [0, 0, 0],
                                '2017': [0, 0, 0]}},
                        'gas_water_heater': {
                            'installed cost': {
                                'typical': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'best': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'best': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'range': {
                                    '2015': 0,
                                    '2016': 0,
                                    '2017': 0},
                                'source': 'EIA AEO',
                                'units': 'years'}}}}}},
        'AIA_CZ3': {
            'mobile home': {
                'new homes': 0,
                'total homes': 0,
                'square footage': 0,
                'distillate': {
                    'heating': {
                        'supply': {
                            'boiler (distillate)': {
                                'installed cost': {
                                    'typical': {
                                        '2015': 4.4371,
                                        '2016': 6.4828,
                                        '2017': 8.5284},
                                    'best': {
                                        '2015': 4.7241,
                                        '2016': 6.8389,
                                        '2017': 8.9537},
                                    'source': 'EIA AEO',
                                    'units': '2013$/kBTU out/hr'},
                                'performance': {
                                    'typical': {
                                        '2015': 1.5121,
                                        '2016': 1.8023,
                                        '2017': 2.0934},
                                    'best': {
                                        '2015': 1.7991,
                                        '2016': 2.1589,
                                        '2017': 2.5187},
                                    'source': 'EIA AEO',
                                    'units': 'BTU out/BTU in'},
                                'lifetime': {
                                    'average': {
                                        '2015': 7.2665,
                                        '2016': 7.2665,
                                        '2017': 7.2665},
                                    'range': {
                                        '2015': 7.2665,
                                        '2016': 7.2665,
                                        '2017': 7.2665},
                                    'source': 'EIA AEO',
                                    'units': 'years'}}}}}},
            'assembly': {
                'total square footage': 0,
                'new square footage': 0,
                'electricity': {
                    'refrigeration': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0.0387, 0.3093, 0.4641],
                                '2016': [0.0387, 0.3093, 0.4641],
                                '2017': [0.0387, 0.3093, 0.4641]},
                            'population fraction': {
                                '2015': [0.0387, 0.1204, 0.1934],
                                '2016': [0.0387, 0.1204, 0.1934],
                                '2017': [0.0387, 0.1204, 0.1934]}},
                        'Supermkt_display_case': {
                            'installed cost': {
                                'typical': {
                                    '2015': 4.1228,
                                    '2016': 5.1064,
                                    '2017': 7.6262},
                                'best': {
                                    '2015': 5.3831,
                                    '2016': 7.1072,
                                    '2017': 7.767},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 6.1551,
                                    '2016': 6.4535,
                                    '2017': 7.4807},
                                'best': {
                                    '2015': 6.4318,
                                    '2016': 6.7303,
                                    '2017': 8.2433},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 6.087,
                                    '2016': 6.1313,
                                    '2017': 6.1756},
                                'range': {
                                    '2015': 9.0586,
                                    '2016': 9.1029,
                                    '2017': 9.1472},
                                'source': 'EIA AEO',
                                'units': 'years'}}}},
                'natural gas': {
                    'water heating': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0.0387, 0.3093, 0.4641],
                                '2016': [0.0387, 0.3093, 0.4641],
                                '2017': [0.0387, 0.3093, 0.4641]},
                            'population fraction': {
                                '2015': [0.0674, 0.1403, 0.1691],
                                '2016': [0.0674, 0.1403, 0.1691],
                                '2017': [0.0674, 0.1403, 0.1691]}},
                        'gas_water_heater': {
                            'installed cost': {
                                'typical': {
                                    '2015': 2.5852,
                                    '2016': 3.1712,
                                    '2017': 3.7572},
                                'best': {
                                    '2015': 3.1154,
                                    '2016': 3.7014,
                                    '2017': 4.2873},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 1.3146,
                                    '2016': 1.7013,
                                    '2017': 2.088},
                                'best': {
                                    '2015': 1.6018,
                                    '2016': 1.9886,
                                    '2017': 2.3753},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 5.8208,
                                    '2016': 5.9202,
                                    '2017': 6.0197},
                                'range': {
                                    '2015': 8.5485,
                                    '2016': 8.6479,
                                    '2017': 8.7474},
                                'source': 'EIA AEO',
                                'units': 'years'}}}}}},
        'AIA_CZ4': {
            'mobile home': {
                'new homes': 0,
                'total homes': 0,
                'square footage': 0,
                'distillate': {
                    'heating': {
                        'supply': {
                            'boiler (distillate)': {
                                'installed cost': {
                                    'typical': {
                                        '2015': 7.2484,
                                        '2016': 10.5619,
                                        '2017': 13.8756},
                                    'best': {
                                        '2015': 7.8376,
                                        '2016': 11.2754,
                                        '2017': 14.7132},
                                    'source': 'EIA AEO',
                                    'units': '2013$/kBTU out/hr'},
                                'performance': {
                                    'typical': {
                                        '2015': 2.5726,
                                        '2016': 3.0807,
                                        '2017': 3.5888},
                                    'best': {
                                        '2015': 3.1618,
                                        '2016': 3.7941,
                                        '2017': 4.4265},
                                    'source': 'EIA AEO',
                                    'units': 'BTU out/BTU in'},
                                'lifetime': {
                                    'average': {
                                        '2015': 12.703,
                                        '2016': 12.703,
                                        '2017': 12.703},
                                    'range': {
                                        '2015': 12.703,
                                        '2016': 12.703,
                                        '2017': 12.703},
                                    'source': 'EIA AEO',
                                    'units': 'years'}}}}}},
            'assembly': {
                'total square footage': 0,
                'new square footage': 0,
                'electricity': {
                    'refrigeration': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0.0658, 0.5262, 0.7893],
                                '2016': [0.0658, 0.5262, 0.7893],
                                '2017': [0.0658, 0.5262, 0.7893]},
                            'population fraction': {
                                '2015': [0.0658, 0.2102, 0.3289],
                                '2016': [0.0658, 0.2102, 0.3289],
                                '2017': [0.0658, 0.2102, 0.3289]}},
                        'Supermkt_display_case': {
                            'installed cost': {
                                'typical': {
                                    '2015': 6.3293,
                                    '2016': 7.7362,
                                    '2017': 11.1451},
                                'best': {
                                    '2015': 8.3775,
                                    '2016': 10.7875,
                                    '2017': 11.8615},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 10.8988,
                                    '2016': 11.2734,
                                    '2017': 12.8594},
                                'best': {
                                    '2015': 11.54,
                                    '2016': 11.9146,
                                    '2017': 14.3082},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 9.7366,
                                    '2016': 9.8657,
                                    '2017': 9.9948},
                                'range': {
                                    '2015': 14.4779,
                                    '2016': 14.607,
                                    '2017': 14.7361},
                                'source': 'EIA AEO',
                                'units': 'years'}}}},
                'natural gas': {
                    'water heating': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0.0658, 0.5262, 0.7893],
                                '2016': [0.0658, 0.5262, 0.7893],
                                '2017': [0.0658, 0.5262, 0.7893]},
                            'population fraction': {
                                '2015': [0.1191, 0.2377, 0.2885],
                                '2016': [0.1191, 0.2377, 0.2885],
                                '2017': [0.1191, 0.2377, 0.2885]}},
                        'gas_water_heater': {
                            'installed cost': {
                                'typical': {
                                    '2015': 4.0586,
                                    '2016': 4.9411,
                                    '2017': 5.8236},
                                'best': {
                                    '2015': 4.9953,
                                    '2016': 5.8778,
                                    '2017': 6.7602},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 2.1063,
                                    '2016': 2.7641,
                                    '2017': 3.4218},
                                'best': {
                                    '2015': 2.6392,
                                    '2016': 3.297,
                                    '2017': 3.9547},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 9.7244,
                                    '2016': 9.8492,
                                    '2017': 9.9741},
                                'range': {
                                    '2015': 14.1368,
                                    '2016': 14.2617,
                                    '2017': 14.3866},
                                'source': 'EIA AEO',
                                'units': 'years'}}}}}},
        'AIZ_CZ5': {
            'mobile home': {
                'new homes': 0,
                'total homes': 0,
                'square footage': 0,
                'distillate': {
                    'heating': {
                        'supply': {
                            'boiler (distillate)': {
                                'installed cost': {
                                    'typical': {
                                        '2015': 8.414,
                                        '2016': 12.4205,
                                        '2017': 16.4269},
                                    'best': {
                                        '2015': 9.9189,
                                        '2016': 14.0056,
                                        '2017': 18.0923},
                                    'source': 'EIA AEO',
                                    'units': '2013$/kBTU out/hr'},
                                'performance': {
                                    'typical': {
                                        '2015': 3.1568,
                                        '2016': 4.0089,
                                        '2017': 4.8611},
                                    'best': {
                                        '2015': 4.6618,
                                        '2016': 5.5941,
                                        '2017': 6.5265},
                                    'source': 'EIA AEO',
                                    'units': 'BTU out/BTU in'},
                                'lifetime': {
                                    'average': {
                                        '2015': 21.3033,
                                        '2016': 21.3033,
                                        '2017': 21.3033},
                                    'range': {
                                        '2015': 21.3033,
                                        '2016': 21.3033,
                                        '2017': 21.3033},
                                    'source': 'EIA AEO',
                                    'units': 'years'}}}}}},
            'assembly': {
                'total square footage': 0,
                'new square footage': 0,
                'electricity': {
                    'refrigeration': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0.0938, 0.7503, 1.1255],
                                '2016': [0.0938, 0.7503, 1.1255],
                                '2017': [0.0938, 0.7503, 1.1255]},
                            'population fraction': {
                                '2015': [0.0938, 0.3356, 0.4689],
                                '2016': [0.0938, 0.3356, 0.4689],
                                '2017': [0.0938, 0.3356, 0.4689]}},
                        'Supermkt_display_case': {
                            'installed cost': {
                                'typical': {
                                    '2015': 8.3794,
                                    '2016': 9.5692,
                                    '2017': 11.9311},
                                'best': {
                                    '2015': 11.7809,
                                    '2016': 13.807,
                                    '2017': 15.3838},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 18.4077,
                                    '2016': 18.5337,
                                    '2017': 19.72},
                                'best': {
                                    '2015': 20.6195,
                                    '2016': 20.7454,
                                    '2017': 22.6386},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 10.2501,
                                    '2016': 10.7925,
                                    '2017': 11.3349},
                                'range': {
                                    '2015': 15.0829,
                                    '2016': 15.6253,
                                    '2017': 16.1678},
                                'source': 'EIA AEO',
                                'units': 'years'}}}},
                'natural gas': {
                    'water heating': {
                        'consumer choice': {
                            'time preference': {
                                '2015': [0.0938, 0.7503, 1.1255],
                                '2016': [0.0938, 0.7503, 1.1255],
                                '2017': [0.0938, 0.7503, 1.1255]},
                            'population fraction': {
                                '2015': [0.1834, 0.3167, 0.4336],
                                '2016': [0.1834, 0.3167, 0.4336],
                                '2017': [0.1834, 0.3167, 0.4336]}},
                        'gas_water_heater': {
                            'installed cost': {
                                'typical': {
                                    '2015': 4.1679,
                                    '2016': 5.4627,
                                    '2017': 6.7574},
                                'best': {
                                    '2015': 5.4172,
                                    '2016': 6.712,
                                    '2017': 8.0068},
                                'source': 'EIA AEO',
                                'units': '2013$/kBTU out/hr'},
                            'performance': {
                                'typical': {
                                    '2015': 2.2187,
                                    '2016': 3.1566,
                                    '2017': 4.0945},
                                'best': {
                                    '2015': 3.1146,
                                    '2016': 4.0525,
                                    '2017': 4.9904},
                                'source': 'EIA AEO',
                                'units': 'BTU out/BTU in'},
                            'lifetime': {
                                'average': {
                                    '2015': 10.6177,
                                    '2016': 10.6597,
                                    '2017': 10.7017},
                                'range': {
                                    '2015': 14.2782,
                                    '2016': 14.3202,
                                    '2017': 14.3622},
                                'source': 'EIA AEO',
                                'units': 'years'}}}}}}}

    # Compare the converted dict of energy, stock, and square footage
    # data to the expected data reported on a climate zone basis
    def test_conversion_of_energy_stock_square_footage_data(self):
        dict1 = fmc.clim_converter(self.test_energy_stock_input,
                                   self.res_cd_cz_array,
                                   self.com_cd_cz_array)
        dict2 = self.test_energy_stock_output
        self.dict_check(dict1, dict2)

    # Compare the converted dict of cost, performance, and lifetime
    # data to the expected data on a climate zone basis
    def test_conversion_of_cost_performance_lifetime_data(self):
        dict1 = fmc.clim_converter(self.test_cpl_input,
                                   self.res_cd_cz_wtavg_array,
                                   self.com_cd_cz_wtavg_array)
        dict2 = self.test_cpl_output
        self.dict_check(dict1, dict2)

    # Check malformed dict to verify that the appropriate error is raised
    def test_census_division_to_climate_zone_conversion_error_handling(self):
        with self.assertRaises(KeyError):
            fmc.clim_converter(self.test_fail_input,
                               self.res_cd_cz_array,
                               self.com_cd_cz_array)


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == '__main__':
    main()
